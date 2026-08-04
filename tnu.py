#!/usr/bin/env python3
"""
TNU 0.5 — determinismo total, code-O no banco e gauge da régua semântica
- Pipeline canônico (texto/float)
- Hash estável (blake2b/sha256) do payload JSON determinístico
- Armazena code-O (parte B) no campo marks (JSON)
- Subcomando `gauge` para gerar CSV da régua por conceito
- Subcomando `transp` para tradução por ressonância (code-O) com tolerância
"""

import sqlite3, json, hashlib, argparse, csv, sys
from pathlib import Path

# --- módulos do projeto ---
from ipa_fixed import ipa_fixed                # IPA determinístico
from emotion import valence                    # valência emocional ∈ [0,1]
from etym import etym_score                    # peso etimológico ∈ [0,1]
from sigma_partial import sigma_partial        # extrai parte B (code-O)

# --- utilidades de determinismo ---
try:
    from tnu_determinism import (
        canonical_text, quantize_seq, stable_json, stable_hash, make_sigma_payload
    )
except Exception:
    import unicodedata
    from decimal import Decimal, ROUND_HALF_UP
    def canonical_text(s: str) -> str:
        s = unicodedata.normalize("NFC", s or "")
        s = s.casefold().strip()
        return " ".join(s.split())
    def quantize_float(x: float, ndigits: int = 6) -> float:
        return float(Decimal(x).quantize(Decimal(f"1e-{ndigits}"), rounding=ROUND_HALF_UP))
    def quantize_seq(xs, ndigits: int = 6):
        return [quantize_float(float(x), ndigits) for x in xs]
    def stable_json(obj) -> str:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    def stable_hash(payload: str, digest_bytes: int = 16) -> str:
        return hashlib.blake2b(payload.encode("utf-8"), digest_size=digest_bytes).hexdigest()
    def make_sigma_payload(word, lang, ipa_seq, sigma_vector, meta=None):
        return stable_json({
            "w": canonical_text(word),
            "lang": canonical_text(lang),
            "ipa": ipa_seq,
            "sigma": quantize_seq(sigma_vector),
            "meta": meta or {}
        })

DB_FILE = "gama.db"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _fmt_triplet(trip) -> str:
    try:
        a, b, c = trip
        return f"{float(a):.3f}–{float(b):.3f}–{float(c):.3f}"
    except Exception:
        # normaliza strings "0.7-0.6-0.5" também
        try:
            parts = [float(x) for x in str(trip).replace("–", "-").split("-")[:3]]
            while len(parts) < 3:
                parts.append(0.0)
            return f"{parts[0]:.3f}–{parts[1]:.3f}–{parts[2]:.3f}"
        except Exception:
            return str(trip)

# ---------------------------------------------------------------------------
# 1) ALFA — vetor numérico determinístico (não use builtin hash())
# ---------------------------------------------------------------------------
def _stable_bucket_01(word: str, lang: str) -> float:
    """número estável em [0,1) derivado de (lang:word) para substituir hash() builtin"""
    key = f"{canonical_text(lang)}:{canonical_text(word)}".encode("utf-8")
    h = hashlib.blake2b(key, digest_size=8).digest()  # 64 bits
    num = int.from_bytes(h, "big") / float(1 << 64)
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(num).quantize(Decimal("1e-6"), rounding=ROUND_HALF_UP))

def alfa_vector(word: str, lang: str) -> tuple[list[float], list[str]]:
    """retorna vetor quantizado e sequência IPA (para o payload)"""
    ipa_seq = ipa_fixed(word, lang)  # determinístico
    ipastr = "".join(ipa_seq) if isinstance(ipa_seq, (list, tuple)) else str(ipa_seq)

    # features (estáveis)
    e1 = sum(ord(ch) for ch in ipastr) / 1000.0
    e2 = sum((ord(ch.lower()) - 97) / 26 for ch in word if ch.isalpha()) / max(1, len(word))
    e3 = max(1, ipastr.count(".") + 1) / 10.0
    e4 = -0.01
    e5 = float(etym_score(word, lang) or 0.0)
    e6 = float(valence(canonical_text(word)) or 0.0)
    e7 = _stable_bucket_01(word, lang)

    vec = [e1, e2, e3, e4, e5, e6, e7]
    vec = quantize_seq(vec, ndigits=6)
    return vec, list(ipa_seq) if isinstance(ipa_seq, (list, tuple)) else [ipastr]

