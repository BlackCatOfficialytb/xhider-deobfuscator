# Lua VM De-obfuscator (XHider Edition)

A powerful, standalone Python toolchain designed to de-obfuscate and beautify Lua scripts protected by **XHider** style Virtual Machines.

## Discord Server

Join our Discord Server to get updates and support: [Discord Server](https://dsc.gg/blackcatofficial)

## ❓ Where is it?

You can find it in [This Discord Server](https://discord.gg/E2N7w35zkt), go to #〔⚫〕ᴏʙғᴜsᴄᴀᴛᴏʀ-ʟᴜᴀ , select Bot2, then use it.

## 🚀 Features

* **String De-obfuscation**: Automatically detects the VM function, extracts the hex pool and keys, and decrypts all embedded strings.
* **Intelligent Math Simplification**: A multi-pass reduction engine that simplifies complex constant expressions (e.g., `1+2*3 -> 7`) while strictly respecting Lua logic boundaries to prevent broken code.
* **Automatic Beautification**: Splits minified/fused Lua code into a clean, readable format with proper indentation and line breaks.
* **Safe VM Commenting**: Automatically wraps the original VM logic in long-bracket comments (`--[[ ... ]]`). It dynamically scales symbols (`--[==[`) if the code contains conflicting brackets.
* **String Protection**: Ensures that de-obfuscation and beautification never corrupt existing Lua strings or multi-line comments.

## 🛠️ Installation

Ensure you have **Python 3.x** installed. No external dependencies are required as the tool uses built-in Python libraries.

1. Clone or download this repository.
2. Place your obfuscated `.lua` files in the directory.

## 📖 Usage

Run the main script via terminal or command prompt:

```powershell
py unvm.py your_script.lua
```

The tool will process the file through 6 passes:

1. **Math Simplification**: Evaluating obfuscated numeric constants.
2. **Component Extraction**: Pulling the hex pool and Q-table keys.
3. **String Decoding**: Decrypting the VM-managed strings.
4. **Script Reconstruction**: Replacing VM calls with real strings.
5. **Beautification**: Re-formatting the entire script for readability.
6. **VM Commenting**: Safely archiving the VM logic within the file.

### Output

The de-obfuscated script will be saved as `<filename>.unvm.lua`.

## 📁 Project Structure

* **unvm.py**: The main entry point and de-obfuscation engine.
* **beautifier.py**: A robust Lua formatting module used for final output cleaning.
* **how_it_works.md**: Technical documentation of the de-obfuscation process.

## ⚠️ Notes

* This tool is specifically optimized for XHider obfuscation. Other obfuscators may require pattern adjustments in `unvm.py`.
* Always review the `.unvm.lua` output to ensure the VM function detection was 100% accurate for your specific file version.

---

*Created for advanced Lua reverse engineering.*
