#!/usr/bin/env python3
"""Importa a fonte JSON da Camada D para o banco SQLite do TNU."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from ontology import load_ontology


def create_ontology_schema(conn: sqlite3.Connection) -> None:
    """Cria tabelas D e metadados sem alterar o comportamento legado."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ontology_sense (
            sense_id TEXT PRIMARY KEY,
            vector_json TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            relations_json TEXT NOT NULL,
            source TEXT NOT NULL,
            revision TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS lexeme_sense (
            lang TEXT NOT NULL,
            lemma TEXT NOT NULL,
            sense_id TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 1.0,
            PRIMARY KEY (lang, lemma, sense_id),
            FOREIGN KEY (sense_id) REFERENCES ontology_sense(sense_id)
        );
        CREATE TABLE IF NOT EXISTS ontology_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )

    # A coluna é pedida para facilitar auditoria das linhas existentes. SQLite
    # não possui ADD COLUMN IF NOT EXISTS, portanto consultamos antes.
    columns = {row[1] for row in conn.execute("PRAGMA table_info(gama)")}
    if columns and "ontology_version" not in columns:
        conn.execute("ALTER TABLE gama ADD COLUMN ontology_version TEXT")


def import_ontology(conn: sqlite3.Connection, ontology: dict, source: str = "ontology_concepts.json") -> None:
    """Faz UPSERT de sentidos, léxicos e versão em uma única transação."""
    create_ontology_schema(conn)
    revision = ontology["revision"]
    source = str(source)
    with conn:
        for sense_id, sense in ontology["senses"].items():
            conn.execute(
                """
                INSERT INTO ontology_sense(sense_id, vector_json, tags_json, relations_json, source, revision)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(sense_id) DO UPDATE SET
                    vector_json=excluded.vector_json, tags_json=excluded.tags_json,
                    relations_json=excluded.relations_json, source=excluded.source,
                    revision=excluded.revision
                """,
                (
                    sense_id,
                    json.dumps(sense["vector"], ensure_ascii=False, sort_keys=True),
                    json.dumps(sense["tags"], ensure_ascii=False),
                    json.dumps(sense["relations"], ensure_ascii=False, sort_keys=True),
                    source,
                    revision,
                ),
            )
        for key, sense_ids in ontology["lexemes"].items():
            lang, lemma = key.split(":", 1)
            for sense_id in sense_ids:
                conn.execute(
                    """
                    INSERT INTO lexeme_sense(lang, lemma, sense_id, confidence)
                    VALUES(?, ?, ?, 1.0)
                    ON CONFLICT(lang, lemma, sense_id) DO UPDATE SET confidence=excluded.confidence
                    """,
                    (lang, lemma, sense_id),
                )
        conn.execute(
            "INSERT INTO ontology_metadata(key, value) VALUES('ontology_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (revision,),
        )
        if {row[1] for row in conn.execute("PRAGMA table_info(gama)")}:
            conn.execute("UPDATE gama SET ontology_version=?", (revision,))


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa a Camada D no SQLite do TNU.")
    parser.add_argument("--file", default="ontology_concepts.json", help="arquivo JSON da ontologia")
    parser.add_argument("--db", default="gama.db", help="arquivo SQLite alvo")
    args = parser.parse_args()
    ontology = load_ontology(args.file)
    conn = sqlite3.connect(args.db)
    try:
        import_ontology(conn, ontology, Path(args.file).name)
    finally:
        conn.close()
    print(f"Ontologia {ontology['revision']} importada em {args.db}.")


if __name__ == "__main__":
    main()
