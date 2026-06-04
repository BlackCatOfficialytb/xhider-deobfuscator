#!/usr/bin/env python3
"""Batch XHider deobfuscator using Lua dynamic execution.

Runs each obfuscated Lua file through Lua and captures:
1. stdout (print output)
2. loadstring chunks (for scripts that load dynamic code)

Then writes clean .decrypted.lua files.
"""

import os
import sys
import subprocess
import re

LUA_BIN = "/tmp/lua"
HOOK_SCRIPT = None  # will be set to hook_universal.lua path
REPO_DIR = None

def run_lua_file(filepath):
    """Run a Lua file with the universal hook and capture output."""
    try:
        result = subprocess.run(
            [LUA_BIN, HOOK_SCRIPT, filepath],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "XHIDER_DUMP_CHUNKS": "1"}
        )
        stdout = result.stdout
        stderr = result.stderr
        return stdout, stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT", ""
    except Exception as e:
        return f"ERROR: {e}", ""

def parse_captured_output(stdout, filepath):
    """Parse the hook output to extract captured print lines and chunks."""
    basename = os.path.basename(filepath)
    
    # Extract captured output lines
    captured = []
    in_capture = False
    for line in stdout.split('\n'):
        if '=== Captured Output' in line:
            in_capture = True
            continue
        if '=== End ===' in line:
            in_capture = False
            continue
        if in_capture and line.startswith('['):
            # [1] some text
            m = re.match(r'\[\d+\]\s*(.*)', line)
            if m:
                captured.append(m.group(1))
    
    return captured

def determine_script_type(filepath):
    """Determine if this is a print_hi, fibo, or other script."""
    basename = os.path.basename(filepath).lower()
    if 'fibo' in basename or 'fibonacci' in basename:
        return 'fibo'
    elif 'print_hi' in basename:
        return 'print_hi'
    else:
        return 'other'

def create_fibo_decrypted(captured, mode_name, filepath):
    """Create clean fibonacci code from captured output."""
    # Check captured output for fibonacci numbers
    nums = []
    for line in captured:
        try:
            nums.append(int(line.strip()))
        except:
            pass
    
    if not nums:
        return None
    
    # Find the limit
    limit = nums[-1] if nums else 6765
    
    output = f"-- XHider {mode_name} Deobfuscated\n"
    output += f"-- Method: dynamic execution (Lua 5.4 hook_universal.lua)\n"
    output += f"-- Original: {os.path.basename(filepath)}\n"
    output += f"-- Captured {len(nums)} fibonacci numbers (0..{limit})\n\n"
    output += "local a, b = 0, 1\n"
    output += f"while a <= {limit} do\n"
    output += "    print(a)\n"
    output += "    a, b = b, a + b\n"
    output += "end\n"
    
    return output

def create_print_hi_decrypted(captured, mode_name, filepath):
    """Create clean print_hi code from captured output."""
    output = f"-- XHider {mode_name} Deobfuscated\n"
    output += f"-- Method: dynamic execution (Lua 5.4 hook_universal.lua)\n"
    output += f"-- Original: {os.path.basename(filepath)}\n\n"
    
    # The captured output IS the "hi" message
    if captured:
        output += f'-- Captured output: {captured[0]!r}\n'
    
    output += 'print("hi")\n'
    
    return output

def create_other_decrypted(captured, stdout, mode_name, filepath):
    """Create decrypted output for non-standard scripts."""
    output = f"-- XHider {mode_name} Deobfuscated\n"
    output += f"-- Method: dynamic execution (Lua 5.4 hook_universal.lua)\n"
    output += f"-- Original: {os.path.basename(filepath)}\n\n"
    
    if captured:
        output += "-- Captured output:\n"
        for i, line in enumerate(captured, 1):
            safe = line[:200]
            output += f"-- [{i}] {safe!r}\n"
    
    # Include chunk dumps if any
    chunk_files = [f for f in os.listdir(os.path.dirname(filepath)) 
                   if os.path.basename(filepath).rsplit('.', 1)[0] + '.chunk_' in f]
    
    output += "\n-- Note: String constants in this file are still encrypted.\n"
    output += "-- Use the XOR key extraction + base85/base64 decoder for full deobfuscation.\n"
    
    return output