# ---------------------------------------------------------------------------
# 2) SIGMA — hash estável do payload canônico
# ---------------------------------------------------------------------------
def sigma_code(word: str, lang: str) -> tuple[str, list[float], list[str]]:
    """Gera o σ (hexa) e retorna também o vetor e a IPA"""
    vec, ipa_seq = alfa_vector(word, lang)
    payload = make_sigma_payload(word, lang, ipa_seq, vec, meta={"ver": "0.5"})
    scode = stable_hash(payload, digest_bytes=16)  # 128 bits (32 hex)
    return scode, vec, ipa_seq

# ---------------------------------------------------------------------------
# 3) BANCO GAMA
# ---------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS gama (
        scode TEXT,
        lang  TEXT,
        lemma TEXT,
        freq  REAL,
        conf  REAL,
        marks TEXT,
        PRIMARY KEY(scode, lang, lemma)
    ) WITHOUT ROWID;
    """)
    conn.commit()
    return conn

def upsert(conn, scode: str, lang: str, lemma: str,
           freq: float = 0.001, conf: float = 0.95, marks=None):
    """Insere/atualiza no banco. Aceita marks como dict (vira JSON) ou string JSON."""
    if isinstance(marks, dict):
        marks_str = json.dumps(marks, ensure_ascii=False, separators=(",", ":"))
    elif isinstance(marks, str):
        marks_str = marks
    else:
        marks_str = "{}"

    conn.execute(
        "INSERT OR REPLACE INTO gama(scode,lang,lemma,freq,conf,marks) VALUES(?,?,?,?,?,?)",
        (scode, lang, lemma, freq, conf, marks_str),
    )
    conn.commit()

def word_to_sigma(conn, word: str, lang: str) -> str:
    sc, _, _ = sigma_code(word, lang)
    return sc

def sigma_to_words(conn, scode: str):
    cur = conn.cursor()
    cur.execute("SELECT lang,lemma,conf,marks FROM gama WHERE scode=? ORDER BY conf DESC", (scode,))
    return cur.fetchall()

# ---------------------------------------------------------------------------
# 4) TRADUÇÃO / UTILITÁRIOS
# ---------------------------------------------------------------------------
def translate(conn, word: str, src: str, tgt: str) -> list[str]:
    # 1) tenta sigma NOVO (payload canônico)
    sc_new, _, _ = sigma_code(word, src)
    cur = conn.cursor()
    cur.execute(
        "SELECT lemma, conf FROM gama WHERE scode=? AND lang=? ORDER BY conf DESC",
        (sc_new, tgt),
    )
    hits = cur.fetchall()

    # 2) fallback: sigma LEGADO (string do vetor "v1-v2-...")
    if not hits:
        legacy_vec = alfa(word, src)      # shim compat
        sc_legacy = sigma(legacy_vec)     # shim compat
        cur.execute(
            "SELECT lemma, conf FROM gama WHERE scode=? AND lang=? ORDER BY conf DESC",
            (sc_legacy, tgt),
        )
        hits = cur.fetchall()

    return [h[0] for h in hits]

# ---------------------------------------------------------------------------
# 5) CLI
# ---------------------------------------------------------------------------
def cli():
    # A CLI pode emitir acentos e símbolos; força UTF-8 em consoles Windows.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="TNU 0.5 — determinístico")
    parser.add_argument("action", choices=[
        "add", "trans", "sigma", "rev",
        "export", "import", "gauge", "transp"
    ])
    parser.add_argument("--word", "-w")
    parser.add_argument("--src", "-s", help="idioma origem")
    parser.add_argument("--tgt", "-t", help="idioma destino")
    parser.add_argument("--scode", "-c", help="sigma code (hex)")

    # transp thresholds
    parser.add_argument("--tol", type=float, default=0.005,
                        help="tolerância leve por componente (default: 0.005)")
    parser.add_argument("--tau-s", type=float, dest="tau_s", default=0.045,
                        help="limiar do escalar (distância triplo) (default: 0.045)")
    parser.add_argument("--tau-c0", type=float, dest="tau_c0", default=0.18,
                        help="limiar do 1º componente (default: 0.18)")
    parser.add_argument("--tau-c1", type=float, dest="tau_c1", default=0.15,
                        help="limiar do 2º componente (default: 0.15)")
    parser.add_argument("--tau-c2", type=float, dest="tau_c2", default=0.20,
                        help="limiar do 3º componente (default: 0.20)")
    parser.add_argument("--debug", action="store_true",
                        help="mostra vizinhos e distâncias no transp")

    # gauge
    parser.add_argument("--inp", help="CSV de entrada (concept,lang,word)")
    parser.add_argument("--out", help="CSV de saída (gauge)")
    args = parser.parse_args()

    conn = init_db()

    if args.action == "add":
        if not (args.word and args.src):
            raise SystemExit("Uso: tnu.py add -w palavra -s pt")
        sc, vec, ipa_seq = sigma_code(args.word, args.src)
        try:
            code_o_raw = sigma_partial(args.word, args.src, "B")
            parts = [float(x) for x in str(code_o_raw).replace("–", "-").split("-")[:3]]
            while len(parts) < 3:
                parts.append(0.0)
            code_o = _fmt_triplet(parts)
        except Exception:
            code_o = None
        marks = {"ipa": ipa_seq, "vec": vec, "codeO": code_o}
        upsert(conn, sc, args.src, args.word, marks=marks)
        print(f"{args.word} ({args.src}) → σ={sc}  code-O={code_o}")

    elif args.action == "trans":
        if not (args.word and args.src and args.tgt):
            raise SystemExit("Uso: tnu.py trans -w vida -s pt -t en")
        res = translate(conn, args.word, args.src, args.tgt)
        print(" ↔ ".join(res) if res else "(vazio)")

    elif args.action == "sigma":
        if not (args.word and args.src):
            raise SystemExit("Uso: tnu.py sigma -w life -s en")
        print(word_to_sigma(conn, args.word, args.src))

    elif args.action == "rev":
        if not args.scode:
            raise SystemExit("Uso: tnu.py rev -c 4f38a2c1...")
        rows = sigma_to_words(conn, args.scode)
        if not rows:
            print("(vazio)")
        else:
            for row in rows:
                if len(row) == 4:
                    lang, lemma, conf, marks = row
                else:
                    lang, lemma, conf = row
                    marks = ""
                print(f"{lang}: {lemma}  (conf={float(conf):.2f})")

    elif args.action == "export":
        rows = conn.execute("SELECT scode,lang,lemma,freq,conf,marks FROM gama").fetchall()
        data = []
        for scode, lang, lemma, freq, conf, marks in rows:
            try:
                marks_obj = json.loads(marks) if marks else {}
            except Exception:
                marks_obj = {"_raw": marks}
            data.append({
                "scode": scode, "lang": lang, "lemma": lemma,
                "freq": float(freq), "conf": float(conf), "marks": marks_obj
            })
        Path("gama_export.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("Exportado → gama_export.json")

    elif args.action == "import":
        data = json.loads(Path("gama_export.json").read_text(encoding="utf-8"))
        for r in data:
            upsert(conn, r["scode"], r["lang"], r["lemma"],
                   r.get("freq", 0.001), r.get("conf", 0.95), r.get("marks", {}))
        print("Importado ← gama_export.json")

    elif args.action == "gauge":
        """
        Gera a régua por conceito.
        Entrada (CSV): concept,lang,word
        Saída (CSV):   concept,lang,word,codeO
        """
        if not (args.inp and args.out):
            raise SystemExit("Uso: tnu.py gauge --inp data.csv --out gauge.csv")

        rows_out = []
        # leitor robusto: ignora BOM, comentários (#) e linhas vazias
        with open(args.inp, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row:
                    continue
                concept = (row.get("concept") or "").strip()
                lang    = (row.get("lang")    or "").strip()
                word    = (row.get("word")    or "").strip()
                if (not concept) or (not lang) or (not word):
                    continue
                if concept.startswith("#") or lang.startswith("#") or word.startswith("#"):
                    continue

                try:
                    code_o_raw = sigma_partial(word, lang, "B")
                    parts = [float(x) for x in str(code_o_raw).replace("–", "-").split("-")[:3]]
                    while len(parts) < 3:
                        parts.append(0.0)
                    code_o = _fmt_triplet(parts)
                except Exception:
                    _, vec, _ = sigma_code(word, lang)
                    code_o = _fmt_triplet(vec[:3])

                rows_out.append({
                    "concept": concept, "lang": lang, "word": word, "codeO": code_o
                })

        rows_out.sort(key=lambda r: (r["concept"], str(r["codeO"])))
        with open(args.out, "w", newline="", encoding="utf-8") as g:
            w = csv.DictWriter(g, fieldnames=["concept", "lang", "word", "codeO"])
            w.writeheader()
            w.writerows(rows_out)
        print(f"Gauge salvo em {args.out}")

    elif args.action == "transp":
        # Tradução por ressonância (code-O)
        if not (args.word and args.src and args.tgt):
            raise SystemExit("Uso: tnu.py transp -w casa -s pt -t fr [--tol 0.005] [--tau-s 0.045] "
                             "[--tau-c0 0.18] [--tau-c1 0.15] [--tau-c2 0.20] [--debug]")
        from translate_partial import translate_partial, _distance_triplet

        out = translate_partial(
            conn, args.word, args.src, args.tgt,
            tol=float(args.tol),
            tau_scalar=float(args.tau_s),
            tau_c0=float(args.tau_c0),
            tau_c1=float(args.tau_c1),
            tau_c2=float(args.tau_c2),
        )
        print(" ↔ ".join(out) if out else "(vazio)")

        if args.debug:
            # ranking de vizinhos no alvo
            try:
                src_trip = [float(x) for x in str(sigma_partial(args.word, args.src, "B")).replace("–", "-").split("-")[:3]]
                while len(src_trip) < 3:
                    src_trip.append(0.0)
            except Exception:
                src_trip = [0.0, 0.0, 0.0]

            cur = conn.cursor()
            cur.execute("SELECT lang,lemma,conf,marks FROM gama WHERE lang=?", (args.tgt,))
            rows = cur.fetchall()
            cand = []
            for lang, lemma, conf, marks in rows:
                try:
                    md = json.loads(marks) if marks else {}
                    b = md.get("codeO")
                    b_trip = [float(x) for x in str(b).replace("–","-").split("-")[:3]]
                    while len(b_trip) < 3:
                        b_trip.append(0.0)
                    d = _distance_triplet(tuple(src_trip), tuple(b_trip))
                    cand.append((lemma, d, _fmt_triplet(b_trip)))
                except Exception:
                    continue
            cand.sort(key=lambda x: x[1])
            if cand:
                print("\n[debug] vizinhos-alvo mais próximos:")
                for lemma, d, b in cand[:10]:
                    print(f"  {lemma:>18s}  d={d:.4f}  codeO={b}")

    else:
        raise SystemExit("Ação inválida")

# -----------------------------------------------------------
# SHIMS DE COMPATIBILIDADE COM test_tnu.py (legado)
# -----------------------------------------------------------
def alfa(word: str, lang: str) -> str:
    """Compat: retorna string do vetor com '-' (como versão antiga)."""
    vec, _ = alfa_vector(word, lang)
    return "-".join(f"{v:.3f}" for v in vec)

def sigma(vector: str) -> str:
    """Compat: recebe 'v1-v2-v3...' e devolve hash blake2b/128 bits."""
    return hashlib.blake2b(vector.encode("utf-8"), digest_size=16).hexdigest()

if __name__ == "__main__":
    cli()
