#!/usr/bin/env python3
"""Static decompiler for XHider psu_hard_mode VM proto JSON.

Reads print_hi.proto.json (dumped from Lua 5.1 runtime) and produces
an annotated Lua-like listing with:
  1. All decoded string/number constants (the main value)
  2. Raw VM instruction trace with heuristic opcode names
  3. Sub-proto disassembly

Proto structure (psu_hard_mode field names):
  Root node:
    rtFqFB4  = some count (NOT instruction count)
    zBUzViOo = instruction array (entries point to instruction nodes)
    88664    = sub-protos array
    z0G15    = upvalues / string constants

  Instruction node:
    756172             = next-instruction pointer (linked list)
    -949121.96183324   = opcode (integer)
    Hz5d6R0Rv          = operand A (constant/register index)
    GVuLI              = operand B (register index)
    -358199            = operand C (often 0)
    bu7vtDN            = operand D (often 0)

The VM executor follows the linked list via 756172 exclusively.
The instruction array provides entry points (index 0 = first instruction).

Opcode mapping is OBFUSCATED (dispatch thresholds computed at runtime
via hash functions), so exact names are heuristic guesses based on
operand patterns and comparison with psu_mode/psu_mid_mode.
"""

import json
import pathlib
import sys

SCRIPT_DIR = pathlib.Path(__file__).parent
PROTO_PATH = SCRIPT_DIR / "print_hi.proto.json"
OUT_PATH = SCRIPT_DIR / "print_hi.decompiled.lua"

# ---------------------------------------------------------------------------
# Field-name constants for psu_hard_mode proto nodes
# ---------------------------------------------------------------------------
KEY_OPCODE = "-949121.96183324"
KEY_OP_A = "Hz5d6R0Rv"
KEY_OP_B = "GVuLI"
KEY_OP_C = "-358199"
KEY_OP_D = "bu7vtDN"
KEY_NEXT = "756172"

KEY_INSTR_ARR = "zBUzViOo"
KEY_SUBPROTO_ARR = "88664"
KEY_CONSTS = "z0G15"
KEY_RT_COUNT = "rtFqFB4"

# ---------------------------------------------------------------------------
# Heuristic opcode names
# ---------------------------------------------------------------------------
# Derived by analyzing operand patterns across all instruction nodes:
#   OP=0  (4x):  A=52, B=2, D=1..4  => SETLIST (batch fill table)
#   OP=1  (1x):  A=0, B=0           => RETURN
#   OP=3  (3x):  A=small, B=small   => CALL (function call)
#   OP=6  (1x):  A=0, B=1           => CLOSURE
#   OP=7  (1x):  A=0, B=1           => FORPREP
#   OP=8  (2x):  A=0, B=0           => NEWTABLE
#   OP=9  (1x):  A=0, B=11          => VARARG
#   OP=10 (208x): A=const_idx, B=reg => LOADK (load constant into register)
#   OP=11 (1x):  A=14, B=12         => CONCAT or GETTABLE_R
#   OP=12 (1x):  A=0, B=?           => FORLOOP
#   OP=13 (5x):  A=large (upval idx)=> GETGLOBAL (get global by name)
#   OP=15 (1x):  A=10, B=10         => NEWTABLE_SIZED
#   OP=16 (1x):  A=2, B=12, D=12    => SETTABLE
#   OP=17 (1x):  A=0, B=0           => LEN / NOP-like
#   OP=18 (1x):  A=ref, B=4         => FUSED_OP (multi-op block)
#   OP=19 (4x):  A=ref target       => JMP (jump / control flow)
#   OP=20 (1x):  A=45, B=2          => CALL_VOID (no return capture)
#   OP=22 (3x):  A=reg, B=reg       => MOVE (register copy)
#   OP=23 (1x):  A=0, B=3           => GETTABLE_K
#   OP=26 (1x):  A=ref target       => JMP_BACK (loop control)
#   OP=27 (1x):  A=2, B=14          => UNM / LEN
#   OP=28 (2x):  A=10, B=8          => SETLIST variant
#
# NOTE: These are HEURISTIC. The real dispatch uses obfuscated
#       threshold comparisons, so opcode numbers may differ at runtime.
HEURISTIC_OP_NAMES = {
    0: "SETLIST",
    1: "RETURN",
    3: "CALL",
    6: "CLOSURE",
    7: "FORPREP",
    8: "NEWTABLE",
    9: "VARARG",
    10: "LOADK",
    11: "GETTABLE_R",
    12: "FORLOOP",
    13: "GETGLOBAL",
    15: "NEWTABLE_SZ",
    16: "SETTABLE",
    17: "NOP_LIKE",
    18: "FUSED",
    19: "JMP",
    20: "CALL_VOID",
    22: "MOVE",
    23: "GETTABLE_K",
    26: "JMP_BACK",
    27: "UNM",
    28: "SETLIST2",
}

