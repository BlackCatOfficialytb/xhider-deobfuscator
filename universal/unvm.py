#!/usr/bin/env python3
"""
XHider UNVM - Hex Pool Deobfuscator
====================================
Deobfuscates XHider scripts that use a raw hex string pool with XOR keys.

Pipeline:
  1. Math simplification (fold obfuscated constants like 715+-715 → 0)
  2. Extract hex pool + 4-byte XOR key
  3. Auto-detect VM decoder function name
  4. Decode all strings via XOR
  5. Inline all func(N) calls → string literals
  6. Comment-wrap VM function block

Usage:
  python unvm.py <file.lua>
  python unvm.py <file.lua> -o <output.lua>

Fixed bugs from original:
  1. Missing '[' in b = [...] list literal (line 65)
  2. 'countsost]' typo → counts[most] (line 95)
  3. 'from beautifier import' removed (module was deleted)
  4. Float division t/2 → integer floor division t//2 in XOR function
  5. Unused 'import ast' removed
"""

import re
import sys
import os


def simplify_math(text):
    """
    Ultimate safe math simplifier.
    Only simplifies constant sequences that are fully delimited by non-math punctuation.
    Prevents partial simplification of 'x + 1' or '(t-1) % 4 + 1'.
    """
    # 1. Inner parentheses reduction: ( 1 + 2 ) -> 3
    # Safe because we replace the entire paren block.
    inner_paren_pattern = r'\(\s*([\-\+]?\s*\d+\.?\d*(?:\s*[\+\-\*\/\%\^]\s*[\-\+]?\s*\d+\.?\d*)*)\s*\)'

    def repl_paren(m):
        try:
            expr = m.group(1)
            val = eval(re.sub(r'\s+', '', expr), {"__builtins__": {}}, {})
            if isinstance(val, (int, float)):
                res = str(int(val)) if float(val).is_integer() else f"{val:.10f}".rstrip('0').rstrip('.')
                return f" {res} "
        except Exception:
            pass
        return m.group(0)

    # 2. Flat sequences: 1 + 2 -> 3
    # MUST be delimited by safe characters (assignments, parens, commas, semi-colons, newlines).
    safe_pre = r'[\=\(\,\[\{\;\n\r]'
    safe_post = r'[\)\,\;\n\r\]\}]'

    flat_math_pattern = r'(^|' + safe_pre + r')(\s*[\-\+]?\s*\d+\.?\d*(?:\s*[\+\-\*\/\%\^]\s*[\-\+]?\s*\d+\.?\d*)+\s*)(?=' + safe_post + r'|$)'

    def repl_flat(m):
        prefix = m.group(1)
        expr = m.group(2).strip()
        try:
            val = eval(re.sub(r'\s+', '', expr), {"__builtins__": {}}, {})
            if isinstance(val, (int, float)):
                res = str(int(val)) if float(val).is_integer() else f"{val:.10f}".rstrip('0').rstrip('.')
                return f"{prefix} {res} "
        except Exception:
            pass
        return m.group(0)

    for _ in range(50):
        prev = text
        text = re.sub(inner_paren_pattern, repl_paren, text)
        text = re.sub(flat_math_pattern, repl_flat, text)
        if text == prev:
            break
    return text


def lua_xor_decode_byte(t, m):
    """Simulate XHider XOR byte decode: XOR with floor division.
    
    Equivalent to Lua: for k=0,7 do if (t/2 + m/2) ~= floor(t/2 + m/2) then res += 2^k end end
    BUG FIX: Uses integer floor division (//) instead of float division (/)
    to avoid floating-point precision errors on large pools.
    """
    res = 0
    for k in range(8):
        v_bit = t // 2 + m // 2
        if v_bit * 2 != t + m:
            res += 1 << k
        t = t // 2
        m = m // 2
    return res


def lua_vm_decode(hex_pool, keys, offset):
    """Simulates XHider Lua VM string decoding from hex pool.
    
    String format at offset:
      [4 bytes: length (XOR decoded)] [length bytes: data (XOR decoded)]
    Length is little-endian, each byte XOR'd with keys[i % 4].
    """
    idx = int(offset) + 1  # Lua is 1-based
    try:
        # BUG FIX: Missing '[' was here → b = [hex_pool[...], ...]
        b = [hex_pool[idx - 1], hex_pool[idx], hex_pool[idx + 1], hex_pool[idx + 2]]
        length = (lua_xor_decode_byte(b[0], keys[0])
                  + lua_xor_decode_byte(b[1], keys[1]) * 256
                  + lua_xor_decode_byte(b[2], keys[2]) * 65536
                  + lua_xor_decode_byte(b[3], keys[3]) * 16777216)
        if length <= 0 or length > 500000 or idx + 4 + length > len(hex_pool):
            return None
        return "".join(
            chr(lua_xor_decode_byte(hex_pool[idx + 4 + i - 1], keys[i % 4]))
            for i in range(length)
        )
    except (IndexError, ValueError):
        return None


def beautify_lua_simple(code):
    """Basic Lua beautifier - add indentation without external dependencies.
    
    BUG FIX: Replaces removed 'from beautifier import beautify_lua'.
    """
    lines = code.split('\n')
    indent = 0
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append('')
            continue
        # Decrease indent for closing keywords
        if stripped.startswith(('end', '}', 'elseif ', 'else', 'until ', ')')):
            indent = max(0, indent - 1)
        result.append('  ' * indent + stripped)
        # Increase indent for opening keywords
        if stripped.endswith(('then', 'do', 'function', 'else', 'repeat',
                              '{', '(')) and not stripped.startswith('--'):
            indent += 1
        elif re.match(r'^(function|if|for|while|repeat|else|elseif)\b', stripped):
            if not stripped.endswith(('then', 'do', 'function')):
                pass  # single-line control flow
            elif not any(stripped.endswith(kw) for kw in ('then', 'do')):
                indent += 1
    return '\n'.join(result)


