"""
Token-level structural fingerprint
====================================
Bo sung cho features.py (dem tu khoa bang regex). Module nay tokenize toan
bo file (KEYWORD/NAME/NUMBER/STRING/OP) roi trich:
  - total_tokens     : tong so token (phan anh "do phinh to" cua vo harness,
                        rat co ich de tach cac mode nhu Weak/Normal/Wrd/
                        Strong/Medium vi chung tang dan do phuc tap).
  - token_hist       : phan bo ty le cac loai token (hinh dang code tong the).
  - prefix           : chuoi loai token cua N token dau tien - day la "van
                        tay" on dinh nhat vi phan dau file luon la ma harness
                        co dinh cua mode, chua bi tron lan voi du lieu script
                        duoc bao ve (thuong nam o giua/cuoi).
Ly do dung tokenizer tu viet thay vi luaparser (AST day du): thu vien
luaparser (dua tren ANTLR) bi TREO/timeout tren ~50% file mau do bieu thuc
so hoc nguy trang qua sau -> khong dung duoc cho tool thuc te.
"""
import collections
from lua_tokenizer import tokenize

PREFIX_LEN = 300


def extract_token_features(text: str) -> dict:
    toks = tokenize(text)
    total = max(len(toks), 1)
    hist = collections.Counter(toks)
    hist_norm = {k: v / total for k, v in hist.items()}
    prefix = toks[:PREFIX_LEN]
    return {
        "total_tokens": len(toks),
        "hist": hist_norm,
        "prefix": prefix,
    }


def prefix_match_len(a, b):
    n = 0
    for x, y in zip(a, b):
        if x == y:
            n += 1
        else:
            break
    return n


def hist_cosine_sim(h1: dict, h2: dict) -> float:
    keys = set(h1) | set(h2)
    if not keys:
        return 1.0
    dot = sum(h1.get(k, 0.0) * h2.get(k, 0.0) for k in keys)
    n1 = sum(v * v for v in h1.values()) ** 0.5
    n2 = sum(v * v for v in h2.values()) ** 0.5
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)
