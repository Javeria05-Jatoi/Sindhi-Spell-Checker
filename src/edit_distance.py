# src/edit_distance.py  (Day 5 baseline, Day 6 weighted extension)
from src.normalization import to_grapheme_clusters
from src.sindhi_cost_model import indel_cost, substitution_cost


def levenshtein_table(a: str, b: str) -> int:
    """Reference DP implementation (clear, O(m*n) space). Operates on grapheme
    clusters (Day 2) so a Sindhi digraph letter counts as ONE edit unit."""
    ca, cb = to_grapheme_clusters(a), to_grapheme_clusters(b)
    m, n = len(ca), len(cb)
    D = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        D[i][0] = i
    for j in range(n + 1):
        D[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ca[i - 1] == cb[j - 1]:
                D[i][j] = D[i - 1][j - 1]
            else:
                D[i][j] = 1 + min(D[i - 1][j], D[i][j - 1], D[i - 1][j - 1])
    return D[m][n]


def levenshtein(a: str, b: str) -> int:
    """Space-optimized version: O(min(m,n)) memory, same result as levenshtein_table."""
    ca, cb = to_grapheme_clusters(a), to_grapheme_clusters(b)
    if len(ca) < len(cb):
        ca, cb = cb, ca
    previous_row = list(range(len(cb) + 1))
    for i, ca_char in enumerate(ca, start=1):
        current_row = [i] + [0] * len(cb)
        for j, cb_char in enumerate(cb, start=1):
            if ca_char == cb_char:
                current_row[j] = previous_row[j - 1]
            else:
                current_row[j] = 1 + min(previous_row[j], current_row[j - 1], previous_row[j - 1])
        previous_row = current_row
    return previous_row[-1]


TRANSPOSITION_COST = 0.6  # Phase 1: swapped adjacent letters are a common typo (tuned)


def weighted_edit_distance(a: str, b: str, cost_fn=substitution_cost,
                            ins_cost=indel_cost, del_cost=indel_cost) -> float:
    """Day 6: substitution cost depends on which two characters are involved,
    using the Sindhi structural-similarity groups in sindhi_cost_model.py.
    Phase 1: weak letters (ا و ي ...) are cheaper to insert/delete, and an
    adjacent transposition counts as one edit (Damerau)."""
    ca, cb = to_grapheme_clusters(a), to_grapheme_clusters(b)
    m, n = len(ca), len(cb)
    D = [[0.0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        D[i][0] = D[i - 1][0] + del_cost(ca[i - 1])
    for j in range(1, n + 1):
        D[0][j] = D[0][j - 1] + ins_cost(cb[j - 1])
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            best = min(
                D[i - 1][j] + del_cost(ca[i - 1]),
                D[i][j - 1] + ins_cost(cb[j - 1]),
                D[i - 1][j - 1] + cost_fn(ca[i - 1], cb[j - 1]),
            )
            if (i > 1 and j > 1 and ca[i - 1] == cb[j - 2]
                    and ca[i - 2] == cb[j - 1] and ca[i - 1] != cb[j - 1]):
                best = min(best, D[i - 2][j - 2] + TRANSPOSITION_COST)
            D[i][j] = best
    return D[m][n]


if __name__ == "__main__":
    print("kitten -> sitting:", levenshtein("kitten", "sitting"))  # expect 3
