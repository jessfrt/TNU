from tnu import init_db, upsert
from lookup_partial import lookup_by_code_o

def test_lookup_by_code_o_exact_and_tol():
    conn = init_db()
    # dois code-O próximos; um no alvo 'fr', outro em 'en'
    code_o_pt = "0.100–0.010–0.800"
    code_o_fr = "0.099–0.010–0.801"
    code_o_en = "0.102–0.011–0.802"

    # simula registros com marks contendo codeO
    upsert(conn, "scode_pt", "pt", "casa", marks={"codeO": code_o_pt})
    upsert(conn, "scode_fr", "fr", "maison", marks={"codeO": code_o_fr})
    upsert(conn, "scode_en", "en", "house", marks={"codeO": code_o_en})

    # match exato (pt)
    ex = lookup_by_code_o(conn, code_o_pt, target_lang="pt", tol=None)
    assert any(lemma == "casa" for (_l, lemma, _c, _d) in ex)

    # match aproximado (fr) perto do pt
    near = lookup_by_code_o(conn, code_o_pt, target_lang="fr", tol=0.005)
    assert any(lemma == "maison" for (_l, lemma, _c, _d) in near)
