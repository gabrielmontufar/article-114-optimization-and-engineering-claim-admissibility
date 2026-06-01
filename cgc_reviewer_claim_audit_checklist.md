# Reviewer Claim-Audit Checklist

| Reviewer question | File or artifact that answers it |
| --- | --- |
| Which claims are encoded? | `cgc_full_code_clause_register.csv`; manuscript Table 3 |
| Which residual verifies each claim? | `cgc_benchmark_reporting_summary.csv`; benchmark scripts |
| Are there residual-positive designs? | `cgc_penalty_weight_sweep.csv`; `cgc_negative_control_claim_test.csv` |
| How is minimum selection checked? | `cgc_milp_crosscheck_pulp.py`; `cgc_milp_crosscheck_pulp_log.txt` |
| What is excluded from the certificate? | `cgc_certificate_handoff_schema.json`; Supplement S6-S10 |
| Is there complete code approval? | No. See `full_code_validation_status` fields and `cgc_portal_frame_full_code_validation_note.txt`. |
| Is there external response support? | No published-response claim is issued. See `cgc_response_support_summary.csv`. |
| Is overclaiming detected? | `cgc_claim_risk_benchmark.csv`; `cgc_extended_claim_risk_benchmark.csv`; `cgc_negative_control_claim_test.csv` |
| Is the AISC benchmark a clause audit? | No. It is an AISC W-shape catalog audit; clause coverage is partial and declared separately. |
| Can the package be regenerated? | `run_all.py`; `requirements.txt`; `environment.yml`; `run_all_log.txt` |



