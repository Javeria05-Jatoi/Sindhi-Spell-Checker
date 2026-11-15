# tests/test_distance.py  (Day 5-6)
from src.edit_distance import levenshtein, levenshtein_table, weighted_edit_distance
from src.sindhi_cost_model import STRUCTURAL_GROUP_COST


def test_identical_strings():
    assert levenshtein("same", "same") == 0


def test_kitten_sitting():
    assert levenshtein("kitten", "sitting") == 3


def test_two_implementations_agree():
    pairs = [("abc", "abd"), ("", "abc"), ("sindhi", "sindi"), ("test", "tent")]
    for a, b in pairs:
        assert levenshtein(a, b) == levenshtein_table(a, b)


def test_weighted_distance_within_group_is_cheaper():
    # \u0628 (be) and \u067B (bbe) are in the same structural group (src/sindhi_cost_model.py)
    a = "\u0628\u0627"
    b = "\u067B\u0627"
    within_group = weighted_edit_distance(a, b)
    assert within_group == STRUCTURAL_GROUP_COST < 1.0
