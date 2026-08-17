# Agent 4: Independent Review

Reads the job description, role identity output, evidence ranking, rendered PDF, stripped payload, live evidence extract, rules, diagnostic sidecar, `cv_length_audit.json`, every rendered-page PNG and `rendered_visual_review.json`. It does not receive the writer's drafting rationale beyond the recorded positioning strategy.

The reviewer must use an actor identity different from Tailor and must review the exact CV hash recorded in `review_loop.json`. The same actor must inspect the rendered page images tied to the exact final PDF hash.

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
15. Are official employment titles, dates, locations, metrics, attribution and project status factually clean?
16. If the Independent Practice entry is present, does it use the exact locked title, organisation/context, dates and `experience_type` from `independent_practice_policy.json`?
17. Does every Independent Practice bullet trace to its declared `evidence_refs`, without implying salaried employment, clients, freelance consulting, paid work, production deployment or commercial outcomes that are not separately evidenced?
18. Does the Independent Practice block read as genuine current technical practice rather than defensive gap language or a target-title imitation?
19. Where Independent Practice and Projects draw from the same body of work, do they serve different functions rather than repeat the same bullets? Experience should describe current scope and practice; Projects should provide named technical proof.
20. If the Independent Practice entry is absent, is there explicit Varun instruction or a recorded role-specific Independent Review rationale in the omission audit?
21. Does every normal employer block carry at least 3 JD-relevant evidence bullets across the employer block as a whole, with no included block visibly starved? If a nested sub-role has only 1 or 2 bullets, does its parent employer still clear the 3-bullet floor and does the sub-role earn its line?
22. Does Independent Practice clear its 2-bullet floor, and does every project clear the applicable floor: 3 bullets on a two-page CV or 2 on a valid one-page CV?
23. Are page count, first-page fill, final-page fill and visual layout acceptable at readable typography?
24. Does the CV contain any unsupported skill, tool, responsibility, leadership claim or outcome?
25. Does the PDF exist, open correctly and match the reviewed payload?
26. Would a recruiter understand why this candidate belongs in this role without reconstructing the argument?
27. Have all page PNGs generated from the exact final PDF hash been inspected at readable zoom?
28. Does page one visibly use the page rather than merely pass a text-character-share calculation?
29. Are there any large lower-page or internal blank areas, hidden pagination breaks or stranded sections?
30. Does each semantic section have exactly one heading across the whole CV, with no `Experience Continued`, `Projects Continued`, `Education Continued`, `Additional Project Evidence` or equivalent label?
31. Is rendered body text at least 9.5 pt and comfortable to read?
32. Does content flow naturally across pages without an explicit DOCX or HTML page break?
33. Is the canonical editable file the exact verified DOCX or HTML source rather than a native Google Docs conversion with pagination drift?
34. If a large page-foot gap appeared, was it diagnosed as pagination/atomicity versus content-volume before evidence was changed?

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

The reviewer must also complete `rendered_visual_review.json.manual_review` after opening every exact page screenshot:

```json
{
  "reviewer_actor": "same independent reviewer actor",
  "outcome": "pass | fail",
  "inspected_all_pages": true,
  "no_large_blank_areas": true,
  "no_duplicate_or_continued_headings": true,
  "readable_typography": true,
  "natural_pagination": true,
  "section_flow_coherent": true,
  "notes": "page-specific observations from the actual rendered images"
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
- A sparse page is a repair trigger, not permission to delete evidence.
- Do not approve from PDF text extraction, page-fill percentages or JSON diagnostics alone. The exact page images are the visual source of truth.
- Do not approve if Page 1 reaches less than 90% of its usable height in a two-page CV, the final page reaches less than 70%, or a large blank gap remains.
- Do not approve a normal employer block below the 3-bullet floor, Independent Practice below 2 bullets, or a project below its page-strategy floor. These floors bind revision cuts as well as first drafts.
- Do not approve body typography below 9.5 pt.
- Do not approve duplicate semantic headings, any continuation heading or any explicit source page break.
- Do not approve a native Google Docs conversion as the canonical editable CV.
- Do not approve an Independent Practice block that changes its locked identity, lacks evidence refs, uses unsupported claims, imitates a target job title, or presents independent work as employer/client work.
- Do not approve omission of the Independent Practice block without explicit Varun instruction or a recorded role-specific rationale in the omission audit.
- If the PDF, screenshot or editable-source hash changes, the rendered visual review is stale and must be repeated.

Fail or require revision when positioning is unclear, a secondary archetype competes for attention, evidence selection precedes classification, the page strategy is unsupported, essential evidence is dropped, an omission is a strategic loss, factual integrity fails, the Independent Practice policy fails, the layout contract fails, composition depth fails, rendered-page review fails or a required artefact is missing.

After recording `revise`, the workflow returns to Tailor. After recording `approve`, the final application quality gate must still verify the approved CV hash, exact PDF hash, page screenshot hashes, linked CV-length review judgement and all package-level checks before release.
