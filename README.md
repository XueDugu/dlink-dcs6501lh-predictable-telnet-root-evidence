# D-Link DCS-6501LH predictable root password (MD5("DCS-6501LH-"+MAC)[0:8]) with a default-enabled Telnet service

The D-Link DCS-6501LH derives the root account password from public device attributes instead of a random
device secret:

    root_password = MD5( "<model>-" + uppercase(MAC) )[0:8]      (model = DCS-6501LH)

The value is generated and written into the persistent account store during MAC provisioning by the vendor's
own code in `/mnt/mtd/aoni_ipc`, and the boot path starts the Telnet daemon unless a suppression file is
present:

    mydlink_open_telnet():  if !exists("/mnt/sd_card/telnet_open")  ->  socket_system("telnetd &")

i.e. Telnet is enabled by default and the flag file suppresses it. An attacker who can reach TCP/23 and knows
(or observes) the device MAC address can compute the root password offline and log in as root without any
secret. Both inputs are public: the model is fixed for the product and the MAC is printed on the label,
visible to any host on the same segment, and readable from the device itself.

## Details

- Trigger chain (provisioning path): `pf_cfg_is_product_mode(0x47c7e0)` -> ... ->
  `produst_set_mac_addr(0x4834e8) -> mydlink_set_dev_mac(0x4912bc) -> mydlink_set_root_pwd(0x4911a8)`.
- Password generation (`mydlink_set_root_pwd`; command strings taken verbatim from `.rodata`):

      socket_system( echo -n "%s-%s" > %s )                -> /tmp/tmp_pwd
      socket_system( echo `md5sum %s | head -c 8` > %s )   -> /tmp/pwd
      socket_system( echo `md5sum %s | head -c 8` >> %s )  -> /tmp/pwd
      socket_system( passwd root < %s )                    -> root account

- Telnet startup (`mydlink_open_telnet 0x497180`, called from `pf_mydlink_init 0x497a2c` at boot):
  `is_file_exist("/mnt/sd_card/telnet_open")`; if absent, `socket_system("telnetd &")`.
- Example: input `DCS-6501LH-12:32:45:78:45:22` -> md5 `7b4e9a9a67cfc3c4352bdedc399813d2` -> password `7b4e9a9a`.
- Authentication consumer: the firmware BusyBox telnetd spawns `/bin/login`, which authenticates root
  against the account store (`/mnt/conf/passwd`, `/mnt/conf/shadow`).

## Verification

The vendor BusyBox executed exactly the four commands the vendor binary generates, producing
`/mnt/conf/passwd` = `root:p5nfaUpna5nGw:20710:0:root:/root:/bin/sh`; `crypt("7b4e9a9a","p5")` equals
`p5nfaUpna5nGw`, i.e. the stored root password is the predicted value. The firmware BusyBox then executed the
vendor command `telnetd &` (Telnet listening on `*:23`). A real Telnet login with `root` / `7b4e9a9a` passes
the password check, while `root` / `wrongpass123` returns `Login incorrect`. Evidence:
[`evidence/03-runtime-verification.txt`](evidence/03-runtime-verification.txt).

## Proof of concept

- `poc/poc_dcs6501lh_root_pwd.py` - password derivation tool (MD5(model-MAC)[0:8]).
- `poc/poc_telnet_login2.py` - real Telnet login client (telnetlib, IAC aware).

```sh
python3 poc/poc_dcs6501lh_root_pwd.py 12:32:45:78:45:22
python3 poc/poc_telnet_login2.py <camera-ip> 23 root 7b4e9a9a        # password accepted
python3 poc/poc_telnet_login2.py <camera-ip> 23 root wrongpass123    # Login incorrect
```

## Firmware

- Package: `DCS6501LHCx_FW303B02_SD.zip`, application version V3.03.02 (built 2025-08-04; Ingenic T31).
- Download: <https://support.dlink.com/resource/PRODUCTS/DCS-6501LH/REVC/DCS6501LHCx_FW303B02_SD.zip>
- SHA-256: package `8751e1219ddfd839f59a3b01b2ecace2ecf3c9b95cc83f8278886bc87e0652c1`;
  image `fdaf265736eab61ec8b5e4849db6c75129cb5123bdb271603eab191f636b8471`;
  `/mnt/mtd/aoni_ipc` `8f010ddcdf27853e3048971e770611d5261b8caa5f53ce8e6b96393b54a2c559`;
  `rootfs/bin/busybox` `aa380fa2ed91caf2c8841c3121492754725ebb7e1df1eb6382d6ec0876f07200`.

## Classification

CWE-798 Use of Hard-coded Credentials; CWE-259 Use of Hard-coded Password; CWE-1391 Use of Weak
Credentials. CVSS 3.1: `CVSS:3.1/AV:A/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` (8.8).

## Vendor coordination

Reported to D-Link SIRT (security@dlink.com). No CVE had been assigned when this package was prepared.
