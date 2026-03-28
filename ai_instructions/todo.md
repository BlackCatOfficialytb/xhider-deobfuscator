# XHider Deobfuscator — Master Todo

## Project Status Overview

| Mode | Status | Key Script |
|------|--------|------------|
| Basic | Done | `basic_mode/decrypt_basic.py` |
| Normal | Done | `normal_mode/decrypt_normal.py` |
| IBS | Done | `ibs_mode/dump_strings_ibs.py` |
| Hard | Done | `hard_mode/decrypt_hard.py` |
| Strong | Done | `strong_mode/decrypt_strong.py` |
| Max Security | **In Progress** | `max_security_mode/decrypt_max_v2.py` |
| Env Mode | Not Started | — |
| Evil Mode | Not Started | — |

---

## 1. Max Security Mode (ACTIVE — Critical Priority)

**Status:** Paused debugging `decrypt_max_v2.py` (1011 lines). Layers 1 & 2 mapping work, but K[2] Base64 map extraction only gets 36/64 characters.

### Key Technical Revelations

1. **Scope of K[2] vs K[10]:**
   - `K[2]`: 64 entries for first Base64 decode (payload chunks).
   - `K[10]`: 64 entries for second Base64 decode (`a[6]` processing).
   - They **do not** need to be merged.

2. **Why K[2] mapping is incomplete in Python:**
   - 28 of 64 keys reference `a[7]` indices with multi-byte hex strings (`81505A09...`).
   - Python script skips them (`len(key) != 1`).
   - In Lua, these are decoded via `K[5]` hex map and condensed to 1-char via `table.concat(H[1])`.
   - Python's `custom_hex_decode` lacks the length conditions (`if K[6](V[2]) == length then`).

3. **MISSING PAYLOAD BLOB:**
   - `a[3]`, `a[6]`, `a[7]` contain only ~6KB of data.
   - `print_hi.lua` is 169KB — the massive payload string is hidden elsewhere.

### Todo — Max Security

- [ ] **Find the Massive Payload String:** Search `print_hi.lua` using regex (`r'"([^"]{1000,})"'`) to locate the multi-KB Base64 payload blob.
- [ ] **Fix K[2] Extraction:** Refactor to perfectly mimic K[5] hex-decoding logic (respect `K[6](V[2]) == length` conditions) instead of filtering by `len != 1`.
- [ ] **Revert K[2]/K[10] Map Merge:** Separate decode scopes in `decrypt_max_v2.py` — remove code merging K[10] into K[2].
- [ ] **Implement Complete Decode Chain:** Apply the fully populated 64-char K[2] map to the actual payload string to extract `\x1bLua` bytecode.
- [ ] **Validate Output:** Confirm the extracted bytecode starts with `\x1bLua` (Lua 5.1 header) or `\x1bLuaS` (Luau).
- [ ] **Wire into main.py:** Ensure `decrypt_max_v2.py` accepts `-i`/`-o` CLI args (currently uses hardcoded paths like `d:\dec bot2\...`).
- [ ] **Cleanup Debug Scripts:** Consolidate or archive the ~15 debug/analysis scripts in `max_security_mode/` once the main decoder works.

---

## 2. Env Mode (Planned)

**Status:** Not started. Only a test file `env_mode/print_hi.lua` exists.

- [ ] **Analyze env mode obfuscation:** Study `env_mode/print_hi.lua` to identify the obfuscation pattern (environment variable manipulation, `getfenv`/`setfenv` hooks, etc.).
- [ ] **Document env mode pattern:** Add pattern description to `ai_instructions/xhider_modes.md`.
- [ ] **Implement `decrypt_env.py`:** Build the deobfuscation script with `-i`/`-o` support.
- [ ] **Wire into main.py:** Add `env` mode to the CLI dispatcher.
- [ ] **Test and validate:** Confirm correct deobfuscation of `env_mode/print_hi.lua`.

---

## 3. Evil Mode (Planned)

**Status:** Not started. Three test files exist: `evil_mode/one.lua`, `two.lua`, `three.lua`. This is the most complex mode — handles all file sizes (no 100KB limit).

- [ ] **Analyze evil mode obfuscation:** Study all three test files to understand the obfuscation layers and how evil mode differs from max security.
- [ ] **Document evil mode pattern:** Add pattern description to `ai_instructions/xhider_modes.md`.
- [ ] **Implement `decrypt_evil.py`:** Build the deobfuscation script (likely the most complex of all modes).
- [ ] **Wire into main.py:** Add `evil` mode to the CLI dispatcher.
- [ ] **Test with multiple file sizes:** Validate against `one.lua`, `two.lua`, and `three.lua`.

---

## 4. Universal Tools & Infrastructure

- [ ] **Implement auto-detection mode:** `main.py -m auto` currently does nothing. Implement heuristic detection that identifies the obfuscation mode automatically based on file patterns/structure.
- [ ] **Standardize CLI interface:** Some mode scripts use hardcoded paths instead of `-i`/`-o` args. Ensure all scripts follow the same CLI pattern.
- [ ] **Add error handling to main.py:** The mode dispatcher doesn't handle subprocess failures gracefully.
- [ ] **Test suite:** Create a basic test harness that runs each mode's decoder against its `print_hi.lua` and validates the output.

---

## 5. Discord Bot (`Bot.js`)

- [ ] **Add env mode support:** Wire new env mode into the bot's command options.
- [ ] **Add evil mode support:** Wire evil mode once the decoder is ready.
- [ ] **Add max security mode support:** Ensure the bot can invoke `decrypt_max_v2.py` once it's finalized.

---

## 6. Documentation

- [ ] **Update README.md:** Add env and evil modes to the supported modes table once implemented.
- [ ] **Update `xhider_modes.md`:** Complete mode descriptions for env and evil modes.
- [ ] **Document the full decode pipeline for max security:** Write up the multi-layer decode chain (K[2], K[4], K[5], K[10]) once finalized.

---

## Priority Order

1. **Max Security** — Fix K[2] extraction + find payload blob (unblocks everything else for this mode)
2. **Env Mode** — Likely simpler than max security, good next target
3. **Evil Mode** — Most complex, tackle last
4. **Auto-detection** — Quality of life, implement after all modes work
5. **Bot integration** — Wire modes in as they become ready
6. **Documentation** — Update as features land
