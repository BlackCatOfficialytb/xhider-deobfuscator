#!/usr/bin/env python3
"""
XHider Deobfuscator Tool - CLI
===============================
Deobfuscates Lua scripts protected by XHider v1.2 (and other obfuscators).

Modes:
  auto       - Auto-detect obfuscator from file signatures and deobfuscate
  bruteforce - Try ALL known XHider sub-modes on a single script
  custom     - Manually select the obfuscator/mode to use

Usage:
  python main.py auto -i script.lua [-o output.lua]
  python main.py bruteforce -i script.lua [-o output_dir]
  python main.py custom -i script.lua --mode basic [-o output.lua]

Requirements:
  - Python 3.8+
  - Lua 5.1+ (optional, for dynamic execution mode)
"""

# Nuitka build configuration (read when compiling: .venv\Scripts\python -m nuitka main.py)
# nuitka-project: --onefile
# nuitka-project: --assume-yes-for-downloads
# nuitka-project: --include-data-dir={MAIN_DIRECTORY}/universal=universal
# nuitka-project: --nofollow-import-to=numpy
# nuitka-project: --nofollow-import-to=imageio
# nuitka-project: --nofollow-import-to=tkinter
# nuitka-project: --output-dir={MAIN_DIRECTORY}/dist-nuitka
# nuitka-project: --output-filename=decbot.exe

import os
import sys
import re
import json
import time
import shutil
import argparse
import subprocess
import traceback
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# =============================================================================
# Constants
# =============================================================================

VERSION = "2.0.0"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HOOK_SCRIPT = os.path.join(SCRIPT_DIR, "universal", "hook_universal.lua")

# Known XHider v1.2 sub-modes
XHIDER_MODES = [
    "basic", "basic_1", "basic_b1",
    "abyss", "abyss2",
    "evil",
    "hard", "strong",
    "normal",
    "ibs", "ibv",
    "mid", "mid_m1", "mid_m2", "mid_m3", "mid_m4",
    "psu", "psu_mid", "psu_hard", "psu_max",
    "ps",
    "l1", "l2", "l3", "l4", "lz",
    "light", "light_rewrite",
    "r1", "r2", "r3", "r4", "rz",
    "flow",
    "me",
    "veil",
    "weak",
    "max_security",
    "luaobfuscator_chaotic_good", "luaobfuscator_ironobf",
]

# Other supported obfuscators (extensible)
OTHER_OBFUSCATORS = [
    "moonsec",
    "ironbrew",
    "unknown",
]

ALL_MODES = XHIDER_MODES + OTHER_OBFUSCATORS


# =============================================================================
# Data Classes
# =============================================================================

class ObfuscatorType(Enum):
    XHIDER = "xhider"
    MOONSEC = "moonsec"
    IRONBREW = "ironbrew"
    LUAFUZZER = "luafuzzer"
    PSYCHOBUTCHER = "psychobutcher"
    LUAOBFUSCATOR = "luaobfuscator"
    UNKNOWN = "unknown"


@dataclass
class DetectionResult:
    obfuscator: ObfuscatorType = ObfuscatorType.UNKNOWN
    version: str = ""
    sub_mode: str = ""
    features: List[str] = field(default_factory=list)
    xor_keys: List[int] = field(default_factory=list)
    encoding: str = ""
    has_bytecode_vm: bool = False
    has_state_machine: bool = False
    has_anti_debug: bool = False
    has_bit32: bool = False
    has_binary_literals: bool = False
    has_base85: bool = False
    has_base64: bool = False
    has_hex_pool: bool = False
    has_obfuscated_math: bool = False
    confidence: float = 0.0


@dataclass
class DeobfResult:
    success: bool = False
    method: str = ""
    output: str = ""
    strings: Dict[int, bytes] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    elapsed: float = 0.0


# =============================================================================
# Lua Helpers
# =============================================================================

def lua_unescape(s: str) -> str:
    """Unescape a Lua string literal."""
    res, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c == '\\' and i + 1 < n:
            nx = s[i + 1]
            if nx.isdigit():
                d = nx; j = i + 2
                while j < n and j < i + 4 and s[j].isdigit():
                    d += s[j]; j += 1
                res.append(chr(int(d))); i = j
            elif nx == 'n': res.append('\n'); i += 2
            elif nx == 'r': res.append('\r'); i += 2
            elif nx == 't': res.append('\t'); i += 2
            elif nx == '\\': res.append('\\'); i += 2
            elif nx == '"': res.append('"'); i += 2
            elif nx == "'": res.append("'"); i += 2
            elif nx == 'a': res.append('\a'); i += 2
            elif nx == 'b': res.append('\b'); i += 2
            else: res.append(nx); i += 2
        else:
            res.append(c); i += 1
    return "".join(res)


def decode_base85(payload: str) -> List[int]:
    """XHider base85 (base-n with charset 0x21..0x75) decode.
    Each group of 5 chars → 4 bytes.
    """
    result = []
    n = 1
    U = len(payload)
    while n <= U:
        if ord(payload[n - 1]) == 0x7A:  # 'z' = 4 zero bytes
            result.extend([0] * 4)
            n += 1
        else:
            a = 0
            X = 5
            if n + 4 > U:
                X = (U - n) + 1
            for j in range(1, X + 1):
                a = a * 0x55 + (ord(payload[n + j - 2]) - 0x21)
            for j in range(X + 1, 6):
                a = a * 0x55 + 0x54
            result.extend([
                (a >> 24) & 0xFF,
                (a >> 16) & 0xFF,
                (a >> 8) & 0xFF,
                a & 0xFF,
            ])
            n += (5 if X == 5 else X)
    return result


def decode_base64_b64(payload: str) -> List[int]:
    """Standard base64 decode."""
    import base64
    # Pad if necessary
    pad = len(payload) % 4
    if pad:
        payload += '=' * (4 - pad)
    return list(base64.b64decode(payload))


def decrypt_xor(data: List[int], offset: int, keys: List[int]) -> Optional[bytes]:
    """Decrypt a string at offset using XOR key wheel."""
    if offset + 3 >= len(data):
        return None
    key_len = len(keys)
    length = 0
    for i in range(min(4, key_len)):
        length |= (data[offset + i] ^ keys[i % key_len]) << (8 * i)
    if length > 500000 or offset + 4 + length > len(data):
        return None
    out = bytes(data[offset + 4 + j] ^ keys[(4 + j) % key_len] for j in range(length))
    return out


def find_lua_binaries() -> List[str]:
    """Find available Lua binaries on the system."""
    candidates = [
        "lua5.1", "lua5.2", "lua5.3", "lua5.4",
        "luajit", "luajit2",
        "lua",
    ]
    found = []
    for name in candidates:
        path = shutil.which(name)
        if path:
            found.append(path)
    # Check common paths
    common = [
        "/usr/local/bin/lua5.1",
        "/usr/local/bin/lua5.4",
        "/usr/bin/lua5.1",
        "/usr/bin/lua5.4",
        "/opt/homebrew/bin/lua5.1",
        "/tmp/lua",
    ]
    for p in common:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            if p not in found:
                found.append(p)
    return found


