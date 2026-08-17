# Agent 5: Review Panel Controller

The Review Panel Controller orchestrates three cold, independent review lanes against the exact same CV revision:

1. `completeness` — hiring case, evidence coverage, block depth, omission audit and page strategy.
2. `defensibility` — factual integrity, provenance, titles, dates, metrics, tools and claim scope.
3. `competitiveness` — recruiter clarity, competitive strength, rendered-page quality, CTA/link rendering and visual composition.

The Controller does not rewrite CV content and does not weaken findings. It only enforces reviewer independence, hash identity, panel completeness and the return path to Tailor.

## Cold-review contract

For every Tailor iteration:

- freeze the completed `cv.json` and record its SHA-256 hash;
- render the exact PDF and page images before reviewer C runs;
- launch three separate reviewer contexts;
- do not provide Tailor's drafting rationale to any reviewer;
- do not provide one reviewer's findings to another reviewer before all three reports are recorded;
- do not reuse the Tailor actor as a reviewer;
- do not reuse one reviewer actor for another lane;
- all three reports must reference the exact same current `cv.json` hash;
- stale reports from a previous revision are invalid.

## Lane ownership

- Reviewer A / `completeness` owns `cv_length_audit.json.review_judgement`.
- Reviewer B / `defensibility` owns factual and provenance findings.
- Reviewer C / `competitiveness` owns `rendered_visual_review.json.manual_review` and must inspect every exact page image.

## Aggregation rules

After all three lanes submit:

- any open `critical` or `major` issue forces panel verdict `revise`;
- any reviewer explicit `revise` verdict forces panel verdict `revise` even if its issue is marked minor;
- open minor observations may remain as non-blocking notes only when the reviewer itself approves and they do not affect hiring-case completeness, factual integrity, page strategy, readability or recruiter comprehension;
- panel approval requires all three lanes to be present, three distinct reviewer actors, the exact current CV hash, no blocking issues and no reviewer `revise` verdict;
- the Controller records a `panel` event in `review_loop.json` with reviewer actors, blocking issues, minor notes and the exact approved/rejected CV hash.

## Revision loop

When the panel verdict is `revise`:

1. Return every blocking issue ID to Tailor.
2. Tailor must explicitly address every blocking issue ID before a new iteration can be recorded.
3. Any content edit creates a new CV hash and invalidates every prior review.
4. Re-render the PDF and page images.
5. Run all three cold reviewers again on the new hash, not only the lane that raised the original issue.
6. Repeat until approved or the default four-iteration limit is exhausted.

Iteration exhaustion blocks automatic release for manual diagnosis. It never downgrades review severity.

## Release rule

`Ready to Apply` is impossible unless `review_loop.py verify` confirms:

- panel contract `jobhuntai-review-panel-v2` or a supported legacy contract for old artefacts;
- latest Tailor revision exists;
- all three current review lanes exist;
- all reviewer actors are distinct from each other and Tailor;
- every reviewer references the current CV hash;
- a current panel aggregation event exists;
- panel verdict is `approve`;
- no critical/major issue remains open;
- final `cv.json` still matches the panel-approved hash.

The final application quality gate must separately verify the Completeness-owned CV-length judgement and the Competitiveness-owned rendered visual review against the same iteration and hash.
