from pathlib import Path
import re
import numpy as np
import pandas as pd

INPUT_CSV = "Adaptive UI in Mixed Reality Post-questionnaire(Sheet1).csv"
OUTPUT_DIR = Path("output")


LIKERT_MAP = {
    "Strongly Disagree": 1,
    "Disagree": 2,
    "Neutral": 3,
    "Agree": 4,
    "Strongly Agree": 5,
}

QUESTION_MAP = {
    # UI Visibility and Movement
    "The interface was clearly visible throughout the Simon game.": "ui_visible",
    "The UI positioning felt appropriate in the environment.": "ui_position_appropriate",
    "The UI remained within a comfortable viewing distance.": "ui_distance_comfortable",
    "The UI movement felt smooth.": "ui_movement_smooth",
    "The UI movement felt natural.": "ui_movement_natural",
    "The repositioning improved my interaction experience.": "ui_repositioning_improved",
    "The repositioning was distracting.": "ui_repositioning_distracting",
    "I had a clear view of the avatar during gameplay for dynamic UI.": "avatar_clear_view",

    # Avatar Interaction
    "The avatar felt socially present in the environment.": "avatar_social_presence",
    "The interaction with the avatar flowed smoothly.": "avatar_interaction_flow",
    "I did not feel awkward during the interaction.": "avatar_not_awkward",
    "I felt comfortable when the avatar approached me.": "avatar_approach_comfort",

    # Comfort and Presence
    "The UI behaviour did not cause discomfort.": "ui_no_discomfort",
    "The interaction felt immersive.": "interaction_immersive",
    "Interacting with the UI felt socially appropriate in the scenario.": "ui_socially_appropriate",
    "I felt comfortable performing the interaction while others were present.": "comfortable_with_others_present",
    "I did not worry that my interaction with the UI would feel disruptive to others in the environment": "ui_not_disruptive",
    "I felt confident that the UI would behave in a predictable way.": "ui_predictable",
}

PARTICIPANT_KEY = "Participant ID"

PREFERENCE_KEY = "Which version of UI do you prefer?"
OPEN_ENDED_KEY = "For the answer of question 6, why do you prefer it rather than the others?"

REVERSE_CODE_ITEMS = {
    "ui_repositioning_distracting",
}


def normalize_text(s):
    s = str(s).replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_csv(path):
    for enc in ["cp1252", "latin1", "utf-8-sig", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    raise ValueError(f"Could not read CSV with supported encodings: {path}")


def build_column_lookup(df):
    norm_to_original = {}
    for col in df.columns:
        norm_col = normalize_text(col)
        norm_to_original[norm_col] = col
    return norm_to_original


def find_column(norm_to_original, target):
    target_norm = normalize_text(target)

    if target_norm in norm_to_original:
        return norm_to_original[target_norm]

    for norm_col, original_col in norm_to_original.items():
        if target_norm in norm_col:
            return original_col

    return None

def coerce_likert(series):
    return series.map(lambda x: LIKERT_MAP.get(normalize_text(x), np.nan))

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw = load_csv(INPUT_CSV)
    norm_to_original = build_column_lookup(raw)

    participant_col = find_column(norm_to_original, PARTICIPANT_KEY)
    if participant_col is None:
        raise KeyError("Participant ID column not found.")

    selected_cols = {participant_col: "participant_id"}

    for q_text, short_name in QUESTION_MAP.items():
        col = find_column(norm_to_original, q_text)
        if col is None:
            raise KeyError(f"Could not find column for question: {q_text}")
        selected_cols[col] = short_name

    # Keep only participant + likert items columns
    df = raw[list(selected_cols.keys())].copy()
    df = df.rename(columns=selected_cols)

    for col in df.columns:
        if col == "participant_id":
            continue
        df[col] = coerce_likert(df[col])

    # reverse coding
    for col in REVERSE_CODE_ITEMS:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: 6 - x if pd.notna(x) else np.nan)

    item_out = OUTPUT_DIR / "subjective_likert_item_scores.csv"
    df.to_csv(item_out, index=False, encoding="utf-8-sig")

    # Construct scores
    construct_df = pd.DataFrame()
    construct_df["participant_id"] = df["participant_id"]

    construct_df["ui_visibility_movement_score"] = df[
        [
            "ui_visible",
            "ui_position_appropriate",
            "ui_distance_comfortable",
            "ui_movement_smooth",
            "ui_movement_natural",
            "ui_repositioning_improved",
            "ui_repositioning_distracting",
            "avatar_clear_view",
        ]
    ].mean(axis=1)

    construct_df["avatar_interaction_score"] = df[
        ["avatar_social_presence", "avatar_interaction_flow", "avatar_not_awkward", "avatar_approach_comfort"]
    ].mean(axis=1)

    construct_df["comfort_presence_score"] = df[
        [
            "ui_no_discomfort",
            "interaction_immersive",
            "ui_socially_appropriate",
            "comfortable_with_others_present",
            "ui_not_disruptive",
            "ui_predictable",
        ]
    ].mean(axis=1)

    construct_out = OUTPUT_DIR / "subjective_construct_scores.csv"
    construct_df.to_csv(construct_out, index=False, encoding="utf-8-sig")

    # Descriptive statistics
    item_stats = []
    for col in df.columns:
        if col == "participant_id":
            continue
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        item_stats.append({
            "variable": col,
            "n": len(s),
            "mean": s.mean(),
            "median": s.median(),
            "std": s.std(ddof=1),
        })
    item_stats_df = pd.DataFrame(item_stats)
    item_stats_df.to_csv(OUTPUT_DIR / "subjective_item_descriptives.csv", index=False, encoding="utf-8-sig")

    construct_stats = []
    for col in ["ui_visibility_movement_score", "avatar_interaction_score", "comfort_presence_score"]:
        s = pd.to_numeric(construct_df[col], errors="coerce").dropna()
        construct_stats.append({
            "construct": col,
            "n": len(s),
            "mean": s.mean(),
            "median": s.median(),
            "std": s.std(ddof=1),
        })

    pd.DataFrame(construct_stats).to_csv(
        OUTPUT_DIR / "subjective_construct_descriptives.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("Saved:")
    print(f" - {item_out}")
    print(f" - {construct_out}")
    print(f" - {OUTPUT_DIR / 'subjective_item_descriptives.csv'}")
    print(f" - {OUTPUT_DIR / 'subjective_construct_descriptives.csv'}")


if __name__ == "__main__":
    main()