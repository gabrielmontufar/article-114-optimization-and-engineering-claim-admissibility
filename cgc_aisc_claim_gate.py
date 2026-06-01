from __future__ import annotations

import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent
CLAUSE_REGISTER = BASE / "cgc_full_code_clause_register.csv"
ORACLE_RESULTS = BASE / "cgc_full_code_validation_oracle_results.csv"
PORTAL_FULL_CODE = BASE / "cgc_portal_frame_full_code_validation.csv"
AISC_CATALOG = BASE / "cgc_aisc_portal_frame_catalog_benchmark.csv"
OUT_CSV = BASE / "cgc_aisc_claim_gate_summary.csv"
OUT_NOTE = BASE / "cgc_aisc_claim_gate_note.txt"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main() -> None:
    clauses = read_csv(CLAUSE_REGISTER)
    oracle = read_csv(ORACLE_RESULTS)
    portal = read_csv(PORTAL_FULL_CODE)[0]
    aisc = read_csv(AISC_CATALOG)[0]

    encoded = [row for row in clauses if row["status"] in {"encoded_exact", "encoded_simplified"}]
    out_scope = [row for row in clauses if row["status"] == "out_of_scope"]
    oracle_mismatches = [row for row in oracle if row["classification_match"] != "yes"]

    aisc_feasible = int(float(aisc["feasible_count"]))
    aisc_candidates = int(float(aisc["candidate_count"]))
    full_code_status = portal["full_code_validation_status"]

    row = {
        "gate": "aisc_catalog_claim_gate",
        "clause_register_count": str(len(clauses)),
        "encoded_or_simplified_clause_count": str(len(encoded)),
        "out_of_scope_clause_count": str(len(out_scope)),
        "oracle_comparison_count": str(len(oracle)),
        "oracle_classification_mismatch_count": str(len(oracle_mismatches)),
        "aisc_catalog_candidate_count": str(aisc_candidates),
        "aisc_catalog_feasible_count": str(aisc_feasible),
        "full_code_validation_status": full_code_status,
        "aisc_catalog_status": "external_catalog_audit_available",
        "allowed_claim": "AISC W-shape catalog audit plus partial code-oracle support",
        "blocked_claim": "full AISC/ASCE approval or professional certification",
        "claim_gate_passed": "yes" if not oracle_mismatches and aisc_feasible > 0 else "no",
    }

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)

    OUT_NOTE.write_text(
        "\n".join(
            [
                "AISC catalog claim gate completed.",
                "The gate combines the clause register, partial oracle comparison, portal-frame code-escalation status, and AISC W-shape catalog audit.",
                "It authorizes only an AISC W-shape catalog-audit statement with partial code-oracle support.",
                "It blocks full AISC/ASCE approval, professional certification, seismic detailing approval, connection prequalification, and safety wording.",
                f"Oracle mismatches: {len(oracle_mismatches)}.",
                f"AISC catalog candidates: {aisc_candidates}; feasible candidates: {aisc_feasible}.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(OUT_CSV)
    print(OUT_NOTE)


if __name__ == "__main__":
    main()



