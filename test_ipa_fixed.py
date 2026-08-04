from ipa_fixed import ipa_fixed

def test_ipa_returns_list_and_is_deterministic():
    out1 = ipa_fixed("Casa", "pt")
    out2 = ipa_fixed("casa", "PT")
    assert isinstance(out1, list) and isinstance(out2, list)
    assert out1 == out2
    assert len(out1) >= 1
