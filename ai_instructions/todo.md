# Max Security Deobfuscation Status & Todo

**Status:**
Paused debugging `decrypt_max_v2.py`. The script currently correctly identifies the Layer 1 and 2 mapping, but the extraction of `K[2]` Base64 map fails to grab all 64 characters. 

## Key Technical Revelations
1. **Scope of K[2] vs K[10]:** 
   - `K[2]` contains 64 entries, mapping single characters to `0-63` values for the first Base64 decode loop (processing payload chunks).
   - `K[10]` contains 64 entries for the second Base64 decode loop (processing `a[6]`). 
   - They **do not** need to be merged.

2. **Why K[2] mapping is incomplete in Python:**
   - 28 of the 64 keys in `K[2]` reference `a[7]` indices that contain multi-byte strings (like `81505A09...`).
   - My python script (`decrypt_max_v2.py`) skipped these keys because `len(key) != 1`.
   - In the Lua script, these hex-encoded strings are decoded using the `K[5]` hex map IN-PLACE and are transformed into *single-character* strings (via `table.concat(H[1])`) before `K[2]` uses them as keys. 
   - My Python script's `custom_hex_decode` is blindly decoding them into long strings (e.g., `kyx...`) because it lacks the specific length conditions present in Lua (`if K[6](V[2]) == length then`). 

3. **MISSING PAYLOAD BLOB:**
   - The arrays we've been analyzing (`a[3]`, `a[6]`, `a[7]`) **do not contain the main bytecode payload**.
   - `a[7]` contains a total of only ~6KB of data.
   - `print_hi.lua` is several megabytes. The massive payload string is hidden somewhere else in the file (likely outside the basic `a={}` struct, or inside another array variable).

## Next Steps (TODO)
- [ ] **Find the Massive Payload String:** Search through `print_hi.lua` using regex (`r'\"([^\"]{1000,})\"'` or similar in Python) to locate the actual multi-megabyte string storing the Base64 payload.
- [ ] **Fix K[2] Extraction:** Refactor the extraction of `K[2]`/`K[10]` in `decrypt_max_v2.py`. Instead of reading from `a[7]` and discarding `len != 1`, we must perfectly mimic the `K[5]` hex-decoding to get the right 1-byte keys.
- [ ] **Revert K[2]/K[10] Map Merge:** Remove the code merging `K[10]` into `K[2]` inside `decrypt_max_v2.py` as they belong to entirely separate decode scopes.
- [ ] **Implement Complete Decode Chain:** Apply the fully populated 64-char `K[2]` map over the *actual* massive payload string to extract the `\x1bLua` bytecode.
