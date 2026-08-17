# Agent 5: Review Panel Controller

The Review Panel Controller orchestrates three cold, independent review lanes against the exact same CV revision:

1. `completeness` — hiring case, evidence coverage, block depth, omission audit and page strategy.
2. `defensibility` — factual integrity, provenance, titles, dates, metrics, tools and claim scope.
3. `competitiveness` — recruiter clarity, competitive strength, rendered-page quality, CTA/link rendering and visual composition.

The Controller does not rewrite CV content and does not weaken findings. It only enforces reviewer independence, hash identity, panel completeness, scored quality thresholds and the return path to Tailor.

## Cold-review contract

For every Tailor iteration:

- freeze the completed `cv.json` and record its SHA-256 hash;
- render the exact PDF and page images before reviewer C runs;
- launch three separate reviewer contexts;
- do not provide Tailor's drafting rationale to any reviewer;
- do not provide one reviewer's findings or score to another reviewer before all three reports are recorded;
- do not reuse the Tailor actor as a reviewer;
- do not reuse one reviewer actor for another lane;
- all three reports must reference the exact same current `cv.json` hash;
- stale reports from a previous revision are invalid.

## Lane ownership

- Reviewer A / `completeness` owns `cv_length_audit.json.review_judgement`.
- Reviewer B / `defensibility` owns factual and provenance findings.
- Reviewer C / `competitiveness` owns `rendered_visual_review.json.manual_review` and must inspect every exact page image.

## Scoring contract

New review runs use `jobhuntai-review-panel-v3`.

Each lane must return:

- `score` from 0 to 100;
- the lane-specific fixed `score_breakdown` whose weighted points sum exactly to `score`;
- an evidence-based `score_rationale` explaining both earned and withheld points;
- the existing `approve | revise` verdict and issue list.

The fixed release thresholds are:

- **each lane >= 85/100**;
- **panel arithmetic mean >= 88/100**;
- existing factual, visual, hash, independence and issue gates remain mandatory.

The score is not a substitute for blocking issues. A 95 cannot cancel a major issue. Conversely, a CV with no major issue can still require revision if a reviewer scores it below 85 or the three-lane mean is below 88.

Score bands are common across lanes:

- `95–100` exceptional
- `90–94.9` excellent
- `85–89.9` strong / release-capable
- `75–84.9` revision required
- `<75` weak

## Aggregation rules

After all three lanes submit:

- any open `critical` or `major` issue forces panel verdict `revise`;
- any reviewer explicit `revise` verdict forces panel verdict `revise` even if its issue is marked minor;
- any lane score below 85 creates a blocking score issue and forces `revise`;
- when all lane scores clear 85 but the panel average is below 88, the Controller creates `SCORE-PANEL` and forces `revise`;
- open minor observations may remain as non-blocking notes only when the reviewer itself approves and they do not affect hiring-case completeness, factual integrity, page strategy, readability or recruiter comprehension;
- panel approval requires all three lanes to be present, three distinct reviewer actors, the exact current CV hash, no blocking issues, no reviewer `revise` verdict, all three lane floors and the panel-average floor;
- the Controller records a `panel` event in `review_loop.json` with reviewer actors, `lane_scores`, `panel_score`, blocking issues, minor notes and the exact approved/rejected CV hash.

## Revision loop

When the panel verdict is `revise`:

1. Return every blocking issue ID — including `SCORE-*` issues — to Tailor.
2. Tailor must explicitly address every blocking issue ID before a new iteration can be recorded.
3. Any content edit creates a new CV hash and invalidates every prior review and score.
4. Re-render the PDF and page images.
5. Run all three cold reviewers again on the new hash, not only the lane that raised the original issue.
6. Recalculate every score from scratch; never carry a score forward.
7. Repeat until approved or the default four-iteration limit is exhausted.

Iteration exhaustion blocks automatic release for manual diagnosis. It never downgrades review severity or scoring thresholds.

## Release rule

`Ready to Apply` is impossible unless `review_loop.py verify` confirms:

- current scored panel contract `jobhuntai-review-panel-v3`, or a supported legacy v2/v1 contract for historical artefacts;
- latest Tailor revision exists;
- all three current review lanes exist;
- all reviewer actors are distinct from each other and Tailor;
- every reviewer references the current CV hash;
- every v3 reviewer has a valid fixed-weight score breakdown and rationale;
- every v3 lane score is at least 85/100;
- v3 panel average is at least 88/100;
- a current panel aggregation event exists and its scores match the three current reviewer events;
- panel verdict is `approve`;
- no critical/major or score-blocking issue remains open;
- final `cv.json` still matches the panel-approved hash.

The final application quality gate must separately verify the Completeness-owned CV-length judgement and the Competitiveness-owned rendered visual review against the same iteration and hash.
