# Supplementary Reproducibility Package

This folder contains the scripts and outputs used for the residual-evidence claim-assurance benchmarks.

## Public Repository

Online Resource 1 and Online Resource 2 are also available in the public GitHub repository:

https://github.com/gabrielmontufar/article-114-optimization-and-engineering-claim-admissibility

The repository is the public access point for the article 114 supplementary material. It includes Online Resource 1, Online Resource 2, this README, manifests, acquisition notes, processed response-support points, and software/package integrity outputs. Third-party raw datasets are not bundled in the submission ZIP; instructions for obtaining the public or official source files are included for optional raw-data reruns.

## Environment

Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Alternatively, create a Conda environment:

```bash
conda env create -f environment.yml
conda activate encoded-claim-optimization
```

## Quick Rebuild

To regenerate summary files from the included outputs:

```bash
python run_all.py --quick
```

## Smoke Rebuild

To run a short reviewer smoke test that checks core logic, claim blocking, manual oracle cases, reporting, and software-package integrity without rerunning the longest enumeration modules:

```bash
python run_all.py --smoke
```

## Core Rebuild

To rerun the core computational scripts and reporting layers:

```bash
python run_all.py --continue-on-error
```

Core benchmarks do not require the AISC spreadsheet. They include the scalar benchmark, penalty sweep, portal-frame code-like benchmark, negative-control claim test, manual oracle check, claim-status-by-evidence table, clause-register audit, partial code-oracle comparison, response-support protocol metrics, published portal-frame/steel-frame response support, published truss response support, grouped ten-bar enumeration, benchmark-strength suite, OpenSeesPy cross-check, Monte Carlo probe, PuLP/CBC finite feasible-set selection check, reporting summary, threshold-sensitivity files, and claim-risk/sensitivity files. Together, these files implement a machine-readable claim passport for deciding which engineering statements an optimization output is allowed to support.

This core rebuild is not a single monolithic reconstruction from every possible raw third-party dataset. It reruns the redistributable and processed-data scripts available in the package. Optional modules that require nonredistributed external files are handled separately below.

The files `cgc_full_code_clause_register.csv`, `cgc_partial_code_oracle_comparison.py`, and `cgc_portal_frame_clause_support_gate.py` implement a validation-escalation layer. The current evidence is a partial oracle comparison for declared simplified checks and a protocol-defined pathway for unimplemented clauses. It is not full ASCE/AISC approval.

The file `cgc_aisc_claim_gate.py` is a claim gate that combines the clause register, partial code-oracle results, portal-frame code-escalation status, and AISC W-shape catalog audit. It authorizes only AISC W-shape catalog-audit wording with partial code-oracle support and blocks full AISC/ASCE approval or professional-certification wording.

The files `cgc_portal_frame_published_test_register.csv`, `cgc_portal_frame_experimental_response.csv`, `cgc_portal_frame_response_support.py`, `cgc_portal_frame_response_support_summary.csv`, `cgc_portal_frame_response_support_details.csv`, `cgc_response_support_threshold_sensitivity.csv`, `cgc_portal_frame_raw_data_manifest.csv`, and `cgc_portal_frame_raw_data_acquisition_note.md` implement the published-response support layer. The raw DesignSafe/NEES files are stored outside the submission ZIP because no open redistribution license was confirmed for the legacy NEES record; the processed service-envelope points needed to rerun the reported support check are included. The resulting status is limited to published steel-frame response support within the tested response family; it is not professional certification, safety certification, AISC approval, or complete regulatory approval.

The files `cgc_truss_published_test_register.csv`, `cgc_truss_experimental_response.csv`, `cgc_truss_response_support.py`, `cgc_truss_response_support_summary.csv`, `cgc_truss_response_support_details.csv`, `cgc_response_support_threshold_sensitivity.csv`, `cgc_truss_raw_data_manifest.csv`, and `cgc_truss_raw_data_acquisition_note.md` implement the published truss response-support layer. The ZIP includes compact processed response points and acquisition instructions for the public Zenodo workbook rather than bundling the large raw workbook. The module screens seven truss damage/collapse cases against intact-state sensor baselines, accepts six under the declared detection rule, logs one discrepancy, and reports `false_certified_count = 0`.

## Reproducibility Boundary

