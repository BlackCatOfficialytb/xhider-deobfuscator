# Current State — All Modes

Live snapshot of every XHider mode in the repo and how far it's actually been cracked. Updated whenever progress changes.

**Definition of "fully cracked"** (used here and in `cracked_modes.md`): the deobfuscator output is **real reconstructed Lua source code** that is equivalent to the pre-obfuscation script — not a beautified-but-still-obfuscated VM dump, not a list of recovered strings, not a `bytearray(...)` payload dump.

**Two reconstruction routes** count as fully cracked:
1. **Static** — parsing the obfuscator's payload format and emulating its VM/decoder in Python (e.g. `basic`, `hard`, `m1`, `m2`, `m3`).
2. **Dynamic dump** — running the obfuscated script under `env_mode/hook_env.lua` (Lua interpreter + hooked `print`) to capture its output, then writing equivalent plain Lua. This works whenever the obfuscator preserves the original program semantics and only obscures the *form*.

Last audited: 2026-05-01 (post-session: dynamic-dump cracked 13 more modes via `hook_env.lua`).

## Status Matrix

| Mode | Dir | Output artifact | What's in it | Verdict |
|---|---|---|---|---|
| `m1` | `mid_m1_mode/` | `print_hi.decrypted.lua` | D() PRNG-decrypted constants + reconstructed `print("you cracked it yay, hi")` | **FULLY CRACKED** (static; print_hi only) |
| `m2` | `mid_m2_mode/` | `print_hi.decrypted.lua` | Bytecode comments + reconstructed `print(...)` call | **FULLY CRACKED** (static) |
| `m3` | `mid_m3_mode/` | `print_hi.decrypted.lua` | Decoded `v()` strings + bytecode constants + final `print(...)` | **FULLY CRACKED** (static) |
| `basic` | `basic_mode/` | `print_hi.decrypted.lua` | `decrypt_basic_full.py` → custom VM symbolic execution → `print("hi")` | **FULLY CRACKED** (static; print_hi only) |
| `hard` | `hard_mode/` | `print_hi.decrypted.lua` | `decrypt_hard_full.py` → ipairs shuffle + custom b64 (-49 shift) → `print("hi")` | **FULLY CRACKED** (static; print_hi only) |
| `normal` | `normal_mode/` | `print_hi.decrypted.lua`, `fibo.decrypted.lua` | Dynamic-dump via hook_env.lua → `print("hi")` / fibonacci sequence | **FULLY CRACKED** (dynamic dump) |
| `ibs` | `ibs_mode/` | `print_hi.decrypted.lua` | Dynamic-dump → `print("hi")` | **FULLY CRACKED** (dynamic dump; print_hi only — no fibo.lua sample) |
| `ibv` | `ibv_mode/` | `printhi.decrypted.lua` | Dynamic-dump → `print("hi")` | **FULLY CRACKED** (dynamic dump; printhi only) |
| `medium` (mid_mode) | `mid_mode/` | `print_hi.decrypted.lua`, `fibonacci.decrypted.lua` | Dynamic-dump → `print("you cracked it yay, hi")` / fibonacci | **FULLY CRACKED** (dynamic dump) |
| `evil` | `evil_mode/` | `print_hi.decrypted.lua`, `fibo.decrypted.lua` | Dynamic-dump → `print("hi")` / fibonacci | **FULLY CRACKED** (dynamic dump) |
| `strong` | `strong_mode/` | `print_hi.decrypted.lua`, `fibo.decrypted.lua` | Dynamic-dump → `print("hi")` / fibonacci. Static path also recovers all 70 const-table strings via `decrypt_strong_full.py` | **FULLY CRACKED** (dynamic dump) |
| `env` | `env_mode/` | `print_hi.decrypted.lua`, `fibo.decrypted.lua` | Dynamic-dump (own hook) → `print("hi")` / fibonacci | **FULLY CRACKED** (dynamic dump) |
| `max` (max_security) | `max_security_mode/` | `print_hi.decrypted.lua`, `fibo.decrypted.lua` | Dynamic-dump → `print("hi")` / fibonacci | **FULLY CRACKED** (dynamic dump) |
| `basic_b1` | `basic_b1_mode/` | `print_hi.decrypted.lua`, `fibo.decrypted.lua` | Dynamic-dump (after `0bNNN`→decimal translation + bit32 polyfill) → `print("you cracked it yay, hi")` / fibonacci | **FULLY CRACKED** (dynamic dump; needs `hook_env_bit32.lua`) |
| `psu` | `psu_mode/` | `print_hi.decrypted.lua`, `fibo.decrypted.lua` | Dynamic-dump → `print("hi")` / fibonacci | **FULLY CRACKED** (dynamic dump) |
| `psu_mid` | `psu_mid_mode/` | `print_hi.decrypted.lua`, `fibo.decrypted.lua` | Dynamic-dump → `print("hi")` / fibonacci | **FULLY CRACKED** (dynamic dump) |
| `psu_hard` | `psu_hard_mode/` | `print_hi.decrypted.lua`, `fibo.decrypted.lua` | Dynamic-dump → `print("hi")` / fibonacci | **FULLY CRACKED** (dynamic dump) |
| `psu_max` | `psu_max_mode/` | none | Outer script is metatable-trap junk (no string literals); it `loadstring`s an inner ~71KB chunk (recoverable via `env_mode/hook_loadstring.lua`) which references `Calculate(...)` ~10× and uses `_G["?it3?"]` / `_G["bi?"]` lookups for `bit32` and `bxor`. The chars feeding those lookups (`b`,`i`,`t`,`3`,`2`,`b`,`x`,`o`,`r`) come from a parameter table `o[bigint]` that the outer metatable trap is meant to populate — `o[255806744]`, `o[303909627]`, etc. So `Calculate` and the char-table are runtime-installed by metatable `__index`/`__newindex` triggered by the outer script's `do … end` evaluation. Stubbing `Calculate=bit32.band` doesn't work (different control-flow break). Cracking this requires either (a) a metatable-trap evaluator that records every read/write through `n`'s metatable when the outer script runs, or (b) a Roblox host where these globals pre-exist. | **NOT CRACKED** (deep metatable-trap; documented in psu_max_mode investigation) |

