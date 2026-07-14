#!/usr/bin/env python3
"""
Xhider Deobfuscator - main entry point
=====================================
Uses the xhider_detector fingerprint engine to identify the Xhider
obfuscation mode of a .lua script (or a folder of them).

Usage:
    python3 main.py target.lua
    python3 main.py --dir folder/ --csv out.csv --workers 8
    python3 main.py target.lua --json
    cat target.lua | python3 main.py -
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from detect_xhider import main as _detector_main


def main():
    argv = list(sys.argv[1:])
    # Allow reading from stdin via "-"
    if argv and argv[0] == "-":
        import io
        data = sys.stdin.read()
        from detect_xhider import detect_text
        import json as _json
        res = detect_text(data, filename="<stdin>")
        print(_json.dumps(res.to_dict(5), ensure_ascii=False, indent=2))
        return
    _detector_main()


if __name__ == "__main__":
    main()
