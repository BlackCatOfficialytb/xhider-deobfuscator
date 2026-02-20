# XHider Obfuscation Modes

XHider provides different security levels, each requiring a specific deobfuscation tactic.

## 1. Basic / Normal Mode (Basic modes is Limit < 300Kb, Normal modes is Limit < 100Kb)
- **Pattern**: Uses standard XOR or byte-shift encryption.
- **Key Extraction**: Look for a function (e.g., `a(p, B)`) that performs XOR in a loop.
- **Decryption**: Extract the encrypted string and XOR key, then replicate in Python.

## 2. IBS Mode (Limit < 100Kb)
- **Pattern**: Similar to Normal but with more "spaghetti code" and math obfuscation.
- **Tactic**: Simplify mathematical expressions first using `universal\simplify_math.py`.

## 3. Hard Mode (Limit < 100Kb)
- **Pattern**: Large table shuffling and multi-phase decryption.
- **Shuffling**: Uses an array of swap pairs `{start, end}`.
- **Decryption**: Involves a byte shift (e.g., `b - 49`) followed by a Base64-like decode using a custom alphabet map.

## 4. Strong Mode (Limit < 100Kb)
- **Pattern**: Complex Base64 decoding with custom alphabets.
- **Decryption**: Uses a map (e.g., `N`) where keys are characters and values are their 6-bit Base64 values. The decryption loop accumulates bits into bytes.

## 5. Max Security Mode (Limit < 100Kb)
- **Pattern**: Heavy fragmentation and nested loops.
- **String Reconstruction**: Strings are built by a function `a[8]` that takes a table of fragments and a list of indices, concatenating them.
- **VM Hooking**: The safest way is to hook the `return(function(...)` call at the end to dump the fully initialized `a[1]` (strings) and `a[3]` (bytecode/constants) tables.

## 6. Upcoming (env mode (Limit < 100Kb), evil mode (All sizes))