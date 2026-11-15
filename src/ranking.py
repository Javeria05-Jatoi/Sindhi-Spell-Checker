# src/ranking.py  (Day 8, log-frequency + context added Phase 2/3)
import math

# Tuned on the synthetic dev split (scripts/tune.py); see docs/results.md.
DEFAULT_W_DIST = 0.8
DEFAULT_W_FREQ = 0.2
DEFAULT_W_CTX = 0.2


def rank_candidates(candidates: list, dictionary, max_distance: float = 2.0,
                     top_n: int = 3, w_dist: float = None, w_freq: float = None,
                     context_scores: dict = None, w_ctx: float = None) -> list:
    """candidates: [(word, distance), ...] from Day 7.
    dictionary: a Day-4 Dictionary instance, used for frequency lookup.
    context_scores: optional {word: log-prob of the word in its sentence}
    (src/context_model.py). Lower score = better suggestion."""
    if not candidates:
        return []
    w_dist = DEFAULT_W_DIST if w_dist is None else w_dist
    w_freq = DEFAULT_W_FREQ if w_freq is None else w_freq
    w_ctx = DEFAULT_W_CTX if w_ctx is None else w_ctx

    frequencies = [dictionary.frequency(w) for w, _ in candidates]
    # Phase 2: log scale, so a handful of very common words can't dominate
    max_log_freq = max(math.log1p(f) for f in frequencies) or 1.0
    best_ctx = max(context_scores.values()) if context_scores else 0.0

    scored = []
    for (word, dist), freq in zip(candidates, frequencies):
        norm_dist = dist / max_distance if max_distance > 0 else 0
        norm_freq = math.log1p(freq) / max_log_freq
        score = w_dist * norm_dist - w_freq * norm_freq
        if context_scores:
            # gap to the best-fitting candidate, ~0..1 for typical log-prob gaps
            score += w_ctx * (best_ctx - context_scores.get(word, best_ctx - 10)) / 10
        scored.append((word, dist, freq, score))

    scored.sort(key=lambda row: row[3])
    return [{"word": w, "distance": d, "frequency": f, "score": s}
            for w, d, f, s in scored[:top_n]]
