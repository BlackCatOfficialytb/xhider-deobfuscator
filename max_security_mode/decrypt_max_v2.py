import re
import math

input_file = r"d:\dec bot2\max_security_mode\987415550020054.beautified.utf8.lua"

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

def lua_eval(expr):
    try:
        expr = expr.replace("\n", " ").strip()
        if not expr: return 0
        # Basic math simplification for evaluation
        # Replace Lua-style math.floor with floor for eval if needed
        expr = expr.replace("math.floor", "math.floor") 
        return int(eval(expr, {"__builtins__": None, "math": math}))
    except:
        # Fallback for complex expressions
        try:
            # Try to simplify simple arithmetic
            expr = re.sub(r'([0-9]+)\.0', r'\1', expr)
            return int(eval(expr, {"__builtins__": None, "math": math}))
        except:
            return 0

def unescape_lua(s):
    def dec_esc(m): return chr(int(m.group(1)))
    s = re.sub(r'\\([0-9]{3})', dec_esc, s)
    s = s.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')\
         .replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
    return s

def decrypt_k4(s_in):
    out = bytearray()
    i = 0
    while i < len(s_in):
        c = s_in[i]
        if c == 'z':
            out.extend([0,0,0,0]); i += 1
        elif c.isspace():
            i += 1
        else:
            block = []
            while len(block) < 5 and i < len(s_in):
                char = s_in[i]
                if char in 'z \n\r\t': break
                block.append(char); i += 1
            count = len(block)
            if count == 0: break
            # Padding is always 'u' in the Lua for short blocks
            padded = block + ['u'] * (5 - count)
            val = 0
            for char in padded:
                val = val * 85 + (ord(char) - 33)
            # Lua: for H=4, 4-(#block-1-1), -1
            # count=5 => H=4..1 (4 bytes)
            # count=2 => H=4..4 (1 byte)
            for h in range(4, 5 - count, -1):
                out.append((val // (256**h)) % 256)
    return out

def reconstruct_a8(block):
    lb = block.rfind('{')
    if lb == -1: return ""
    indices_p = block[:lb]
    strings_p = block[lb+1 : block.rfind('}')]
    s_l = [unescape_lua(m.group(1) or m.group(2)) for m in re.finditer(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'', strings_p)]
    indices = []
    parts = re.split(r'[;,]', indices_p)
    for p in parts:
        if p.strip():
            indices.append(lua_eval(p))
    res = "".join(s_l[i-1] for i in indices if 0 < i <= len(s_l))
    return res

# 1. Reconstruct a[1] (Full)
print("Parsing full a[1] table...")
start_match = re.search(r'a\[1\]\s*=\s*\{', content)
if not start_match:
    print("Could not find a[1] start!")
    exit(1)

p = start_match.end()
bal = 1
parts = []
curr_part = ""
in_q, qc = False, None
while p < len(content):
    c = content[p]
    if in_q:
        curr_part += c
        if c == '\\':
            p += 1
            if p < len(content): curr_part += content[p]
        elif c == qc: in_q = False
    else:
        if c in ('"', "'"): in_q = True; qc = c; curr_part += c
        elif c == '{': bal += 1; curr_part += c
        elif c == '}':
            bal -= 1
            if bal == 0: break
            curr_part += c
        elif (c == ',' or c == ';') and bal == 1:
            parts.append(curr_part.strip()); curr_part = ""
        else: curr_part += c
    p += 1
if curr_part.strip(): parts.append(curr_part.strip())

a1_raw = []
for p_str in parts:
    if p_str.startswith("a[8]"):
        m = re.search(r'a\[8\]\(\{(.*)\}\)', p_str, re.DOTALL)
        if m: a1_raw.append(reconstruct_a8(m.group(1)))
        else: a1_raw.append("")
    elif p_str.startswith('"') or p_str.startswith("'"):
        a1_raw.append(unescape_lua(p_str[1:-1]))
    else: a1_raw.append("")

# Shuffle a[1]
print("Shuffling a[1]...")
ipairs_match = re.search(r'a\[2\]=function.*?for K,H in ipairs\(\{(.*?)\}\)do', content, re.DOTALL)
if ipairs_match:
    pairs_list = re.split(r'\}\s*,\s*\{', ipairs_match.group(1).replace('\n', ''))
    for p_str in pairs_list:
        parts_p = re.split(r'[;,]', p_str.replace('{', '').replace('}', ''))
        if len(parts_p) >= 2:
            s_idx, e_idx = lua_eval(parts_p[0]) - 1, lua_eval(parts_p[1]) - 1
            if s_idx < 0: s_idx = 0
            if e_idx >= len(a1_raw): e_idx = len(a1_raw) - 1
            while s_idx < e_idx:
                a1_raw[s_idx], a1_raw[e_idx] = a1_raw[e_idx], a1_raw[s_idx]
                s_idx += 1; e_idx -= 1

a1_decoded = []
for s in a1_raw:
    try: a1_decoded.append(decrypt_k4(s))
    except: a1_decoded.append(b"")

from collections import Counter
print(f"Decoded alphabet entry lengths: {Counter(len(x) for x in a1_decoded)}")
print(f"Sample a1 entries (40-70):")
for i in range(40, 70):
    if i < len(a1_raw):
        print(f"[{i+1}] Raw: {repr(a1_raw[i])}, Decoded: {list(a1_decoded[i])}")

class LuaPRNG:
    def __init__(self, k3, k7):
        self.k3, self.k7, self.k12 = k3, k7, []
    def next(self):
        if not self.k12:
            self.k3 = (self.k3 * 237 + 15189139956072) % 35184372088832
            while True:
                self.k7 = (self.k7 * 203) % 257
                if self.k7 != 1: break
            h1 = self.k7 % 32
            h10 = (math.floor(self.k3 / (2**(13 - (self.k7-h1)//32))) % 4294967296) / (2**h1)
            h9 = math.floor((h10 % 1) * 4294717296) + math.floor(h10)
            h5 = h9 % 65536
            h6 = (h9 - h5) // 65536
            h8 = h5 % 256
            h7 = (h5 - h8) // 256
            h3 = h6 % 256
            h2 = (h6 - h3) // 256
            self.k12 = [h8, h7, h3, h2]
        return self.k12.pop()

def decrypt_a5(ciphertext, seed):
    k3_init = seed % 35184372088832
    k7_init = seed % 255 + 2
    prng_gen = LuaPRNG(k3_init, k7_init)
    curr_h1 = 72
    res = bytearray()
    for b in ciphertext:
        curr_h1 = (b + prng_gen.next() + curr_h1) % 256
        res.append(curr_h1)
    return res

def get_a2_val(k_expr):
    idx = lua_eval(k_expr) + 19462 - 1
    if 0 <= idx < len(a1_decoded): return a1_decoded[idx]
    return b""

# 2. Extract and Decrypt a[7] Entries (Layer 1)
print("Decrypting a[7] Layer 1...")
# Find the a[7] = { ... } block
a7_match = re.search(r'a\[7\]\s*=\s*\{(.*?)\}for', content, re.DOTALL)
if not a7_match:
    print("Could not find a[7] initialization!")
    exit(1)

a7_init_str = a7_match.group(1)
a7_entries_raw = re.findall(r'a\[12\]\[a\[5\]\(a\[2\]\((.*?)\),(.*?)\)\]', a7_init_str)
a7_layer1 = []
for idx_expr, seed_expr in a7_entries_raw:
    ciphertext = get_a2_val(idx_expr)
    seed = lua_eval(seed_expr)
    decrypted = decrypt_a5(ciphertext, seed)
    a7_layer1.append(decrypted)

# Shuffle a[7]
print("Shuffling a[7]...")
# for K,H in ipairs({{(250854-820864)-(-570011);-709353+709635},{714398+-714397;-449227-(-449321)};{111310+-111215;-947470+947752}})do
ipairs_a7 = re.search(r'a\[7\]=\{.*?\}for K,H in ipairs\(\{(.*?)\}\)do', content, re.DOTALL)
if ipairs_a7:
    pairs_list = re.split(r'\}\s*,\s*\{', ipairs_a7.group(1).replace('\n', ''))
    for p_str in pairs_list:
        parts_p = re.split(r'[;,]', p_str.replace('{', '').replace('}', ''))
        if len(parts_p) >= 2:
            s_idx, e_idx = lua_eval(parts_p[0]) - 1, lua_eval(parts_p[1]) - 1
            if s_idx < 0: s_idx = 0
            if e_idx >= len(a7_layer1): e_idx = len(a7_layer1) - 1
            while s_idx < e_idx:
                a7_layer1[s_idx], a7_layer1[e_idx] = a7_layer1[e_idx], a7_layer1[s_idx]
                s_idx += 1; e_idx -= 1

# 3. Layer 2: Custom Hex Decoding
print("Extracting K[5] custom hex mapping (Layer 2)...")
k5_match = re.search(r'K\[5\]\s*=\s*\{(.*?)\}for', content, re.DOTALL)
hex_map = {}
if k5_match:
    k5_inner = k5_match.group(1)
    # Sophisticated split for K[5] entries
    # Each entry is [a[12][a[5](a[2](...), ...)]] = ...
    # We want to find the pairs of (a[2]_expr, seed_expr) and the value.
    
    p = 0
    while p < len(k5_inner):
        start = k5_inner.find('[a[12][a[5](a[2](', p)
        if start == -1: break
        
        # Parse first arg of a5 (the a2 call)
        # a[5](a[2](  <-- we are after this
        p1 = start + len('[a[12][a[5](a[2](')
        bal = 1
        a2_expr = ""
        while p1 < len(k5_inner) and bal > 0:
            c = k5_inner[p1]
            if c == '(': bal += 1
            elif c == ')': bal -= 1
            if bal > 0: a2_expr += c
            p1 += 1
        
        # Now we are after a[2](...)
        # Next comes the comma
        comma_idx = k5_inner.find(',', p1)
        if comma_idx == -1: break
        
        # Parse second arg of a5 (the seed)
        p2 = comma_idx + 1
        bal = 1 # We are inside a[5](
        seed_expr = ""
        while p2 < len(k5_inner) and bal > 0:
            c = k5_inner[p2]
            if c == '(': bal += 1
            elif c == ')': bal -= 1
            if bal > 0: seed_expr += c
            p2 += 1
        
        # Now we are after a[5](...)
        # Next follows ]]] = 
        eq_idx = k5_inner.find('=', p2)
        if eq_idx == -1: break
        
        p_val = eq_idx + 1
        val_str = ""
        while p_val < len(k5_inner):
            c = k5_inner[p_val]
            if c in (',', ';', '}'): break
            val_str += c
            p_val += 1
        
        ciphertext = get_a2_val(a2_expr)
        seed = lua_eval(seed_expr)
        digit_bytes = bytes(decrypt_a5(ciphertext, seed))
        val = lua_eval(val_str)
        hex_map[digit_bytes] = val
        
        p = p_val + 1

print(f"Custom Hex Map (Bytes): {hex_map}")
found_vals = sorted(hex_map.values())
missing = [i for i in range(16) if i not in found_vals]
print(f"Values found: {found_vals}")
if missing:
    print(f"WARNING: Missing values from hex map: {missing}")

def custom_hex_decode(data_bytes):
    res = bytearray()
    for i in range(0, len(data_bytes), 2):
        if i + 1 < len(data_bytes):
            c1 = bytes([data_bytes[i]])
            c2 = bytes([data_bytes[i+1]])
            if c1 in hex_map and c2 in hex_map:
                val = hex_map[c1] * 16 + hex_map[c2]
                res.append(val)
            else:
                # Fallback: if not all bytes match, it might not be hex-encoded
                # or the entry is incomplete. 
                # For Max Security, we expect most a7 to be hex.
                return data_bytes 
    return res

print("Decoding a[7] Layer 2...")
a7_final = []
for entry in a7_layer1:
    decoded = custom_hex_decode(entry)
    a7_final.append(decoded)

# 4. Final Tiers: a[3] and a[6]
print("Reconstructing a[3] and a[6] tables...")

# Helper to get a[7] value by index
def get_a7_val(idx_expr):
    idx = lua_eval(idx_expr)
    real_idx = idx - (143733 - 126130) - 1 # Adjusted from a4 function
    if 0 <= real_idx < len(a7_final):
        return a7_final[real_idx]
    return bytearray()

a3_match = re.search(r'a\[3\]=\{(.*?)\}a\[11\]', content, re.DOTALL)
a3 = []
if a3_match:
    # Use re.findall to get all a[4](...) and literal values
    # The split approach was brittle due to commas inside a4(...)
    # entries = re.findall(r'a\[4\]\((.*?)\)|([-0-9]+(?:\+[-0-9]+)*|\".*?\")|(\{(?:[^{}]|(?R))*\})', a3_match.group(1), re.DOTALL)
    # Simple split since it's a list constructor
    # Actually, the best way is to find a[4](...) or literal
    
    ptr = 0
    inner = a3_match.group(1)
    while ptr < len(inner):
        if inner[ptr:ptr+5] == 'a[4](':
            start = ptr + 5
            bal = 1; p1 = start
            while p1 < len(inner) and bal > 0:
                if inner[p1] == '(': bal += 1
                elif inner[p1] == ')': bal -= 1
                p1 += 1
            expr = inner[start:p1-1]
            a3.append(get_a7_val(expr))
            ptr = p1
        elif inner[ptr] in ',; ':
            ptr += 1
        else:
            # find next delimiter
            next_d = len(inner)
            for d in ',;':
                idx = inner.find(d, ptr)
                if idx != -1 and idx < next_d: next_d = idx
            val_str = inner[ptr:next_d].strip()
            if val_str:
                val = lua_eval(val_str)
                if isinstance(val, str):
                    a3.append(bytearray(val.encode('utf-8')))
                else:
                    a3.append(val) # Keep as int
            ptr = next_d + 1

# a[3] Swaps
# Indices calculated from ipairs({{(638612-583602)-55009,611521-611209}, ...})
a3_swaps_data = [[1, 312], [1, 42], [43, 312]]
for start_idx, end_idx in a3_swaps_data:
    p1, p2 = start_idx, end_idx
    while p1 < p2:
        if p1-1 < len(a3) and p2-1 < len(a3):
            a3[p1-1], a3[p2-1] = a3[p2-1], a3[p1-1]
        p1 += 1; p2 -= 1

# a[6] population
def get_a11_val(idx_expr):
    idx = lua_eval(idx_expr)
    real_idx = idx - (301403 - 258337) - 1
    if 0 <= real_idx < len(a3):
        return a3[real_idx]
    return bytearray()

a6_match = re.search(r'a\[6\]=\{(.*?)\}for\s*K,H\s*in\s*ipairs\(\{\{\(\-182754', content, re.DOTALL)
a6 = []
if a6_match:
    inner = a6_match.group(1)
    ptr = 0
    while ptr < len(inner):
        if inner[ptr:ptr+6] == 'a[11](':
            start = ptr + 6
            bal = 1; p1 = start
            while p1 < len(inner) and bal > 0:
                if inner[p1] == '(': bal += 1
                elif inner[p1] == ')': bal -= 1
                p1 += 1
            expr = inner[start:p1-1]
            a6.append(get_a11_val(expr))
            ptr = p1
        elif inner[ptr] in ',; ':
            ptr += 1
        else:
            next_d = len(inner)
            for d in ',;':
                idx = inner.find(d, ptr)
                if idx != -1 and idx < next_d: next_d = idx
            val_str = inner[ptr:next_d].strip()
            if val_str:
                val = lua_eval(val_str)
                if isinstance(val, str):
                    a6.append(bytearray(val.encode('utf-8')))
                else:
                    a6.append(val)
            ptr = next_d + 1

# a[6] Swaps
# ipairs({{(-182754-44535)+227290,-641773+641911},{492954+(-766458+273505),912768+-912715},{-102655-(-102709);(1055342-656305)-398899}})
a6_swaps_data = [[1, 138], [1, 53], [54, 138]]
for start_idx, end_idx in a6_swaps_data:
    p1, p2 = start_idx, end_idx
    while p1 < p2:
        if p1-1 < len(a6) and p2-1 < len(a6):
            a6[p1-1], a6[p2-1] = a6[p2-1], a6[p1-1]
        p1 += 1; p2 -= 1

# Layer 3 Decryption on a[6] strings
# The logic uses a custom mapping table for substitution
# We'll just extract the mapping table first.
k10_match = re.search(r'K\[10\]\s*=\s*\{(.*?)\}K\[7\]', content, re.DOTALL)
l3_map = {}
if k10_match:
    k10_inner = k10_match.group(1)
    # The entries are [a[11](...)] = ...
    p = 0
    while p < len(k10_inner):
        start = k10_inner.find('[a[11](', p)
        if start == -1: break
        p1 = start + len('[a[11](')
        bal = 1; expr = ""
        while p1 < len(k10_inner) and bal > 0:
            if k10_inner[p1] == '(': bal += 1
            elif k10_inner[p1] == ')': bal -= 1
            if bal > 0: expr += k10_inner[p1]
            p1 += 1
        eq_idx = k10_inner.find('=', p1)
        if eq_idx == -1: break
        p_val = eq_idx + 1
        val_str = ""
        while p_val < len(k10_inner):
            if k10_inner[p_val] in (',', ';', '}'): break
            val_str += k10_inner[p_val]
            p_val += 1
        
        chunk = get_a11_val(expr)
        val = lua_eval(val_str)
        if isinstance(chunk, (bytearray, bytes)):
            l3_map[bytes(chunk)] = val
        p = p_val + 1

def layer3_decrypt(data):
    if not isinstance(data, (bytearray, bytes)): return data
    # 1. Byte subtraction -40
    shifted = bytearray()
    for b in data:
        shifted.append((b - 40) % 256)
    
    # 2. Base 64-like decoding
    res = bytearray()
    acc = 0
    count = 0
    for b in shifted:
        c_byte = bytes([b])
        if c_byte in l3_map:
            val = l3_map[c_byte]
            acc = acc * 64 + val
            count += 1
            if count == 4:
                res.append((acc // 65536) % 256)
                res.append((acc // 256) % 256)
                res.append(acc % 256)
                acc = 0; count = 0
        elif b == ord('='):
            if count == 2:
                res.append((acc // 64) % 256) # Adjust count logic
            elif count == 3:
                res.append((acc // 4096) % 256)
                res.append((acc // 64) % 256)
            break
    # Optimization: if res is empty, return original (might not have been encoded)
    return res if res else data

print("Applying Layer 3 decryption to a[6]...")
a6_final = []
for entry in a6:
    if isinstance(entry, (bytearray, bytes)):
        dec = layer3_decrypt(entry)
        a6_final.append(dec)
    else:
        a6_final.append(entry)

print(f"Final object table a[6] reconstructed with {len(a6_final)} entries.")
with open(r'd:\dec bot2\max_security_mode\a6_final.txt', 'w', encoding='utf-8', errors='replace') as f:
    for i, entry in enumerate(a6_final):
        if isinstance(entry, (bytearray, bytes)):
            s = entry.decode('utf-8', errors='replace')
            f.write(f"[{i+1}] (string) {s}\n")
        else:
            f.write(f"[{i+1}] (number) {entry}\n")

print("Final strings and constants saved to a6_final.txt")

output_file = r"d:\dec bot2\max_security_mode\a7_v4_decrypted.bin"
with open(output_file, "wb") as f:
    for i, data in enumerate(a7_final):
        f.write(f"\n--- ENTRY {i+1} ---\n".encode('ascii'))
        f.write(data)

txt_output = r"d:\dec bot2\max_security_mode\a7_v4_decrypted.txt"
with open(txt_output, "w", encoding="utf-8", errors="replace") as f:
    for i, data in enumerate(a7_final):
        f.write(f"[{i+1}] {data.decode('utf-8', errors='replace')}\n")

print(f"Fully decrypted data saved to {output_file} and {txt_output}")