# =============================================================================
# Detector
# =============================================================================

class ObfuscatorDetector:
    """Analyzes Lua source code to detect the obfuscator and its sub-mode."""

    def detect(self, content: str, filepath: str = "") -> DetectionResult:
        result = DetectionResult()
        result.features = []
        result.xor_keys = []

        # Check file header for obfuscator signatures
        first_line = content.split('\n')[0] if content else ""
        header = content[:2000]

        # XHider detection
        xhider_match = re.search(r'[Xx][Hh]ider.*?v(\d[\d.]*)\w*', header)
        if xhider_match:
            result.obfuscator = ObfuscatorType.XHIDER
            result.version = xhider_match.group(1)
            result.confidence = 0.95
            result.features.append(f"xhider_v{result.version}")
        elif re.search(r'[Xx][Hh]ider', header):
            result.obfuscator = ObfuscatorType.XHIDER
            result.confidence = 0.85
            result.features.append("xhider_header")
        elif re.search(r'Xhider Obfuscator', header):
            result.obfuscator = ObfuscatorType.XHIDER
            result.confidence = 0.90
            result.features.append("xhider_watermark")

        # MoonSec detection (must NOT be XHider)
        if result.obfuscator == ObfuscatorType.UNKNOWN and re.search(r'MoonSec|m[0o]on[s5]ec|MoonSecV', header, re.IGNORECASE):
            result.obfuscator = ObfuscatorType.MOONSEC
            result.confidence = 0.9
            mver = re.search(r'(?:MoonSec|m[0o]on[s5]ec)\s*(?:v|V)?(\d[\d.x]*)', header, re.IGNORECASE)
            if mver:
                result.version = mver.group(1)
                result.features.append(f"moonsec_v{result.version}")

        # IronBrew detection (must NOT be XHider)
        if result.obfuscator == ObfuscatorType.UNKNOWN and re.search(r'IronBrew|ironbrew|IRONBREW', header):
            result.obfuscator = ObfuscatorType.IRONBREW
            result.confidence = 0.9

        # LuaObfuscator detection (but NOT if XHider already detected)
        if result.obfuscator == ObfuscatorType.UNKNOWN and re.search(r'luaobfuscator', header, re.IGNORECASE):
            result.obfuscator = ObfuscatorType.LUAOBFUSCATOR
            result.confidence = 0.8

        # Feature detection (regardless of obfuscator)
        result.has_state_machine = bool(re.search(r'while\s+W\s+do\s+if\s+W\s*[<>=]', content))
        if result.has_state_machine:
            result.features.append("state_machine")

        result.has_anti_debug = bool(
            re.search(r'debug\.getinfo|debug\.gethook|debug\.sethook', content)
        )
        if result.has_anti_debug:
            result.features.append("anti_debug")

        result.has_bit32 = bool(re.search(r'bit32\.(band|bor|bxor|bnot|lshift|rshift|extract)', content))
        if result.has_bit32:
            result.features.append("bit32")

        result.has_binary_literals = bool(re.search(r'[^0-9a-zA-Z_]0[bB][01_]+', content))
        if result.has_binary_literals:
            result.features.append("binary_literals")

        # Detect encoding type
        # Base85: local X="..." with chars in 0x21..0x75 range
        # Base64: local X="..." with chars in A-Za-z0-9+/= range
        long_strings = re.findall(r'local\s+(\w+)\s*=\s*"((?:[^"\\]|\\.)*)"', content[:5000])
        for var_name, payload_raw in long_strings:
            if len(payload_raw) < 20:
                continue
            payload = lua_unescape(payload_raw)
            # Check if all chars are in base85 range
            if all(0x21 <= ord(c) <= 0x75 for c in payload):
                result.has_base85 = True
                result.encoding = "base85"
                result.features.append("base85")
                break
            # Check if it looks like base64 (alphanumeric + /+=)
            b64_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
            if all(c in b64_chars for c in payload) and len(payload) > 20:
                result.has_base64 = True
                result.encoding = "base64"
                result.features.append("base64")
                break

        if not result.has_base85 and not result.has_base64:
            # Check for hex-encoded payloads (raw hex pool in a string)
            hex_strings = re.findall(r'local\s+\w+\s*=\s*"([0-9A-Fa-f]{100,})"', content[:3000])
            if hex_strings:
                result.has_hex_pool = True
                result.encoding = "hex_pool"
                result.features.append("hex_pool")

        # Detect obfuscated math constants (715+-715, 35/5, etc.)
        if re.search(r'[\d.]+[\+\-\*/][\+\-]?\d', content[:2000]):
            result.has_obfuscated_math = True
            result.features.append("obfuscated_math")

        # Extract XOR key
        key = self._extract_xor_key(content)
        if key:
            result.xor_keys = key
            result.features.append(f"xor_key({len(key)})")

        # Detect bytecode VM
        result.has_bytecode_vm = bool(
            re.search(r'0xD3|0xA6|0xC8|0xBE|0x33|0xB2|0xCF', content[:5000])
        )
        if result.has_bytecode_vm:
            result.features.append("bytecode_vm")

        # Detect sub-mode from file path
        if filepath:
            fname = os.path.basename(filepath)
            dir_name = os.path.basename(os.path.dirname(filepath))
            if dir_name.endswith('_mode'):
                result.sub_mode = dir_name[:-5]

        # Heuristic sub-mode detection from code features
        if result.obfuscator == ObfuscatorType.XHIDER and not result.sub_mode:
            result.sub_mode = self._guess_xhider_mode(content, result)

        return result

    def _extract_xor_key(self, content: str) -> Optional[List[int]]:
        """Extract the XOR key table from the code."""
        # Pattern: local R={0xAB,0xCD;0xEF,0x12}  (Lua allows ; in tables)
        patterns = [
            # {0xAA,0xBB,0xCC,0xDD} or with semicolons
            re.compile(r'\{((?:0x[0-9A-Fa-f]+[;,]\s*){1,15}0x[0-9A-Fa-f]+)\}'),
        ]
        # Search in the first 5000 chars for the key
        search_range = content[:5000]
        for pat in patterns:
            for m in pat.finditer(search_range):
                key_str = m.group(1)
                vals = []
                for part in re.split(r'[;,]\s*', key_str):
                    part = part.strip()
                    if not part:
                        continue
                    try:
                        v = int(part, 16)
                        vals.append(v)
                    except ValueError:
                        continue
                # A valid XOR key is typically 2-16 bytes, all in 0-255
                if 2 <= len(vals) <= 16 and all(0 <= v < 256 for v in vals):
                    return vals
        return None

    def _guess_xhider_mode(self, content: str, result: DetectionResult) -> str:
        """Guess the XHider sub-mode from code characteristics."""
        feats = set(result.features)
        size = len(content)

        # Light mode: very small files
        if size < 3000:
            return "light"

        # Weak mode: small with binary literals
        if size < 5000 and result.has_binary_literals:
            return "weak"

        # Basic mode: small, simple structure
        if size < 7000 and result.has_base85 and result.has_bytecode_vm:
            return "basic"

        # Basic_1: medium size with binary literals
        if size < 8000 and result.has_binary_literals and not result.has_bit32:
            return "basic_1"

        # ME mode: very small, simple
        if size < 3000 and not result.has_binary_literals:
            return "me"

        # Evil mode: very large with base85
        if size > 100000:
            return "evil"

        # Max security: very large with bit32
        if size > 150000 and result.has_bit32:
            return "max_security"

        # L3: large, no special features
        if 50000 < size < 80000 and not result.has_bit32:
            return "l3"

        # R1-R4: medium-large, no special features
        if 35000 < size < 50000 and not result.has_bit32:
            return "r1"

        # LZ: medium, bit32
        if 35000 < size < 50000 and result.has_bit32:
            return "lz"

        # PSU modes
        if 30000 < size < 40000 and result.has_bit32 and result.has_base85:
            return "psu"

        # Mid modes
        if 15000 < size < 50000 and not result.has_bit32 and not result.has_bytecode_vm:
            return "mid"

        # Hard mode: large, no bit32
        if 50000 < size < 70000 and not result.has_bit32:
            return "hard"

        # Normal: medium
        if 15000 < size < 20000:
            return "normal"

        # IBS: medium with specific structure
        if 10000 < size < 25000:
            return "ibs"

        return "unknown"


