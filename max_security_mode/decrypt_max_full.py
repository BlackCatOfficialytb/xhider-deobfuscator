import re
import math

input_file = r"d:\dec bot2\max_security_mode\987415550020054.beautified.utf8.lua"

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

def lua_eval(expr):
    try:
        expr = expr.replace("\n", " ").strip()
        if not expr: return 0
        return int(eval(expr, {"__builtins__": None, "math": math}))
    except:
        return 0

def unescape_lua(s):
    # Handle \ddd escapes
    def dec_esc(m):
        return chr(int(m.group(1)))
    s = re.sub(r'\\([0-9]{3})', dec_esc, s)
    s = s.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')\
         .replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
    return s

def reconstruct_a8(block):
    last_brace = block.rfind('{')
    if last_brace == -1: return ""
    
    indices_part = block[:last_brace]
    strings_part = block[last_brace+1 : block.rfind('}')]
    
    s_pattern = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'')
    s_list = []
    for sm in s_pattern.finditer(strings_part):
        s = sm.group(1) if sm.group(1) is not None else sm.group(2)
        s_list.append(unescape_lua(s))
        
    if not s_list: return ""
    
    indices = []
    curr = ""
    bal = 0
    for c in indices_part:
        if c == '(': bal+=1
        elif c == ')': bal-=1
        if (c==',' or c==';') and bal==0:
            indices.append(lua_eval(curr))
            curr = ""
        else:
            if c != ' ': curr += c
    if curr.strip(): indices.append(lua_eval(curr))
    
    res = ""
    for i in indices:
        idx = i - 1
        if 0 <= idx < len(s_list):
            res += s_list[idx]
    return res

# 1. Parse a[1]
print("Parsing strings...")
strings_pool = []
curr = 0
while True:
    start_marker = "a[8]({"
    idx = content.find(start_marker, curr)
    if idx == -1: break
    if "function" in content[idx-20:idx]:
        curr = idx + 1
        continue
    bal = 1
    p = idx + len(start_marker)
    in_q, qc = False, None
    while p < len(content):
        c = content[p]
        if in_q:
            if c == '\\': p+=1
            elif c == qc: in_q = False
        else:
            if c == '"' or c == "'": in_q=True; qc=c
            elif c == '{': bal += 1
            elif c == '}': bal -= 1
        if bal == 0:
            if content[p+1] == ')':
                blocks_content = content[idx+6 : p]
                strings_pool.append(reconstruct_a8(blocks_content))
                curr = p + 2
                break
        p += 1
    else: curr = idx + 1

print(f"Recovered {len(strings_pool)} strings.")

# 2. Extract Shuffles
ipairs_match = re.search(r'ipairs\(\{(.*?)\}\)do', content, re.DOTALL)
if ipairs_match:
    pairs_content = ipairs_match.group(1).replace('\n', '')
    raw_pairs = re.split(r'\}\s*,\s*\{', pairs_content)
    for p in raw_pairs:
        p = p.replace('{', '').replace('}', '')
        parts = re.split(r'[;,]', p)
        if len(parts) >= 2:
            start, end = lua_eval(parts[0]), lua_eval(parts[1])
            s, e = start - 1, end - 1
            if s < 0: s = 0
            if e >= len(strings_pool): e = len(strings_pool) - 1
            while s < e:
                strings_pool[s], strings_pool[e] = strings_pool[e], strings_pool[s]
                s += 1; e -= 1
    print("Applied shuffles.")

# 3. K[4] Decryption (ASCII85-like)
def decrypt_k4(s_in):
    # Lua logic:
    # while V[4]<=V[2] do
    #   if "z" then char(0,0,0,0)
    #   if "whitespace" then skip
    #   else block of 5 chars
    #   K[6] = K[6]*85 + (byte - 33)
    #   bytes: K[6]/256^H % 256 for H=4 to 4-K[3]
    
    out = bytearray()
    i = 0
    while i < len(s_in):
        c = s_in[i]
        if c == 'z':
            out.extend([0,0,0,0])
            i += 1
        elif c.isspace():
            i += 1
        else:
            # Accumulate up to 5 chars
            block = []
            while len(block) < 5 and i < len(s_in):
                char = s_in[i]
                if char in 'z \n\r\t': break
                block.append(char)
                i += 1
            
            count = len(block)
            # Pad with 'u' (ASCII 117)
            padded = block + ['u'] * (5 - count)
            
            val = 0
            for char in padded:
                val = val * 85 + (ord(char) - 33)
            
            # Extract bytes
            # H goes from 4 down to 4 - (count - 1)
            # if count=5, indices 4,3,2,1,0? Wait.
            # Lua: H=4, 4-K[3], -1 where K[3] = K[5]-1.
            # if count=5, K[3]=4. H=4, 3, 2, 1, 0. (5 bytes)
            # Wait, ASCII85 usually produces 4 bytes from 5 chars.
            # Standard ASCII85: val = c1*85^4 + c2*85^3 ...
            # Then val / 256^3, val / 256^2 ...
            # Let's re-read the Lua logic.
            # for H=4, 4-K[3], -1 do
            #   z[2]=math.floor(K[6]/(256)^z[1])%(256)
            #   table.insert(V[5],string.char(z[2]))
            # end
            
            # If count=5, K[3]=4. H=4, 3, 2, 1, 0. -> 5 bytes!
            # If count=4, K[3]=3. H=4, 3, 2, 1. -> 4 bytes.
            # This is slightly non-standard ASCII85 but I'll follow it.
            
            num_bytes = count # Actually K[3]+1 = count - 1 + 1 = count.
            # Wait. loop H=4, 4-K[3], -1. 
            # If count=5, H=4,3,2,1,0. Total 5 iterations.
            # If count=2, K[3]=1. H=4, 3. Total 2 iterations.
            
            for h in range(4, 4 - count, -1):
                b = (val // (256**h)) % 256
                out.append(b)
                
    return out

print("Decrypting string pool...")
decrypted_pool = []
for s in strings_pool:
    try:
        dec = decrypt_k4(s)
        # Use errors='replace' to avoid crashes on non-decrypted blobs
        decrypted_pool.append(dec.decode('utf-8', errors='replace'))
    except:
        decrypted_pool.append("[DECRYPT_FAILED]")

with open(r"d:\dec bot2\max_security_mode\decrypted_final.txt", "w", encoding="utf-8") as f:
    for i, s in enumerate(decrypted_pool):
        f.write(f"[{i+1}] {s}\n")

# Search for interesting bits
for i, s in enumerate(decrypted_pool):
    if "You Are Lost" in s:
        print(f"Found PayLoad at index {i+1}!")
    if "http" in s:
        print(f"Found URL at index {i+1}: {s}")
    if "loadstring" in s:
        print(f"Found loadstring at index {i+1}: {s}")