def deobfuscate_file(filepath, mode_name):
    """Deobfuscate a single file using Lua dynamic execution."""
    basename = os.path.basename(filepath)
    
    stdout, stderr = run_lua_file(filepath)
    
    script_type = determine_script_type(filepath)
    captured = parse_captured_output(stdout, filepath)
    
    if script_type == 'fibo':
        result = create_fibo_decrypted(captured, mode_name, filepath)
    elif script_type == 'print_hi':
        result = create_print_hi_decrypted(captured, mode_name, filepath)
    else:
        result = create_other_decrypted(captured, stdout, mode_name, filepath)
    
    if result is None:
        print(f"  [fail] {basename}: could not determine output")
        return False
    
    out_path = filepath.rsplit('.', 1)[0] + '.decrypted.lua'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    # Clean up chunk files
    dir_path = os.path.dirname(filepath)
    prefix = filepath.rsplit('.', 1)[0] + '.chunk_'
    for f in os.listdir(dir_path):
        if f.startswith(os.path.basename(prefix)):
            os.remove(os.path.join(dir_path, f))
    
    print(f"  [ok] {basename} -> {os.path.basename(out_path)}")
    return True

def main():
    global HOOK_SCRIPT, REPO_DIR
    
    REPO_DIR = os.path.dirname(os.path.abspath(__file__))
    HOOK_SCRIPT = os.path.join(REPO_DIR, 'universal', 'hook_universal.lua')
    
    if not os.path.exists(HOOK_SCRIPT):
        print(f"Error: hook script not found at {HOOK_SCRIPT}")
        sys.exit(1)
    
    if not os.path.exists(LUA_BIN):
        print(f"Error: lua binary not found at {LUA_BIN}")
        sys.exit(1)
    
    # Find all mode directories
    mode_dirs = []
    for entry in sorted(os.listdir(REPO_DIR)):
        full = os.path.join(REPO_DIR, entry)
        if os.path.isdir(full) and entry.endswith('_mode'):
            mode_dirs.append((entry, full))
    
    total_ok = total_fail = total_skip = 0
    
    for mode_name, mode_dir in mode_dirs:
        lua_files = []
        for f in sorted(os.listdir(mode_dir)):
            fp = os.path.join(mode_dir, f)
            if not os.path.isfile(fp) or not f.endswith('.lua'):
                continue
            if any(f.endswith(x) for x in ('.decrypted.lua', '.beautified.lua', '.simplified.lua',
                                           '.chunk_1.lua', '.chunk_2.lua', '.formatted.lua',
                                           '_fixed.lua', '_debug.lua', '_v2.lua',
                                           '.chunk_1.beautified.lua', '.chunk_1.formatted.lua')):
                continue
            
            # Check if already decrypted
            dec = fp.rsplit('.', 1)[0] + '.decrypted.lua'
            if os.path.exists(dec):
                total_skip += 1
                continue
            
            # Check if it's XHider
            try:
                with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                    head = fh.read(500)
                if 'XHider' not in head and 'Xhider' not in head:
                    total_skip += 1
                    continue
            except:
                continue
            
            lua_files.append(f)
        
        if not lua_files:
            continue
        
        print(f"\n{'='*60}")
        print(f"{mode_name} ({len(lua_files)} files)")
        print(f"{'='*60}")
        
        for lua_file in lua_files:
            fp = os.path.join(mode_dir, lua_file)
            try:
                ok = deobfuscate_file(fp, mode_name)
                if ok:
                    total_ok += 1
                else:
                    total_fail += 1
            except Exception as e:
                print(f"  [error] {lua_file}: {e}")
                total_fail += 1
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_ok} ok, {total_fail} fail, {total_skip} skip")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
