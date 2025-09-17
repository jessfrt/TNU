#!/usr/bin/env python3
"""
TNU- 0.4 – IPA real, valência emocional, etimologia
MIT – github.com/seuuser/tnu-real
"""
import sqlite3, json, hashlib, os, argparse
from pathlib import Path
# nossos módulos novos
from ipa_provider import ipa
from emotion import valence
from etym import etym_score

# ---------- CONFIG ----------
DB_FILE = "gama.db"

# ---------- SIGMA (BLAKE3 se disponível) ----------
def sigma(vector: str) -> str:
    try:
        import blake3
        return blake3.blake3(vector.encode()).hexdigest()
    except ImportError:
        return hashlib.sha256(vector.encode()).hexdigest()

# ---------- ATOMIZADOR ALFA ----------
def alfa(word: str, lang: str) -> str:
    ipastr = ipa(word, lang)
    e1 = sum(ord(ch) for ch in ipastr) / 1000
    e2 = sum((ord(ch.lower()) - 97) / 26 for ch in word if ch.isalpha()) / max(1, len(word))
    e3 = max(1, ipastr.count(".") + 1) / 10
    e4 = -0.01  # placeholder bigrama
    e5 = etym_score(word, lang)
    e6 = valence(word.lower())
    e7 = hash(word) % 1000 / 1000
    vec = [round(x, 3) for x in [e1, e2, e3, e4, e5, e6, e7]]
    return "-".join(f"{v:.3f}" for v in vec)

# ---------- BANCO GAMA ----------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS gama (
        scode TEXT,
        lang TEXT,
        lemma TEXT,
        freq REAL,
        conf REAL,
        marks TEXT,
        PRIMARY KEY(scode, lang, lemma)
    ) WITHOUT ROWID;
    """)
    conn.commit()
    return conn

def upsert(conn, scode: str, lang: str, lemma: str, freq: float = 0.001, conf: float = 0.95, marks: str = ""):
    conn.execute("""INSERT OR REPLACE INTO gama(scode,lang,lemma,freq,conf,marks)
                    VALUES(?,?,?,?,?,?)""", (scode, lang, lemma, freq, conf, marks))
    conn.commit()

def lookup(conn, scode: str, lang=None):
    cur = conn.cursor()
    if lang:
        cur.execute("SELECT lemma,conf FROM gama WHERE scode=? AND lang=? ORDER BY conf DESC", (scode, lang))
    else:
        cur.execute("SELECT lang,lemma,conf FROM gama WHERE scode=? ORDER BY conf DESC", (scode,))
    return cur.fetchall()

# ---------- TRADUÇÃO ----------
def translate(conn, word: str, src: str, tgt: str) -> list[str]:
    vec = alfa(word, src)
    sc = sigma(vec)
    hits = lookup(conn, sc, tgt)
    return [h[0] for h in hits]

def word_to_sigma(conn, word: str, lang: str) -> str:
    return sigma(alfa(word, lang))

def sigma_to_words(conn, scode: str):
    return lookup(conn, scode)

# ---------- CLI ----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TNU-real 0.4")
    parser.add_argument("action", choices=["add", "trans", "sigma", "rev", "export", "import"])
    parser.add_argument("--word", "-w")
    parser.add_argument("--src", "-s", help="idioma origem")
    parser.add_argument("--tgt", "-t", help="idioma destino")
    parser.add_argument("--scode", "-c", help="sigma code (hex)")
    args = parser.parse_args()

    conn = init_db()

    if args.action == "add":
        if not (args.word and args.src):
            exit("Uso: tnu.py add -w palavra -s pt")
        vec = alfa(args.word, args.src)
        sc = sigma(vec)
        upsert(conn, sc, args.src, args.word)
        print(f"{args.word} ({args.src}) → σ={sc}")

    elif args.action == "trans":
        if not (args.word and args.src and args.tgt):
            exit("Uso: tnu.py trans -w vida -s pt -t en")
        res = translate(conn, args.word, args.src, args.tgt)
        print(" ↔ ".join(res) if res else "(vazio)")

    elif args.action == "sigma":
        if not (args.word and args.src):
            exit("Uso: tnu.py sigma -w life -s en")
        print(word_to_sigma(conn, args.word, args.src))

    elif args.action == "rev":
        if not args.scode:
            exit("Uso: tnu.py rev -c 4f38a2c1...")
        rows = sigma_to_words(conn, args.scode)
        for lang, lemma, conf in rows:
            print(f"{lang}: {lemma}  (conf={conf:.2f})")

    elif args.action == "export":
        rows = conn.execute("SELECT * FROM gama").fetchall()
        data = [{"scode": r[0], "lang": r[1], "lemma": r[2], "freq": r[3], "conf": r[4], "marks": r[5]} for r in rows]
        Path("gama_export.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print("Exportado → gama_export.json")

    elif args.action == "import":
        data = json.loads(Path("gama_export.json").read_text())
        for r in data:
            upsert(conn, r["scode"], r["lang"], r["lemma"], r["freq"], r["conf"], r["marks"])
        print("Importado ← gama_export.json")