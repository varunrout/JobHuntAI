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

## Review output

Write a report with `lane: "defensibility"` and issue IDs prefixed `DEF-`.

```json
{
  "lane": "defensibility",
  "verdict": "approve | revise",
  "cv_sha256": "exact current hash",
  "summary": "cold factual and provenance assessment",
  "issues": []
}
```

Any unsupported or materially misleading claim is at least `major`; title/date/metric fabrication or false employment/client/deployment implication is `critical`. Critical or major open issues require `revise`.
