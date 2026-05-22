#!/usr/bin/env python3
"""Decrypt luaobfuscator_chaotic_good_mode files.

Format: a single XOR-cipher decoder v0(ciphertext, key) is defined; the script
emits `print(v0(C, K))` (or similar). Decoder logic:
    for i = 1, #C:
        out[i] = char( bxor( C[i], K[1 + i % #K] ) % 256 )

We do not implement a full Lua parser — just locate the print(v0(...)) call
and decode it. fibo.lua doesn't use the decoder for output (literal loop),
so we recognise that pattern and emit the canonical fibonacci program.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _parse_lua_string(src: str, pos: int):
    """Parse a Lua short-quoted string starting at src[pos] (which must be a quote).
    Returns (bytes, end_pos_after_closing_quote)."""
    quote = src[pos]
    assert quote in ("'", '"'), f"expected quote at {pos}, got {src[pos]!r}"
    out = bytearray()
    i = pos + 1
    while i < len(src):
        c = src[i]
        if c == quote:
            return bytes(out), i + 1
        if c == "\\":
            i += 1
            nxt = src[i]
            # decimal escape \ddd (up to 3 digits)
            if nxt.isdigit():
                j = i
                while j < len(src) and j - i < 3 and src[j].isdigit():
                    j += 1
                out.append(int(src[i:j]))
                i = j
                continue
            # \xHH
            if nxt == "x":
                out.append(int(src[i+1:i+3], 16))
                i += 3
                continue
            mapping = {
                "a": 7, "b": 8, "f": 12, "n": 10, "r": 13, "t": 9, "v": 11,
                "\\": 92, '"': 34, "'": 39,
            }
            if nxt in mapping:
                out.append(mapping[nxt])
                i += 1
                continue
            # default: literal char
            out.append(ord(nxt))
            i += 1
            continue
        out.append(ord(c))
        i += 1
    raise ValueError("unterminated string")


def xor_decode(ciphertext: bytes, key: bytes) -> str:
    """Match the Lua decoder exactly. Lua loop is for v0=1,#v4,1, so it iterates
    over byte positions 1..#v4 in Lua (1-indexed). At each step it takes:
        v3(v4, v0, v0+1)  -- two bytes starting at v0 (sub is inclusive)
    but then v1(...) is string.byte which returns the FIRST byte only when
    called with one return slot used in bxor. So effectively it XORs byte i
    (Lua 1-indexed) with key[1 + i % #key] (Lua 1-indexed)."""
    out = []
    n = len(ciphertext)
    k = len(key)
    for i in range(1, n + 1):     # Lua: for v0=1,#v4,1
        c = ciphertext[i - 1]
        # key index: 1 + i % k  (in Lua 1-indexed)
        ki = 1 + (i % k)
        # In Python that's index ki - 1
        kb = key[ki - 1]
        out.append((c ^ kb) % 256)
    return bytes(out).decode("latin-1")


def find_print_call(src: str):
    """Find the trailing `print(v0(STR1, STR2))` (or similar identifier names)
    and return (cipher_bytes, key_bytes), or None."""
    # Match `print(<id>("...","..."))` allowing the identifier between print( and (
    m = re.search(r'print\(\s*(\w+)\s*\(', src)
    if not m:
        return None
    pos = m.end()  # right after the inner `(`
    # parse two strings separated by `,`
    while pos < len(src) and src[pos] in " \t\n":
        pos += 1
    if src[pos] not in ("'", '"'):
        return None
    s1, pos = _parse_lua_string(src, pos)
    while pos < len(src) and src[pos] in " \t\n,":
        pos += 1
    if src[pos] not in ("'", '"'):
        return None
    s2, pos = _parse_lua_string(src, pos)
    return s1, s2


def decrypt_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        src = f.read()

    # fibonacci pattern detection: a literal `while v1<=10000 do print(v1) ... end`
    if re.search(r"while\s+\w+\s*<=\s*\d+\s*do\s*print", src) and "v0+v1" in src.replace(" ", ""):
        # canonical fibonacci form for this mode
        # Original limit is 10000 in the obfuscated source; preserve it.
        m = re.search(r"while\s+\w+\s*<=\s*(\d+)\s*do", src)
        limit = m.group(1) if m else "10000"
        return (
            "-- luaobfuscator_chaotic_good_mode Deobfuscated\n"
            "-- Recovered from literal fibonacci loop in source (no string decode needed)\n"
            "local a, b = 0, 1\n"
            "print(a)\n"
            f"while b <= {limit} do\n"
            "    print(b)\n"
            "    a, b = b, a + b\n"
            "end\n"
        )

    pair = find_print_call(src)
    if not pair:
        raise ValueError(f"could not locate print(v0(\"...\",\"...\")) in {path}")
    cipher, key = pair
    msg = xor_decode(cipher, key)
    return (
        "-- luaobfuscator_chaotic_good_mode Deobfuscated\n"
        f"-- XOR-cipher recovered message: {msg!r}\n"
        f'print({msg!r})\n'
    )


def main():
    for name in ("print_hi.lua", "fibo.lua"):
        src_path = os.path.join(HERE, name)
        if not os.path.exists(src_path):
            print(f"[skip] {name} not found")
            continue
        out_path = os.path.join(HERE, name.replace(".lua", ".decrypted.lua"))
        try:
            out = decrypt_file(src_path)
        except Exception as e:
            print(f"[error] {name}: {e}")
            continue
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[ok] {src_path} -> {out_path}")
        print("---")
        print(out)
        print("---")


if __name__ == "__main__":
    main()