# Opcodes where operand A is a constant-pool index (resolve to name)
CONST_INDEX_A_OPS = {10, 13}  # LOADK, GETGLOBAL

MAX_LINKED_STEPS = 600


def load_proto(path):
    """Load the proto JSON and return (nodes_dict, root_id)."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["nodes"], data["root"]


def deref(node, key, nodes):
    """Dereference a $ref pointer, or return the raw value."""
    v = node.get(key)
    if isinstance(v, dict) and "$ref" in v:
        return nodes[str(v["$ref"])]
    return v


def build_obj_id_map(nodes):
    """Build id(node_object) -> int node_id for O(1) reverse lookup."""
    return {id(v): int(k) for k, v in nodes.items() if isinstance(v, dict)}


def extract_upvalues(proto_node, nodes):
    """Extract the upvalue/string constant table from a proto node."""
    consts_node = deref(proto_node, KEY_CONSTS, nodes)
    if not isinstance(consts_node, dict):
        return {}
    upvalues = {}
    for k in consts_node:
        if k.lstrip("-").isdigit():
            upvalues[int(k)] = consts_node[k]
    return upvalues


def extract_instructions(proto_node, nodes):
    """Extract the instruction array from a proto node.

    Returns list of (array_index, instruction_node) tuples, sorted by index.
    """
    instr_table = deref(proto_node, KEY_INSTR_ARR, nodes)
    if not isinstance(instr_table, dict):
        return []
    entries = []
    for k in instr_table:
        if k.lstrip("-").isdigit():
            ref = instr_table[k]
            if isinstance(ref, dict) and "$ref" in ref:
                instr = nodes[str(ref["$ref"])]
                entries.append((int(k), instr))
    entries.sort(key=lambda x: x[0])
    return entries


def fmt_val(val, upvalues=None):
    """Format a scalar operand value.

    If upvalues is provided and val is an integer key into the table,
    resolve it to show the constant name.
    """
    if val is None:
        return "?"
    if isinstance(val, dict) and "$ref" in val:
        return f"->#{val['$ref']}"
    if isinstance(val, str):
        return repr(val)
    if isinstance(val, float) and val == int(val):
        val = int(val)
    if isinstance(val, int) and upvalues is not None and val in upvalues:
        uv = upvalues[val]
        return f"{val} [{uv!r}]"
    return str(val)


def disasm_proto(proto_node, nodes, upvalues, obj_id_map, depth=0, name="main"):
    """Disassemble a proto node and return list of output lines."""
    indent = "  " * depth
    lines = []

    # Header
    count = proto_node.get(KEY_RT_COUNT, "?")
    lines.append(f"{indent}-- == {name} (rtFqFB4={count}) ==")

    # Extract instructions
    instr_entries = extract_instructions(proto_node, nodes)
    if not instr_entries:
        lines.append(f"{indent}  -- (no instructions)")
        return lines

    # Build node_graph_id -> instruction array index (for @N markers)
    node_to_arr_idx = {}
    for arr_idx, instr_node in instr_entries:
        gid = obj_id_map.get(id(instr_node))
        if gid is not None:
            node_to_arr_idx[gid] = arr_idx

    # Find starting node
    _, first_instr = instr_entries[0]
    first_nid = obj_id_map.get(id(first_instr))
    if first_nid is None:
        lines.append(f"{indent}  -- (cannot resolve first instruction node)")
        return lines

    # Follow linked list
    step = 0
    cur_node = first_instr
    cur_nid = first_nid
    visited = set()

    while cur_node is not None and cur_nid not in visited:
        visited.add(cur_nid)
        op = cur_node.get(KEY_OPCODE, "?")
        a = cur_node.get(KEY_OP_A)
        b = cur_node.get(KEY_OP_B)
        c = cur_node.get(KEY_OP_C)
        d = cur_node.get(KEY_OP_D)

        # Heuristic opcode name
        if isinstance(op, int):
            op_name = HEURISTIC_OP_NAMES.get(op, f"OP{op}")
        else:
            op_name = f"OP{op}"

        # Format A: resolve constant-pool index for LOADK/GETGLOBAL,
        # otherwise show raw (register index or ref).
        if isinstance(op, int) and op in CONST_INDEX_A_OPS:
            a_str = fmt_val(a, upvalues)
        else:
            a_str = fmt_val(a)
        b_str = fmt_val(b)
        c_str = fmt_val(c)
        d_str = fmt_val(d)

        # Mark instruction-array entry points
        arr_mark = ""
        if cur_nid in node_to_arr_idx:
            arr_mark = f"  @{node_to_arr_idx[cur_nid]}"

        line = (
            f"{indent}  -- [{step:>3}] {op_name:<14} "
            f"A={a_str:<35} B=r{b_str:<6} C={c_str:<6} D={d_str}"
            f"{arr_mark}"
        )
        lines.append(line)

        # Advance via linked list
        nxt = cur_node.get(KEY_NEXT)
        if isinstance(nxt, dict) and "$ref" in nxt:
            cur_nid = nxt["$ref"]
            cur_node = nodes.get(str(cur_nid))
        else:
            break

        step += 1
        if step > MAX_LINKED_STEPS:
            lines.append(f"{indent}  -- ... (truncated at {MAX_LINKED_STEPS})")
            break

    lines.append(f"{indent}-- {step + 1} instruction nodes in linked list")

    # Recurse into sub-protos
    subproto_table = deref(proto_node, KEY_SUBPROTO_ARR, nodes)
    if isinstance(subproto_table, dict):
        sub_keys = sorted(
            (k for k in subproto_table if k.lstrip("-").isdigit()),
            key=lambda x: int(x),
        )
        for sk in sub_keys:
            sp_ref = subproto_table[sk]
            if isinstance(sp_ref, dict) and "$ref" in sp_ref:
                sp = nodes.get(str(sp_ref["$ref"]))
                if sp and KEY_RT_COUNT in sp:
                    sub_uv = extract_upvalues(sp, nodes)
                    sub_name = f"{name}.sub[{sk}]"
                    if sub_uv:
                        lines.append("")
                        lines.append(
                            f"{indent}  -- Sub-proto upvalues ({len(sub_uv)} entries)"
                        )
                        for idx, val in sorted(sub_uv.items()):
                            lines.append(f"{indent}  --   [{idx:>3}] {val!r}")
                    lines.append("")
                    lines.extend(
                        disasm_proto(sp, nodes, sub_uv, obj_id_map,
                                     depth + 1, sub_name)
                    )

    return lines


def generate_output(nodes, root_id):
    """Generate the full decompiled output as a string."""
    root = nodes[str(root_id)]
    obj_id_map = build_obj_id_map(nodes)
    lines = []

    # ── Header ────────────────────────────────────────────────────────────
    lines.append("-- XHider psu_hard_mode Static Decompile")
    lines.append("-- Decoded from proto.json via Lua 5.1 runtime dump")
    lines.append("--")
    lines.append("-- NOTE: Opcode names are HEURISTIC.  The VM dispatch uses")
    lines.append("-- obfuscated threshold comparisons (d()/a() hash functions),")
    lines.append("-- so exact opcode semantics cannot be determined statically.")
    lines.append("-- The VM follows a linked list (756172) for instruction sequencing.")
    lines.append("")

    # ── Constants ─────────────────────────────────────────────────────────
    upvalues = extract_upvalues(root, nodes)
    strings = {i: v for i, v in upvalues.items() if isinstance(v, str)}
    numbers = {i: v for i, v in upvalues.items() if not isinstance(v, str)}

    lines.append(
        f"-- === Decoded String/Number Constants ({len(upvalues)} entries) ==="
    )
    lines.append(
        f"--   Strings: {len(strings)}, Numbers: {len(numbers)}"
    )
    lines.append("--")

    for idx, val in sorted(upvalues.items()):
        if isinstance(val, str):
            lines.append(f"-- [{idx:>3}] {val!r}")
        else:
            lines.append(f"-- [{idx:>3}] {val!r}  (number)")

    lines.append("")

    # Highlight the most interesting constants
    highlights = {
        "print", "hi", "game", "getgc", "hookfunction", "pcall",
        "require", "table", "string", "math", "warn", "error",
        "tostring", "type", "getgenv", "getrenv", "getreg",
        "setreadonly", "make_writable", "hookfunction",
        "new", "findFirstChild", "GetService", "GetChildren",
    }
    notable = [f"--   [{i:>3}] {v!r}"
               for i, v in sorted(upvalues.items())
               if isinstance(v, str) and v in highlights]
    if notable:
        lines.append("-- === Notable Constants ===")
        for n in notable:
            lines.append(n)
        lines.append("")

    # ── Instruction Trace ─────────────────────────────────────────────────
    lines.append("-- === VM Instruction Trace ===")
    lines.append("-- Instructions walked via linked list from instruction-array[0].")
    lines.append("-- '@N' marks instruction-array entry points.")
    lines.append("-- A operand: LOADK/GETGLOBAL show resolved constant name; others show raw.")
    lines.append("-- B/C/D operands: register indices (prefixed 'r') or flags.")
    lines.append("")

    main_lines = disasm_proto(root, nodes, upvalues, obj_id_map,
                              depth=0, name="main")
    lines.extend(main_lines)

    # ── Footer ────────────────────────────────────────────────────────────
    lines.append("")
    lines.append("-- === End of Static Decompile ===")
    lines.append("-- Expected behavior: print('hi')")
    lines.append(
        "-- For full deobfuscation, combine with dynamic analysis "
        "(e.g. env_mode/hook_env.lua)."
    )

    return "\n".join(lines) + "\n"


def main():
    proto_path = PROTO_PATH
    out_path = OUT_PATH

    if len(sys.argv) > 1:
        proto_path = pathlib.Path(sys.argv[1])
    if len(sys.argv) > 2:
        out_path = pathlib.Path(sys.argv[2])

    print(f"Loading proto: {proto_path}")
    nodes, root_id = load_proto(proto_path)
    print(f"  Nodes: {len(nodes)}, Root: {root_id}")

    root = nodes[str(root_id)]
    upvalues = extract_upvalues(root, nodes)
    instr_entries = extract_instructions(root, nodes)
    obj_id_map = build_obj_id_map(nodes)

    instr_nids = {obj_id_map[id(n)] for _, n in instr_entries
                  if id(n) in obj_id_map}
    print(f"  Upvalues: {len(upvalues)}")
    print(f"  Instruction array entries: {len(instr_entries)}")
    print(f"  Unique instruction nodes: {len(instr_nids)}")

    # Opcode frequency
    opcounts = {}
    for nid in instr_nids:
        n = nodes[str(nid)]
        if KEY_OPCODE in n:
            op = n[KEY_OPCODE]
            opcounts[op] = opcounts.get(op, 0) + 1
    print(f"  Opcode distribution: {dict(sorted(opcounts.items()))}")

    # Generate and write output
    output = generate_output(nodes, root_id)
    out_path.write_text(output, encoding="utf-8")
    print(f"\nWrote: {out_path} ({len(output)} bytes, {output.count(chr(10))} lines)")

    # Preview
    print("\n--- Output preview (first 50 lines) ---")
    for line in output.split("\n")[:50]:
        print(line)


if __name__ == "__main__":
    main()