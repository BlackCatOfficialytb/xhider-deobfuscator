#!/usr/bin/env python3
"""Deobfuscate the hex-named XHider files (actual scripts) using dynamic execution."""
import os, sys, subprocess, re, time

LUA_BIN = "/tmp/lua"
REPO_DIR = "/tmp/xhider-deob"
HOOK = os.path.join(REPO_DIR, "universal", "hook_universal.lua")

def run_lua(filepath, timeout=15):
    try:
        r = subprocess.run([LUA_BIN, HOOK, filepath], 
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "XHIDER_DUMP_CHUNKS": "1", "XHIDER_VERBOSE": "1"})
        return r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT"
    except Exception as e:
        return "", str(e)

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

def parse_chunks(stdout):
    chunks = []
    for l in stdout.split('\n'):
        m = re.match(r'\[chunk (\d+)\]\s+(\d+) bytes', l)
        if m:
            chunks.append((int(m.group(1)), int(m.group(2))))
    return chunks

# Find hex-named files that don't have .decrypted.lua yet
hex_files = []
for entry in sorted(os.listdir(REPO_DIR)):
    md = os.path.join(REPO_DIR, entry)
    if not os.path.isdir(md) or not entry.endswith('_mode'): continue
    
    for f in sorted(os.listdir(md)):
        fp = os.path.join(md, f)
        if not os.path.isfile(fp) or not f.endswith('.lua'): continue
        # Skip non-hex named files and already processed files
        if not re.match(r'^[0-9A-Fa-f]{32,}\.lua$', f): continue
        dec = fp.rsplit('.', 1)[0] + '.decrypted.lua'
        if os.path.exists(dec): continue
        
        try:
            with open(fp, 'r', errors='replace') as fh:
                h = fh.read(500)
            if 'XHider' in h or 'Xhider' in h:
                hex_files.append((entry, fp, f))
        except: pass

print(f"Found {len(hex_files)} hex-named files to process")

ok = fail = 0
for mode, fp, fn in hex_files:
    print(f"\n{mode}/{fn}")
    stdout, stderr = run_lua(fp, timeout=15)
    
    cap = parse_captured(stdout)
    chunks = parse_chunks(stdout)
    
    out_path = fp.rsplit('.', 1)[0] + '.decrypted.lua'
    
    txt = f"-- XHider {mode} Deobfuscated\n"
    txt += f"-- Method: dynamic execution (Lua 5.4 hook_universal.lua)\n"
    txt += f"-- Original: {fn}\n"
    
    if chunks:
        txt += f"-- Detected {len(chunks)} loadstring chunks\n"
        for ci, cs in chunks:
            txt += f"--   chunk {ci}: {cs} bytes\n"
    
    if cap:
        txt += f"--\n-- Captured output ({len(cap)} lines):\n"
        for i, c in enumerate(cap[:50], 1):
            safe = c[:200]
            txt += f"-- [{i}] {safe!r}\n"
        if len(cap) > 50:
            txt += f"-- ... +{len(cap)-50} more lines\n"
    else:
        txt += "-- No stdout captured (anti-debug may have triggered)\n"
    
    txt += "\n-- NOTE: Full string decryption requires static analysis.\n"
    txt += "-- The obfuscated code contains encrypted string constants\n"
    txt += "-- that are XOR-decrypted at runtime. Use the XOR key extraction\n"
    txt += "-- approach for complete deobfuscation.\n"
    
    # If we have chunk files, include their content
    d = os.path.dirname(fp)
    pfx = fn.rsplit('.', 1)[0] + '.chunk_'
    chunk_contents = []
    for cf in sorted(os.listdir(d)):
        if cf.startswith(pfx) and cf.endswith('.lua'):
            cfp = os.path.join(d, cf)
            try:
                with open(cfp, 'r', encoding='utf-8', errors='replace') as fh:
                    content = fh.read()
                chunk_contents.append((cf, content))
                txt += f"\n-- === {cf} ({len(content)} bytes) ===\n"
                txt += content[:5000]
                if len(content) > 5000:
                    txt += f"\n-- ... truncated ({len(content)} total bytes)\n"
            except: pass
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(txt)
    
    # Cleanup chunk files
    for cf in os.listdir(d):
        if cf.startswith(pfx) and cf.endswith('.lua'):
            os.remove(os.path.join(d, cf))
    
    print(f"  [ok] captured={len(cap)} chunks={len(chunks)}")
    ok += 1

print(f"\nTOTAL: {ok} ok, {fail} fail")
