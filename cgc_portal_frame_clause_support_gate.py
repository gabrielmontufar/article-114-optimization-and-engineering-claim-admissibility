from __future__ import annotations

import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent
CLAUSE_REGISTER = BASE / "cgc_full_code_clause_register.csv"
ORACLE_RESULTS = BASE / "cgc_partial_code_oracle_results.csv"
OUT_CSV = BASE / "cgc_portal_frame_clause_support_gate.csv"
OUT_NOTE = BASE / "cgc_portal_frame_clause_support_gate_note.txt"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main() -> None:
    clauses = read_csv(CLAUSE_REGISTER)
    oracle = read_csv(ORACLE_RESULTS) if ORACLE_RESULTS.exists() else []
    encoded = [c for c in clauses if c["status"] in {"encoded_exact", "encoded_simplified"}]
    protocol = [c for c in clauses if c["status"] == "protocol_defined"]
    out_scope = [c for c in clauses if c["status"] == "out_of_scope"]
    mismatches = [r for r in oracle if r["classification_match"] != "yes"]
    coverage = 100.0 * len(encoded) / max(1, len(clauses))
    status = (
        "validated_against_partial_code_oracle"
        if oracle and not mismatches
        else "protocol_defined"
    )
    supported_claim = (
        "conditional partial code-check support for declared simplified checks"
        if status == "validated_against_partial_code_oracle"
        else "protocol-defined code-check pathway only"
    )
    row = {
        "benchmark": "portal_frame_full_code_escalation",
        "code_standard_family": "ASCE 7-22 / AISC 360-22 / AISC 341-22 / AISC 358",
        "clause_register_count": len(clauses),
        "encoded_or_simplified_clause_count": len(encoded),
        "protocol_defined_clause_count": len(protocol),
        "out_of_scope_clause_count": len(out_scope),
        "code_clause_coverage_percent": f"{coverage:.2f}",
        "oracle_comparison_count": len(oracle),
        "classification_mismatch_count": len(mismatches),
        "clause_support_status": status,
        "supported_claim_level": supported_claim,
    }
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)
    OUT_NOTE.write_text(
        "\n".join(
            [
                "Portal-frame clause-support gate audit.",
                "The clause register maps ASCE/AISC code families to encoded, simplified, protocol-defined, or out-of-scope status.",
                "The current implementation provides partial code-oracle agreement for declared simplified checks only.",
                "It does not constitute full ASCE/AISC code approval, professional certification, connection design approval, or seismic detailing approval.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(OUT_CSV)
    print(OUT_NOTE)


if __name__ == "__main__":
    main()



