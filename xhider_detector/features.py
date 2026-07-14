"""
Xhider Obfuscator Mode Detector - Feature Extraction
Trich xuat cac dac trung cau truc (structural fingerprint) tu 1 file .lua
da duoc bao ve boi Xhider, dung de nhan dien mode (Basic, Hard, Ib1, R2, ...).

Nguyen tac thiet ke:
- Cac dac trung DEM SO LAN GOI HAM runtime (getfenv, setfenv, newproxy, rawget,
  bit32.*, coroutine.*, pcall...) phan anh "vo VM / harness" co dinh cua tung
  mode -> hau nhu KHONG doi du script goc duoc bao ve la gi (rat on dinh).
- Cac dac trung ve MA HOA HANG SO (so hex, chuoi hex dai, bieu thuc so hoc
  nguy trang, dat ten bien kieu v_0/v_1...) phan anh KY THUAT ma hoa constant
  pool cua mode -> co the co gia tri tuyet doi thay doi theo kich thuoc script
  nhung SU HIEN DIEN (co dung hay khong) la on dinh -> dung dang boolean/ratio.
- KHONG dung "size" file lam dac trung chinh (chi dung de phan hang phu / tie-break)
  vi no phu thuoc hoan toan vao kich thuoc script duoc bao ve.
"""
import re

# ---- cac pattern regex dung chung ----
_RE = {
    "getfenv": re.compile(r"getfenv"),
    "setfenv": re.compile(r"setfenv"),
    "debug_": re.compile(r"debug\.\w+"),
    "bit32": re.compile(r"bit32"),
    "coroutine": re.compile(r"coroutine\.\w+"),
    "string_char": re.compile(r"string\.char"),
    "string_byte": re.compile(r"string\.byte"),
    "table_concat": re.compile(r"table\.concat"),
    "table_remove": re.compile(r"table\.remove"),
    "math_random": re.compile(r"math\.random"),
    "loadstring": re.compile(r"loadstring|load\("),
    "select_hash": re.compile(r"select\(['\"]#"),
    "pcall": re.compile(r"\bpcall\("),
    "xpcall": re.compile(r"\bxpcall\("),
    "elseif_chain": re.compile(r"elseif"),
    "getmetatable": re.compile(r"getmetatable"),
    "setmetatable": re.compile(r"setmetatable"),
    "rawget": re.compile(r"rawget|rawset|rawequal|rawlen"),
    "newproxy": re.compile(r"newproxy"),
    "os_": re.compile(r"os\.\w+"),
    "collectgarbage": re.compile(r"collectgarbage"),
    "ipairs_pairs": re.compile(r"\bipairs\(|\bpairs\("),
    "unpack": re.compile(r"\bunpack\(|table\.unpack"),
    "bxor_ops": re.compile(r"bxor|band|bor|bnot|lshift|rshift"),
    "func_defs": re.compile(r"function\("),
    "for_loops": re.compile(r"\bfor\b"),
    "while_loops": re.compile(r"\bwhile\b"),
    "gsub": re.compile(r"\.gsub\("),
    "gmatch": re.compile(r"\.gmatch\("),
    "dispatch_while_v": re.compile(r"while \w{1,3} do if \w{1,3}<"),
    "hex_numbers": re.compile(r"0[xX][0-9A-Fa-f]+"),
    "long_hex_str": re.compile(r'"[0-9A-Fa-f]{16,}"'),
    "underscore_var": re.compile(r"\b[A-Za-z_][A-Za-z0-9]*_[0-9]+\b"),
    "arith_obf": re.compile(r"\(-?[0-9]+[+\-]\(-?[0-9]+\)\)"),
    "semicolon_table": re.compile(r'";"'),  # phan cach ; trong bang chuoi
    "header_gsub_wrap": re.compile(r'gsub\(".\+"'),
    "long_string_bracket": re.compile(r"\[\["),
}

# cac dac trung "dem so lan" (count features) -> dung nguyen gia tri, so sanh
# gan dung (tolerance nho) vi day la phan "vo harness" it doi theo script.
COUNT_FEATURES = [
    "getfenv", "setfenv", "debug_", "bit32", "coroutine", "string_char",
    "string_byte", "table_concat", "table_remove", "math_random",
    "loadstring", "select_hash", "pcall", "xpcall", "elseif_chain",
    "getmetatable", "setmetatable", "rawget", "newproxy", "os_",
    "collectgarbage", "ipairs_pairs", "unpack", "bxor_ops", "for_loops",
    "while_loops", "gsub", "gmatch", "dispatch_while_v",
]

# cac dac trung "ty le / boolean" (data-encoding style) -> phu thuoc kich
# thuoc script nen so sanh theo nguong hien dien (>0) hoac ty le / size.
RATIO_FEATURES = [
    "hex_numbers", "long_hex_str", "underscore_var", "arith_obf",
    "semicolon_table", "long_string_bracket",
]

BOOL_FEATURES = ["header_gsub_wrap"]


def extract_features(text: str) -> dict:
    feats = {}
    size = max(len(text), 1)
    for name in COUNT_FEATURES:
        feats[name] = len(_RE[name].findall(text))
    for name in RATIO_FEATURES:
        cnt = len(_RE[name].findall(text))
        feats[name + "_present"] = 1 if cnt > 0 else 0
        feats[name + "_ratio"] = cnt / size * 1000.0  # per-mille of file size
    for name in BOOL_FEATURES:
        feats[name] = 1 if _RE[name].search(text) else 0
    feats["_size"] = size
    return feats
