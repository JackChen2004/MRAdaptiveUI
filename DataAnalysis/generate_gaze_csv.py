import csv
import re
from pathlib import Path

PARTICIPANT_ID_MAP = {
    # Deleted for data confidentiality
    # The output gaze_summary.csv is not shown in this repository for same reason.
}


def parse_file(file_path):
    text = file_path.read_text(encoding="utf-8-sig")
    lines = [line.strip() for line in text.splitlines()]

    result_value = ""
    completion_time = ""

    for line in lines:
        if line.startswith("Result:"):
            raw = line.split(":", 1)[1].strip().upper()
            if raw == "SUCCESS":
                result_value = "Success"
            elif raw == "FAILED":
                result_value = "Failed"
            else:
                result_value = raw.title() if raw else ""
        elif line.startswith("TotalTimeFromStartPress_sec:"):
            completion_time = line.split(":", 1)[1].strip()

    gaze_data = {}
    in_gaze = False
    for line in lines:
        if line.startswith("PerSecondGaze:"):
            in_gaze = True
            continue

        if not in_gaze or not line:
            continue

        # Expected format: second,label
        if "," not in line:
            continue

        second_str, label = line.split(",", 1)
        second_str = second_str.strip()
        label = label.strip()

        if not second_str.isdigit():
            continue

        second = int(second_str)
        # If duplicated seconds exist, keep the latest one.
        gaze_data[second] = label

    return result_value, completion_time, gaze_data


def parse_participant_and_condition(file_name):
    stem = Path(file_name).stem
    m = re.match(r"^(.*?)([123])$", stem)
    if not m:
        return stem, ""

    participant = m.group(1)
    cond_num = m.group(2)
    condition_map = {"1": "C0", "2": "C1", "3": "C2"}
    condition = condition_map.get(cond_num, "")
    return participant, condition


def main():
    data_dir = Path("data")
    output_csv = Path("gaze_summary.csv")

    txt_files = sorted(data_dir.glob("*.txt"))
    if not txt_files:
        raise SystemExit("No .txt files found in data directory.")

    rows = []
    all_seconds = set()

    for file_path in txt_files:
        participant, condition = parse_participant_and_condition(file_path.name)
        result_value, completion_time, gaze_data = parse_file(file_path)

        all_seconds.update(gaze_data.keys())
        rows.append(
            {
                "Participant ID": PARTICIPANT_ID_MAP.get(participant, ""),
                "condition": condition,
                "result": result_value,
                "completion time": completion_time,
                "gaze": gaze_data,
            }
        )

    second_columns = sorted(all_seconds)

    headers = ["Participant ID", "condition", "result", "completion time"] + [
        f"gaze_second{sec}" for sec in second_columns
    ]

    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for row in rows:
            values = [
                row["Participant ID"],
                row["condition"],
                row["result"],
                row["completion time"],
            ]
            for sec in second_columns:
                values.append(row["gaze"].get(sec, ""))
            writer.writerow(values)

if __name__ == "__main__":
    main()
