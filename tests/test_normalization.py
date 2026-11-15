# tests/test_normalization.py  (Day 2)
from src.normalization import normalize, to_grapheme_clusters


def test_zero_width_stripped():
    a = "\u0633\u0646\u068A\u064A"
    b = "\u0633\u0646\u068A\u200D\u064A"  # same word + stray ZWJ
    assert normalize(a) == normalize(b)


def test_digraph_is_one_grapheme_cluster():
    word = "\u062C\u0647\u06BE" + "\u0627"  # jjhe + alif
    clusters = to_grapheme_clusters(word)
    assert clusters[0] == "\u062C\u0647\u06BE"
    assert len(clusters) == 2


def test_empty_and_none_safe():
    assert normalize("") == ""
    assert normalize(None) == ""


# --- Phase 1 ---------------------------------------------------------------
from src.normalization import lookup_key, strip_diacritics  # noqa: E402


def test_keyboard_variants_fold_to_sindhi_letters():
    sindhi = "سنڌي"  # sindhi with Arabic yeh
    assert normalize("سنڌى") == sindhi  # alef maksura
    assert normalize("سنڌی") == sindhi  # Farsi yeh
    assert normalize("كتاب") == "ڪتاب"  # Arabic kaf -> Sindhi kaf
    assert normalize("ہ") == "ه"  # Urdu heh goal


def test_distinct_sindhi_letters_are_not_folded():
    for a, b in [("ڪ", "ک"), ("ب", "ٻ"), ("ر", "ڙ")]:
        assert lookup_key(a) != lookup_key(b)


def test_tatweel_digits_and_presentation_forms():
    assert normalize("ڪـتاب") == "ڪتاب"
    assert normalize("۲۰۲۶") == "2026"
    assert normalize("ﮡ") == "ڻ"  # rnoon final form


def test_diacritics_ignored_for_lookup_only():
    marked = "ڪِتَابُ"
    assert strip_diacritics(marked) == "ڪتاب"
    assert lookup_key(marked) == lookup_key("ڪتاب")
    assert normalize(marked) != "ڪتاب"  # display form keeps the marks


def test_do_chashmi_heh_matches_heh():
    assert lookup_key("آھي") == lookup_key("آهي")
