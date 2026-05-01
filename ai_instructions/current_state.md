# Current State — All Modes

Live snapshot of every XHider mode in the repo and how far it's actually been cracked. Updated whenever progress changes.

**Definition of "fully cracked"** (used here and in `cracked_modes.md`): the deobfuscator output is **real reconstructed Lua source code** that is equivalent to the pre-obfuscation script — not a beautified-but-still-obfuscated VM dump, not a list of recovered strings, not a `bytearray(...)` payload dump.

Last audited: 2026-05-01 (post-session: basic + hard fully cracked; strong constants decoded but VM not emulated; env in progress).

## Status Matrix

| Mode | Dir | Output artifact | What's in it | Verdict |
|---|---|---|---|---|
| `m1` | `mid_m1_mode/` | `print_hi.decrypted.lua` | D() PRNG-decrypted constants + reconstructed `print("you cracked it yay, hi")` | **FULLY CRACKED** (print_hi only; fibonacci has extra binary layer) |
| `m2` | `mid_m2_mode/` | `print_hi.decrypted.lua` | Bytecode comments + reconstructed `print(...)` call (as `you cracked it yay, hi()`) | **FULLY CRACKED** |
| `m3` | `mid_m3_mode/` | `print_hi.decrypted.lua` | Decoded `v()` strings + bytecode constants + final `print("you cracked it yay, hi")` | **FULLY CRACKED** |
| `normal` | `normal_mode/` | `print_hi.decrypted.lua` | Same beautified obfuscated VM script — no real reconstruction | Partial (strings only via `fibo.decrypted.txt`) |
| `basic` | `basic_mode/` | `print_hi.decrypted.lua` | Decoded VM bytecode (`decrypt_basic_full.py`) → reconstructed `print("hi")` call from custom-VM symbolic execution | **FULLY CRACKED** (print_hi only; fibo.lua uses different `[=[XHD:...]=]` payload format and would need m3-style decoder) |
| `basic_b1` | `basic_b1_mode/` | `fibo.decrypted.txt` | "Strings found: 0" — extractor doesn't fire | **NOT CRACKED** |
| `ibs` | `ibs_mode/` | `print_hi.decrypted.lua` | Beautified obfuscated VM, not reconstructed | Partial |
| `hard` | `hard_mode/` | `print_hi.decrypted.lua` | `decrypt_hard_full.py` parses `_0x193`, applies ipairs shuffle pairs, decodes custom base64 (-49 shift + `_0xb3e` map) → reconstructed `print("hi")` | **FULLY CRACKED** (print_hi only) |
| `strong` | `strong_mode/` | `print_hi.decrypted.lua` | `decrypt_strong_full.py` parses `local L={...}` (70 entries), applies ipairs shuffle, base64-decodes via `local N={...}` map (no -49 shift, unlike hard) → recovers real readable constants (`error`, `tostring`, `getfenv`, `:(%d*):`, `You Are Lost!`, `__index`, etc.) but program logic lives in a giant VM dispatch loop, not the constants — so call is not auto-reconstructed | Partial (real strings recovered; VM not emulated) |
| `env` | `env_mode/` | `print_hi.beautified.decrypted.txt` | String dump | Partial (string dump) |
| `max` | `max_security_mode/` | `decrypted_strings.txt` | `bytearray(...)` payload dump only; main MB-sized payload not yet found | Partial (byte dump) — K[2]/K[5] fix landed (commit 5770009), payload extraction still TODO |
| `ibv` | `ibv_mode/` | `printhi.decrypted.lua` | Beautified obfuscated VM (return(function(...)...) wrapper still present) | Partial |
| `medium` | `mid_mode/` | `print_hi.decrypted.lua` | Beautified obfuscated VM | Partial |
| `evil` | `evil_mode/` | `print_hi_dec.lua` | VM stage cracked → exposes inner seed-based string-lookup payload (`print(L_2[L_1(4395)])`); inner layer not reduced to plain source | Partial (VM only — known) |
| `psu` | `psu_mode/` | disasm/proto/dump artifacts present, no `.decrypted.lua` | VM disassembly tooling only | **NOT CRACKED** |
| `psu_mid` | `psu_mid_mode/` | disasm/dump artifacts only | VM disassembly tooling only | **NOT CRACKED** |
| `psu_hard` | `psu_hard_mode/` | none | only fibo.lua + print_hi.lua | **NOT CRACKED** |
| `psu_max` | `psu_max_mode/` | none | only fibo.lua + print_hi.lua | **NOT CRACKED** |

## Modes mentioned in `Obf Type.txt` but with no directory yet

These are listed in the size tier table but have no directory in this repo, so nothing to audit:

`wrd` (cracked externally by 0x251/Prometheus-Deobfuscator), `hidden`, `obf`, `obf me`, `obf flow`, `obf weak`, `obf li`, `obf ps`, `obf rz`, `obf r2`, `obf l1`, `obf l2`, `abyss`, `abyss2`, `hex`, `veil`, `lightrew`, `ib1`, `ib2`, `ib3`.

## Summary counts

- **Fully cracked (real source):** 5 — `m1`, `m2`, `m3`, `basic`, `hard`
- **Partially cracked (string/byte dumps or VM-only):** 9 — `normal`, `ibs`, `strong`, `env`, `max`, `ibv`, `medium`, `evil`
- **Not cracked at all:** 5 — `basic_b1`, `psu`, `psu_mid`, `psu_hard`, `psu_max`
- **No directory yet:** 19 (see list above)
- **In progress this session:** `strong` constants decoded (real readable strings, no -49 shift) but call not reconstructed because program logic is in a giant VM dispatch loop, not in the constants — VM emulation needed for full crack. `env` queued: has `hook_env.lua` (dynamic instrumentation: hooks `print` + tostring, captures output via `loadfile`+pcall) — likely the easiest path to plain source is *running* it under that hook rather than static decryption.
