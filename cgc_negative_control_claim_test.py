from __future__ import annotations

import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent
OUT_CSV = BASE / "cgc_negative_control_claim_test.csv"


CASES = [
    {
        "negative_case": "off_catalog_section",
        "inserted_violation": "section is not in declared catalog",
        "encoded_feasible": "no",
        "catalog_valid": "no",
        "verification_route": "enumeration",
        "reported_claim": "conditional encoded-compliance claim",
        "expected_result": "no certificate",
    },
    {
        "negative_case": "positive_residual",
        "inserted_violation": "drift or demand/capacity residual is positive",
        "encoded_feasible": "no",
        "catalog_valid": "yes",
        "verification_route": "enumeration",
        "reported_claim": "conditional encoded-compliance claim",
        "expected_result": "high claim risk",
    },
    {
        "negative_case": "missing_solver_route",
        "inserted_violation": "zero residual but no recorded solver/enumeration route",
        "encoded_feasible": "yes",
        "catalog_valid": "yes",
        "verification_route": "missing",
        "reported_claim": "conditional encoded-compliance claim",
        "expected_result": "moderate claim risk",
    },
    {
        "negative_case": "aisc_wording_overclaim",
        "inserted_violation": "AISC approval claimed with only catalog audit",
        "encoded_feasible": "yes",
        "catalog_valid": "yes",
        "verification_route": "AISC catalog enumeration",
        "reported_claim": "unsupported AISC approval wording",
        "expected_result": "unsupported claim",
    },
    {
        "negative_case": "robust_wording_overclaim",
        "inserted_violation": "robust claim asserted for nominal-only feasible design",
        "encoded_feasible": "yes",
        "catalog_valid": "yes",
        "verification_route": "nominal enumeration",
        "reported_claim": "robust response support",
        "expected_result": "no robust claim",
    },
]


def classify(row: dict[str, str]) -> dict[str, str]:
    claim = row["reported_claim"].lower()
    route = row["verification_route"].lower()
    encoded = row["encoded_feasible"] == "yes"
    catalog = row["catalog_valid"] == "yes"
    if not catalog:
        result = "no certificate"
    elif not encoded:
        result = "high claim risk"
    elif route == "missing":
        result = "moderate claim risk"
    elif "aisc approval" in claim:
        result = "unsupported claim"
    elif "robust" in claim:
        result = "no robust claim"
    else:
        result = "accepted encoded claim"
    out = dict(row)
    out["observed_result"] = result
    out["claim_blocked_or_downgraded"] = "yes" if result == row["expected_result"] else "no"
    out["false_certified"] = "yes" if result == "accepted encoded claim" and row["expected_result"] != result else "no"
    return out


def main() -> None:
    rows = [classify(row) for row in CASES]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(OUT_CSV)


if __name__ == "__main__":
    main()



