from __future__ import annotations

import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent
IN_CSV = BASE / "cgc_response_support_protocol_rows.csv"
OUT_CSV = BASE / "cgc_response_support_summary.csv"
OUT_NOTE = BASE / "cgc_response_support_note.txt"


def is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def main() -> None:
    with IN_CSV.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    measured = [
        r for r in rows
        if is_number(r.get("measured_displacement", ""))
        and is_number(r.get("predicted_displacement", ""))
    ]
    false_certified = [
        r for r in rows
        if r.get("encoded_feasible", "").lower() in {"yes", "true"}
        and r.get("experimental_feasible", "").lower() in {"no", "false"}
    ]
    if measured:
        disp_errors = [float(r["relative_error_displacement"]) for r in measured if is_number(r["relative_error_displacement"])]
        strain_errors = [float(r["relative_error_strain"]) for r in measured if is_number(r["relative_error_strain"])]
        classification = [r for r in measured if r.get("classification_match") == "yes"]
        status = "supported_by_lab_response_data"
    else:
        disp_errors = []
        strain_errors = []
        classification = []
        status = "protocol_defined"

    summary = {
        "specimen_rows": len(rows),
        "measured_rows": len(measured),
        "mean_relative_error_displacement": f"{sum(disp_errors)/len(disp_errors):.6f}" if disp_errors else "not_applicable",
        "max_relative_error_displacement": f"{max(disp_errors):.6f}" if disp_errors else "not_applicable",
        "mean_relative_error_strain": f"{sum(strain_errors)/len(strain_errors):.6f}" if strain_errors else "not_applicable",
        "classification_accuracy": f"{len(classification)/len(measured):.6f}" if measured else "not_applicable",
        "false_certified_count": len(false_certified),
        "response_support_status": "response_support_failed" if false_certified else status,
    }
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)
    OUT_NOTE.write_text(
        "\n".join(
            [
                "external response-support protocol-row summary.",
                f"Status: {summary['response_support_status']}.",
                "No published-response claim is allowed unless measured or published response data are supplied and false_certified_count is zero.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(OUT_CSV)
    print(OUT_NOTE)


if __name__ == "__main__":
    main()




