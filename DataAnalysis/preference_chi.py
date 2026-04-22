from pathlib import Path
import pandas as pd
from scipy.stats import chisquare

INPUT_FILE = "Adaptive UI in Mixed Reality Post-questionnaire(Sheet1).csv"
OUTPUT_DIR = Path("output")
OUTPUT_FILE = OUTPUT_DIR / "preference_chisquare_results.txt"

PREFERENCE_COL = "Which version of UI do you prefer?"

ORDER = [
    "Static UI",
    "Dynamic UI (Left Movement)",
    "Dynamic UI (Upward Movement)",
]

LABEL_MAP = {
    "Static UI": "C0",
    "Dynamic UI (Left Movement)": "C1",
    "Dynamic UI (Upward Movement)": "C2",
}


def normalize_text(s):
    return str(s).replace("\xa0", " ").strip()

def load_csv(path):
    for enc in ["cp1252", "latin1", "utf-8-sig", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    raise ValueError(f"Could not read {path}")

def find_column(df, target):
    target_norm = normalize_text(target)
    for col in df.columns:
        if target_norm in normalize_text(col):
            return col
    return None

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_csv(INPUT_FILE)
    pref_col = find_column(df, PREFERENCE_COL)
    pref = df[pref_col].map(normalize_text)

    observed = (
        pref.value_counts()
        .reindex(ORDER)
        .fillna(0)
        .astype(int)
    )

    total = observed.sum()
    expected = [total / len(ORDER)] * len(ORDER)

    chi2, p = chisquare(f_obs=observed.values, f_exp=expected)
    df_chi = len(ORDER) - 1

    lines = []
    lines.append("Chi-square goodness-of-fit test for UI preference")
    lines.append("\nObserved counts:")
    for cond in ORDER:
        lines.append(f"  {LABEL_MAP[cond]} ({cond}): {observed[cond]}")
    lines.append("\nExpected counts under H0 (equal preference):")
    for cond, exp in zip(ORDER, expected):
        lines.append(f"  {LABEL_MAP[cond]} ({cond}): {exp:.3f}")
    lines.append(f"\nTotal N = {total}")
    lines.append(f"Chi-square statistic = {chi2:.4f}")
    lines.append(f"Degrees of freedom = {df_chi}")
    lines.append(f"p-value = {p:.6f}")

    result_text = "\n".join(lines)
    OUTPUT_FILE.write_text(result_text, encoding="utf-8")

    print(result_text)
    print(f"\nSaved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()