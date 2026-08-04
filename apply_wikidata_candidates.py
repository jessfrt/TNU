#!/usr/bin/env python3
"""Aplica somente candidatos Wikidata aceitos ao ontology_concepts.json."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main() -> None:
    parser = argparse.ArgumentParser(description="Aplica candidatos multilíngues aceitos")
    parser.add_argument("--ontology", default="ontology_concepts.json")
    parser.add_argument("--candidates", default="wikidata_candidates.json")
    parser.add_argument("--apply", action="store_true", help="necessário para alterar o JSON")
    args = parser.parse_args()
    ontology_path, candidate_path = ROOT / args.ontology, ROOT / args.candidates
    ontology = json.loads(ontology_path.read_text(encoding="utf-8"))
    data = json.loads(candidate_path.read_text(encoding="utf-8"))
    accepted = [row for row in data["candidates"] if row["status"] == "accepted"]
    if not args.apply:
        print(f"Simulação: {len(accepted)} candidatos aceitos seriam aplicados. Use --apply.")
        return
    added = 0
    for row in accepted:
        sense = ontology["senses"].get(row["sense_id"])
        if not sense:
            continue
        sense["wikidata_qid"] = row["qid"]
        sense["translation_source"] = "Wikidata"
        sense["translation_confidence"] = row["confidence"]
        for lang, label in row["labels"].items():
            if lang == "pt" or not label:
                continue
            key = f"{lang}:{label.casefold()}"
            ids = ontology["lexemes"].setdefault(key, [])
            if row["sense_id"] not in ids:
                ids.append(row["sense_id"]); added += 1
    ontology["revision"] = f"{ontology.get('revision', 'ontology')}-wikidata"
    ontology_path.write_text(json.dumps(ontology, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Aplicados {len(accepted)} sentidos e {added} lexemes; revisão={ontology['revision']}")

if __name__ == "__main__":
    main()
