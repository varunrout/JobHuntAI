# Agent 4: Independent Review Panel

Single-reviewer approval is no longer the default for new JobHuntAI application runs. New runs use the `jobhuntai-review-panel-v3` state-machine contract and three cold reviewer lanes against the exact same CV hash.

The lanes are:

1. `04a_review_completeness.md` — Completeness / Hiring Case.
2. `04b_review_defensibility.md` — Defensibility / Factual Integrity.
3. `04c_review_competitiveness.md` — Competitiveness / Recruiter + Visual.

Aggregation, scoring thresholds and the return-to-Tailor path are defined in `05_review_controller.md` and enforced by `review_loop.py` plus `review_scoring.py`.

## Non-negotiable panel rules

- Tailor and all three reviewer actors must be distinct.
- Reviewers are cold: no Tailor drafting rationale and no cross-reviewer findings or scores before all three reports are recorded.
- All three reviewers inspect the same exact `cv.json` SHA-256 hash.
- Reviewer A owns `cv_length_audit.json.review_judgement`.
- Reviewer B owns factual/provenance findings.
- Reviewer C owns `rendered_visual_review.json.manual_review` and must inspect every exact rendered page image.
- Every v3 reviewer must return a 0–100 score, fixed weighted score breakdown and evidence-based score rationale.
- Every v3 lane must score at least **85/100**.
- The v3 arithmetic panel average must score at least **88/100**.
- Any open critical or major issue forces `revise` regardless of score.
- Any reviewer explicit `revise` also forces panel `revise`.
- A below-floor lane or panel score creates a blocking `SCORE-*` issue and returns the CV to Tailor.
- A new Tailor edit invalidates the complete panel and all three lanes/scores rerun on the new hash.
- Default maximum is four Tailor/panel iterations; exhaustion blocks automatic release.
- Final release still requires `application_quality_gate.py` after panel approval.

## Backward compatibility

Historical artefacts using `jobhuntai-review-panel-v2` and `jobhuntai-tailor-review-v1` remain readable by `review_loop.py`. They do not establish the standard for new application runs. New runs must initialise `jobhuntai-review-panel-v3`.