# =============================================================================
# Static Deobfuscator (XHider)
# =============================================================================

class XHiderStaticDeobfuscator:
    """Pure Python static deobfuscation for XHider v1.2 scripts.

    Pipeline:
    1. Extract the base85/base64 payload string (or hex pool)
    2. Decode to byte array
    3. Decrypt all strings using XOR key wheel
    4. If bytecode VM detected, parse and reconstruct Lua source
    5. Inline decoded strings back into source code

    Supports 3 encoding strategies:
    - base85: Default XHider (chars 0x21..0x75)
    - base64: Custom base64 with substitution table (abyss, l1-l4)
    - hex_pool: Raw hex string with XOR keys (unvm approach)
    """

    def __init__(self, keys: Optional[List[int]] = None):
        self.keys = keys or []
        self.string_decoder = self._decrypt_string

    def deobfuscate(self, content: str, detection: DetectionResult) -> DeobfResult:
        result = DeobfResult()
        start = time.time()

        # Strategy 1: Hex pool approach (unvm-style)
        if detection.has_hex_pool:
            hex_result = self._deobfuscate_hex_pool(content, detection)
            if hex_result.success:
                result = hex_result
                result.elapsed = time.time() - start
                return result

        # Strategy 2: Base85/Base64 payload approach
        payload = self._extract_payload(content)
        if not payload:
            result.method = "none"
            result.warnings.append("Could not extract payload string from file")
            result.elapsed = time.time() - start
            return result

        # Determine encoding and decode
        data = self._decode_payload(content, payload, detection)
        if data is None:
            result.method = "none"
            result.warnings.append("Could not decode payload")
            result.elapsed = time.time() - start
            return result

        if detection.has_base85 or self._looks_like_base85(payload):
            result.method = "base85_xor_static"
        elif detection.has_base64 or self._looks_like_base64(payload):
            result.method = "base64_xor_static"
        else:
            result.method = "static_xor"

        # Try to find XOR keys
        if not self.keys:
            self.keys = detection.xor_keys
        if not self.keys:
            self.keys = self._bruteforce_keys(data)

        if not self.keys:
            result.method = "none"
            result.warnings.append("Could not determine XOR keys")
            result.elapsed = time.time() - start
            return result

        # Decrypt all strings
        result.strings = self._decrypt_all_strings(data)

        # Build output
        header = self._build_header(content, detection, result.strings)
        strings_section = self._format_strings(result.strings)

        # Try bytecode reconstruction if detected
        vm_output = ""
        if detection.has_bytecode_vm:
            bc_data = self._find_bytecode(result.strings)
            if bc_data:
                vm_output = self._reconstruct_vm(bc_data, result.strings)

        result.output = header + strings_section + vm_output
        result.success = len(result.strings) > 0
        result.elapsed = time.time() - start
        return result

    def _extract_payload(self, content: str) -> Optional[str]:
        """Extract the longest string payload from local declarations."""
        candidates = re.findall(r'local\s+(\w+)\s*=\s*"((?:[^"\\]|\\.)*)"', content)
        if not candidates:
            return None
        # Return the longest payload
        payload_var, payload = max(candidates, key=lambda c: len(c[1]))
        if len(payload) < 20:
            return None
        return lua_unescape(payload)

    def _simplify_math(self, text: str) -> str:
        """Fold obfuscated math constants: 715+-715 → 0, 35/5 → 7, etc.
        
        Only simplifies fully-delimited constant sequences to avoid corrupting
        expressions like 'x + 1' or '(t-1) % 4 + 1'.
        """
        inner_paren = r'\(\s*([\-\+]?\s*\d+\.?\d*(?:\s*[\+\-\*\/\%\^]\s*[\-\+]?\s*\d+\.?\d*)*)\s*\)'
        safe_pre = r'[\=\(\,\[\{\;\n\r]'
        safe_post = r'[\)\,\;\n\r\]\}]'
        flat_math = r'(^|' + safe_pre + r')(\s*[\-\+]?\s*\d+\.?\d*(?:\s*[\+\-\*\/\%\^]\s*[\-\+]?\s*\d+\.?\d*)+\s*)(?=' + safe_post + r'|$)'

        def repl_paren(m):
            try:
                val = eval(re.sub(r'\s+', '', m.group(1)), {"__builtins__": {}}, {})
                if isinstance(val, (int, float)):
                    res = str(int(val)) if float(val).is_integer() else f"{val:.10f}".rstrip('0').rstrip('.')
                    return f" {res} "
            except Exception:
                pass
            return m.group(0)

        def repl_flat(m):
            prefix = m.group(1)
            expr = m.group(2).strip()
            try:
                val = eval(re.sub(r'\s+', '', expr), {"__builtins__": {}}, {})
                if isinstance(val, (int, float)):
                    res = str(int(val)) if float(val).is_integer() else f"{val:.10f}".rstrip('0').rstrip('.')
                    return f"{prefix} {res} "
            except Exception:
                pass
            return m.group(0)

        for _ in range(50):
            prev = text
            text = re.sub(inner_paren, repl_paren, text)
            text = re.sub(flat_math, repl_flat, text)
            if text == prev:
                break
        return text

    def _lua_xor_byte(self, t: int, m: int) -> int:
        """XHider XOR byte decode using integer floor division.
        
        Equivalent to Lua VM: for k=0,7 do if (t//2+m//2)*2~=t+m then res+=2^k end
        Uses integer arithmetic to avoid float precision errors.
        """
        res = 0
        for k in range(8):
            v_bit = t // 2 + m // 2
            if v_bit * 2 != t + m:
                res += 1 << k
            t = t // 2
            m = m // 2
        return res

    def _deobfuscate_hex_pool(self, content: str, detection: DetectionResult) -> DeobfResult:
        """Deobfuscate using hex pool + XOR keys (unvm approach).
        
        This handles XHider scripts that embed a raw hex string and use
        direct XOR with a 4-byte key wheel, rather than base85 encoding.
        """
        result = DeobfResult()
        result.method = "hex_pool_xor_static"

        # Simplify obfuscated math first
        if detection.has_obfuscated_math:
            content = self._simplify_math(content)

        # Extract hex pool
        hex_m = re.search(r'["\']([0-9a-fA-F]{200,})["\']', content)
        if not hex_m:
            result.warnings.append("Hex pool not found")
            return result
        hex_pool = list(bytes.fromhex(hex_m.group(1)))

        # Extract XOR keys (decimal, not hex)
        q_m = re.search(r'\{\s*(\d+)\s*[,;]\s*(\d+)\s*[,;]\s*(\d+)\s*[,;]\s*(\d+)', content)
        if not q_m:
            q_m = re.search(r'(\d+)\s*[,;]\s*(\d+)\s*[,;]\s*(\d+)\s*[,;]\s*(\d+)', content)
        if not q_m:
            result.warnings.append("XOR keys not found")
            return result
        keys = [int(q_m.group(i)) for i in range(1, 5)]

        # Also extract hex-style keys as fallback
        if not detection.xor_keys:
            detection.xor_keys = keys

        # Detect VM function name
        func_name = self._detect_vm_function(content)
        if not func_name:
            result.warnings.append("VM function not found")
            return result

        # Decode all strings
        func_pattern = re.escape(func_name)
        calls = sorted(set(
            int(c) for c in re.findall(r'\b' + func_pattern + r'\((\d+)\)', content)
        ))

        decoded = {}
        for offset in calls:
            idx = offset + 1  # 1-based
            try:
                b = [hex_pool[idx - 1], hex_pool[idx], hex_pool[idx + 1], hex_pool[idx + 2]]
                length = (self._lua_xor_byte(b[0], keys[0])
                          + self._lua_xor_byte(b[1], keys[1]) * 256
                          + self._lua_xor_byte(b[2], keys[2]) * 65536
                          + self._lua_xor_byte(b[3], keys[3]) * 16777216)
                if length <= 0 or length > 500000 or idx + 4 + length > len(hex_pool):
                    continue
                s = "".join(
                    chr(self._lua_xor_byte(hex_pool[idx + 4 + i - 1], keys[i % 4]))
                    for i in range(length)
                )
                decoded[offset] = s.encode('utf-8', errors='replace')
            except (IndexError, ValueError):
                continue

        result.strings = decoded
        if not decoded:
            result.warnings.append("No strings decoded from hex pool")
            return result

        # Build output: header + strings + inlined code
        lines = [
            "-- XHider Deobfuscator v" + VERSION,
            f"-- Method: hex_pool_xor_static (unvm)",
            "",
        ]
        if detection.sub_mode:
            lines.append(f"-- Detected mode: {detection.sub_mode}")
        if detection.version:
            lines.append(f"-- XHider version: {detection.version}")
        lines.append(f"-- XOR keys: {keys}")
        lines.append(f"-- VM function: {func_name}")
        lines.append(f"-- Decoded {len(decoded)} strings from hex pool ({len(hex_pool)} bytes)")
        lines.append("")

        # Decoded strings dump
        lines.append("-- === Decoded Strings ===")
        lines.append("")
        printable = 0
        for offset in sorted(decoded.keys()):
            val = decoded[offset]
            try:
                txt = val.decode('utf-8')
                lines.append(f'-- S({offset}) = {repr(txt)}')
                printable += 1
            except (UnicodeDecodeError, ValueError):
                lines.append(f'-- S({offset}) = <binary {len(val)} bytes>')
        lines.append("")
        lines.append(f"-- Total: {printable} printable strings")
        lines.append("")

        # Inline decoded strings into source
        lines.append("-- === Inlined Source ===")
        lines.append("")

        def repl_call(m):
            offset = int(m.group(1))
            if offset in decoded:
                s = decoded[offset].decode('utf-8', errors='replace')
                s = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
                return f'"{s}"'
            return m.group(0)

        inlined = re.sub(r'\b' + func_pattern + r'\((\d+)\)', repl_call, content)
        lines.append(inlined)

        result.output = "\n".join(lines)
        result.success = True
        return result

    def _detect_vm_function(self, content: str) -> Optional[str]:
        """Auto-detect the VM decoder function name.
        
        Strategy 1: function X(y) ... if not cache[y] ...
        Strategy 2: most-called identifier(number) pattern
        """
        m = re.search(
            r'function\s+([a-zA-Z0-9_]+)\s*\(([a-zA-Z0-9_]+)\)'
            r'(?:(?!function).)+?'
            r'if\s+not\s+[a-zA-Z0-9_]+\[\2\]',
            content, re.DOTALL
        )
        if m:
            return m.group(1)

        counts = {}
        for match in re.finditer(r'([a-zA-Z0-9_]+)\(\d+\)', content):
            name = match.group(1)
            counts[name] = counts.get(name, 0) + 1
        if counts:
            return max(counts, key=counts.get)
        return None

    def _decode_payload(self, content: str, payload: str, detection: DetectionResult) -> Optional[List[int]]:
        """Decode the payload string to bytes using the detected encoding.
        
        Handles:
        - Base85 (XHider default): chars 0x21..0x75, 'z' = 4 zeros
        - Base64 with custom alphabet (XHider abyss, l1-l4, etc.)
        - Standard base64
        """
        import base64

        # Try base85 first (default XHider)
        if self._looks_like_base85(payload):
            try:
                return decode_base85(payload)
            except Exception:
                pass

        # Try to detect and handle custom base64 with substitution table
        # XHider modes like abyss embed a substitution lookup table:
        #   for l=1,32 do s[sub(e,l,l)]=l end
        # This maps each base64 char to its index
        custom_b64_table = self._extract_custom_b64_table(content, payload)
        if custom_b64_table:
            try:
                return self._custom_b64_decode(payload, custom_b64_table)
            except Exception:
                pass

        # Try standard base64
        if self._looks_like_base64(payload):
            try:
                pad = len(payload) % 4
                if pad:
                    payload_padded = payload + '=' * (4 - pad)
                else:
                    payload_padded = payload
                decoded = base64.b64decode(payload_padded)
                return list(decoded)
            except Exception:
                pass

        # Try base85 on entire payload even if some chars out of range
        # (some modes have slight variations)
        try:
            cleaned = ''.join(c for c in payload if 0x21 <= ord(c) <= 0x75 or c == 'z')
            if len(cleaned) > len(payload) * 0.8:
                return decode_base85(cleaned)
        except Exception:
            pass

        return None

    def _extract_custom_b64_table(self, content: str, payload: str) -> Optional[str]:
        """Extract the custom base64 alphabet from the obfuscated code.
        
        XHider abyss-like modes embed a substitution table:
          local function K(f)
            local s = {}
            for l = 1, 32 do s[sub(e, l, l)] = l end
            ...
        Where 'e' is the base64 alphabet string.
        """
        # Find the payload variable name
        payload_match = re.search(r'local\s+(\w+)\s*=\s*"([^"]{20,})"', content[:2000])
        if not payload_match:
            return None
        payload_var = payload_match.group(1)

        # Find the substitution table construction
        # Pattern: for l=1,32 do s[sub(e,l,l)]=l end
        # or: for l=1,32 do s[a(e,l,l)]=l end  (a = string.sub alias)
        table_pattern = re.search(
            r'for\s+\w+\s*=\s*\d+\s*,\s*(?:\d[\d.*/+-]*|32)\s*,\s*\d[\d.*/+-]*\s*do\s*'
            r's\[[a-z]\(' + re.escape(payload_var) + r'\s*,\s*\w+\s*,\s*\w+\)\]\s*=\s*\w+\s*end',
            content[:3000]
        )
        if not table_pattern:
            return None

        # Extract the base64 alphabet from the payload string itself
        # The alphabet is typically the first 32+ chars of the payload
        # but in these modes, the payload IS the base64 encoded data
        # We need to find the substitution table that maps char -> index

        # Alternative: find all single-char table lookups in the decode function
        sub_func = re.search(r'local\s+(\w+)\s*=\s*string\.sub', content[:2000])
        if not sub_func:
            sub_func = re.search(r'local\s+(\w+)\s*=\s*\w+\.sub', content[:2000])
        
        # For now, use the standard base64 alphabet as a fallback
        return None

    def _custom_b64_decode(self, payload: str, table: str) -> List[int]:
        """Decode using a custom base64 alphabet."""
        import base64
        # Not implemented yet - will fall back to standard
        raise NotImplementedError("Custom base64 not yet supported")

    def _looks_like_base85(self, payload: str) -> bool:
        if not payload:
            return False
        sample = payload[:500]
        return all(0x21 <= ord(c) <= 0x75 for c in sample) if sample else False

    def _looks_like_base64(self, payload: str) -> bool:
        if not payload:
            return False
        sample = payload[:500]
        return bool(re.match(r'^[A-Za-z0-9+/=\s]+$', sample))

    def _bruteforce_keys(self, data: List[int]) -> Optional[List[int]]:
        """Try to brute-force the XOR key by checking string validity.
        Assumes the first decrypted string should be readable text.
        """
        if not data:
            return None
        # Try 4-byte key extraction from known patterns
        # The length field of the first string should be small (< 500)
        # Try all possible 4-byte keys
        # This is impractical for full brute-force, so we use heuristics:
        # - First string length should be small
        # - Decrypted chars should be printable ASCII

        best_key = None
        best_score = 0

        # Quick heuristic: try common key patterns
        for a in range(256):
            for b in range(256):
                length = data[0] ^ a | ((data[1] ^ b) << 8)
                if length < 2 or length > 200 or 4 + length > len(data):
                    continue
                # Check if first 4 chars are printable
                sample = bytes(data[4 + j] for j in range(min(4, length)))
                if all(32 <= c < 127 for c in sample):
                    # Check remaining key bytes
                    for c_key in range(256):
                        for d_key in range(256):
                            full_sample = bytes(
                                data[4 + j] ^ [a, b, c_key, d_key][j % 4]
                                for j in range(min(20, length))
                            )
                            score = sum(1 for c in full_sample if 32 <= c < 127 or c in (10, 13, 9))
                            if score > best_score:
                                best_score = score
                                best_key = [a, b, c_key, d_key]

        # Fallback: try known common XHider keys
        common_keys = [
            [0xF5, 0xD1, 0xC6, 0xC5],
            [0x71, 0x60, 0x6D, 0xFA],
            [0xF2, 0x3B, 0x1C, 0x1D],
            [0x55, 0x51, 0x52, 0x36],
        ]
        for key in common_keys:
            length = 0
            for i in range(min(4, len(key))):
                if i < len(data):
                    length |= (data[i] ^ key[i]) << (8 * i)
            if 2 <= length <= 200 and 4 + length <= len(data):
                sample = bytes(
                    data[4 + j] ^ key[j % len(key)]
                    for j in range(min(20, length))
                )
                score = sum(1 for c in sample if 32 <= c < 127 or c in (10, 13, 9))
                if score > best_score:
                    best_score = score
                    best_key = key

        return best_key

    def _decrypt_string(self, data: List[int], offset: int, keys: List[int]) -> Optional[bytes]:
        return decrypt_xor(data, offset, keys)

    def _decrypt_all_strings(self, data: List[int]) -> Dict[int, bytes]:
        """Decrypt all strings in the data blob."""
        strings = {}
        if not self.keys:
            return strings
        offset = 0
        max_strings = 50000  # safety limit
        attempts = 0
        while offset < len(data) and attempts < max_strings:
            dec = decrypt_xor(data, offset, self.keys)
            if dec is None:
                break
            strings[offset] = dec
            offset += 4 + len(dec)
            attempts += 1
        return strings

    def _build_header(self, content: str, detection: DetectionResult,
                       strings: Dict[int, bytes]) -> str:
        lines = [
            "-- XHider Deobfuscator v" + VERSION,
            "-- Method: " + detection.method if hasattr(detection, 'method') else "-- Method: static XOR",
            "",
        ]
        if detection.sub_mode:
            lines.append(f"-- Detected mode: {detection.sub_mode}")
        if detection.version:
            lines.append(f"-- XHider version: {detection.version}")
        if detection.xor_keys:
            lines.append(f"-- XOR key: {[hex(k) for k in detection.xor_keys]}")
        if detection.features:
            lines.append(f"-- Features: {', '.join(detection.features)}")
        lines.append(f"-- Decoded {len(strings)} strings")
        lines.append("")
        return "\n".join(lines)

    def _format_strings(self, strings: Dict[int, bytes]) -> str:
        lines = ["-- === Decoded Strings ===", ""]
        printable_count = 0
        binary_count = 0
        for offset in sorted(strings.keys()):
            val = strings[offset]
            try:
                txt = val.decode('utf-8')
                lines.append(f'-- S(0x{offset:04X}) = {repr(txt)}')
                printable_count += 1
            except (UnicodeDecodeError, ValueError):
                lines.append(f'-- S(0x{offset:04X}) = <binary {len(val)} bytes>')
                binary_count += 1
        lines.append("")
        lines.append(f"-- Total: {printable_count} strings, {binary_count} binary blobs")
        lines.append("")
        return "\n".join(lines)

    def _find_bytecode(self, strings: Dict[int, bytes]) -> Optional[bytes]:
        """Find the longest binary blob (likely bytecode VM)."""
        best = None
        best_len = 0
        for val in strings.values():
            try:
                val.decode('utf-8')
            except (UnicodeDecodeError, ValueError):
                if len(val) > best_len:
                    best = val
                    best_len = len(val)
        return best

    def _reconstruct_vm(self, bc: bytes, strings: Dict[int, bytes]) -> str:
        """Try to reconstruct Lua source from bytecode VM.
        
        VM structure (1-based indexing, as in Lua VM):
          Header: 3 bytes (n_G)
          G table: n_G * 3 bytes
          n_p: 3 bytes
          p offsets: n_p * 4 bytes  
          Padding: 6 bytes (includes 3-byte l_instr + 3 unknown)
          Code: l_instr * 4 bytes
          Constant pool follows
        """
        lines = ["-- === Bytecode VM Reconstruction ===", ""]
        try:
            Q = list(bc)
            if len(Q) < 20:
                lines.append("-- Bytecode too small for reconstruction")
                return "\n".join(lines)

            def M(j, p):
                if j + p > len(Q) + 1:
                    return 0
                v = 0
                for k in range(p):
                    if j + k - 1 < len(Q):
                        v |= Q[j + k - 1] << (8 * k)
                return v

            # Parse VM header
            N = 4
            n_G = M(1, 3)
            N += n_G * 3
            n_p = M(N, 3)
            N += n_p * 4 + 6  # skip offsets + padding
            l_instr = M(N - 3, 3)
            n_const_start = N + l_instr * 4

            lines.append(f"-- VM Info: {n_G} G entries, {n_p} constants, {l_instr} instructions")
            lines.append("")

            consts = {}
            # Parse p offset array (1-indexed)
            p_arr = [0] * (n_p + 1)
            for idx in range(1, n_p + 1):
                base_off = 4 + n_G * 3 + 3 + (idx - 1) * 4
                p_arr[idx] = M(base_off + 1, 4)

            for idx in range(1, n_p + 1):
                l_ptr = p_arr[idx] + n_const_start
                if l_ptr < 1 or l_ptr > len(Q):
                    continue
                t = Q[l_ptr - 1]
                if t == 0:  # string
                    if l_ptr + 4 < len(Q):
                        slen = M(l_ptr + 1, 4)
                        if slen > 0 and l_ptr + 4 + slen <= len(Q):
                            sval = bytes(Q[l_ptr + 4: l_ptr + 4 + slen])
                            try:
                                consts[idx] = ('string', sval.decode('utf-8'))
                            except:
                                consts[idx] = ('string', sval.decode('latin-1'))
                elif t == 1:  # positive int
                    if l_ptr + 4 < len(Q):
                        consts[idx] = ('int', M(l_ptr + 1, 4))
                elif t == 2:  # negative int
                    if l_ptr + 4 < len(Q):
                        consts[idx] = ('int', -M(l_ptr + 1, 4))

            if consts:
                lines.append("-- VM Constants:")
                for i, c in sorted(consts.items()):
                    kind, val = c
                    if kind == 'string':
                        safe = val[:200]
                        lines.append(f'--   c[{i}] = {repr(safe)}')
                    else:
                        lines.append(f'--   c[{i}] = {val}')
                lines.append("")

            # Parse instructions
            code = []
            for i in range(l_instr):
                ip = N + i * 4
                if ip + 3 >= len(Q):
                    break
                code.append((Q[ip - 1], Q[ip], Q[ip + 1], Q[ip + 2]))

            if code:
                # Known opcodes
                op_names = {
                    0xD3: "LOADK", 0xA6: "GETGLOBAL", 0xC8: "ENTER_FRAME",
                    0x86: "SNAPSHOT", 0x33: "MOVE_RETURN", 0xBE: "CALL",
                    0xC2: "CLEAR_FRAME", 0xB2: "RETURN", 0xCF: "NOP",
                }
                lines.append(f"-- VM Instructions ({len(code)} total, showing first 50):")
                for i, (op, a1, a2, a3) in enumerate(code[:50]):
                    name = op_names.get(op, f"OP_0x{op:02X}")
                    operand = a1 | (a2 << 8) | (a3 << 16)
                    lines.append(f'--   [{i:4d}] {name} 0x{operand:04X}  ({a1:3d} {a2:3d} {a3:3d})')
                if len(code) > 50:
                    lines.append(f'--   ... and {len(code) - 50} more')
                lines.append("")

        except Exception as e:
            lines.append(f"-- VM parse error: {e}")
            import traceback
            lines.append(f"-- {traceback.format_exc()}")

        lines.append("-- Note: Full VM reconstruction requires dynamic execution (Lua).")
        lines.append("")
        return "\n".join(lines)


