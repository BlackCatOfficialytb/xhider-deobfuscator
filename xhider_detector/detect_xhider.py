#!/usr/bin/env python3
"""
Xhider Mode Detector (v3)
===========================
Nhan dien mode obfuscation cua file .lua da duoc bao ve boi Xhider, dua
tren fingerprint trich xuat tu sample dinh kem.

CLI:
    python3 detect_xhider.py target.lua
    python3 detect_xhider.py target.lua --top 5 --detail
    python3 detect_xhider.py target.lua --json
    python3 detect_xhider.py --dir folder/ --csv out.csv --workers 8
    python3 detect_xhider.py --dir folder/ --matrix matrix.csv

Module (embed vao bot/tool khac):
    from detect_xhider import detect_text, detect_file
    result = detect_file("target.lua")
    print(result.best_mode, result.best_score, result.is_confident)
"""
import argparse
import csv
import glob
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict

from features import extract_features, COUNT_FEATURES, RATIO_FEATURES, BOOL_FEATURES
from token_features import extract_token_features, prefix_match_len, hist_cosine_sim
from constpool_features import extract_constpool_features, CONSTPOOL_SCALAR_FEATURES
from version_detect import detect_xhider_version

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FP_DIR = os.path.join(SCRIPT_DIR, "fingerprints")

# ---- trong so cho tung nhom dac trung (regex, dem "vo harness") ----
W_COUNT = 1.0
W_PRESENCE = 1.4
W_RATIO_MAG = 0.4
W_BOOL = 1.0

# ---- trong so cho dac trung token-level ----
W_TOKEN_COUNT = 1.8
W_TOKEN_HIST = 1.6
W_TOKEN_PREFIX = 2.2

# ---- trong so cho dac trung constant-pool (entropy/thong ke du lieu) ----
W_CONSTPOOL = 1.0

CONFIDENCE_THRESHOLD = 78.0
CLOSE_MARGIN = 3.0
# neu diem top-1 thap hon nguong nay -> rat co the la preset KHONG co
# trong fingerprint DB (vd preset moi/an nhu "Hidden" tren xhider.xyz)
UNKNOWN_PRESET_THRESHOLD = 55.0

FAMILY_GROUPS = [
    {"Basic", "M1", "M2", "Light", "Normal", "Weak", "Wrd", "Veil", "Strong",
     "Medium", "Hard", "PsuMax", "R1", "R2", "R3", "R4", "Rz", "Ps",
     "Ib1", "Ib2", "Ibv", "Hex"},
    {"Abyss", "Abyss2", "Evil", "Flow", "Ib3", "L2", "M3"},
    {"Psu", "PsuMedium", "PsuHard"},
    {"L1", "L3", "L4", "Lightrew", "Lightrew2", "MaxSecurity"},
]


# ============================== ket qua ==============================

@dataclass
class ModeScore:
    mode: str
    score: float


@dataclass
class DetectionResult:
    file: str
    size: int
    xhider_version_detected: Optional[str]
    db_version_used: str
    ranked: List[ModeScore]
    warnings: List[str] = field(default_factory=list)

    @property
    def best_mode(self) -> str:
        return self.ranked[0].mode if self.ranked else "?"

    @property
    def best_score(self) -> float:
        return self.ranked[0].score if self.ranked else 0.0

    @property
    def is_confident(self) -> bool:
        if not self.ranked or self.best_score < CONFIDENCE_THRESHOLD:
            return False
        if len(self.ranked) > 1 and (self.best_score - self.ranked[1].score) < CLOSE_MARGIN:
            return False
        return True

    @property
    def likely_unknown_preset(self) -> bool:
        """Diem qua thap voi MOI mode trong DB -> co the la preset chua
        duoc them vao fingerprint (vd preset moi/an cua Xhider)."""
        return bool(self.ranked) and self.best_score < UNKNOWN_PRESET_THRESHOLD

    def to_dict(self, top_n=5):
        return {
            "file": self.file,
            "size": self.size,
            "xhider_version_detected": self.xhider_version_detected,
            "db_version_used": self.db_version_used,
            "results": [{"mode": r.mode, "score": round(r.score, 2)} for r in self.ranked[:top_n]],
            "best_mode": self.best_mode,
            "best_score": round(self.best_score, 2),
            "is_confident": self.is_confident,
            "likely_unknown_preset": self.likely_unknown_preset,
            "warnings": self.warnings,
        }


# =========================== fingerprint DB ===========================

