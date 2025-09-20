from tnu import init_db
from lookup_partial import lookup_partial
from sigma_partial import sigma_partial

def translate_partial(word: str, src: str, tgt: str, part: str = 'C') -> list[str]:
    conn = init_db()
    partial = sigma_partial(word, src, part)
    hits = []
    for lang, lemma, conf in lookup_partial(conn, partial):
        if lang == tgt:
            hits.append(lemma)
    return hits