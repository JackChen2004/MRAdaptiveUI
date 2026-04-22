from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

INPUT_CSV = Path("output/subjective_construct_scores.csv")
OUTPUT_CSV = Path("output/subjective_construct_wilcoxon_vs_neutral.csv")

CONSTRUCTS = [
    "ui_visibility_movement_score",
    "avatar_interaction_score",
    "comfort_presence_score",
]
NEUTRAL = 3

def scores_wilcoxon(values, neutral=NEUTRAL):
    values = pd.to_numeric(values, errors="coerce").dropna()
    diffs = values - neutral
    diffs = diffs[diffs != 0]
    if len(diffs) == 0:
        return np.nan, np.nan, 0
    stat, p = wilcoxon(diffs, alternative="greater")
    return stat, p, len(diffs)

def main():
    df = pd.read_csv(INPUT_CSV)

    rows = []
    for col in CONSTRUCTS:
        if col not in df.columns:
            raise KeyError(f"Missing construct column: {col}")
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        stat, p, n_nonzero = scores_wilcoxon(s, neutral=NEUTRAL)
        rows.append({
            "construct": col,
            "neutral_value": NEUTRAL,
            "n": len(s),
            "mean": s.mean(),
            "median": s.median(),
            "wilcoxon_statistic": stat,
            "p_value_one_sided_greater": p,
            "n_nonzero_differences": n_nonzero,
        })

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print("Wilcoxon signed-rank test (H1: score > Neutral=3):")
    for row in rows:
        print(
            f"  {row['construct']}: "
            f"n={row['n']}, mean={row['mean']:.3f}, median={row['median']:.3f}, "
            f"W={row['wilcoxon_statistic']}, p={row['p_value_one_sided_greater']}"
        )
    print(f"\nSaved: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
