# src/spellchecker.py  (Day 9, SymSpell + context ranking added Phase 1-3)
from src.candidate_generator import SymSpellIndex, generate_candidates
from src.context_model import BigramModel
from src.dictionary import Dictionary
from src.normalization import lookup_key
from src.ranking import rank_candidates
from src.tokenizer import tokenize, tokenize_with_spans

MAX_PHRASE_LEN = 3


class SpellChecker:
    """Public API. Any UI (CLI, Streamlit, web...) should only ever
    call these methods -- never reach into src/ internals directly."""

    def __init__(self, dictionary_path: str = "data/dictionary.json",
                 max_distance: float = 2.0, top_n: int = 3, use_index: bool = True):
        self.dictionary = Dictionary(dictionary_path)
        self.max_distance = max_distance
        self.top_n = top_n
        self._vocab = self.dictionary.candidate_vocabulary()
        self._words = list(self._vocab)
        self._index = SymSpellIndex(self._vocab) if use_index else None
        self.context = BigramModel(self._vocab)

    def _candidates(self, word: str) -> list:
        key = lookup_key(word)
        if self._index is not None:
            return self._index.candidates(key, self.max_distance)
        return generate_candidates(key, self._words, self.max_distance)

    def suggest(self, word: str, prev: str = None, nxt: str = None) -> list:
        """Top-N corrections for one word; prev/nxt are its neighbours, if any."""
        candidates = self._candidates(word)
        context_scores = None
        if self.context.available and (prev or nxt):
            context_scores = {
                w: self.context.context_score(w, lookup_key(prev) if prev else None,
                                              lookup_key(nxt) if nxt else None)
                for w, _ in candidates
            }
        return rank_candidates(candidates, self.dictionary, self.max_distance, self.top_n,
                               context_scores=context_scores)

    def check_text(self, text: str) -> list:
        """Return a list of {token, known, suggestions, start, end, status} dicts,
        one per token. `start`/`end` are offsets into the original text."""
        spans = tokenize_with_spans(text)
        keys = [lookup_key(tok) if is_sindhi else None for tok, _, _, is_sindhi in spans]

        # Phase 1: multi-word dictionary headwords ("اک ڇنڀ") count as known
        in_phrase = [False] * len(spans)
        for size in range(MAX_PHRASE_LEN, 1, -1):
            for i in range(len(spans) - size + 1):
                window = keys[i:i + size]
                if all(window) and not any(in_phrase[i:i + size]) \
                        and self.dictionary.is_phrase(window):
                    for j in range(i, i + size):
                        in_phrase[j] = True

        results = []
        for i, (token, start, end, is_sindhi) in enumerate(spans):
            entry = {"token": token, "start": start, "end": end, "known": True,
                     "status": "skip", "suggestions": []}
            if is_sindhi:
                status = "phrase" if in_phrase[i] else self.dictionary.status(token)
                entry["status"] = status
                entry["known"] = status != "unknown"
                prev = spans[i - 1][0] if i > 0 and spans[i - 1][3] else None
                nxt = spans[i + 1][0] if i + 1 < len(spans) and spans[i + 1][3] else None
                if not entry["known"]:
                    entry["suggestions"] = self.suggest(token, prev, nxt)
                elif status in ("lexicon", "corpus") and prev and nxt:
                    better = self.real_word_check(token, prev, nxt)
                    if better:
                        entry["warning"] = "context"
                        entry["suggestions"] = better
            results.append(entry)
        return results

    # --- Phase 3b: real-word errors ("مهمن نواز" -> "مهمان نواز") ----------------
    REAL_WORD_MAX_DISTANCE = 1.0
    # thresholds from scripts/eval_real_word.py: 4/5 flagged 2.7 % of clean words,
    # 8/50 flags 0.8 % and still catches about half of real-word swaps
    REAL_WORD_MIN_GAIN = 8.0       # log-prob margin (nats) the alternative must win by
    REAL_WORD_MIN_FREQ_RATIO = 50  # ...and it must be this many times more common
    REAL_WORD_MIN_LETTERS = 2

    def real_word_check(self, token: str, prev: str, nxt: str):
        """If a correctly spelled word fits its neighbours far worse than a
        near-identical word, return suggestions (alternative first)."""
        if not self.context.available:
            return None
        key, prev_key, next_key = lookup_key(token), lookup_key(prev), lookup_key(nxt)
        if len(key) < self.REAL_WORD_MIN_LETTERS:
            return None
        own = self.context.context_score(key, prev_key, next_key)
        own_freq = self.dictionary.frequency(key)
        best = None
        for word, dist in self._candidates(key):
            if word == key or dist > self.REAL_WORD_MAX_DISTANCE or len(word) < self.REAL_WORD_MIN_LETTERS:
                continue
            gain = self.context.context_score(word, prev_key, next_key) - own
            if gain >= self.REAL_WORD_MIN_GAIN and \
                    self.dictionary.frequency(word) >= self.REAL_WORD_MIN_FREQ_RATIO * max(own_freq, 1):
                if best is None or gain > best[1]:
                    best = (word, gain, dist)
        if best is None:
            return None
        return [{"word": best[0], "distance": best[2], "frequency": self.dictionary.frequency(best[0]),
                 "score": -best[1]},
                {"word": key, "distance": 0.0, "frequency": own_freq, "score": 0.0}]

    def corrected_text(self, text: str) -> str:
        """Apply the top suggestion to every unknown word."""
        out, last = [], 0
        for item in self.check_text(text):
            if not item["known"] and item["suggestions"]:
                out.append(text[last:item["start"]])
                out.append(item["suggestions"][0]["word"])
                last = item["end"]
        out.append(text[last:])
        return "".join(out)

    def meanings(self, word: str) -> list:
        return self.dictionary.get_meanings(word)

    def tokens(self, text: str) -> list:
        return tokenize(text)
