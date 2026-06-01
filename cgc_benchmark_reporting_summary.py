from __future__ import annotations

import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent


def read_csv(name: str) -> list[dict[str, str]]:
    with (BASE / name).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_runtime_log() -> dict[str, str]:
    log_path = BASE / "run_all_log.txt"
    runtimes: dict[str, str] = {}
    if not log_path.exists():
        return runtimes
    for line in log_path.read_text(encoding="utf-8").splitlines():
        parts = [part.strip() for part in line.split(",")]
        if not parts:
            continue
        script = parts[0]
        elapsed = ""
        for part in parts[1:]:
            if part.startswith("elapsed_s="):
                elapsed = part.split("=", 1)[1]
                break
        if elapsed:
            runtimes[script] = elapsed
    return runtimes


def max_float(row: dict[str, str], fields: list[str]) -> float:
    vals = []
    for field in fields:
        value = row.get(field, "")
        if value not in ("", None):
            vals.append(float(value))
    return max(vals) if vals else 0.0


def main() -> None:
    rows: list[dict[str, str]] = []
    runtimes = read_runtime_log()
    full_code_summary = {}
    full_code_path = BASE / "cgc_portal_frame_clause_support_gate.csv"
    if full_code_path.exists():
        full_code_rows = read_csv("cgc_portal_frame_clause_support_gate.csv")
        if full_code_rows:
            full_code_summary = full_code_rows[0]
    physical_summary = {}
    portal_physical_summary = {}
    truss_physical_summary = {}
    physical_path = BASE / "cgc_response_support_summary.csv"
    if physical_path.exists():
        physical_rows = read_csv("cgc_response_support_summary.csv")
        if physical_rows:
            physical_summary = physical_rows[0]
    portal_physical_path = BASE / "cgc_portal_frame_response_support_summary.csv"
    if portal_physical_path.exists():
        portal_physical_rows = read_csv("cgc_portal_frame_response_support_summary.csv")
        if portal_physical_rows:
            portal_physical_summary = portal_physical_rows[0]
    truss_physical_path = BASE / "cgc_truss_response_support_summary.csv"
    if truss_physical_path.exists():
        truss_physical_rows = read_csv("cgc_truss_response_support_summary.csv")
        if truss_physical_rows:
            truss_physical_summary = truss_physical_rows[0]

    scalar = read_csv("cgc_scalar_benchmark_results.csv")
    for row in scalar:
        rows.append(
            {
                "benchmark": "scalar_catalog",
                "case": row["formulation"],
                "candidate_count": "5",
                "feasible_candidates": "not_applicable",
                "objective_or_weight": row["selected_area_mm2"],
                "max_normalized_residual": str(
                    max_float(
                        row,
                        [
                            "strength_residual",
                            "serviceability_residual",
                            "constructability_residual",
                        ],
                    )
                ),
                "encoded_feasible": "yes"
                if max_float(
                    row,
                    [
                        "strength_residual",
                        "serviceability_residual",
                        "constructability_residual",
                    ],
                )
                == 0
                else "no",
                "solver_or_method": "catalog enumeration",
                "reported_runtime_s": runtimes.get("cgc_scalar_benchmark.py", "not_measured"),
                "runtime_scope": "wall-clock run of cgc_scalar_benchmark.py",
                "code_standard_family": "not_applicable",
                "code_clause_coverage_percent": "0",
                "clause_support_status": "not_applicable",
                "response_support_status": "not_applicable",
                "oracle_comparison_count": "0",
                "classification_mismatch_count": "0",
                "false_certified_count": "0",
                "supported_claim_level": "encoded logic only",
            }
        )

    truss = read_csv("cgc_ten_bar_truss_exhaustive_grouped_results.csv")
    for row in truss:
        rows.append(
            {
                "benchmark": "grouped_ten_bar_truss",
                "case": row["case"],
                "candidate_count": row["candidate_count"],
                "feasible_candidates": row["feasible_count"],
                "objective_or_weight": row["weight_lb"],
                "max_normalized_residual": str(
                    max_float(
                        row,
                        [
                            "stress_residual",
                            "disp_residual",
                            "constructability_residual",
                        ],
                    )
                ),
                "encoded_feasible": row["encoded_feasible"],
                "solver_or_method": "exhaustive grouped catalog enumeration",
                "reported_runtime_s": runtimes.get("cgc_ten_bar_truss_exhaustive_grouped.py", "not_measured"),
                "runtime_scope": "wall-clock run of cgc_ten_bar_truss_exhaustive_grouped.py",
                "code_standard_family": "not_applicable",
                "code_clause_coverage_percent": "0",
                "clause_support_status": "not_applicable",
                "response_support_status": truss_physical_summary.get("response_support_status", "not_applicable"),
                "oracle_comparison_count": "0",
                "classification_mismatch_count": "0",
                "false_certified_count": truss_physical_summary.get("false_certified_count", "0"),
                "supported_claim_level": truss_physical_summary.get(
                    "supported_claim_level",
                    "encoded feasibility; no truss published-response claim",
                ),
            }
        )

    portal = read_csv("cgc_portal_frame_code_results.csv")
    for row in portal:
        rows.append(
            {
                "benchmark": "portal_frame_code_like",
                "case": row["case"],
                "candidate_count": "25",
                "feasible_candidates": "5",
                "objective_or_weight": row["weight_proxy"],
                "max_normalized_residual": str(
                    max_float(
                        row,
                        [
                            "drift_residual",
                            "column_strength_residual",
                            "beam_strength_residual",
                            "strong_column_weak_beam_residual",
                            "column_shear_hierarchy_residual",
                            "beam_shear_hierarchy_residual",
                        ],
                    )
                ),
                "encoded_feasible": str(row["encoded_feasible"]).lower(),
                "solver_or_method": "exhaustive catalog enumeration",
                "reported_runtime_s": runtimes.get("cgc_portal_frame_code_benchmark.py", "not_measured"),
                "runtime_scope": "wall-clock run of cgc_portal_frame_code_benchmark.py",
                "code_standard_family": "ASCE 7-22 / AISC 360-22 simplified checks",
                "code_clause_coverage_percent": full_code_summary.get("code_clause_coverage_percent", "0"),
                "clause_support_status": full_code_summary.get("clause_support_status", "protocol_defined"),
                "response_support_status": portal_physical_summary.get(
                    "response_support_status",
                    physical_summary.get("response_support_status", "protocol_defined"),
                ),
                "oracle_comparison_count": full_code_summary.get("oracle_comparison_count", "0"),
                "classification_mismatch_count": full_code_summary.get("classification_mismatch_count", "0"),
                "false_certified_count": portal_physical_summary.get(
                    "false_certified_count",
                    physical_summary.get("false_certified_count", "0"),
                ),
                "supported_claim_level": portal_physical_summary.get(
                    "supported_claim_level",
                    full_code_summary.get("supported_claim_level", "encoded code-like support"),
                ),
            }
        )

    aisc = read_csv("cgc_aisc_portal_frame_catalog_benchmark.csv")
    for row in aisc:
        rows.append(
            {
                "benchmark": "aisc_w_shape_portal_frame",
                "case": row["case"],
                "candidate_count": row["candidate_count"],
                "feasible_candidates": row["feasible_count"],
                "objective_or_weight": row["weight_lb"],
                "max_normalized_residual": row["max_residual"],
                "encoded_feasible": str(row["encoded_feasible"]).lower(),
                "solver_or_method": "exhaustive AISC W-shape catalog enumeration",
                "reported_runtime_s": runtimes.get("cgc_aisc_portal_frame_catalog_benchmark.py", "not_measured"),
                "runtime_scope": "script reads local AISC v16 spreadsheet and evaluates all column-beam W-shape pairs",
                "code_standard_family": "AISC W-shape catalog audit",
                "code_clause_coverage_percent": full_code_summary.get("code_clause_coverage_percent", "0"),
                "clause_support_status": full_code_summary.get("clause_support_status", "protocol_defined"),
                "response_support_status": portal_physical_summary.get(
                    "response_support_status",
                    physical_summary.get("response_support_status", "protocol_defined"),
                ),
                "oracle_comparison_count": full_code_summary.get("oracle_comparison_count", "0"),
                "classification_mismatch_count": full_code_summary.get("classification_mismatch_count", "0"),
                "false_certified_count": portal_physical_summary.get(
                    "false_certified_count",
                    physical_summary.get("false_certified_count", "0"),
                ),
                "supported_claim_level": "AISC catalog audit plus published published-response support evidence; no AISC approval",
            }
        )

    opensees = read_csv("cgc_opensees_blind_crosscheck.csv")
    ok_opensees = [r for r in opensees if r["status"] == "ok"]
    mismatches = [r for r in ok_opensees if r["classification_match"] != "yes"]
    max_stress_diff = max(float(r["max_stress_ratio_abs_diff"]) for r in ok_opensees)
    max_disp_diff = max(float(r["max_disp_ratio_abs_diff"]) for r in ok_opensees)
    rows.append(
        {
            "benchmark": "openseespy_external_fem_crosscheck",
            "case": "45_case_blind_feasibility_classification",
            "candidate_count": str(len(opensees)),
            "feasible_candidates": f"classification_mismatches={len(mismatches)}",
            "objective_or_weight": "not_applicable",
            "max_normalized_residual": f"max_stress_diff={max_stress_diff:.3e}; max_disp_diff={max_disp_diff:.3e}",
            "encoded_feasible": "yes" if not mismatches else "no",
            "solver_or_method": "OpenSeesPy independent FEM cross-check",
            "reported_runtime_s": "not_measured",
            "runtime_scope": "external FEM agreement check, not optimization runtime",
            "code_standard_family": "not_applicable",
            "code_clause_coverage_percent": "0",
            "clause_support_status": "not_applicable",
            "response_support_status": "not_applicable",
            "oracle_comparison_count": "0",
            "classification_mismatch_count": str(len(mismatches)),
            "false_certified_count": "0",
            "supported_claim_level": "independent computational verification",
        }
    )

    robustness = read_csv("cgc_uncertainty_robustness_probe.csv")
    for row in robustness:
        rows.append(
            {
                "benchmark": "monte_carlo_uncertainty_probe",
                "case": row["case"],
                "candidate_count": row["samples"],
                "feasible_candidates": f"feasible_rate={row['feasible_rate']}",
                "objective_or_weight": row["nominal_weight_lb"],
                "max_normalized_residual": row["max_residual_max"],
                "encoded_feasible": row["robust_encoded_feasible_under_probe"],
                "solver_or_method": row["perturbation_box"],
                "reported_runtime_s": "not_measured",
                "runtime_scope": "Monte Carlo perturbation probe of load and elastic modulus",
                "code_standard_family": "not_applicable",
                "code_clause_coverage_percent": "0",
                "clause_support_status": "not_applicable",
                "response_support_status": "not_applicable",
                "oracle_comparison_count": "0",
                "classification_mismatch_count": "0",
                "false_certified_count": "0",
                "supported_claim_level": "robustness boundary probe; no robust physical claim",
            }
        )

    milp = read_csv("cgc_milp_crosscheck_pulp_results.csv")
    for row in milp:
        rows.append(
            {
                "benchmark": row["benchmark"],
                "case": "PuLP_CBC_cross_check",
                "candidate_count": row["candidate_count"],
                "feasible_candidates": row["feasible_candidates"],
                "objective_or_weight": row["objective"],
                "max_normalized_residual": str(
                    max_float(
                        row,
                        [
                            "stress_residual",
                            "disp_residual",
                            "constructability_residual",
                        ],
                    )
                ),
                "encoded_feasible": "yes" if row["status"] == "Optimal" else "no",
                "solver_or_method": f"{row['solver']} {row['pulp_version']}",
                "reported_runtime_s": row["elapsed_s"],
                "runtime_scope": "MILP solve time after candidate feasible-set construction",
                "code_standard_family": "not_applicable",
                "code_clause_coverage_percent": "0",
                "clause_support_status": "not_applicable",
                "response_support_status": "not_applicable",
                "oracle_comparison_count": "0",
                "classification_mismatch_count": "0",
                "false_certified_count": "0",
                "supported_claim_level": "finite feasible-set selection certificate",
            }
        )

    out = BASE / "cgc_benchmark_reporting_summary.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    note = BASE / "cgc_runtime_reproducibility_note.txt"
    note.write_text(
        "\n".join(
            [
                "Hardware used for local verification: Intel(R) Core(TM) i5-10210U CPU @ 1.60GHz; Microsoft Windows 11 Home Single Language.",
                "Measured wall-clock runtimes are local verification measurements, not universal performance claims.",
                "The PuLP/CBC log reports solver time after feasible candidate sets are constructed; total enumeration wall-clock times are reported separately in cgc_benchmark_reporting_summary.csv.",
                "The AISC benchmark uses a locally supplied AISC Shapes Database v16.0 spreadsheet; the spreadsheet is not redistributed in the clean ZIP.",
                "The OpenSeesPy cross-check verifies finite-element classification agreement and is not counted as an optimization runtime.",
                "The Monte Carlo perturbation probe is a robustness boundary test; it is not used to claim robust response support unless every sampled perturbation remains feasible.",
                "The reporting summary reads reproducibility runtimes from the included run_all_log.txt when available.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(out)
    print(note)


if __name__ == "__main__":
    main()



