# Agent 2: Tailor

Writes `cv.json`, `cv_diagnostic.json` and the cover-letter payload from the accepted role identity, ranked evidence and live evidence bank.

## CV sequence

1. Load the selected archetype from `archetypes.json`.
2. Preserve the accepted role identity. Do not reclassify the role during drafting.
3. Generate the professional headline from the archetype and target role. Keep every official employment title unchanged.
4. Write the summary in the archetype's executive-summary style. It must establish identity, problem class, proof, approach and distinctive delivery strength.
5. Use the archetype's section order and approved section labels unless the diagnostic records a role-specific layout override.
6. Build the skills section only from the archetype's skills taxonomy and evidence visible elsewhere in the CV.
7. Select evidence from the archetype-ranked list. Lower-ranked evidence may be used only with a recorded reason.
8. Draft bullets against the selected optimisation dimensions: technical depth, commercial influence, transformation, stakeholder engagement, strategic thinking, operational optimisation and leadership.
9. Apply the archetype's preferred verbs and bullet style. The same evidence must be framed differently when the target archetype changes.
10. Keep one principal action, one method or analytical basis and one outcome, influence or consequence per bullet.
11. Use Selected Impact only when the archetype layout calls for it. It is not a substitute for unsupported executive claims.
12. Select projects according to archetype project importance. Every project still requires a direct GitHub link and two or three evidence bullets.
13. Apply the page strategy from Role Identity Classification. Two pages are encouraged when they carry materially relevant proof. One page is never pursued by default.
14. Never solve page pressure by shrinking the approved typography. Delete globally weaker evidence or reduce project count first.
15. Produce the archetype diagnostic before rendering.
16. Run `pipeline_gate.py`, then the factual linter.

The identity layer controls positioning. The evidence bank controls factual truth. Neither may override the other.
