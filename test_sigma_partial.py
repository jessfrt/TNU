from sigma_partial import sigma_partial
from ipa_fixed import ipa_fixed

def test_code_o_triplet_shape():
    c = sigma_partial("casa", "pt", "B")
    assert c.count("–") == 2  # "a–b–c"
