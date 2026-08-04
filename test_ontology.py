import json
import sqlite3
from pathlib import Path

import pytest

from import_ontology import import_ontology
from ontology import load_ontology, ontology_distance, relation_type, senses_for
from sigma_partial import sigma_partial
from translate_partial import hybrid_search


ONTOLOGY_FILE = Path(__file__).with_name("ontology_concepts.json")


def test_load_and_validate_schema(tmp_path):
    ontology = load_ontology(ONTOLOGY_FILE)
    assert ontology["revision"] == "industrial-seed-pt-v1"
    assert "WATER.SUBSTANCE" in ontology["senses"]
    assert {"FOOD.MEAL", "LOVE.ROMANTIC", "HOUSE.DWELLING", "EMOTION.JOY", "BODY.HEART", "LIGHT.LUMINOSITY", "VEHICLE.CAR", "EMOTION.HAPPINESS"} <= set(ontology["senses"])

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"schema_version": 1, "revision": "x", "senses": {}, "lexemes": {"pt:x": ["NOPE"]}}))
    with pytest.raises(ValueError, match="inexistentes"):
        load_ontology(bad)


def test_senses_and_distance():
    ontology = load_ontology(ONTOLOGY_FILE)
    assert senses_for("PT", " ÁGUA ", ontology) == ["WATER.SUBSTANCE"]
    assert senses_for("en", "unknown", ontology) == []
    assert ontology_distance("pt", "água", "en", "water", ontology) == 0.0
    assert ontology_distance("pt", "água", "en", "sea", ontology) > 0.10
    assert ontology_distance("pt", "água", "en", "life", ontology) > 0.70
    assert relation_type("WATER.SUBSTANCE", "WATER.SEA", ontology) == "related"
    assert relation_type("WATER.STREAM", "WATER.RIVER", ontology) == "narrower"
    assert relation_type("EMOTION.JOY", "EMOTION.SADNESS", ontology) == "opposite"


def test_sqlite_import_and_hybrid_search():
    ontology = load_ontology(ONTOLOGY_FILE)
    conn = sqlite3.connect(":memory:")
    conn.execute("""CREATE TABLE gama (
        scode TEXT, lang TEXT, lemma TEXT, freq REAL, conf REAL, marks TEXT,
        PRIMARY KEY(scode, lang, lemma))""")
    import_ontology(conn, ontology, "test.json")
    assert conn.execute("SELECT count(*) FROM ontology_sense").fetchone()[0] >= 393
    assert conn.execute("SELECT count(*) FROM lexeme_sense").fetchone()[0] >= 751
    assert conn.execute("SELECT value FROM ontology_metadata WHERE key='ontology_version'").fetchone()[0] == "industrial-seed-pt-v1"

    source_code = sigma_partial("água", "pt", "B")
    # B é deliberadamente igual: o teste prova que D separa water de sea.
    for lemma in ("water", "sea"):
        conn.execute(
            "INSERT INTO gama(scode, lang, lemma, freq, conf, marks) VALUES(?, 'en', ?, 0.001, 0.95, ?)",
            (f"test-{lemma}", lemma, json.dumps({"codeO": source_code})),
        )
    conn.commit()
    rows = hybrid_search(conn, "pt", "água", "en", None, ontology, top_k=2)
    assert [row["lemma"] for row in rows] == ["water", "sea"]
    assert rows[0]["score"] < rows[1]["score"]
    assert rows[0]["relation"] == "same"
    assert rows[1]["relation"] == "related"
