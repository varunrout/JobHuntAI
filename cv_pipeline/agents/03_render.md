# Agent 3: Render

Renders the approved payload and runs artefact-level checks. It never rewrites claims or positioning.

## Contract dispatch

- Legacy payloads without `role_identity` use the locked `cv_template.html` and `visual_gate.py` contract unchanged.
- Archetype payloads with `layout_contract: jobhuntai-archetype-v1` use `cv_archetype_template.html`, `archetype_visual_gate.py` and `archetype_render_gate.py`.
- Cover letters continue through the existing locked cover-letter contract.

## Archetype visual system

The approved one-column serif design remains stable. Archetype layouts may change section order, section labels and the presence of Selected Impact. They may not change factual content, typography, bullet alignment, page margins or contact-link requirements.

Stable section IDs are:

- summary
- impact
- skills
- experience
- projects
- education

The rendered label is supplied by the archetype registry. `Selected Projects` remains forbidden.

## Hard gate sequence

1. Run `pipeline_gate.py` and `lint.py`.
2. Render through `render.py`.
3. Run the matching visual contract.
4. Run `archetype_render_gate.py` for archetype CVs or `render_gate.py` for legacy CVs.
5. Run `rendered_visual_gate.py capture` against the exact final PDF. Render every page to PNG and create `rendered_visual_review.json` with exact PDF and screenshot hashes.
6. Inspect every generated page image at readable zoom. Do not infer visual quality from extracted text, character share, JSON geometry or a prior render.
7. Record the independent review actor's page-specific findings in `rendered_visual_review.json` and run `rendered_visual_gate.py validate`.
8. Copy `meaningful_fill` values from the validated rendered-page review into `cv_length_audit.json`. Hand-entered or text-share page-fill values are prohibited.
9. Run `cv_length_gate.py cv.json cv_length_audit.json`.
10. Delete generated outputs when any gate fails.

## Required checks

- Page one establishes professional identity, at least two proof points, operating context and consequence.
- Page count respects the evidence-based page strategy, with a normal maximum of two pages.
- A two-page CV must reach at least 82% of the usable first page and 70% of the usable final page with materially relevant evidence.
- A large internal blank gap blocks release even when extracted text counts look acceptable.
- A two-page CV may not use `Experience Continued`, `Projects Continued`, `Education Continued`, `Additional Project Evidence` or any equivalent duplicate continuation heading. Each semantic section heading appears exactly once in the whole document.
- Explicit DOCX or HTML page-break directives are prohibited. Pagination must arise naturally from readable typography and content flow.
- Body text must have a rendered median of at least 9.5 pt. Typography may not be shrunk to manufacture page fill.
- A native Google Docs conversion is never the canonical editable CV because conversion can change pagination. Keep the exact verified DOCX or HTML source alongside the fixed-layout PDF.
- A two-page CV must use at least 70% of its second page with materially relevant evidence and may not contain filler.
- An underfilled page returns to Tailor for ordered remediation. Render must not convert that visual finding into permission to delete evidence or force one page.
- If page count changes after rendering, the previous approval is invalid. The exact revised payload and exact rendered PDF must return through Tailor and Independent Review.
- Section labels and order match the selected archetype or a documented role-specific override.
- Every project has a visible GitHub link and two or three bullets.
- The Portfolio link is clickable.
- Bullet continuation lines remain aligned.
- Typography is never reduced to meet page pressure.
