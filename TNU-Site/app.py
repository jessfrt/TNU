"""Servidor web do Tradutor Numérico Universal (TNU)."""

from __future__ import annotations

import csv
import io
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

SITE_ROOT = Path(__file__).resolve().parent
TNU_ROOT = SITE_ROOT.parent
DB_PATH = TNU_ROOT / "gama.db"
ONTOLOGY_PATH = TNU_ROOT / "ontology_concepts.json"
sys.path.insert(0, str(TNU_ROOT))

from import_ontology import create_ontology_schema, import_ontology
from ontology import load_ontology
from translate_partial import hybrid_search, translate_partial

app = Flask(__name__)
CORS(app)
_ontology_cache: dict | None = None
_ontology_mtime: int | None = None
LANGUAGES = {"pt", "en", "es", "fr", "de", "it"}


def db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ontology_data() -> dict:
    """Carrega a ontologia somente quando o arquivo-fonte for modificado."""
    global _ontology_cache, _ontology_mtime
    mtime = ONTOLOGY_PATH.stat().st_mtime_ns
    if _ontology_cache is None or _ontology_mtime != mtime:
        _ontology_cache = load_ontology(ONTOLOGY_PATH)
        _ontology_mtime = mtime
    return _ontology_cache


def json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def search_payload() -> tuple[str, str, str, int] | tuple[None, None, None, None]:
    body = request.get_json(silent=True) or {}
    query = str(body.get("query", "")).strip()
    source = str(body.get("lang_from", "pt")).lower().strip()
    target = str(body.get("lang_to", "en")).lower().strip()
    try:
        top_k = max(1, min(10, int(body.get("top_k", 5))))
    except (TypeError, ValueError):
        top_k = 5
    if not query:
        return None, None, None, None
    if source not in LANGUAGES or target not in LANGUAGES:
        return None, None, None, None
    return query, source, target, top_k


