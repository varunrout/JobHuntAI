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
8. Write the summary in the archetype's executive-summary style. It must establish identity, problem class, proof, approach and distinctive delivery strength.
9. Use the archetype's section order and approved section labels unless the diagnostic records a role-specific layout override.
10. Build the skills section only from the archetype's skills taxonomy and evidence visible elsewhere in the CV.
11. Select evidence from the archetype-ranked list. Lower-ranked evidence may be used only with a recorded reason.
12. Draft bullets against the selected optimisation dimensions: technical depth, commercial influence, transformation, stakeholder engagement, strategic thinking, operational optimisation and leadership.
13. Apply the archetype's preferred verbs and bullet style. The same evidence must be framed differently when the target archetype changes.
14. Keep one principal action, one method or analytical basis and one outcome, influence or consequence per bullet.
15. `Selected Impact` is OFF by default for every Varun CV, regardless of archetype, evidence strength, seniority, page strategy or available space. Do not create, infer or preserve a `selected_impact` block unless Varun explicitly requests or approves that section for the specific application run. When explicit approval exists, record `selected_impact_approval` with `approved: true` and `source: "explicit_user_instruction"`. Approval is run-specific and must never be inherited from another CV, template, archetype or prior application.
16. Select projects according to archetype project importance. Every project still requires a direct GitHub link and two or three evidence bullets.
17. Apply the page strategy from Role Identity Classification and the CV-length audit. Two pages are encouraged when they carry materially relevant proof. One page is never pursued by default.
18. Never solve page pressure by shrinking the approved typography or deleting essential evidence.
19. When a second page is sparse, repair in this exact order: section ordering, restore relevant omitted evidence, improve bullet depth, adjust section placement, tune spacing within approved limits, repair page breaks. Page-count reduction may be considered only after all six steps are recorded in `page_transition.remediation_steps`.
20. Record every excluded relevant role, project or proof point in the omission audit. Classify it as `harmless` or `strategic_loss` and explain why. A strategic-loss omission blocks release.
21. If page count changes, set `page_transition.fresh_strategic_review` only after the exact new revision has been independently reviewed. A visual check alone is insufficient.
22. Produce the archetype diagnostic and CV-length audit before rendering.
23. Run `pipeline_gate.py`, the factual linter and `cv_length_gate.py`.
24. Record the exact SHA-256 hash of the completed `cv.json` as a Tailor event in `review_loop.json`.
25. When this is a re-tailor iteration, record every addressed review issue ID. The state machine rejects partial issue closure.
26. Hand the exact recorded revision and CV-length audit to Independent Review. Do not make further edits while that revision is under review.

Tailor cannot approve its own work or mark a package ready. The identity layer controls positioning. The evidence bank controls factual truth. Review controls release. Page-count optimisation cannot override evidence retention. None may override another.
