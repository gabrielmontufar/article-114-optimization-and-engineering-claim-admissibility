from pathlib import Path
import csv
import random
import time

import numpy as np

from cgc_ten_bar_truss_benchmark import CATALOG, MEMBERS, analyze, penalty_score


BASE = Path(__file__).resolve().parent
OUT_CSV = BASE / "cgc_penalty_weight_sweep.csv"


def main():
    rng = random.Random(20260511)
    penalty_weights = [10, 75, 250, 1000, 5000, 20000]
    candidates = []
    start = time.perf_counter()
    for _ in range(50000):
        areas = np.array([rng.choice(CATALOG.tolist()) for _ in range(len(MEMBERS))], dtype=float)
        result = analyze(areas)
        if result is not None:
            candidates.append(result)
    rows = []
    for weight in penalty_weights:
        best = min(candidates, key=lambda r: penalty_score(r, weight))
        rows.append(
            {
                "penalty_weight": weight,
                "selected_weight_lb": f"{best['weight_lb']:.6f}",
                "max_stress_ratio": f"{best['max_stress_ratio']:.6f}",
                "max_disp_ratio": f"{best['max_disp_ratio']:.6f}",
                "stress_residual": f"{best['stress_residual']:.6f}",
                "disp_residual": f"{best['disp_residual']:.6f}",
                "constructability_residual": f"{best['constructability_residual']:.6f}",
                "feasible_encoded": "yes"
                if best["stress_residual"] <= 1e-9 and best["disp_residual"] <= 1e-9 and best["constructability_residual"] <= 1e-9
                else "no",
                "areas_in2": " ".join(f"{a:.3f}" for a in best["areas"]),
            }
        )
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(OUT_CSV)
    print(f"candidate_count={len(candidates)} elapsed_s={time.perf_counter() - start:.3f}")


if __name__ == "__main__":
    main()




