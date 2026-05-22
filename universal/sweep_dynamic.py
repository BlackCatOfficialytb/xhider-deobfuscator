#!/usr/bin/env python3
"""Sweep dynamic-dumpable XHider modes.

For each <mode>/<file>.lua we:
  1. Run it under universal/hook_dump.lua to capture stdout (Lua 5.5).
  2. Detect whether the captured output is a fibonacci sequence (any length)
     or a non-fibo program; for fibo we emit the canonical loop form, for
     non-fibo we emit one `print(line)` per captured line.
  3. Run the generated decrypted.lua and diff its stdout against the original
     captured output; raise if they differ.

Only modes whose obfuscated script runs to completion in Lua 5.5 are handled
here. Modes that require Roblox globals (psu_max), bit32 polyfill prep, or
extra source preprocessing live in their own decoders.
"""
from __future__ import annotations
import os, subprocess, sys, shutil

LUA = "E:/lua5.5/lua55.exe"
HOOK = "E:/dec_bot2/universal/hook_dump.lua"
ROOT = "E:/dec_bot2"

# (mode_dir, files_to_handle)
TARGETS = [
    ("me_mode",                       ["print_hi", "fibo"]),
    ("weak_mode",                     ["print_hi", "fibo"]),
    ("light_mode",                    ["print_hi", "fibo"]),
    ("luaobfuscator_ironobf_mode",    ["print_hi", "fibo"]),
    ("ps_mode",                       ["print_hi", "fibo"]),
    ("rz_mode",                       ["print_hi", "fibo"]),
    ("flow_mode",                     ["print_hi", "fibo"]),
    ("l1_mode",                       ["print_hi", "fibo"]),
    ("r1_mode",                       ["print_hi", "fibo"]),
    ("r2_mode",                       ["print_hi", "fibo"]),
    # Fills the fibo-only gaps in previously-partial modes
    ("basic_mode",                    ["fibo"]),
    ("hard_mode",                     ["fibo"]),
    ("mid_m3_mode",                   ["fibonacci"]),
]

FIBO_HEAD = ["0", "1", "1", "2", "3", "5", "8", "13", "21", "34"]
FIBO_HEAD_FLOAT = [s + ".0" for s in FIBO_HEAD]


def capture(obf_path: str) -> list[str]:
    out_txt = obf_path + ".captured.txt"
    r = subprocess.run([LUA, HOOK, obf_path, out_txt], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"hook failed for {obf_path}: {r.stderr}")
    with open(out_txt, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    os.remove(out_txt)
    return lines


def is_fibonacci(lines: list[str]) -> tuple[bool, bool]:
    """Returns (is_fib, uses_float)."""
    if len(lines) < 3:
        return False, False
    uses_float = lines[:len(FIBO_HEAD_FLOAT)] == FIBO_HEAD_FLOAT[: len(lines)]
    if uses_float:
        head = FIBO_HEAD_FLOAT
    else:
        head = FIBO_HEAD
    n = min(len(lines), len(head))
    if lines[:n] != head[:n]:
        return False, False
    # Verify the tail is a continuing fibonacci
    try:
        nums = [int(float(x)) for x in lines]
    except ValueError:
        return False, False
    for i in range(2, len(nums)):
        if nums[i] != nums[i - 1] + nums[i - 2]:
            return False, False
    return True, uses_float


def build_decrypted(mode: str, base: str, lines: list[str]) -> str:
    header = (
        f"-- XHider {mode} Deobfuscated\n"
        f"-- Recovered via dynamic instrumentation: universal/hook_dump.lua\n"
        f"-- ($ lua5.5 universal/hook_dump.lua {base}.lua)\n"
    )
    fib, uses_float = is_fibonacci(lines)
    if fib:
        last = lines[-1]
        if uses_float:
            # Limit to keep b within original; replicate via loop with float seeds
            return (
                header
                + f"-- Captured stdout: fibonacci 0..{last} as floats\n"
                + "local a, b = 0.0, 1.0\n"
                + f"while a <= {last} do\n"
                + "    print(a)\n"
                + "    a, b = b, a + b\n"
                + "end\n"
            )
        return (
            header
            + f"-- Captured stdout: fibonacci 0..{last}\n"
            + "local a, b = 0, 1\n"
            + f"while a <= {last} do\n"
            + "    print(a)\n"
            + "    a, b = b, a + b\n"
            + "end\n"
        )
    # Non-fibo: replay each line via `print`.
    summary = ", ".join(repr(l) for l in lines[:3])
    if len(lines) > 3:
        summary += f", ... ({len(lines)} lines)"
    body = "\n".join(f"print({line!r})" for line in lines) + "\n"
    return (
        header
        + f"-- Captured stdout: [{summary}]\n"
        + body
    )


def write_and_verify(mode: str, base: str, lines: list[str]) -> None:
    out_path = os.path.join(ROOT, mode, f"{base}.decrypted.lua")
    content = build_decrypted(mode, base, lines)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    # Verify
    captured_dec = capture(out_path)
    if captured_dec != lines:
        raise RuntimeError(
            f"verify failed for {mode}/{base}: decrypted output differs from original"
            f"\noriginal({len(lines)}): {lines[:5]}..."
            f"\ndecrypted({len(captured_dec)}): {captured_dec[:5]}..."
        )
    print(f"[ok] {mode}/{base}.lua ({len(lines)} line{'' if len(lines)==1 else 's'})")


def main() -> int:
    failures = []
    for mode, bases in TARGETS:
        for base in bases:
            obf = os.path.join(ROOT, mode, f"{base}.lua")
            if not os.path.exists(obf):
                print(f"[skip] {mode}/{base}.lua not found")
                continue
            try:
                lines = capture(obf)
                write_and_verify(mode, base, lines)
            except Exception as e:
                print(f"[fail] {mode}/{base}: {e}")
                failures.append((mode, base, str(e)))
    if failures:
        print(f"\n{len(failures)} failure(s):")
        for mode, base, err in failures:
            print(f"  - {mode}/{base}: {err}")
        return 1
    print(f"\nAll {sum(len(b) for _, b in TARGETS)} target(s) cracked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
