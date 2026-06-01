# Reproducible illustrative benchmark for the Optimization and Engineering claim-admissibility manuscript.
# The benchmark is intentionally simple: it demonstrates how a penalty model,
# a continuous hard-constraint model, and a discrete catalog formulation support
# different compliance claims.

import csv
from pathlib import Path

CATALOG_A_MM2 = [800, 1000, 1200, 1500, 1800]
STRENGTH_REQUIRED_A_MM2 = 1200
SERVICE_REQUIRED_A_MM2 = 1400
PENALTY_WEIGHT = 100.0


def residuals(area, catalog=True):
    strength = max(0.0, STRENGTH_REQUIRED_A_MM2 / area - 1.0)
    service = max(0.0, SERVICE_REQUIRED_A_MM2 / area - 1.0)
    constructability = 0.0 if catalog else 1.0
    return strength, service, constructability


def penalty_objective(area):
    strength, service, _ = residuals(area, catalog=True)
    return area + PENALTY_WEIGHT * (strength + service)

rows = []
for area in CATALOG_A_MM2:
    strength, service, constructability = residuals(area, catalog=True)
    rows.append({
        'formulation': 'soft_penalty_candidate',
        'area_mm2': area,
        'catalog_admissible': 'yes',
        'objective': round(penalty_objective(area), 6),
        'strength_residual': round(strength, 6),
        'serviceability_residual': round(service, 6),
        'constructability_residual': round(constructability, 6),
    })

soft = min(rows, key=lambda r: r['objective'])
continuous_area = max(STRENGTH_REQUIRED_A_MM2, SERVICE_REQUIRED_A_MM2)
discrete_area = min(a for a in CATALOG_A_MM2 if a >= continuous_area)

summary = [
    ('soft penalty', soft['area_mm2'], soft['strength_residual'], soft['serviceability_residual'], 0.0, 'no strict encoded-compliance certificate'),
    ('continuous hard constraints', continuous_area, 0.0, 0.0, 1.0, 'feasible mathematically but not catalog-buildable'),
    ('discrete catalog hard-constraint enumeration', discrete_area, *residuals(discrete_area, catalog=True), 'conditional encoded-compliance claim'),
]

out = Path(__file__).with_name('cgc_scalar_benchmark_results.csv')
with out.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['formulation', 'selected_area_mm2', 'strength_residual', 'serviceability_residual', 'constructability_residual', 'supported_claim'])
    writer.writerows(summary)

print(out)





