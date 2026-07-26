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

Official employment titles are never changed. The role-specific professional headline is rendered in the document header and remains separate from official employment titles.

## Canonical templates

- `templates/cv_template.html`
- `templates/cover_letter_template.html`
- `visual_contract.json`

The HTML templates are authoritative. PDF is the authoritative application artefact. DOCX and Google Docs versions may be created as convenience derivatives, but they must never be used to redefine spacing, typography, headings or alignment.

## Locked output design

- One-column A4 layout based on the approved standalone CV and cover-letter templates.
- Classical serif hierarchy using Cormorant Garamond and Lora tokens with approved serif fallbacks.
- Left-aligned uppercase name, visible professional headline and compact contact line containing LinkedIn, Portfolio and GitHub.
- Warm off-white surface, charcoal text, restrained gold accents and fine neutral divider rules.
- Exact CV section labels: Professional Summary, Skills, Experience, Projects and Education.
- The heading `Selected Projects` is forbidden.
- Strong role hierarchy, italic employer or context lines, right-aligned dates and one shared left edge.
- Wrapped bullet lines start directly under the first word after the bullet.
- Every project requires a direct GitHub link and two or three evidence bullets.
- Cover-letter header, role subject, company/date row, greeting and body use one shared content column.
- Tables, sidebars, icons, negative alignment offsets and manual Word-only layout fixes are forbidden.

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

The complete static and rendered visual suite runs in GitHub Actions for every pull request that changes the pipeline or templates.

## Local checks

```bash
python visual_gate.py
python visual_contract_gate.py
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
