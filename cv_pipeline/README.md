# CV Pipeline

This directory is the version-controlled implementation snapshot for JobHuntAI CV generation. The live evidence bank remains in the connected Drive workspace and continues to be the sole factual source.

## Flow

1. Intake selects one dominant CV identity and three to five signature proof points.
2. Tailor builds `cv.json` and `cv_diagnostic.json` from the live evidence bank.
3. `quality_gate.py` checks identity coherence, summary and capability structure, bullet allocation, project proof and diagnostics.
4. `lint.py` applies the existing factual and evidence-integrity gates.
5. `visual_gate.py` verifies the exact HTML templates, shared CSS, headings, alignment grid, contact order and bullet geometry.
6. The renderer creates the CV or cover-letter PDF directly from the locked HTML template.
7. `render_gate.py` checks page count, first-page sufficiency and the locked visual contract before release.
8. An independent reviewer reads the rendered artefact and diagnostic before release.

## Controlled identities

- Forecasting Data Scientist
- Data Engineer
- Energy Market Analyst
- Football Research Engineer

Official employment titles are never changed. The target headline remains an internal framing field and is not rendered as a separate visual line.

## Authoritative visual files

- `templates/shared_visual.css`
- `templates/cv_template.html`
- `templates/cover_letter_template.html`
- `visual_contract.json`

These HTML files are the only visual source of truth. DOCX may be produced as a secondary editable export, but it is never the render source and must not be manually restyled.

## Approved output design

- One-column A4 layout based on the approved Simran reference CVs.
- Times New Roman-compatible serif typography.
- Centred uppercase name and a compact contact line containing LinkedIn, Portfolio and GitHub.
- Black text, blue underlined hyperlinks and thin black rules.
- Bold roles, italic employer lines, right-aligned dates and one shared left edge.
- The section heading is always `Projects`; `Selected Projects` is blocked.
- Every project requires a direct GitHub link and two or three evidence bullets.
- Wrapped bullet lines align under the first word, not under an extra indent.
- Cover-letter role, company/date row, greeting, body and sign-off share one content width.

## Hard visual gate

`visual_contract.json` stores SHA-256 hashes of the approved HTML and CSS. CI fails when:

- any locked file changes without an explicit contract-version update;
- `Selected Projects` appears;
- a project or experience list stops using the shared bullet class;
- bullet indentation, font size or marker position drifts;
- a table or inline style is introduced for layout;
- the cover-letter alignment grid changes;
- contact links are removed or reordered.

## Local checks

```bash
python visual_gate.py
python -m unittest discover -s tests -v
python tests_gate10_tenure.py
python tests_gate11_repo_claims.py
python tests_nested_visibility.py
```
