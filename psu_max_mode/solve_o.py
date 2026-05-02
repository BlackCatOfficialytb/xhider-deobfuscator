# Solve o[K] -> char mapping using known Lua/Roblox library/method names.
# 20 concat patterns from chunk_1, each must equal a known string.

# Format: list of (template, candidates)
# Template is a list of pieces: ('lit', s) or ('o', key)
# We'll try each candidate; the unique fits give us the char map.

import itertools

patterns_text = [
    "'' .. o[255806744] .. 'it3' .. o[303909627]",          # bit32
    "'' .. o[255806744] .. o[780364647] .. 't' .. o[209867084]",  # byte
    "'' .. o[821956203] .. o[29799631] .. o[676273207] .. 'h'",   # math
    "'' .. o[864117863] .. 'd' .. o[209867084] .. 'x' .. o['W8ZpaIfush']", # ldexp
    "'' .. o[997985534] .. 'n' .. o['W8ZpaIfush'] .. 'a' .. o[767826132] .. o[407365380]", # unpack
    "'' .. o[821956203] .. 'a' .. o[676273207] .. 'h'",     # math
    "'' .. o[860093539] .. 'lo' .. o[926356572] .. 'r'",    # floor
    "'' .. o[676273207] .. 'onu' .. o[821956203] .. o[255806744] .. o[209867084] .. 'r'", # tonumber
    "'' .. o[864117863] .. 's' .. o[669545735] .. 'ift'",   # lshift
    "'' .. o[255806744] .. o[29799631] .. 'n' .. o['anierBSX']", # band
    "'' .. o[255806744] .. 'n' .. o[926356572] .. 't'",     # bnot
    "'' .. o[255806744] .. o[462186921] .. 't'",            # bit
    "'' .. o[255806744] .. o[293684876] .. o[926356572] .. 't'", # bnot? bxor? bget?  4-letter
    "'' .. o[828614386] .. 's' .. o[669545735] .. 'if' .. o[676273207]", # rshift
    "'' .. o[255806744] .. 'or'",                            # bor
    "'' .. o[676273207] .. o[29799631] .. 'bl' .. o[209867084]", # table
    "'' .. o[676273207] .. 'abl' .. o[209867084]",           # table
    "'' .. o[462186921] .. 'nser' .. o[676273207]",          # insert
    "'' .. o[828614386] .. o[209867084] .. 'mo' .. o[466982296] .. 'e'", # remove
    "'' .. o[255806744] .. 'i' .. o[676273207] .. '3' .. o[303909627]",  # bit32
]

# Map each pattern -> expected string
expected = [
    'bit32', 'byte', 'math', 'ldexp', 'unpack', 'math', 'floor',
    'tonumber', 'lshift', 'band', 'bnot', 'bit', 'bxor', 'rshift',
    'bor', 'table', 'table', 'insert', 'remove', 'bit32',
]
# The 13th pattern was bnot not bxor; replace.
expected[12] = 'bnot'
# Hack-fix: drop trailing dummy
_unused = [
]

# Parse the pattern_text manually for each
import re
PIECE = re.compile(r"'([^']*)'|o\[(-?\d+)\]|o\['([A-Za-z_][A-Za-z0-9_]*)'\]")

def parse(pt):
    pieces = []
    for m in PIECE.finditer(pt):
        lit, intk, strk = m.groups()
        if lit is not None:
            pieces.append(('lit', lit))
        elif intk is not None:
            pieces.append(('o', int(intk)))
        else:
            pieces.append(('o', strk))
    return pieces

assignments = {}  # key -> char

def fit(pieces, target):
    # Try to match: each lit piece must appear in target at the right position.
    # Each o piece consumes exactly one char (since we observed that earlier).
    # Walk pieces, accumulating position in target.
    pos = 0
    local = {}
    for kind, val in pieces:
        if kind == 'lit':
            if not target.startswith(val, pos):
                return None
            pos += len(val)
        else:
            if pos >= len(target):
                return None
            ch = target[pos]
            if val in assignments and assignments[val] != ch:
                return None
            if val in local and local[val] != ch:
                return None
            local[val] = ch
            pos += 1
    if pos != len(target):
        return None
    return local

for pt, tgt in zip(patterns_text, expected):
    pieces = parse(pt)
    res = fit(pieces, tgt)
    if res is None:
        print(f"FAIL: {pt} -> {tgt}")
    else:
        for k, v in res.items():
            if k in assignments and assignments[k] != v:
                print(f"CONFLICT: o[{k}] previously {assignments[k]!r}, now {v!r}")
            assignments[k] = v

print("Solved:")
for k, v in sorted(assignments.items(), key=lambda x: str(x[0])):
    print(f"  o[{k!r}] = {v!r}")
