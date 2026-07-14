# Deobfuscation Status & Todo

## Completed Work

### Batch deobfuscation (2026-07-14)
- All 37 modes with obfuscated test scripts now produce **reconstructed Lua source** via `main.py batch --force`
- Dynamic output improved: `_build_dynamic_output` now emits equivalent Lua source (fibonacci loops, print calls) instead of just listing captured output as comments
- `luaobfuscator_ironobf_mode` files had UTF-8 BOM stripped to enable Lua parsing

## Max Security Mode (`max_security_mode/decrypt_max_v2.py`)

**Status:** K[2] multi-byte fix landed (commit 5770009). Mode fully cracked via dynamic dump.

## PSU Max — PARTIALLY CRACKED (Layers 1-2)

| Directory | Status |
|---|---|
| `psu_max_mode/` | Layers 1-2 cracked (outer metatable-trap bypassed, LZW string decoded). Layer 3 (custom bytecode VM with delta-XOR stream cipher) still being reversed. |

### Plan
- [ ] Finalize `psu_max_mode/proto_dumper.py` to correctly parse instructions from `chunk_2.bin`.
- [ ] Map PSU Max opcodes to Lua instructions.

## Files uncrackable outside Roblox

- `evil_mode/one.lua` — requires Roblox `game` global
- `evil_mode/two.lua` — anti-tamper `error("You Are Lost!")` before payload executes
