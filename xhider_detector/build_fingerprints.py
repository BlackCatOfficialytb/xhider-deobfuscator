"""
Build fingerprint DB tu thu muc chua sample (xhider-<Mode>.lua).
Fingerprint duoc luu theo TUNG VERSION cua Xhider (doc tu header file),
vi 1 mode ten giong nhau o cac version khac nhau co the co harness code
khac nhau hoan toan.

Cach dung:
    python3 build_fingerprints.py /path/to/sample_dir [--out fingerprints]

Neu khong truyen sample_dir, mac dinh dung thu muc sample dinh kem
trong repo (neu co).
"""
import argparse
import glob
import json
import os

from features import extract_features
from token_features import extract_token_features
from constpool_features import extract_constpool_features
from version_detect import detect_xhider_version

DEFAULT_OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fingerprints")


def build(sample_dir: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)

    entries = []  # (mode, base, text, version_or_None)
    for path in sorted(glob.glob(os.path.join(sample_dir, "*.lua"))):
        base = os.path.basename(path)
        if not base.lower().startswith("xhider-"):
            continue
        mode = os.path.splitext(base[len("xhider-"):])[0]
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        entries.append((mode, base, text, detect_xhider_version(text)))

    # Ca thu muc sample thuong la 1 "lo" cua CUNG 1 version Xhider (nguoi
    # dung thuong tai toan bo full-mode zip cua 1 ban Xhider ve). Vai mode
    # co the KHONG co header hien thi ('--// This file was created by
    # XHider v...') do chinh ky thuat obfuscation cua mode do lam mat luon
    # comment dau file (vd PsuMax) -> ta gan cho no version pho bien nhat
    # tim thay trong ca lo, thay vi tach rieng thanh 1 "unknown" ao.
    detected_versions = [v for _, _, _, v in entries if v]
    batch_version = max(set(detected_versions), key=detected_versions.count) if detected_versions else "unknown"

    by_version = {}
    for mode, base, text, version in entries:
        v = version or batch_version
        regex_feats = extract_features(text)
        tok_feats = extract_token_features(text)
        cp_feats = extract_constpool_features(text)
        by_version.setdefault(v, {})[mode] = {
            "regex": regex_feats,
            "token": tok_feats,
            "constpool": cp_feats,
        }
        tag = "" if version else "  (khong co header, gan theo batch)"
        print(f"  [{v}] {mode:<14} <- {base}{tag}")

    for version, modes in by_version.items():
        out_path = os.path.join(out_dir, f"v{version}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(modes, f, ensure_ascii=False)
        print(f"-> Wrote {len(modes)} modes to {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sample_dir", nargs="?",
                     default="/home/claude/xhider_extracted/Xhider-full-mode",
                     help="Thu muc chua file mau xhider-<Mode>.lua")
    ap.add_argument("--out", default=DEFAULT_OUT_DIR, help="Thu muc ghi fingerprint DB")
    args = ap.parse_args()
    build(args.sample_dir, args.out)


if __name__ == "__main__":
    main()
