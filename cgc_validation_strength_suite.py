from __future__ import annotations

import csv
import random
import statistics as stats
import time
from itertools import product
from pathlib import Path

import numpy as np

from cgc_ten_bar_truss_benchmark import analyze, penalty_score
from cgc_ten_bar_truss_exhaustive_grouped import CATALOG, GROUPS, expand_grouped


BASE = Path(__file__).resolve().parent
OUT_RUNS = BASE / "cgc_validation_multiseed_runs.csv"
OUT_SUMMARY = BASE / "cgc_validation_strength_summary.csv"
OUT_NOTE = BASE / "cgc_validation_strength_note.txt"

SEEDS = list(range(202600, 202620))
SAMPLES_PER_SEED = 1000
PENALTY_WEIGHTS = [100, 1000, 5000, 20000]
TOL = 1e-9


def feasible(result: dict[str, float]) -> bool:
    return (
        result["stress_residual"] <= TOL
        and result["disp_residual"] <= TOL
        and result["constructability_residual"] <= TOL
    )


def max_residual(result: dict[str, float]) -> float:
    return max(result["stress_residual"], result["disp_residual"], result["constructability_residual"])


def exact_grouped_ground_truth() -> tuple[float, int, int]:
    best_weight = float("inf")
    feasible_count = 0
    candidate_count = 0
    for values in product(CATALOG.tolist(), repeat=len(GROUPS)):
        candidate_count += 1
        values_arr = np.array(values, dtype=float)
        result = analyze(expand_grouped(values_arr))
        if result is None:
            continue
        result["constructability_residual"] = 0.0
        if feasible(result):
            feasible_count += 1
            best_weight = min(best_weight, result["weight_lb"])
    return best_weight, feasible_count, candidate_count


def sample_grouped(seed: int, samples: int) -> list[tuple[np.ndarray, dict[str, float]]]:
    rng = random.Random(seed)
    rows: list[tuple[np.ndarray, dict[str, float]]] = []
    catalog_list = CATALOG.tolist()
    for _ in range(samples):
        values = np.array([rng.choice(catalog_list) for _ in GROUPS], dtype=float)
        result = analyze(expand_grouped(values))
        if result is None:
            continue
        result["constructability_residual"] = 0.0
        rows.append((values, result))
    return rows


def run_validation() -> None:
    start = time.perf_counter()
    exact_best, exact_feasible, exact_candidates = exact_grouped_ground_truth()
    exact_elapsed = time.perf_counter() - start

    run_rows: list[dict[str, str]] = []
    for seed in SEEDS:
        sampled = sample_grouped(seed, SAMPLES_PER_SEED)
        for strategy in ["hard_random"] + [f"penalty_w_{w}" for w in PENALTY_WEIGHTS]:
            if strategy == "hard_random":
                feasible_rows = [(v, r) for v, r in sampled if feasible(r)]
                if feasible_rows:
                    values, result = min(feasible_rows, key=lambda item: item[1]["weight_lb"])
                else:
                    values, result = sampled[0]
            else:
                weight = int(strategy.split("_")[-1])
                values, result = min(sampled, key=lambda item: penalty_score(item[1], weight))

            is_feasible = feasible(result)
            gap = (
                (result["weight_lb"] - exact_best) / exact_best
                if is_feasible and exact_best > 0
                else ""
            )
            run_rows.append(
                {
                    "seed": str(seed),
                    "strategy": strategy,
                    "samples": str(SAMPLES_PER_SEED),
                    "weight_lb": f"{result['weight_lb']:.6f}",
                    "max_stress_ratio": f"{result['max_stress_ratio']:.6f}",
                    "max_disp_ratio": f"{result['max_disp_ratio']:.6f}",
                    "max_residual": f"{max_residual(result):.6f}",
                    "encoded_feasible": "yes" if is_feasible else "no",
                    "optimality_gap_vs_exact": "" if gap == "" else f"{gap:.6f}",
                    "group_areas_in2": " ".join(f"{v:.3f}" for v in values),
                }
            )

    with OUT_RUNS.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(run_rows[0].keys()))
        writer.writeheader()
        writer.writerows(run_rows)

    summary_rows = []
    for strategy in sorted({r["strategy"] for r in run_rows}):
        rows = [r for r in run_rows if r["strategy"] == strategy]
        feasible_rows = [r for r in rows if r["encoded_feasible"] == "yes"]
        gaps = [float(r["optimality_gap_vs_exact"]) for r in feasible_rows if r["optimality_gap_vs_exact"]]
        residuals = [float(r["max_residual"]) for r in rows]
        summary_rows.append(
            {
                "strategy": strategy,
                "runs": str(len(rows)),
                "samples_per_seed": str(SAMPLES_PER_SEED),
                "feasible_hit_rate": f"{len(feasible_rows) / len(rows):.3f}",
                "mean_max_residual": f"{stats.mean(residuals):.6f}",
                "max_max_residual": f"{max(residuals):.6f}",
                "mean_optimality_gap_vs_exact_feasible_only": "" if not gaps else f"{stats.mean(gaps):.6f}",
                "best_optimality_gap_vs_exact_feasible_only": "" if not gaps else f"{min(gaps):.6f}",
            }
        )

    with OUT_SUMMARY.open("w", newline="", encoding="utf-8") as f:
        fields = list(summary_rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary_rows)

    OUT_NOTE.write_text(
        "\n".join(
            [
                "Validation-strength suite for encoded-claim engineering optimization.",
                f"Exact grouped ground truth: {exact_candidates} candidates, {exact_feasible} encoded-feasible candidates, best feasible weight {exact_best:.6f} lb.",
                f"Exact enumeration wall-clock time in this run: {exact_elapsed:.3f} s.",
                f"Multi-seed calibration: {len(SEEDS)} seeds, {SAMPLES_PER_SEED} random grouped-catalog samples per seed.",
                "Purpose: test whether penalty-selected or randomly sampled candidates support encoded-compliance claims when compared against exact enumeration ground truth.",
                "Outputs: cgc_validation_multiseed_runs.csv and cgc_validation_strength_summary.csv.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(OUT_RUNS)
    print(OUT_SUMMARY)
    print(OUT_NOTE)


if __name__ == "__main__":
    run_validation()



