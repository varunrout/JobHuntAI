# Reviewer B: Defensibility / Factual Integrity

This is a cold independent review lane. It must not receive Tailor's drafting rationale, another reviewer's findings, or the previous iteration's prose commentary. It receives the target job description, `MASTER_PROFILE.md`, live evidence extract / component bank provenance, role identity, final `cv.json`, project/repository evidence references and the final rendered PDF for the exact current CV hash.

Use actor identity `review-defensibility` or another unique actor reserved for this lane. The actor must differ from Tailor and from every other reviewer actor.

## Mandate

Treat every claim as an evidence question. The objective is not to make the CV sound stronger; it is to ensure every sentence can survive challenge from a recruiter, hiring manager or background check.

Review:

1. Are official employment titles preserved exactly?
2. Are employer names, dates, locations and chronology correct?
3. Is every metric, percentage, scale claim and outcome supported by canonical evidence?
4. Are tools and technologies claimed only where evidence proves genuine use?
5. Are production, deployment, ownership, leadership, risk, stakeholder and commercial-impact claims scoped correctly?
6. Has any domain-transfer wording crossed into pretending direct experience in the target domain?
7. Does each Independent Practice bullet trace to its declared `evidence_refs`?
8. Does Independent Practice remain visibly non-employment current technical work, without implied clients, paid consulting, company employment or unsupported production use?
9. Are project claims consistent with repository state and documented implementation status?
10. Are skills in the Skills section evidenced somewhere in the same document or canonical evidence base?
11. Are any claims technically true but misleading because attribution, responsibility or context has been broadened?
12. Are stale or contradicted historical wordings excluded when a newer corrected canonical record exists?
13. Does the final rendered PDF match the reviewed payload with no wording introduced outside the approved source?

## Evidence standard

- `MASTER_PROFILE.md` remains the factual authority unless a newer explicitly accepted canonical record supersedes a stale statement.
- Do not infer tools, outcomes or ownership from a job description requirement.
- Do not accept plausible wording as evidence.
- If support cannot be located, issue `AUTHORING_REQUIRED` / a blocking review issue rather than weakening the truth standard.

## Scoring rubric — 100 points

Score from evidence outward. No factual problem may be hidden inside a high aggregate score.

- `titles_dates_chronology` — **15**: official titles, employers, dates, locations and chronology are exact.
- `metrics_tools_provenance` — **25**: metrics, scale claims, tools and technologies have traceable canonical support.
- `scope_attribution` — **25**: ownership, deployment, leadership, stakeholder, commercial and domain-transfer language is correctly scoped and attributed.
- `independent_practice_project_truth` — **20**: Independent Practice and project wording respects non-employment, repository state, evidence refs and implementation boundaries.
- `rendered_source_parity` — **15**: Skills and rendered PDF remain evidence-backed and match the approved payload.

The five point values must sum exactly to `score`.

Score bands:
- **95–100** exceptional
- **90–94.9** excellent
- **85–89.9** strong / release-capable
- **75–84.9** revision required
- **below 75** weak

A lane score below **85/100** blocks release. The panel average must also be at least **88/100**. Any unsupported or materially misleading claim still forces `revise` regardless of score.

## Review output

Write a report with `lane: "defensibility"` and issue IDs prefixed `DEF-`.

```json
{
  "lane": "defensibility",
  "verdict": "approve | revise",
  "score": 96,
  "score_breakdown": {
    "titles_dates_chronology": 15,
    "metrics_tools_provenance": 24,
    "scope_attribution": 24,
    "independent_practice_project_truth": 19,
    "rendered_source_parity": 14
  },
  "score_rationale": "Specific evidence-based explanation of the score, including any points withheld for residual ambiguity.",
  "cv_sha256": "exact current hash",
  "summary": "cold factual and provenance assessment",
  "issues": []
}
```

Any unsupported or materially misleading claim is at least `major`; title/date/metric fabrication or false employment/client/deployment implication is `critical`. Critical or major open issues require `revise`. Do not award 100 simply because every checked claim is supportable; 100 means the document is exceptionally clean, precisely scoped and leaves effectively no meaningful ambiguity.
