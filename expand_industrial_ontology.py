#!/usr/bin/env python3
"""Expansão industrial inicial, curável e determinística da Camada D.

Cria raízes de domínio e sentidos PT para o vocabulário-base. Traduções não
curadas não são inventadas: cada nova entrada recebe ``source=seed_pt_v1`` e
fica pronta para revisão/mapeamento multilíngue posterior.
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILE = ROOT / "ontology_concepts.json"

DOMAINS = {
    "EMOTION": "alegria felicidade gratidão esperança otimismo entusiasmo admiração confiança orgulho serenidade calma paz compaixão empatia amizade lealdade devoção coragem bondade gentileza tristeza melancolia depressão medo raiva nojo ódio inveja ciúmes culpa vergonha frustração ansiedade pânico solidão violência perdão reconciliação surpresa curiosidade reflexão compreensão",
    "NATURE": "floresta montanha serra planalto planície vale vulcão cânion colina oceano mar lago lagoa rio riacho córrego nascente cachoeira chuva neve granizo furacão tornado ilha arquipélago praia duna recife pântano manguezal solo rocha mineral areia argila ecossistema bioma habitat poluição sustentabilidade energia solar energia eólica",
    "HEALTH": "cabeça crânio cérebro neurônio coração pulmão fígado rim estômago intestino sangue osso músculo pele olho ouvido respiração circulação digestão metabolismo imunidade febre dor náusea inflamação infecção vírus bactéria fungo parasita dengue gripe pneumonia diabetes câncer cirurgia transplante antibiótico vacina insulina vitamina",
    "TECHNOLOGY": "computador desktop notebook tablet smartphone servidor processador cpu gpu memória ram disco ssd teclado mouse monitor câmera microfone impressora internet site portal rede social api sdk biblioteca framework compilador interpretador ide terminal banco de dados container docker kubernetes algoritmo inteligência artificial aprendizado máquina modelo tokenização criptografia autenticação privacidade",
    "SPORT": "futebol basquete vôlei handebol tênis badminton golfe atletismo natação surfe skate ciclismo corrida caminhada musculação pilates ioga alongamento força resistência velocidade agilidade competição torneio campeonato olimpíadas medalha campeão treinador árbitro estádio quadra piscina",
    "ART": "pintura desenho escultura fotografia cinema animação design arquitetura moda cerâmica mosaico graffiti instalação performance música jazz blues rock samba bossa nova composição violão guitarra piano bateria canto poesia romance conto fábula mito lenda teatro drama comédia literatura",
    "SCIENCE": "número adição subtração multiplicação divisão equação função matriz vetor geometria álgebra estatística probabilidade lógica física mecânica energia força massa velocidade gravidade eletricidade magnetismo química átomo molécula elemento composto reação biologia genética evolução ecologia anatomia filosofia ontologia epistemologia ética estética",
    "SOCIETY": "estado nação país república democracia monarquia ditadura governo eleição voto legislativo executivo judiciário justiça lei constituição contrato direito diplomacia aliança economia capitalismo socialismo comércio indústria agricultura investimento renda riqueza pobreza inflação desemprego desigualdade migração refugiado asilo",
}

PROFILES = {
    "EMOTION": {"abstract": 1, "mental": 1, "social": 1, "intense": 1},
    "NATURE": {"entity": 1, "physical": 1, "natural": 1, "inanimate": 1},
    "HEALTH": {"entity": 1, "physical": 1, "biological": 1, "natural": 1},
    "TECHNOLOGY": {"entity": 1, "physical": 1, "artificial": 1, "inanimate": 1},
    "SPORT": {"abstract": 1, "physical": 1, "social": 1, "process": 1},
    "ART": {"abstract": 1, "social": 1, "mental": 1, "positive": 1},
    "SCIENCE": {"abstract": 1, "mental": 1, "social": 1, "neutral": 1},
    "SOCIETY": {"abstract": 1, "social": 1, "mental": 1},
}
POSITIVE = {"alegria", "felicidade", "gratidão", "esperança", "otimismo", "serenidade", "calma", "paz", "compaixão", "empatia", "amizade", "perdão", "reconciliação"}
NEGATIVE = {"tristeza", "melancolia", "depressão", "medo", "raiva", "nojo", "ódio", "inveja", "ciúmes", "culpa", "vergonha", "frustração", "ansiedade", "pânico", "solidão", "violência", "dor", "náusea", "infecção", "poluição", "pobreza", "desemprego", "desigualdade", "ditadura"}
EXISTING = {"alegria": "EMOTION.JOY", "tristeza": "EMOTION.SADNESS", "medo": "EMOTION.FEAR", "raiva": "EMOTION.ANGER", "nojo": "EMOTION.DISGUST", "surpresa": "EMOTION.SURPRISE", "felicidade": "EMOTION.HAPPINESS"}
OPPOSITES = {"alegria": "tristeza", "felicidade": "tristeza", "amor": "ódio", "paz": "violência", "esperança": "desespero", "coragem": "medo", "riqueza": "pobreza", "democracia": "ditadura"}


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().upper()
    return "_".join("".join(c if c.isalnum() else " " for c in text).split())


def sense_id(domain: str, word: str) -> str:
    return EXISTING.get(word, f"{domain}.{slug(word)}")


def main() -> None:
    data = json.loads(FILE.read_text(encoding="utf-8"))
    senses, lexemes = data["senses"], data["lexemes"]
    for domain, word_string in DOMAINS.items():
        root_id = f"DOMAIN.{domain}"
        senses.setdefault(root_id, {"vector": {"abstract": 1, "social": 1}, "tags": ["domain", domain.lower()],
                                   "relations": {"broader": [], "narrower": [], "related": [], "opposite": []}, "domain": domain.lower(), "source": "seed_pt_v1"})
        for word in word_string.split(" "):
            sid = sense_id(domain, word)
            vector = dict(PROFILES[domain])
            if word in POSITIVE: vector.update({"positive": 1, "pleasant": 1, "negative": 0})
            if word in NEGATIVE: vector.update({"negative": 1, "unpleasant": 1, "positive": 0})
            senses.setdefault(sid, {"vector": vector, "tags": [domain.lower(), slug(word).lower()],
                                    "relations": {"broader": [root_id], "narrower": [], "part_of": [], "has_part": [], "related": [], "opposite": []},
                                    "domain": domain.lower(), "commonness": 0.5, "formality": 0.5, "source": "seed_pt_v1"})
            lexemes.setdefault(f"pt:{word.casefold()}", [])
            if sid not in lexemes[f"pt:{word.casefold()}"]:
                lexemes[f"pt:{word.casefold()}"].append(sid)
    for word, opposite in OPPOSITES.items():
        ids = lexemes.get(f"pt:{word}", [])
        target = lexemes.get(f"pt:{opposite}", [])
        for sid in ids:
            for other in target:
                if other not in senses[sid]["relations"].setdefault("opposite", []):
                    senses[sid]["relations"]["opposite"].append(other)
    data["revision"] = "industrial-seed-pt-v1"
    FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Ontologia industrial: {len(senses)} sentidos; {len(lexemes)} léxicos.")


if __name__ == "__main__":
    main()
