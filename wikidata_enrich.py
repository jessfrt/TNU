#!/usr/bin/env python3
"""Gera candidatos multilíngues auditáveis a partir da API pública Wikidata.

Não altera a ontologia. Os resultados ficam em JSON com QID, descrições,
confiança e motivo da decisão. Use ``apply_wikidata_candidates.py`` somente
para os itens aceitos após a revisão do relatório.
"""
from __future__ import annotations

import argparse
import json
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
LANGS = ("en", "es", "fr", "de", "it")
API = "https://www.wikidata.org/w/api.php"
HEADERS = {"User-Agent": "TNU-Ontology-Enricher/1.0 (academic-project; contact=local)"}


def norm(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text or "").casefold().split())


def fetch(params: dict) -> dict:
    url = f"{API}?{urlencode({**params, 'format': 'json', 'origin': '*'})}"
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1.2 * (attempt + 1))
    raise RuntimeError("unreachable")


def representative_lexemes(ontology: dict) -> dict[str, str]:
    result = {}
    for key, sense_ids in ontology["lexemes"].items():
        if not key.startswith("pt:"):
            continue
        word = key.split(":", 1)[1]
        for sense_id in sense_ids:
            result.setdefault(sense_id, word)
    return result


def candidate(sense_id: str, word: str, sense: dict) -> dict:
    base = {"sense_id": sense_id, "pt": word, "domain": sense.get("domain"), "status": "review", "qid": None,
            "labels": {}, "descriptions": {}, "confidence": 0.0, "reason": ""}
    try:
        search = fetch({"action": "wbsearchentities", "search": word, "language": "pt", "uselang": "pt", "type": "item", "limit": 10})
        exact = [row for row in search.get("search", []) if norm(row.get("label", "")) == norm(word)]
        if len(exact) != 1:
            base["reason"] = "no_exact_unique_wikidata_item"
            return base
        qid = exact[0]["id"]
        entity = fetch({"action": "wbgetentities", "ids": qid, "props": "labels|descriptions", "languages": "pt|en|es|fr|de|it"})
        item = entity.get("entities", {}).get(qid, {})
        labels = {lang: item.get("labels", {}).get(lang, {}).get("value") for lang in ("pt", *LANGS)}
        descriptions = {lang: item.get("descriptions", {}).get(lang, {}).get("value") for lang in ("pt", "en")}
        base.update({"qid": qid, "labels": labels, "descriptions": descriptions})
        missing = [lang for lang in LANGS if not labels.get(lang)]
        if missing:
            base["reason"] = f"missing_labels:{','.join(missing)}"
            return base
        # Regra conservadora: rótulo PT exato, único item e cinco rótulos disponíveis.
        base.update({"status": "accepted", "confidence": 0.95, "reason": "exact_unique_pt_label_with_all_target_labels"})
        return base
    except Exception as exc:
        base["status"] = "error"
        base["reason"] = f"request_error:{type(exc).__name__}"
        return base


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta candidatos multilíngues do Wikidata")
    parser.add_argument("--file", default="ontology_concepts.json")
    parser.add_argument("--out", default="wikidata_candidates.json")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0, help="limita sentidos; 0 = todos")
    args = parser.parse_args()
    ontology = json.loads((ROOT / args.file).read_text(encoding="utf-8"))
    representatives = representative_lexemes(ontology)
    jobs = [(sid, word, ontology["senses"][sid]) for sid, word in representatives.items()
            if not all(any(sid in ids for key, ids in ontology["lexemes"].items() if key.startswith(f"{lang}:")) for lang in LANGS)]
    if args.limit:
        jobs = jobs[:args.limit]
    candidates = []
    with ThreadPoolExecutor(max_workers=max(1, min(8, args.workers))) as executor:
        futures = [executor.submit(candidate, *job) for job in jobs]
        for index, future in enumerate(as_completed(futures), 1):
            candidates.append(future.result())
            if index % 25 == 0 or index == len(jobs):
                print(f"Consultados {index}/{len(jobs)}")
    candidates.sort(key=lambda row: row["sense_id"])
    result = {"source": "Wikidata Action API", "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "ontology_revision": ontology.get("revision"), "languages": list(LANGS), "candidates": candidates}
    (ROOT / args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    counts = {state: sum(row["status"] == state for row in candidates) for state in ("accepted", "review", "error")}
    print(f"Arquivo salvo: {args.out}; {counts}")


if __name__ == "__main__":
    main()
