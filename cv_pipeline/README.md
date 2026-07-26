# CV Pipeline

This directory is the version-controlled implementation snapshot for JobHuntAI CV generation. The live evidence bank remains in the connected Drive workspace and continues to be the sole factual source.

## Flow

1. Intake selects one dominant CV identity and three to five signature proof points.
2. Tailor builds `cv.json` and `cv_diagnostic.json` from the live evidence bank.
3. `quality_gate.py` checks identity coherence, summary and capability structure, bullet allocation, project proof and diagnostics.
4. `lint.py` applies the factual and evidence-integrity gates.
5. `render.py` renders the payload directly through the canonical HTML template to HTML and PDF.
6. `visual_gate.py` checks the locked HTML contract and the geometry and typography of the rendered PDF.
7. `render_gate.py` or `cover_letter_render_gate.py` blocks release on any content or visual failure.
8. An independent reviewer reads the rendered artefact and diagnostic before release.

## Controlled identities

- Forecasting Data Scientist
- Data Engineer
- Energy Market Analyst
- Football Research Engineer

Official employment titles are never changed. The target headline remains an internal framing field and is not rendered as a separate visual line.

## Canonical templates

- `templates/cv_template.html`
- `templates/cover_letter_template.html`
- `visual_contract.json`

The HTML templates are authoritative. PDF is the authoritative application artefact. DOCX and Google Docs versions may be created as convenience derivatives, but they must never be used to redefine spacing, typography, headings or alignment.

## Locked output design

- One-column A4 layout based on the approved Simran reference CVs.
- Times New Roman-compatible serif typography.
- Centred uppercase name and a compact contact line containing LinkedIn, Portfolio and GitHub.
- Black text, blue underlined hyperlinks and thin black rules.
- Exact CV section labels: Professional Summary, Skills, Experience, Projects and Education.
- The heading `Selected Projects` is forbidden.
- Bold roles, italic employer lines, right-aligned dates and one shared left edge.
- Wrapped bullet lines start directly under the first word after the bullet.
- Every project requires a direct GitHub link and two or three evidence bullets.
- Cover-letter role, company/date, greeting and body use one shared content column.
- Tables, negative alignment offsets and manual Word-only layout fixes are forbidden.

## Hard visual gate

The gate fails on:

- any change to locked CSS values or page margins;
- missing visual-contract version hooks;
- wrong or renamed section headings;
- non-contract fonts or font sizes;
- missing clickable portfolio links;
- section-edge drift;
- project and experience bullet-size differences;
- wrapped bullet continuation indentation;
- cover-letter company/date rows extending beyond the body grid;
- unexpected page count;
- table-based layout.

## Local checks

```bash
python visual_gate.py
python -m unittest discover -s tests -v
python tests_gate10_tenure.py
python tests_gate11_repo_claims.py
python tests_nested_visibility.py
```

## Canonical rendering

```bash
python render.py cv runs/JOB_ID/cv.json \
  --html-out runs/JOB_ID/cv.html \
  --pdf-out runs/JOB_ID/cv.pdf

python render.py cl runs/JOB_ID/cover_letter.json \
  --html-out runs/JOB_ID/cover_letter.html \
  --pdf-out runs/JOB_ID/cover_letter.pdf
```

A failed visual gate removes the generated HTML and PDF rather than releasing a defective artefact.
