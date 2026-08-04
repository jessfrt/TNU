from tnu_determinism import make_sigma_payload, stable_hash, quantize_seq

def test_payload_and_hash_stable():
    ipa = ["ˈka", "za"]
    vec = quantize_seq([0.10000012, 0.0099999, 0.8000003], ndigits=6)
    p1 = make_sigma_payload("Casa", "PT", ipa, vec)
    p2 = make_sigma_payload("casa ", "pt", ipa, vec)
    assert p1 == p2
    assert stable_hash(p1) == stable_hash(p2)

