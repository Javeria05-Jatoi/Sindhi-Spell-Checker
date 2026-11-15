# data/build_alphabet_reference.py
# Produces data/sindhi_alphabet_ref.json from the adopted 52-letter convention.
# Source: Wikipedia "Sindhi alphabet" letter listing; Unicode Arabic block code points.
# NOTE: this is a project convention (see Day 1 write-up in the PDF guide), not a
# universal linguistic count. jjhe/gghe are 2-code-point digraphs treated as ONE letter.

import json

SINDHI_LETTERS = [
    {"letter": "\u0627", "name": "alif"},
    {"letter": "\u0628", "name": "be"},
    {"letter": "\u067B", "name": "bbe (implosive b)"},
    {"letter": "\u0680", "name": "bhe"},
    {"letter": "\u067E", "name": "pe"},
    {"letter": "\u062A", "name": "te"},
    {"letter": "\u067F", "name": "tteheh (Sindhi-specific)"},
    {"letter": "\u067D", "name": "teheh two dots above (Sindhi-specific)"},
    {"letter": "\u067A", "name": "tteheh / the (Sindhi-specific)"},
    {"letter": "\u062B", "name": "se"},
    {"letter": "\u062C", "name": "jim"},
    {"letter": "\u0684", "name": "jje (implosive j, Sindhi-specific)"},
    {"letter": "\u062C\u0647\u06BE", "name": "jjhe (aspirate digraph, Sindhi-specific)"},
    {"letter": "\u0683", "name": "nyeh / je (Sindhi-specific)"},
    {"letter": "\u0686", "name": "che"},
    {"letter": "\u0687", "name": "cche (Sindhi-specific)"},
    {"letter": "\u062D", "name": "hah"},
    {"letter": "\u062E", "name": "khah"},
    {"letter": "\u062F", "name": "dal"},
    {"letter": "\u0688", "name": "ddal (Sindhi-specific)"},
    {"letter": "\u068F", "name": "dde (implosive d, Sindhi-specific)"},
    {"letter": "\u068A", "name": "dahal (Sindhi-specific)"},
    {"letter": "\u0689", "name": "dhal (Sindhi-specific)"},
    {"letter": "\u0630", "name": "zal"},
    {"letter": "\u0631", "name": "re"},
    {"letter": "\u0691", "name": "rre (Sindhi-specific)"},
    {"letter": "\u0632", "name": "ze"},
    {"letter": "\u0633", "name": "sin"},
    {"letter": "\u0634", "name": "shin"},
    {"letter": "\u0635", "name": "sad"},
    {"letter": "\u0636", "name": "dad"},
    {"letter": "\u0637", "name": "tah"},
    {"letter": "\u0638", "name": "zah"},
    {"letter": "\u0639", "name": "ain"},
    {"letter": "\u063A", "name": "ghain"},
    {"letter": "\u0641", "name": "fe"},
    {"letter": "\u06A6", "name": "phe (Sindhi-specific)"},
    {"letter": "\u0642", "name": "qaf"},
    {"letter": "\u06AA", "name": "kaf / kaaf"},
    {"letter": "\u06A9", "name": "keheh"},
    {"letter": "\u06AF", "name": "gaf"},
    {"letter": "\u06B3", "name": "gge (implosive g, Sindhi-specific)"},
    {"letter": "\u06AF\u0647\u06BE", "name": "gghe (aspirate digraph, Sindhi-specific)"},
    {"letter": "\u06B1", "name": "ngeh (Sindhi-specific)"},
    {"letter": "\u0644", "name": "lam"},
    {"letter": "\u0645", "name": "mim"},
    {"letter": "\u0646", "name": "nun"},
    {"letter": "\u0655", "name": "nnah (Sindhi-specific, retroflex n)"},
    {"letter": "\u0648", "name": "wau"},
    {"letter": "\u06BE", "name": "he (do-chashmi)"},
    {"letter": "\u0621", "name": "hamza"},
    {"letter": "\u064A", "name": "ye"},
]


def build(out_path="data/sindhi_alphabet_ref.json"):
    assert len(SINDHI_LETTERS) == 52, "Adopted convention expects 52 entries"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(SINDHI_LETTERS, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(SINDHI_LETTERS)} letters to {out_path}")


if __name__ == "__main__":
    build()
