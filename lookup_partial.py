# lookup_partial.py
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
import json
import math

EN_DASH = "–"  # en dash usado na serialização do code-O

def _split_triplet(s: str) -> List[float]:
    """
    Converte "0.100–0.010–0.800" ou "0.100-0.010-0.800" em [0.100, 0.010, 0.800]
    """
    if not s:
        return []
    s = s.strip()
    if EN_DASH in s:
        parts = s.split(EN_DASH)
    else:
        parts = s.split("-")
    vals = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        try:
            vals.append(float(p))
        except Exception:
            # ignora tokens inválidos
            pass
    return vals[:3]

def _triplet_distance(a: List[float], b: List[float], metric: str = "l2") -> float:
    if not a or not b or len(a) != len(b):
        return float("inf")
    if metric == "l1":
        return sum(abs(x - y) for x, y in zip(a, b))
    # l2 (default)
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

def _norm_code_o(s: str) -> str:
    """
    Normaliza string do code-O para a forma canônica com EN_DASH e 3 casas.
    """
    vals = _split_triplet(s)
    if not vals:
        return ""
    return EN_DASH.join(f"{v:.3f}" for v in vals)

def build_code_o_index(conn) -> Dict[str, List[Tuple[str, str, float]]]:
    """
    Lê a tabela gama e constrói um índice:
      codeO_str -> [(lang, lemma, conf), ...]
    """
    cur = conn.cursor()
    cur.execute("SELECT lang, lemma, conf, marks FROM gama")
    out: Dict[str, List[Tuple[str, str, float]]] = {}
    for lang, lemma, conf, marks in cur.fetchall():
        code_o_str = ""
        if marks:
            try:
                m = json.loads(marks)
                code_o_str = _norm_code_o(m.get("codeO", ""))
            except Exception:
                code_o_str = ""
        if not code_o_str:
            # sem code-O, ignora
            continue
        out.setdefault(code_o_str, []).append((lang, lemma, float(conf)))
    return out

def lookup_by_code_o(
    conn,
    code_o_query: str,
    target_lang: Optional[str] = None,
    tol: Optional[float] = None,
    metric: str = "l2",
) -> List[Tuple[str, str, float, float]]:
    """
    Busca por ressonância do code-O.
    - code_o_query: string "0.100–0.010–0.800" (qualquer separador aceito)
    - target_lang: se fornecido, filtra para o idioma de destino
    - tol: tolerância (None = match EXATO)
    - metric: "l1" ou "l2"
    Retorna lista [(lang, lemma, conf, dist)] ordenada por distância (e conf decrescente).
    """
    idx = build_code_o_index(conn)
    q_vec = _split_triplet(code_o_query)
    q_str = _norm_code_o(code_o_query)

    results: List[Tuple[str, str, float, float]] = []

    if tol is None:
        # match exato
        hits = idx.get(q_str, [])
        for lang, lemma, conf in hits:
            if (target_lang is None) or (lang == target_lang):
                results.append((lang, lemma, conf, 0.0))
        # ordena por conf desc (dist é 0 para todos)
        results.sort(key=lambda r: (-r[2], r[1]))
        return results

    # por tolerância (busca aproximada)
    for key, entries in idx.items():
        k_vec = _split_triplet(key)
        dist = _triplet_distance(q_vec, k_vec, metric=metric)
        if math.isfinite(dist) and dist <= float(tol):
            for lang, lemma, conf in entries:
                if (target_lang is None) or (lang == target_lang):
                    results.append((lang, lemma, conf, dist))

    # ordena por menor distância e maior confiança
    results.sort(key=lambda r: (r[3], -r[2], r[1]))
    return results
