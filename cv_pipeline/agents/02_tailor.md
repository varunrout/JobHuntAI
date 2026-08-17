# Agent 2: Tailor

Writes `cv.json`, `cv_diagnostic.json`, `cv_length_audit.json` and the cover-letter payload from the accepted role identity, ranked evidence and live evidence bank.

## CV sequence

1. Load the selected archetype from `archetypes.json`.
2. Preserve the accepted role identity. Do not reclassify the role during drafting.
3. Initialise `review_loop.json` with `jobhuntai-review-panel-v2` before the first draft when it does not already exist. Historical v1 state files remain readable but new runs use the panel contract.
4. When returning from panel Review, load every blocking issue ID and treat each as a required revision input.
5. Before drafting, classify page strategy as `ONE_PAGE_ALLOWED`, `TWO_PAGE_PREFERRED` or `TWO_PAGE_REQUIRED` using seniority, relevant years, relevant roles, relevant projects, technical breadth and domain-transfer burden.
6. Build `cv_length_audit.json.candidate_role_profile` and the essential evidence map before writing CV copy. Every role-critical proof point needs at least one exact `match_any` marker.
7. Generate the professional headline from the archetype and target role. Keep every official employment title unchanged.
8. Load `independent_practice_policy.json`. Unless Varun explicitly requested omission or the review panel recorded a role-specific omission rationale, add the locked `independent_practice` entry at the top of Professional Experience using exact title, organisation and dates.
9. Give Independent Practice at least two `evidence_refs` pointing to verified current project/repository evidence. Do not imply clients, paid consulting, company employment, production deployment or commercial outcomes unless separately verified.
10. Use Independent Practice for current scope/practice and Projects as the detailed proof layer. Do not repeat bullets verbatim.
11. Write the summary in the archetype's executive-summary style. It must establish identity, problem class, proof, approach and distinctive delivery strength.
12. Use the archetype's section order and approved labels unless the diagnostic records a role-specific override.
13. Build Skills only from the archetype taxonomy and evidence visible elsewhere in the CV.
14. Select evidence from the archetype-ranked list. Lower-ranked evidence may be used only with a recorded reason.
15. Draft bullets against selected optimisation dimensions: technical depth, commercial influence, transformation, stakeholder engagement, strategic thinking, operational optimisation and leadership.
16. Apply the archetype's preferred verbs and bullet style. The same evidence may be framed differently across target archetypes without changing facts.
17. Keep one principal action, one method/analytical basis and one outcome/influence/consequence per bullet.
18. `Selected Impact` is OFF by default for every Varun CV. It may appear only after explicit run-specific Varun approval recorded as `selected_impact_approval.approved=true` and `source="explicit_user_instruction"`.
19. Every normal employer block must clear the 3-bullet parent-block floor; Independent Practice must clear 2; projects must clear 3 on a two-page CV or 2 on a valid one-page CV. Do not create filler to satisfy a floor.
20. Select projects according to archetype importance and include direct GitHub links.
21. Apply the page strategy from Role Identity and the CV-length audit. Two pages are encouraged when they carry materially relevant proof. One page is never pursued by default.
22. Never solve page pressure by shrinking approved typography or deleting essential evidence.
23. When a page is sparse, first distinguish pagination/atomicity from content-volume. Repair atomicity before changing evidence. For genuine content-volume issues use the recorded remediation order: section ordering, restore relevant omitted evidence, improve bullet depth, adjust section placement, tune spacing, repair page breaks; reduce page count only after all prior steps.
24. Record every excluded relevant role/project/proof point in the omission audit as `harmless` or `strategic_loss`. Strategic loss blocks release.
25. Produce the archetype diagnostic and CV-length audit before rendering.
26. Run `pipeline_gate.py`, factual lint, composition gate and `cv_length_gate.py`.
27. Record the exact SHA-256 hash of the completed `cv.json` as a Tailor event in `review_loop.json`.
28. When this is a re-tailor iteration, record every panel blocking issue ID as addressed. The state machine rejects partial blocking-issue closure.
29. Freeze the revision. Do not edit while it is under review.
30. Hand the same exact revision to all three cold lanes: Completeness, Defensibility and Competitiveness. Do not provide drafting rationale or one reviewer's findings to another reviewer.
31. If the panel returns `revise`, address every blocking issue ID, create a new hash, rerender, and send the entire new revision through all three lanes again.

Tailor cannot approve its own work or mark a package ready. Role Identity controls positioning. The evidence bank controls factual truth. The three-reviewer panel controls release. Page-count optimisation cannot override evidence retention. None may override another.
