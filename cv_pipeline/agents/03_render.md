# Agent 3: Render

Renders the approved payload and runs artefact-level checks. It never rewrites claims.

## Approved visual system

- A4, dense single-column serif layout based on the approved Simran reference CVs.
- Centred uppercase name and one compact contact line: phone, email, LinkedIn, Portfolio, GitHub and location.
- Black body typography, blue underlined hyperlinks and thin black section rules.
- Title-case section headings: Professional Summary, Skills, Experience, Projects and Education.
- The projects heading is always exactly `Projects`. `Selected Projects` is prohibited.
- Bold role titles, italic employer and location lines, right-aligned dates and one shared left edge for headings, role lines, employer lines and bullet content.
- Experience and project bullets use one shared HTML class, font size, marker size, line height and wrapped-line text edge.
- The cover letter uses the same typeface, header, rules, hyperlink treatment and spacing.

## Required checks

- Run `visual_contract_gate.py`, the construction gate and factual linter before rendering.
- Treat the HTML templates as locked production assets. Any change to a layout-critical selector, value, heading, class or structural element must update the visual contract explicitly and pass CI.
- Do not render a separate target-headline line; the identity must be clear from the summary and evidence.
- Default to one readable page. Two pages are permitted only when the intake brief records that the hiring case cannot be proved cleanly on one page.
- Verify the contact line includes a working Portfolio link and does not wrap.
- Place Skills below the summary and before evidence sections.
- Verify every project has a visible GitHub link and two or three bullets.
- Verify page one contains the target identity, at least two stack markers, the strongest achievement, operating context and a business, operational or user consequence.
- Fail on misaligned job-title rows, employer lines, bullets or dates; wrapped bullet lines that do not share the first-line text edge; stranded headings; project titles split from their first bullet; or excessive bullet wrapping.
- Prefer project-count or evidence reduction over typography reduction.
- Write page count, word count, first-page sufficiency and layout result back to `cv_diagnostic.json`.

The original approved application PDFs are never overwritten by regression runs.
