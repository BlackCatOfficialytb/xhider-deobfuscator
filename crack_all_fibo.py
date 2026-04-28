"""
Crack all XHider fibo.lua files across all modes.
"""

import re
import math
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ==================== SHARED UTILITIES ====================

def lua_eval(expr):
    try:
        expr = str(expr).replace('\n', ' ').strip()
        if not expr: return None
        r = eval(expr, {"__builtins__": None, "math": math})
        if isinstance(r, float): return int(r)
        return int(r)
    except:
        return None

def lua_unescape(s):
    res = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == '\\' and i + 1 < n:
            nc = s[i+1]
            if nc.isdigit():
                d = nc; j = i + 2
                while j < n and j < i + 4 and s[j].isdigit():
                    d += s[j]; j += 1
                res.append(chr(int(d))); i = j
            elif nc == 'n': res.append('\n'); i += 2
            elif nc == 'r': res.append('\r'); i += 2
            elif nc == 't': res.append('\t'); i += 2
            elif nc == '\\': res.append('\\'); i += 2
            elif nc == '"': res.append('"'); i += 2
            elif nc == "'": res.append("'"); i += 2
            else: res.append(nc); i += 2
        else:
            res.append(c); i += 1
    return "".join(res)

def decode_xhd_payload(raw_str):
    s = raw_str[4:] if raw_str.startswith("XHD:") else raw_str
    s = s.replace("z", "!!!!!")
    s = re.sub(r'[\s\r\n]', '', s)
    result = []
    i = 0
    while i < len(s):
        block_size = min(5, len(s) - i)
        val = 0
        for j in range(block_size):
            val = val * 0x55 + (ord(s[i + j]) - 0x21)
        for j in range(block_size, 5):
            val = val * 0x55 + 0x54
        result.extend([(val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF])
        i += block_size
    return result

def extract_key_map(content):
    best_map = {}
    for m in re.finditer(r'\{([^{}]{200,})\}', content):
        block = m.group(1)
        km = {}
        for entry in re.finditer(r'(?:\["([^"]+)"\]|(\b[a-zA-Z_]\b))\s*=\s*([^,;}\]]+)', block):
            key = entry.group(1) if entry.group(1) else entry.group(2)
            if len(key) != 1: continue
            val = lua_eval(entry.group(3).strip())
            if val is not None and 0 <= val <= 63:
                km[key] = val
        if len(km) > len(best_map):
            best_map = km
    return best_map

def decode_base64_custom(encoded_str, key_map):
    buf = 0
    cnt = 0
    result = []
    for ch in encoded_str:
        if ch == '=':
            if cnt == 2:
                result.append((buf >> 4) & 0xFF)
            elif cnt == 3:
                result.append((buf >> 10) & 0xFF)
                result.append((buf >> 2) & 0xFF)
            break
        if ch not in key_map: continue
        buf = (buf << 6) | key_map[ch]
        cnt += 1
        if cnt == 4:
            result.extend([(buf >> 16) & 0xFF, (buf >> 8) & 0xFF, buf & 0xFF])
            buf = 0; cnt = 0
    return "".join(chr(b) for b in result)

def extract_shuffle_pairs(content):
    pairs = []
    m = re.search(r'ipairs\(\{(.*?)\}\s*\)\s*do', content, re.DOTALL)
    if not m: return pairs
    raw = re.split(r'\}\s*,\s*\{', m.group(1).replace('\n', ' '))
    for p_str in raw:
        p_str = p_str.replace('{', '').replace('}', '')
        parts = re.split(r'[;,]', p_str)
        if len(parts) >= 2:
            s = lua_eval(parts[0]); e = lua_eval(parts[1])
            if s and e and s > 0 and e > 0: pairs.append((s, e))
    return pairs

def apply_shuffle(lst, pairs):
    for start, end_val in pairs:
        s, e = start - 1, end_val - 1
        if s < 0: s = 0
        if e >= len(lst): e = len(lst) - 1
        while s < e:
            lst[s], lst[e] = lst[e], lst[s]; s += 1; e -= 1

def write_output(output_file, mode, strings, input_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"-- Decrypted from: {os.path.basename(input_file)}\n")
        f.write(f"-- Mode: {mode}\n")
        f.write(f"-- Strings found: {len(strings)}\n\n")
        for i, s in enumerate(strings):
            safe = s.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            f.write(f"[{i}] {safe}\n")
    print(f"  Extracted {len(strings)} strings")
    for i, s in enumerate(strings[:30]):
        safe = s.replace('\n', '\\n').replace('\r', '\\r')[:80]
        try: print(f"    [{i}] {safe}")
        except: print(f"    [{i}] <binary>")
    if len(strings) > 30:
        print(f"    ... and {len(strings)-30} more")


# ==================== BASIC MODE ====================

def crack_basic(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    xhd = re.search(r'\[=\[(XHD:.*?)\]=\]', content, re.DOTALL)
    if not xhd: xhd = re.search(r'"(XHD:.*?)"', content, re.DOTALL)
    if not xhd:
        print("  [!] No XHD payload"); return False
    data = decode_xhd_payload(xhd.group(1))
    print(f"  Decoded {len(data)} bytes")
    km = re.search(r'\{(0x[0-9A-Fa-f]+)[;,]\s*(0x[0-9A-Fa-f]+)[;,]\s*(0x[0-9A-Fa-f]+)[;,]\s*(0x[0-9A-Fa-f]+)\}', content)
    keys = [int(km.group(i), 16) for i in range(1, 5)] if km else [0xF5, 0xD1, 0xC6, 0xC5]
    print(f"  Keys: {[hex(k) for k in keys]}")
    strings = []
    pos = 0
    while pos + 4 <= len(data):
        length = (data[pos]^keys[0]) + (data[pos+1]^keys[1])*256 + (data[pos+2]^keys[2])*65536 + (data[pos+3]^keys[3])*16777216
        if length < 0 or length > 50000: break
        pos += 4
        chars = [chr(data[pos+j] ^ keys[j%4]) for j in range(length) if pos+j < len(data)]
        strings.append("".join(chars))
        pos += length
    write_output(output_file, "basic", strings, input_file)
    return len(strings) > 0


# ==================== NORMAL / STRONG MODE ====================

def crack_normal_strong(input_file, output_file, mode_name):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract string pool
    pool_match = re.search(r'local\s+(\w+)\s*=\s*\{((?:"[^"]*"[;,\s]*)+)\}', content)
    if not pool_match:
        print("  [!] No string pool"); return False
    pool = [m.group(1) for m in re.finditer(r'"([^"]*)"', pool_match.group(2))]
    print(f"  Found {len(pool)} strings in pool")

    pairs = extract_shuffle_pairs(content)
    if pairs:
        print(f"  Shuffle: {pairs}")
        apply_shuffle(pool, pairs)

    key_map = extract_key_map(content)
    print(f"  {len(key_map)} Base64 keys")

    decoded = [decode_base64_custom(enc, key_map) for enc in pool]
    write_output(output_file, mode_name, decoded, input_file)
    return True


# ==================== HARD MODE ====================

def crack_hard(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract the mixed table (strings + numbers)
    items = extract_mixed_table(content)
    print(f"  Found {len(items)} items in table")

    pairs = extract_shuffle_pairs(content)
    if pairs:
        print(f"  Shuffle: {pairs}")
        apply_shuffle(items, pairs)

    key_map = extract_key_map(content)
    print(f"  {len(key_map)} Base64 keys")

    # Decode strings: shift -49 then Base64
    decoded = []
    for entry in items:
        if entry["type"] == "string":
            bv = parse_lua_bytes(entry["val"])
            shifted = "".join(chr((b - 49) % 256) for b in bv)
            decoded.append(decode_base64_custom(shifted, key_map))
        else:
            decoded.append("")

    result = [s for s in decoded if s]
    write_output(output_file, "hard", result if result else decoded, input_file)
    return len(result) > 0


def extract_mixed_table(content):
    best = []
    for ts in re.finditer(r'local\s+\w+\s*=\s*\{', content):
        start = ts.end()
        depth = 1; i = start; in_q = False; qc = None
        while i < len(content) and depth > 0:
            c = content[i]
            if in_q:
                if c == '\\': i += 1
                elif c == qc: in_q = False
            else:
                if c in ('"', "'"): in_q = True; qc = c
                elif c == '{': depth += 1
                elif c == '}': depth -= 1
            i += 1
        tc = content[start:i-1]
        items = parse_mixed_table(tc)
        str_count = sum(1 for x in items if x["type"] == "string")
        if str_count > sum(1 for x in best if x.get("type") == "string"):
            best = items
    return best

def parse_mixed_table(tc):
    items = []; cur = ""; in_q = False; qc = None; esc = False
    for c in tc:
        if in_q:
            if esc: cur += c; esc = False
            elif c == '\\': cur += c; esc = True
            elif c == qc: cur += c; in_q = False
            else: cur += c
        else:
            if c in ('"', "'"): in_q = True; qc = c; cur += c
            elif c in (',', ';'):
                s = cur.strip()
                if s:
                    if (s.startswith('"') and s.endswith('"')): items.append({"type":"string","val":s})
                    else: items.append({"type":"number","val":lua_eval(s) or 0})
                cur = ""
            else: cur += c
    s = cur.strip()
    if s:
        if (s.startswith('"') and s.endswith('"')): items.append({"type":"string","val":s})
        else: items.append({"type":"number","val":lua_eval(s) or 0})
    return items

def parse_lua_bytes(raw_str):
    s = raw_str[1:-1]; bv = []; i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i+1 < len(s):
            nc = s[i+1]
            if nc.isdigit():
                d = nc; j = i+2
                while j < len(s) and j < i+4 and s[j].isdigit(): d += s[j]; j += 1
                bv.append(int(d)); i = j
            elif nc == 'n': bv.append(10); i += 2
            elif nc == 'r': bv.append(13); i += 2
            elif nc == 't': bv.append(9); i += 2
            elif nc == '\\': bv.append(92); i += 2
            elif nc == '"': bv.append(34); i += 2
            elif nc == "'": bv.append(39); i += 2
            else: bv.append(ord(nc)); i += 2
        else: bv.append(ord(c)); i += 1
    return bv


# ==================== ENV MODE ====================

def crack_env(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Env mode: X[13]=X[14]({Dk={...}}) where Dk contains:
    # - (X[9]+key)({indices, "frag1", "frag2"}) calls
    # - Plain strings like "lMg"
    # Find the Dk={ start
    dk_match = re.search(r'Dk\s*=\s*\{', content)
    if not dk_match:
        print("  [!] No Dk table found"); return False

    start = dk_match.end()
    strings = parse_string_pool_with_calls(content, start, r'\(X\[\d+\]\s*[+\-]\s*[\d\s\+\-\*\/\(\)]+\)\s*\(\{')

    print(f"  Found {len(strings)} strings from Dk table")

    pairs = extract_shuffle_pairs(content)
    if pairs:
        print(f"  Shuffle: {pairs}")
        apply_shuffle(strings, pairs)

    write_output(output_file, "env", strings, input_file)
    return len(strings) > 0


# ==================== MAX SECURITY MODE ====================

def crack_max_security(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Max security: M[11]={...} where entries are:
    # - M[4]({indices; "frag1", "frag2"}) calls
    # - Plain strings like "^&7"
    pool_match = re.search(r'\w\[11\]\s*=\s*\{', content)
    if not pool_match:
        print("  [!] No M[11] table found"); return False

    start = pool_match.end()
    strings = parse_string_pool_with_calls(content, start, r'\w\[4\]\(\{')

    print(f"  Found {len(strings)} raw strings")

    pairs = extract_shuffle_pairs(content)
    if pairs:
        print(f"  Shuffle: {pairs}")
        apply_shuffle(strings, pairs)

    # ASCII85 decode
    decrypted = []
    for s in strings:
        try:
            dec = decrypt_ascii85(s)
            decrypted.append(dec.decode('utf-8', errors='replace'))
        except:
            decrypted.append(s)

    write_output(output_file, "max_security", decrypted, input_file)
    return len(decrypted) > 0


def parse_string_pool_with_calls(content, start_pos, call_pattern):
    """Parse a Lua table starting at start_pos, extracting plain strings and reconstructed strings from function calls."""
    strings = []

    # Find the end of this table (matching closing brace)
    depth = 1; i = start_pos; in_q = False; qc = None
    while i < len(content) and depth > 0:
        c = content[i]
        if in_q:
            if c == '\\': i += 1
            elif c == qc: in_q = False
        else:
            if c in ('"', "'"): in_q = True; qc = c
            elif c == '{': depth += 1
            elif c == '}': depth -= 1
        i += 1
    table_end = i - 1
    table_content = content[start_pos:table_end]

    # Now parse entries: either function calls or plain strings
    pos = 0
    while pos < len(table_content):
        # Skip whitespace and separators
        while pos < len(table_content) and table_content[pos] in ' \t\n\r,;':
            pos += 1
        if pos >= len(table_content): break

        # Check for function call: (X[9]+key)({ or M[4]({
        call_match = re.match(call_pattern, table_content[pos:])
        if call_match:
            # Find matching closing )}
            call_start = pos + call_match.end()
            d = 1; j = call_start; in_s = False; sc = None
            while j < len(table_content) and d > 0:
                c = table_content[j]
                if in_s:
                    if c == '\\': j += 1
                    elif c == sc: in_s = False
                else:
                    if c in ('"', "'"): in_s = True; sc = c
                    elif c == '{': d += 1
                    elif c == '}': d -= 1
                j += 1
            # Skip closing )
            if j < len(table_content) and table_content[j] == ')':
                j += 1
            block = table_content[call_start:j-2]
            decoded = reconstruct_indexed_string(block)
            strings.append(decoded if decoded else "")
            pos = j

        elif table_content[pos] == '"':
            # Plain string
            j = pos + 1
            while j < len(table_content):
                if table_content[j] == '\\': j += 2; continue
                elif table_content[j] == '"': break
                j += 1
            if j < len(table_content):
                s = lua_unescape(table_content[pos+1:j])
                strings.append(s)
                pos = j + 1
            else:
                pos += 1
        else:
            pos += 1

    return strings


def reconstruct_indexed_string(block):
    """Reconstruct string from {indices; "frag1", "frag2"} block.
    The M[4] function: for each index in the list, pick fragment at that position."""
    # Find ALL string fragments in the block
    frag_pattern = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'')
    all_frags = []
    for m in frag_pattern.finditer(block):
        s = m.group(1) if m.group(1) is not None else m.group(2)
        all_frags.append((m.start(), lua_unescape(s)))

    if not all_frags:
        return ""

    # Find the last { which starts the fragments sub-table
    last_brace = block.rfind('{')
    if last_brace == -1:
        return ""

    # Fragments are after the last {
    fragments = [s for pos, s in all_frags if pos > last_brace]
    if not fragments:
        fragments = [s for _, s in all_frags]

    # Indices are before the last {
    indices_part = block[:last_brace]
    indices = []
    current = ""
    balance = 0
    for c in indices_part:
        if c == '(': balance += 1; current += c
        elif c == ')': balance -= 1; current += c
        elif c == '{': balance += 1; current += c
        elif c == '}': balance -= 1; current += c
        elif c in (',', ';') and balance == 0:
            val = lua_eval(current.strip())
            if val is not None and val != 0:
                indices.append(val)
            current = ""
        else:
            current += c
    if current.strip():
        val = lua_eval(current.strip())
        if val is not None and val != 0:
            indices.append(val)

    result = ""
    for idx in indices:
        py_idx = idx - 1
        if 0 <= py_idx < len(fragments):
            result += fragments[py_idx]

    return result


def decrypt_ascii85(s_in):
    out = bytearray()
    i = 0
    while i < len(s_in):
        c = s_in[i]
        if c == 'z':
            out.extend([0, 0, 0, 0]); i += 1
        elif c in ' \t\n\r':
            i += 1
        else:
            block = []
            while len(block) < 5 and i < len(s_in):
                ch = s_in[i]
                if ch == 'z' or ch in ' \t\n\r': break
                block.append(ch); i += 1
            if not block: continue
            count = len(block)
            padded = block + ['u'] * (5 - count)
            val = 0
            for ch in padded:
                val = val * 85 + (ord(ch) - 33)
            bytes_out = count - 1 if count < 5 else 4
            for h in range(3, 3 - bytes_out, -1):
                out.append((val >> (h * 8)) & 0xFF)
    return out


# ==================== MAIN ====================

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    modes = [
        ("basic_b1_mode", "fibo.lua", crack_basic, "basic_b1"),
        ("basic_mode", "fibo.lua", crack_basic, "basic"),
        ("normal_mode", "fibo.lua", lambda i,o: crack_normal_strong(i,o,"normal"), "normal"),
        ("strong_mode", "fibo.lua", lambda i,o: crack_normal_strong(i,o,"strong"), "strong"),
        ("hard_mode", "fibo.lua", crack_hard, "hard"),
        ("env_mode", "fibo.lua", crack_env, "env"),
        ("max_security_mode", "fibo.lua", crack_max_security, "max_security"),
    ]

    results = {}
    for mode_dir, filename, crack_func, mode_name in modes:
        input_path = os.path.join(base_dir, mode_dir, filename)
        output_path = os.path.join(base_dir, mode_dir, filename.replace('.lua', '.decrypted.txt'))

        if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
            print(f"\n[SKIP] {mode_dir}/{filename}")
            results[mode_dir] = "SKIP/EMPTY"
            continue

        print(f"\n{'='*60}")
        print(f"[CRACK] {mode_dir}/{filename}")
        print(f"{'='*60}")

        try:
            success = crack_func(input_path, output_path)
            results[mode_dir] = "CRACKED" if success else "FAILED"
            print(f"  {'[OK]' if success else '[FAIL]'} -> {output_path}")
        except Exception as e:
            results[mode_dir] = f"ERROR: {e}"
            print(f"  [ERROR] {e}")
            import traceback; traceback.print_exc()

    print(f"\n{'='*60}\nSUMMARY\n{'='*60}")
    for mode, status in results.items():
        icon = "[+]" if status == "CRACKED" else "[-]"
        print(f"  {icon} {mode}: {status}")

if __name__ == "__main__":
    main()
