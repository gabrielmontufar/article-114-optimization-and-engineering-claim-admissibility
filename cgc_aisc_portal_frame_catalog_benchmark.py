from __future__ import annotations

import csv
from itertools import product
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parent
AISC_XLSX = BASE / "aisc-shapes-database-v160-2.xlsx"
OUT_CSV = BASE / "cgc_aisc_portal_frame_catalog_benchmark.csv"
OUT_NOTE = BASE / "cgc_aisc_portal_frame_catalog_benchmark_note.txt"
OUT_PNG = BASE / "cgc_aisc_portal_frame_catalog_benchmark.png"

# Simplified single-bay, single-story steel portal frame benchmark.
# Units: in, lb, psi. Section properties are taken from the AISC v16.0
# Shapes Database when the spreadsheet is available locally.
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


def numeric(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def load_aisc_w_shapes() -> list[dict[str, float | str]]:
    if not AISC_XLSX.exists():
        raise FileNotFoundError(f"Missing AISC database: {AISC_XLSX}")
    df = pd.read_excel(AISC_XLSX, sheet_name="Database v16.0")
    df = df[df["Type"].astype(str).str.upper().eq("W")].copy()
    shapes = []
    for _, row in df.iterrows():
        shape = {
            "name": str(row["AISC_Manual_Label"]),
            "W": numeric(row["W"]),
            "A": numeric(row["A"]),
            "d": numeric(row["d"]),
            "tw": numeric(row["tw"]),
            "Ix": numeric(row["Ix"]),
            "Zx": numeric(row["Zx"]),
        }
        if all(pd.notna(shape[k]) for k in ["W", "A", "d", "tw", "Ix", "Zx"]):
            shape["Av"] = float(shape["d"]) * float(shape["tw"])
            shapes.append(shape)
    return shapes


def capacity(section):
    mp = PHI_M * FY * float(section["Zx"])
    vp = PHI_V * 0.6 * FY * float(section["Av"])
    return mp, vp


def evaluate(column, beam):
    weight_lb = 2.0 * float(column["W"]) * (STORY_HEIGHT / 12.0) + float(beam["W"]) * (SPAN / 12.0)

    k_columns = 24.0 * E * float(column["Ix"]) / STORY_HEIGHT**3
    k_beam = 12.0 * E * float(beam["Ix"]) / SPAN**3
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
    max_residual = max(residuals.values())
    return {
        "column": column["name"],
        "beam": beam["name"],
        "column_W_lb_ft": f"{float(column['W']):.3f}",
        "beam_W_lb_ft": f"{float(beam['W']):.3f}",
        "weight_lb": weight_lb,
        "drift_in": drift,
        "drift_ratio": drift_ratio,
        "column_dcr": column_dcr,
        "beam_dcr": beam_dcr,
        "scwb_ratio": scwb_ratio,
        "column_shear_ratio": column_shear_ratio,
        "beam_shear_ratio": beam_shear_ratio,
        **residuals,
        "max_residual": max_residual,
        "encoded_feasible": max_residual <= 1.0e-12,
    }


def penalty_objective(row, penalty_weight):
    return float(row["weight_lb"]) + penalty_weight * float(row["max_residual"])


def draw(summary):
    img = Image.new("RGB", (1700, 720), "white")
    draw = ImageDraw.Draw(img)
    try:
        title = ImageFont.truetype("arial.ttf", 24)
        font = ImageFont.truetype("arial.ttf", 17)
    except OSError:
        title = ImageFont.load_default()
        font = ImageFont.load_default()
    draw.text((40, 28), "AISC W-shape portal-frame catalog benchmark", fill="black", font=title)
    headers = ["Case", "Column", "Beam", "Weight", "Drift", "Col DCR", "Beam DCR", "SC/WB", "Max res.", "Feasible"]
    xs = [40, 320, 450, 580, 700, 820, 960, 1110, 1260, 1420]
    y = 90
    for x, h in zip(xs, headers):
        draw.text((x, y), h, fill="black", font=font)
    y += 35
    draw.line((40, y, 1630, y), fill=(120, 120, 120), width=2)
    y += 22
    for row in summary:
        vals = [
            row["case"],
            row["column"],
            row["beam"],
            f"{float(row['weight_lb']):.0f}",
            f"{float(row['drift_ratio']):.2f}",
            f"{float(row['column_dcr']):.2f}",
            f"{float(row['beam_dcr']):.2f}",
            f"{float(row['scwb_ratio']):.2f}",
            f"{float(row['max_residual']):.2f}",
            row["encoded_feasible"],
        ]
        for x, value in zip(xs, vals):
            draw.text((x, y), str(value)[:28], fill="black", font=font)
        y += 52
    draw.text(
        (40, 635),
        "External catalog source: AISC Shapes Database v16.0 spreadsheet supplied locally; simplified checks are audit constraints, not code approval.",
        fill=(60, 60, 60),
        font=font,
    )
    img.save(OUT_PNG)


def main() -> None:
    shapes = load_aisc_w_shapes()
    all_rows = [evaluate(c, b) for c, b in product(shapes, shapes)]
    feasible = [r for r in all_rows if r["encoded_feasible"]]
    if not feasible:
        raise RuntimeError("No AISC W-shape pair satisfied the encoded portal-frame checks.")

    best_hard = min(feasible, key=lambda r: float(r["weight_lb"]))
    summary = []
    for case, row in [
        ("soft penalty w=500", min(all_rows, key=lambda r: penalty_objective(r, 500.0))),
        ("soft penalty w=20000", min(all_rows, key=lambda r: penalty_objective(r, 20_000.0))),
        ("exhaustive AISC hard constraints", best_hard),
    ]:
        summary.append({"case": case, "candidate_count": len(all_rows), "feasible_count": len(feasible), **row})

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        fields = list(summary[0].keys())
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary)

    OUT_NOTE.write_text(
        "\n".join(
            [
                "AISC W-shape portal-frame catalog benchmark for encoded-claim engineering optimization.",
                f"AISC W-shapes read from local spreadsheet: {len(shapes)}.",
                f"Catalog pairs evaluated: {len(all_rows)}.",
                f"Encoded-feasible pairs: {len(feasible)}.",
                f"Best feasible pair: column {best_hard['column']}, beam {best_hard['beam']}, weight {float(best_hard['weight_lb']):.3f} lb.",
                "Official source page: https://www.aisc.org/aisc/publications/steel-construction-manual/aisc-shapes-database-v160/",
                "Expected local spreadsheet filename: aisc-shapes-database-v160-2.xlsx.",
                "The benchmark replaces the synthetic portal-frame section list with externally sourced AISC W-shape properties.",
                "The checks remain simplified audit constraints and are not a complete AISC code-design approval.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    draw(summary)
    print(OUT_CSV)
    print(OUT_NOTE)
    print(OUT_PNG)
    print(f"shapes={len(shapes)} candidate_count={len(all_rows)} feasible_count={len(feasible)}")


if __name__ == "__main__":
    main()



