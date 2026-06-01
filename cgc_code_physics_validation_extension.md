# Code-and-Physics Validation Extension

This note defines how the residual-evidence certificate can be escalated beyond
encoded feasibility without overstating the evidence available in the present
benchmark package.

## Evidence Ladder

| Level | Required evidence | Admissible claim |
|---|---|---|
| L0 | Objective value only | Optimization-result only |
| L1 | Encoded residuals, catalog membership, and solver or enumeration route | Encoded-compliance support |
| L2 | L1 plus declared load-code combinations | Load-code-supported claim |
| L3 | L2 plus clause coverage and independent code-oracle agreement | Clause-complete code-check-supported claim within declared scope |
| L4 | L3 plus verified nonlinear simulation, published response benchmark, or laboratory response data | Published published-response support claim within declared assumptions |
| L5 | L4 plus responsible professional review | Engineering approval |

L5 is outside the manuscript. L3 and L4 are not automatic consequences of
encoded feasibility; they are evidence-gated upgrades.

## Current Package Status

- L1 is demonstrated for the declared encoded benchmark spaces when residual,
  catalog, and solver/enumeration evidence are present.
- The AISC W-shape benchmark supports an external catalog audit under declared
  simplified checks. It is not AISC approval.
- The current code-oracle layer provides partial code-oracle support for declared
  simplified checks through the AISC catalog claim gate and manual oracle files.
  It does not provide clause-complete ASCE/AISC approval.
- The published-response layer now provides limited published-response support
  for declared steel-frame and truss response families through DesignSafe/NEES
  and Zenodo datasets. This is not comprehensive experimental validation,
  safety certification, nonlinear collapse validation, or professional approval.

## Required Evidence For Upgrade

To issue a clause-complete code-check-supported claim, the package must include:

- declared code editions and structural family;
- load-combination register;
- clause coverage matrix;
- implemented check for each in-scope clause;
- independent oracle value or pass/fail classification;
- discrepancy log with unit and tolerance checks.

To issue a published published-response support claim, the package must additionally include:

- a validated nonlinear virtual-test model or experimental/published response
  dataset;
- declared similarity domain for member family, loading, boundary conditions,
  material, and failure mode;
- response metrics such as displacement, strain, drift, force, or DCR;
- classification mismatch count and false-certified count.

## Overclaim Blocking Rule

If the corresponding evidence layer is absent, the claim is downgraded:

- complete code approval wording without clause-complete oracle evidence is blocked;
- safety wording without verified published-response support evidence is blocked;
- professional approval wording without responsible review is outside scope.

This extension preserves the central rule of the manuscript: optimization
performance and encoded feasibility are not allowed to imply broader claims
unless the missing evidence layer is supplied.




