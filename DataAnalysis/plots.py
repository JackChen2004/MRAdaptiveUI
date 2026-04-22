import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Paths and constants
GAZE_CSV = Path("gaze_summary.csv")
OUTPUT_DIR = Path("output")

SUBJ_ITEM_CSV = Path("output/subjective_item_descriptives.csv")
SUBJ_CONSTRUCT_CSV = Path("output/subjective_construct_scores.csv")
SUBJ_OUTPUT_DIR = Path("output")

CONDITIONS = ["C0", "C1", "C2"]

CONSTRUCTS = [
    ("ui_visibility_movement_score", "UI Visibility\n& Movement"),
    ("avatar_interaction_score", "Avatar\nInteraction"),
    ("comfort_presence_score", "Comfort\n& Presence"),
]

NEUTRAL = 3

PREFERENCE_CSV = Path("Adaptive UI in Mixed Reality Post-questionnaire(Sheet1).csv")
PREFERENCE_COL = "Which version of UI do you prefer?"
PREFERENCE_MAP = {
    "Static UI": "C0",
    "Dynamic UI (Left Movement)": "C1",
    "Dynamic UI (Upward Movement)": "C2",
}


def save_fig(output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved: {output_path.resolve()}")


def compute_stats(values):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return None
    return {
        "min": float(np.min(arr)),
        "q1": float(np.percentile(arr, 25)),
        "median": float(np.percentile(arr, 50)),
        "mean": float(np.mean(arr)),
        "q3": float(np.percentile(arr, 75)),
        "max": float(np.max(arr)),
        "arr": arr,
    }

def load_completion_times(csv_path, result_filter):
    data = {c: [] for c in CONDITIONS}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            result = (row.get("result") or "").strip().lower()
            condition = (row.get("condition") or "").strip()
            time_raw = (row.get("completion time") or "").strip()

            if result != result_filter or condition not in data or not time_raw:
                continue
            try:
                data[condition].append(float(time_raw))
            except ValueError:
                continue
    return data


def plot_completion_distribution(data, title, output_path: Path,
                                 figsize, annotate_fn, apply_ylim=False,
                                 margin_x=0.18):
    values = [data[c] for c in CONDITIONS]
    positions = [1, 2, 3]

    plt.figure(figsize=figsize)
    ax = plt.gca()

    parts = ax.violinplot(values, positions=positions, showmeans=True, showmedians=True)
    for body in parts["bodies"]:
        body.set_alpha(0.35)

    ax.boxplot(values, positions=positions, widths=0.22, patch_artist=False)

    for x_pos, series in zip(positions, values):
        annotate_fn(ax, x_pos, series)

    ax.set_xticks(positions, CONDITIONS)
    ax.set_xlabel("Condition")
    ax.set_ylabel("Task Completion Time (s)")
    ax.set_title(title)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    if apply_ylim:
        all_vals = [v for series in values for v in series]
        if all_vals:
            y_min, y_max = min(all_vals), max(all_vals)
            pad = max(1.0, (y_max - y_min) * 0.2)
            ax.set_ylim(y_min - pad * 0.3, y_max + pad)

    plt.tight_layout()
    ax.margins(x=margin_x)
    save_fig(output_path)

    print(f"  Counts: " + ", ".join(f"{c}={len(data[c])}" for c in CONDITIONS))
    stds = []
    for c in CONDITIONS:
        arr = np.asarray(data[c], dtype=float)
        stds.append(f"{c}={np.std(arr, ddof=1):.2f}" if len(arr) > 1 else f"{c}=N/A")
    print(f"  Std: " + ", ".join(stds))



# Distribution of Failed Task Completion Time
def annotate_fig1(ax, x_pos, values):
    s = compute_stats(values)
    if s is None:
        return
    labels = [
        (s["max"], f"max={s['max']:.1f}", (8, 0)),
        (s["q3"], f"Q3={s['q3']:.1f}", (8, 0)),
        (s["median"], f"median={s['median']:.1f}", (8, -10)),
        (s["mean"], f"mean={s['mean']:.1f}", (8, 10)),
        (s["q1"], f"Q1={s['q1']:.1f}", (8, 0)),
        (s["min"], f"min={s['min']:.1f}", (8, 0)),
    ]
    for y, text, offset in labels:
        ax.annotate(text, xy=(x_pos, y), xytext=offset,
                    textcoords="offset points", ha="left", va="center", fontsize=8)

def plot_fig1():
    data = load_completion_times(GAZE_CSV, "failed")
    plot_completion_distribution(
        data,
        title="Distribution of Failed Task Completion Time by Condition",
        output_path=OUTPUT_DIR / "failed_completion_time_distribution.png",
        figsize=(8, 5),
        annotate_fn=annotate_fig1,
        apply_ylim=False,
        margin_x=0.18,
    )



# Distribution of Successful Task Completion Time
def annotate_fig2(ax, x_pos, values):
    s = compute_stats(values)
    if s is None:
        return
    labels = [
        (s["max"], f"max={s['max']:.1f}"),
        (s["q3"], f"Q3={s['q3']:.1f}"),
        (s["mean"], f"mean={s['mean']:.1f}"),
        (s["median"], f"median={s['median']:.1f}"),
        (s["q1"], f"Q1={s['q1']:.1f}"),
        (s["min"], f"min={s['min']:.1f}"),
    ]

    arr = s["arr"]
    y_span = max(1.0, float(arr.max() - arr.min()))
    min_gap = max(0.6, y_span * 0.06)

    labels = sorted(labels, key=lambda x: x[0])
    adjusted = []
    prev_y = None
    for y, text in labels:
        y_text = y if prev_y is None else max(y, prev_y + min_gap)
        adjusted.append((y, y_text, text))
        prev_y = y_text

    over = adjusted[-1][1] - arr.max()
    if over > y_span * 0.25:
        shift = over - y_span * 0.25
        adjusted = [(y, y_text - shift, text) for (y, y_text, text) in adjusted]

    for y, y_text, text in adjusted:
        ax.annotate(
            text, xy=(x_pos, y), xytext=(x_pos + 0.24, y_text),
            textcoords="data", ha="left", va="center", fontsize=8,
            arrowprops=dict(arrowstyle="-", lw=0.6, color="gray", shrinkA=0, shrinkB=0),
        )


def plot_fig2():
    print("\nSuccessful Task Completion Time Distribution")
    data = load_completion_times(GAZE_CSV, "success")
    plot_completion_distribution(
        data,
        title="Distribution of Successful Task Completion Time by Condition",
        output_path=OUTPUT_DIR / "success_completion_time_distribution.png",
        figsize=(8, 6.5),
        annotate_fn=annotate_fig2,
        apply_ylim=True,
        margin_x=0.22,
    )



# Figure 3: Success Rate by Condition
def plot_fig3():
    print("\nSuccess Rate by Condition")
    counts = {c: {"success": 0, "failed": 0} for c in CONDITIONS}

    with GAZE_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cond = (row.get("condition") or "").strip()
            result = (row.get("result") or "").strip().lower()
            if cond in counts and result in ("success", "failed"):
                counts[cond][result] += 1

    success = np.array([counts[c]["success"] for c in CONDITIONS], dtype=float)
    failed = np.array([counts[c]["failed"] for c in CONDITIONS], dtype=float)
    total = success + failed

    with np.errstate(divide="ignore", invalid="ignore"):
        success_rate = np.where(total > 0, success / total * 100.0, 0.0)
        failed_rate = np.where(total > 0, failed / total * 100.0, 0.0)

    fig, ax = plt.subplots(figsize=(8, 5.5))
    x = np.arange(len(CONDITIONS))

    ax.bar(x, success_rate, width=0.58, color="#2a9d8f", label="Success")
    ax.bar(x, failed_rate, width=0.58, bottom=success_rate,
           color="#e76f51", label="Failed")

    for i in range(len(CONDITIONS)):
        ax.text(x[i], 102, f"n={int(total[i])}", ha="center", va="bottom", fontsize=9)
        if success_rate[i] > 0:
            ax.text(x[i], success_rate[i] / 2, f"{success_rate[i]:.1f}%",
                    ha="center", va="center", color="white",
                    fontsize=9, fontweight="bold")
        if failed_rate[i] > 0:
            ax.text(x[i], success_rate[i] + failed_rate[i] / 2, f"{failed_rate[i]:.1f}%",
                    ha="center", va="center", color="white",
                    fontsize=9, fontweight="bold")

    ax.set_ylim(0, 110)
    ax.set_xticks(x, CONDITIONS)
    ax.set_ylabel("Rate (%)")
    ax.set_xlabel("Condition")
    ax.set_title("Success Rate by Condition")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend(loc="upper right")

    plt.tight_layout()
    save_fig(OUTPUT_DIR / "success_rate_by_condition.png")

    for i, c in enumerate(CONDITIONS):
        s, fld, t = int(success[i]), int(failed[i]), int(total[i])
        rate = (s / t * 100.0) if t > 0 else 0.0
        print(f"  {c}: success={s}, failed={fld}, success_rate={rate:.2f}%")


# Visual Attention: Composition + Avatar Timeline
def load_gaze_rows(csv_path):
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        gaze_cols = [c for c in reader.fieldnames if c.startswith("gaze_second")]
        rows = list(reader)
    return rows, gaze_cols


def plot_attention_composition(rows, gaze_cols):
    labels = ["UI", "Avatar", "None"]
    colors = {"UI": "#4e79a7", "Avatar": "#f28e2b", "None": "#9ea3a8"}

    counts = {cond: defaultdict(int) for cond in CONDITIONS}
    totals = {cond: 0 for cond in CONDITIONS}

    for row in rows:
        cond = (row.get("condition") or "").strip()
        if cond not in counts:
            continue
        for c in gaze_cols:
            val = (row.get(c) or "").strip()
            if val in labels:
                counts[cond][val] += 1
                totals[cond] += 1

    pct = {label: [] for label in labels}
    for cond in CONDITIONS:
        denom = totals[cond]
        for label in labels:
            pct[label].append((counts[cond][label] / denom * 100.0) if denom > 0 else 0.0)

    x = np.arange(len(CONDITIONS))
    fig, ax = plt.subplots(figsize=(8, 5.2))
    bottom = np.zeros(len(CONDITIONS), dtype=float)

    for label in labels:
        vals = np.array(pct[label], dtype=float)
        bars = ax.bar(x, vals, bottom=bottom, width=0.62,
                      color=colors[label], label=label)
        for i, b in enumerate(bars):
            if vals[i] >= 4.0:
                ax.text(b.get_x() + b.get_width() / 2,
                        bottom[i] + vals[i] / 2,
                        f"{vals[i]:.1f}%",
                        ha="center", va="center",
                        fontsize=9, color="white", fontweight="bold")
        bottom += vals

    for i, cond in enumerate(CONDITIONS):
        ax.text(x[i], 102, f"N={totals[cond]}", ha="center", va="bottom", fontsize=9)

    ax.set_ylim(0, 108)
    ax.set_xticks(x, CONDITIONS)
    ax.set_xlabel("Condition")
    ax.set_ylabel("Gaze Composition (%)")
    ax.set_title("Visual Attention Composition by Condition")
    ax.legend(loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    plt.tight_layout()
    save_fig(OUTPUT_DIR / "figure_attention_1_composition_by_condition.png")

    for cond in CONDITIONS:
        idx = CONDITIONS.index(cond)
        print(f"  {cond}: N={totals[cond]}, "
              f"UI={counts[cond]['UI']} ({pct['UI'][idx]:.2f}%), "
              f"Avatar={counts[cond]['Avatar']} ({pct['Avatar'][idx]:.2f}%), "
              f"None={counts[cond]['None']} ({pct['None'][idx]:.2f}%)")


def plot_avatar_timeline(rows, gaze_cols):
    colors = {"C0": "#1f77b4", "C1": "#ff7f0e", "C2": "#2ca02c"}

    avatar_count = {cond: np.zeros(len(gaze_cols)) for cond in CONDITIONS}
    valid_count = {cond: np.zeros(len(gaze_cols)) for cond in CONDITIONS}

    for row in rows:
        cond = (row.get("condition") or "").strip()
        if cond not in CONDITIONS:
            continue
        for i, c in enumerate(gaze_cols):
            val = (row.get(c) or "").strip()
            if not val:
                continue
            valid_count[cond][i] += 1
            if val == "Avatar":
                avatar_count[cond][i] += 1

    x = np.arange(len(gaze_cols))
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    peaks = {}

    for cond in CONDITIONS:
        denom = valid_count[cond]
        rate = np.divide(avatar_count[cond] * 100.0, denom,
                         out=np.full_like(avatar_count[cond], np.nan),
                         where=denom > 0)

        # 3-second moving average for readability
        valid = np.where(np.isnan(rate), 0.0, rate)
        mask = np.where(np.isnan(rate), 0.0, 1.0)
        kernel = np.ones(3)
        smooth_num = np.convolve(valid, kernel, mode="same")
        smooth_den = np.convolve(mask, kernel, mode="same")
        smooth = np.divide(smooth_num, smooth_den,
                           out=np.full_like(smooth_num, np.nan),
                           where=smooth_den > 0)

        ax.plot(x, smooth, linewidth=2.0, color=colors[cond], label=cond)

        visible = smooth[:61]
        if np.all(np.isnan(visible)):
            peaks[cond] = (np.nan, None)
        else:
            peak_idx = int(np.nanargmax(visible))
            peaks[cond] = (float(visible[peak_idx]), peak_idx)

    ax.set_xlim(0, 60)
    ax.set_ylim(0, 60)
    ax.set_xlabel("Second")
    ax.set_ylabel("Avatar Gaze Rate (%)")
    ax.set_title("Avatar Attention Over Time by Condition")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend(loc="upper right", title="Condition")

    plt.tight_layout()
    save_fig(OUTPUT_DIR / "figure_attention_2_avatar_timeline_by_condition.png")

    for cond in CONDITIONS:
        peak_val, peak_sec = peaks[cond]
        if peak_sec is None:
            print(f"  {cond}: peak = N/A")
        else:
            print(f"  {cond}: peak = {peak_val:.2f}% at second {peak_sec}")


def plot_attention():
    print("\nVisual Attention - Composition + Avatar Timeline")
    rows, gaze_cols = load_gaze_rows(GAZE_CSV)
    plot_attention_composition(rows, gaze_cols)
    plot_avatar_timeline(rows, gaze_cols)



# Item-level Subjective Ratings
LIKERT_LABEL_MAP = {
    "ui_visible": "UI visible",
    "ui_position_appropriate": "Position appropriate",
    "ui_distance_comfortable": "Comfortable distance",
    "ui_movement_smooth": "Movement smooth",
    "ui_movement_natural": "Movement natural",
    "ui_repositioning_improved": "Improved interaction",
    "ui_repositioning_distracting": "Not distracting",
    "avatar_clear_view": "Clear avatar view",
    "avatar_social_presence": "Avatar socially present",
    "avatar_interaction_flow": "Interaction flowed smoothly",
    "avatar_not_awkward": "Not awkward",
    "avatar_approach_comfort": "Comfortable when approached",
    "ui_no_discomfort": "No discomfort",
    "interaction_immersive": "Immersive",
    "ui_socially_appropriate": "Socially appropriate",
    "comfortable_with_others_present": "Comfortable with others",
    "ui_not_disruptive": "Not disruptive",
    "ui_predictable": "Predictable",
}

def plot_likert1():
    print("\nItem-level Subjective Ratings")
    df = pd.read_csv(SUBJ_ITEM_CSV)
    df["label"] = df["variable"].map(LIKERT_LABEL_MAP).fillna(df["variable"])

    plt.figure(figsize=(12, 6))
    x = range(len(df))
    plt.bar(x, df["mean"], capsize=4)
    plt.axhline(NEUTRAL, linestyle="--", linewidth=1, label=f"Neutral = {NEUTRAL}")
    plt.xticks(x, df["label"], rotation=45, ha="right")
    plt.ylabel("Mean Likert Score")
    plt.title("Item-level Subjective Ratings")
    plt.legend()
    plt.tight_layout()

    save_fig(SUBJ_OUTPUT_DIR / "figure_subjective_item_means.png")



# Likert Plot 2: Construct-level Subjective Ratings (Boxplot)
def plot_likert2():
    print("\nConstruct-level Subjective Ratings")
    df = pd.read_csv(SUBJ_CONSTRUCT_CSV)
    values = [df[col].dropna() for col, _ in CONSTRUCTS]
    labels = [label for _, label in CONSTRUCTS]

    plt.figure(figsize=(8, 5))
    plt.boxplot(values, labels=labels, showmeans=True)
    plt.axhline(NEUTRAL, linestyle="--", linewidth=1, label=f"Neutral = {NEUTRAL}")
    plt.ylabel("Construct Score")
    plt.title("Distribution of Construct-level Subjective Ratings")
    plt.legend()
    plt.tight_layout()

    save_fig(SUBJ_OUTPUT_DIR / "figure_subjective_construct_distribution.png")

# H2 Plot: Participant-level Differences from Neutral Midpoint
def plot_h2():
    print("\nParticipant-level Differences from Neutral Midpoint")
    df = pd.read_csv(SUBJ_CONSTRUCT_CSV)

    plt.figure(figsize=(8, 5))
    for i, (col, _) in enumerate(CONSTRUCTS, start=1):
        values = pd.to_numeric(df[col], errors="coerce").dropna() - NEUTRAL
        x = np.random.normal(i, 0.05, size=len(values))  # jitter
        plt.scatter(x, values, alpha=0.7)

    plt.axhline(0, linestyle="--", linewidth=1, label=f"Neutral = {NEUTRAL}")
    plt.xticks(range(1, len(CONSTRUCTS) + 1), [label for _, label in CONSTRUCTS])
    plt.ylabel("Difference from Neutral")
    plt.title("Participant-level Differences from Neutral Midpoint")
    plt.legend()
    plt.tight_layout()

    save_fig(SUBJ_OUTPUT_DIR / "figure_subjective_wilcoxon_diff.png")


# Preferred UI Condition
def load_csv_flex(path):
    for enc in ["cp1252", "latin1", "utf-8-sig", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    raise ValueError(f"Could not read {path}")


def normalize_text(s):
    return str(s).replace("\xa0", " ").strip()


def find_column(df, target):
    target_norm = normalize_text(target)
    for col in df.columns:
        if target_norm in normalize_text(col):
            return col
    return None


def plot_preference():
    print("\nPreferred UI Condition")
    SUBJ_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_csv_flex(PREFERENCE_CSV)
    pref_col = find_column(df, PREFERENCE_COL)
    if pref_col is None:
        raise KeyError("Preference column not found.")

    pref = df[[pref_col]].copy()
    pref.columns = ["raw_preference"]
    pref["raw_preference"] = pref["raw_preference"].map(normalize_text)
    pref["condition"] = pref["raw_preference"].map(PREFERENCE_MAP)

    counts = (
        pref["condition"]
        .value_counts(dropna=False)
        .reindex(CONDITIONS)
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    counts.columns = ["condition", "count"]
    counts["percentage"] = counts["count"] / counts["count"].sum() * 100

    counts.to_csv(SUBJ_OUTPUT_DIR / "preference_counts.csv",
                  index=False, encoding="utf-8-sig")

    plt.figure(figsize=(6, 4))
    plt.bar(counts["condition"], counts["count"])
    for i, row in counts.iterrows():
        plt.text(i, row["count"] + 0.1,
                 f'{row["count"]}\n({row["percentage"]:.1f}%)',
                 ha="center", va="bottom", fontsize=9)

    plt.xlabel("Condition")
    plt.ylabel("Number of Participants")
    plt.title("Preferred UI Condition")
    plt.tight_layout()
    save_fig(SUBJ_OUTPUT_DIR / "figure_preference_distribution.png")


def main():
    plot_fig1()
    plot_fig2()
    plot_fig3()
    plot_attention()
    plot_likert1()
    plot_likert2()
    plot_h2()
    plot_preference()
    print("\nAll figures generated.")


if __name__ == "__main__":
    main()
