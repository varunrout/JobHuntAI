# Agent 4: Independent Adversarial Review Panel

Single-reviewer approval is not valid for new JobHuntAI runs. New runs use `jobhuntai-review-panel-v4` and three cold reviewer lanes against the same application revision.

The lanes are:

1. `04a_review_completeness.md` — Completeness / Hiring Case / Evidence Selection.
2. `04b_review_defensibility.md` — Defensibility / Factual + Semantic Integrity.
3. `04c_review_competitiveness.md` — Competitiveness / Buying Intent / Recruiter + Visual.

Aggregation and release policy are defined in `05_review_controller.md` and enforced by `review_loop.py` plus `review_scoring.py`.

## Non-negotiable rules

- Tailor and all three reviewers are distinct actors.
- Reviewers are cold: no Tailor rationale, prior scores, previous reviewer commentary or cross-reviewer findings before all reports are recorded.
- Scores are recalculated from scratch on every changed revision.
- Every lane uses its exact fixed weighted rubric; scores are not back-filled from a preferred headline number.
- Completeness floor: **85**.
- Defensibility floor: **90**.
- Competitiveness floor: **85**.
- Panel mean floor: **88**.
- 95+ means essentially no actionable weakness after adversarial challenge and should be rare.
- Reviewer B returns separate hard semantic integrity checks; a failed gate blocks without converting the quality score to zero.
- Reviewer C must model employer buying intent and a realistic competing candidate.
- Buying intent `partly/no` caused by document execution is blocking; a purely candidate-structural ceiling is recorded as a shortlist risk instead of creating an endless Tailor loop.
- `strong_candidate`, `strong_document`, `strong_fit` and `strong_shortlist` are separate judgements.
- Materially stronger unused evidence is a review finding even when every included claim is true.
- Metric support means value **plus scope**: denominator/subset, evaluation split, qualifier, comparator and causal status when those change interpretation.
- Literal truth that creates a materially unsupported reader inference still fails Defensibility.
- CV/CL contradictions are factual defects. When a cover letter is part of the reviewed application, all reviewers inspect it as part of the same evidence package.
- Deterministic mechanical gates remain authoritative for page geometry, link annotations and render facts; subjective reviewers must not replace a mechanical check with guesswork.
- Any critical/major issue, explicit `revise`, below-floor score or v4 policy blocker returns the application to Tailor.
- A new reviewed content revision invalidates the whole panel.
- Default maximum: four Tailor/panel iterations.
- Final release still requires `application_quality_gate.py`.

## Backward compatibility

Historical `jobhuntai-review-panel-v3`, `jobhuntai-review-panel-v2` and `jobhuntai-tailor-review-v1` artefacts remain readable. They do not define the standard for new runs. New runs initialise v4.
