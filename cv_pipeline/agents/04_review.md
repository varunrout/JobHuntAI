# Agent 4: Independent Review

Reads the job description, role identity output, evidence ranking, rendered PDF, stripped payload, live evidence extract, rules and diagnostic sidecar. It does not receive the writer's drafting rationale beyond the recorded positioning strategy.

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
11. Are official titles, dates, locations, metrics, attribution and project status factually clean?
12. Are page count, final-page fill and visual layout acceptable at the preserved typography?
13. Does the CV contain any unsupported skill, tool, responsibility, leadership claim or outcome?
14. Does the PDF exist, open correctly and match the reviewed payload?
15. Would a recruiter understand why this candidate belongs in this role without reconstructing the argument?

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

## Verdict rules

- Use `approve` only when there are no open issues.
- Use `revise` when any factual, positioning, evidence, page-strategy, visual or recruiter-clarity issue remains.
- A revision verdict must contain at least one open issue with a concrete required action.
- Do not rewrite the CV inside the review report. Return issue IDs to Tailor.
- Do not approve a CV hash different from the latest Tailor event.
- Do not approve because the application is urgent.
- Do not weaken a finding to avoid another iteration.

Fail or require revision when positioning is unclear, a secondary archetype competes for attention, evidence selection precedes classification, the page strategy is unsupported, factual integrity fails, the layout contract fails or a required artefact is missing.

After recording `revise`, the workflow returns to Tailor. After recording `approve`, the final application quality gate must still verify the approved hash and all package-level checks before release.