# =============================================================================
# Dynamic Deobfuscator (Lua)
# =============================================================================

class DynamicDeobfuscator:
    """Deobfuscate by running the script through Lua with hook_universal.lua."""

    def __init__(self):
        self.lua_bins = find_lua_binaries()
        self.hook_script = HOOK_SCRIPT

    def is_available(self) -> bool:
        return len(self.lua_bins) > 0 and os.path.exists(self.hook_script)

    def deobfuscate(self, filepath: str, detection: DetectionResult,
                    timeout: int = 30) -> DeobfResult:
        result = DeobfResult()
        start = time.time()

        if not self.is_available():
            result.warnings.append("No Lua binary found. Dynamic deobfuscation unavailable.")
            result.elapsed = time.time() - start
            return result

        lua_bin = self.lua_bins[0]
        env = {**os.environ}
        env["XHIDER_DUMP_CHUNKS"] = "1"
        if detection.has_binary_literals:
            env["XHIDER_NO_PREPROCESS"] = "0"  # enable preprocess for binary lit
        if detection.has_bit32:
            env["XHIDER_NO_BIT32"] = "0"

        try:
            proc = subprocess.run(
                [lua_bin, self.hook_script, filepath],
                capture_output=True, text=True, timeout=timeout, env=env,
            )
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired:
            result.warnings.append(f"Execution timed out after {timeout}s")
            result.method = "dynamic_timeout"
            result.elapsed = time.time() - start
            return result
        except Exception as e:
            result.warnings.append(f"Execution failed: {e}")
            result.elapsed = time.time() - start
            return result

        # Parse captured output
        captured = self._parse_captured(stdout)
        chunks = self._extract_chunks(filepath)

        result.method = "dynamic_lua"
        result.success = len(captured) > 0 or len(chunks) > 0

        # Build output
        lines = [
            "-- XHider Deobfuscator v" + VERSION,
            f"-- Method: dynamic execution via {os.path.basename(lua_bin)}",
            "",
        ]
        if detection.sub_mode:
            lines.append(f"-- Detected mode: {detection.sub_mode}")
        if detection.version:
            lines.append(f"-- XHider version: {detection.version}")

        if captured:
            lines.append(f"-- Captured {len(captured)} output lines")
            lines.append("")
            lines.append("-- === Captured Output ===")
            lines.append("")
            for i, line in enumerate(captured, 1):
                safe = line[:500]
                lines.append(f'-- [{i}] {repr(safe)}')
            lines.append("")

        if chunks:
            lines.append(f"-- Captured {len(chunks)} loadstring chunks")
            lines.append("")
            for i, (src, source_type) in enumerate(chunks, 1):
                lines.append(f"-- === Chunk {i} ({source_type}, {len(src)} bytes) ===")
                lines.append("")
                # Try to decode as text
                try:
                    chunk_text = src.decode('utf-8', errors='replace')
                    lines.append(chunk_text)
                except:
                    lines.append(f"-- (binary data, {len(src)} bytes)")
                lines.append("")

        result.output = "\n".join(lines)
        result.elapsed = time.time() - start
        return result

    def _parse_captured(self, stdout: str) -> List[str]:
        captured = []
        in_capture = False
        for line in stdout.split('\n'):
            if '=== Captured Output' in line:
                in_capture = True
                continue
            if '=== End ===' in line:
                in_capture = False
                continue
            if in_capture:
                m = re.match(r'\[\d+\]\s*(.*)', line)
                if m:
                    captured.append(m.group(1))
        return captured

    def _extract_chunks(self, filepath: str) -> List[Tuple[bytes, str]]:
        chunks = []
        base = os.path.splitext(filepath)[0]
        i = 1
        while True:
            chunk_path = f"{base}.chunk_{i}.lua"
            if not os.path.exists(chunk_path):
                break
            try:
                with open(chunk_path, 'rb') as f:
                    data = f.read()
                chunks.append((data, os.path.basename(chunk_path)))
                os.remove(chunk_path)  # clean up
            except:
                break
            i += 1
        return chunks


