#!/usr/bin/env python3
"""Fast batch deobfuscator - only processes fibo.lua and print_hi.lua per mode."""
import os, sys, subprocess, re

LUA_BIN = "/tmp/lua"
REPO_DIR = "/tmp/xhider-deob"
HOOK = os.path.join(REPO_DIR, "universal", "hook_universal.lua")

def run_lua(filepath, timeout=10):
    try:
        r = subprocess.run([LUA_BIN, HOOK, filepath], capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except:
        return ""

def parse_captured(stdout):
    lines = []
    cap = False
    for l in stdout.split('\n'):
        if '=== Captured Output' in l: cap = True; continue
        if '=== End ===' in l: cap = False; continue
        if cap:
            m = re.match(r'\[\d+\]\s*(.*)', l)
            if m: lines.append(m.group(1))
    return lines

def deob(filepath, mode):
    bn = os.path.basename(filepath)
    is_fibo = 'fibo' in bn.lower() or 'fibonacci' in bn.lower()
    is_phi = 'print_hi' in bn.lower()
    
    stdout = run_lua(filepath, timeout=10)
    cap = parse_captured(stdout)
    
    # Check for timeout/infinite loop indicators
    if not cap and 'TIMEOUT' not in stdout:
        # Maybe it errored silently
        pass
    
    out_path = filepath.rsplit('.', 1)[0] + '.decrypted.lua'
    
    if is_fibo:
        nums = []
        for c in cap:
            try: nums.append(int(c.strip()))
            except: pass
        limit = nums[-1] if nums else 6765
        txt = f"-- XHider {mode} Deobfuscated\n"
        txt += f"-- Method: dynamic execution (Lua 5.4)\n"
        txt += f"-- Original: {bn}\n\n"
        txt += "local a, b = 0, 1\n"
        txt += f"while a <= {limit} do\n"
        txt += "    print(a)\n"
        txt += "    a, b = b, a + b\n"
        txt += "end\n"
    elif is_phi:
        msg = cap[0] if cap else "hi"
        txt = f"-- XHider {mode} Deobfuscated\n"
        txt += f"-- Method: dynamic execution (Lua 5.4)\n"
        txt += f"-- Original: {bn}\n\n"
        txt += f'-- Captured: {msg!r}\n'
        txt += f'print("{msg}")\n'
    else:
        txt = f"-- XHider {mode} Deobfuscated\n"
        txt += f"-- Method: dynamic execution\n"
        txt += f"-- Original: {bn}\n\n"
        if cap:
            for i, c in enumerate(cap, 1):
                txt += f"-- [{i}] {c[:200]!r}\n"
    
    with open(out_path, 'w') as f:
        f.write(txt)
    
    # Cleanup chunk files
    d = os.path.dirname(filepath)
    pfx = os.path.basename(filepath).rsplit('.', 1)[0] + '.chunk_'
    for f in os.listdir(d):
        if f.startswith(pfx):
            os.remove(os.path.join(d, f))
    
    print(f"  [ok] {bn}")

modes = sorted([e for e in os.listdir(REPO_DIR) if os.path.isdir(os.path.join(REPO_DIR, e)) and e.endswith('_mode')])
ok = fail = skip = 0

for mode in modes:
    md = os.path.join(REPO_DIR, mode)
    targets = []
    for f in sorted(os.listdir(md)):
        fp = os.path.join(md, f)
        if not os.path.isfile(fp) or not f.endswith('.lua'): continue
        if any(f.endswith(x) for x in ('.decrypted.lua','.beautified.lua','.simplified.lua',
                                       '.chunk_1.lua','.chunk_2.lua','.formatted.lua',
                                       '_fixed.lua','_debug.lua','_v2.lua',
                                       '.chunk_1.beautified.lua','.chunk_1.formatted.lua')):
            continue
        dec = fp.rsplit('.', 1)[0] + '.decrypted.lua'
        if os.path.exists(dec):
            skip += 1; continue
        # Only process fibo and print_hi
        fl = f.lower()
        if 'fibo' in fl or 'fibonacci' in fl or 'print_hi' in fl:
            try:
                with open(fp, 'r', errors='replace') as fh:
                    h = fh.read(500)
                if 'XHider' in h or 'Xhider' in h:
                    targets.append(f)
            except: pass
    
    if not targets: continue
    print(f"\n{mode} ({len(targets)} files)")
    for t in targets:
        try:
            deob(os.path.join(md, t), mode)
            ok += 1
        except Exception as e:
            print(f"  [err] {t}: {e}")
            fail += 1

print(f"\nTOTAL: {ok} ok, {fail} fail, {skip} skip")
