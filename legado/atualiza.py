#!/usr/bin/env python3
from tnu import init_db, upsert, alfa, sigma

def atualiza_par(nucleo: str, src_word: str, tgt_word: str, src_lang: str, tgt_lang: str):
    """
    Garante que duas palavras tenham o MESMO σ atual.
    Ex.: nucleo = 'casa', src_word = 'casa', tgt_word = 'maison'
    """
    conn = init_db()
    sc = sigma(alfa(src_word, src_lang))  # σ atual
    upsert(conn, sc, src_lang, src_word)
    upsert(conn, sc, tgt_lang, tgt_word)
    print(f'Atualizado: {src_word}({src_lang}) ↔ {tgt_word}({tgt_lang}) → σ={sc}')

if __name__ == '__main__':
    # ==== CONFIGURE AQUI ====
    atualiza_par(nucleo='casa', src_word='casa', tgt_word='maison', src_lang='pt', tgt_lang='fr')
    atualiza_par(nucleo='house', src_word='house', tgt_word='maison', src_lang='en', tgt_lang='fr')
    # ========================