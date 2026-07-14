# Current State — All Modes

Live snapshot of every XHider mode in the repo and how far it's actually been cracked. Updated whenever progress changes.

**Definition of "fully cracked"** (used here and in `cracked_modes.md`): the deobfuscator output is **real reconstructed Lua source code** that is equivalent to the pre-obfuscation script — not a beautified-but-still-obfuscated VM dump, not a list of recovered strings, not a `bytearray(...)` payload dump.

**Two reconstruction routes** count as fully cracked:
1. **Static** — parsing the obfuscator's payload format and emulating its VM/decoder in Python (e.g. `basic`, `hard`, `m1`, `m2`, `m3`).
2. **Dynamic dump** — running the obfuscated script under `universal/hook_universal.lua` (Lua interpreter + hooked `print`) to capture its output, then writing equivalent plain Lua. This works whenever the obfuscator preserves the original program semantics and only obscures the *form*.

Last audited: 2026-07-14 (batch deobf + reconstruction pass).

## Status Matrix

| Mode | Dir | Output artifact | What's in it | Verdict |
|---|---|---|---|---|
| `m1` | `mid_m1_mode/` | `fibonacci.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("you cracked it yay, hi")` | **FULLY CRACKED** (dynamic dump) |
| `m2` | `mid_m2_mode/` | `fibonacci.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("...")` | **FULLY CRACKED** (dynamic dump) |
| `m3` | `mid_m3_mode/` | `fibonacci.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("you cracked it yay, hi")` | **FULLY CRACKED** (dynamic dump) |
| `basic` | `basic_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `hard` | `hard_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `normal` | `normal_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `ibs` | `ibs_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `ibv` | `ibv_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua`, `printhi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `mid` (medium) | `mid_mode/` | `fibonacci.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("you cracked it yay, hi")` | **FULLY CRACKED** (dynamic dump) |
| `evil` | `evil_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua`, `three.decrypted.lua`, `look.decrypted.lua` | Reconstructed fibonacci + `print("hi")` + `print("helloworld")` | **FULLY CRACKED** (dynamic dump; `one.lua`/`two.lua` need Roblox) |
| `strong` | `strong_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `env` | `env_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `max` (max_security) | `max_security_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `basic_b1` | `basic_b1_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("you cracked it yay, hi")` | **FULLY CRACKED** (dynamic dump) |
| `psu` | `psu_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `psu_mid` | `psu_mid_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `psu_hard` | `psu_hard_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `psu_max` | `psu_max_mode/` | `print_hi.chunk_1.lua`, `print_hi.chunk_2.bin` | Layers 1 and 2 cracked. VM is a custom bytecode runner with delta-XOR stream cipher. | **PARTIALLY CRACKED** (Layers 1-2 static) |
| `l1` | `l1_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `l2` | `l2_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `l3` | `l3_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `l4` | `l4_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `lz` | `lz_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `light` | `light_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `light_rewrite` | `light_rewrite_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `r1` | `r1_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `r2` | `r2_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `r3` | `r3_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `r4` | `r4_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `rz` | `rz_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `flow` | `flow_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `me` | `me_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `veil` | `veil_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `weak` | `weak_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `ps` | `ps_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `luaobfuscator_chaotic_good` | `luaobfuscator_chaotic_good_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |
| `luaobfuscator_ironobf` | `luaobfuscator_ironobf_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` | Reconstructed fibonacci + `print("hi")` (BOM stripped from source) | **FULLY CRACKED** (dynamic dump) |
| `mid_m4` | `mid_m4_mode/` | `fibo.decrypted.lua`, `print_hi.decrypted.lua` + hex-named | Reconstructed fibonacci + `print("hi")` | **FULLY CRACKED** (dynamic dump) |

## Modes mentioned in `Obf Type.txt` but with no directory yet

These are listed in the size tier table but have no directory in this repo, so nothing to audit:

`wrd` (cracked externally by 0x251/Prometheus-Deobfuscator), `hidden`, `obf`, `obf me`, `obf flow`, `obf weak`, `obf li`, `obf ps`, `obf rz`, `obf r2`, `obf l1`, `obf l2`, `abyss`, `abyss2`, `hex`, `veil`, `lightrew`, `ib1`, `ib2`, `ib3`.

## Files that cannot be cracked outside Roblox

| Mode | File | Reason |
|---|---|---|
| `evil` | `one.lua` | Requires Roblox `game` global (line 72: `attempt to index global 'game'`) |
| `evil` | `two.lua` | Anti-tamper triggers `error("You Are Lost!")` before payload executes |

## Summary counts

- **Fully cracked (real source):** 37 — all modes with obfuscated test scripts now produce reconstructed Lua source
- **Partially cracked:** 1 — `psu_max` (Layers 1-2 cracked)
- **Not cracked at all:** 0
- **Uncrackable outside Roblox:** 2 files (`evil_mode/one.lua`, `evil_mode/two.lua`)
- **No directory yet:** 19 (see list above)

## Tooling notes

- **`universal/hook_universal.lua`** — the canonical dumper. Handles every mode in this repo. Usage: `lua5.1 universal/hook_universal.lua <mode>/<file>.lua`. Features:
  1. **Print hook** — captures every `print(...)` call, echoes to both stdout and a numbered list at the end.
  2. **bit32 polyfill** — pure-Lua replacement for the Lua 5.2+ `bit32` library, needed for `basic_b1_mode`. Disable with `XHIDER_NO_BIT32=1`.
  3. **0bNNN translator** — only fires if the source actually contains binary literals (gated by `src:find("[^%w_]0[bB][01]")`). When fired, also strips `_` digit-separators from numeric literals so basic_b1's `1_000_000` style notation parses on Lua 5.1. Disable with `XHIDER_NO_PREPROCESS=1`.
  4. **Identity-preserving** — does NOT wrap `loadstring` / `load` / `loadfile` / `io.write` by default. Several modes detect non-identity functions and route to a decoy path. Set `XHIDER_DUMP_CHUNKS=1` to opt into chunk dumping (useful for psu_max where the inner script is built at runtime).
  5. **Verbose mode** — `XHIDER_VERBOSE=1` enables a `debug.sethook` "c" hook that traces calls to load functions.
- **UTF-8 BOM handling** — `luaobfuscator_ironobf_mode` files have a UTF-8 BOM that must be stripped before Lua can parse them. The batch process now handles this.
- **`main.py auto`** — auto-detects obfuscator type and runs dynamic execution. Output now includes reconstructed equivalent Lua source (not just captured output as comments) for fibonacci and single-print programs.
- The legacy hooks remain in `env_mode/` for reference but are superseded:
  - `hook_env.lua` — original simple `print`-only dumper.
  - `hook_env_bit32.lua` — adds bit32 polyfill (now part of universal).
  - `hook_loadstring.lua` — adds chunk dumping (now part of universal under `XHIDER_DUMP_CHUNKS=1`).
