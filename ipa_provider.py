import re
from phonemizer import phonemize
from phonemizer.backend import EspeakBackend

# backends disponíveis
BACKENDS = {
    "pt": "pt-br",
    "en": "en-us",
    "es": "es",
    "fr": "fr-fr",
    "de": "de",
    "it": "it",
}

def ipa(word: str, lang: str) -> str:
    if lang in BACKENDS:
        backend = EspeakBackend(BACKENDS[lang])
        ipa_str = backend.phonemize([word], strip=True)[0]
        return ipa_str
    # fallback
    return re.sub(r'\W+', '', word.lower())