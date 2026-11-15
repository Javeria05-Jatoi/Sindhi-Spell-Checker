# src/normalization.py  (Day 2, extended Phase 1)
# Canonicalizes Sindhi Unicode text before ANY lookup, comparison, or
# edit-distance operation. Every other module depends on this being correct.

import re
import unicodedata
from functools import lru_cache

ZERO_WIDTH = {"​", "‌", "‍", "﻿", "‎", "‏"}

# Presentation-form -> base-letter folding (Phase 1): built from Unicode's own
# compatibility decompositions for the whole Arabic presentation-form blocks,
# instead of a hand-written partial table.
def _build_presentation_form_map() -> dict:
    table = {}
    for start, end in ((0xFB50, 0xFDFF), (0xFE70, 0xFEFF)):
        for cp in range(start, end + 1):
            ch = chr(cp)
            # isolated harakat forms decompose to " " + mark; drop the space
            folded = unicodedata.normalize("NFKC", ch).replace(" ", "")
            if folded != ch and folded:
                table[ch] = folded
    return table


PRESENTATION_FORM_MAP = _build_presentation_form_map()

# Phase 1: code points that are the SAME letter typed from an Arabic, Urdu or
# Persian keyboard. Letters that are distinct in Sindhi (ڪ/ک, ه/ھ, ب/ٻ/ڀ,
# ر/ڙ ...) are deliberately NOT folded.
CHAR_FOLD_MAP = {
    "ى": "ي",  # ى alef maksura   -> ي
    "ی": "ي",  # ی Farsi yeh       -> ي
    "ك": "ڪ",  # ك Arabic kaf      -> ڪ Sindhi kaf
    "ہ": "ه",  # ہ Urdu heh goal   -> ه
    "ۂ": "هٔ",
    "ۀ": "هٔ",
    "ە": "ه",  # ە ae              -> ه
    "ـ": "",        # tatweel (kashida) is decoration only
}
for _i, _d in enumerate("٠١٢٣٤٥٦٧٨٩"):
    CHAR_FOLD_MAP[_d] = str(_i)
for _i, _d in enumerate("۰۱۲۳۴۵۶۷۸۹"):
    CHAR_FOLD_MAP[_d] = str(_i)

# Short vowels and other marks (zabar, zer, pesh, tanween, shadda, sukun,
# superscript alef...). Optional in everyday Sindhi writing, so they are
# ignored for lookup but kept for display.
DIACRITICS_PATTERN = re.compile("[ً-ٰٟۖ-ۭ]")

# After diacritics are gone, the lexicon's "ۇ" (U+06C7) is a mis-encoded
# waw + pesh and should match plain waw. Sindhi Wikipedia writes do-chashmi
# heh (ھ) where the lexicon writes heh (ه) -- "آھي" vs "آهي" -- so both are
# one letter for lookup purposes (display keeps whatever the writer typed).
KEY_FOLD_MAP = {"ۇ": "و", "ھ": "ه"}

# Two-code-point letters that must be treated as ONE logical letter (Day 1 convention).
DIGRAPH_LETTERS = ["جهھ", "گهھ"]  # jjhe, gghe

_TRANSLATE_TABLE = str.maketrans({**PRESENTATION_FORM_MAP, **CHAR_FOLD_MAP})
_KEY_TABLE = str.maketrans(KEY_FOLD_MAP)


def strip_zero_width(text: str) -> str:
    return "".join(ch for ch in text if ch not in ZERO_WIDTH)


def fold_presentation_forms(text: str) -> str:
    return "".join(PRESENTATION_FORM_MAP.get(ch, ch) for ch in text)


def normalize(text: str) -> str:
    """Canonicalize Sindhi text before any lookup or comparison."""
    if text is None:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = strip_zero_width(text)
    # presentation forms first, then the fold map, so NFKC output can't
    # reintroduce a variant letter
    text = text.translate(_TRANSLATE_TABLE)
    text = unicodedata.normalize("NFC", text)
    text = text.strip()
    return text


def strip_diacritics(text: str) -> str:
    return DIACRITICS_PATTERN.sub("", text)


def lookup_key(text: str) -> str:
    """Phase 1: the canonical key used for dictionary lookup and spelling."""
    return strip_diacritics(normalize(text)).translate(_KEY_TABLE)


@lru_cache(maxsize=200_000)
def _clusters(word: str) -> tuple:
    clusters = []
    i = 0
    while i < len(word):
        matched = False
        for digraph in DIGRAPH_LETTERS:
            if word.startswith(digraph, i):
                clusters.append(digraph)
                i += len(digraph)
                matched = True
                break
        if not matched:
            clusters.append(word[i])
            i += 1
    return tuple(clusters)


def to_grapheme_clusters(word: str) -> list:
    """Split a normalized word into logical letters, keeping Day-1 digraphs as one unit."""
    return list(_clusters(word))


if __name__ == "__main__":
    # quick manual smoke test
    sample = "سنڊي" + "‍"  # a word + a stray zero-width joiner
    print(repr(sample), "->", repr(normalize(sample)))