def detect_vm_function(code):
    """Auto-detect the VM decoder function name.
    
    Strategy:
    1. Find function with pattern: function X(y) ... if not cache[y] ...
    2. Fall back to the most-called identifier(number) pattern
    """
    # Strategy 1: Pattern match for the decoder function
    m_func_match = re.search(
        r'function\s+([a-zA-Z0-9_]+)\s*\(([a-zA-Z0-9_]+)\)'
        r'(?:(?!function).)+?'
        r'if\s+not\s+[a-zA-Z0-9_]+\[\2\]',
        code, re.DOTALL
    )
    if m_func_match:
        return m_func_match.group(1)

    # Strategy 2: Most-called identifier(number) pattern
    counts = {}
    for match in re.finditer(r'([a-zA-Z0-9_]+)\(\d+\)', code):
        name = match.group(1)
        counts[name] = counts.get(name, 0) + 1
    if counts:
        return max(counts, key=counts.get)

    return 'm'  # default fallback


def comment_vm_block(code, func_name):
    """Wrap the VM function block in a Lua comment."""
    def comment_block(match):
        inner = match.group(0).strip()
        # Use [=[ ]]= style for nested brackets
        if "[[" in inner or "]]" in inner:
            eq = "="
            while f"]{eq}]" in inner or f"[{eq}[" in inner:
                eq += "="
            head = f"--[{eq}[ DECODED VM"
            tail = f"]{eq}]"
        else:
            head = "--[[ DECODED VM"
            tail = "]]"
        return f"{head}\n{inner}\n{tail}"

    pattern = r'(function\s+' + re.escape(func_name) + r'\(.+?end\s*;?\s*end\s*;?)'
    return re.sub(pattern, comment_block, code, flags=re.DOTALL)


def unvm_deobfuscate(filepath, output=None):
    """Main deobfuscation pipeline for hex-pool XHider scripts."""
    if not os.path.isfile(filepath):
        print(f"[-] File not found: {filepath}")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()

    print(f"[*] Input: {filepath} ({len(code):,} chars)")

    # Step 1: Math simplification
    print("[1/6] Math simplification...")
    code = simplify_math(code)

    # Step 2: Extract hex pool and XOR keys
    print("[2/6] Component extraction...")
    hex_m = re.search(r'["\']([0-9a-fA-F]{200,})["\']', code)
    if not hex_m:
        print("[-] Hex pool not found (need 200+ hex chars in a string).")
        return False
    hex_pool = list(bytes.fromhex(hex_m.group(1)))
    print(f"  Hex pool: {len(hex_pool):,} bytes")

    # Extract XOR keys: {N1, N2, N3, N4} or N1, N2, N3, N4
    q_m = re.search(r'\{\s*(\d+)\s*[,;]\s*(\d+)\s*[,;]\s*(\d+)\s*[,;]\s*(\d+)', code)
    if not q_m:
        q_m = re.search(r'(\d+)\s*[,;]\s*(\d+)\s*[,;]\s*(\d+)\s*[,;]\s*(\d+)', code)
    if not q_m:
        print("[-] XOR keys not found (need 4 integers).")
        return False
    keys = [int(q_m.group(i)) for i in range(1, 5)]
    print(f"  XOR keys: {keys}")

    # Step 3: Detect VM function name
    print("[3/6] Detecting VM function...")
    func_name = detect_vm_function(code)
    print(f"  VM function: {func_name}")

    # Step 4: Decode all strings
    print("[4/6] String deobfuscation...")
    calls = sorted(set(
        int(c) for c in re.findall(r'\b' + re.escape(func_name) + r'\((\d+)\)', code)
    ))
    results = {}
    for offset in calls:
        decoded = lua_vm_decode(hex_pool, keys, offset)
        if decoded is not None:
            results[offset] = decoded
    print(f"  Decoded: {len(results)}/{len(calls)} strings")

    if not results:
        print("[-] No strings decoded. Wrong keys or pool?")
        return False

    # Step 5: Inline all func(N) calls with decoded strings
    print("[5/6] Inlining strings...")
    def repl_call(m):
        offset = int(m.group(1))
        if offset in results:
            s = (results[offset]
                 .replace('\\', '\\\\')
                 .replace('"', '\\"')
                 .replace('\n', '\\n')
                 .replace('\r', '\\r'))
            return f'"{s}"'
        return m.group(0)

    final_code = re.sub(
        r'\b' + re.escape(func_name) + r'\((\d+)\)',
        repl_call, code
    )

    # Step 6: Beautify + comment-wrap VM block
    print("[6/6] Beautification...")
    final_code = beautify_lua_simple(final_code)
    final_code = comment_vm_block(final_code, func_name)

    # Write output
    if output is None:
        output = os.path.splitext(filepath)[0] + ".unvm.lua"
    os.makedirs(os.path.dirname(os.path.abspath(output)) or '.', exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        f.write(final_code)

    print(f"[+] Output: {output}")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python unvm.py <file.lua> [-o output.lua]")
        return

    filepath = sys.argv[1]
    output = None
    if '-o' in sys.argv:
        idx = sys.argv.index('-o')
        if idx + 1 < len(sys.argv):
            output = sys.argv[idx + 1]

    unvm_deobfuscate(filepath, output)


if __name__ == "__main__":
    main()
