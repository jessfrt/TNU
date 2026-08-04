"""Sinal etimológico provisório, mas reprodutível.

Até existir uma fonte etimológica curada, este valor não deve ser interpretado
como etimologia real. Ele apenas mantém a dimensão numérica estável entre
execuções; ``hash()`` do Python é aleatorizado por processo e não serve para
um pipeline determinístico.
"""

import hashlib

ETYMO_WEIGHT = {"latin": 0.9, "greek": 0.8, "germanic": 0.7, "slavic": 0.6}


def etym_score(word: str, lang: str) -> float:
    """Retorna um placeholder estável em {0.5, 0.6, 0.7, 0.8, 0.9}."""
    key = f"{(lang or '').casefold().strip()}:{(word or '').casefold().strip()}"
    bucket = hashlib.blake2b(key.encode("utf-8"), digest_size=1).digest()[0] % 5
    return 0.5 + bucket / 10
