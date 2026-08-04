from sigma_partial import sigma_partial
from tnu import init_db, upsert
from translate_partial import translate_partial


def test_translate_partial_by_resonance():
    conn = init_db()
    # gera o code-O com a MESMA função do sistema
    code_o_casa_pt = sigma_partial("casa", "pt", "B")
    code_o_maison_fr = code_o_casa_pt  # para garantir match exato no teste

    upsert(conn, "scode_pt", "pt", "casa",   marks={"codeO": code_o_casa_pt})
    upsert(conn, "scode_fr", "fr", "maison", marks={"codeO": code_o_maison_fr})

    out = translate_partial(conn, "casa", "pt", "fr", tol=None)  # exato
    assert "maison" in out
