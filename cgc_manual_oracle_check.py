from __future__ import annotations

import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent
IN_CSV = BASE / "cgc_manual_oracle_check.csv"
OUT_CSV = BASE / "cgc_manual_oracle_check_results.csv"
OUT_NOTE = BASE / "cgc_manual_oracle_check_note.txt"


def to_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def main() -> None:
    with IN_CSV.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    out = []
    mismatches = 0
    for row in rows:
        hand = to_float(row["hand_calc_value"])
        script = to_float(row["script_value"])
        if hand is not None and script is not None:
            rel = abs(script - hand) / max(abs(hand), 1e-12)
        else:
            rel = 0.0 if row["hand_calc_value"] == row["script_value"] else 1.0
        match = (
            row["pass_fail_hand"].lower() == row["pass_fail_script"].lower()
            and rel <= 0.03
        )
        row = dict(row)
        row["relative_error"] = f"{rel:.6f}"
        row["classification_match"] = "yes" if match else "no"
        if not match:
            mismatches += 1
        out.append(row)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        writer.writeheader()
        writer.writerows(out)
    OUT_NOTE.write_text(
        f"Manual oracle checks: {len(out)} cases; classification mismatches: {mismatches}.\n",
        encoding="utf-8",
    )
    print(OUT_CSV)
    print(OUT_NOTE)


if __name__ == "__main__":
    main()



