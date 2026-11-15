# src/sindhi_cost_model.py  (Day 6, revised Phase 1/2)
#
# STATUS: project assumption, tuned on a synthetic dev set (Phase 2) --
# NOT a verified confusability study.
# See docs/cost_table_assumptions.md before quoting these numbers anywhere.

# Structural similarity groups: letters built on the same undotted base shape,
# i.e. they differ only in dots. Phase 1 added the Sindhi letters the Day-6
# table was missing (ڙ ڻ ڌ ڍ ڎ ڃ ...) and the remaining shared-shape families.
STRUCTURAL_GROUPS = [
    {"ب", "ٻ", "ڀ", "پ", "ت", "ٿ", "ٽ",
     "ٺ", "ث", "ٹ"},                                    # be/te-family (ب ٻ ڀ پ ت ٿ ٽ ٺ ث ٹ)
    {"ج", "ڄ", "ڃ", "چ", "ڇ", "ح", "خ"},  # jim-family (ج ڄ ڃ چ ڇ ح خ)
    {"د", "ڌ", "ڏ", "ڊ", "ڍ", "ڎ", "ذ",
     "ڈ", "ډ"},                                              # dal-family (د ڌ ڏ ڊ ڍ ڎ ذ ڈ ډ)
    {"ر", "ڙ", "ز", "ڑ"},                          # re-family (ر ڙ ز ڑ)
    {"س", "ش"},                                              # seen/sheen
    {"ص", "ض"},                                              # sad/dad
    {"ط", "ظ"},                                              # tah/zah
    {"ع", "غ"},                                              # ain/ghain
    {"ف", "ڦ", "ق"},                                    # fe-family (ف ڦ ق)
    {"ڪ", "ک"},                                              # kaf/keheh
    {"گ", "ڳ", "ڱ"},                                    # gaf-family (گ ڳ ڱ)
    {"ن", "ڻ"},                                              # nun/rnoon (ن ڻ)
    {"ه", "ھ"},                                              # heh/do-chashmi heh (ه ھ)
    {"ي", "ئ"},                                              # ye/ye-hamza (ي ئ)
    {"ا", "آ", "أ", "إ"},                          # alif-family (ا آ أ إ)
    {"و", "ؤ"},                                              # waw/waw-hamza (و ؤ)
]

# Phase 1: letters that SOUND the same in Sindhi, so writers mix them up even
# though they look different (Arabic loan spellings).
PHONETIC_GROUPS = [
    {"س", "ص", "ث"},                    # s: س ص ث
    {"ز", "ذ", "ض", "ظ"},          # z: ز ذ ض ظ
    {"ت", "ط"},                              # t: ت ط
    {"ح", "ه"},                              # h: ح ه
    {"ع", "ا", "ء"},                    # glottal: ع ا ء
    {"ق", "ڪ"},                              # q/k: ق ڪ
    {"ب", "ٻ"}, {"ج", "ڄ"},        # plain vs implosive
    {"د", "ڏ"}, {"گ", "ڳ"},
    {"ڻ", "ن"},                              # ڻ ن
]

# Long vowels / weak letters are often dropped or added.
WEAK_LETTERS = {"ا", "و", "ي", "ء", "ئ", "ه", "ھ"}

DEFAULT_SUBSTITUTION_COST = 1.0
STRUCTURAL_GROUP_COST = 0.6  # tuned on the dev split (scripts/tune.py), was 0.5
PHONETIC_GROUP_COST = 0.5
DEFAULT_INDEL_COST = 1.0
WEAK_LETTER_INDEL_COST = 0.7


def _index(groups):
    lookup = {}
    for group in groups:
        for ch in group:
            lookup.setdefault(ch, set()).update(group)
    return lookup


_group_lookup = _index(STRUCTURAL_GROUPS)
_phonetic_lookup = _index(PHONETIC_GROUPS)


def substitution_cost(a_char: str, b_char: str) -> float:
    if a_char == b_char:
        return 0.0
    if b_char in _group_lookup.get(a_char, ()):
        return STRUCTURAL_GROUP_COST
    if b_char in _phonetic_lookup.get(a_char, ()):
        return PHONETIC_GROUP_COST
    return DEFAULT_SUBSTITUTION_COST


def indel_cost(char: str) -> float:
    """Phase 1: cost of inserting or deleting one letter."""
    return WEAK_LETTER_INDEL_COST if char in WEAK_LETTERS else DEFAULT_INDEL_COST


def configure(structural=None, phonetic=None, weak_indel=None):
    """Phase 2: override costs (used by the tuning script)."""
    global STRUCTURAL_GROUP_COST, PHONETIC_GROUP_COST, WEAK_LETTER_INDEL_COST
    if structural is not None:
        STRUCTURAL_GROUP_COST = structural
    if phonetic is not None:
        PHONETIC_GROUP_COST = phonetic
    if weak_indel is not None:
        WEAK_LETTER_INDEL_COST = weak_indel
