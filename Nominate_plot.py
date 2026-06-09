"""
Read Most Nominated.csv and plot how often each nominee was picked.
Run from this folder: python Nominate_plot.py
Requires: matplotlib (pip install matplotlib)
"""

import csv
import os
import re
import sys
from collections import Counter

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Install matplotlib first: pip install matplotlib", file=sys.stderr)
    sys.exit(1)

# Same panel as Main.py — used to add MBTI when older CSV rows only have first names.
MBTI_BY_NAME = {
    "Arthur": "ISTJ",
    "Luna": "ENFP",
    "Victor": "ENTJ",
    "Mira": "INFJ",
    "Diego": "ESTP",
}

def _canonical_nominee_label(cell: str) -> str:
    """
    Turn a 'nominated' cell into a stable display key 'Name (MBTI)'.

    Handles cells that are already 'Name (TYPE)' and bare 'Name' from older CSVs.
    """
    raw = (cell or "").strip()
    if not raw:
        return ""
    m = re.match(r"^(.+?)\s*\(([A-Z]{4})\)\s*$", raw)
    if m:
        base, mbti = m.group(1).strip(), m.group(2)
        return f"{base} ({mbti})"
    if raw in MBTI_BY_NAME:
        return f"{raw} ({MBTI_BY_NAME[raw]})"
    return raw

def load_nomination_counts(csv_path: str) -> Counter[str]:
    """
    Count non-empty values in the 'nominated' column (one count per row).
    Keys are normalized 'Name (MBTI)' so old and new CSV formats merge correctly.
    """
    counts: Counter[str] = Counter()
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            label = _canonical_nominee_label(row.get("nominated") or "")
            if label:
                counts[label] += 1
    return counts

def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "Most Nominated.csv")

    if not os.path.isfile(csv_path):
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    counts = load_nomination_counts(csv_path)
    if not counts:
        print("No non-empty 'nominated' rows found.", file=sys.stderr)
        sys.exit(1)

    # Highest counts first so the chart reads like a simple leaderboard.
    names = sorted(counts.keys(), key=lambda n: counts[n], reverse=True)
    values = [counts[n] for n in names]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(names, values, color="steelblue", edgecolor="white", linewidth=0.8)
    ax.set_xlabel("Nominee (MBTI)")
    ax.set_ylabel("Number of nominations")
    ax.set_title("Nomination frequency")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    for i, v in enumerate(values):
        ax.text(i, v, str(v), ha="center", va="bottom", fontsize=10)
    fig.tight_layout()

    out_path = os.path.join(base_dir, "nomination_frequency.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.show()

if __name__ == "__main__":
    main()
