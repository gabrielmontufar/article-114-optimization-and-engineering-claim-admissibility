from __future__ import annotations

import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent
SUMMARY = BASE / "cgc_benchmark_reporting_summary.csv"
OUT_CSV = BASE / "cgc_claim_risk_benchmark.csv"
SENSITIVITY_CSV = BASE / "cgc_claim_risk_sensitivity.csv"
OUT_TXT = BASE / "cgc_claim_risk_benchmark_note.txt"


def to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


WEIGHT_SETS = {
    "baseline": (0.40, 0.30, 0.20, 0.10),
    "residual_heavy": (0.60, 0.20, 0.15, 0.05),
    "certificate_heavy": (0.25, 0.25, 0.40, 0.10),
    "feasibility_heavy": (0.30, 0.50, 0.15, 0.05),
}


def score_from_components(
    residual_exposure: float,
    infeasibility_penalty: float,
    certificate_penalty: float,
    penalty_method_penalty: float,
    weights: tuple[float, float, float, float],
) -> float:
    wr, wf, wc, wp = weights
    return round(
        wr * residual_exposure
        + wf * infeasibility_penalty
        + wc * certificate_penalty
        + wp * penalty_method_penalty,
        6,
    )


def ordinal_claim_label(
    residual: float,
    encoded_feasible: bool,
    has_certificate: bool,
    penalty_selected: bool,
) -> tuple[str, str]:
    if residual > 0.0:
        return "high claim risk", "positive residual blocks encoded-compliance wording"
    if not encoded_feasible:
        return "high claim risk", "encoded feasibility is not supported"
    if not has_certificate:
        return "moderate claim risk", "residual is zero, but no explicit certificate or enumeration route is recorded"
    if penalty_selected:
        return "moderate claim risk", "penalty-selected feasible candidate needs independent certificate wording"
    return "low claim risk", "zero residual, valid encoded feasibility, and recorded verification route"


def claim_risk(row: dict[str, str]) -> dict[str, str]:
    residual = to_float(row["max_normalized_residual"])
    encoded_feasible = str(row["encoded_feasible"]).strip().lower() in {"yes", "true"}
    method = row["solver_or_method"].lower()
    case = row["case"].lower()

    residual_exposure = min(1.0, residual)
    infeasibility_penalty = 0.0 if encoded_feasible else 1.0
    has_certificate = "pulp" in method or "exhaustive" in method or "enumeration" in method
    certificate_penalty = 0.0 if has_certificate else 0.5
    penalty_selected = "penalty" in case
    penalty_method_penalty = 0.5 if penalty_selected else 0.0

    # The editorial decision is ordinal, not driven by arbitrary weights. The
    # numeric score is retained only as a reproducible audit index and is checked
    # by cgc_claim_risk_sensitivity.csv under several plausible weight sets.
    label, rule_basis = ordinal_claim_label(
        residual, encoded_feasible, has_certificate, penalty_selected
    )
    score = score_from_components(
        residual_exposure,
        infeasibility_penalty,
        certificate_penalty,
        penalty_method_penalty,
        WEIGHT_SETS["baseline"],
    )

    supported_claim = (
        "conditional encoded-compliance claim"
        if label == "low claim risk"
        else "optimization result only; compliance claim not supported"
    )

    return {
        "benchmark": row["benchmark"],
        "case": row["case"],
        "encoded_feasible": row["encoded_feasible"],
        "max_normalized_residual": row["max_normalized_residual"],
        "solver_or_method": row["solver_or_method"],
        "runtime_scope": row["runtime_scope"],
        "response_support_status": row.get("response_support_status", "not_performed"),
        "full_code_validation_status": row.get("full_code_validation_status", "not_performed"),
        "supported_claim_level": row.get("supported_claim_level", "encoded-only"),
        "claim_risk_score": f"{score:.6f}",
        "claim_risk_label": label,
        "ordinal_rule_basis": rule_basis,
        "supported_claim": supported_claim,
    }


def sensitivity_rows(row: dict[str, str]) -> list[dict[str, str]]:
    residual = to_float(row["max_normalized_residual"])
    encoded_feasible = str(row["encoded_feasible"]).strip().lower() in {"yes", "true"}
    method = row["solver_or_method"].lower()
    case = row["case"].lower()
    residual_exposure = min(1.0, residual)
    infeasibility_penalty = 0.0 if encoded_feasible else 1.0
    has_certificate = "pulp" in method or "exhaustive" in method or "enumeration" in method
    certificate_penalty = 0.0 if has_certificate else 0.5
    penalty_method_penalty = 0.5 if "penalty" in case else 0.0
    ordinal_label, _ = ordinal_claim_label(
        residual, encoded_feasible, has_certificate, "penalty" in case
    )
    rows = []
    for name, weights in WEIGHT_SETS.items():
        score = score_from_components(
            residual_exposure,
            infeasibility_penalty,
            certificate_penalty,
            penalty_method_penalty,
            weights,
        )
        rows.append(
            {
                "benchmark": row["benchmark"],
                "case": row["case"],
                "weight_set": name,
                "score": f"{score:.6f}",
                "ordinal_label": ordinal_label,
            }
        )
    return rows


def main() -> None:
    with SUMMARY.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    out_rows = [claim_risk(row) for row in rows]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    sensitivity = [s for row in rows for s in sensitivity_rows(row)]
    with SENSITIVITY_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(sensitivity[0].keys()))
        writer.writeheader()
        writer.writerows(sensitivity)

    high = [r for r in out_rows if r["claim_risk_label"] == "high claim risk"]
    low = [r for r in out_rows if r["claim_risk_label"] == "low claim risk"]
    OUT_TXT.write_text(
        "\n".join(
            [
                "Claim-risk benchmark for conditional compliance certificates.",
                "Purpose: quantify when an optimized or generated design supports only an optimization-result claim versus a conditional encoded-compliance claim.",
                "Primary classification is ordinal: positive residual or unsupported encoded feasibility yields high claim risk; zero residual plus encoded feasibility but no recorded certificate yields moderate claim risk; zero residual plus encoded feasibility plus recorded enumeration/solver route yields low claim risk.",
                "The numeric score is not a safety factor and not a code approval metric; it is a secondary reproducible audit index based on residual exposure, encoded feasibility, certificate availability, and penalty-only selection.",
                f"Sensitivity file: {SENSITIVITY_CSV.name}; weight sets evaluated: {', '.join(WEIGHT_SETS)}.",
                f"Rows evaluated: {len(out_rows)}.",
                f"Low-risk claim rows: {len(low)}.",
                f"High-risk claim rows: {len(high)}.",
                "This benchmark is the novelty pivot of the manuscript: it evaluates the epistemic status of the claim attached to an optimization result, not only the objective value.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(OUT_CSV)
    print(SENSITIVITY_CSV)
    print(OUT_TXT)


if __name__ == "__main__":
    main()