| Layer | Reproducible from ZIP only | Requires external public raw dataset |
|---|---|---|
| Core optimization and claim-risk scripts | Yes | No |
| Software-package integrity checks | Yes, in supplement-only mode; upload hash is checked in the full package folder | No |
| Portal-frame published response support | Yes for processed service-envelope points and reported metrics | Yes to regenerate processed points from raw DesignSafe/NEES files |
| Truss published response support | Yes, using processed response scores plus Zenodo acquisition instructions | No |
| AISC W-shape catalog audit | Yes for included audit outputs | Yes to rerun from the official AISC spreadsheet |

## Third-Party Raw-Data Redistribution Note

The submission ZIP intentionally separates processed evidence from large or third-party source files. The Zenodo steel-truss workbook is public and citable, but the submission ZIP provides processed response points and acquisition instructions rather than bundling the large workbook. The legacy DesignSafe/NEES SAC Steel Project raw files are not redistributed because an open redistribution license was not confirmed for that record; processed service-envelope points, manifest rows, and an acquisition note are included instead. The AISC Shapes Database spreadsheet is also not redistributed because it is a third-party catalog resource; the package includes audit outputs and an acquisition note explaining how a reviewer can obtain the official spreadsheet and rerun the optional AISC catalog audit.

The files `cgc_software_package_integrity.py`, `cgc_software_package_integrity_details.csv`, `cgc_software_package_integrity_summary.csv`, and `cgc_software_package_integrity_note.txt` implement software-package integrity checks for the reproducibility package. This layer checks Python syntax, required application scripts, CSV schemas, processed datasets, presentation artifacts, ZIP restrictions, and upload-package hash consistency. It supports software/package integrity only; it is not structural-code approval, legal approval, professional approval, or complete regulatory approval.

The older files `cgc_response_support_protocol.md`, `cgc_response_support_protocol_rows.csv`, and `cgc_response_support_metrics.py` remain as a historical protocol/gating demonstration for future external-response datasets; the CSV contains protocol rows only, not redistributed third-party raw measurements. The published-response module above is the active response-support layer used by the reporting summary.

The file `cgc_certificate_handoff_schema.json` is not a validation result. It is a reproducible data schema showing how the encoded-claim certificate can be handed off to later nonlinear virtual testing, commercial clause-complete checking, or laboratory-response planning without implying that those downstream validations have already been performed.

The package does not vendor solver binaries. Install PuLP/CBC through `requirements.txt` before running the finite-set cross-check scripts.

The files `cgc_claim_status_by_evidence_layer.csv`, `cgc_negative_control_claim_test.py`, `cgc_negative_control_claim_test.csv`, `cgc_manual_oracle_check.py`, `cgc_manual_oracle_check.csv`, `cgc_manual_oracle_check_results.csv`, `cgc_reviewer_claim_audit_checklist.md`, and `cgc_code_physics_validation_extension.md` provide the reviewer-facing claim-control layer. The negative-control file deliberately includes unsupported wording examples and verifies that they are blocked or downgraded; the manual oracle file checks 18 hand-calculation cases with zero classification mismatches.

The file `cgc_operator_property_examples.csv` summarizes benchmark-level examples of the post-optimization admissibility operator properties used in the manuscript: missing-evidence blocking, compatible-evidence monotonicity, contradictory-evidence downgrade, idempotence under an unchanged evidence record, and scope monotonicity. It is an index over existing benchmark outputs, not a new safety or code-approval result.

## Optional External-Data Rebuild

The AISC W-shape benchmark is optional because the AISC spreadsheet is not redistributed. Raw DesignSafe/NEES portal-frame files are also not redistributed because open redistribution permission was not confirmed. The file `cgc_aisc_source_traceability.csv` reports the local spreadsheet SHA256 used during verification, the output checksum, shape count, candidate count, feasible count, and best feasible W-shape pair. To reproduce the AISC catalog audit from the official spreadsheet, download the AISC Shapes Database v16.0 from the official AISC page, place it in this folder as `aisc-shapes-database-v160-2.xlsx`, and run:

```bash
python cgc_aisc_portal_frame_catalog_benchmark.py
python cgc_benchmark_reporting_summary.py
python cgc_claim_risk_benchmark.py
```

The included logs and verification tables document quick/reporting execution, per-script core checks, software-package integrity checks, and optional external-data checks where the required local inputs were present. They should not be read as evidence that every nonredistributed raw external dataset can be reconstructed from the ZIP alone.

## Scope

The scripts certify encoded constraints under declared assumptions. They do not certify full physical safety, complete regulatory approval, robust response support under uncertainty, or unrestricted global MINLP optimality.








