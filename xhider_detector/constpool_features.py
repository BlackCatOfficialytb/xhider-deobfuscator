"""
Phan tich thong ke "constant pool" (bang hang so)
====================================================
Bo sung lop dac trung thu 3 (ngoai regex-count va token-shape): thong ke
tren CHINH NOI DUNG cac chuoi/so lieu duoc nhung trong file, thay vi chi
dem so lan xuat hien cau truc. Y tuong: 2 mode co the giong het nhau ve
"vo harness" (so lan goi ham, so vong lap...) nhung khac nhau o CACH MA
HOA du lieu (VD 1 mode encode string thanh mang so nguyen dai, 1 mode
khac encode thanh chuoi hex, 1 mode khac dung base64-like alphabet...).
Entropy va phan bo do dai la dau hieu it bi anh huong boi kich thuoc
script hon la dem tuyet doi.
"""
import math
import re
import collections

_STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
_NUMBER_RE = re.compile(r"\b\d+\.\d+\b|\b0[xX][0-9A-Fa-f]+\b|\b\d+\b")
_INT_RE = re.compile(r"^\d+$")
_HEX_RE = re.compile(r"^0[xX][0-9A-Fa-f]+$")
_FLOAT_RE = re.compile(r"^\d+\.\d+$")


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = collections.Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def extract_constpool_features(text: str) -> dict:
    strings = [m.group(0)[1:-1] for m in _STRING_RE.finditer(text)]
    numbers = [m.group(0) for m in _NUMBER_RE.finditer(text)]

    joined_strings = "".join(strings)
    str_lengths = [len(s) for s in strings]

    n_int = sum(1 for n in numbers if _INT_RE.match(n))
    n_hex = sum(1 for n in numbers if _HEX_RE.match(n))
    n_float = sum(1 for n in numbers if _FLOAT_RE.match(n))
    n_total = max(len(numbers), 1)

    feats = {
        "str_count": len(strings),
        "str_entropy": round(_shannon_entropy(joined_strings), 3),
        "str_avg_len": round(sum(str_lengths) / len(str_lengths), 2) if str_lengths else 0.0,
        "str_len_std": round(_stdev(str_lengths), 2) if len(str_lengths) > 1 else 0.0,
        "num_int_ratio": round(n_int / n_total, 3),
        "num_hex_ratio": round(n_hex / n_total, 3),
        "num_float_ratio": round(n_float / n_total, 3),
        "num_count": len(numbers),
    }
    return feats


def _stdev(vals):
    m = sum(vals) / len(vals)
    var = sum((v - m) ** 2 for v in vals) / len(vals)
    return var ** 0.5


CONSTPOOL_SCALAR_FEATURES = [
    "str_entropy", "str_avg_len", "str_len_std",
    "num_int_ratio", "num_hex_ratio", "num_float_ratio",
]
