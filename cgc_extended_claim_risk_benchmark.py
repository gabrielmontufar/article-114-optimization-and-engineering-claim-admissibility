from __future__ import annotations

import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent
SUMMARY = BASE / "cgc_benchmark_reporting_summary.csv"
OUT_CSV = BASE / "cgc_extended_claim_risk_benchmark.csv"


def to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def extended_label(row: dict[str, str]) -> str:
    residual = to_float(row.get("max_normalized_residual", "0"))
    encoded = row.get("encoded_feasible", "").lower() in {"yes", "true"}
    full_code = row.get("full_code_validation_status", "not_performed")
    physical = row.get("response_support_status", "not_performed")
    certificate = any(
        key in row.get("solver_or_method", "").lower()
        for key in ["pulp", "enumeration", "exhaustive", "opensees"]
    )

    if residual > 0:
        return "high"
    if not encoded or not certificate:
        return "moderate_or_unresolved"
    if (
        full_code == "validated_against_full_code_oracle"
        and physical in {"supported_by_processed_published_response_data", "supported_by_lab_response_data"}
    ):
        return "low_physical_and_code_supported"
    if full_code == "validated_against_full_code_oracle":
        return "low_code_supported"
    if physical in {"supported_by_processed_published_response_data", "supported_by_lab_response_data"}:
        return "low_response_supported"
    if full_code == "validated_against_partial_code_oracle":
        return "low_partial_code_supported"
    return "low_encoded_only"


def main() -> None:
    with SUMMARY.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    out_rows = []
    for row in rows:
        out = {
            "benchmark": row["benchmark"],
            "case": row["case"],
            "encoded_feasible": row["encoded_feasible"],
            "max_normalized_residual": row["max_normalized_residual"],
            "full_code_validation_status": row.get("full_code_validation_status", "not_performed"),
            "response_support_status": row.get("response_support_status", "not_performed"),
            "code_clause_coverage_percent": row.get("code_clause_coverage_percent", "0"),
            "oracle_comparison_count": row.get("oracle_comparison_count", "0"),
            "classification_mismatch_count": row.get("classification_mismatch_count", "0"),
            "false_certified_count": row.get("false_certified_count", "0"),
            "supported_claim_level": extended_label(row),
        }
        out_rows.append(out)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    print(OUT_CSV)


if __name__ == "__main__":
    main()



