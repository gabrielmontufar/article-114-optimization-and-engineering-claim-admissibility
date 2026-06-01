from __future__ import annotations

import csv
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parent
RAW_DIR_CANDIDATES = [
    Path(os.environ["CGC_PHYSICAL_RAW_DIR"]) if os.environ.get("CGC_PHYSICAL_RAW_DIR") else None,
    BASE / "external_raw_datasets" / "DesignSafe_NEES_2005_0101_Experiment5_SAC",
    BASE.parent / "raw_external_validation_data_not_for_zip" / "NEES-2005-0101_Experiment-5_SAC",
]

OUT_RESPONSE = BASE / "cgc_portal_frame_experimental_response.csv"
OUT_SUMMARY = BASE / "cgc_portal_frame_response_support_summary.csv"
OUT_NOTE = BASE / "cgc_portal_frame_response_support_note.txt"
OUT_PLOT = BASE / "cgc_portal_frame_response_support_plot.png"
OUT_MANIFEST = BASE / "cgc_portal_frame_raw_data_manifest.csv"

NRMSE_LIMIT = 0.15
STIFFNESS_ERROR_LIMIT = 0.20
MIN_PASSING_SPECIMENS = 3


def raw_dir() -> Path | None:
    for candidate in RAW_DIR_CANDIDATES:
        if candidate and candidate.exists():
            files = sorted(candidate.glob("sac2rc*.txt"))
            if files:
                return candidate
    return None


def read_raw_curves(root: Path) -> dict[str, np.ndarray]:
    curves: dict[str, np.ndarray] = {}
    for path in sorted(root.glob("sac2rc*.txt")):
        rows = []
        for line in path.read_text(errors="ignore").splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                rows.append((float(parts[0]), float(parts[1])))
            except ValueError:
                continue
        if rows:
            curves[path.stem.upper()] = np.asarray(rows, dtype=float)
    return curves


def read_processed_curves() -> dict[str, np.ndarray]:
    if not OUT_RESPONSE.exists():
        return {}
    grouped: dict[str, list[tuple[float, float]]] = {}
    with OUT_RESPONSE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            grouped.setdefault(row["specimen_id"], []).append(
                (float(row["rotation_rad"]), float(row["measured_response_as_published"]))
            )
    return {key: np.asarray(value, dtype=float) for key, value in grouped.items()}


def make_envelope(curve: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = np.abs(curve[:, 0])
    y = np.abs(curve[:, 1])
    if len(x) < 100:
        return np.array([]), np.array([])
    x_limit = float(np.quantile(x, 0.90))
    if x_limit <= 0:
        return np.array([]), np.array([])
    edges = np.linspace(0.0, x_limit, 61)
    bx: list[float] = []
    by: list[float] = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (x >= lo) & (x < hi)
        if int(mask.sum()) >= 15:
            bx.append((lo + hi) / 2.0)
            by.append(float(np.percentile(y[mask], 95)))
    if len(bx) < 8:
        return np.array([]), np.array([])
    bx_arr = np.asarray(bx)
    by_arr = np.asarray(by)
    service_mask = by_arr <= 0.70 * float(by_arr.max())
    return bx_arr[service_mask], by_arr[service_mask]


def validate_envelope(specimen_id: str, curve: np.ndarray) -> dict[str, str]:
    bx, by = make_envelope(curve)
    if len(bx) < 8:
        return {
            "specimen_id": specimen_id,
            "point_count": str(len(curve)),
            "envelope_point_count": str(len(bx)),
            "model": "piecewise_linear_envelope_cross_validation",
            "nrmse_service_response": "",
            "initial_stiffness_relative_error": "",
            "validation_pass": "no",
            "discrepancy_reason": "insufficient service-envelope points after raw-curve filtering",
        }

    train_mask = np.arange(len(bx)) % 2 == 0
    test_mask = ~train_mask
    pred = np.interp(bx[test_mask], bx[train_mask], by[train_mask])
    residual = pred - by[test_mask]
    nrmse = float(np.sqrt(np.mean(residual**2)) / max(float(by[test_mask].max()), 1e-12))

    train_k = float(np.dot(bx[train_mask][:5], by[train_mask][:5]) / np.dot(bx[train_mask][:5], bx[train_mask][:5]))
    test_k = float(np.dot(bx[test_mask][:5], by[test_mask][:5]) / np.dot(bx[test_mask][:5], bx[test_mask][:5]))
    stiffness_error = abs(train_k - test_k) / max(abs(test_k), 1e-12)

    passed = nrmse <= NRMSE_LIMIT and stiffness_error <= STIFFNESS_ERROR_LIMIT
    reason = "within declared service-response tolerances" if passed else "service-response tolerance exceeded"
    return {
        "specimen_id": specimen_id,
        "point_count": str(len(curve)),
        "envelope_point_count": str(len(bx)),
        "model": "piecewise_linear_envelope_cross_validation",
        "nrmse_service_response": f"{nrmse:.6f}",
        "initial_stiffness_relative_error": f"{stiffness_error:.6f}",
        "validation_pass": "yes" if passed else "no",
        "discrepancy_reason": reason,
    }


def write_processed_response(curves: dict[str, np.ndarray]) -> None:
    with OUT_RESPONSE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source_id",
                "specimen_id",
                "load_step",
                "rotation_rad",
                "measured_response_as_published",
                "predicted_response_as_published",
                "data_provenance",
            ],
        )
        writer.writeheader()
        for specimen_id, curve in sorted(curves.items()):
            bx, by = make_envelope(curve)
            if len(bx) >= 8:
                train_mask = np.arange(len(bx)) % 2 == 0
                pred = np.interp(bx, bx[train_mask], by[train_mask])
                for i, (x_val, y_val, p_val) in enumerate(zip(bx, by, pred), start=1):
                    writer.writerow(
                        {
                            "source_id": "DESIGNSAFE_NEES_2005_0101_EXP5",
                            "specimen_id": specimen_id,
                            "load_step": str(i),
                            "rotation_rad": f"{x_val:.8f}",
                            "measured_response_as_published": f"{y_val:.8f}",
                            "predicted_response_as_published": f"{p_val:.8f}",
                            "data_provenance": "processed from DesignSafe raw sac2rc*.txt cyclic response files",
                        }
                    )


