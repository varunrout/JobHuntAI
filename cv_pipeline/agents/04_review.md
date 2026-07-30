# Agent 4: Independent Review

Reads the job description, role identity output, evidence ranking, rendered PDF, stripped payload, live evidence extract, rules, diagnostic sidecar and `cv_length_audit.json`. It does not receive the writer's drafting rationale beyond the recorded positioning strategy.

The reviewer must use an actor identity different from Tailor and must review the exact CV hash recorded in `review_loop.json`.

## Review questions

1. What professional is this candidate after a 10-second scan?
2. Does that identity match the classified archetype and target hiring context?
3. What problem class does the candidate solve?
4. Which three proof points establish the case?
5. Do the headline, summary, section architecture, skills and first three bullets tell the same story?
6. Was evidence selected after identity classification and in line with archetype scores?
7. Are technical depth, commercial influence, transformation, stakeholder engagement, strategy, operations and leadership balanced appropriately for this archetype?
8. Do selected projects reinforce the archetype, or do they consume space that stronger employment evidence needs?
9. Is the recommended page length justified by evidence density, seniority, breadth, strategic depth and leadership expectations?
10. Does page one independently establish identity, proof, context and consequence?
11. Has page-count optimisation removed evidence that materially improves the hiring case?
12. Does the omission audit identify every relevant role, project or proof point removed from the final CV, and classify each omission as harmless or a strategic loss?
13. If a sparse second page triggered a rebuild, did Tailor try section ordering, evidence restoration, bullet depth, section placement, approved spacing and page-break repair before considering page-count reduction?
14. If page count changed, has this exact revision received a fresh strategic review rather than only a visual check?
15. Are official titles, dates, locations, metrics, attribution and project status factually clean?
16. Are page count, final-page fill and visual layout acceptable at the preserved typography?
17. Does the CV contain any unsupported skill, tool, responsibility, leadership claim or outcome?
18. Does the PDF exist, open correctly and match the reviewed payload?
19. Would a recruiter understand why this candidate belongs in this role without reconstructing the argument?

## Review output

Write a structured review report containing:

```json
{
  "verdict": "approve | revise",
  "cv_sha256": "hash of the exact reviewed cv.json",
  "summary": "independent assessment",
  "issues": [
    {
      "id": "FACT-1",
      "severity": "critical | major | minor",
      "status": "open | closed",
      "message": "specific failure",
      "required_action": "specific correction"
    }
  ]
}
```

The same independent review must complete `cv_length_audit.json.review_judgement` with:

```json
{
  "material_evidence_removed": false,
  "omission_audit_complete": true,
  "page_strategy_approved": true,
  "rationale": "why the final page strategy preserves the hiring case",
  "review_actor": "same actor recorded in review_loop.json",
  "review_iteration": 1,
  "cv_sha256": "same exact reviewed hash"
}
```

## Verdict rules

- Use `approve` only when there are no open issues.
- Use `revise` when any factual, positioning, evidence-retention, omission, page-strategy, visual or recruiter-clarity issue remains.
- A revision verdict must contain at least one open issue with a concrete required action.
- Do not rewrite the CV inside the review report. Return issue IDs to Tailor.
- Do not approve a CV hash different from the latest Tailor event.
- Do not approve because the application is urgent.
- Do not weaken a finding to avoid another iteration.
- Do not approve when `material_evidence_removed` is true or unclear.
- Do not approve a one-page exception unless every essential evidence marker remains, every omission is harmless and the exact compressed revision has received a fresh strategic review.
- A sparse second page is a repair trigger, not permission to delete evidence.

Fail or require revision when positioning is unclear, a secondary archetype competes for attention, evidence selection precedes classification, the page strategy is unsupported, essential evidence is dropped, an omission is a strategic loss, factual integrity fails, the layout contract fails or a required artefact is missing.

After recording `revise`, the workflow returns to Tailor. After recording `approve`, the final application quality gate must still verify the approved hash, the linked CV-length review judgement and all package-level checks before release.
