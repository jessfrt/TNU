# translate_partial.py
import argparse
import json, sqlite3
import sys
from typing import List, Tuple, Dict

EN_DASH = "–"

DEFAULT_HYBRID_WEIGHTS = {"D": 0.80, "B": 0.10, "A": 0.05, "C": 0.05}

def _parse_triplet(code_o: str) -> List[float]:
    s = (code_o or "").strip()
    parts = s.split(EN_DASH) if EN_DASH in s else s.split("-")
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        try:
            out.append(float(p))
        except:
            out.append(0.0)
    while len(out) < 3:
        out.append(0.0)
    return out[:3]

def _scalar_weighted(vals: List[float]) -> float:
    c0, c1, c2 = (vals + [0.0, 0.0, 0.0])[:3]
    return 0.5*c0 + 0.4*c1 + 0.1*c2

def _sub(a: List[float], b: List[float]) -> List[float]:
    return [a[i]-b[i] for i in range(3)]

def _l1(a: List[float], b: List[float]) -> float:
    return sum(abs(a[i]-b[i]) for i in range(3))

def _distance_triplet(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    """Distância euclidiana dos três componentes, usada pelo debug de tnu.py."""
    return sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)) ** 0.5

def _normalized_ipa_distance(word_a: str, lang_a: str, word_b: str, lang_b: str) -> float:
    """Distância de Levenshtein sobre a pseudo-IPA, normalizada em [0, 1]."""
    from ipa_fixed import ipa_fixed
    a = "".join(ipa_fixed(word_a, lang_a))
    b = "".join(ipa_fixed(word_b, lang_b))
    if not a and not b:
        return 0.0
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, 1):
        current = [i]
        for j, char_b in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (char_a != char_b)))
        previous = current
    return previous[-1] / max(len(a), len(b), 1)

def _pos_distance(source_marks: dict, target_marks: dict) -> float:
    """C é opcional: enquanto não houver POS, não influencia a busca."""
    source_pos, target_pos = source_marks.get("pos"), target_marks.get("pos")
    if not source_pos or not target_pos:
        return 0.0
    return 0.0 if source_pos == target_pos else 1.0

def hybrid_search(
    conn: sqlite3.Connection,
    query_lang: str,
    query_word: str,
    target_lang: str,
    weights: Dict[str, float] | None,
    ontology: dict,
    top_k: int = 5,
    missing_d_penalty: float = 1.0,
) -> list[dict]:
    """Busca alvo por score híbrido D+B+A+C, preservando a busca legado.

    Retorna dicionários com lema, score, componentes e relação ontológica.
    D ausente não é confundido com igualdade: recebe a penalidade configurada.
    """
    from ontology import hybrid_score, ontology_distance, relation_type, senses_for
    from sigma_partial import sigma_partial

    active_weights = dict(DEFAULT_HYBRID_WEIGHTS)
    if weights:
        active_weights.update(weights)
    if any(value < 0 for value in active_weights.values()):
        raise ValueError("Pesos híbridos não podem ser negativos.")

    source_code_o = _parse_triplet(sigma_partial(query_word, query_lang, "B"))
    source_marks = {"ipa": [], "codeO": EN_DASH.join(str(x) for x in source_code_o)}
    source_senses = senses_for(query_lang, query_word, ontology)
    cursor = conn.cursor()
    cursor.execute("SELECT lemma, marks FROM gama WHERE lang=?", (target_lang,))
    results: dict[str, dict] = {}
    for lemma, marks_raw in cursor.fetchall():
        try:
            target_marks = json.loads(marks_raw) if marks_raw else {}
        except (TypeError, json.JSONDecodeError):
            target_marks = {}
        target_code_o = _parse_triplet(target_marks.get("codeO", ""))
        # Distância B L1 normalizada: três componentes em escala aproximada [0,1].
        d_b = min(1.0, _l1(source_code_o, target_code_o) / 3.0)
        d_a = _normalized_ipa_distance(query_word, query_lang, lemma, target_lang)
        d_c = _pos_distance(source_marks, target_marks)
        d_d_raw = ontology_distance(query_lang, query_word, target_lang, lemma, ontology)
        d_d = missing_d_penalty if d_d_raw is None else d_d_raw
        components = {"D": d_d, "B": d_b, "A": d_a, "C": d_c}
        score = hybrid_score(components, {}, active_weights)

        target_senses = senses_for(target_lang, lemma, ontology)
        relation = None
        if source_senses and target_senses:
            # Mostra a primeira relação explícita encontrada; a distância usa o mínimo.
            relation = next(
                (rel for source in source_senses for target in target_senses
                 if (rel := relation_type(source, target, ontology)) is not None),
                None,
            )
        item = {"lemma": lemma, "lang": target_lang, "score": round(score, 6),
                "distance": components, "relation": relation,
                "senses": target_senses}
        # gama pode conter versões históricas da mesma palavra: conserva a melhor.
        if lemma not in results or item["score"] < results[lemma]["score"]:
            results[lemma] = item
    return sorted(results.values(), key=lambda row: (row["score"], row["lemma"]))[:max(1, top_k)]

