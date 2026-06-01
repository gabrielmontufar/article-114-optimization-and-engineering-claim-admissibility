from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import openseespy.opensees as ops

from cgc_ten_bar_truss_benchmark import (
    ALLOWABLE_DISPLACEMENT,
    ALLOWABLE_STRESS,
    E,
    FIXED_DOF,
    LOAD,
    MEMBERS,
    NODES,
    analyze,
)
from cgc_ten_bar_truss_exhaustive_grouped import expand_grouped


BASE = Path(__file__).resolve().parent
EXHAUSTIVE_CSV = BASE / "cgc_ten_bar_truss_exhaustive_grouped_results.csv"
RUNS_CSV = BASE / "cgc_validation_multiseed_runs.csv"
OUT_CSV = BASE / "cgc_opensees_blind_crosscheck.csv"
OUT_NOTE = BASE / "cgc_opensees_blind_crosscheck_note.txt"


def opensees_analyze(areas: np.ndarray) -> dict[str, float] | None:
    ops.wipe()
    ops.model("basic", "-ndm", 2, "-ndf", 2)

    for node_id, (x, y) in enumerate(NODES, start=1):
        ops.node(node_id, float(x), float(y))

    fixed_nodes = sorted({int(dof // 2) + 1 for dof in FIXED_DOF})
    for node_id in fixed_nodes:
        ops.fix(node_id, 1, 1)

    ops.uniaxialMaterial("Elastic", 1, float(E))
    for ele_id, (area, (i, j)) in enumerate(zip(areas, MEMBERS), start=1):
        ops.element("truss", ele_id, int(i) + 1, int(j) + 1, float(area), 1)

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    for node_id in range(1, len(NODES) + 1):
        fx = LOAD[2 * (node_id - 1)]
        fy = LOAD[2 * (node_id - 1) + 1]
        if abs(fx) > 0 or abs(fy) > 0:
            ops.load(node_id, float(fx), float(fy))

    ops.constraints("Plain")
    ops.numberer("Plain")
    ops.system("FullGeneral")
    ops.test("NormDispIncr", 1.0e-12, 10)
    ops.algorithm("Linear")
    ops.integrator("LoadControl", 1.0)
    ops.analysis("Static")
    status = ops.analyze(1)
    if status != 0:
        return None

    u = np.zeros(2 * len(NODES))
    for node_id in range(1, len(NODES) + 1):
        disp = ops.nodeDisp(node_id)
        u[2 * (node_id - 1)] = disp[0]
        u[2 * (node_id - 1) + 1] = disp[1]

    stresses = []
    lengths = []
    for (i, j) in MEMBERS:
        xi, yi = NODES[i]
        xj, yj = NODES[j]
        dx, dy = xj - xi, yj - yi
        length = float(np.hypot(dx, dy))
        c, s = dx / length, dy / length
        dof = [2 * i, 2 * i + 1, 2 * j, 2 * j + 1]
        local_extension = np.array([-c, -s, c, s]) @ u[dof]
        stresses.append(E * local_extension / length)
        lengths.append(length)

    stresses = np.array(stresses)
    max_stress_ratio = float(np.max(np.abs(stresses)) / ALLOWABLE_STRESS)
    max_disp_ratio = float(np.max(np.abs(u)) / ALLOWABLE_DISPLACEMENT)
    return {
        "max_stress_ratio": max_stress_ratio,
        "max_disp_ratio": max_disp_ratio,
        "stress_residual": max(0.0, max_stress_ratio - 1.0),
        "disp_residual": max(0.0, max_disp_ratio - 1.0),
        "max_abs_displacement": float(np.max(np.abs(u))),
        "max_abs_stress": float(np.max(np.abs(stresses))),
    }


def parse_areas(text: str) -> np.ndarray:
    values = np.array([float(x) for x in text.split()], dtype=float)
    if len(values) == 5:
        return expand_grouped(values)
    if len(values) == 10:
        return values
    raise ValueError(f"Expected 5 grouped or 10 member areas, got {len(values)}")


def feasible(result: dict[str, float]) -> bool:
    return result["stress_residual"] <= 1.0e-9 and result["disp_residual"] <= 1.0e-9


def rows_to_check() -> list[tuple[str, np.ndarray]]:
    cases: list[tuple[str, np.ndarray]] = []
    with EXHAUSTIVE_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row = {k.strip("\ufeff"): v for k, v in row.items()}
            cases.append((f"exhaustive::{row['case']}", parse_areas(row["group_areas_in2"])))

    with RUNS_CSV.open(newline="", encoding="utf-8") as f:
        for idx, row in enumerate(csv.DictReader(f)):
            row = {k.strip("\ufeff"): v for k, v in row.items()}
            if idx >= 40:
                break
            cases.append((f"blind_seed_{row['seed']}::{row['strategy']}", parse_areas(row["group_areas_in2"])))
    return cases


def main() -> None:
    rows = []
    for case, areas in rows_to_check():
        native = analyze(areas)
        external = opensees_analyze(areas)
        if native is None or external is None:
            rows.append(
                {
                    "case": case,
                    "status": "solver_failure",
                    "native_feasible": "",
                    "opensees_feasible": "",
                    "max_stress_ratio_abs_diff": "",
                    "max_disp_ratio_abs_diff": "",
                    "classification_match": "no",
                    "member_areas_in2": " ".join(f"{x:.3f}" for x in areas),
                }
            )
            continue

        native_feasible = feasible(native)
        external_feasible = feasible(external)
        rows.append(
            {
                "case": case,
                "status": "ok",
                "native_feasible": "yes" if native_feasible else "no",
                "opensees_feasible": "yes" if external_feasible else "no",
                "native_max_stress_ratio": f"{native['max_stress_ratio']:.12f}",
                "opensees_max_stress_ratio": f"{external['max_stress_ratio']:.12f}",
                "native_max_disp_ratio": f"{native['max_disp_ratio']:.12f}",
                "opensees_max_disp_ratio": f"{external['max_disp_ratio']:.12f}",
                "max_stress_ratio_abs_diff": f"{abs(native['max_stress_ratio'] - external['max_stress_ratio']):.12e}",
                "max_disp_ratio_abs_diff": f"{abs(native['max_disp_ratio'] - external['max_disp_ratio']):.12e}",
                "classification_match": "yes" if native_feasible == external_feasible else "no",
                "member_areas_in2": " ".join(f"{x:.3f}" for x in areas),
            }
        )

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    ok_rows = [r for r in rows if r["status"] == "ok"]
    mismatches = [r for r in ok_rows if r["classification_match"] != "yes"]
    max_stress_diff = max(float(r["max_stress_ratio_abs_diff"]) for r in ok_rows)
    max_disp_diff = max(float(r["max_disp_ratio_abs_diff"]) for r in ok_rows)
    OUT_NOTE.write_text(
        "\n".join(
            [
                "OpenSeesPy blind cross-check for the ten-bar encoded-claim benchmark.",
                f"Cases checked: {len(rows)}; successful OpenSeesPy solves: {len(ok_rows)}.",
                f"Feasibility-classification mismatches: {len(mismatches)}.",
                f"Maximum absolute stress-ratio difference: {max_stress_diff:.12e}.",
                f"Maximum absolute displacement-ratio difference: {max_disp_diff:.12e}.",
                "Purpose: independently check the custom stiffness-matrix evaluator against an external open-source FEM engine.",
                "Outputs: cgc_opensees_blind_crosscheck.csv and this note.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(OUT_CSV)
    print(OUT_NOTE)
    print(f"cases={len(rows)} mismatches={len(mismatches)} max_stress_diff={max_stress_diff:.3e} max_disp_diff={max_disp_diff:.3e}")


if __name__ == "__main__":
    main()



