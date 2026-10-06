#!/usr/bin/env python3
"""真实 telnet 登录（telnetlib，处理 IAC 协商）"""
import sys, time, telnetlib
host, port, user, pw = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
try:
    tn = telnetlib.Telnet(host, port, timeout=15)
except Exception as e:
    print(f"==> 连接失败: {type(e).__name__} {e}"); sys.exit(0)
def rd(pat=b'', t=8):
    try: return tn.read_until(pat, t) if pat else tn.read_very_eager()
    except Exception: return b''
out = rd(b'login:', 12)
print(f'[banner/login-prompt] {out!r}')
if b'login:' not in out.lower():
    tn.close(); print('==> 结果: NO-LOGIN-PROMPT'); sys.exit(0)
tn.write(user.encode()+b'\n')
o2 = rd(b'password:', 10); print(f'[password-prompt] {o2!r}')
tn.write(pw.encode()+b'\n')
time.sleep(1.5)
tn.write(b'id; uname -a; cat /etc/hostname 2>/dev/null; exit\n')
time.sleep(2.0)
o3 = rd(t=5); print(f'[session] {o3!r}')
res = 'SUCCESS(uid=0)' if b'uid=0' in o3 else ('REJECTED/NO-SHELL' if b'incorrect' in o3.lower() or b'login' in o3.lower() else 'UNKNOWN')
print(f'==> 结果: {res}')
tn.close()
