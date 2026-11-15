# scripts/eval_real_word.py  (Phase 3b)
# Measures the real-word error detector (SpellChecker.real_word_check):
#   * false alarms: how often it flags a word in CLEAN held-out Wikipedia text
#   * recall: how often it catches a word swapped for a near-identical real word
# Writes docs/real_word_results.json.
import json
import random
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from scripts.build_corpus_stats import WIKI_PATH, _SEGMENT_BREAK, iter_wikipedia  # noqa: E402
from src.normalization import lookup_key  # noqa: E402
from src.spellchecker import SpellChecker  # noqa: E402

N_SEGMENTS = 400


def main():
    rng = random.Random(7)
    checker = SpellChecker()
    if len(sys.argv) > 2:  # python scripts/eval_real_word.py <min_gain> <min_freq_ratio>
        checker.REAL_WORD_MIN_GAIN = float(sys.argv[1])
        checker.REAL_WORD_MIN_FREQ_RATIO = float(sys.argv[2])
    segments = []
    for text in iter_wikipedia(WIKI_PATH, holdout=True):
        for seg in _SEGMENT_BREAK.split(text):
            if len(seg.split()) >= 6:
                segments.append(seg)
                break
        if len(segments) >= N_SEGMENTS:
            break

    checked = flagged = 0
    swaps = caught = 0
    examples = []
    for seg in segments:
        results = checker.check_text(seg)
        words = [r for r in results if r["status"] in ("lexicon", "corpus")]
        checked += len(words)
        flagged += sum(1 for r in words if r.get("warning"))
        # swap one interior word for a real word one edit away, then see if it's caught
        sindhi = [r for r in results if r["status"] != "skip"]
        if len(sindhi) < 3:
            continue
        i = rng.randrange(1, len(sindhi) - 1)
        target = sindhi[i]
        if target["status"] != "lexicon":
            continue
        options = [w for w, d in checker._candidates(lookup_key(target["token"]))
                   if 0 < d <= 1.0 and checker.dictionary.status(w) == "lexicon"]
        if not options:
            continue
        swapped_word = rng.choice(options)
        swapped = seg[:target["start"]] + swapped_word + seg[target["end"]:]
        swaps += 1
        hit = any(r.get("warning") and lookup_key(r["token"]) == swapped_word
                  and r["suggestions"][0]["word"] == lookup_key(target["token"])
                  for r in checker.check_text(swapped))
        caught += hit
        if hit and len(examples) < 5:
            examples.append(f"{swapped_word} -> {lookup_key(target['token'])}")

    report = {"clean_words_checked": checked, "false_alarm_rate": flagged / max(checked, 1),
              "swaps": swaps, "recall": caught / max(swaps, 1), "examples": examples,
              "min_gain_nats": checker.REAL_WORD_MIN_GAIN,
              "min_freq_ratio": checker.REAL_WORD_MIN_FREQ_RATIO}
    print(json.dumps(report, ensure_ascii=False, indent=1))
    out = "docs/real_word_results.json" if len(sys.argv) <= 2 else \
        f"data/cache/real_word_{sys.argv[1]}_{sys.argv[2]}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
