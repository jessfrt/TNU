#!/usr/bin/env python3
"""
AtualizaAuto – cadastra palavras com σ fixo e arquiva
Uso: python atualiza_auto.py
"""
from tnu import init_db, upsert, alfa, sigma
from datetime import datetime
import json, pathlib

# VOCÊ EDITA AQUI: mesma palavra em vários idiomas
PALAVRAS = [
    {'nucleo': 'casa',   'pt': 'casa',   'fr': 'maison', 'en': 'house',  'es': 'casa'},
    {'nucleo': 'agua',   'pt': 'agua',   'fr': 'eau',    'en': 'water',  'es': 'agua'},
    {'nucleo': 'amor',   'pt': 'amor',   'fr': 'amour',  'en': 'love',   'es': 'amor'},
]

ARQUIVO_LOG = "atualiza_auto.log.json"  # histórico

def atualiza_palavra(nucleo: str, palavras: dict):
    conn = init_db()
    # gera σ fixo uma vez só (a partir da palavra-base)
    sc = sigma(alfa(palavras['pt'], 'pt'))  # usa pt como base
    log_entry = {
        'data': datetime.now().isoformat(),
        'nucleo': nucleo,
        'sigma': sc,
        'palavras': palavras
    }
    # cadastra todas as línguas com o mesmo σ
    for lang, lemma in palavras.items():
        if lang == 'nucleo':  # pulamos a chave auxiliar
            continue
        upsert(conn, sc, lang, lemma)
    # salva log
    pathlib.Path(ARQUIVO_LOG).write_text(json.dumps(log_entry, ensure_ascii=False, indent=2))
    print(f'✅ Atualizado: {nucleo} → σ={sc}')

if __name__ == '__main__':
    for item in PALAVRAS:
        atualiza_palavra(item['nucleo'], item)