# =============================================================================
# Bruteforce Deobfuscator
# =============================================================================

class BruteforceDeobfuscator:
    """Try all known XHider sub-mode configurations on a script."""

    def __init__(self):
        self.detector = ObfuscatorDetector()
        self.static = XHiderStaticDeobfuscator()
        self.dynamic = DynamicDeobfuscator()

    def deobfuscate(self, filepath: str, output_dir: str = "",
                    timeout: int = 15) -> List[Tuple[str, DeobfResult]]:
        """Try all modes and return list of (mode_name, result) tuples."""
        results = []
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        for mode_name in XHIDER_MODES:
            # Create detection with forced mode
            detection = self.detector.detect(content, filepath)
            detection.sub_mode = mode_name

            # Try static first
            static_result = self.static.deobfuscate(content, detection)
            if static_result.success and len(static_result.strings) > 10:
                results.append((mode_name, static_result))
                continue

            # Try dynamic
            if self.dynamic.is_available():
                dyn_result = self.dynamic.deobfuscate(filepath, detection, timeout)
                if dyn_result.success:
                    results.append((mode_name, dyn_result))
                    continue

            # Record failure
            fail_result = DeobfResult(success=False, method="failed",
                                     warnings=[f"No method succeeded for {mode_name}"])
            results.append((mode_name, fail_result))

        return results


