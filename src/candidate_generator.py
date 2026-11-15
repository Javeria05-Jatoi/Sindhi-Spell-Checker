# src/candidate_generator.py  (Day 7 baseline, Day 13 length-indexed optimization)
from collections import defaultdict
from src.edit_distance import weighted_edit_distance
from src.normalization import to_grapheme_clusters


def generate_candidates(query: str, dictionary_words: list, max_distance: float = 2.0):
    """Day 7 baseline: length-filtered brute force.
    Returns [(word, distance), ...] sorted by distance ascending."""
    q_len = len(to_grapheme_clusters(query))
    candidates = []
    for word in dictionary_words:
        w_len = len(to_grapheme_clusters(word))
        if abs(w_len - q_len) > max_distance:
            continue  # cannot possibly be within max_distance
        dist = weighted_edit_distance(query, word)
        if dist <= max_distance:
            candidates.append((word, dist))
    candidates.sort(key=lambda pair: pair[1])
    return candidates


# --- Day 13: length-bucketed index, for larger dictionaries ------------------
def build_length_index(dictionary_words: list) -> dict:
    index = defaultdict(list)
    for word in dictionary_words:
        index[len(to_grapheme_clusters(word))].append(word)
    return index


def generate_candidates_indexed(query: str, length_index: dict, max_distance: float = 2.0):
    q_len = len(to_grapheme_clusters(query))
    candidates = []
    for length in range(max(0, q_len - int(max_distance)), q_len + int(max_distance) + 1):
        for word in length_index.get(length, []):
            dist = weighted_edit_distance(query, word)
            if dist <= max_distance:
                candidates.append((word, dist))
    candidates.sort(key=lambda pair: pair[1])
    return candidates


# --- Phase 1: SymSpell index (symmetric-delete), for < 50 ms lookups ----------
import hashlib  # noqa: E402
import os  # noqa: E402
import pickle  # noqa: E402

CACHE_DIR = "data/cache"


class SymSpellIndex:
    """Generates candidates with SymSpell (plain edit distance <= max_edit) and
    re-scores them with the Sindhi-weighted distance, so the cost model still
    decides the final order."""

    def __init__(self, vocabulary: dict, max_edit: int = 2, prefix_length: int = 7,
                 cache_dir: str = CACHE_DIR):
        from symspellpy import SymSpell

        self.max_edit = max_edit
        digest = hashlib.sha1()
        for word in sorted(vocabulary):
            digest.update(word.encode("utf-8"))
        digest.update(f"{max_edit}/{prefix_length}".encode())
        cache_path = os.path.join(cache_dir, f"symspell-{digest.hexdigest()[:12]}.pickle")

        self._sym = SymSpell(max_dictionary_edit_distance=max_edit, prefix_length=prefix_length)
        if os.path.exists(cache_path):
            self._sym.load_pickle(cache_path)
        else:
            for word, count in vocabulary.items():
                self._sym.create_dictionary_entry(word, max(int(count), 1))
            os.makedirs(cache_dir, exist_ok=True)
            self._sym.save_pickle(cache_path)

    def candidates(self, query: str, max_distance: float = 2.0, limit: int = 60):
        from symspellpy import Verbosity

        items = self._sym.lookup(query, Verbosity.ALL, max_edit_distance=self.max_edit,
                                 include_unknown=False, transfer_casing=False)
        items.sort(key=lambda item: (item.distance, -item.count))
        scored = []
        for item in items[:limit]:
            dist = weighted_edit_distance(query, item.term)
            if dist <= max_distance:
                scored.append((item.term, dist))
        scored.sort(key=lambda pair: pair[1])
        return scored
