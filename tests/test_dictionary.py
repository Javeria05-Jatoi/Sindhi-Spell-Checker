# tests/test_dictionary.py  (Day 4, Phase 1/2 cases added)
import json
import os
import tempfile
from src.dictionary import Dictionary, split_headword

KITAB = "ڪتاب"
SAMPLE_ENTRIES = [
    {"word": KITAB, "meanings": ["book"], "pos": "noun",
     "frequency": 10, "variants": [], "source": "test"},
    {"word": "ڪِتَاب", "meanings": [], "translations": ["s. m. A book."],
     "pos": "noun", "frequency": 0, "variants": [], "source": "test2"},
    {"word": "اڪڑ، اڪڑو يا اڪڑي",
     "meanings": ["x"], "variants": [], "source": "test"},
    {"word": "اڪ ڇنڀ", "meanings": ["blink"], "variants": [], "source": "test"},
]


def _make_temp_dictionary():
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_ENTRIES, f, ensure_ascii=False)
    return path


def _dictionary():
    path = _make_temp_dictionary()
    d = Dictionary(path, frequencies_path="", extra_translations_path="", user_words_path="")
    os.remove(path)
    return d


def test_known_word_lookup():
    d = _dictionary()
    assert d.is_known(KITAB) is True
    assert d.get_meanings(KITAB) == ["book"]


def test_unknown_word_lookup():
    d = _dictionary()
    assert d.is_known("not-a-real-word") is False
    assert d.lookup("not-a-real-word") is None


def test_diacritic_variants_merge_into_one_entry():
    d = _dictionary()
    entry = d.lookup(KITAB)
    assert entry["translations"] == ["A book."]  # "s. m." grammar prefix cleaned
    assert set(entry["sources"]) == {"test", "test2"}


def test_compound_headword_is_split():
    assert split_headword("اڪڑ، اڪڑو يا اڪڑي") == \
        ["اڪڑ", "اڪڑو", "اڪڑي"]
    d = _dictionary()
    for word in ["اڪڑ", "اڪڑو", "اڪڑي"]:
        assert d.status(word) == "lexicon"


def test_phrases_kept_out_of_spelling_vocabulary():
    d = _dictionary()
    assert d.is_phrase(["اڪ", "ڇنڀ"])
    assert all(" " not in w for w in d.candidate_vocabulary())


def test_base_form_of_inflected_word():
    d = _dictionary()
    assert d.base_form(KITAB + "ن")["key"] == KITAB  # kitab + n (oblique plural)


def test_reverse_lookup_english():
    d = _dictionary()
    assert [e["key"] for e in d.reverse_lookup("book")] == [KITAB]
