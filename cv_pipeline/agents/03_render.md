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
5. Delete generated outputs when any gate fails.

## Required checks

- Page one establishes professional identity, at least two proof points, operating context and consequence.
- Page count respects the evidence-based page strategy, with a normal maximum of two pages.
- A two-page CV must use its final page materially and may not contain filler.
- Section labels and order match the selected archetype or a documented role-specific override.
- Every project has a visible GitHub link and two or three bullets.
- The Portfolio link is clickable.
- Bullet continuation lines remain aligned.
- Typography is never reduced to meet page pressure.