# =============================================================================
# Main Orchestrator
# =============================================================================

class Deobfuscator:
    """Main deobfuscation orchestrator."""

    def __init__(self):
        self.detector = ObfuscatorDetector()
        self.static = XHiderStaticDeobfuscator()
        self.dynamic = DynamicDeobfuscator()
        self.bruteforce = BruteforceDeobfuscator()

    def auto(self, input_file: str, output_file: str = "") -> DeobfResult:
        """Auto-detect obfuscator and deobfuscate."""
        print(f"[*] Auto-detecting obfuscator for: {input_file}")

        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        detection = self.detector.detect(content, input_file)
        self._print_detection(detection)

        result = DeobfResult()

        # Strategy: try static first, then dynamic
        if detection.obfuscator == ObfuscatorType.XHIDER:
            # Static deobfuscation
            static_result = self.static.deobfuscate(content, detection)
            if static_result.success:
                result = static_result
                print(f"[+] Static deobfuscation succeeded: {len(result.strings)} strings")
            else:
                print(f"[-] Static deobfuscation failed: {'; '.join(static_result.warnings)}")

            # Try dynamic as well if static didn't get great results
            if self.dynamic.is_available():
                print(f"[*] Trying dynamic execution...")
                dyn_result = self.dynamic.deobfuscate(input_file, detection)
                if dyn_result.success:
                    # Merge results
                    if result.success and dyn_result.output:
                        result.output += "\n\n" + dyn_result.output
                        result.method += " + dynamic"
                    else:
                        result = dyn_result
                    print(f"[+] Dynamic deobfuscation succeeded")

        elif detection.obfuscator == ObfuscatorType.UNKNOWN:
            # Try both
            print(f"[?] Unknown obfuscator, trying both static and dynamic...")

            static_result = self.static.deobfuscate(content, detection)
            if static_result.success:
                result = static_result
                print(f"[+] Static deobfuscation succeeded: {len(result.strings)} strings")

            if self.dynamic.is_available():
                dyn_result = self.dynamic.deobfuscate(input_file, detection)
                if dyn_result.success:
                    if result.success and dyn_result.output:
                        result.output += "\n\n" + dyn_result.output
                        result.method += " + dynamic"
                    elif dyn_result.success:
                        result = dyn_result
                    print(f"[+] Dynamic deobfuscation succeeded")
        else:
            result.warnings.append(f"Obfuscator {detection.obfuscator.value} not fully supported yet")
            # Try dynamic anyway
            if self.dynamic.is_available():
                dyn_result = self.dynamic.deobfuscate(input_file, detection)
                if dyn_result.success:
                    result = dyn_result

        # Write output
        if result.output:
            out_path = output_file or self._default_output(input_file)
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(result.output)
            print(f"[+] Output saved to: {out_path}")
        else:
            print(f"[-] No output generated")

        return result

    def bruteforce(self, input_file: str, output_dir: str = "") -> List[Tuple[str, DeobfResult]]:
        """Try all modes."""
        print(f"[*] Bruteforcing all modes for: {input_file}")
        out_dir = output_dir or os.path.splitext(input_file)[0] + "_bruteforce"
        os.makedirs(out_dir, exist_ok=True)

        results = self.bruteforce.deobfuscate(input_file, out_dir)

        successful = []
        for mode_name, res in results:
            status = "OK" if res.success else "FAIL"
            print(f"  [{status}] {mode_name}: {res.method} "
                  f"({'strings=' + str(len(res.strings)) if res.strings else 'no output'})")
            if res.success and res.output:
                out_path = os.path.join(out_dir, f"{mode_name}.decrypted.lua")
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(res.output)
                successful.append((mode_name, res))

        print(f"\n[*] Bruteforce complete: {len(successful)}/{len(results)} modes succeeded")
        print(f"[*] Results saved to: {out_dir}")
        return results

    def custom(self, input_file: str, mode: str, output_file: str = "") -> DeobfResult:
        """Deobfuscate with a specific mode."""
        print(f"[*] Deobfuscating with mode '{mode}': {input_file}")

        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        detection = self.detector.detect(content, input_file)
        detection.sub_mode = mode
        self._print_detection(detection)

        result = DeobfResult()

        # Static
        static_result = self.static.deobfuscate(content, detection)
        if static_result.success:
            result = static_result
            print(f"[+] Static deobfuscation succeeded: {len(result.strings)} strings")

        # Dynamic
        if self.dynamic.is_available():
            dyn_result = self.dynamic.deobfuscate(input_file, detection)
            if dyn_result.success:
                if result.success and dyn_result.output:
                    result.output += "\n\n" + dyn_result.output
                    result.method += " + dynamic"
                elif dyn_result.success:
                    result = dyn_result
                print(f"[+] Dynamic deobfuscation succeeded")

        if result.output:
            out_path = output_file or self._default_output(input_file)
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(result.output)
            print(f"[+] Output saved to: {out_path}")
        else:
            print(f"[-] No output generated")

        return result

    def _default_output(self, input_file: str) -> str:
        base = os.path.splitext(input_file)[0]
        return base + ".decrypted.lua"

    def _print_detection(self, detection: DetectionResult):
        print(f"  Obfuscator: {detection.obfuscator.value}")
        if detection.version:
            print(f"  Version:    {detection.version}")
        if detection.sub_mode:
            print(f"  Sub-mode:   {detection.sub_mode}")
        if detection.features:
            print(f"  Features:   {', '.join(detection.features)}")
        if detection.xor_keys:
            print(f"  XOR key:    {[hex(k) for k in detection.xor_keys]}")
        if detection.encoding:
            print(f"  Encoding:   {detection.encoding}")
        print(f"  Confidence: {detection.confidence:.0%}")
        lua_available = self.dynamic.is_available()
        print(f"  Lua:        {'available' if lua_available else 'not found'}")


