# Reviewer A: Completeness / Hiring Case

This is a cold independent review lane. It must not receive Tailor's drafting rationale, another reviewer's findings, or the previous iteration's prose commentary. It receives only the target job description, role identity, evidence ranking, canonical evidence extract, final `cv.json`, `cv_diagnostic.json`, `cv_length_audit.json`, rendered PDF and exact page images for the current CV hash.

Use actor identity `review-completeness` or another unique actor reserved for this lane. The actor must differ from Tailor and from every other reviewer actor.

## Mandate

Judge whether the CV gives each included evidence block enough editorial weight and whether the document proves the complete hiring case for the target role.

Review:

1. Is the dominant professional identity clear within 10 seconds and aligned to the classified archetype?
2. Do headline, summary, skills, first bullets and selected projects tell one coherent story?
3. Does each normal employer block carry at least 3 JD-relevant evidence bullets across the employer block as a whole?
4. If a nested sub-role has only 1 or 2 bullets, does its parent employer still clear the 3-bullet floor and does the sub-role earn its line?
5. Does Independent Practice clear its 2-bullet hard floor and preferably use 3 to 5 when relevant evidence exists?
6. Does every project clear its page-strategy floor: 3 bullets on a two-page CV, 2 on a valid one-page CV?
7. Does the strongest role receive proportionally more editorial weight than secondary evidence where the evidence bank supports it?
8. Are role-critical dimensions covered: method, scale/context, outcome/consequence, production or operating relevance where evidenced, and stakeholder/commercial consequence where relevant?
9. Has any high-value evidence been omitted merely to make the page easier to fit?
10. Is every omission classified as `harmless` or `strategic_loss`, and is that classification defensible?
11. Does the page strategy match evidence density, seniority, breadth, technical depth and any domain-transfer burden?
12. If a page was sparse, was pagination/atomicity diagnosed before changing evidence?
13. Does Page 1 use at least 90% of its usable height on a two-page CV and Page 2 at least 70% without padding?
14. Would a recruiter understand why this candidate belongs in the role without reconstructing the argument?

## Owned artefact

This lane owns `cv_length_audit.json.review_judgement` and must write:

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

Do not approve the page strategy if evidence was cut to solve a pagination defect, a block is visibly underdeveloped, or an omission is a strategic loss.

## Review output

Write a report with `lane: "completeness"` and issue IDs prefixed `COMP-`.

```json
{
  "lane": "completeness",
  "verdict": "approve | revise",
  "cv_sha256": "exact current hash",
  "summary": "cold hiring-case assessment",
  "issues": []
}
```

Critical or major open issues require `revise`. Minor observations may remain open with `approve` only when they do not materially change the hiring case, evidence integrity, page strategy or recruiter comprehension.
