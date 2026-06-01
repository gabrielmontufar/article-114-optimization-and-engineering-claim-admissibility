from __future__ import annotations

import csv
import hashlib
import py_compile
import sys
from pathlib import Path
from zipfile import ZipFile, BadZipFile


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
OUT_DETAILS = BASE / "cgc_software_package_integrity_details.csv"
OUT_SUMMARY = BASE / "cgc_software_package_integrity_summary.csv"
OUT_NOTE = BASE / "cgc_software_package_integrity_note.txt"
BENCHMARK_SUMMARY = BASE / "cgc_benchmark_reporting_summary.csv"

REQUIRED_APPLICATION_SCRIPTS = [
    "run_all.py",
    "cgc_benchmark_reporting_summary.py",
    "cgc_claim_risk_benchmark.py",
    "cgc_extended_claim_risk_benchmark.py",
    "cgc_aisc_claim_gate.py",
    "cgc_portal_frame_response_support.py",
    "cgc_truss_response_support.py",
    "cgc_response_support_threshold_sensitivity.py",
    "cgc_aisc_source_traceability.py",
    "cgc_portal_frame_full_code_validation.py",
]

REQUIRED_PRESENTATION_ARTIFACTS = [
    ROOT / "00 Files for Optimization and Engineering upload" / "01 Manuscript" / "An Optimizer Agnostic.docx",
    ROOT / "00 Files for Optimization and Engineering upload" / "01 Manuscript" / "An Optimizer Agnostic.pdf",
    ROOT / "00 Files for Optimization and Engineering upload" / "02 Supplementary material" / "Supplementary_Material.docx",
    ROOT / "00 Files for Optimization and Engineering upload" / "02 Supplementary material" / "supplementary material.zip",
    ROOT / "00 Files for Optimization and Engineering upload",
]

CSV_REQUIREMENTS = {
    "cgc_benchmark_reporting_summary.csv": [
        "benchmark",
        "case",
        "response_support_status",
        "full_code_validation_status",
        "supported_claim_level",
        "false_certified_count",
    ],
    "cgc_portal_frame_response_support_summary.csv": [
        "response_support_status",
        "supported_claim_level",
        "false_certified_count",
    ],
    "cgc_truss_response_support_summary.csv": [
        "response_support_status",
        "supported_claim_level",
        "false_certified_count",
    ],
    "cgc_aisc_claim_gate_summary.csv": [
        "full_code_validation_status",
        "claim_gate_passed",
        "allowed_claim",
        "blocked_claim",
    ],
    "cgc_extended_claim_risk_benchmark.csv": [
        "benchmark",
        "case",
        "response_support_status",
        "full_code_validation_status",
        "supported_claim_level",
    ],
}

REQUIRED_DATA_ARTIFACTS = [
    "README.md",
    "run_all_log.txt",
    "cgc_portal_frame_experimental_response.csv",
    "cgc_portal_frame_raw_data_manifest.csv",
    "cgc_portal_frame_raw_data_acquisition_note.md",
    "cgc_truss_experimental_response.csv",
    "cgc_truss_raw_data_manifest.csv",
    "cgc_truss_raw_data_acquisition_note.md",
    "third_party_raw_data_redistribution_note.md",
    "external_raw_datasets/Zenodo_15658671_SteelTruss/LatentMechanisms_SteelTruss_ExperimentalData.xlsx",
    "vendor_pulp_license_note.txt",
    "cgc_portal_frame_response_support_plot.png",
    "cgc_truss_response_support_plot.png",
    "cgc_response_support_threshold_sensitivity.csv",
    "cgc_aisc_source_traceability.csv",
]

FORBIDDEN_ZIP_SUFFIXES = {".pyc"}
FORBIDDEN_ZIP_NAMES = {
    "__pycache__",
    "aisc-shapes-database-v160-2.xlsx",
}

