import re

_VERSION_RE = re.compile(r"XHider\s+v([0-9]+(?:\.[0-9]+)*)", re.IGNORECASE)


def detect_xhider_version(text: str) -> str | None:
    """Doc header '--// This file was created by XHider v1.2 [...]'.
    Tra ve chuoi version (vd '1.2') hoac None neu khong tim thay."""
    m = _VERSION_RE.search(text[:500])  # header luon o dau file
    return m.group(1) if m else None
