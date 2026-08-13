# Agent 2: Tailor

Writes `cv.json`, `cv_diagnostic.json`, `cv_length_audit.json` and the cover-letter payload from the accepted role identity, ranked evidence and live evidence bank.

## CV sequence

1. Load the selected archetype from `archetypes.json`.
2. Preserve the accepted role identity. Do not reclassify the role during drafting.
3. Initialise `review_loop.json` before the first draft when it does not already exist.
4. When returning from Review, load every open issue ID and treat each as a required revision input.
5. Before drafting, classify the page strategy as `ONE_PAGE_ALLOWED`, `TWO_PAGE_PREFERRED` or `TWO_PAGE_REQUIRED` using seniority, relevant years, relevant roles, relevant projects, technical breadth and whether a domain-transfer case must be proved.
6. Build `cv_length_audit.json.candidate_role_profile` and the essential evidence map before writing CV copy. Every role-critical proof point needs at least one exact `match_any` marker that must survive into the final CV.
7. Generate the professional headline from the archetype and target role. Keep every official employment title unchanged.
8. Load `independent_practice_policy.json`. Unless Varun explicitly requested omission or a prior Independent Review recorded a role-specific omission rationale, add the locked `independent_practice` entry at the top of Professional Experience using the exact title, organisation and dates in that policy. This is non-employment current technical practice, not a target-role title and not a substitute employer.
9. Give the Independent Practice entry at least two `evidence_refs` pointing to verified current project or repository evidence. Every bullet in the block must be defensible from those refs. Do not imply clients, paid consulting, company employment, production deployment or commercial outcomes unless separately verified. Do not use Career Break, Upskilling, Between Roles, Job Search or equivalent defensive language.
10. Use the Independent Practice block to describe current scope and working practice. Use the Projects section as the detailed proof layer. The same body of work may support both sections, but do not repeat bullets verbatim and do not use the Independent Practice block as a disguised project dump.
11. Write the summary in the archetype's executive-summary style. It must establish identity, problem class, proof, approach and distinctive delivery strength.
12. Use the archetype's section order and approved section labels unless the diagnostic records a role-specific layout override.
13. Build the skills section only from the archetype's skills taxonomy and evidence visible elsewhere in the CV.
14. Select evidence from the archetype-ranked list. Lower-ranked evidence may be used only with a recorded reason.
15. Draft bullets against the selected optimisation dimensions: technical depth, commercial influence, transformation, stakeholder engagement, strategic thinking, operational optimisation and leadership.
16. Apply the archetype's preferred verbs and bullet style. The same evidence must be framed differently when the target archetype changes.
17. Keep one principal action, one method or analytical basis and one outcome, influence or consequence per bullet.
18. `Selected Impact` is OFF by default for every Varun CV, regardless of archetype, evidence strength, seniority, page strategy or available space. Do not create, infer or preserve a `selected_impact` block unless Varun explicitly requests or approves that section for the specific application run. When explicit approval exists, record `selected_impact_approval` with `approved: true` and `source: "explicit_user_instruction"`. Approval is run-specific and must never be inherited from another CV, template, archetype or prior application.
19. Select projects according to archetype project importance. Every project still requires a direct GitHub link and two or three evidence bullets.
20. Apply the page strategy from Role Identity Classification and the CV-length audit. Two pages are encouraged when they carry materially relevant proof. One page is never pursued by default.
21. Never solve page pressure by shrinking the approved typography or deleting essential evidence.
22. When a second page is sparse, repair in this exact order: section ordering, restore relevant omitted evidence, improve bullet depth, adjust section placement, tune spacing within approved limits, repair page breaks. Page-count reduction may be considered only after all six steps are recorded in `page_transition.remediation_steps`.
23. Record every excluded relevant role, project or proof point in the omission audit. Classify it as `harmless` or `strategic_loss` and explain why. A strategic-loss omission blocks release. If the Independent Practice entry is omitted, record the explicit user instruction or Independent Review rationale here.
24. If page count changes, set `page_transition.fresh_strategic_review` only after the exact new revision has been independently reviewed. A visual check alone is insufficient.
25. Produce the archetype diagnostic and CV-length audit before rendering.
26. Run `pipeline_gate.py`, the factual linter and `cv_length_gate.py`.
27. Record the exact SHA-256 hash of the completed `cv.json` as a Tailor event in `review_loop.json`.
28. When this is a re-tailor iteration, record every addressed review issue ID. The state machine rejects partial issue closure.
29. Hand the exact recorded revision and CV-length audit to Independent Review. Do not make further edits while that revision is under review.

Tailor cannot approve its own work or mark a package ready. The identity layer controls positioning. The evidence bank controls factual truth. Review controls release. Page-count optimisation cannot override evidence retention. None may override another.
