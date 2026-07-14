"""
Lua Tokenizer (nhe, khong dung thu vien ngoai, khong de quy)
==============================================================
Dung de trich xuat "structural shape" o muc token thay vi phai parse
AST day du (thu vien luaparser dua tren ANTLR bi TREO/timeout tren ~50%
file mau do bieu thuc so hoc nguy trang qua sau -> khong dung duoc cho
tool thuc te). Tokenizer nay chi phan loai token (KEYWORD/NAME/NUMBER/
STRING/OP/...) theo thu tu xuat hien, du de lam "van tay cau truc" ma
van chay duoc tren file vai tram KB trong vai chuc milli-giay.
"""
import re

_KEYWORDS = {
    "and", "break", "do", "else", "elseif", "end", "false", "for",
    "function", "goto", "if", "in", "local", "nil", "not", "or",
    "repeat", "return", "then", "true", "until", "while",
}

# thu tu quan trong: string (bao gom long string [[..]]) va comment truoc,
# roi den number, roi name/keyword, roi operator/punct
# long string / long comment [[ .. ]] hoac [=[ .. ]=] (khong ho tro backref
# trong 1 pattern gop chung nen tach rieng, du de fingerprint)
_LONGBRACKET_RE = re.compile(r"\[(=*)\[.*?\]\1\]", re.DOTALL)

_TOKEN_RE = re.compile(r"""
    (?P<COMMENT>--[^\n]*)
  | (?P<STRING>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
  | (?P<NUMBER>0[xX][0-9A-Fa-f]+|\d+\.?\d*(?:[eE][+-]?\d+)?)
  | (?P<NAME>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<OP>\.\.\.|\.\.|==|~=|<=|>=|::|[-+*/%^#<>=(){}\[\];:,.])
""", re.VERBOSE | re.DOTALL)


def tokenize(text, max_tokens=200000):
    """Tra ve list token dang (TYPE) - da gop KEYWORD rieng khoi NAME.
    Gioi han max_tokens de tranh file cuc lon lam cham (van du de fingerprint).
    """
    out = []
    pos = 0
    n = len(text)
    count = 0
    while pos < n and count < max_tokens:
        # thu khop long-bracket string/comment truoc ([[ ... ]] / [=[ ... ]=])
        if text[pos] == "[" and pos + 1 < n and text[pos + 1] in "[=":
            lm = _LONGBRACKET_RE.match(text, pos)
            if lm:
                out.append("STRING")
                count += 1
                pos = lm.end()
                continue
        m = _TOKEN_RE.match(text, pos)
        if not m:
            pos += 1
            continue
        kind = m.lastgroup
        if kind == "COMMENT":
            pos = m.end()
            continue
        if kind == "NAME":
            val = m.group(0)
            kind = "KEYWORD" if val in _KEYWORDS else "NAME"
        out.append(kind)
        count += 1
        pos = m.end()
    return out
