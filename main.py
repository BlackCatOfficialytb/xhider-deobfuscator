#!/usr/bin/env python3
"""Thin shim: forwards to xhider_detector."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "xhider_detector"))

from detect_xhider import main as _main


def main():
    argv = list(sys.argv[1:])
    if argv and argv[0] == "-":
        import json
        from detect_xhider import detect_text
        res = detect_text(sys.stdin.read(), filename="<stdin>")
        print(json.dumps(res.to_dict(5), ensure_ascii=False, indent=2))
        return
    _main()


if __name__ == "__main__":
    main()