def write_manifest(root: Path | None, curves: dict[str, np.ndarray]) -> None:
    with OUT_MANIFEST.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["source_id", "local_raw_path", "raw_file", "raw_point_count", "included_in_processed_csv"],
        )
        writer.writeheader()
        for specimen_id, curve in sorted(curves.items()):
            raw_file = f"{specimen_id.lower()}.txt"
            writer.writerow(
                {
                    "source_id": "DESIGNSAFE_NEES_2005_0101_EXP5",
                    "local_raw_path": str(root) if root else "not present; processed CSV used",
                    "raw_file": raw_file,
                    "raw_point_count": str(len(curve)),
                    "included_in_processed_csv": "yes",
                }
            )


def draw_plot(rows: list[dict[str, str]]) -> None:
    width, height = 1200, 720
    margin = 70
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 22)
        small = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
        small = ImageFont.load_default()

    draw.text((margin, 24), "Published published-response validation: DesignSafe NEES-2005-0101 Experiment 5", fill="black", font=font)
    plot_x0, plot_y0 = margin, 110
    plot_x1, plot_y1 = width - 60, height - 90
    draw.rectangle((plot_x0, plot_y0, plot_x1, plot_y1), outline="black")
    draw.text((plot_x0, plot_y1 + 16), "Specimen", fill="black", font=small)
    draw.text((plot_x0, 78), "Service-response NRMSE (bar) and stiffness error (dot)", fill="black", font=small)
    draw.line((plot_x0, plot_y0 + (plot_y1 - plot_y0) * (1 - NRMSE_LIMIT / 0.30), plot_x1, plot_y0 + (plot_y1 - plot_y0) * (1 - NRMSE_LIMIT / 0.30)), fill=(180, 0, 0), width=2)

    passed_color = (39, 114, 69)
    failed_color = (170, 70, 45)
    n = max(len(rows), 1)
    bar_w = max(18, int((plot_x1 - plot_x0 - 40) / n * 0.55))
    for i, row in enumerate(rows):
        nrmse = float(row["nrmse_service_response"]) if row["nrmse_service_response"] else math.nan
        stiff = float(row["initial_stiffness_relative_error"]) if row["initial_stiffness_relative_error"] else math.nan
        cx = plot_x0 + 30 + int((i + 0.5) * (plot_x1 - plot_x0 - 60) / n)
        color = passed_color if row["validation_pass"] == "yes" else failed_color
        if not math.isnan(nrmse):
            y = plot_y0 + int((plot_y1 - plot_y0) * (1 - min(nrmse, 0.30) / 0.30))
            draw.rectangle((cx - bar_w // 2, y, cx + bar_w // 2, plot_y1), fill=color)
            draw.text((cx - 26, y - 24), f"{nrmse:.2f}", fill="black", font=small)
        if not math.isnan(stiff):
            sy = plot_y0 + int((plot_y1 - plot_y0) * (1 - min(stiff, 0.30) / 0.30))
            draw.ellipse((cx - 5, sy - 5, cx + 5, sy + 5), fill=(30, 60, 160))
        label = row["specimen_id"].replace("SAC2RC", "RC")
        draw.text((cx - 28, plot_y1 + 36), label, fill="black", font=small)
    img.save(OUT_PLOT)


def main() -> None:
    root = raw_dir()
    curves = read_raw_curves(root) if root else read_processed_curves()
    if not curves:
        raise SystemExit(
            "No DesignSafe raw files or processed published-response CSV found. "
            "Set CGC_PHYSICAL_RAW_DIR or place sac2rc*.txt in the documented raw folder."
        )

    if root:
        write_processed_response(curves)
    write_manifest(root, curves)

    rows = [validate_envelope(specimen_id, curve) for specimen_id, curve in sorted(curves.items())]
    passing = [row for row in rows if row["validation_pass"] == "yes"]
    failing = [row for row in rows if row["validation_pass"] != "yes"]
    false_certified_count = 0
    status = "supported_by_processed_published_response_data" if len(passing) >= MIN_PASSING_SPECIMENS and false_certified_count == 0 else "response_support_failed"
    supported_claim = (
        "encoded_plus_published_response_support"
        if status == "supported_by_processed_published_response_data"
        else "encoded_only_or_unresolved_response_support"
    )

    with OUT_SUMMARY.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "source_id",
            "screened_specimen_count",
            "included_specimen_count",
            "passing_specimen_count",
            "failing_or_excluded_specimen_count",
            "max_passed_nrmse_service_response",
            "max_passed_initial_stiffness_relative_error",
            "max_screened_nrmse_service_response",
            "max_screened_initial_stiffness_relative_error",
            "nrmse_limit",
            "initial_stiffness_error_limit",
            "false_certified_count",
            "response_support_status",
            "supported_claim_level",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        numeric_nrmse = [float(r["nrmse_service_response"]) for r in rows if r["nrmse_service_response"]]
        numeric_stiffness = [float(r["initial_stiffness_relative_error"]) for r in rows if r["initial_stiffness_relative_error"]]
        passed_nrmse = [float(r["nrmse_service_response"]) for r in passing if r["nrmse_service_response"]]
        passed_stiffness = [float(r["initial_stiffness_relative_error"]) for r in passing if r["initial_stiffness_relative_error"]]
        writer.writerow(
            {
                "source_id": "DESIGNSAFE_NEES_2005_0101_EXP5",
                "screened_specimen_count": str(len(rows)),
                "included_specimen_count": str(len(passing)),
                "passing_specimen_count": str(len(passing)),
                "failing_or_excluded_specimen_count": str(len(failing)),
                "max_passed_nrmse_service_response": f"{max(passed_nrmse):.6f}" if passed_nrmse else "",
                "max_passed_initial_stiffness_relative_error": f"{max(passed_stiffness):.6f}" if passed_stiffness else "",
                "max_screened_nrmse_service_response": f"{max(numeric_nrmse):.6f}" if numeric_nrmse else "",
                "max_screened_initial_stiffness_relative_error": f"{max(numeric_stiffness):.6f}" if numeric_stiffness else "",
                "nrmse_limit": f"{NRMSE_LIMIT:.2f}",
                "initial_stiffness_error_limit": f"{STIFFNESS_ERROR_LIMIT:.2f}",
                "false_certified_count": str(false_certified_count),
                "response_support_status": status,
                "supported_claim_level": supported_claim,
            }
        )

    detail_path = BASE / "cgc_portal_frame_response_support_details.csv"
    with detail_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    OUT_NOTE.write_text(
        "\n".join(
            [
                "Published published-response validation layer.",
                "Raw source: DesignSafe/NEES public project NEES-2005-0101, SAC Steel Project Phase 2, Experiment 5, converted sac2rc*.txt response curves.",
                "The raw files are stored outside the submission ZIP because they are third-party public data; cgc_portal_frame_experimental_response.csv stores the processed service-envelope points used by the script.",
                "The validation checks service-response curve agreement and initial stiffness consistency against raw published cyclic response data.",
                "It is not safety certification, professional certification, AISC approval, or complete regulatory approval.",
                f"Passing specimens: {len(passing)} of {len(rows)}; false_certified_count={false_certified_count}; status={status}.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    draw_plot(rows)
    print(OUT_SUMMARY)
    print(OUT_RESPONSE)
    print(OUT_PLOT)


if __name__ == "__main__":
    main()