def ensure_progress_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS user_progress (
            user_key TEXT PRIMARY KEY,
            tutorial_complete INTEGER NOT NULL DEFAULT 0,
            theme TEXT,
            updated_at TEXT NOT NULL
        )"""
    )
    conn.commit()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/docs/<name>")
def docs(name: str):
    """Expõe somente a documentação pública armazenada no projeto TNU."""
    if name not in {"ONTOLOGIA.md", "RELATORIO_LIMPEZA.md", "RELATORIO_CAMADA_D.md"}:
        return json_error("Documento não encontrado.", 404)
    return send_from_directory(TNU_ROOT, name, mimetype="text/markdown")


@app.post("/api/search")
def api_search():
    query, source, target, top_k = search_payload()
    if query is None:
        return json_error("Informe uma palavra e idiomas válidos.")
    try:
        with db_connection() as conn:
            rows = hybrid_search(conn, source, query, target, None, ontology_data(), top_k)
        return jsonify({"ok": True, "query": query, "lang_from": source, "lang_to": target,
                        "mode": "hybrid", "results": rows})
    except Exception as exc:
        return json_error(f"Falha na busca híbrida: {exc}", 500)


@app.post("/api/search_legacy")
def api_search_legacy():
    query, source, target, top_k = search_payload()
    if query is None:
        return json_error("Informe uma palavra e idiomas válidos.")
    try:
        with db_connection() as conn:
            lemmas = translate_partial(conn, query, source, target, topk=top_k)
        results = [{"lemma": lemma, "lang": target, "score": None, "distance": {}, "relation": None}
                   for lemma in lemmas]
        return jsonify({"ok": True, "query": query, "lang_from": source, "lang_to": target,
                        "mode": "legacy", "results": results})
    except Exception as exc:
        return json_error(f"Falha na busca legada: {exc}", 500)


@app.get("/api/ontology")
def api_ontology():
    ontology = ontology_data()
    grouped: dict[str, list[str]] = {sense_id: [] for sense_id in ontology["senses"]}
    for lexeme, senses in ontology["lexemes"].items():
        for sense in senses:
            grouped.setdefault(sense, []).append(lexeme)
    senses = [{"sense_id": sense_id, **data, "lexemes": sorted(grouped.get(sense_id, []))}
              for sense_id, data in ontology["senses"].items()]
    return jsonify({"ok": True, "revision": ontology["revision"], "senses": senses})


@app.post("/api/ontology/import")
def api_ontology_import():
    try:
        data = load_ontology(ONTOLOGY_PATH)
        with db_connection() as conn:
            import_ontology(conn, data, ONTOLOGY_PATH.name)
        global _ontology_cache
        _ontology_cache = data
        return jsonify({"ok": True, "message": f"Ontologia {data['revision']} importada com sucesso."})
    except Exception as exc:
        return json_error(f"Falha ao importar ontologia: {exc}", 500)


@app.get("/api/stats")
def api_stats():
    try:
        ontology = ontology_data()
        with db_connection() as conn:
            create_ontology_schema(conn)
            total = conn.execute("SELECT COUNT(DISTINCT lang || ':' || lemma) FROM gama").fetchone()[0]
            by_lang = [dict(row) for row in conn.execute(
                "SELECT lang AS label, COUNT(DISTINCT lemma) AS value FROM gama GROUP BY lang ORDER BY lang")]
            by_sense = [dict(row) for row in conn.execute(
                "SELECT sense_id AS label, COUNT(*) AS value FROM lexeme_sense GROUP BY sense_id ORDER BY sense_id")]
        mapped = sum(row["value"] for row in by_sense)
        return jsonify({"ok": True, "total_words": total, "languages": len(by_lang),
                        "senses": len(ontology["senses"]), "average_words_per_sense": round(mapped / max(1, len(by_sense)), 2),
                        "by_language": by_lang, "by_sense": by_sense})
    except Exception as exc:
        return json_error(f"Falha ao calcular estatísticas: {exc}", 500)


@app.get("/api/ruler")
def api_ruler():
    concept = request.args.get("concept", "all").strip()
    path = TNU_ROOT / "out" / "gauge-verificado.csv"
    if not path.exists():
        path = TNU_ROOT / "out.csv"
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if concept != "all" and row.get("concept") != concept:
                continue
            try:
                code_o = str(row.get("codeO", "")).replace("–", "-").split("-")
                x = float(code_o[0])
            except (IndexError, ValueError):
                continue
            rows.append({"concept": row["concept"], "lang": row["lang"], "word": row["word"], "x": x})
    return jsonify({"ok": True, "concept": concept, "points": rows})


@app.post("/api/export")
def api_export():
    body = request.get_json(silent=True) or {}
    data = body.get("data", [])
    export_format = str(body.get("format", "json")).lower()
    metadata = {"exported_at": datetime.now(timezone.utc).isoformat(), "parameters": body.get("parameters", {}), "results": data}
    if export_format == "json":
        return Response(json.dumps(metadata, ensure_ascii=False, indent=2), mimetype="application/json",
                        headers={"Content-Disposition": "attachment; filename=tnu-resultados.json"})
    if export_format in {"csv", "markdown"}:
        if export_format == "csv":
            output = io.StringIO()
            fields = ["lemma", "lang", "score", "D_distance", "relation"]
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for item in data:
                writer.writerow({"lemma": item.get("lemma"), "lang": item.get("lang"), "score": item.get("score"),
                                 "D_distance": item.get("distance", {}).get("D"), "relation": item.get("relation")})
            return Response(output.getvalue(), mimetype="text/csv; charset=utf-8",
                            headers={"Content-Disposition": "attachment; filename=tnu-resultados.csv"})
        lines = ["# Resultados TNU", "", f"Data: {metadata['exported_at']}", "", "| Palavra | Idioma | Score | D | Relação |", "|---|---|---:|---:|---|"]
        lines += [f"| {x.get('lemma','')} | {x.get('lang','')} | {x.get('score','')} | {x.get('distance',{}).get('D','')} | {x.get('relation','')} |" for x in data]
        return Response("\n".join(lines), mimetype="text/markdown; charset=utf-8",
                        headers={"Content-Disposition": "attachment; filename=tnu-resultados.md"})
    return json_error("Formato suportado: csv, json ou markdown.")


@app.get("/api/tutorial/status")
def tutorial_status():
    user_key = request.args.get("user_key", "anonymous")
    with db_connection() as conn:
        ensure_progress_schema(conn)
        row = conn.execute("SELECT tutorial_complete, theme FROM user_progress WHERE user_key=?", (user_key,)).fetchone()
    return jsonify({"ok": True, "complete": bool(row and row["tutorial_complete"]), "theme": row["theme"] if row else None})


@app.post("/api/tutorial/complete")
def tutorial_complete():
    body = request.get_json(silent=True) or {}
    user_key = str(body.get("user_key", "anonymous"))[:100]
    complete = int(bool(body.get("complete", True)))
    theme = body.get("theme")
    with db_connection() as conn:
        ensure_progress_schema(conn)
        conn.execute("""INSERT INTO user_progress(user_key, tutorial_complete, theme, updated_at)
                        VALUES(?, ?, ?, ?)
                        ON CONFLICT(user_key) DO UPDATE SET tutorial_complete=excluded.tutorial_complete,
                        theme=COALESCE(excluded.theme, user_progress.theme), updated_at=excluded.updated_at""",
                     (user_key, complete, theme, datetime.now(timezone.utc).isoformat()))
        conn.commit()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
