from tnu import init_db, upsert, translate, alfa, sigma

def test_translate_legacy_sigma_fallback():
    conn = init_db()
    # monta sigma no formato legado
    vec = alfa("vida", "pt")
    sc  = sigma(vec)
    # cadastra PT e EN com o MESMO sigma legado
    upsert(conn, sc, "pt", "vida")
    upsert(conn, sc, "en", "life")
    # traduz usando a função atual (que tenta novo e cai no legado)
    out = translate(conn, "vida", "pt", "en")
    assert "life" in out
