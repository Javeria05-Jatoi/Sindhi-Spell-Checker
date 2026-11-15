# src/dictionary.py  (Day 4, extended Day 10, reworked Phase 1/2)
import json
import os
import re
from collections import defaultdict

from src.normalization import lookup_key, normalize

FREQUENCIES_PATH = "data/frequencies.tsv"
EXTRA_TRANSLATIONS_PATH = "data/extra_translations.json"
USER_WORDS_PATH = "data/user_words.txt"

# Phase 2: a corpus word seen at least this often is accepted as correctly
# spelled even when the lexicon (which lists base forms only) lacks it.
CORPUS_KNOWN_MIN_COUNT = 5
# ...and offered as a spelling suggestion when seen at least this often.
CORPUS_CANDIDATE_MIN_COUNT = 10

# Headwords like "اڳاڃ، اڳاڃو يا اڳاڃو" list several spellings at once.
_HEADWORD_SPLIT = re.compile(r"\s*[،,]\s*|\s+يا\s+")
_PARENTHETICAL = re.compile(r"\([^)]*\)")

# Phase 2: inflection endings tried when a word has no entry of its own
# (longest first). Each stripped stem is retried with these lemma endings.
_SUFFIXES = sorted([
    "ن", "ين", "ون", "ئون", "يون", "ئين", "ئي", "يو", "يا", "ي", "ا", "و", "ءَ", "ءُ",
    "ندو", "ندي", "ندا", "نديون", "ڻو", "ڻي", "ڻا", "يندو", "يندي", "يندا",
    "ائين", "ائي", "ايو", "ايا", "ڻ", "ون", "ات", "ن جو", "ڪار",
], key=len, reverse=True)
_LEMMA_ENDINGS = ["", "و", "ڻ", "ي", "ا", "ُ"]

# Mewaram-style glosses start with grammar abbreviations ("s. m.", "Inter.").
_GLOSS_PREFIX = re.compile(
    r"^(?:(?:s|a|ad|adv|v|vt|vi|inter|interj|conj|pron|prep|post|f|m|n|pl|plu|"
    r"nom|c|ind|part|num|mf)\.\s*)+", re.IGNORECASE)

_WORD_TOKEN = re.compile(r"[a-z]+")
_STOPWORDS = set("a an the of to in on for and or is be by as at with from".split())


_EMPTY_GLOSSES = {"see", "see.", "do.", "ditto", "ditto."}


def clean_gloss(text: str) -> str:
    text = _GLOSS_PREFIX.sub("", text.strip())
    if text.lower() in _EMPTY_GLOSSES or len(text) < 2:
        return ""
    return text[:1].upper() + text[1:]


def split_headword(word: str) -> list:
    word = _PARENTHETICAL.sub(" ", word)
    return [w.strip() for w in _HEADWORD_SPLIT.split(word) if w.strip()]


def _load_frequencies(path: str) -> dict:
    freqs = {}
    if not os.path.exists(path):
        return freqs
    with open(path, encoding="utf-8") as f:
        for line in f:
            word, _, count = line.rstrip("\n").partition("\t")
            if count:
                freqs[word] = int(count)
    return freqs


