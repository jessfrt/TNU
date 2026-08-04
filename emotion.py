"""Cálculo opcional de valência emocional.

O restante do projeto deve continuar funcionando quando o NLTK (ou o corpus
``sentiwordnet``) não estiver instalado. Nesse caso, usamos a valência neutra.
"""

try:
    from nltk.corpus import sentiwordnet as swn
except ImportError:
    swn = None


def valence(word: str) -> float:
    """Retorna uma valência em [0, 1], ou 0.5 quando o recurso não existe."""
    if swn is None:
        return 0.5

    try:
        synsets = list(swn.senti_synsets(word))
    except LookupError:
        # NLTK instalado, mas corpus ``wordnet``/``sentiwordnet`` ausente.
        return 0.5

    if not synsets:
        return 0.5
    pos = sum(s.pos_score() for s in synsets) / len(synsets)
    neg = sum(s.neg_score() for s in synsets) / len(synsets)
    return round(0.5 + pos - neg, 3)

