import unicodedata
import re
from typing import List, Tuple, Dict

# ------------------------------
# 1) Normalização determinística
# ------------------------------
def _canon(s: str) -> str:
    # NFC + casefold + colapso de espaços
    s = unicodedata.normalize("NFC", s or "")
    s = s.casefold().strip()
    s = " ".join(s.split())
    return s

# -------------------------------------------------
# 2) Dicionário canônico (por idioma, por palavra)
#    → sempre preferido quando houver match exato
# -------------------------------------------------
# Formato: (lang, lemma) -> "ipa.com.pontos"
IPA_FIXO: Dict[Tuple[str, str], str] = {
    ("pt", "casa"):   "ˈka.za",
    ("fr", "maison"): "mɛ.zɔ̃",
    ("en", "house"):  "haʊs",

    ("pt", "água"):   "ˈa.ɣwa",
    ("es", "agua"):   "ˈa.ɣwa",

    ("pt", "amor"):   "a.ˈmoɾ",
    ("es", "amor"):   "a.ˈmoɾ",

    ("en", "water"):  "ˈwɔ.təɹ",
    ("en", "love"):   "ˈlʌv",

    ("fr", "eau"):    "o",
    ("fr", "amour"):  "a.ˈmuʁ",
}

# ---------------------------------------------------------
# 3) Regras mínimas por idioma (substituições deterministas)
#    → objetivo: pseudo-IPA estável, não perfeição fonética
# ---------------------------------------------------------
LANG_RULES: Dict[str, Tuple[Tuple[str, str], ...]] = {
    # português
    "pt": (
        ("nh", "ɲ"), ("lh", "ʎ"), ("ch", "ʃ"),
        ("qu", "k"), ("gu", "g"),
        ("rr", "ʁ"), ("r", "ɾ"),
        ("x", "ʃ"), ("ç", "s"),
    ),
    # espanhol
    "es": (
        ("ll", "ʎ"), ("ch", "tʃ"), ("ñ", "ɲ"),
        ("qu", "k"), ("gue", "ge"), ("gui", "gi"),
    ),
    # francês
    "fr": (
        ("ch", "ʃ"), ("gn", "ɲ"),
        ("on", "ɔ̃"), ("an", "ɑ̃"), ("en", "ɑ̃"),
        ("in", "ɛ̃"), ("un", "œ̃"),
        ("oi", "wa"), ("ou", "u"),
    ),
    # inglês (simplificado)
    "en": (
        ("ch", "tʃ"), ("sh", "ʃ"), ("th", "θ"),
        ("ph", "f"), ("gh", "g"), ("qu", "kw"),
    ),
    # alemão (mínimo)
    "de": (
        ("sch", "ʃ"), ("ch", "x"), ("qu", "kv"),
    ),
    # italiano (mínimo)
    "it": (
        ("ch", "k"), ("gli", "ʎi"), ("gn", "ɲ"),
    ),
}

# vogais por idioma (para silabificação simples e estável)
VOWELS_BY_LANG: Dict[str, str] = {
    "pt": "aeiouáéíóúâêôãõ",
    "es": "aeiouáéíóúü",
    "fr": "aeiouàâæçéèêëîïôœùûüÿ",
    "en": "aeiouy",
    "de": "aeiouyäöü",
    "it": "aeiouàèéìíîòóùú",
}

DEFAULT_VOWELS = "aeiouy"

# --------------------------------------------
# 4) Fallback determinístico (pseudo-IPA estável)
# --------------------------------------------
def _apply_lang_rules(word: str, lang: str) -> str:
    rules = LANG_RULES.get(lang, ())
    s = word
    # aplica regras na ordem (determinístico)
    for a, b in rules:
        s = s.replace(a, b)
    # remove tudo que não for letra/diacrítico/ipa básico
    s = re.sub(r"[^a-zA-Zɑɛɔɲʎʃʁʒθtʃxœ̃ɔ̃ɑ̃ɛ̃ɾ]", "", s)
    return s

def _syllabify_simple(s: str, lang: str) -> List[str]:
    """
    Silabifica de forma estável:
    - separa por grupos CV aproximados usando vogais do idioma
    - marca acento primário na primeira sílaba ('ˈ') se houver 2+ sílabas
    Não é fonologia perfeita — é determinismo estável para o alfa.
    """
    vowels = VOWELS_BY_LANG.get(lang, DEFAULT_VOWELS)
    # grupos "até a próxima vogal" (C* V+)
    pattern = rf"[^ {vowels}]*[{vowels}]+"
    toks = re.findall(pattern, s)
    toks = [t for t in toks if t] or [s]  # garante pelo menos 1 token
    if len(toks) >= 2 and not toks[0].startswith("ˈ"):
        toks[0] = "ˈ" + toks[0]
    return toks

# -------------------------------------------------------
# 5) Função pública — SEMPRE retorna lista de tokens IPA
# -------------------------------------------------------
def ipa_fixed(word: str, lang: str) -> List[str]:
    """
    Retorna uma sequência IPA determinística (lista de tokens).
    1) Tenta dicionário canônico (lang, lemma).
    2) Caso contrário, aplica regras mínimas do idioma e silabificação estável.
    """
    lemma = _canon(word)
    lang  = _canon(lang)

    # 1) dicionário canônico
    ipa_known = IPA_FIXO.get((lang, lemma))
    if ipa_known:
        # "ˈka.za" -> ["ˈka", "za"]
        return [t for t in ipa_known.split(".") if t]

    # 2) fallback determinístico
    # remove espaços e pontuação, mantem letras/diacríticos
    base = re.sub(r"[^a-zA-Záàâãäçéèêëíìïîóòôõöúùüŷñ]", "", lemma)
    base = base or lemma  # se tudo sumir, usa lemma canônico

    mapped = _apply_lang_rules(base, lang)
    tokens = _syllabify_simple(mapped, lang)
    return tokens
