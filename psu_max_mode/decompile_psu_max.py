#!/usr/bin/env python3
"""
Static decompiler for XHider psu_max_mode VM proto JSON.

Reads print_hi.parsed.json (produced by decrypt_psu_max.py / psu_max_static.py)
and produces an annotated Lua-like listing with:
  1. All decoded string/number constants (the main value)
  2. Raw VM instruction trace with heuristic opcode names
  3. Register state tracking with constant resolution

Heuristic opcode mapping (derived from frequency + pattern analysis):
  op  0 -> RETURN       op  1 -> LOADK        op  2 -> GETUPVAL
  op  3 -> CLOSURE      op  4 -> STOP         op  5 -> SETUPVAL
  op  6 -> GETGLOBAL    op  7 -> CLOSE        op  8 -> GETTABLE
  op  9 -> SETLIST      op 10 -> SETTABLE     op 11 -> GETTABLE_R
  op 12 -> CALL         op 13 -> RETURN2      op 14 -> SETTABLE_K
  op 15 -> GETUPVAL2    op 16 -> NEWTABLE     op 17 -> GETGLOBAL2

Usage:
  python3 decompile_psu_max.py [parsed.json] [output.lua]
"""

import json
import pathlib
import sys
from collections import Counter

SCRIPT_DIR = pathlib.Path(__file__).parent

HEURISTIC_OP_NAMES = {
    0: "RETURN", 1: "LOADK", 2: "GETUPVAL", 3: "CLOSURE",
    4: "STOP", 5: "SETUPVAL", 6: "GETGLOBAL", 7: "CLOSE",
    8: "GETTABLE", 9: "SETLIST", 10: "SETTABLE", 11: "GETTABLE_R",
    12: "CALL", 13: "RETURN2", 14: "SETTABLE_K", 15: "GETUPVAL2",
    16: "NEWTABLE", 17: "GETGLOBAL2",
}

# Opcodes where B field is a constant-pool index (resolve to name)
CONST_INDEX_B_OPS = {1, 17, 6, 11}  # LOADK, GETGLOBAL2, GETGLOBAL, GETTABLE_R

# Opcodes where A field is a constant-pool index (resolve to name)
CONST_INDEX_A_OPS = {10, 14}  # SETTABLE, SETTABLE_K

HIGHLIGHT_CONSTS = {
    "print", "game", "getgc", "hookfunction", "pcall", "require",
    "table", "string", "math", "warn", "error", "tostring", "type",
    "getgenv", "getrenv", "getreg", "setreadonly", "make_writable",
    "new", "findFirstChild", "GetService", "GetChildren",
    "Workspace", "Players", "Lighting", "ReplicatedStorage",
    "RunService", "UserInputService", "StarterGui", "PlayerGui",
}


def load_proto(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fmt_field(val, consts=None, resolve_const=False, max_len=40):
    """Format a field as either a resolved constant or a register."""
    if isinstance(val, dict):
        if "UV" in val:
            return f"uv[{val['UV']}]"
        return "{...}"
    if isinstance(val, str):
        s = repr(val)
        if len(s) > max_len:
            s = s[:max_len - 3] + "..."
        return s
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, int):
        if resolve_const and consts is not None and 0 <= val < len(consts):
            c = consts[val]
            if c is not None:
                return f"{val} {c!r}"
        return f"r{val}"
    if isinstance(val, float):
        return str(int(val)) if val == int(val) else str(val)
    return str(val) if val is not None else "nil"


def fmt_next(val):
    if isinstance(val, dict):
        return "uv_ref" if "UV" in val else "{...}"
    return str(val)