SOFTWARE_FIELDS = [
    "software_package_integrity_status",
    "syntax_error_count",
    "data_schema_error_count",
    "missing_artifact_count",
    "upload_package_hash_match",
    "software_layer_validation_claim",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add(rows: list[dict[str, str]], layer: str, check: str, status: str, detail: str) -> None:
    rows.append({"layer": layer, "check": check, "status": status, "detail": detail})


def check_syntax(rows: list[dict[str, str]]) -> int:
    errors = 0
    for path in sorted(BASE.glob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
            add(rows, "application", f"syntax:{path.name}", "pass", "py_compile succeeded")
        except py_compile.PyCompileError as exc:
            errors += 1
            add(rows, "application", f"syntax:{path.name}", "fail", str(exc))
    return errors


def check_application(rows: list[dict[str, str]]) -> int:
    missing = 0
    for name in REQUIRED_APPLICATION_SCRIPTS:
        path = BASE / name
        if path.exists():
            add(rows, "application", f"script_exists:{name}", "pass", "script present")
        else:
            missing += 1
            add(rows, "application", f"script_exists:{name}", "fail", "script missing")
    return missing


def read_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        return next(reader, [])


def check_data(rows: list[dict[str, str]]) -> tuple[int, int]:
    schema_errors = 0
    missing = 0
    for name, columns in CSV_REQUIREMENTS.items():
        path = BASE / name
        if not path.exists():
            missing += 1
            add(rows, "data", f"csv_exists:{name}", "fail", "CSV missing")
            continue
        header = read_header(path)
        absent = [column for column in columns if column not in header]
        if absent:
            schema_errors += len(absent)
            add(rows, "data", f"schema:{name}", "fail", "missing columns: " + "; ".join(absent))
        else:
            add(rows, "data", f"schema:{name}", "pass", "required columns present")
    for name in REQUIRED_DATA_ARTIFACTS:
        path = BASE / name
        if path.exists():
            add(rows, "data", f"artifact_exists:{name}", "pass", "artifact present")
        else:
            missing += 1
            add(rows, "data", f"artifact_exists:{name}", "fail", "artifact missing")
    return schema_errors, missing


def package_context_available() -> bool:
    return any(path.exists() for path in REQUIRED_PRESENTATION_ARTIFACTS)


def check_zip(rows: list[dict[str, str]]) -> tuple[int, str]:
    missing = 0
    zip_path = ROOT / "00 Files for Optimization and Engineering upload" / "02 Supplementary material" / "supplementary material.zip"
    if not zip_path.exists():
        add(rows, "presentation", "zip_exists", "skip", "upload ZIP not present in supplement-only extraction")
        return missing, "not_applicable"
    add(rows, "presentation", "zip_path_checked", "pass", str(zip_path))
    try:
        with ZipFile(zip_path) as z:
            names = z.namelist()
    except BadZipFile as exc:
        add(rows, "presentation", "zip_readable", "fail", str(exc))
        return missing + 1, "not_applicable"
    forbidden = [
        name
        for name in names
        if Path(name).suffix.lower() in FORBIDDEN_ZIP_SUFFIXES
        or any(part in FORBIDDEN_ZIP_NAMES for part in Path(name).parts)
    ]
    if forbidden:
        add(rows, "presentation", "zip_forbidden_files", "fail", "; ".join(forbidden[:12]))
        missing += len(forbidden)
    else:
        add(rows, "presentation", "zip_forbidden_files", "pass", "no restricted raw/cache files in ZIP")

    add(rows, "presentation", "upload_zip_hash_match", "skip", "final ZIP SHA256 is recorded in the delivery manifest to avoid self-hash recursion")
    return missing, "not_applicable"


def check_presentation(rows: list[dict[str, str]]) -> tuple[int, str]:
    missing = 0
    if package_context_available():
        for path in REQUIRED_PRESENTATION_ARTIFACTS:
            if path.exists():
                add(rows, "presentation", f"artifact_exists:{path.name}", "pass", str(path))
            else:
                missing += 1
                add(rows, "presentation", f"artifact_exists:{path.name}", "fail", str(path))
    else:
        add(rows, "presentation", "submission_artifacts", "skip", "supplement-only extraction context")
    zip_missing, hash_match = check_zip(rows)
    return missing + zip_missing, hash_match


def write_details(rows: list[dict[str, str]]) -> None:
    with OUT_DETAILS.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["layer", "check", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)


def update_benchmark_summary(summary: dict[str, str]) -> None:
    if not BENCHMARK_SUMMARY.exists():
        return
    with BENCHMARK_SUMMARY.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    for field in SOFTWARE_FIELDS:
        if field not in fieldnames:
            fieldnames.append(field)
    for row in rows:
        row.update({field: summary[field] for field in SOFTWARE_FIELDS})
    with BENCHMARK_SUMMARY.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows: list[dict[str, str]] = []
    syntax_errors = check_syntax(rows)
    missing_application = check_application(rows)
    data_schema_errors, missing_data = check_data(rows)
    missing_presentation, upload_hash_match = check_presentation(rows)
    missing_artifacts = missing_application + missing_data + missing_presentation
    status = "passed" if syntax_errors == 0 and data_schema_errors == 0 and missing_artifacts == 0 else "failed"
    claim = (
        "software-package integrity check passed for the reproducibility package"
        if status == "passed"
        else "software-package integrity check failed; reproducibility claim must be downgraded"
    )
    summary = {
        "validator": "cgc_software_package_integrity",
        "software_package_integrity_status": status,
        "syntax_error_count": str(syntax_errors),
        "data_schema_error_count": str(data_schema_errors),
        "missing_artifact_count": str(missing_artifacts),
        "upload_package_hash_match": upload_hash_match,
        "software_layer_validation_claim": claim,
    }
    write_details(rows)
    with OUT_SUMMARY.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)
    OUT_NOTE.write_text(
        "\n".join(
            [
                "software-package integrity check for the reproducibility package.",
                "Presentation layer: manuscript/supplement/PDF/ZIP/upload artifacts and ZIP restrictions.",
                "Application layer: Python syntax and required script presence.",
                "Data layer: required CSV schemas, processed datasets, manifests, plots, and status fields.",
                "Integration layer: the validator writes summary fields back to cgc_benchmark_reporting_summary.csv.",
            "This is software-package integrity checking only; it is not structural-code approval, legal approval, professional approval, or complete regulatory approval.",
                f"Status: {status}; syntax_error_count={syntax_errors}; data_schema_error_count={data_schema_errors}; missing_artifact_count={missing_artifacts}; upload_package_hash_match={upload_hash_match}.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    update_benchmark_summary(summary)
    print(OUT_SUMMARY)
    print(OUT_DETAILS)
    if status != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()




