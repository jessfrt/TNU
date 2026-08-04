# tnu_determinism.py
import unicodedata, json, hashlib
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Any

def canonical_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "")
    s = s.casefold().strip()
    return " ".join(s.split())

def quantize_float(x: float, ndigits: int = 6) -> float:
    return float(Decimal(x).quantize(Decimal(f"1e-{ndigits}"), rounding=ROUND_HALF_UP))

def quantize_seq(xs: List[float], ndigits: int = 6) -> List[float]:
    return [quantize_float(float(x), ndigits) for x in xs]

def stable_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def stable_hash(payload: str, digest_bytes: int = 16) -> str:
    # 128 bits hexa (32 chars); determinístico
    return hashlib.blake2b(payload.encode("utf-8"), digest_size=digest_bytes).hexdigest()

def make_sigma_payload(word: str, lang: str, ipa_seq, sigma_vector, meta=None) -> str:
    return stable_json({
        "w": canonical_text(word),
        "lang": canonical_text(lang),
        "ipa": list(ipa_seq) if isinstance(ipa_seq, (list, tuple)) else [str(ipa_seq)],
        "sigma": quantize_seq(sigma_vector),
        "meta": meta or {}
    })
