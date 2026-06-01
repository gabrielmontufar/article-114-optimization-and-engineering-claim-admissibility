from __future__ import annotations

import csv
import hashlib
from pathlib import Path


BASE = Path(__file__).resolve().parent
SOURCE = BASE / "aisc-shapes-database-v160-2.xlsx"
BENCHMARK = BASE / "cgc_aisc_portal_frame_catalog_benchmark.csv"
OUT = BASE / "cgc_aisc_source_traceability.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    benchmark_hash = sha256(BENCHMARK)
    source_hash = sha256(SOURCE) if SOURCE.exists() else "not_in_clean_zip"
    with BENCHMARK.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    best = next(row for row in rows if row["case"] == "exhaustive AISC hard constraints")
    out_row = {
        "source_filename": SOURCE.name,
        "source_sha256_local_verification": source_hash,
        "source_redistributed_in_zip": "no",
        "official_source_page": "https://www.aisc.org/aisc/publications/steel-construction-manual/aisc-shapes-database-v160/",
        "benchmark_output_file": BENCHMARK.name,
        "benchmark_output_sha256": benchmark_hash,
        "w_shapes_read": "289",
        "candidate_pairs_evaluated": best["candidate_count"],
        "feasible_pairs": best["feasible_count"],
        "best_feasible_column": best["column"],
        "best_feasible_beam": best["beam"],
        "best_feasible_weight_lb": best["weight_lb"],
        "scope_note": "AISC W-shape catalog audit under simplified encoded checks; not AISC approval",
    }
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_row.keys()))
        writer.writeheader()
        writer.writerow(out_row)
    print(OUT)


if __name__ == "__main__":
    main()
