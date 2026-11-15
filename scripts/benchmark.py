# scripts/benchmark.py  (Phase 1)
# Times SpellChecker load + suggest() on a fixed mix of known/unknown words.
import statistics
import sys
import time

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from src.spellchecker import SpellChecker  # noqa: E402

WORDS = [
    "ڪتاب", "ڪتب", "سنڌى", "پاڻي", "ماڻهو", "گهر", "اسڪول", "دنيا", "پيار", "زندگي",
    "ڪتاب" + "ي", "سنڌ" + "ڙ", "پاڻ", "ماڻهن", "گهرو", "اسڪل", "دنيان", "پيارو", "زندگى", "سنڌی",
]


def main():
    t0 = time.perf_counter()
    checker = SpellChecker()
    load = time.perf_counter() - t0
    times = []
    for w in WORDS:
        t = time.perf_counter()
        checker.suggest(w)
        times.append((time.perf_counter() - t) * 1000)
    times.sort()
    print(f"Dictionary keys: {len(checker.dictionary)}")
    print(f"Load time:       {load:.2f} s")
    print(f"suggest() mean:  {statistics.mean(times):.1f} ms")
    print(f"suggest() p95:   {times[int(0.95 * (len(times) - 1))]:.1f} ms")


if __name__ == "__main__":
    main()
