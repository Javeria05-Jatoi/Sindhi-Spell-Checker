# src/char_validation.py  (Day 2)
import json


def load_alphabet(path: str = "data/sindhi_alphabet_ref.json") -> set:
    with open(path, encoding="utf-8") as f:
        return {entry["letter"] for entry in json.load(f)}


def find_unrecognized_chars(word: str, alphabet: set) -> list:
    """Return characters in `word` that are not in the Day-1 alphabet table.
    Digits, ASCII, and spaces intentionally are NOT flagged here;
    extend the allow-list as the project's real-world input grows."""
    allowed_extra = set("0123456789 ")
    return [ch for ch in word if ch not in alphabet and ch not in allowed_extra]
