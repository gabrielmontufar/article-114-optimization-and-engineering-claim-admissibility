from pathlib import Path
import csv
from itertools import product
import sys
import time

import numpy as np

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / "vendor_pulp"))

import pulp

from cgc_ten_bar_truss_benchmark import analyze
from cgc_ten_bar_truss_exhaustive_grouped import CATALOG as TRUSS_CATALOG, GROUPS, expand_grouped
from cgc_portal_frame_code_benchmark import CATALOG as PORTAL_CATALOG, evaluate


OUT_CSV = BASE / "cgc_milp_crosscheck_pulp_results.csv"
OUT_LOG = BASE / "cgc_milp_crosscheck_pulp_log.txt"


def solve_candidate_milp(name, candidates):
    problem = pulp.LpProblem(name, pulp.LpMinimize)
    y = [pulp.LpVariable(f"y_{i}", cat="Binary") for i in range(len(candidates))]
    problem += pulp.lpSum(c["weight"] * y_i for c, y_i in zip(candidates, y))
    problem += pulp.lpSum(y) == 1
    solver = pulp.PULP_CBC_CMD(msg=False)
    start = time.perf_counter()
    status_code = problem.solve(solver)
    elapsed = time.perf_counter() - start
    selected = max(range(len(y)), key=lambda i: y[i].value() or 0.0)
    return {
        "benchmark": name,
        "solver": "PuLP CBC",
        "pulp_version": pulp.__version__,
        "status": pulp.LpStatus[status_code],
        "objective": pulp.value(problem.objective),
        "candidate_count": len(candidates),
        "binary_variables": len(candidates),
        "constraints": 1,
        "elapsed_s": elapsed,
        "selected_index": selected,
        **candidates[selected],
    }


def truss_candidates():
    candidates = []
    total = 0
    for values in product(TRUSS_CATALOG.tolist(), repeat=len(GROUPS)):
        total += 1
        values = np.array(values, dtype=float)
        result = analyze(expand_grouped(values))
        if result is None:
            continue
        result["constructability_residual"] = 0.0
        if result["stress_residual"] <= 1e-9 and result["disp_residual"] <= 1e-9:
            candidates.append(
                {
                    "weight": result["weight_lb"],
                    "total_enumerated": total,
                    "feasible_candidates": 0,  # filled after enumeration
                    "design": " ".join(f"{v:.3f}" for v in values),
                    "max_stress_ratio": result["max_stress_ratio"],
                    "max_disp_ratio": result["max_disp_ratio"],
                    "stress_residual": result["stress_residual"],
                    "disp_residual": result["disp_residual"],
                    "constructability_residual": result["constructability_residual"],
                }
            )
    for c in candidates:
        c["total_enumerated"] = total
        c["feasible_candidates"] = len(candidates)
    return candidates


def portal_candidates():
    candidates = []
    total = 0
    for column, beam in product(PORTAL_CATALOG, PORTAL_CATALOG):
        total += 1
        row = evaluate(column, beam)
        if row["encoded_feasible"]:
            candidates.append(
                {
                    "weight": row["weight_proxy"],
                    "total_enumerated": total,
                    "feasible_candidates": 0,
                    "design": f"column={row['column']}; beam={row['beam']}",
                    "max_stress_ratio": max(row["column_dcr"], row["beam_dcr"]),
                    "max_disp_ratio": row["drift_ratio"],
                    "stress_residual": max(row["column_strength_residual"], row["beam_strength_residual"]),
                    "disp_residual": row["drift_residual"],
                    "constructability_residual": 0.0,
                    "scwb_ratio": row["scwb_ratio"],
                    "column_shear_ratio": row["column_shear_ratio"],
                    "beam_shear_ratio": row["beam_shear_ratio"],
                }
            )
    for c in candidates:
        c["total_enumerated"] = total
        c["feasible_candidates"] = len(candidates)
    return candidates


def main():
    results = [
        solve_candidate_milp("grouped_ten_bar_truss", truss_candidates()),
        solve_candidate_milp("portal_frame_code_like", portal_candidates()),
    ]
    fields = sorted({k for row in results for k in row.keys()})
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    with OUT_LOG.open("w", encoding="utf-8") as f:
        for row in results:
            f.write(f"benchmark={row['benchmark']}\n")
            f.write(f"solver={row['solver']}\n")
            f.write(f"pulp_version={row['pulp_version']}\n")
            f.write(f"status={row['status']}\n")
            f.write(f"objective={row['objective']}\n")
            f.write(f"total_enumerated={row['total_enumerated']}\n")
            f.write(f"feasible_candidates={row['feasible_candidates']}\n")
            f.write(f"binary_variables={row['binary_variables']}\n")
            f.write(f"constraints={row['constraints']}\n")
            f.write(f"elapsed_s={row['elapsed_s']:.6f}\n")
            f.write(f"design={row['design']}\n\n")
    print(OUT_CSV)
    print(OUT_LOG)


if __name__ == "__main__":
    main()




