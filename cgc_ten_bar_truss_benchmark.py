from pathlib import Path
import csv
import math
import random
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parent
OUT_CSV = BASE / "cgc_ten_bar_truss_results.csv"
OUT_PNG = BASE / "cgc_ten_bar_truss_results.png"

E = 10_000_000.0  # psi
RHO = 0.1  # lb/in^3
ALLOWABLE_STRESS = 25_000.0  # psi
ALLOWABLE_DISPLACEMENT = 2.0  # in
MIN_AREA = 0.5  # in^2
MAX_AREA = 35.0  # in^2
CATALOG = np.array([0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0])

NODES = np.array(
    [
        [0.0, 0.0],
        [360.0, 0.0],
        [720.0, 0.0],
        [0.0, 360.0],
        [360.0, 360.0],
        [720.0, 360.0],
    ]
)
MEMBERS = np.array(
    [
        [0, 1],
        [1, 2],
        [3, 4],
        [4, 5],
        [1, 4],
        [2, 5],
        [0, 4],
        [1, 3],
        [1, 5],
        [2, 4],
    ]
)
FIXED_DOF = np.array([0, 1, 6, 7])
LOAD = np.zeros(12)
LOAD[5] = -100_000.0
LOAD[11] = -100_000.0


def analyze(areas):
    ndof = 2 * len(NODES)
    k = np.zeros((ndof, ndof))
    lengths = []
    cosines = []

    for area, (i, j) in zip(areas, MEMBERS):
        xi, yi = NODES[i]
        xj, yj = NODES[j]
        dx, dy = xj - xi, yj - yi
        length = math.hypot(dx, dy)
        c, s = dx / length, dy / length
        lengths.append(length)
        cosines.append((c, s))
        ke = (E * area / length) * np.array(
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
        u[free] = np.linalg.solve(k[np.ix_(free, free)], LOAD[free])
    except np.linalg.LinAlgError:
        return None

    stresses = []
    for area, (i, j), length, (c, s) in zip(areas, MEMBERS, lengths, cosines):
        dof = [2 * i, 2 * i + 1, 2 * j, 2 * j + 1]
        local_extension = np.array([-c, -s, c, s]) @ u[dof]
        stresses.append(E * local_extension / length)

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
        "constructability_residual": 0.0 if np.all(np.isin(np.round(areas, 6), CATALOG)) else 1.0,
        "areas": areas.copy(),
    }


def penalty_score(result, penalty_weight):
    return result["weight_lb"] + penalty_weight * (
        result["stress_residual"] + result["disp_residual"] + result["constructability_residual"]
    )


def random_catalog_search(seed, samples, penalty_weight=None, hard=False):
    rng = random.Random(seed)
    best = None
    best_score = float("inf")
    start = time.perf_counter()
    for _ in range(samples):
        areas = np.array([rng.choice(CATALOG.tolist()) for _ in range(len(MEMBERS))], dtype=float)
        result = analyze(areas)
        if result is None:
            continue
        if hard and (result["stress_residual"] > 1e-9 or result["disp_residual"] > 1e-9):
            continue
        score = penalty_score(result, penalty_weight) if penalty_weight is not None else result["weight_lb"]
        if score < best_score:
            best_score = score
            best = result
    elapsed = time.perf_counter() - start
    return best, best_score, elapsed


def coordinate_improve_catalog(initial, hard=True, max_passes=25):
    best = analyze(np.array(initial, dtype=float))
    if best is None:
        return None
    if hard and (best["stress_residual"] > 1e-9 or best["disp_residual"] > 1e-9):
        return None
    improved = True
    passes = 0
    while improved and passes < max_passes:
        passes += 1
        improved = False
        for member_index in range(len(MEMBERS)):
            current_area = best["areas"][member_index]
            for candidate_area in CATALOG[CATALOG < current_area][::-1]:
                trial_areas = best["areas"].copy()
                trial_areas[member_index] = candidate_area
                trial = analyze(trial_areas)
                if trial is None:
                    continue
                if hard and (trial["stress_residual"] > 1e-9 or trial["disp_residual"] > 1e-9):
                    continue
                if trial["weight_lb"] + 1e-9 < best["weight_lb"]:
                    best = trial
                    improved = True
                    break
    return best


