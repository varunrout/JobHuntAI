# CV Identity Pipeline Implementation Report

Date: 26 July 2026
Branch: `agent/cv-identity-pipeline`

## Implemented

- Four controlled CV identities: Forecasting Data Scientist, Data Engineer, Energy Market Analyst and Football Research Engineer.
- Target headlines separated from official employment titles.
- Signature evidence selected before drafting.
- Professional summaries limited to 45 to 70 words and one coherent argument.
- Role-specific capability maps placed directly below the summary.
- Identity-specific bullet selection, ordering, project selection and terminology.
- Professional-thesis, first-page sufficiency, identity-consistency, evidence-integrity and layout gates.
- Review-facing diagnostic sidecar for every CV.
- Default two-page ceiling and final-page fill checks.
- Defensive title and transition language prohibited.

## Evidence controls preserved

The existing factual linter remains authoritative for title, tenure, attribution, measured versus illustrative metrics, unsupported claims, project status and source traceability. No factual hard gate was removed.

Two false-positive defects were repaired:

- Nested E.ON role bullets now count as body evidence for summary-metric checks.
- StatsBomb is treated as a shared data source rather than an exclusive Frame2Threat marker. Frame2Threat-specific architecture markers remain exclusive.

## Regression results

QuantumBlack preserved honest same-sample benchmarking and evaluation rigour while gaining a target-role headline, page-one capability map and shorter project proof. Result: 465 words, 2 pages, 60.0 per cent final-page fill, all gates passed.

The AA preserved its operational forecasting identity and planning consequences while gaining a target-role headline, page-one capability map and removal of unsupported legacy project claims. Result: 474 words, 2 pages, 61.8 per cent final-page fill, all gates passed.

Original approved application PDFs were not overwritten.

## Tests run

- `python -m unittest discover -s tests -v`: 8 passed
- `python tests_gate10_tenure.py`: passed
- `python tests_gate11_repo_claims.py`: passed
- `python tests_nested_visibility.py`: passed
- QuantumBlack factual, construction, render and visual checks: passed
- The AA factual, construction, render and visual checks: passed

## Resolved conflicts

- Replaced blanket three-bullet block density with role-based evidence allocation.
- Replaced fill-the-page behaviour with thesis sufficiency and lower-priority deletion.
- Excluded unsupported HealthBeauty360 legacy claims because evidence controls take precedence.
- Narrowed a shared StatsBomb attribution marker without weakening project-specific attribution checks.

## Unresolved conflicts

None affecting CV generation or regression behaviour.
