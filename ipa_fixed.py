import re

# IPA gravado uma vez só (você decide)
IPA_FIXO = {
    # já existem
    'casa':   'ˈka.za',
    'maison': 'mɛ.zɔ̃',
    'house':  'haʊs',
    'agua':   'ˈa.ɣwa',   # pt/es
    'amor':   'a.ˈmor',   # pt/es
    'water':  'ˈwɔ.tər',  # en
    'love':   'ˈlʌv',     # en
    'eau':    'o',        # fr
    'amour':  'a.ˈmuʁ',   # fr
}

def ipa_fixed(word: str, lang: str) -> str:
    word = word.lower()
    return IPA_FIXO.get(word, re.sub(r'[^a-z]', '', word))