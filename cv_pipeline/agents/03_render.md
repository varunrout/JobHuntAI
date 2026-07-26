# Agent 3: Render

Renders the approved payload and runs artefact-level checks. It never rewrites claims.

## Canonical source

`cv_pipeline/templates/cv_template.html` and `cv_pipeline/templates/cover_letter_template.html` are the only authoritative visual templates. `cv_pipeline/render.py` renders HTML and PDF directly from the approved payload. A manually reformatted DOCX, Google Doc or PDF is never authoritative and must not replace the HTML output.

## Approved visual system

- A4, dense single-column serif layout based on the approved Simran reference CVs.
- Centred uppercase name and one compact contact line: phone, email, LinkedIn, Portfolio, GitHub and location.
- Black body typography, blue underlined hyperlinks and thin black section rules.
- Title-case CV section headings: Professional Summary, Skills, Experience, Projects and Education.
- The project heading is always exactly `Projects`. `Selected Projects` is forbidden.
- Bold role titles, italic employer and location lines, right-aligned dates and one shared left edge for headings, role lines, employer lines and bullet content.
- Wrapped bullet lines begin directly under the first word after the bullet.
- The cover letter uses the same typeface, header, rules and spacing. Its role line, company/date row, greeting and body share one left and right content grid.

## Hard gate sequence

1. Run the construction gate and factual linter.
2. Render with `render.py` from the canonical HTML template.
3. Run `visual_gate.py` on the HTML and rendered PDF.
4. For CVs, run `render_gate.py`; for cover letters, run `cover_letter_render_gate.py`.
5. Block release and delete generated outputs when any visual check fails.

The hard visual gate checks template version, exact section labels, page margins, font family and size, section edges, bullet font and continuation alignment, contact links, page count, cover-letter column alignment and forbidden table-based layout.

## Required checks

- Do not render a separate target-headline line; the identity must be clear from the summary and evidence.
- Default to one readable page. Two pages are permitted only when the intake brief records that the hiring case cannot be proved cleanly on one page.
- Verify the contact line includes a working Portfolio link and does not wrap.
- Place Skills below the summary and before evidence sections.
- Verify every project has a visible GitHub link and two or three bullets.
- Verify page one contains the target identity, at least two stack markers, the strongest achievement, operating context and a business, operational or user consequence.
- Prefer project-count or evidence reduction over typography reduction.
- Write page count, word count, first-page sufficiency, visual-contract status and layout result back to `cv_diagnostic.json`.

The original approved application PDFs are never overwritten by regression runs.
