# Supplementary Reproducibility Package

This folder contains the scripts and outputs used for the residual-evidence claim-assurance benchmarks.

## Public Repository

The submitted supplementary Word document and the clean reproducibility archive are also available in the public GitHub repository:

https://github.com/gabrielmontufar/article-114-engineering-optimization-claim-assurance

The repository is the public access point for the article 114 supplementary material. It includes the supplementary Word document, the submitted ZIP archive, this README, manifests, acquisition notes, and software/package validation outputs. Third-party raw datasets are redistributed only when permission is clear. The raw Zenodo steel-truss workbook is included because the source record declares a Creative Commons Attribution 4.0 International license; raw DesignSafe/NEES portal-frame files and the AISC Shapes Database spreadsheet are not redistributed because open redistribution permission was not confirmed. Processed validation points, manifests, acquisition notes, and instructions for obtaining those sources are included.

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

## Full Rebuild

To rerun the core computational scripts and reporting layers:

```bash
python run_all.py --continue-on-error
```

Core benchmarks do not require the AISC spreadsheet. They include the scalar benchmark, penalty sweep, portal-frame code-like benchmark, negative-control claim test, manual oracle check, claim-status-by-evidence table, clause-register audit, partial code-oracle comparison, physical-validation protocol metrics, published portal-frame/steel-frame response validation, published truss response validation, grouped ten-bar enumeration, validation-strength suite, OpenSeesPy cross-check, Monte Carlo probe, PuLP/CBC cross-check, reporting summary, and claim-risk/sensitivity files. Together, these files implement a machine-readable claim passport for deciding which engineering statements an optimization output is allowed to support.

The files `cgc_full_code_clause_register.csv`, `cgc_full_code_validation_oracle_comparison.py`, and `cgc_portal_frame_full_code_validation.py` implement a validation-escalation layer. The current evidence is a partial oracle comparison for declared simplified checks and a protocol-defined pathway for unimplemented clauses. It is not full ASCE/AISC approval.

The file `cgc_full_code_aisc_validator.py` is a claim gate that combines the clause register, partial code-oracle results, portal-frame code-escalation status, and AISC W-shape catalog audit. It authorizes only AISC W-shape catalog-audit wording with partial code-oracle support and blocks full AISC/ASCE approval or professional-certification wording.

The files `cgc_portal_frame_published_test_register.csv`, `cgc_portal_frame_experimental_response.csv`, `cgc_portal_frame_physical_validation.py`, `cgc_portal_frame_physical_validation_summary.csv`, `cgc_portal_frame_physical_validation_details.csv`, `cgc_portal_frame_raw_data_manifest.csv`, and `cgc_portal_frame_raw_data_acquisition_note.md` implement the published physical-response validation layer. The raw DesignSafe/NEES files are stored outside the submission ZIP because no open redistribution license was confirmed for the legacy NEES record; the processed service-envelope points needed to rerun the reported validation are included. The resulting status is limited to published steel-frame response support within the tested response family; it is not professional certification, safety certification, AISC approval, or complete regulatory approval.

The files `cgc_truss_published_test_register.csv`, `cgc_truss_experimental_response.csv`, `cgc_truss_physical_validation.py`, `cgc_truss_physical_validation_summary.csv`, `cgc_truss_physical_validation_details.csv`, `cgc_truss_raw_data_manifest.csv`, and `cgc_truss_raw_data_acquisition_note.md` implement the published truss physical-response validation layer. The raw Zenodo workbook is included in the ZIP under `external_raw_datasets/Zenodo_15658671_SteelTruss/` because the record is licensed under Creative Commons Attribution 4.0 International; compact processed response scores are also included. The module screens seven truss damage/collapse cases against intact-state sensor baselines, accepts six under the declared detection rule, logs one discrepancy, and reports `false_certified_count = 0`.

## Reproducibility Boundary

