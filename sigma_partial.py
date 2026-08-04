# sigma_partial.py
from typing import List
from tnu_determinism import quantize_seq

EN_DASH = "–"

def _format_triplet(vals: List[float]) -> str:
    return EN_DASH.join(f"{v:.3f}" for v in vals)

def sigma_partial(word: str, lang: str, which: str = "B",
                  *, sigma_vector: List[float] | None = None,
                  make_vector_fn=None) -> str:
    """
    Núcleo B₂ (mais estável, menos ruído fonético):
      vec = [e1,e2,e3,e4,e5,e6,e7]
      c0 = média(e1, e2, e7)   -> fonética + forma + bucket estável
      c1 = e5                  -> etimologia
      c2 = e6                  -> valência emocional
    """
    if sigma_vector is None:
        if make_vector_fn is None:
            from tnu import alfa_vector as _alfa_vector
            vec, _ = _alfa_vector(word, lang)
        else:
            vec = make_vector_fn(word, lang)
    else:
        vec = list(sigma_vector)

    vec = quantize_seq(vec, ndigits=6)
    while len(vec) < 7:
        vec.append(0.0)

    e1, e2, e3, e4, e5, e6, e7 = vec[:7]
    c0 = round((e1 + e2 + e7) / 3.0, 6)
    c1 = e5
    c2 = e6

    return _format_triplet([c0, c1, c2])
