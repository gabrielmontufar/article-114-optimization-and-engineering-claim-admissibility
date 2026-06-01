from __future__ import annotations

import csv
import random
from pathlib import Path

import numpy as np

from cgc_ten_bar_truss_benchmark import (
    ALLOWABLE_DISPLACEMENT,
    ALLOWABLE_STRESS,
    E,
    FIXED_DOF,
    LOAD,
    MEMBERS,
    NODES,
    RHO,
)
from cgc_ten_bar_truss_exhaustive_grouped import expand_grouped


BASE = Path(__file__).resolve().parent
OUT_CSV = BASE / "cgc_uncertainty_robustness_probe.csv"
OUT_NOTE = BASE / "cgc_uncertainty_robustness_probe_note.txt"

SEED = 20260520
SAMPLES = 2000
PERTURBATION = 0.10
BEST_GROUPED_AREAS = np.array([32.0, 32.0, 1.0, 24.0, 24.0], dtype=float)
PENALTY_AREAS = np.array([24.0, 40.0, 2.0, 24.0, 24.0], dtype=float)


def analyze_with_params(areas: np.ndarray, elastic_modulus: float, load_scale: float) -> dict[str, float] | None:
    load = LOAD * load_scale
    ndof = 2 * len(NODES)
    k = np.zeros((ndof, ndof))
    lengths = []
    cosines = []

    for area, (i, j) in zip(areas, MEMBERS):
        xi, yi = NODES[i]
        xj, yj = NODES[j]
        dx, dy = xj - xi, yj - yi
        length = float(np.hypot(dx, dy))
        c, s = dx / length, dy / length
        lengths.append(length)
        cosines.append((c, s))
        ke = (elastic_modulus * area / length) * np.array(
            [
                [c * c, c * s, -c * c, -c * s],
                [c * s, s * s, -c * s, -s * s],
                [-c * c, -c * s, c * c, c * s],
                [-c * s, -s * s, c * s, s * s],
            ]
        )
        dof = [2 * i, 2 * i + 1, 2 * j, 2 * j + 1]
        for a in range(4):
            for b in range(4):
                k[dof[a], dof[b]] += ke[a, b]

    free = np.array([d for d in range(ndof) if d not in set(FIXED_DOF)])
    u = np.zeros(ndof)
    try:
        u[free] = np.linalg.solve(k[np.ix_(free, free)], load[free])
    except np.linalg.LinAlgError:
        return None

    stresses = []
    for (i, j), length, (c, s) in zip(MEMBERS, lengths, cosines):
        dof = [2 * i, 2 * i + 1, 2 * j, 2 * j + 1]
        local_extension = np.array([-c, -s, c, s]) @ u[dof]
        stresses.append(elastic_modulus * local_extension / length)

    stresses = np.array(stresses)
    lengths = np.array(lengths)
    weight = RHO * float(np.sum(areas * lengths))
    max_stress_ratio = float(np.max(np.abs(stresses)) / ALLOWABLE_STRESS)
    max_disp_ratio = float(np.max(np.abs(u)) / ALLOWABLE_DISPLACEMENT)
    return {
        "weight_lb": weight,
        "max_stress_ratio": max_stress_ratio,
        "max_disp_ratio": max_disp_ratio,
        "stress_residual": max(0.0, max_stress_ratio - 1.0),
        "disp_residual": max(0.0, max_disp_ratio - 1.0),
        "max_residual": max(0.0, max_stress_ratio - 1.0, max_disp_ratio - 1.0),
    }


def summarize_case(case: str, group_areas: np.ndarray, rng: random.Random) -> dict[str, str]:
    areas = expand_grouped(group_areas)
    rows = []
    for _ in range(SAMPLES):
        load_scale = rng.uniform(1.0 - PERTURBATION, 1.0 + PERTURBATION)
        e_scale = rng.uniform(1.0 - PERTURBATION, 1.0 + PERTURBATION)
        result = analyze_with_params(areas, E * e_scale, load_scale)
        if result is None:
            continue
        rows.append(result)

    max_residuals = [r["max_residual"] for r in rows]
    stress = [r["max_stress_ratio"] for r in rows]
    disp = [r["max_disp_ratio"] for r in rows]
    feasible = [r for r in rows if r["max_residual"] <= 1.0e-9]
    return {
        "case": case,
        "samples": str(len(rows)),
        "perturbation_box": f"+/-{PERTURBATION:.0%} load and elastic modulus",
        "group_areas_in2": " ".join(f"{x:.3f}" for x in group_areas),
        "nominal_weight_lb": f"{rows[0]['weight_lb']:.6f}" if rows else "",
        "feasible_rate": f"{len(feasible) / len(rows):.6f}" if rows else "",
        "max_stress_ratio_mean": f"{float(np.mean(stress)):.6f}",
        "max_stress_ratio_max": f"{float(np.max(stress)):.6f}",
        "max_disp_ratio_mean": f"{float(np.mean(disp)):.6f}",
        "max_disp_ratio_max": f"{float(np.max(disp)):.6f}",
        "max_residual_mean": f"{float(np.mean(max_residuals)):.6f}",
        "max_residual_max": f"{float(np.max(max_residuals)):.6f}",
        "robust_encoded_feasible_under_probe": "yes" if len(feasible) == len(rows) else "no",
    }


def main() -> None:
    rng = random.Random(SEED)
    summary = [
        summarize_case("exact_grouped_certificate_nominal", BEST_GROUPED_AREAS, rng),
        summarize_case("near_boundary_penalty_selected", PENALTY_AREAS, rng),
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    OUT_NOTE.write_text(
        "\n".join(
            [
                "Monte Carlo robustness probe for the ten-bar claim certificate.",
                f"Random seed: {SEED}. Samples per design: {SAMPLES}.",
                f"Independent uniform perturbations: load scale and elastic modulus in [1-{PERTURBATION:.2f}, 1+{PERTURBATION:.2f}].",
                "Purpose: test whether a nominal zero-residual certificate should be described as robust under parameter perturbation.",
                "Interpretation: a nominal encoded-compliance certificate is not automatically a robust certificate; robust wording requires all sampled perturbed residuals to remain zero or an explicit margin argument.",
                "Outputs: cgc_uncertainty_robustness_probe.csv and this note.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(OUT_CSV)
    print(OUT_NOTE)


if __name__ == "__main__":
    main()