def available_db_versions() -> List[str]:
    if not os.path.isdir(FP_DIR):
        return []
    out = []
    for p in glob.glob(os.path.join(FP_DIR, "v*.json")):
        name = os.path.basename(p)[1:-5]
        out.append(name)
    return sorted(out)


def _version_key(v: str):
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _closest_version(target: str, candidates: List[str]) -> str:
    """Chon version trong DB GAN target nhat (so sanh tung so major.minor),
    thay vi luon lay ban 'moi nhat' mot cach mu quang."""
    tk = _version_key(target)
    def dist(v):
        vk = _version_key(v)
        n = max(len(tk), len(vk))
        tk2 = tk + (0,) * (n - len(tk))
        vk2 = vk + (0,) * (n - len(vk))
        return sum(abs(a - b) for a, b in zip(tk2, vk2))
    return min(candidates, key=dist)


_FP_CACHE: Dict[str, dict] = {}


def load_fingerprints(version: Optional[str]) -> Tuple[dict, str, List[str]]:
    warnings = []
    versions = available_db_versions()
    if not versions:
        sys.exit(f"[!] Khong tim thay fingerprint DB nao trong {FP_DIR}.\n"
                  f"    Hay chay build_fingerprints.py truoc.")

    if version and version in versions:
        chosen = version
    elif version:
        chosen = _closest_version(version, versions)
        warnings.append(
            f"Khong co fingerprint rieng cho XHider v{version} (DB co: {versions}). "
            f"Dang dung ban gan nhat (v{chosen}) - ket qua co the kem chinh xac hon "
            f"neu Xhider da doi cau truc harness giua cac version."
        )
    else:
        chosen = versions[-1]
        warnings.append(
            "Khong doc duoc version XHider tu header file. "
            f"Dang dung DB moi nhat (v{chosen})."
        )

    if chosen not in _FP_CACHE:
        with open(os.path.join(FP_DIR, f"v{chosen}.json"), encoding="utf-8") as f:
            _FP_CACHE[chosen] = json.load(f)
    return _FP_CACHE[chosen], chosen, warnings


# ============================ scoring ============================

def _count_similarity(t, r):
    if t == 0 and r == 0:
        # ca 2 ben deu khong dung feature nay -> KHONG mang nhieu thong tin,
        # cho diem trung tinh thay vi "khop tuyet doi" de tranh lam phinh
        # diem gia (vd script Lua thuong, khong lien quan Xhider, cung se
        # co rat nhieu feature = 0 va vo tinh "khop" voi mode it dung ham).
        return 0.5
    denom = max(r, t, 1)
    return max(0.0, 1.0 - abs(t - r) / denom)


def _ratio_mag_similarity(t, r):
    if t <= 0 or r <= 0:
        return None
    diff = abs(math.log(t + 1e-6) - math.log(r + 1e-6))
    return max(0.0, 1.0 - diff / 6.0)


def _scalar_similarity(t, r, scale=1.0):
    """So sanh 2 gia tri thuc (vd entropy, ty le) -> diem 0..1."""
    diff = abs(t - r)
    return max(0.0, 1.0 - diff / scale)


def score_against(target_regex, target_token, target_cp, ref_regex, ref_token, ref_cp):
    total_w = 0.0
    total_s = 0.0

    for name in COUNT_FEATURES:
        s = _count_similarity(target_regex.get(name, 0), ref_regex.get(name, 0))
        total_s += s * W_COUNT
        total_w += W_COUNT

    for name in RATIO_FEATURES:
        p_key, r_key = name + "_present", name + "_ratio"
        s_presence = 1.0 if target_regex.get(p_key, 0) == ref_regex.get(p_key, 0) else 0.0
        total_s += s_presence * W_PRESENCE
        total_w += W_PRESENCE
        s_mag = _ratio_mag_similarity(target_regex.get(r_key, 0), ref_regex.get(r_key, 0))
        if s_mag is not None:
            total_s += s_mag * W_RATIO_MAG
            total_w += W_RATIO_MAG

    for name in BOOL_FEATURES:
        s = 1.0 if target_regex.get(name, 0) == ref_regex.get(name, 0) else 0.0
        total_s += s * W_BOOL
        total_w += W_BOOL

    s_count = _count_similarity(target_token.get("total_tokens", 0), ref_token.get("total_tokens", 0))
    total_s += s_count * W_TOKEN_COUNT
    total_w += W_TOKEN_COUNT

    s_hist = hist_cosine_sim(target_token.get("hist", {}), ref_token.get("hist", {}))
    total_s += s_hist * W_TOKEN_HIST
    total_w += W_TOKEN_HIST

    pref_len = prefix_match_len(target_token.get("prefix", []), ref_token.get("prefix", []))
    max_pref = max(len(target_token.get("prefix", [])), len(ref_token.get("prefix", [])), 1)
    s_prefix = pref_len / max_pref
    total_s += s_prefix * W_TOKEN_PREFIX
    total_w += W_TOKEN_PREFIX

    # constant-pool entropy/thong ke (scale rieng cho tung dac trung)
    scales = {
        "str_entropy": 3.0, "str_avg_len": 200.0, "str_len_std": 200.0,
        "num_int_ratio": 1.0, "num_hex_ratio": 1.0, "num_float_ratio": 1.0,
    }
    per_feat_w = W_CONSTPOOL / len(CONSTPOOL_SCALAR_FEATURES)
    for name in CONSTPOOL_SCALAR_FEATURES:
        s = _scalar_similarity(target_cp.get(name, 0.0), ref_cp.get(name, 0.0), scales.get(name, 1.0))
        total_s += s * per_feat_w
        total_w += per_feat_w

    return (total_s / total_w) * 100.0 if total_w else 0.0


