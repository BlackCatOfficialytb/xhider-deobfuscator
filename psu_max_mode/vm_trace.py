#!/usr/bin/env python3
"""Trace the psu_max VM execution to understand flow and find bugs."""
import sys, math, os

sys.path.insert(0, os.path.dirname(__file__))
from decrypt_psu_max import (
    extract_psu_string, lzw_decode, XORReader, bit_extract, lua_tostring,
    MASK32, tobit, bxor, band, O_TABLE
)

def main():
    source_path = sys.argv[1] if len(sys.argv) > 1 else "print_hi.lua.chunk_1.clean.lua"
    base = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(source_path):
        source_path = os.path.join(base, source_path)

    with open(source_path, "r") as f:
        source = f.read()

    psu_str = extract_psu_string(source)
    byte_list, xor_key = lzw_decode(psu_str)
    print(f"Decoded {len(byte_list)} bytes, XOR key={xor_key}")

    rd = XORReader(byte_list, xor_key, start_pos=0)
    F = rd.read_byte()       # num_params
    numregs = rd.read_uint16()  # register frame size
    num_consts = rd.read_uint32()

    # Parse constants
    constants = []
    for _ in range(num_consts):
        tag = rd.read_byte()
        if tag == 56:
            constants.append(rd.read_byte() != 0)
        elif tag == 20:
            raw_m = rd.read_uint32()
            raw_se = rd.read_uint32()
            mantissa = bit_extract(raw_m, 1, 20)
            full_mant = mantissa * (2 ** 32)
            exp = bit_extract(raw_se, 21, 31)
            sign_bit = bit_extract(raw_se, 32)
            sign = (-1) ** sign_bit
            if exp == 0:
                constants.append(0.0)
            elif exp == 2047:
                constants.append(float("nan"))
            else:
                constants.append(sign * math.ldexp(1, exp - 1023) * (full_mant / (2 ** 52)))
        elif tag == 9:
            slen = rd.read_uint32()
            if slen == 0:
                constants.append("")
            else:
                chars = [chr(rd.read_byte()) for _ in range(slen)]
                constants.append("".join(chars))
        else:
            constants.append(None)

    count_val = rd.read_uint32()
    print(f"Proto: params={F}, numregs={numregs}, consts={num_consts}, loop_count={count_val}")

    # Create upvalue tables (these ARE the instruction tables)
    upvalues = {}
    for _n in range(count_val):
        upvalues[_n] = {}

    # Parse instructions into upvalue tables
    for C_idx in range(count_val):
        fmt_raw = rd.read_byte()
        if fmt_raw == 0:
            continue
        fmt = fmt_raw - 1
        h_type = bit_extract(fmt, 1, 3)
        l_val = e_val = c_val = 0
        t_val = 0
        x_val = 0
        s_val = 0

        if h_type == 0:
            l_val = rd.read_uint16()
            t_val = rd.read_uint16()
            c_val = rd.read_byte()
            e_val = rd.read_uint16()
        elif h_type == 1:
            uv_idx = rd.read_uint32()
            t_val = upvalues.get(uv_idx, {})
            c_val = rd.read_byte()
            e_val = rd.read_uint16()
        elif h_type == 2:
            uv_idx = rd.read_uint32()
            t_val = upvalues.get(uv_idx, {})
            c_val = rd.read_byte()
            e_val = rd.read_uint16()
        elif h_type == 3:
            l_val = rd.read_uint16()
            uv_idx = rd.read_uint32()
            t_val = upvalues.get(uv_idx, {})
            c_val = rd.read_byte()
            e_val = rd.read_uint16()
        elif h_type == 5:
            l_val = rd.read_uint16()
            uv_idx = rd.read_uint32()
            t_val = upvalues.get(uv_idx, {})
            c_val = rd.read_byte()
            e_val = rd.read_uint16()
            x_val = {}
            for _n in range(l_val):
                x_val[_n] = {0: rd.read_byte(), 1: rd.read_uint16()}
        elif h_type == 6:
            pass

        # Post-processing flags
        if bit_extract(fmt, 6, 6) == 1:
            if isinstance(l_val, int) and 0 <= l_val < len(constants):
                l_val = constants[l_val]
        if bit_extract(fmt, 8, 8) == 1:
            uv_idx2 = rd.read_uint32()
            s_val = upvalues.get(uv_idx2, {})
        else:
            s_val = upvalues.get(C_idx + 1, {})
        if bit_extract(fmt, 5, 5) == 1:
            if isinstance(t_val, int) and 0 <= t_val < len(constants):
                t_val = constants[t_val]
        if bit_extract(fmt, 4, 4) == 1:
            if isinstance(e_val, int) and 0 <= e_val < len(constants):
                e_val = constants[e_val]
        if bit_extract(fmt, 7, 7) == 1:
            x_val = {}
            cnt = rd.read_byte()
            for _n in range(cnt):
                x_val[_n + 1] = rd.read_uint32()

        # Store in upvalue table
        n = upvalues[C_idx]
        n["zIcQPw9IGm"] = s_val      # next pointer
        n[-953553] = c_val            # opcode
        n["tr32bpYRo"] = l_val       # A field
        n["jVDyuN"] = t_val          # B field
        n["HIvaDexWw8"] = x_val      # extra
        n["duvaqQLpM"] = e_val       # C field

    print(f"Remaining bytes after parse: {len(byte_list) - rd.pos}")

    # Build reverse mapping: dict id -> instruction index
    id_to_idx = {}
    for idx, u in upvalues.items():
        if -953553 in u:
            id_to_idx[id(u)] = idx

    populated = sorted(id_to_idx.values())
    print(f"Populated instructions ({len(populated)}): first 30 = {populated[:30]}")
    print(f"  ... last 10 = {populated[-10:]}")

    def resolve_idx(obj):
        """Convert an upvalue dict reference to an instruction index."""
        if isinstance(obj, dict) and id(obj) in id_to_idx:
            return id_to_idx[id(obj)]
        return None

    # ── VM Execution ──
    output = []
    regs = [None] * (numregs + 20)

    def do_print(*args):
        parts = [lua_tostring(a) for a in args]
        output.append("\t".join(parts))

    # Create a minimal environment table (like the Lua _G)
    env = {"print": do_print}

    def resolve_int_or_idx(val):
        """Get integer value, or if dict, get its instruction index."""
        if isinstance(val, int) and not isinstance(val, bool):
            return val
        if isinstance(val, dict):
            return resolve_idx(val)
        return None

    a_ref = upvalues[0]  # Start at instruction 0

    TRACE = True  # Set to False for speed
    MAX_STEPS = 100000

    for step in range(MAX_STEPS):
        if not isinstance(a_ref, dict) or -953553 not in a_ref:
            tgt = resolve_idx(a_ref)
            if TRACE:
                print(f"Step {step}: BAD REF idx={tgt}, stopping")
            break

        e = a_ref[-953553]  # opcode
        a_next = a_ref.get("zIcQPw9IGm", None)  # default next
        r_val = a_ref.get("duvaqQLpM", 0)   # C field
        d_val = a_ref.get("jVDyuN", 0)      # B field
        i_val = a_ref.get("tr32bpYRo", 0)  # A field
        cur_idx = resolve_idx(a_ref)

        if TRACE and step < 100:
            d_s = f"uv[{resolve_idx(d_val)}]" if isinstance(d_val, dict) else str(d_val)[:20]
            r_s = str(r_val)[:15] if not isinstance(r_val, dict) else f"uv[{resolve_idx(r_val)}]"
            i_s = str(i_val)[:15] if not isinstance(i_val, dict) else f"uv[{resolve_idx(i_val)}]"
            n_s = str(resolve_idx(a_next)) if resolve_idx(a_next) is not None else "?"
            print(f"  [{step:4d}] idx={cur_idx:3d} op={e:2d}  d(B)={d_s:20s}  r(C)={r_s:15s}  i(A)={i_s:15s}  next={n_s}")

        # ── Dispatch ──
        if e <= 1:
            # SET: n[_[r]] = _[d]
            dest = r_val if isinstance(r_val, int) else 0
            if 0 <= dest < len(regs):
                regs[dest] = d_val
            if TRACE and step < 100:
                print(f"         → SET regs[{dest}] = {type(d_val).__name__}{'('+str(resolve_idx(d_val))+')' if isinstance(d_val,dict) else ''}")

        elif e <= 8:
            # JMP: a = _[d]
            tgt = resolve_idx(d_val)
            if TRACE and step < 100:
                print(f"         → JMP to {tgt}")
            a_ref = d_val
            continue

        elif e == 9:
            # SETLIST: n[_[r]]...n[_[r]+_[i]-1] = _[extra] content
            # For now, handle as NOP
            pass

        elif e <= 12:
            # GETTABLE_IDX: n[_[r]] = n[_[d]][_[i]]
            dest = r_val if isinstance(r_val, int) else 0
            src = d_val if isinstance(d_val, int) else 0
            key = i_val
            tbl = regs[src] if 0 <= src < len(regs) else None
            val = None
            if isinstance(tbl, dict) and key is not None:
                val = tbl.get(key)
            if 0 <= dest < len(regs):
                regs[dest] = val
            if TRACE and step < 100:
                print(f"         → GETTABLE_IDX regs[{dest}] = regs[{src}][{repr(key)[:20]}] = {repr(val)[:30]}")

        elif e == 13:
            # SELF_CALL: local o=_[r]; n[o]=n[o](n[o+1])
            dest = r_val if isinstance(r_val, int) else 0
            if 0 <= dest < len(regs):
                fn = regs[dest]
                arg = regs[dest + 1] if dest + 1 < len(regs) else None
                if fn == do_print:
                    do_print(arg)
                    if TRACE:
                        print(f"         → PRINT({repr(arg)[:50]})")
                elif callable(fn):
                    try:
                        result = fn(arg)
                        regs[dest] = result
                    except:
                        pass
                else:
                    if TRACE and step < 100:
                        print(f"         → SELF_CALL regs[{dest}] fn={type(fn).__name__}")

        elif e == 16:
            # MOVE: n[_[r]] = n[_[d]]
            dest = r_val if isinstance(r_val, int) else 0
            src = d_val if isinstance(d_val, int) else 0
            val = regs[src] if 0 <= src < len(regs) else None
            if 0 <= dest < len(regs):
                regs[dest] = val
            if TRACE and step < 100:
                print(f"         → MOVE regs[{dest}] = regs[{src}]")

        else:
            # GETTABLE_KEY (14, 15, 17+): n[_[r]] = n[_[d]][n[_[i]]]
            dest = r_val if isinstance(r_val, int) else 0
            src = d_val if isinstance(d_val, int) else 0
            key_idx = i_val if isinstance(i_val, int) else 0
            tbl = regs[src] if 0 <= src < len(regs) else None
            key = regs[key_idx] if 0 <= key_idx < len(regs) else None
            val = None
            if isinstance(tbl, dict) and key is not None:
                val = tbl.get(key)
            if 0 <= dest < len(regs):
                regs[dest] = val
            if TRACE and step < 100:
                print(f"         → GETTABLE_KEY regs[{dest}] = regs[{src}][regs[{key_idx}]] key={repr(key)[:20]} = {repr(val)[:30]}")

        a_ref = a_next

    print(f"\n=== VM stopped after {step+1} steps ===")
    print(f"Output ({len(output)} lines):")
    for line in output:
        print(f"  {line}")

if __name__ == "__main__":
    main()