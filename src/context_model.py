# src/context_model.py  (Phase 3b, CPU version)
# A small bigram language model built from Sindhi Wikipedia + CC-100
# (scripts/build_corpus_stats.py). Used to re-rank spelling suggestions by the
# words around them: "ڪتاب پڙهي" vs "ڪتب پڙهي".

import gzip
import math
import os

BIGRAMS_PATH = "data/bigrams.tsv.gz"
SMOOTHING_K = 5.0  # pseudo-count mass given to the unigram backoff


class BigramModel:
    def __init__(self, unigrams: dict, bigrams_path: str = BIGRAMS_PATH):
        self.unigrams = unigrams
        self.total = sum(unigrams.values()) or 1
        self.vocab_size = len(unigrams) or 1
        self.bigrams = {}
        self.left_counts = {}
        if bigrams_path and os.path.exists(bigrams_path):
            with gzip.open(bigrams_path, "rt", encoding="utf-8") as f:
                for line in f:
                    pair, _, count = line.rstrip("\n").rpartition("\t")
                    if pair:
                        self.bigrams[pair] = int(count)
            for pair, count in self.bigrams.items():
                left = pair.partition(" ")[0]
                self.left_counts[left] = self.left_counts.get(left, 0) + count

    @property
    def available(self) -> bool:
        return bool(self.bigrams)

    def unigram_logprob(self, word: str) -> float:
        return math.log((self.unigrams.get(word, 0) + 0.5) / (self.total + 0.5 * self.vocab_size))

    def logprob(self, word: str, prev: str) -> float:
        """log P(word | prev), interpolated with the unigram distribution."""
        p_uni = math.exp(self.unigram_logprob(word))
        pair = self.bigrams.get(f"{prev} {word}", 0)
        left = self.left_counts.get(prev, 0)
        return math.log((pair + SMOOTHING_K * p_uni) / (left + SMOOTHING_K))

    def context_score(self, candidate: str, prev=None, nxt=None) -> float:
        """log P(candidate | prev) + log P(next | candidate); unigram if no neighbours."""
        score = self.logprob(candidate, prev) if prev else self.unigram_logprob(candidate)
        if nxt:
            score += self.logprob(nxt, candidate)
        return score
