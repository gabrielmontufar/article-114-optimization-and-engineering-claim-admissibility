from pathlib import Path
import csv
from itertools import product

from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parent
OUT_CSV = BASE / "cgc_portal_frame_code_results.csv"
OUT_PNG = BASE / "cgc_portal_frame_code_results.png"

# Simplified single-bay, single-story steel portal frame benchmark.
# Units: in, lb, psi. This is a reproducible code-like audit, not a
# substitute for a design-code check.
E = 29_000_000.0
FY = 50_000.0
STORY_HEIGHT = 144.0
SPAN = 240.0
LATERAL_LOAD = 18_000.0
GRAVITY_LINE_LOAD = 400.0
DRIFT_LIMIT = STORY_HEIGHT / 50.0
PHI_M = 0.90
PHI_V = 0.90
SCWB_FACTOR = 1.20
SHEAR_FACTOR = 1.20

CATALOG = [
    {"name": "S1", "A": 7.1, "Ix": 90.0, "Zx": 18.0, "Av": 3.5},
    {"name": "S2", "A": 9.8, "Ix": 170.0, "Zx": 28.0, "Av": 4.8},
    {"name": "S3", "A": 13.2, "Ix": 310.0, "Zx": 43.0, "Av": 6.5},
    {"name": "S4", "A": 18.5, "Ix": 620.0, "Zx": 70.0, "Av": 9.0},
    {"name": "S5", "A": 25.0, "Ix": 1180.0, "Zx": 112.0, "Av": 12.0},
]


def capacity(section):
    mp = PHI_M * FY * section["Zx"]
    vp = PHI_V * 0.6 * FY * section["Av"]
    return mp, vp


def evaluate(column, beam):
    # Two columns and one beam. Weight proxy uses area times member length.
    weight_proxy = 2.0 * column["A"] * STORY_HEIGHT + beam["A"] * SPAN

    # Lateral stiffness approximation for a braced-end portal audit.
    k_columns = 24.0 * E * column["Ix"] / STORY_HEIGHT**3
    k_beam = 12.0 * E * beam["Ix"] / SPAN**3
    drift = LATERAL_LOAD / (k_columns + k_beam)

    col_mp, col_vp = capacity(column)
    beam_mp, beam_vp = capacity(beam)

    column_moment_demand = LATERAL_LOAD * STORY_HEIGHT / 2.0
    beam_moment_demand = GRAVITY_LINE_LOAD * SPAN**2 / 8.0
    column_shear_demand = LATERAL_LOAD / 2.0
    beam_shear_demand = GRAVITY_LINE_LOAD * SPAN / 2.0

    drift_ratio = drift / DRIFT_LIMIT
    column_dcr = column_moment_demand / col_mp
    beam_dcr = beam_moment_demand / beam_mp
    scwb_ratio = (2.0 * col_mp) / (SCWB_FACTOR * beam_mp)
    column_shear_ratio = (SHEAR_FACTOR * column_shear_demand) / col_vp
    beam_shear_ratio = (SHEAR_FACTOR * beam_shear_demand) / beam_vp

    residuals = {
        "drift_residual": max(0.0, drift_ratio - 1.0),
        "column_strength_residual": max(0.0, column_dcr - 1.0),
        "beam_strength_residual": max(0.0, beam_dcr - 1.0),
        "strong_column_weak_beam_residual": max(0.0, 1.0 - scwb_ratio),
        "column_shear_hierarchy_residual": max(0.0, column_shear_ratio - 1.0),
        "beam_shear_hierarchy_residual": max(0.0, beam_shear_ratio - 1.0),
    }
    encoded_feasible = all(v <= 1e-12 for v in residuals.values())
    return {
        "column": column["name"],
        "beam": beam["name"],
        "weight_proxy": weight_proxy,
        "drift_in": drift,
        "drift_ratio": drift_ratio,
        "column_dcr": column_dcr,
        "beam_dcr": beam_dcr,
        "scwb_ratio": scwb_ratio,
        "column_shear_ratio": column_shear_ratio,
        "beam_shear_ratio": beam_shear_ratio,
        **residuals,
        "encoded_feasible": encoded_feasible,
    }


def penalty_objective(row, penalty_weight):
    residual_sum = sum(
        row[k]
        for k in [
            "drift_residual",
            "column_strength_residual",
            "beam_strength_residual",
            "strong_column_weak_beam_residual",
            "column_shear_hierarchy_residual",
            "beam_shear_hierarchy_residual",
        ]
    )
    return row["weight_proxy"] + penalty_weight * residual_sum


def draw_results(rows):
    img = Image.new("RGB", (1600, 650), "white")
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        font = ImageFont.truetype("arial.ttf", 17)
    except OSError:
        title_font = ImageFont.load_default()
        font = ImageFont.load_default()
    draw.text((40, 28), "Portal-frame code-like constraint audit", fill="black", font=title_font)
    headers = ["Case", "Col", "Beam", "Weight", "Drift", "Col DCR", "Beam DCR", "SC/WB", "Feasible"]
    xs = [40, 250, 340, 450, 570, 690, 830, 990, 1160]
    y = 90
    for x, h in zip(xs, headers):
        draw.text((x, y), h, fill="black", font=font)
    y += 35
    draw.line((40, y, 1520, y), fill=(120, 120, 120), width=2)
    y += 22
    for row in rows:
        values = [
            row["case"],
            row["column"],
            row["beam"],
            f"{float(row['weight_proxy']):.0f}",
            f"{float(row['drift_ratio']):.2f}",
            f"{float(row['column_dcr']):.2f}",
            f"{float(row['beam_dcr']):.2f}",
            f"{float(row['scwb_ratio']):.2f}",
            row["encoded_feasible"],
        ]
        for x, value in zip(xs, values):
            draw.text((x, y), str(value)[:24], fill="black", font=font)
        y += 48
    draw.text(
        (40, 570),
        "Code-like checks: drift limit, member strength, strong-column/weak-beam hierarchy, and shear hierarchy.",
        fill=(60, 60, 60),
        font=font,
    )
    img.save(OUT_PNG)


def main():
    all_rows = [evaluate(c, b) for c, b in product(CATALOG, CATALOG)]
    feasible = [r for r in all_rows if r["encoded_feasible"]]
    best_hard = min(feasible, key=lambda r: r["weight_proxy"])
    best_soft = min(all_rows, key=lambda r: penalty_objective(r, 500.0))
    best_soft_high = min(all_rows, key=lambda r: penalty_objective(r, 20_000.0))

    summary = []
    for case, row in [
        ("soft penalty w=500", best_soft),
        ("soft penalty w=20000", best_soft_high),
        ("exhaustive hard constraints", best_hard),
    ]:
        summary.append({"case": case, **row})

    fields = list(summary[0].keys())
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary)

    draw_results(summary)

    print(OUT_CSV)
    print(OUT_PNG)
    print(f"candidate_count={len(all_rows)} feasible_count={len(feasible)}")


if __name__ == "__main__":
    main()