| Layer | Reproducible from ZIP only | Requires external public raw dataset |
|---|---|---|
| Core optimization and claim-risk scripts | Yes | No |
| Software full-stack validation | Yes, in supplement-only mode; upload hash is checked in the full package folder | No |
| Portal-frame published response support | Yes for processed service-envelope points and reported metrics | Yes to regenerate processed points from raw DesignSafe/NEES files |
| Truss published response support | Yes, including the CC BY 4.0 raw Zenodo workbook and processed response scores | No |
| AISC W-shape catalog audit | Yes for included audit outputs | Yes to rerun from the official AISC spreadsheet |

## Third-Party Raw-Data Redistribution Note

The submission ZIP intentionally separates datasets by redistribution status. The Zenodo steel-truss workbook is included under `external_raw_datasets/Zenodo_15658671_SteelTruss/` because the source record declares a Creative Commons Attribution 4.0 International license. The legacy DesignSafe/NEES SAC Steel Project raw files are not redistributed because an open redistribution license was not confirmed for that record; processed service-envelope points, manifest rows, and an acquisition note are included instead. The AISC Shapes Database spreadsheet is also not redistributed because it is a third-party catalog resource; the package includes audit outputs and an acquisition note explaining how a reviewer can obtain the official spreadsheet and rerun the optional AISC catalog audit.

The files `cgc_software_full_stack_validation.py`, `cgc_software_full_stack_validation_details.csv`, `cgc_software_full_stack_validation_summary.csv`, and `cgc_software_full_stack_validation_note.txt` implement software full-stack validation of the reproducibility package. This layer checks Python syntax, required application scripts, CSV schemas, processed datasets, presentation artifacts, ZIP restrictions, and upload-package hash consistency. It validates software/package integrity only; it is not structural-code approval, legal approval, professional approval, or complete regulatory approval.

The older files `cgc_physical_validation_protocol.md`, `cgc_physical_validation_raw_data.csv`, and `cgc_physical_validation_metrics.py` remain as the protocol/gating demonstration for future laboratory datasets. The published-response module above is the active physical-evidence layer used by the reporting summary.

The file `cgc_certificate_handoff_schema.json` is not a validation result. It is a reproducible data schema showing how the encoded-claim certificate can be handed off to later nonlinear virtual testing, commercial full-code checking, or physical laboratory planning without implying that those downstream validations have already been performed.

The `vendor_pulp/` directory is included only to keep the PuLP/CBC finite-set cross-check reproducible when PuLP is not installed. Upstream license files are retained in `vendor_pulp/pulp-3.3.1.dist-info/licenses/LICENSE` and the CBC `coin-license.txt` files; see `vendor_pulp_license_note.txt`.

The files `cgc_claim_status_by_evidence_layer.csv`, `cgc_negative_control_claim_test.py`, `cgc_negative_control_claim_test.csv`, `cgc_manual_oracle_check.py`, `cgc_manual_oracle_check.csv`, `cgc_manual_oracle_check_results.csv`, `cgc_reviewer_claim_audit_checklist.md`, and `cgc_code_physics_validation_extension.md` provide the reviewer-facing claim-control layer. The negative-control file deliberately includes unsupported wording examples and verifies that they are blocked or downgraded; the manual oracle file checks 18 hand-calculation cases with zero classification mismatches.

## Optional AISC External-Data Benchmark

The AISC W-shape benchmark is optional because the AISC spreadsheet is not redistributed. To reproduce it, download the AISC Shapes Database v16.0 from the official AISC page, place it in this folder as `aisc-shapes-database-v160-2.xlsx`, and run:

```bash
python cgc_aisc_portal_frame_catalog_benchmark.py
python cgc_benchmark_reporting_summary.py
python cgc_claim_risk_benchmark.py
```

A complete local run on 2026-05-20 completed every core, reporting, OpenSeesPy, PuLP/CBC, Monte Carlo, and AISC optional benchmark script with return code 0; see `run_all_log.txt`.

## Scope

The scripts certify encoded constraints under declared assumptions. They do not certify full physical safety, complete regulatory approval, robust response support under uncertainty, or unrestricted global MINLP optimality.


