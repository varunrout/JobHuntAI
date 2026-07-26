# CV Pipeline

This directory is the version-controlled implementation snapshot for JobHuntAI CV generation. The live evidence bank remains in the connected Drive workspace and continues to be the sole factual source.

## Flow

1. Intake selects one dominant CV identity and three to five signature proof points.
2. Tailor builds `cv.json` and `cv_diagnostic.json` from the live evidence bank.
3. `quality_gate.py` checks identity coherence, summary and capability structure, bullet allocation, project proof and diagnostics.
4. `lint.py` applies the existing factual and evidence-integrity gates.
5. The renderer uses the approved dense serif CV or matching cover-letter template and checks page count, first-page sufficiency and layout.
6. An independent reviewer reads the rendered artefact and diagnostic before release.

## Controlled identities

- Forecasting Data Scientist
- Data Engineer
- Energy Market Analyst
- Football Research Engineer

Official employment titles are never changed. The target headline remains an internal framing field and is not rendered as a separate visual line.

## Approved output design

- One-column A4 layout based on the approved Simran reference CVs.
- Times New Roman-compatible serif typography.
- Centred uppercase name and a compact contact line containing LinkedIn, Portfolio and GitHub.
- Black text, blue underlined hyperlinks and thin black rules.
- Bold roles, italic employer lines, right-aligned dates and one shared left edge.
- Selected projects require a direct GitHub link and two or three evidence bullets.
- Cover letters use the same header, typography, rules and spacing.

## Local checks

```bash
python -m unittest discover -s tests -v
python tests_gate10_tenure.py
python tests_gate11_repo_claims.py
python tests_nested_visibility.py
```