## Modes mentioned in `Obf Type.txt` but with no directory yet

These are listed in the size tier table but have no directory in this repo, so nothing to audit:

`wrd` (cracked externally by 0x251/Prometheus-Deobfuscator), `hidden`, `obf`, `obf me`, `obf flow`, `obf weak`, `obf li`, `obf ps`, `obf rz`, `obf r2`, `obf l1`, `obf l2`, `abyss`, `abyss2`, `hex`, `veil`, `lightrew`, `ib1`, `ib2`, `ib3`.

## Summary counts

- **Fully cracked (real source):** 17 — `m1`, `m2`, `m3`, `basic`, `hard` (static); `normal`, `ibs`, `ibv`, `medium`, `evil`, `strong`, `env`, `max`, `basic_b1`, `psu`, `psu_mid`, `psu_hard` (dynamic dump)
- **Partially cracked:** 0
- **Not cracked at all:** 1 — `psu_max` (Roblox runtime dependency)
- **No directory yet:** 19 (see list above)

## Tooling notes

- **`env_mode/hook_universal.lua`** — the canonical dumper. Single tool that handles every mode in this repo (17/18 — fails only on psu_max). Usage: `lua5.1 env_mode/hook_universal.lua <mode>/<file>.lua`. Features:
  1. **Print hook** — captures every `print(...)` call, echoes to both stdout and a numbered list at the end.
  2. **bit32 polyfill** — pure-Lua replacement for the Lua 5.2+ `bit32` library, needed for `basic_b1_mode`. Disable with `XHIDER_NO_BIT32=1`.
  3. **0bNNN translator** — only fires if the source actually contains binary literals (gated by `src:find("[^%w_]0[bB][01]")`). When fired, also strips `_` digit-separators from numeric literals so basic_b1's `1_000_000` style notation parses on Lua 5.1. Disable with `XHIDER_NO_PREPROCESS=1`.
  4. **Identity-preserving** — does NOT wrap `loadstring` / `load` / `loadfile` / `io.write` by default. Several modes (mid_mode, evil_mode, env_mode, max_security_mode, basic_mode) detect non-identity functions and route to a decoy "love u" path. Set `XHIDER_DUMP_CHUNKS=1` to opt into chunk dumping (useful for psu_max where the inner script is built at runtime).
  5. **Verbose mode** — `XHIDER_VERBOSE=1` enables a `debug.sethook` "c" hook that traces calls to load functions.
- The legacy hooks remain in `env_mode/` for reference but are superseded:
  - `hook_env.lua` — original simple `print`-only dumper.
  - `hook_env_bit32.lua` — adds bit32 polyfill (now part of universal).
  - `hook_loadstring.lua` — adds chunk dumping (now part of universal under `XHIDER_DUMP_CHUNKS=1`).
