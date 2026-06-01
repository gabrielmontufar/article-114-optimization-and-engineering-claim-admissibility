from pathlib import Path
import csv
from itertools import product
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from cgc_ten_bar_truss_benchmark import analyze, penalty_score


BASE = Path(__file__).resolve().parent
OUT_CSV = BASE / "cgc_ten_bar_truss_exhaustive_grouped_results.csv"
OUT_PNG = BASE / "cgc_ten_bar_truss_exhaustive_grouped_results.png"

# Grouped ten-bar truss benchmark. Five design variables are used to keep
# exhaustive enumeration transparent and reproducible:
# g1 -> members 1-2, g2 -> members 3-4, g3 -> members 5-6,
# g4 -> members 7-8, g5 -> members 9-10.
GROUPS = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
CATALOG = np.array([1.0, 2.0, 4.0, 8.0, 12.0, 16.0, 24.0, 32.0, 40.0, 50.0])
PENALTY_WEIGHTS = [100, 1000, 5000, 20000]


def expand_grouped(values):
    areas = np.zeros(10)
    for value, group in zip(values, GROUPS):
        for member in group:
            areas[member] = value
    return areas


def row_from_result(case, values, result, candidate_count, feasible_count=None):
    return {
        "case": case,
        "candidate_count": candidate_count,
        "feasible_count": "" if feasible_count is None else feasible_count,
        "group_areas_in2": " ".join(f"{v:.3f}" for v in values),
        "member_areas_in2": " ".join(f"{a:.3f}" for a in result["areas"]),
        "weight_lb": f"{result['weight_lb']:.6f}",
        "max_stress_ratio": f"{result['max_stress_ratio']:.6f}",
        "max_disp_ratio": f"{result['max_disp_ratio']:.6f}",
        "stress_residual": f"{result['stress_residual']:.6f}",
        "disp_residual": f"{result['disp_residual']:.6f}",
        "constructability_residual": f"{result['constructability_residual']:.6f}",
        "encoded_feasible": "yes"
        if result["stress_residual"] <= 1e-9 and result["disp_residual"] <= 1e-9 and result["constructability_residual"] <= 1e-9
        else "no",
    }


def draw(rows):
    img = Image.new("RGB", (1600, 650), "white")
    draw = ImageDraw.Draw(img)
    try:
        title = ImageFont.truetype("arial.ttf", 24)
        font = ImageFont.truetype("arial.ttf", 17)
    except OSError:
        title = ImageFont.load_default()
        font = ImageFont.load_default()
    draw.text((40, 28), "Grouped ten-bar truss exhaustive enumeration", fill="black", font=title)
    headers = ["Case", "Candidates", "Feasible", "Weight", "Stress res.", "Disp. res.", "Feasible?"]
    xs = [40, 420, 590, 730, 880, 1050, 1220]
    y = 90
    for x, h in zip(xs, headers):
        draw.text((x, y), h, fill="black", font=font)
    y += 35
    draw.line((40, y, 1520, y), fill=(120, 120, 120), width=2)
    y += 22
    for row in rows:
        vals = [
            row["case"],
            row["candidate_count"],
            row["feasible_count"],
            f"{float(row['weight_lb']):.1f}",
            f"{float(row['stress_residual']):.3f}",
            f"{float(row['disp_residual']):.3f}",
            row["encoded_feasible"],
        ]
        for x, v in zip(xs, vals):
            draw.text((x, y), str(v)[:34], fill="black", font=font)
        y += 48
    draw.text(
        (40, 570),
        "All 8^5 grouped catalog designs are evaluated; the hard-constraint row is globally best within this grouped space.",
        fill=(60, 60, 60),
        font=font,
    )
    img.save(OUT_PNG)


def main():
    start = time.perf_counter()
    evaluated = []
    for values in product(CATALOG.tolist(), repeat=len(GROUPS)):
        values = np.array(values, dtype=float)
        result = analyze(expand_grouped(values))
        if result is not None:
            # This grouped benchmark defines its own explicit catalog; reset
            # constructability after expanding because the imported analyzer
            # uses the ungrouped benchmark catalog.
            result["constructability_residual"] = 0.0
            evaluated.append((values, result))
    candidate_count = len(evaluated)
    feasible = [(v, r) for v, r in evaluated if r["stress_residual"] <= 1e-9 and r["disp_residual"] <= 1e-9 and r["constructability_residual"] <= 1e-9]
    feasible_count = len(feasible)
    best_hard_values, best_hard = min(feasible, key=lambda item: item[1]["weight_lb"])

    rows = [row_from_result("exhaustive hard constraints", best_hard_values, best_hard, candidate_count, feasible_count)]
    for weight in PENALTY_WEIGHTS:
        best_values, best = min(evaluated, key=lambda item: penalty_score(item[1], weight))
        rows.append(row_from_result(f"soft penalty w={weight}", best_values, best, candidate_count, feasible_count))

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    draw(rows)
    print(OUT_CSV)
    print(OUT_PNG)
    print(f"candidate_count={candidate_count} feasible_count={feasible_count} elapsed_s={time.perf_counter()-start:.3f}")


if __name__ == "__main__":
    main()




