# scripts/eval_baseline.py  (Phase 2)
# Scores the ORIGINAL Day-15 code (git commit ec34d1f) on today's test sets,
# so docs/results.md can show an honest before/after. Slow (~1.6 s/word).
import json
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
BASE_COMMIT = "ec34d1f"
OUT_DIR = "data/cache/baseline"
FILES = ["src/__init__.py", "src/normalization.py", "src/tokenizer.py", "src/dictionary.py",
         "src/edit_distance.py", "src/sindhi_cost_model.py", "src/candidate_generator.py",
         "src/ranking.py", "src/spellchecker.py"]


def extract():
    for path in FILES:
        dest = os.path.join(OUT_DIR, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        blob = subprocess.run(["git", "show", f"{BASE_COMMIT}:{path}"], capture_output=True, check=True).stdout
        with open(dest, "wb") as f:
            f.write(blob)


def main():
    extract()
    sys.path.insert(0, OUT_DIR)
    from src.spellchecker import SpellChecker  # the OLD package
    from src.normalization import normalize
    import re
    strip = lambda w: re.sub("[ً-ٰٟ]", "", normalize(w))  # compare without vowel marks

    checker = SpellChecker("data/dictionary.json")
    report = {}
    for path in ["data/test_words.json", "data/test_context.json"]:
        cases = [c for c in json.load(open(path, encoding="utf-8")) if c.get("split") == "test"]
        n = flagged_ok = top1 = top3 = top5 = fa = negatives = 0
        t0 = time.time()
        for c in cases:
            known = checker.dictionary.is_known(c["misspelled"])
            if c["correct"] is None:
                negatives += 1
                fa += not known
                continue
            n += 1
            if known:
                continue
            flagged_ok += 1
            sugs = [strip(s["word"]) for s in checker.suggest(c["misspelled"])]
            top1 += sugs[:1] == [c["correct"]]
            top3 += c["correct"] in sugs[:3]
            top5 += c["correct"] in sugs[:5]
        report[path] = {"n": n, "recall": flagged_ok / n, "top1": top1 / n, "top3": top3 / n,
                        "top5": top5 / n, "false_alarm_rate": fa / negatives if negatives else None,
                        "seconds_per_word": (time.time() - t0) / max(flagged_ok, 1)}
        print(path, json.dumps(report[path]))
    with open("docs/baseline_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)


if __name__ == "__main__":
    main()