def family_of(mode):
    for grp in FAMILY_GROUPS:
        if mode in grp:
            return grp
    return {mode}


# ============================ core API ============================

def detect_text(text: str, filename: str = "<memory>", db_version: Optional[str] = None) -> DetectionResult:
    warnings = []
    detected_version = detect_xhider_version(text)
    fingerprints, db_ver_used, db_warnings = load_fingerprints(db_version or detected_version)
    warnings.extend(db_warnings)

    target_regex = extract_features(text)
    target_token = extract_token_features(text)
    target_cp = extract_constpool_features(text)

    ranked = []
    for mode, ref in fingerprints.items():
        s = score_against(target_regex, target_token, target_cp,
                           ref["regex"], ref["token"], ref.get("constpool", {}))
        ranked.append(ModeScore(mode, s))
    ranked.sort(key=lambda x: x.score, reverse=True)

    result = DetectionResult(
        file=filename,
        size=len(text),
        xhider_version_detected=detected_version,
        db_version_used=db_ver_used,
        ranked=ranked,
        warnings=warnings,
    )

    if result.likely_unknown_preset:
        result.warnings.append(
            f"Diem khop cao nhat chi {result.best_score:.1f}% (< {UNKNOWN_PRESET_THRESHOLD}%) - "
            f"THAP BAT THUONG so voi cac lan detect binh thuong (thuong ~90-100%). "
            f"Rat co the day la 1 preset CHUA CO trong fingerprint DB (vd preset moi/an nhu "
            f"'Hidden' tren xhider.xyz), hoac file khong phai duoc bao ve boi Xhider."
        )
    elif result.best_score < CONFIDENCE_THRESHOLD:
        result.warnings.append(
            f"Diem khop cao nhat chi {result.best_score:.1f}% (< {CONFIDENCE_THRESHOLD}%)."
        )
    elif len(ranked) > 1 and (ranked[0].score - ranked[1].score) < CLOSE_MARGIN:
        fam = family_of(ranked[0].mode)
        close = [r.mode for r in ranked if r.mode in fam][:6]
        result.warnings.append(
            f"Diem khop giua top cac mode rat gan nhau ({ranked[0].score:.1f}% vs "
            f"{ranked[1].score:.1f}%). Cac mode {close} co harness gan giong het nhau."
        )

    return result


def detect_file(path: str, db_version: Optional[str] = None) -> DetectionResult:
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    return detect_text(text, filename=path, db_version=db_version)


def _all_mode_scores(text: str, db_version: Optional[str] = None) -> Dict[str, float]:
    """Tra ve dict {mode: score} day du (dung cho --matrix)."""
    detected_version = detect_xhider_version(text)
    fingerprints, _, _ = load_fingerprints(db_version or detected_version)
    target_regex = extract_features(text)
    target_token = extract_token_features(text)
    target_cp = extract_constpool_features(text)
    out = {}
    for mode, ref in fingerprints.items():
        out[mode] = score_against(target_regex, target_token, target_cp,
                                   ref["regex"], ref["token"], ref.get("constpool", {}))
    return out


# ============================== CLI ==============================

def _print_result(res: DetectionResult, top_n: int, show_detail: bool):
    print(f"{'#':<3}{'Mode':<14}{'Do khop':>10}")
    print("-" * 30)
    for i, r in enumerate(res.ranked[:top_n], 1):
        print(f"{i:<3}{r.mode:<14}{r.score:>8.1f}%")
    print()
    if res.likely_unknown_preset:
        print(f"[!] {res.warnings[-1]}")
        print()
    print(f"==> Mode: {res.best_mode} ({res.best_score:.1f}%)")


