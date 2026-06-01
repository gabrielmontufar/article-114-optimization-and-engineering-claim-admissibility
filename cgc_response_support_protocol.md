# Physical / Experimental Validation Protocol

This protocol defines how a future physical or published-data validation layer
must be added before any published-response claim is allowed.

## Specimen families

1. Reduced truss specimen aligned with the ten-bar benchmark family.
2. Steel portal-frame specimen aligned with the drift, demand/capacity, and
   hierarchy checks used in the portal-frame benchmark.

## Required measurements

- Applied load.
- Nodal displacement or story drift.
- Member strain or inferred axial force where applicable.
- Material properties used by the model.
- Boundary conditions and support compliance.
- Observed limit-state or failure mode if the test is pushed beyond elastic range.

## Acceptance metrics

- Displacement relative error or NRMSE within a declared tolerance.
- Strain or axial-force relative error within a declared tolerance.
- Feasible/infeasible classification matrix.
- False-certified count equal to zero for critical claims.
- Monotonic relation between encoded residual severity and measured response severity.

## Claim rule

If `false_certified_count > 0`, the candidate cannot receive an
experimentally supported claim. If no measured or published response data are
available, `response_support_status` must remain `protocol_defined` or
`not_performed`.