class Dictionary:
    def __init__(self, path: str = "data/dictionary.json",
                 frequencies_path: str = FREQUENCIES_PATH,
                 extra_translations_path: str = EXTRA_TRANSLATIONS_PATH,
                 user_words_path: str = USER_WORDS_PATH):
        with open(path, encoding="utf-8") as f:
            raw_entries = json.load(f)

        self._entries = {}   # lookup_key -> merged entry (single words)
        self._phrases = {}   # "key key" -> merged entry (multi-word headwords)
        for raw in raw_entries:
            forms = split_headword(raw["word"]) or [raw["word"]]
            for form in forms:
                self._add(form, raw)
            for variant in raw.get("variants", []):
                # variants look like "ڪِتَابُ جمع ڪِتَابَ"; keep the first token
                first = normalize(variant).split(" ")[0] if variant else ""
                if first:
                    self._add(first, raw, display=False)

        self._frequencies = _load_frequencies(frequencies_path)
        for key, entry in self._entries.items():
            entry["frequency"] = max(entry.get("frequency") or 0,
                                     self._frequencies.get(key, 0))

        self._extra_translations = {}
        if extra_translations_path and os.path.exists(extra_translations_path):
            with open(extra_translations_path, encoding="utf-8") as f:
                self._extra_translations = json.load(f)
            for key, glosses in self._extra_translations.items():
                entry = self._entries.get(key)
                if entry is None:
                    entry = self._add(key, {"word": key, "meanings": [], "translations": [],
                                            "pos": None, "source": "Wiktionary"})
                for gloss in glosses:
                    if gloss not in entry["translations"]:
                        entry["translations"].insert(0, gloss)
                if "Wiktionary" not in entry["sources"]:
                    entry["sources"].append("Wiktionary")

        self._user_words = set()
        self.user_words_path = user_words_path
        if user_words_path and os.path.exists(user_words_path):
            with open(user_words_path, encoding="utf-8") as f:
                self._user_words = {lookup_key(w) for w in f if w.strip()}

        self._reverse_index = None

    # --- Phase 1: entry merging ----------------------------------------------
    def _add(self, form: str, raw: dict, display: bool = True):
        form = normalize(form)
        key = lookup_key(form)
        if not key:
            return None
        table = self._phrases if " " in key else self._entries
        entry = table.get(key)
        if entry is None:
            entry = table[key] = {
                "word": form, "key": key, "forms": [], "meanings": [], "translations": [],
                "pos": None, "frequency": raw.get("frequency") or 0, "sources": [],
                "examples": raw.get("examples", []),
            }
        if display and form not in entry["forms"]:
            entry["forms"].append(form)
        for meaning in raw.get("meanings", []):
            if meaning and meaning not in entry["meanings"]:
                entry["meanings"].append(meaning)
        for translation in raw.get("translations", []):
            translation = clean_gloss(translation)
            if translation and translation not in entry["translations"]:
                entry["translations"].append(translation)
        if not entry["pos"] and raw.get("pos"):
            entry["pos"] = raw["pos"]
        source = raw.get("source")
        if source and source not in entry["sources"]:
            entry["sources"].append(source)
        return entry

    # --- Day 4: basic lookup -------------------------------------------------
    def is_known(self, word: str) -> bool:
        return self.status(word) != "unknown"

    def status(self, word: str) -> str:
        """Phase 2: why a word counts as correct: lexicon / phrase / corpus / user / unknown."""
        key = lookup_key(word)
        if not key:
            return "unknown"
        if key in self._entries:
            return "lexicon"
        if key in self._phrases:
            return "phrase"
        if key in self._user_words:
            return "user"
        if self._frequencies.get(key, 0) >= CORPUS_KNOWN_MIN_COUNT:
            return "corpus"
        return "unknown"

    def lookup(self, word: str):
        key = lookup_key(word)
        return self._entries.get(key) or self._phrases.get(key)

    def get_meanings(self, word: str) -> list:
        entry = self.lookup(word)
        return entry["meanings"] if entry else []

    def get_translations(self, word: str) -> list:
        entry = self.lookup(word)
        return entry.get("translations", []) if entry else []

    def all_words(self) -> list:
        return list(self._entries.keys())

    def __len__(self):
        return len(self._entries)

    def frequency(self, word: str) -> int:
        key = lookup_key(word)
        return self._frequencies.get(key, 0) or (self._entries.get(key) or {}).get("frequency", 0)

    def is_phrase(self, keys: list) -> bool:
        return " ".join(keys) in self._phrases

    def candidate_vocabulary(self) -> dict:
        """Phase 1/2: every single word that may be offered as a suggestion -> count."""
        vocab = {key: self._frequencies.get(key, 0) for key in self._entries}
        for key, count in self._frequencies.items():
            if count >= CORPUS_CANDIDATE_MIN_COUNT and " " not in key:
                vocab.setdefault(key, count)
        for key in self._user_words:
            vocab.setdefault(key, 1)
        return vocab

    # --- Phase 2: inflected forms ---------------------------------------------
    def base_form(self, word: str, need_translation: bool = False):
        """Best-guess lexicon headword for an inflected word (ڪتابن -> ڪتاب).
        need_translation=True skips headwords that have no English gloss."""
        key = lookup_key(word)
        exact = self._entries.get(key)
        if exact and (exact["translations"] or not need_translation):
            return exact
        for suffix in _SUFFIXES:
            if key.endswith(suffix) and len(key) - len(suffix) >= 2:
                stem = key[: -len(suffix)]
                for ending in _LEMMA_ENDINGS:
                    entry = self._entries.get(lookup_key(stem + ending))
                    if entry and (entry["translations"] or not need_translation):
                        return entry
        return None

    # --- Phase 2: user allow-list -----------------------------------------------
    def add_user_word(self, word: str) -> bool:
        key = lookup_key(word)
        if not key or key in self._user_words:
            return False
        self._user_words.add(key)
        if self.user_words_path:
            os.makedirs(os.path.dirname(self.user_words_path) or ".", exist_ok=True)
            with open(self.user_words_path, "a", encoding="utf-8") as f:
                f.write(normalize(word) + "\n")
        return True

    # --- Phase 2: English -> Sindhi ------------------------------------------
    def reverse_lookup(self, english: str, limit: int = 20) -> list:
        """Sindhi headwords whose English gloss contains every query word."""
        if self._reverse_index is None:
            index = defaultdict(set)
            for key, entry in self._entries.items():
                for gloss in entry["translations"]:
                    for token in _WORD_TOKEN.findall(gloss.lower()):
                        if token not in _STOPWORDS:
                            index[token].add(key)
            self._reverse_index = index
        tokens = [t for t in _WORD_TOKEN.findall(english.lower()) if t not in _STOPWORDS]
        if not tokens:
            return []
        keys = set.intersection(*(self._reverse_index.get(t, set()) for t in tokens))

        def rank(key):
            entry = self._entries[key]
            # prefer short glosses that start with the query ("A book." for "book")
            best = min((len(g) for g in entry["translations"]
                        if english.lower() in g.lower()), default=999)
            return (best, -entry.get("frequency", 0))

        return [self._entries[k] for k in sorted(keys, key=rank)[:limit]]

    # --- Day 10: richer translation detail -----------------------------------
    def meanings_detailed(self, word: str):
        entry = self.lookup(word)
        if not entry:
            return None
        return {
            "word": entry["word"],
            "meanings": entry["meanings"],
            "pos": entry.get("pos"),
            "examples": entry.get("examples", []),
        }


if __name__ == "__main__":
    d = Dictionary()
    print(f"Loaded {len(d)} dictionary entries.")
