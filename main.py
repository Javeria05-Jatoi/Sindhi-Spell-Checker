# main.py  (Day 9 demo entry point, CLI arguments added Phase 2)
#   python main.py                      # demo sentence
#   python main.py "سنڌى ٻولي"           # check your own text
#   python main.py --file input.txt     # check a file
#   python main.py --fix --file in.txt  # print the text with top suggestions applied
import argparse
import sys

from src.spellchecker import SpellChecker

DEMO = "سنڌى ٻوللي ڪتاپ"


def main():
    parser = argparse.ArgumentParser(description="Sindhi spell checker")
    parser.add_argument("text", nargs="?", help="Sindhi text to check")
    parser.add_argument("--file", help="read the text from this UTF-8 file")
    parser.add_argument("--fix", action="store_true", help="print the corrected text only")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.text or DEMO

    checker = SpellChecker()
    if args.fix:
        print(checker.corrected_text(text))
        return
    print(f"Loaded {len(checker.dictionary)} dictionary entries.\n")

    for item in checker.check_text(text):
        if item["status"] == "skip":
            continue
        status = "OK" if item["known"] else "UNKNOWN"
        if item.get("warning"):
            status = "CHECK (fits the sentence badly)"
        print(f"{item['token']:20s} [{status}]")
        for s in item["suggestions"]:
            print(f"    -> {s['word']}  (distance={s['distance']:.2f}, freq={s['frequency']})")


if __name__ == "__main__":
    main()