def deterministic_continuous_feasible():
    areas = np.full(len(MEMBERS), MAX_AREA, dtype=float)
    best = analyze(areas)
    for member_index in range(len(MEMBERS)):
        low, high = MIN_AREA, areas[member_index]
        for _ in range(45):
            mid = 0.5 * (low + high)
            trial_areas = areas.copy()
            trial_areas[member_index] = mid
            trial = analyze(trial_areas)
            if trial and trial["stress_residual"] <= 1e-9 and trial["disp_residual"] <= 1e-9:
                high = mid
                best = trial
            else:
                low = mid
        areas[member_index] = high
    return best


def continuous_random_search(seed, samples):
    rng = random.Random(seed)
    best = None
    start = time.perf_counter()
    for _ in range(samples):
        areas = np.array([rng.uniform(MIN_AREA, MAX_AREA) for _ in range(len(MEMBERS))], dtype=float)
        result = analyze(areas)
        if result is None:
            continue
        if result["stress_residual"] <= 1e-9 and result["disp_residual"] <= 1e-9:
            if best is None or result["weight_lb"] < best["weight_lb"]:
                best = result
    elapsed = time.perf_counter() - start
    return best, elapsed


def write_png(rows):
    width, height = 1500, 650
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
        small = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
        small = ImageFont.load_default()
    draw.text((40, 30), "Ten-bar truss conditional encoded-claim benchmark", fill="black", font=font)
    cols = ["Formulation", "Weight", "Stress res.", "Disp. res.", "Catalog res.", "Claim"]
    xs = [40, 310, 470, 650, 830, 1030]
    y = 90
    for x, col in zip(xs, cols):
        draw.text((x, y), col, fill="black", font=small)
    y += 35
    draw.line((40, y, 1460, y), fill=(120, 120, 120), width=2)
    y += 20
    for row in rows:
        values = [
            row["formulation"],
            f"{float(row['weight_lb']):.1f}",
            f"{float(row['stress_residual']):.3f}",
            f"{float(row['disp_residual']):.3f}",
            f"{float(row['constructability_residual']):.1f}",
            row["supported_claim"],
        ]
        for x, value in zip(xs, values):
            draw.text((x, y), value[:34], fill="black", font=small)
        y += 48
    draw.text(
        (40, 570),
        "Residuals are normalized violations beyond allowable stress, displacement, and catalog membership.",
        fill=(60, 60, 60),
        font=small,
    )
    img.save(OUT_PNG)


def main():
    penalty, penalty_score_value, penalty_time = random_catalog_search(20260508, 30000, penalty_weight=75.0, hard=False)
    continuous, continuous_time = continuous_random_search(20260509, 40000)
    discrete, discrete_score, discrete_time = random_catalog_search(20260510, 60000, hard=True)
    if continuous is None:
        start = time.perf_counter()
        continuous = deterministic_continuous_feasible()
        continuous_time = time.perf_counter() - start
    if discrete is None:
        start = time.perf_counter()
        discrete = coordinate_improve_catalog(np.full(len(MEMBERS), MAX_AREA, dtype=float), hard=True)
        discrete_time = time.perf_counter() - start
    if penalty is None:
        start = time.perf_counter()
        penalty = analyze(np.full(len(MEMBERS), MIN_AREA, dtype=float))
        penalty_time = time.perf_counter() - start
    rows = []
    for formulation, result, method, elapsed, claim in [
        ("soft penalty", penalty, "catalog random search with low penalty weight", penalty_time, "No strict encoded-compliance certificate"),
        ("continuous hard constraints", continuous, "continuous random feasible search", continuous_time, "Mathematical feasibility only"),
        ("discrete MINLP hard constraints", discrete, "catalog random feasible search", discrete_time, "Conditional encoded compliance"),
    ]:
        rows.append(
            {
                "formulation": formulation,
                "method": method,
                "weight_lb": f"{result['weight_lb']:.6f}",
                "max_stress_ratio": f"{result['max_stress_ratio']:.6f}",
                "max_disp_ratio": f"{result['max_disp_ratio']:.6f}",
                "stress_residual": f"{result['stress_residual']:.6f}",
                "disp_residual": f"{result['disp_residual']:.6f}",
                "constructability_residual": f"{result['constructability_residual']:.6f}",
                "elapsed_s": f"{elapsed:.6f}",
                "areas_in2": " ".join(f"{a:.3f}" for a in result["areas"]),
                "supported_claim": claim,
            }
        )
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    write_png(rows)
    print(OUT_CSV)
    print(OUT_PNG)


if __name__ == "__main__":
    main()




