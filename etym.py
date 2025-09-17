# etym.py – placeholder até conectar Wikidata
ETYMO_WEIGHT = {"latin": 0.9, "greek": 0.8, "germanic": 0.7, "slavic": 0.6}

def etym_score(word: str, lang: str) -> float:
    # mock: baseado na inicial da palavra
    return 0.5 + (hash(word) % 5) / 10