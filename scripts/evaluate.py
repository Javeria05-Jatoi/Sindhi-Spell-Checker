# scripts/evaluate.py  (Day 12, per-error-type + context eval added Phase 2)
#
# python scripts/evaluate.py                       # test split, both test files
# python scripts/evaluate.py --split dev
# python scripts/evaluate.py --test-path data/test_words_gold.json --split all
import argparse
import json
import os
import statistics
import sys
import time
from collections import defaultdict

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from src.normalization import lookup_key  # noqa: E402
from src.spellchecker import SpellChecker  # noqa: E402


def load_cases(path, split):
    with open(path, encoding="utf-8") as f:
        cases = [c for c in json.load(f) if c.get("misspelled")]  # skip unfilled rows
    if split != "all":
        cases = [c for c in cases if c.get("split", "test") == split]
    return cases


def evaluate_cases(checker, cases, use_context=True):
    """Returns a metrics dict; prints nothing (scripts/tune.py reuses it)."""
    tp = fp = fn = tn = 0
    by_type = defaultdict(lambda: [0, 0, 0, 0])  # n, top1, top3, top5
    latencies = []
    top_n = checker.top_n
    checker.top_n = 5
    try:
        for case in cases:
            is_actually_misspelled = case["correct"] is not None
            flagged = not checker.dictionary.is_known(case["misspelled"])
            if is_actually_misspelled and flagged:
                tp += 1
            elif is_actually_misspelled:
                fn += 1
            elif flagged:
                fp += 1
            else:
                tn += 1
            if not (is_actually_misspelled and flagged):
                continue
            t = time.perf_counter()
            prev, nxt = (case.get("prev"), case.get("next")) if use_context else (None, None)
            suggestions = [s["word"] for s in checker.suggest(case["misspelled"], prev, nxt)]
            latencies.append((time.perf_counter() - t) * 1000)
            correct = lookup_key(case["correct"])
            row = by_type[case["error_type"]]
            row[0] += 1
            row[1] += suggestions[:1] == [correct]
            row[2] += correct in suggestions[:3]
            row[3] += correct in suggestions[:5]
    finally:
        checker.top_n = top_n

    total = tp + fp + fn + tn
    n = sum(r[0] for r in by_type.values())
    return {
        "cases": total,
        "accuracy": (tp + tn) / total if total else 0,
        "precision": tp / (tp + fp) if tp + fp else 0,
        "recall": tp / (tp + fn) if tp + fn else 0,
        "false_alarm_rate": fp / (fp + tn) if fp + tn else None,
        "top1": sum(r[1] for r in by_type.values()) / n if n else 0,
        "top3": sum(r[2] for r in by_type.values()) / n if n else 0,
        "top5": sum(r[3] for r in by_type.values()) / n if n else 0,
        "by_type": {k: {"n": r[0], "top1": r[1] / r[0], "top3": r[2] / r[0], "top5": r[3] / r[0]}
                    for k, r in sorted(by_type.items())},
        "latency_ms": statistics.mean(latencies) if latencies else 0,
    }


def print_report(title, m):
    print(f"\n## {title}  ({m['cases']} cases)")
    print(f"Detection  accuracy {m['accuracy']:.1%}  precision {m['precision']:.1%}  "
          f"recall {m['recall']:.1%}" + (f"  false-alarm rate {m['false_alarm_rate']:.1%}"
                                          if m["false_alarm_rate"] is not None else ""))
    print(f"Correction top-1 {m['top1']:.1%}  top-3 {m['top3']:.1%}  top-5 {m['top5']:.1%}  "
          f"(mean {m['latency_ms']:.1f} ms/word)")
    print("| error type | n | top-1 | top-3 | top-5 |")
    print("|---|---|---|---|---|")
    for k, r in m["by_type"].items():
        print(f"| {k} | {r['n']} | {r['top1']:.1%} | {r['top3']:.1%} | {r['top5']:.1%} |")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-path", default=None)
    parser.add_argument("--split", default="test", choices=["dev", "test", "all"])
    parser.add_argument("--no-context", action="store_true")
    parser.add_argument("--save", action="store_true", help="write docs/results.json (shown in the web UI)")
    args = parser.parse_args()

    checker = SpellChecker()
    paths = [args.test_path] if args.test_path else ["data/test_words.json", "data/test_context.json"]
    saved = {"split": args.split}
    for path in paths:
        if not os.path.exists(path):
            print(f"(missing {path} -- run scripts/make_test_set.py)")
            continue
        cases = load_cases(path, args.split)
        metrics = evaluate_cases(checker, cases, use_context=not args.no_context)
        print_report(f"{path} [{args.split}]", metrics)
        saved["context" if "context" in path else "words"] = metrics
    if args.save:
        with open("docs/results.json", "w", encoding="utf-8") as f:
            json.dump(saved, f, indent=1)
        print("\nSaved docs/results.json")


if __name__ == "__main__":
    main()
