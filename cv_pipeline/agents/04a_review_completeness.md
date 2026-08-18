# Reviewer A: Completeness / Hiring Case

This is a cold independent review lane. It must not receive Tailor drafting rationale, prior scores, prior reviewer commentary, or another reviewer report. It receives the target JD, role identity, evidence ranking, canonical evidence extract, final `cv.json`, optional final cover-letter payload, `cv_diagnostic.json`, `cv_length_audit.json`, rendered PDF and exact page images for the current application revision.

Use actor identity `review-completeness` or another unique actor reserved for this lane. The actor must differ from Tailor and every other reviewer actor.

## Mandate

Judge whether the application uses the **right true evidence**, not merely whether every included block looks complete. A clean document can still be incomplete if stronger evidence was omitted, buried, underweighted, or replaced by lower-value proof.

Review from scratch:

1. In 10 seconds, is the target professional identity clear and coherent?
2. Do summary, skills, first bullets and selected projects tell one hiring story?
3. Does every normal employer block clear the composition floor across the employer block as a whole?
4. Does Independent Practice clear its floor and explain current relevant technical activity without pretending employment?
5. Do projects clear their page-strategy floor and earn the space they consume?
6. Are the JD's highest-value requirements evidenced with method, scale/context, outcome/consequence and operating/stakeholder relevance where evidence exists?
7. What is the **strongest unused piece of evidence** in the evidence bank for this exact vacancy? If it is stronger than something on the page, why was it omitted?
8. Has any evidence been omitted mainly because it is harder to fit, harder to explain, or less visually convenient?
9. Are old/generic/off-domain bullets consuming space that higher-value evidence should own?
10. Does the date column create an unexplained timeline hole or seniority signal that the prose does not resolve?
11. If a role-critical capability is missing from the candidate record, is that correctly treated as a candidate gap rather than disguised as a document omission?
12. Does the cover letter, when present, close a genuine context gap rather than duplicate the CV or introduce a new unexplained claim?
13. Does page strategy match evidence density and domain-transfer burden rather than forcing evidence to serve a page count?
14. On a two-page CV, does Page 1 use at least 90% and Page 2 at least 70% of usable height without padding?
15. Would a recruiter understand why this candidate belongs in the role without reconstructing the argument from scattered evidence?

## Adversarial selection audit

You MUST identify the strongest role-relevant evidence that did not make the CV, even if the correct answer is `none materially stronger`. Compare it against the weakest included evidence. Do not mark an omission harmless merely because the document still reads well.

Return:

```json
"selection_audit": {
  "risk": "none | minor | material",
  "strongest_unused_evidence": "specific evidence or none",
  "rationale": "why the selection is or is not strategically lossy"
}
```

`material` is a release blocker. It means the document is spending scarce space on materially weaker proof while stronger relevant evidence exists.

## Scoring rubric — 100 points

Score bottom-up. Do not choose a headline number first.

- `identity_coherence` — **10**
- `evidence_coverage` — **30**
- `block_depth_weighting` — **15**
- `evidence_selection_omission` — **25**
- `recruiter_comprehension` — **20**

The five values must sum exactly to `score`.

Score bands:
- **95–100** exceptional: essentially no actionable hiring-case or selection weakness
- **90–94.9** excellent: only small residual weaknesses
- **85–89.9** strong / release-capable
- **75–84.9** good candidate evidence but revision required
- **60–74.9** material hiring-case weakness
- **below 60** substantially incomplete or misallocated

Lane floor: **85/100**. Panel mean floor: **88/100**.

Do not award 90+ because the CV is tidy or because every block has enough bullets. A 90+ Completeness score means the **best available evidence has been selected and proportioned well for this vacancy**.

## Owned artefact

This lane owns `cv_length_audit.json.review_judgement`:

```json
{
  "material_evidence_removed": false,
  "omission_audit_complete": true,
  "page_strategy_approved": true,
  "rationale": "specific evidence-based rationale",
  "review_actor": "review-completeness",
  "review_iteration": 1,
  "cv_sha256": "exact current cv.json hash"
}
```

Do not approve page strategy if evidence was cut to solve pagination, a block is visibly underfed, or the selection audit is material.

## Review output

Issue IDs use prefix `COMP-`.

```json
{
  "lane": "completeness",
  "verdict": "approve | revise",
  "score": 88,
  "score_breakdown": {
    "identity_coherence": 9,
    "evidence_coverage": 27,
    "block_depth_weighting": 13,
    "evidence_selection_omission": 21,
    "recruiter_comprehension": 18
  },
  "score_rationale": "Specific explanation of earned and withheld points.",
  "selection_audit": {
    "risk": "minor",
    "strongest_unused_evidence": "specific evidence",
    "rationale": "why the omission is acceptable or why it costs points"
  },
  "cv_sha256": "exact current hash",
  "summary": "cold hiring-case assessment",
  "issues": []
}
```

Critical/major issues require `revise`. Minor notes may remain only when they do not materially alter selection, page strategy or hiring-case comprehension. Score uncertainty downward rather than assuming Tailor made the right trade.
