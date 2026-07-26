# CV Pipeline

This directory is the version-controlled implementation snapshot for JobHuntAI CV generation. The live evidence bank remains in the connected Drive workspace and continues to be the sole factual source.

## Flow

1. Intake selects one dominant CV identity and three to five signature proof points.
2. Tailor builds `cv.json` and `cv_diagnostic.json` from the live evidence bank.
3. `quality_gate.py` checks identity coherence, summary and capability structure, bullet allocation, project proof and diagnostics.
4. `lint.py` applies the existing factual and evidence-integrity gates.
5. `render.py` produces the PDF and checks page count, first-page sufficiency, final-page fill and layout.
6. An independent reviewer reads the rendered artefact and diagnostic before release.

## Controlled identities

- Forecasting Data Scientist
- Data Engineer
- Energy Market Analyst
- Football Research Engineer

Official employment titles are never changed. The target headline is a separate positioning line.

## Local checks

```bash
python -m unittest discover -s tests -v
python tests_gate10_tenure.py
python tests_gate11_repo_claims.py
python tests_nested_visibility.py
```
