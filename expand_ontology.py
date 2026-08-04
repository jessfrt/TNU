#!/usr/bin/env python3
"""Expande a ontologia TNU com um catálogo multilíngue de domínio aberto.

O catálogo é declarativo e o resultado é sempre o mesmo JSON ordenado. A
função não remove sentidos ou léxicos existentes; ela os complementa.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ONTOLOGY_FILE = ROOT / "ontology_concepts.json"

UNIVERSAL_WEIGHTS = {
    "entity": 2.0, "abstract": 2.0, "animate": 2.0, "inanimate": 1.5,
    "natural": 1.5, "artificial": 1.5, "physical": 2.0, "mental": 2.0,
    "social": 1.5, "biological": 2.0, "solid": 1.2, "liquid": 2.5,
    "gaseous": 1.2, "mass": 1.2, "countable": 1.2, "has_shape": 1.0,
    "has_color": 0.5, "has_texture": 0.5, "has_temperature": 0.8,
    "edible": 2.0, "drinkable": 2.0, "sheltering": 2.0, "transportable": 0.8,
    "storable": 0.8, "transformable": 0.8, "renewable": 0.8, "consumable": 1.0,
    "positive": 1.2, "negative": 1.2, "neutral": 0.5, "intense": 0.8,
    "mild": 0.5, "pleasant": 1.0, "unpleasant": 1.0, "process": 1.5,
    "record": 1.5, "state": 1.5, "water_body": 2.0, "atmospheric": 1.5,
}

PROFILES = {
    "water": {"entity": 1, "physical": 1, "natural": 1, "inanimate": 1, "liquid": 1, "mass": 1, "has_temperature": 1, "renewable": 1},
    "life": {"entity": 1, "abstract": 1, "biological": 1, "animate": 1, "state": 1, "natural": 1},
    "food": {"entity": 1, "physical": 1, "inanimate": 1, "edible": 1, "consumable": 1, "pleasant": 1, "positive": 1, "transformable": 1},
    "love": {"abstract": 1, "mental": 1, "social": 1, "positive": 1, "pleasant": 1, "intense": 1},
    "house": {"entity": 1, "physical": 1, "artificial": 1, "inanimate": 1, "solid": 1, "has_shape": 1, "sheltering": 1, "countable": 1},
    "shelter": {"abstract": 1, "social": 1, "positive": 1, "sheltering": 1, "pleasant": 1},
    "emotion": {"abstract": 1, "mental": 1, "social": 1, "intense": 1},
    "nature": {"entity": 1, "physical": 1, "natural": 1, "inanimate": 1, "has_shape": 1},
    "time": {"abstract": 1, "state": 1, "neutral": 1},
    "body": {"entity": 1, "physical": 1, "biological": 1, "animate": 1, "natural": 1, "countable": 1, "has_shape": 1},
    "light": {"entity": 1, "physical": 1, "natural": 1, "inanimate": 1, "gaseous": 1, "has_color": 1, "has_temperature": 1, "positive": 1},
    "vehicle": {"entity": 1, "physical": 1, "artificial": 1, "inanimate": 1, "solid": 1, "countable": 1, "has_shape": 1, "transportable": 1},
}


def entry(suffix, pt, en, fr, es, de, it, tags=(), overrides=None):
    return (suffix, (pt, en, fr, es, de, it), list(tags), overrides or {})


CATALOG = {
    "WATER": ("water", [
        entry("ICE", "gelo", "ice", "glace", "hielo", "eis", "ghiaccio", ("solid", "frozen"), {"solid": 1, "liquid": 0, "mass": 1}),
        entry("VAPOR", "vapor", "vapor", "vapeur", "vapor", "dampf", "vapore", ("gaseous", "water"), {"gaseous": 1, "liquid": 0, "mass": 1}),
        entry("OCEAN", "oceano", "ocean", "océan", "océano", "ozean", "oceano", ("water_body", "ocean"), {"water_body": 1}),
        entry("LAKE", "lago", "lake", "lac", "lago", "see", "lago", ("water_body", "lake"), {"water_body": 1}),
    ]),
    "LIFE": ("life", [
        entry("ORGANISM", "organismo", "organism", "organisme", "organismo", "organismus", "organismo", ("biology", "organism"), {"physical": 1, "abstract": 0}),
        entry("SPECIES", "espécie", "species", "espèce", "especie", "art", "specie", ("biology", "taxonomy"), {"social": 1}),
        entry("ECOSYSTEM", "ecossistema", "ecosystem", "écosystème", "ecosistema", "ökosystem", "ecosistema", ("biology", "environment"), {"physical": 1, "social": 1}),
    ]),
    "FOOD": ("food", [
        entry("MEAL", "refeição", "meal", "repas", "comida", "mahlzeit", "pasto", ("prepared", "meal"), {"artificial": 1, "countable": 1, "solid": 1}),
        entry("NUTRIENT", "nutriente", "nutrient", "nutriment", "nutriente", "nährstoff", "nutriente", ("nutrition", "substance"), {"natural": 1, "mass": 1}),
        entry("FOODSTUFF", "alimento", "foodstuff", "aliment", "alimento", "nahrungsmittel", "alimento", ("food", "general"), {"natural": 1, "mass": 1}),
        entry("FRUIT", "fruta", "fruit", "fruit", "fruta", "obst", "frutto", ("plant", "fruit"), {"natural": 1, "countable": 1, "has_color": 1}),
        entry("VEGETABLE", "legume", "vegetable", "légume", "verdura", "gemüse", "verdura", ("plant", "vegetable"), {"natural": 1, "countable": 1}),
        entry("MEAT", "carne", "meat", "viande", "carne", "fleisch", "carne", ("animal", "protein"), {"mass": 1, "biological": 1}),
        entry("GRAIN", "grão", "grain", "céréale", "grano", "getreide", "cereale", ("cereal", "seed"), {"natural": 1, "countable": 1, "storable": 1}),
        entry("DAIRY", "laticínio", "dairy", "produit laitier", "lácteo", "milchprodukt", "latticino", ("milk", "food"), {"biological": 1, "storable": 1}),
        entry("DRINK", "bebida", "drink", "boisson", "bebida", "getränk", "bevanda", ("drink", "liquid"), {"liquid": 1, "drinkable": 1, "mass": 1}),
        entry("SNACK", "lanche", "snack", "collation", "tentempié", "imbiss", "spuntino", ("food", "small_meal"), {"artificial": 1, "countable": 1}),
        entry("DESSERT", "sobremesa", "dessert", "dessert", "postre", "nachtisch", "dolce", ("sweet", "dessert"), {"artificial": 1, "countable": 1, "pleasant": 1}),
    ]),
    "LOVE": ("love", [
        entry("ROMANTIC", "amor romântico", "romantic love", "amour romantique", "amor romántico", "romantische liebe", "amore romantico", ("romance", "love")),
        entry("AFFECTION", "afeição", "affection", "affection", "afecto", "zuneigung", "affetto", ("affection", "care"), {"mild": 1, "intense": 0}),
        entry("PASSION", "paixão", "passion", "passion", "pasión", "leidenschaft", "passione", ("passion", "intense"), {"intense": 1}),
        entry("FAMILIAL", "amor familiar", "familial love", "amour familial", "amor familiar", "familienliebe", "amore familiare", ("family", "love")),
        entry("FRIENDSHIP", "amizade", "friendship", "amitié", "amistad", "freundschaft", "amicizia", ("friendship", "social"), {"mild": 1, "intense": 0}),
        entry("SELF", "amor próprio", "self-love", "amour-propre", "amor propio", "selbstliebe", "amor proprio", ("self", "esteem")),
        entry("PLATONIC", "amor platônico", "platonic love", "amour platonique", "amor platónico", "platonische liebe", "amore platonico", ("platonic", "love")),
        entry("UNCONDITIONAL", "amor incondicional", "unconditional love", "amour inconditionnel", "amor incondicional", "bedingungslose liebe", "amore incondizionato", ("unconditional", "love")),
    ]),
    "HOUSE": ("house", [
        entry("DWELLING", "moradia", "dwelling", "logement", "vivienda", "wohnung", "abitazione", ("housing", "dwelling")),
        entry("HOME", "lar", "home", "foyer", "hogar", "zuhause", "casa", ("home", "belonging"), {"abstract": 1, "physical": 1}),
        entry("RESIDENCE", "domicílio", "residence", "domicile", "domicilio", "wohnsitz", "residenza", ("residence", "formal")),
        entry("SHELTER", "abrigo", "shelter", "abri", "refugio", "unterkunft", "riparo", ("shelter", "housing")),
        entry("APARTMENT", "apartamento", "apartment", "appartement", "apartamento", "wohnung", "appartamento", ("housing", "apartment")),
        entry("COTTAGE", "casa de campo", "cottage", "cottage", "casa rural", "landhaus", "cottage", ("rural", "house")),
        entry("MANSION", "mansão", "mansion", "manoir", "mansión", "villa", "villa", ("large", "house"), {"social": 1}),
    ]),
    "SHELTER": ("shelter", [
        entry("PROTECTION", "proteção", "protection", "protection", "protección", "schutz", "protezione", ("safety", "protection")),
        entry("REFUGE", "refúgio", "refuge", "refuge", "refugio", "zuflucht", "rifugio", ("refuge", "safety")),
        entry("ASYLUM", "asilo", "asylum", "asile", "asilo", "asyl", "asilo", ("asylum", "social"), {"social": 1}),
        entry("COVER", "cobertura", "cover", "couverture", "cubierta", "deckung", "copertura", ("cover", "protection"), {"physical": 1, "abstract": 0}),
        entry("HAVEN", "porto seguro", "safe haven", "havre", "puerto seguro", "sicherer hafen", "porto sicuro", ("haven", "safety")),
        entry("SANCTUARY", "santuário", "sanctuary", "sanctuaire", "santuario", "heiligtum", "santuario", ("sanctuary", "safety"), {"social": 1}),
    ]),
    "EMOTION": ("emotion", [
        entry("JOY", "alegria", "joy", "joie", "alegría", "freude", "gioia", ("emotion", "joy"), {"positive": 1, "pleasant": 1}),
        entry("SADNESS", "tristeza", "sadness", "tristesse", "tristeza", "traurigkeit", "tristezza", ("emotion", "sadness"), {"negative": 1, "unpleasant": 1}),
        entry("FEAR", "medo", "fear", "peur", "miedo", "angst", "paura", ("emotion", "fear"), {"negative": 1, "unpleasant": 1}),
        entry("ANGER", "raiva", "anger", "colère", "ira", "wut", "rabbia", ("emotion", "anger"), {"negative": 1, "unpleasant": 1}),
        entry("SURPRISE", "surpresa", "surprise", "surprise", "sorpresa", "überraschung", "sorpresa", ("emotion", "surprise"), {"neutral": 1, "positive": 0}),
        entry("DISGUST", "nojo", "disgust", "dégoût", "asco", "ekel", "disgusto", ("emotion", "disgust"), {"negative": 1, "unpleasant": 1}),
        entry("HAPPINESS", "felicidade", "happiness", "bonheur", "felicidad", "glück", "felicità", ("emotion", "happiness"), {"positive": 1, "pleasant": 1}),
    ]),
    "NATURE": ("nature", [
        entry("FOREST", "floresta", "forest", "forêt", "bosque", "wald", "foresta", ("nature", "forest"), {"biological": 1}),
        entry("MOUNTAIN", "montanha", "mountain", "montagne", "montaña", "berg", "montagna", ("nature", "mountain"), {"solid": 1}),
        entry("DESERT", "deserto", "desert", "désert", "desierto", "wüste", "deserto", ("nature", "desert"), {"solid": 1, "has_temperature": 1}),
        entry("JUNGLE", "selva", "jungle", "jungle", "selva", "dschungel", "giungla", ("nature", "jungle"), {"biological": 1}),
        entry("ISLAND", "ilha", "island", "île", "isla", "insel", "isola", ("nature", "island"), {"solid": 1, "water_body": 1}),
    ]),
    "TIME": ("time", [
        entry("DAY", "dia", "day", "jour", "día", "tag", "giorno", ("time", "day")),
        entry("NIGHT", "noite", "night", "nuit", "noche", "nacht", "notte", ("time", "night")),
        entry("MORNING", "manhã", "morning", "matin", "mañana", "morgen", "mattina", ("time", "morning")),
        entry("EVENING", "tarde", "evening", "soir", "tarde", "abend", "sera", ("time", "evening")),
        entry("SEASON", "estação", "season", "saison", "estación", "jahreszeit", "stagione", ("time", "season")),
    ]),
    "BODY": ("body", [
        entry("HAND", "mão", "hand", "main", "mano", "hand", "mano", ("body", "hand"), {"transportable": 0}),
        entry("FOOT", "pé", "foot", "pied", "pie", "fuß", "piede", ("body", "foot"), {"transportable": 0}),
        entry("HEAD", "cabeça", "head", "tête", "cabeza", "kopf", "testa", ("body", "head"), {"transportable": 0}),
        entry("HEART", "coração", "heart", "cœur", "corazón", "herz", "cuore", ("body", "heart"), {"transportable": 0}),
        entry("BRAIN", "cérebro", "brain", "cerveau", "cerebro", "gehirn", "cervello", ("body", "brain"), {"transportable": 0, "mental": 1}),
    ]),
    "LIGHT": ("light", [
        entry("LUMINOSITY", "luz", "light", "lumière", "luz", "licht", "luce", ("light", "luminosity")),
    ]),
    "VEHICLE": ("vehicle", [
        entry("CAR", "carro", "car", "voiture", "coche", "auto", "automobile", ("vehicle", "car")),
    ]),
}

# Lemas gerais e variantes do corpus. Cada entrada aponta para um sentido já
# declarado e evita que uma busca se torne "sem ontologia" por usar sinônimo.
ALIASES = {
    "pt:comida": ["FOOD.FOODSTUFF"], "en:food": ["FOOD.FOODSTUFF"], "fr:nourriture": ["FOOD.FOODSTUFF"], "es:comida": ["FOOD.FOODSTUFF"], "de:essen": ["FOOD.FOODSTUFF"], "it:cibo": ["FOOD.FOODSTUFF"],
    "pt:amor": ["LOVE.ROMANTIC"], "en:love": ["LOVE.ROMANTIC"], "fr:amour": ["LOVE.ROMANTIC"], "es:amor": ["LOVE.ROMANTIC"], "de:liebe": ["LOVE.ROMANTIC"], "it:amore": ["LOVE.ROMANTIC"],
    "pt:casa": ["HOUSE.DWELLING"], "en:house": ["HOUSE.DWELLING"], "fr:maison": ["HOUSE.DWELLING"], "es:casa": ["HOUSE.DWELLING"], "de:haus": ["HOUSE.DWELLING"], "it:casa": ["HOUSE.DWELLING"],
    "pt:existência": ["LIFE.EXISTENCE"], "en:existence": ["LIFE.EXISTENCE"], "fr:existence": ["LIFE.EXISTENCE"], "es:existencia": ["LIFE.EXISTENCE"], "de:existenz": ["LIFE.EXISTENCE"], "it:esistenza": ["LIFE.EXISTENCE"],
}


def add_group(data: dict, group: str, profile_name: str, definitions: list) -> None:
    senses, lexemes = data["senses"], data["lexemes"]
    for suffix, words, tags, overrides in definitions:
        sense_id = f"{group}.{suffix}"
        vector = dict(PROFILES[profile_name])
        vector.update(overrides)
        senses[sense_id] = {
            "vector": vector,
            "tags": [group.lower(), *tags],
            "relations": {
                "broader": [group], "narrower": [], "part_of": [], "has_part": [], "opposite": [],
                "related": [f"{group}.{x}" for x, *_ in definitions if x != suffix][:4],
            },
            "domain": {"WATER": "nature", "LIFE": "biology", "FOOD": "nutrition", "LOVE": "emotion",
                       "HOUSE": "housing", "SHELTER": "social", "EMOTION": "emotion", "NATURE": "nature",
                       "TIME": "time", "BODY": "anatomy", "LIGHT": "physics", "VEHICLE": "transport"}[group],
            "commonness": 0.65,
            "formality": 0.5,
        }
        for lang, word in zip(("pt", "en", "fr", "es", "de", "it"), words):
            key = f"{lang}:{word.casefold()}"
            existing = lexemes.setdefault(key, [])
            if sense_id not in existing:
                existing.append(sense_id)


def main() -> None:
    data = json.loads(ONTOLOGY_FILE.read_text(encoding="utf-8"))
    data.setdefault("feature_weights", {}).update(UNIVERSAL_WEIGHTS)
    for group, (profile, definitions) in CATALOG.items():
        add_group(data, group, profile, definitions)
    for lexeme, sense_ids in ALIASES.items():
        existing = data["lexemes"].setdefault(lexeme, [])
        for sense_id in sense_ids:
            if sense_id not in existing:
                existing.append(sense_id)
    # Completa metadados relacionais nos sentidos da primeira prova de conceito.
    for sense_id in ("WATER.SUBSTANCE", "WATER.SEA", "WATER.RIVER", "WATER.STREAM", "WATER.RAIN", "LIFE.EXISTENCE"):
        relation_data = data["senses"][sense_id].setdefault("relations", {})
        for key in ("broader", "narrower", "part_of", "has_part", "related", "opposite"):
            relation_data.setdefault(key, [])
    data["revision"] = "open-domain-73-v1"
    data["schema_version"] = max(1, int(data.get("schema_version", 1)))
    ONTOLOGY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Ontologia expandida: {len(data['senses'])} sentidos e {len(data['lexemes'])} léxicos.")


if __name__ == "__main__":
    main()
