# Agent 3: Render

Renders the approved payload and runs artefact-level checks. It never rewrites claims or positioning.

## Contract dispatch

- Legacy payloads without `role_identity` use the locked `cv_template.html` and `visual_gate.py` contract unchanged.
- Archetype payloads with `layout_contract: jobhuntai-archetype-v1` use `cv_archetype_template.html`, `archetype_visual_gate.py`, `composition_gate.py` and `archetype_render_gate.py`.
- Cover letters continue through the existing locked cover-letter contract.

## Archetype visual system

The approved one-column serif design remains stable. Archetype layouts may change section order, section labels and the presence of Selected Impact only when explicitly approved. They may not change factual content, typography, bullet alignment, page margins or contact-link requirements.

Stable section IDs are summary, impact, skills, experience, projects and education. `Selected Projects` remains forbidden.

## Hard gate sequence

1. Run `pipeline_gate.py` and `lint.py`.
2. Render through `render.py` with the composition report enabled for archetype CVs.
3. Run the matching visual contract.
4. Run `archetype_render_gate.py` for archetype CVs or `render_gate.py` for legacy CVs.
5. Run `rendered_visual_gate.py capture` against the exact final PDF. Render every page to PNG and create `rendered_visual_review.json` with exact PDF and screenshot hashes.
6. Hand the exact page images and PDF to the cold `competitiveness` reviewer. Reviewer C must inspect every page at readable zoom; extracted text and metrics cannot substitute for image review.
7. Record Reviewer C's page-specific findings in `rendered_visual_review.json.manual_review` with the same reviewer actor used in the `competitiveness` lane, then run `rendered_visual_gate.py validate`.
8. Copy exact `meaningful_fill` values from the validated rendered-page review into `cv_length_audit.json`. Hand-entered or text-share fill values are prohibited.
9. Run `cv_length_gate.py` against the final CV/audit; the Completeness lane owns the page-strategy judgement.
10. Delete generated outputs when any gate fails.

## Required checks

- Page one establishes professional identity, proof, operating context and consequence.
- Page count respects the evidence-based page strategy, with a normal maximum of two pages.
- A two-page CV must reach at least 90% of usable Page 1 and 70% of usable Page 2 with materially relevant evidence.
- A large internal blank gap blocks release even when extracted text counts look acceptable.
- Duplicate or continuation headings are forbidden; each semantic section heading appears exactly once.
- Explicit source page-break directives are prohibited. Pagination must arise naturally from readable typography and content flow.
- Body text must have a rendered median of at least 9.5 pt. Typography may not be shrunk to manufacture page fill.
- A native Google Docs conversion is never the canonical editable CV. Keep the exact verified HTML or DOCX source alongside the fixed-layout PDF.
- An underfilled page returns to Tailor for diagnosed remediation; Render never deletes evidence to manufacture compactness.
- If CV content, page count, PDF hash, screenshot hash or editable source changes, the previous Competitiveness visual review is stale and the complete three-reviewer panel must rerun on the new CV hash.
- Section labels/order match the selected archetype or a documented role-specific override.
- Every project clears its page-strategy bullet floor and has a visible GitHub link.
- GitHub and Portfolio CTA links are clickable and their icons/labels render correctly.
- Bullet continuation lines remain aligned.