def _lang_means(conn: sqlite3.Connection) -> Dict[str, List[float]]:
    cur = conn.cursor()
    cur.execute("SELECT lang, marks FROM gama")
    acc: Dict[str, Tuple[List[float], int]] = {}
    for lang, marks in cur.fetchall():
        try:
            m = json.loads(marks) if marks else {}
        except Exception:
            m = {}
        trip = _parse_triplet(m.get("codeO", ""))
        s, n = acc.get(lang, ([0.0, 0.0, 0.0], 0))
        acc[lang] = ([s[0]+trip[0], s[1]+trip[1], s[2]+trip[2]], n+1)
    mu: Dict[str, List[float]] = {}
    for lang, (s, n) in acc.items():
        n = max(1, n)
        mu[lang] = [s[0]/n, s[1]/n, s[2]/n]
    return mu

def _semantic_aux(word: str, lang: str) -> Tuple[float, float]:
    try:
        from etym import etym_score
        from emotion import valence
        e = float(etym_score(word, lang) or 0.0)
        v = float(valence(word.casefold()) or 0.0)
        return e, v
    except Exception:
        return 0.0, 0.0

def translate_partial(
    conn: sqlite3.Connection,
    word: str,
    src: str,
    tgt: str,
    tol: float | None = 0.005,
    *,
    norm: str = "lang",
    tau_scalar: float = 0.045,
    tau_c0: float = 0.18,
    tau_c1: float = 0.15,
    tau_c2: float = 0.20,
    w_aux: float = 0.30,
    topk: int = 1
) -> list[str]:
    from sigma_partial import sigma_partial

    # --------- MODO EXATO ---------
    if tol is None:
        try:
            code_o_src = sigma_partial(word, src, "B")
        except Exception:
            return []
        v_src = _parse_triplet(code_o_src)
        cur = conn.cursor()
        cur.execute("SELECT lemma, marks FROM gama WHERE lang=?", (tgt,))
        out = []
        for lemma, marks in cur.fetchall():
            try:
                m = json.loads(marks) if marks else {}
            except Exception:
                m = {}
            v_tgt = _parse_triplet(m.get("codeO", ""))
            if _l1(v_src, v_tgt) <= 1e-12:
                out.append(lemma)
        return out[:1] if out else []
    # --------- FIM MODO EXATO ---------

    # origem
    try:
        code_o_src = sigma_partial(word, src, "B")
    except Exception:
        return []
    v_src = _parse_triplet(code_o_src)

    mu = _lang_means(conn) if norm == "lang" else {}
    mu_src = mu.get(src, [0.0, 0.0, 0.0])
    mu_tgt = mu.get(tgt, [0.0, 0.0, 0.0])

    v_src_n = _sub(v_src, mu_src) if norm == "lang" else v_src
    s_src = _scalar_weighted(v_src_n)
    e_src, val_src = _semantic_aux(word, src)

    cur = conn.cursor()
    cur.execute("SELECT lemma, marks FROM gama WHERE lang=?", (tgt,))
    scored: List[tuple[float, str]] = []
    for lemma, marks in cur.fetchall():
        try:
            m = json.loads(marks) if marks else {}
        except Exception:
            m = {}
        v_tgt = _parse_triplet(m.get("codeO", ""))
        v_tgt_n = _sub(v_tgt, mu_tgt) if norm == "lang" else v_tgt

        # gates
        if abs(v_src_n[0] - v_tgt_n[0]) > tau_c0:  # c0 (norm)
            continue
        if abs(v_src[1] - v_tgt[1]) > tau_c1:      # c1 (raw)
            continue
        if abs(v_src[2] - v_tgt[2]) > tau_c2:      # c2 (raw)
            continue

        s_tgt = _scalar_weighted(v_tgt_n)
        d_scalar = abs(s_src - s_tgt)
        if d_scalar > tau_scalar:
            continue

        e_tgt, val_tgt = _semantic_aux(lemma, tgt)
        aux_penalty = w_aux * (abs(e_src - e_tgt) + abs(val_src - val_tgt))
        score = d_scalar + aux_penalty
        scored.append((score, lemma))

    scored.sort(key=lambda x: x[0])
    return [lem for _, lem in scored[:max(1, topk)]]


def _cli() -> None:
    """CLI opcional para comparar a busca híbrida com a implementação legado."""
    # Windows pode iniciar Python com cp1252; resultados do TNU contêm acentos
    # e o separador ↔, portanto a CLI precisa declarar UTF-8 explicitamente.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Busca parcial/híbrida do TNU")
    parser.add_argument("--hybrid", action="store_true", help="ativa a Camada D")
    parser.add_argument("--query", required=True, help="palavra de consulta")
    parser.add_argument("--lang", required=True, help="idioma de consulta")
    parser.add_argument("--target", required=True, help="idioma alvo")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--db", default="gama.db")
    parser.add_argument("--ontology", default="ontology_concepts.json")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db)
    try:
        if args.hybrid:
            from ontology import load_ontology
            rows = hybrid_search(conn, args.lang, args.query, args.target,
                                 DEFAULT_HYBRID_WEIGHTS, load_ontology(args.ontology), args.top_k)
            for row in rows:
                print(f"{row['lang']}:{row['lemma']} score={row['score']:.6f} "
                      f"D={row['distance']['D']:.3f} relation={row['relation']}")
        else:
            print(" ↔ ".join(translate_partial(conn, args.query, args.lang, args.target, topk=args.top_k)) or "(vazio)")
    finally:
        conn.close()


if __name__ == "__main__":
    _cli()
