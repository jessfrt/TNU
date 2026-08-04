"""Camada D: ontologia simbólica e determinística do TNU."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def _canonical(value: str) -> str:
    """Normaliza as chaves léxicas da mesma forma em todas as buscas."""
    return " ".join((value or "").casefold().strip().split())


def load_ontology(filepath: str | Path) -> dict[str, Any]:
    """Carrega e valida a estrutura mínima de uma ontologia em JSON.

    A validação é deliberadamente pequena: bloqueia arquivos malformados sem
    impedir que novas dimensões vetoriais sejam adicionadas no futuro.
    """
    path = Path(filepath)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("A ontologia deve ser um objeto JSON.")
    if not isinstance(data.get("schema_version"), int):
        raise ValueError("Campo obrigatório ausente ou inválido: schema_version.")
    if not isinstance(data.get("revision"), str):
        raise ValueError("Campo obrigatório ausente ou inválido: revision.")
    senses = data.get("senses")
    lexemes = data.get("lexemes")
    if not isinstance(senses, dict) or not isinstance(lexemes, dict):
        raise ValueError("Campos obrigatórios senses e lexemes devem ser objetos.")

    for sense_id, sense in senses.items():
        if not isinstance(sense_id, str) or not isinstance(sense, dict):
            raise ValueError("Cada sentido deve ter identificador e objeto válidos.")
        if not isinstance(sense.get("vector"), dict):
            raise ValueError(f"{sense_id}: vector deve ser um objeto.")
        if not isinstance(sense.get("tags"), list):
            raise ValueError(f"{sense_id}: tags deve ser uma lista.")
        if not isinstance(sense.get("relations"), dict):
            raise ValueError(f"{sense_id}: relations deve ser um objeto.")
        for key, value in sense["vector"].items():
            if not isinstance(key, str) or not isinstance(value, (int, float)):
                raise ValueError(f"{sense_id}: vector deve conter números por dimensão.")

    for lexeme, sense_ids in lexemes.items():
        if not isinstance(lexeme, str) or ":" not in lexeme:
            raise ValueError("Cada chave de lexemes deve ser 'idioma:lema'.")
        if not isinstance(sense_ids, list) or not all(isinstance(x, str) for x in sense_ids):
            raise ValueError(f"{lexeme}: sentidos devem ser uma lista de strings.")
        unknown = set(sense_ids) - set(senses)
        if unknown:
            raise ValueError(f"{lexeme}: sentidos inexistentes: {sorted(unknown)}")
    return data


def senses_for(lang: str, lemma: str, ontology: Mapping[str, Any]) -> list[str]:
    """Retorna os sentidos anotados para ``lang<lemma``; [] se não anotado."""
    key = f"{_canonical(lang)}:{_canonical(lemma)}"
    return list(ontology.get("lexemes", {}).get(key, []))


def weighted_jaccard(
    vec_a: Mapping[str, float], vec_b: Mapping[str, float], weights: Mapping[str, float] | None = None
) -> float:
    """Calcula distância Jaccard ponderada em vetores esparsos não negativos.

    O retorno está em [0, 1]: 0 é igualdade e 1 é nenhuma característica em
    comum. Dimensões ausentes equivalem a zero.
    """
    dimensions = set(vec_a) | set(vec_b)
    if not dimensions:
        return 0.0
    numerator = denominator = 0.0
    for dim in dimensions:
        weight = float((weights or {}).get(dim, 1.0))
        if weight < 0:
            raise ValueError("Pesos da ontologia não podem ser negativos.")
        a = max(0.0, float(vec_a.get(dim, 0.0)))
        b = max(0.0, float(vec_b.get(dim, 0.0)))
        numerator += weight * min(a, b)
        denominator += weight * max(a, b)
    return 0.0 if denominator == 0.0 else 1.0 - numerator / denominator


def ontology_distance(
    lang_a: str, word_a: str, lang_b: str, word_b: str, ontology: Mapping[str, Any]
) -> float | None:
    """Menor distância D entre todos os sentidos possíveis dos dois lemas."""
    senses_a = senses_for(lang_a, word_a, ontology)
    senses_b = senses_for(lang_b, word_b, ontology)
    if not senses_a or not senses_b:
        return None
    senses = ontology["senses"]
    weights = ontology.get("feature_weights", {})
    return min(
        weighted_jaccard(senses[a]["vector"], senses[b]["vector"], weights)
        for a in senses_a for b in senses_b
    )


def hybrid_score(
    a: Mapping[str, float], b: Mapping[str, float], weights: Mapping[str, float]
) -> float:
    """Combina distâncias/componentes A, B, C e D com pesos explícitos.

    Na integração atual ``a`` contém as distâncias calculadas e ``b`` é um
    vetor nulo. A forma geral também permite comparar dois vetores de
    projeções numéricas no futuro.
    """
    return sum(
        max(0.0, float(weights.get(component, 0.0)))
        * abs(float(a.get(component, 0.0)) - float(b.get(component, 0.0)))
        for component in ("D", "B", "A", "C")
    )


def relation_type(sense_a: str, sense_b: str, ontology: Mapping[str, Any]) -> str | None:
    """Classifica a relação explícita entre dois sentidos, quando houver."""
    if sense_a == sense_b and sense_a in ontology.get("senses", {}):
        return "same"
    senses = ontology.get("senses", {})
    a = senses.get(sense_a)
    b = senses.get(sense_b)
    if not a or not b:
        return None
    a_rel = a.get("relations", {})
    b_rel = b.get("relations", {})
    if sense_b in a_rel.get("broader", []):
        return "narrower"
    if sense_a in b_rel.get("broader", []):
        return "broader"
    if sense_b in a_rel.get("opposite", []) or sense_a in b_rel.get("opposite", []):
        return "opposite"
    if sense_b in a_rel.get("related", []) or sense_a in b_rel.get("related", []):
        return "related"
    return None
