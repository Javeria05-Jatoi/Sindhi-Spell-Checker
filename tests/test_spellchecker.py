# tests/test_spellchecker.py  (Day 9, Phase 1-3 cases added)
# NOTE: these tests need a real data/dictionary.json to exist first
# (run scripts/download_lexicon.py + scripts/build_dictionary_json.py,
# or scripts/build_seed_dictionary.py for a tiny offline sample).
import os
import time

import pytest
from src.spellchecker import SpellChecker

DICT_PATH = "data/dictionary.json"
needs_data = pytest.mark.skipif(not os.path.exists(DICT_PATH), reason="dictionary.json not built yet")


@pytest.fixture(scope="module")
def checker():
    return SpellChecker(DICT_PATH)


@needs_data
def test_check_text_runs(checker):
    results = checker.check_text("test")
    assert isinstance(results, list)


@needs_data
def test_empty_input(checker):
    assert checker.check_text("") == []


@needs_data
def test_only_top_three_suggestions(checker):
    assert len(checker.suggest("ڪتاپ")) <= 3


@needs_data
def test_common_typo_is_corrected(checker):
    # kitap -> kitab ("book"), iskool+l -> iskool ("school")
    assert checker.suggest("ڪتاپ")[0]["word"] == "ڪتاب"
    assert checker.suggest("اسڪولل")[0]["word"] == "اسڪول"


@needs_data
def test_offsets_point_into_original_text(checker):
    text = "مان ڪتاپ، پڑهان"
    for item in checker.check_text(text):
        assert text[item["start"]:item["end"]] == item["token"]


@needs_data
def test_corrected_text_applies_top_suggestion(checker):
    assert checker.corrected_text("ڪتاپ") == "ڪتاب"


@needs_data
def test_suggest_is_fast(checker):
    checker.suggest("زندگا")  # warm up
    t = time.perf_counter()
    for _ in range(10):
        checker.suggest("اسڪل")
    assert (time.perf_counter() - t) / 10 < 0.2  # was ~1.6 s before SymSpell