def _cmd_single(args):
    if not os.path.exists(args.file):
        sys.exit(f"[!] Khong tim thay file: {args.file}")
    res = detect_file(args.file, db_version=args.version)
    if args.json:
        print(json.dumps(res.to_dict(args.top), ensure_ascii=False, indent=2))
    else:
        _print_result(res, args.top, args.detail)


def _detect_one_for_batch(path, db_version):
    try:
        res = detect_file(path, db_version=db_version)
        return {
            "file": path,
            "best_mode": res.best_mode,
            "best_score": round(res.best_score, 2),
            "is_confident": res.is_confident,
            "likely_unknown_preset": res.likely_unknown_preset,
            "note": "; ".join(res.warnings) if res.warnings else "",
        }
    except Exception as e:
        return {"file": path, "best_mode": "ERROR", "best_score": 0.0,
                "is_confident": False, "likely_unknown_preset": False, "note": str(e)}


def _matrix_row_for_batch(path, db_version):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        return path, _all_mode_scores(text, db_version=db_version)
    except Exception as e:
        return path, {}


def _cmd_dir(args):
    files = sorted(glob.glob(os.path.join(args.dir, "**", "*.lua"), recursive=True))
    if not files:
        sys.exit(f"[!] Khong tim thay file .lua nao trong {args.dir}")

    if args.matrix:
        all_modes = set()
        rows = {}
        workers = max(1, args.workers)
        if workers > 1 and len(files) > 1:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                futs = {ex.submit(_matrix_row_for_batch, p, args.version): p for p in files}
                for fut in as_completed(futs):
                    path, scores = fut.result()
                    rows[path] = scores
                    all_modes.update(scores.keys())
        else:
            for p in files:
                path, scores = _matrix_row_for_batch(p, args.version)
                rows[path] = scores
                all_modes.update(scores.keys())

        all_modes = sorted(all_modes)
        with open(args.matrix, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["file"] + all_modes)
            for path in files:
                scores = rows.get(path, {})
                w.writerow([path] + [round(scores.get(m, 0.0), 2) for m in all_modes])
        print(f"-> Da ghi ma tran diem ({len(files)} file x {len(all_modes)} mode) vao {args.matrix}")
        return

    workers = max(1, args.workers)
    rows = []
    if workers > 1 and len(files) > 1:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_detect_one_for_batch, p, args.version): p for p in files}
            results_by_path = {}
            for fut in as_completed(futs):
                r = fut.result()
                results_by_path[r["file"]] = r
            rows = [results_by_path[p] for p in files]
    else:
        rows = [_detect_one_for_batch(p, args.version) for p in files]

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["file", "best_mode", "best_score",
                                               "is_confident", "likely_unknown_preset", "note"])
            w.writeheader()
            w.writerows(rows)
        print(f"-> Da ghi {len(rows)} ket qua vao {args.csv}")

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(f"{'File':<40}{'Mode':<14}{'Diem':>8}  Ghi chu")
        print("-" * 90)
        for r in rows:
            flag = "?unk" if r["likely_unknown_preset"] else ("OK" if r["is_confident"] else "?")
            print(f"{os.path.basename(r['file']):<40}{r['best_mode']:<14}{r['best_score']:>7.1f}%  {flag}")


def main():
    ap = argparse.ArgumentParser(description="Xhider obfuscation mode detector")
    ap.add_argument("file", nargs="?", help="File .lua can nhan dien")
    ap.add_argument("--dir", help="Quet toan bo file .lua trong 1 thu muc (batch mode)")
    ap.add_argument("--top", type=int, default=5, help="So luong ket qua hien thi (mac dinh 5)")
    ap.add_argument("--json", action="store_true", help="Xuat ket qua dang JSON")
    ap.add_argument("--csv", help="(dung voi --dir) ghi ket qua batch ra file CSV")
    ap.add_argument("--matrix", help="(dung voi --dir) ghi ma tran diem day du (file x mode) ra CSV")
    ap.add_argument("--workers", type=int, default=1, help="(dung voi --dir) so tien trinh song song")
    ap.add_argument("--detail", action="store_true", help="In chi tiet diem tung dac trung (single-file)")
    ap.add_argument("--version", help="Ep dung fingerprint DB cua 1 version cu the (vd 1.2)")
    args = ap.parse_args()

    if args.dir:
        _cmd_dir(args)
    elif args.file:
        _cmd_single(args)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
