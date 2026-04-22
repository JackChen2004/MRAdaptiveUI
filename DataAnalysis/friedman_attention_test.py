import csv
import math
from pathlib import Path

import numpy as np
from scipy.stats import friedmanchisquare, wilcoxon

INPUT_CSV = Path("gaze_summary.csv")
ALPHA = 0.05

def load_avatar_attention(csv_path):
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        gaze_cols = [c for c in reader.fieldnames if c.startswith("gaze_second")]
        gaze_cols = sorted(gaze_cols, key=lambda x: int(x.replace("gaze_second", "")))

        data = {}
        for row in reader:
            pid = (row.get("Participant ID") or "").strip()
            cond = (row.get("condition") or "").strip()
            if not pid or cond not in {"C0", "C1", "C2"}:
                continue

            valid = 0
            avatar = 0
            for c in gaze_cols:
                v = (row.get(c) or "").strip()
                if not v:
                    continue
                valid += 1
                if v == "Avatar":
                    avatar += 1

            rate = (avatar / valid * 100.0) if valid > 0 else np.nan
            data.setdefault(pid, {})[cond] = rate

    complete = {
        pid: conds
        for pid, conds in data.items()
        if all(c in conds and not np.isnan(conds[c]) for c in ["C0", "C1", "C2"])
    }
    return complete

def summarize(arr):
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def wilcoxon_effect_r(x, y, w_stat):
    # Approximate z from Wilcoxon to report effect size
    d = x - y
    d = d[d != 0]
    n = len(d)
    if n == 0:
        return np.nan, 0

    mean_w = n * (n + 1) / 4.0
    sd_w = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    if sd_w == 0:
        return np.nan, n
    z = (w_stat - mean_w) / sd_w
    r = abs(z) / math.sqrt(n)
    return float(r), n


def run_test(data, alpha):
    pids = sorted(data.keys(), key=lambda x: int(x) if x.isdigit() else x)
    c0 = np.array([data[pid]["C0"] for pid in pids], dtype=float)
    c1 = np.array([data[pid]["C1"] for pid in pids], dtype=float)
    c2 = np.array([data[pid]["C2"] for pid in pids], dtype=float)

    stat, p = friedmanchisquare(c0, c1, c2)

    print("Friedman Test on Avatar Attention Rate")
    print(f"Participants (complete repeated measures): n = {len(pids)}")
    for cond, arr in [("C0", c0), ("C1", c1), ("C2", c2)]:
        s = summarize(arr)
        print(
            f"{cond}: mean={s['mean']:.3f}, median={s['median']:.3f}, "
            f"std={s['std']:.3f}, min={s['min']:.3f}, max={s['max']:.3f}"
        )

    print(f"\nFriedman chi-square = {stat:.4f}, p-value = {p:.6f}")

    if p < alpha:
        print(f"Result: Significant condition effect (p < {alpha}).")
    else:
        print(f"Result: Not significant (p >= {alpha}).")

    # Composite adaptive measure
    adaptive_arr = (c1 + c2) / 2.0

    # Adaptive > C0 wilcoxon
    w_stat, p_one_sided = wilcoxon(
        adaptive_arr, c0,
        zero_method="wilcox",
        alternative="greater",
        correction=False,
    )
    r, n_eff = wilcoxon_effect_r(adaptive_arr, c0, w_stat)

    s_adp = summarize(adaptive_arr)
    print(
        f"\nAdaptive = (C1 + C2) / 2: mean={s_adp['mean']:.3f}, "
        f"median={s_adp['median']:.3f}, std={s_adp['std']:.3f}, "
        f"min={s_adp['min']:.3f}, max={s_adp['max']:.3f}"
    )
    print("\nOne-sided Wilcoxon signed-rank test (Adaptive > C0):")
    print(
        f"W = {w_stat:.4f}, p_one_sided = {p_one_sided:.6f}, "
        f"effect_r = {r:.3f}, n_eff = {n_eff}"
    )


def main():
    data = load_avatar_attention(INPUT_CSV)
    run_test(data, alpha=ALPHA)


if __name__ == "__main__":
    main()