def disasm_proto(proto, depth=0, name="main"):
    indent = "  " * depth
    lines = []

    consts = proto.get("consts", [])
    instrs = proto.get("instrs", [])
    numregs = proto.get("numregs", 0)
    subs = proto.get("subs", [])

    non_nil_consts = [(i, c) for i, c in enumerate(consts) if c is not None]
    non_nil_instrs = [i for i in instrs if i is not None]

    # Header
    lines.append(f"{indent}-- Proto stats:")
    lines.append(f"{indent}--   Registers:    {numregs}")
    lines.append(f"{indent}--   Constants:    {len(consts)}")
    lines.append(f"{indent}--   Instructions: {len(instrs)}")
    lines.append(f"{indent}--   Sub-protos:   {len(subs)}")
    lines.append("")

    # Constants
    strings = [(i, c) for i, c in non_nil_consts if isinstance(c, str)]
    numbers = [(i, c) for i, c in non_nil_consts if not isinstance(c, str)]

    lines.append(f"{indent}-- === Decoded Constants ({len(non_nil_consts)} entries) ===")
    lines.append(f"{indent}--   Strings: {len(strings)}, Numbers: {len(numbers)}, Bools: 0")
    lines.append(f"{indent}--")

    for idx, val in non_nil_consts:
        if isinstance(val, str):
            lines.append(f"{indent}-- [{idx:>3}] {val!r}")
        else:
            lines.append(f"{indent}-- [{idx:>3}] {val!r}  (number)")

    notable = [(i, v) for i, v in non_nil_consts
               if isinstance(v, str) and v in HIGHLIGHT_CONSTS]
    if notable:
        lines.append("")
        lines.append(f"{indent}-- === Notable Constants ===")
        for i, v in notable:
            lines.append(f"{indent}--   [{i:>3}] {v!r}")
        lines.append("")

    lines.append("")

    # Instructions
    reg_comments = {}
    lines.append(f"{indent}-- === VM Instruction Trace ===")

    step = 0
    for idx, ins in enumerate(instrs):
        if ins is None:
            continue

        op = ins.get("opcode", "?")
        a_val = ins.get("A")
        b_val = ins.get("B")
        c_val = ins.get("C")
        next_val = ins.get("next", idx + 1)

        op_name = HEURISTIC_OP_NAMES.get(op, f"OP{op}")

        resolve_b = op in CONST_INDEX_B_OPS
        resolve_a = op in CONST_INDEX_A_OPS

        a_str = fmt_field(a_val, consts, resolve_const=resolve_a)
        b_str = fmt_field(b_val, consts, resolve_const=resolve_b)
        c_str = fmt_field(c_val, consts, resolve_const=False)
        next_str = fmt_next(next_val)

        # Register tracking comments
        comment = ""
        if op_name == "LOADK" and isinstance(b_val, int) and 0 <= b_val < len(consts):
            c = consts[b_val]
            if c is not None and isinstance(c, str) and isinstance(c_val, int):
                reg_comments[c_val] = c
                comment = f"  -- r{c_val} = {c!r}"
        elif op_name == "GETGLOBAL2" and isinstance(b_val, int) and 0 <= b_val < len(consts):
            c = consts[b_val]
            if c is not None and isinstance(c, str) and isinstance(c_val, int):
                comment = f"  -- r{c_val} = _G[{c!r}]"
        elif op_name == "GETGLOBAL" and isinstance(b_val, int) and 0 <= b_val < len(consts):
            c = consts[b_val]
            if c is not None and isinstance(c, str):
                comment = f"  -- _G[{c!r}]"
        elif op_name == "GETUPVAL2":
            comment = "  -- getupval"
        elif op_name == "SETUPVAL":
            if isinstance(b_val, int) and 0 <= b_val < len(consts):
                c = consts[b_val]
                if c is not None and isinstance(c, str):
                    comment = f"  -- setupval ({c!r})"
        elif op_name == "CLOSURE":
            comment = "  -- closure/upvalue setup"
        elif op_name == "CLOSE":
            comment = "  -- close upvalues"
        elif op_name == "NEWTABLE":
            comment = "  -- r0 = {}  (newtable)"

        line = (
            f"{indent}  -- [{idx:>3}] {op_name:<14} "
            f"A={a_str:<35} "
            f"B={b_str:<25} "
            f"C={c_str:<15} "
            f"next={next_str}"
            f"{comment}"
        )
        lines.append(line)
        step += 1

    lines.append(f"{indent}-- {step} instructions in trace")

    if reg_comments:
        lines.append("")
        lines.append(f"{indent}-- === Register State Summary ===")
        for reg, val in sorted(reg_comments.items()):
            lines.append(f"{indent}-- r{reg} = {val!r}")

    for si, sub in enumerate(subs):
        lines.append("")
        lines.append(f"{indent}-- == Sub-proto [{si}] ==")
        lines.extend(disasm_proto(sub, depth + 1, f"{name}.sub[{si}]"))

    return lines


def generate_output(proto):
    lines = [
        "-- XHider psu_max_mode Static Decompile",
        "-- Decoded from binary proto via parse_proto.py",
        "--",
        "-- NOTE: Opcode names are HEURISTIC based on frequency and",
        "-- operand pattern analysis. The VM dispatch uses obfuscated",
        "-- threshold comparisons, so exact semantics require runtime.",
        "-- The VM follows the 'next' field for instruction sequencing.",
        "-- 'uv_ref' entries indicate upvalue-reference jumps that cannot",
        "-- be resolved without the full runtime environment.",
        "",
    ]
    lines.extend(disasm_proto(proto, depth=0, name="main"))
    lines.extend([
        "",
        "-- === End of Static Decompile ===",
        "-- For full deobfuscation, combine with dynamic analysis "
        "(e.g. psu_max_shim.lua + binary patching).",
    ])
    return "\n".join(lines) + "\n"


def main():
    default_proto = SCRIPT_DIR / "print_hi.parsed.json"
    default_out = SCRIPT_DIR / "print_hi.decompiled.lua"

    proto_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else default_proto
    out_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else default_out

    print(f"Loading proto: {proto_path}")
    proto = load_proto(proto_path)

    consts = proto.get("consts", [])
    instrs = proto.get("instrs", [])
    non_nil = [i for i in instrs if i is not None]
    non_nil_c = [c for c in consts if c is not None]

    print(f"  Registers: {proto.get('numregs', 0)}")
    print(f"  Constants: {len(consts)} ({len(non_nil_c)} non-nil)")
    print(f"  Instructions: {len(instrs)} ({len(non_nil)} non-null)")
    print(f"  Sub-protos: {len(proto.get('subs', []))}")

    opcounts = Counter(i["opcode"] for i in non_nil)
    print(f"  Opcodes: {dict(sorted(opcounts.items()))}")

    output = generate_output(proto)
    out_path.write_text(output, encoding="utf-8")
    print(f"\nWrote: {out_path} ({len(output)} bytes, {output.count(chr(10))} lines)")

    print("\n--- Output preview (first 30 lines) ---")
    for line in output.split("\n")[:30]:
        print(line)


if __name__ == "__main__":
    main()