# Agent 5: Review Panel Controller

The Review Panel Controller orchestrates three cold, independent review lanes against the exact same application revision:

1. `completeness` — hiring case, evidence coverage, evidence selection/omission, block depth and page strategy.
2. `defensibility` — factual integrity, metric scope, reader inference, provenance, attribution and CV/CL consistency.
3. `competitiveness` — employer buying intent, realistic competitor model, shortlist strength, evidence hierarchy and rendered-page quality.

The Controller does not rewrite content and does not weaken findings. It enforces independence, revision identity, scoring/gates and the return path to Tailor.

## Cold-review contract

For every Tailor iteration:

- freeze the completed `cv.json` and record its SHA-256;
- when a cover letter is part of the application, freeze it before review and treat CV + CL as one evidence package;
- render exact PDFs/page images before Reviewer C runs;
- launch three separate reviewer contexts;
- provide no Tailor rationale, prior reviewer commentary, prior reviewer score or cross-reviewer result;
- do not reuse Tailor or reviewer actor identities;
- stale reports from a prior application revision are invalid;
- a content edit to either reviewed CV or reviewed CL invalidates the whole panel.

## v4 philosophy

New runs use `jobhuntai-review-panel-v4`.

v4 separates three concepts that must never be collapsed:

1. **quality score** — how strong the reviewed document is on a 0–100 rubric;
2. **blocking integrity/policy gate** — whether a specific defect prevents release regardless of score;
3. **candidate/shortlist ceiling** — whether the remaining weakness can be fixed by document work at all.

A single false clause may block a Defensibility score of 91 without turning the quality score into 0. Conversely, a technically clean document can remain competitively weak.

## Lane thresholds

- Completeness: **>=85**
- Defensibility: **>=90**
- Competitiveness: **>=85**
- Arithmetic panel mean: **>=88**

95+ is exceptional and should be rare. It means effectively no material actionable weakness on that lane after adversarial challenge.

## Mandatory v4 extensions

### Completeness

Requires `selection_audit`:
- `risk`: `none | minor | material`
- strongest unused evidence
- evidence-based rationale

`material` automatically creates `SELECTION-MATERIAL-OMISSION` and returns the application to Tailor.

### Defensibility

Requires five hard semantic integrity booleans:
- metric scope preserved
- inference integrity
- CV/CL consistency
- generalisation boundaries
- attribution integrity

Any false value becomes an `INTEGRITY-*` blocking issue. The numeric Defensibility score remains the underlying quality score and is not zeroed.

### Competitiveness

Requires `buying_intent` with:
- `yes | mostly | partly | no`
- ceiling `none | document | candidate | mixed`
- strong candidate / strong document / strong fit / strong shortlist judgements
- realistic competitor model
- likely rejection reason
- spend recommendation

If buying intent is `partly/no` and the ceiling is `document` or `mixed`, Controller creates `BUYING-INTENT-DOCUMENT` and forces revision.

If buying intent is `partly/no` and the ceiling is purely `candidate`, the Controller records a structural shortlist risk instead of forcing an endless Tailor loop. The application can still be release-approved if all document/factual gates pass, but `shortlist_certified` is false.

This is deliberate: **application quality** and **shortlist certainty** are not the same thing.

## Aggregation rules

After all three lanes submit:

- any open `critical` or `major` issue forces `revise`;
- any reviewer explicit `revise` forces `revise`, even on a minor issue;
- a below-floor lane creates `SCORE-*` and forces revision;
- if all lane floors clear but panel mean <88, create `SCORE-PANEL`;
- v4 policy issues (`SELECTION-*`, `INTEGRITY-*`, document-fixable `BUYING-INTENT-*`) are blocking;
- candidate-only structural risks are recorded but do not create fake document work;
- panel approval requires three current lanes, unique actors, exact current revision, valid v4 schemas, no blocking issues and all numeric floors;
- `shortlist_certified` additionally requires buying intent `yes/mostly` and Reviewer C `strong_shortlist: true`.

## Revision loop

When verdict is `revise`:

1. Return every blocking issue ID to Tailor.
2. Tailor must address all blocking IDs before a new iteration.
3. Any reviewed CV or CL content edit creates a new application revision.
4. Re-render.
5. Run all three cold reviewers again, not only the lane that raised the defect.
6. Recalculate every score and verdict from scratch. Never carry a score forward.
7. Maximum four Tailor/panel iterations by default.

If iteration exhaustion is caused by a candidate-only ceiling, do not keep rewriting the document. Surface the structural risk and the spend recommendation instead.

## Release rule

`Ready to Apply` requires `review_loop.py verify` to confirm:

- current v4 contract, or supported historical v3/v2/v1 state;
- current Tailor revision exists;
- all three current reviewer lanes exist and are independent;
- exact revision hash identity;
- valid lane-specific score breakdowns and v4 extensions;
- Completeness >=85, Defensibility >=90, Competitiveness >=85;
- panel mean >=88;
- no blocking issue or document-fixable buying-intent failure;
- panel verdict `approve` and final CV still matches the approved revision.

For v4, the panel also records:
- `application_release_approved`
- `shortlist_certified`
- `buying_intent`
- `structural_risks`

The final application quality gate still verifies deterministic CV-length and rendered-visual ownership against the same review iteration. Mechanical render/link facts remain deterministic gates; subjective reviewers should not invent mechanical failures that deterministic tools can test directly.
