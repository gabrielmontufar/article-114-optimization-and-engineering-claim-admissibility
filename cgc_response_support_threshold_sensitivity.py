from __future__ import annotations

import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent
OUT = BASE / "cgc_response_support_threshold_sensitivity.csv"


def read_rows(name: str) -> list[dict[str, str]]:
    with (BASE / name).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def to_float(value: str) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def main() -> None:
    rows: list[dict[str, str | int | float]] = []

    portal = read_rows("cgc_portal_frame_response_support_details.csv")
    for nrmse_limit in (0.10, 0.15, 0.20):
        for stiffness_limit in (0.15, 0.20, 0.25):
            passing = 0
            insufficient = 0
            for row in portal:
                nrmse = to_float(row.get("nrmse_service_response", ""))
                stiffness = to_float(row.get("initial_stiffness_relative_error", ""))
                if nrmse is None or stiffness is None:
                    insufficient += 1
                    continue
                if nrmse <= nrmse_limit and stiffness <= stiffness_limit:
                    passing += 1
            rows.append(
                {
                    "family": "portal_frame",
                    "nrmse_limit": f"{nrmse_limit:.2f}",
                    "stiffness_error_limit": f"{stiffness_limit:.2f}",
                    "detection_rate_limit": "not_applicable",
                    "passing_count": passing,
                    "screened_count": len(portal),
                    "insufficient_count": insufficient,
                    "false_certified_count": 0,
                    "interpretation": "response-support sensitivity only; not safety certification",
                }
            )

    truss = read_rows("cgc_truss_response_support_details.csv")
    for detection_limit in (0.45, 0.50, 0.55):
        passing = 0
        for row in truss:
            detection = to_float(row.get("damaged_detection_rate", ""))
            if detection is not None and detection >= detection_limit:
                passing += 1
        rows.append(
            {
                "family": "truss",
                "nrmse_limit": "not_applicable",
                "stiffness_error_limit": "not_applicable",
                "detection_rate_limit": f"{detection_limit:.2f}",
                "passing_count": passing,
                "screened_count": len(truss),
                "insufficient_count": 0,
                "false_certified_count": 0,
                "interpretation": "response-support sensitivity only; not safety certification",
            }
        )

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(OUT)


if __name__ == "__main__":
    main()
