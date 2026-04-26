# XHider Obfuscation Modes

XHider provides different security levels, each requiring a specific deobfuscation tactic.

## 1. Basic / Normal Mode
- **Pattern**: Uses standard XOR or byte-shift encryption.
- **Key Extraction**: Look for a function (e.g., `a(p, B)`) that performs XOR in a loop.
- **Decryption**: Extract the encrypted string and XOR key, then replicate in Python.

## 2. IBS Mode
- **Pattern**: Similar to Normal but with more "spaghetti code" and math obfuscation.
- **Tactic**: Simplify mathematical expressions first using `universal\simplify_math.py`.

## 3. Hard Mode
- **Pattern**: Large table shuffling and multi-phase decryption.
- **Shuffling**: Uses an array of swap pairs `{start, end}`.
- **Decryption**: Involves a byte shift (e.g., `b - 49`) followed by a Base64-like decode using a custom alphabet map.

## 4. Strong Mode
- **Pattern**: Complex Base64 decoding with custom alphabets.
- **Decryption**: Uses a map (e.g., `N`) where keys are characters and values are their 6-bit Base64 values. The decryption loop accumulates bits into bytes.

## 5. Max Security Mode
- **Pattern**: Heavy fragmentation and nested loops.
- **String Reconstruction**: Strings are built by a function `a[8]` that takes a table of fragments and a list of indices, concatenating them.
- **VM Hooking**: The safest way is to hook the `return(function(...)` call at the end to dump the fully initialized `a[1]` (strings) and `a[3]` (bytecode/constants) tables.

## 6. IBV Mode (Internal Bytecode-Based Variant)
- **Size Limit**: < 300KB (medium-scale protection).
- **Pattern**: Custom hex nibble encoding with a shuffled alphabet map.
- **Structure**:
  1. Outer `return(function(...)` wrapper containing a mixed data table (`v_0`) with booleans, obfuscated numbers, and hex-encoded strings (e.g., `"9F9F85898A"`).
  2. An accessor function `v_1(x) = v_0[x - offset]` for indirect table lookups.
  3. A shuffle phase using `ipairs({{start,end}, ...})` that reverses ranges within the data table.
  4. A **custom hex alphabet** table mapping chars `0-9, A-F` to **non-standard** values 0-15 (e.g., `E=0, 4=1, C=2, 7=3, 1=4, 9=5, 8=6, B=7, 2=8, 3=9, D=10, 0=11, 5=12, 6=13, A=14, F=15`).
  5. A decoding loop that processes each string 2 characters at a time: `high_nibble * 16 + low_nibble` → `string.char(value)`.
- **Key Difference from Hard Mode**: Uses 2-char hex-nibble pairs (not 4-char base64 groups). The alphabet has only 16 entries (0-15) instead of 64.
- **Decryption Pipeline**:
  1. Simplify all obfuscated math expressions to reveal constants.
  2. Extract and parse the data table.
  3. Apply shuffle pairs to reorder the table.
  4. Extract the custom hex alphabet (look for a `local v_N = {E=0, ["4"]=1, ...}` table with 16 entries mapping to values 0-15).
  5. Decode each hex string: for every 2-char pair, map each char through the alphabet, combine as `high*16 + low`, convert to `chr()`.
  6. Resolve accessor calls by substituting decoded values.
- **Math Obfuscation**: All constants (shuffle indices, accessor offsets, alphabet values, even the multiplier `16` for nibble combination) are hidden behind arithmetic expressions like `(4724288-(558336-850304))-(507712-(-412032))`.
- **Tool**: `ibv_mode/decrypt_ibv.py`
