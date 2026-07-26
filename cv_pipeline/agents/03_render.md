# Agent 3: Render

Renders the approved payload and runs artefact-level checks. It never rewrites claims.

## Required checks

- Run the construction gate and factual linter before rendering.
- Use the preserved JobHuntAI design tokens and readable font sizes.
- Place Core Capabilities below the summary and before evidence sections.
- Enforce a two-page maximum unless the brief records an explicit exception.
- Fail when the final page is below 45 per cent filled. Treat 45 to 60 per cent as advisory.
- Verify page one contains the target identity, at least two stack markers, the strongest achievement, operating context and a business, operational or user consequence.
- Fail on stranded headings, project titles split from their first bullet, awkward contact wrapping or excessive bullet wrapping.
- Prefer content deletion over typography reduction.
- Write page count, word count, first-page sufficiency and layout result back to `cv_diagnostic.json`.

The original approved application PDFs are never overwritten by regression runs.
