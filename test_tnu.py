from tnu import init_db, translate, upsert, sigma, alfa

def test_vida_life():
    conn = init_db()
    # cadastra as duas palavras com o MESMO sigma (manual)
    vec = alfa("vida", "pt")
    sc  = sigma(vec)
    upsert(conn, sc, "pt", "vida")
    upsert(conn, sc, "en", "life")
    # tradução
    res = translate(conn, "vida", "pt", "en")
    assert "life" in res