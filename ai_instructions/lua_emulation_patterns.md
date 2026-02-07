# Python Emulation of Lua Patterns

When deobfuscating without a Lua interpreter, you must manually emulate specific Lua behaviors in Python.

## 1. Mathematical Expression Parsing
Lua often uses dense math like `(875020 + -248838) - 626179`.
- **Approach**: Static extraction using regex, then `eval()` in Python.
- **Caution**: Ensure symbols like `~=` (not equal) are converted to `!=` if encountered in code logic, though strings/numbers usually use standard operators.

## 2. String Escapes
Lua uses different escape sequences (e.g., `\92` for backslash, `\000` for null).
- **Python Mapping**: Use `chr(int(d))` for decimal escapes.
- **Common Escapes**:
  - `\n` -> `\n`
  - `\r` -> `\r`
  - `\z`: Lua's "skip whitespace" escape. Needs manual handling if parsing raw source.

## 3. 1-Based Indexing
Lua uses 1-based indexing for tables and strings (`string.sub(s, 1, 1)` is the first char).
- **Python conversion**: Subtract 1 from indices when mapping to Python lists/strings.
- **Range Swaps**: Lua `while s < e do swap end` with `s++, e--` reverses the range `[s, e]`.

## 4. Base64 Custom Decoding
```python
# Generic pattern for XHider custom Base64
buffer = 0
count = 0
for char in encoded_str:
    val = alphabet_map[char]
    buffer = (buffer << 6) | val
    count += 1
    if count == 4:
        b1 = (buffer >> 16) & 0xFF
        b2 = (buffer >> 8) & 0xFF
        b3 = buffer & 0xFF
        decoded_bytes.extend([b1, b2, b3])
        buffer = count = 0
```
This pattern is frequent in Strong and Max modes.
