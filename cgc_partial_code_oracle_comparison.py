from __future__ import annotations

import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent
IN_CSV = BASE / "cgc_partial_code_oracle_examples.csv"
OUT_CSV = BASE / "cgc_partial_code_oracle_results.csv"
OUT_LOG = BASE / "cgc_partial_code_oracle_discrepancy_log.txt"


def to_float(value: str) -> float:
    return float(value.strip())


def main() -> None:
    with IN_CSV.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    out_rows = []
    discrepancies = []
    for row in rows:
        oracle = to_float(row["manual_or_oracle_value"])
        script = to_float(row["script_value"])
        denom = max(abs(oracle), 1e-12)
        rel = abs(script - oracle) / denom
        oracle_pf = row["pass_fail_oracle"].strip().lower()
        script_pf = row["pass_fail_script"].strip().lower()
        match = "yes" if oracle_pf == script_pf and rel <= 0.03 else "no"
        out = dict(row)
        out["relative_error"] = f"{rel:.6f}"
        out["classification_match"] = match
        out_rows.append(out)
        if match != "yes":
            discrepancies.append(
                f"{row['example_id']}: oracle={oracle} script={script} rel={rel:.6f} "
                f"oracle_pf={oracle_pf} script_pf={script_pf}"
            )

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    if discrepancies:
        text = "\n".join(discrepancies) + "\n"
    else:
        text = (
            "Partial code-oracle comparison completed with zero classification mismatches. "
            "This is a limited oracle check for declared simplified checks and does not "
            "constitute full AISC/ASCE design approval.\n"
        )
    OUT_LOG.write_text(text, encoding="utf-8")
    print(OUT_CSV)
    print(OUT_LOG)


if __name__ == "__main__":
    main()



