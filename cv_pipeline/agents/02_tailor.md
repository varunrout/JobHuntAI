# Agent 2: Tailor

Writes `cv.json`, `cv_diagnostic.json` and the cover-letter payload from the accepted role identity, ranked evidence and live evidence bank.

## CV sequence

1. Load the selected archetype from `archetypes.json`.
2. Preserve the accepted role identity. Do not reclassify the role during drafting.
3. Initialise `review_loop.json` before the first draft when it does not already exist.
4. When returning from Review, load every open issue ID and treat each as a required revision input.
5. Generate the professional headline from the archetype and target role. Keep every official employment title unchanged.
6. Write the summary in the archetype's executive-summary style. It must establish identity, problem class, proof, approach and distinctive delivery strength.
7. Use the archetype's section order and approved section labels unless the diagnostic records a role-specific layout override.
8. Build the skills section only from the archetype's skills taxonomy and evidence visible elsewhere in the CV.
9. Select evidence from the archetype-ranked list. Lower-ranked evidence may be used only with a recorded reason.
10. Draft bullets against the selected optimisation dimensions: technical depth, commercial influence, transformation, stakeholder engagement, strategic thinking, operational optimisation and leadership.
11. Apply the archetype's preferred verbs and bullet style. The same evidence must be framed differently when the target archetype changes.
12. Keep one principal action, one method or analytical basis and one outcome, influence or consequence per bullet.
13. Use Selected Impact only when the archetype layout calls for it. It is not a substitute for unsupported executive claims.
14. Select projects according to archetype project importance. Every project still requires a direct GitHub link and two or three evidence bullets.
15. Apply the page strategy from Role Identity Classification. Two pages are encouraged when they carry materially relevant proof. One page is never pursued by default.
16. Never solve page pressure by shrinking the approved typography. Delete globally weaker evidence or reduce project count first.
17. Produce the archetype diagnostic before rendering.
18. Run `pipeline_gate.py`, then the factual linter.
19. Record the exact SHA-256 hash of the completed `cv.json` as a Tailor event in `review_loop.json`.
20. When this is a re-tailor iteration, record every addressed review issue ID. The state machine rejects partial issue closure.
21. Hand the exact recorded revision to Independent Review. Do not make further edits while that revision is under review.

Tailor cannot approve its own work or mark a package ready. The identity layer controls positioning. The evidence bank controls factual truth. Review controls release. None may override another.