# =============================================================================
# CLI Entry Point
# =============================================================================

def cmd_auto(args):
    deobf = Deobfuscator()
    input_files = args.input
    if not isinstance(input_files, list):
        input_files = [input_files]

    for f in input_files:
        if not os.path.isfile(f):
            print(f"[-] File not found: {f}")
            continue
        out = args.output if args.output and len(input_files) == 1 else ""
        deobf.auto(f, out)


def cmd_bruteforce(args):
    deobf = Deobfuscator()
    if not args.input:
        print("[-] Error: -i/--input is required for bruteforce mode")
        sys.exit(1)
    deobf.bruteforce(args.input, args.output)


def cmd_custom(args):
    deobf = Deobfuscator()
    if not args.input:
        print("[-] Error: -i/--input is required")
        sys.exit(1)
    if not args.mode:
        print("[-] Error: --mode is required for custom mode")
        sys.exit(1)
    deobf.custom(args.input, args.mode, args.output)


def cmd_batch(args):
    """Process all mode folders in the repo."""
    deobf = Deobfuscator()
    repo_dir = args.repo_dir or SCRIPT_DIR

    mode_dirs = []
    for entry in sorted(os.listdir(repo_dir)):
        full = os.path.join(repo_dir, entry)
        if os.path.isdir(full) and entry.endswith('_mode'):
            mode_dirs.append((entry, full))

    total_ok = total_fail = total_skip = 0

    for mode_name, mode_dir in mode_dirs:
        lua_files = []
        for f in sorted(os.listdir(mode_dir)):
            fp = os.path.join(mode_dir, f)
            if not os.path.isfile(fp) or not f.endswith('.lua'):
                continue
            # Skip non-obfuscated files
            if any(x in f for x in ['.decrypted', '.beautified', '.simplified',
                                     '.chunk_', '_fixed', '_debug', '_v2',
                                     '.formatted', '.bytecode', '.bin']):
                continue
            # Skip files without XHider header
            try:
                with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                    head = fh.read(500)
                if 'XHider' not in head and 'Xhider' not in head:
                    total_skip += 1
                    continue
            except:
                continue

            # Skip if already deobfuscated
            dec = fp.rsplit('.', 1)[0] + '.decrypted.lua'
            if os.path.exists(dec) and not args.force:
                total_skip += 1
                continue

            lua_files.append(f)

        if not lua_files:
            continue

        print(f"\n{'=' * 60}")
        print(f"{mode_name} ({len(lua_files)} files)")
        print(f"{'=' * 60}")

        for lua_file in lua_files:
            fp = os.path.join(mode_dir, lua_file)
            result = deobf.auto(fp)
            if result.success:
                total_ok += 1
            else:
                total_fail += 1

    print(f"\n{'=' * 60}")
    print(f"TOTAL: {total_ok} ok, {total_fail} fail, {total_skip} skip")
    print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(
        prog="XHider Deobfuscator",
        description=f"Deobfuscate Lua scripts protected by XHider and other obfuscators. v{VERSION}",
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")
    subparsers = parser.add_subparsers(dest="command", help="Deobfuscation mode")

    # auto mode
    p_auto = subparsers.add_parser("auto", help="Auto-detect obfuscator and deobfuscate")
    p_auto.add_argument("-i", "--input", nargs="+", required=True, help="Input file(s)")
    p_auto.add_argument("-o", "--output", help="Output file (default: <input>.decrypted.lua)")

    # bruteforce mode
    p_brute = subparsers.add_parser("bruteforce", help="Try all known XHider sub-modes")
    p_brute.add_argument("-i", "--input", required=True, help="Input file")
    p_brute.add_argument("-o", "--output", help="Output directory (default: <input>_bruteforce/)")

    # custom mode
    p_custom = subparsers.add_parser("custom", help="Use a specific obfuscator mode")
    p_custom.add_argument("-i", "--input", required=True, help="Input file")
    p_custom.add_argument("-o", "--output", help="Output file")
    p_custom.add_argument("-m", "--mode", required=True,
                           help=f"Mode to use: {', '.join(ALL_MODES[:10])}...")

    # batch mode
    p_batch = subparsers.add_parser("batch", help="Process all mode folders in the repo")
    p_batch.add_argument("-d", "--repo-dir", help="Repository root directory")
    p_batch.add_argument("-f", "--force", action="store_true",
                         help="Re-deobfuscate even if .decrypted.lua exists")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "auto":
        cmd_auto(args)
    elif args.command == "bruteforce":
        cmd_bruteforce(args)
    elif args.command == "custom":
        cmd_custom(args)
    elif args.command == "batch":
        cmd_batch(args)


if __name__ == "__main__":
    main()
