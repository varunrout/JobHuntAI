# JobHuntAI Workflow Controller

## Purpose

Own the complete lifecycle of every serious job from intake through outcome. A pasted job description or public job link is treated as an instruction to begin the workflow automatically unless the user explicitly asks only for analysis.

## Automatic trigger

When the user pastes a job description or job link:

1. Resolve the live job and capture the source.
2. Search Jobs, Applications and the supplied tracker for duplicates without changing any read-only tracker.
3. Create or update the Job record only when the active instruction permits edits.
4. Apply stop-before-tailor gates.
5. Score role fit and visa or work-authorisation feasibility.
6. Create a job output folder inside `JobHuntAI/Outputs`.
7. Save the job description and intake review.
8. Run Role Identity Classification before selecting evidence.
9. Save `role_identity.json` with archetype, confidence, secondary archetypes, positioning strategy and recommended page length.
10. Build the competency matrix and verified evidence candidates.
11. Reweight evidence against the selected archetype and save `evidence_ranking.json`.
12. Initialise `review_loop.json` with the `jobhuntai-tailor-review-v1` contract.
13. Tailor the CV and record the exact `cv.json` hash as a tailor iteration.
14. Render the CV and run construction, factual, positioning, visual and page-strategy gates.
15. Render every exact final PDF page to PNG and create `rendered_visual_review.json` containing the PDF hash, screenshot hashes, geometry, fill and font measurements.
16. Run an independent cold review against the job description, canonical evidence, role identity, diagnostic, exact rendered PDF and every page image.
17. Require the reviewer to inspect all page images and explicitly confirm readable typography, natural pagination, coherent section flow, no large blank areas and no duplicate or continuation headings.
18. Record the review against the exact tailored CV hash and exact rendered PDF hash.
19. When the verdict is `revise`, return every open issue to Tailor, require all issue IDs to be addressed, then repeat Tailor, Render and Review.
20. Continue only when the latest independent review verdict is `approve`, no review issues remain open, the approved hash matches final `cv.json`, and `rendered_visual_gate.py` passes the exact PDF and screenshots.
21. Produce and review a cover letter only when useful or requested.
22. Prepare portal answers and the submission checklist.
23. Build `application_manifest.json` and run `application_quality_gate.py`.
24. Mark `Ready to Apply` only when the final application quality gate passes.
25. After the user confirms submission, create the Applications row.
26. Start Networking automatically for P0 and P1 applications.
27. Log every networking contact, touchpoint and follow-up.
28. Reconcile Gmail stages when requested or when new application mail is found.

## Mandatory Tailor and Review loop

The loop is a release requirement, not an optional quality check.

- Events must alternate `tailor`, then `review`.
- The reviewer actor must be different from the tailor actor.
- Every review must reference the SHA-256 hash of the exact CV revision reviewed.
- The rendered visual review must reference the SHA-256 hash of the exact PDF and every page screenshot.
- A `revise` verdict creates a mandatory new tailor iteration.
- Re-tailoring must explicitly address every open review issue ID.
- An `approve` verdict cannot contain open issues.
- Any CV, PDF, screenshot, page-count or editable-source change after approval invalidates approval and requires another render and review.
- The default maximum is four iterations. Exhaustion blocks automatic release for manual diagnosis rather than weakening the gate.

## Fail-closed rendered-page rules

- The actual page images are the visual source of truth. Extracted text, character share, JSON geometry and prose claims cannot substitute for opening every page image.
- A two-page CV must use at least 82% of the usable first page and 70% of the usable final page.
- Large internal blank gaps block release.
- Rendered body text below 9.5 pt blocks release.
- Every semantic section heading appears exactly once. `Experience Continued`, `Projects Continued`, `Education Continued`, `Additional Project Evidence` and equivalent headings are forbidden.
- Explicit DOCX `pageBreakBefore`, explicit page-break elements and HTML `break-before: page` or `page-break-before: always` are forbidden. Pagination must flow naturally.
- A native Google Docs conversion cannot be the canonical editable CV because conversion can change pagination. Store the exact verified DOCX or HTML source alongside the fixed-layout PDF.
- `cv_length_audit.json.page_fill` must be copied from the exact PDF measurements in `rendered_visual_review.json`. Hand-entered fill figures or text-share estimates block release.

## Fail-closed gates

Do not mark `Ready to Apply` unless:

- the job description is saved;
- the duplicate and tracker checks are complete;
- viability review is complete;
- Role Identity Classification is complete;
- the evidence map and archetype ranking exist;
- final CV passes factual, positioning, structural, visual and rendered-page review;
- every exact rendered page screenshot has been inspected and hash-locked to the final PDF;
- the mandatory Tailor and Review loop is approved and hash-locked to the final CV;
- material gaps are recorded;
- work-authorisation assumptions are explicit;
- required PDF and canonical editable files exist and are non-empty;
- Drive save is verified rather than assumed;
- `application_quality_gate.py` returns `ready_to_apply`.

Do not mark `Applied` unless the user confirms submission or reliable portal or email evidence exists.

## Workspace boundary

All files, records and folders must remain inside `JobHuntAI/`. Never create a separate root Jobs folder.
