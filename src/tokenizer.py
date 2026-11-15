# src/tokenizer.py  (Day 2, spans added Phase 1)
import re
from src.normalization import normalize

# Sindhi/Urdu-style punctuation plus common ASCII punctuation.
_PUNCT_PATTERN = re.compile(r"[،؛؟۔.,!?;:()\[\]{}\"'“”\-]+")
_WHITESPACE_PATTERN = re.compile(r"\s+")

# Phase 1: a "word" is a run of Arabic-script letters/marks (plus ZWNJ/ZWJ),
# so offsets into the ORIGINAL text survive for click-to-replace in the UI.
# Excludes Arabic punctuation (، ؛ ؟ ۔ ٪ ٫ ٬) and both digit sets.
_ARABIC_WORD = re.compile(
    r"[ء-غـ-ٰٟ-ۓە-ۯۺ-ۿ"
    r"ݐ-ݿﭐ-﷿ﹰ-ﻼ‌‍]+")
_OTHER_WORD = re.compile(r"[A-Za-z0-9٠-٩۰-۹ऀ-ॿ]+")


def tokenize(text: str) -> list:
    text = normalize(text)
    text = _PUNCT_PATTERN.sub(" ", text)
    tokens = [t for t in _WHITESPACE_PATTERN.split(text) if t]
    return tokens


def tokenize_with_spans(text: str) -> list:
    """[(token, start, end, is_sindhi), ...] with offsets into `text`."""
    spans = [(m.group(), m.start(), m.end(), True) for m in _ARABIC_WORD.finditer(text or "")]
    spans += [(m.group(), m.start(), m.end(), False) for m in _OTHER_WORD.finditer(text or "")]
    spans.sort(key=lambda s: s[1])
    return spans


if __name__ == "__main__":
    print(tokenize("hello world, test، sentence"))
