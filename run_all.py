from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


BASE = Path(__file__).resolve().parent

CORE_SCRIPTS = [
    "cgc_scalar_benchmark.py",
    "cgc_penalty_weight_sweep.py",
    "cgc_portal_frame_code_benchmark.py",
    "cgc_negative_control_claim_test.py",
    "cgc_manual_oracle_check.py",
    "cgc_full_code_validation_oracle_comparison.py",
    "cgc_portal_frame_full_code_validation.py",
    "cgc_response_support_metrics.py",
    "cgc_portal_frame_response_support.py",
    "cgc_truss_response_support.py",
    "cgc_ten_bar_truss_benchmark.py",
    "cgc_ten_bar_truss_exhaustive_grouped.py",
    "cgc_validation_strength_suite.py",
    "cgc_opensees_blind_crosscheck.py",
    "cgc_uncertainty_robustness_probe.py",
    "cgc_milp_crosscheck_pulp.py",
]

REPORTING_SCRIPTS = [
    "cgc_benchmark_reporting_summary.py",
    "cgc_response_support_threshold_sensitivity.py",
    "cgc_aisc_source_traceability.py",
    "cgc_claim_risk_benchmark.py",
    "cgc_extended_claim_risk_benchmark.py",
    "cgc_aisc_claim_gate.py",
    "cgc_software_package_integrity.py",
]

SMOKE_SCRIPTS = [
    "cgc_scalar_benchmark.py",
    "cgc_negative_control_claim_test.py",
    "cgc_manual_oracle_check.py",
    "cgc_benchmark_reporting_summary.py",
    "cgc_response_support_threshold_sensitivity.py",
    "cgc_aisc_source_traceability.py",
    "cgc_claim_risk_benchmark.py",
    "cgc_software_package_integrity.py",
]

OPTIONAL_EXTERNAL_DATA = [
    ("aisc-shapes-database-v160-2.xlsx", "cgc_aisc_portal_frame_catalog_benchmark.py"),
]


def run_script(script: str, continue_on_error: bool) -> tuple[str, int, float]:
    start = time.perf_counter()
    proc = subprocess.run([sys.executable, str(BASE / script)], cwd=BASE)
    elapsed = time.perf_counter() - start
    if proc.returncode != 0 and not continue_on_error:
        raise SystemExit(proc.returncode)
    return script, proc.returncode, elapsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate the CGC supplementary benchmark outputs.")
    parser.add_argument("--quick", action="store_true", help="Run only reporting scripts that summarize existing outputs.")
    parser.add_argument("--smoke", action="store_true", help="Run a short reviewer smoke test covering core logic and reporting.")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue if an optional or long-running script fails.")
    args = parser.parse_args()

    if args.quick and args.smoke:
        raise SystemExit("--quick and --smoke are mutually exclusive")

    if args.quick:
        scripts = list(REPORTING_SCRIPTS)
    elif args.smoke:
        scripts = list(SMOKE_SCRIPTS)
    else:
        scripts = list(CORE_SCRIPTS)

    if not args.quick and not args.smoke:
        for required_file, script in OPTIONAL_EXTERNAL_DATA:
            if (BASE / required_file).exists():
                scripts.append(script)
            else:
                print(f"SKIP optional external-data benchmark {script}: missing {required_file}")
        scripts.extend(REPORTING_SCRIPTS)

    log_rows = []
    for script in scripts:
        print(f"RUN {script}")
        log_rows.append(run_script(script, args.continue_on_error))

    out = BASE / "run_all_log.txt"
    out.write_text(
        "\n".join(f"{script},returncode={code},elapsed_s={elapsed:.3f}" for script, code, elapsed in log_rows)
        + "\n",
        encoding="utf-8",
    )
    print(out)


if __name__ == "__main__":
    main()



