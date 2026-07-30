# JobHuntAI Rules

## Mission

Help Varun secure a sponsored role before 13 December 2026 through a focused, evidence-led and tracked search.

## Positioning rule

The pipeline must determine the professional identity that best matches the target role before selecting CV evidence. It must not assume that every role is a variation of Data Scientist or Data Analyst.

The canonical archetypes are:

1. Data Scientist
2. Analytics Engineer
3. Data Engineer
4. Strategy & Innovation Analyst
5. Commercial Analyst
6. Football Performance Analyst
7. Football Strategy Analyst
8. Business Intelligence Analyst
9. Forecasting & Pricing Analyst
10. Product Analytics
11. Marketing Analytics

Every application has one dominant archetype. Secondary archetypes are permitted only when the job genuinely combines identities, and they must remain subordinate.

## Visa rule

Treat work-authorisation feasibility as a first-class filter. Do not spend serious tailoring time where sponsorship or permit support is clearly unrealistic.

## Truth rule

Never invent job titles, responsibilities, tools, metrics or formal risk ownership. `MASTER_PROFILE.md` remains the sole factual source. Existing claim-status, attribution, title, tenure and source-traceability gates remain binding.

## Stop-before-tailor

Stop for fatal sponsorship, salary, seniority or technical-fit issues.

## Role scoring

Score domain fit, skills fit, seniority fit, sponsorship likelihood, salary viability, location fit and evidence strength.

- 28 to 35: apply properly and tailor.
- 22 to 27: apply lightly or use outreach first.
- Under 22: skip unless strategically justified.

## Role Identity Classification

Before evidence selection, classify the role using:

- complete job description;
- seniority;
- industry;
- hiring team;
- responsibilities;
- success metrics.

The required output is:

```json
{
  "archetype": "...",
  "confidence": 0.0,
  "secondary_archetypes": [],
  "positioning_strategy": "...",
  "recommended_page_length": 1
}
```

Evidence selection must happen after this stage.

## Evidence reweighting

The same verified evidence may carry different value and language under different archetypes. Reweight evidence for technical depth, commercial influence, transformation, stakeholder engagement, strategic thinking, operational optimisation, leadership, domain relevance, quantified impact and evidence strength.

The factual source does not change. Only the positioning, priority and language change.

## CV construction contract

Before drafting, record:

- the role identity output;
- the dominant archetype and any secondary archetypes;
- the target professional headline, separate from official employment titles;
- a one-sentence professional thesis;
- three to five signature proof points;
- the ranked evidence and exclusion rationale;
- the section architecture;
- the bullet optimisation dimensions;
- the page strategy;
- the first-page evidence markers.

The submitted CV must:

- answer "What professional is this candidate?" within the first 10 seconds;
- keep official work titles and dates unchanged;
- use the selected archetype's summary style, skills taxonomy, evidence priorities, stakeholder language, verbs and bullet style;
- order sections and evidence by the positioning strategy rather than chronology alone;
- include no more evidence than is needed to prove the hiring case;
- avoid defensive title, transition or gap-explaining language;
- include LinkedIn, `https://varunrout.com` and GitHub;
- include a direct GitHub link and two or three evidence bullets for every project;
- never use the heading `Selected Projects`;
- preserve the approved typography and bullet geometry.

## Mandatory Tailor and Review loop

Every application CV must pass an executable Tailor and Review loop before release.

1. Initialise `review_loop.json` before the first CV draft.
2. Tailor writes the CV and records the exact SHA-256 hash of `cv.json`.
3. An independent reviewer evaluates the job description, role identity, evidence ranking, CV payload, diagnostic and rendered PDF.
4. The reviewer records either `approve` or `revise` against the exact CV hash.
5. A `revise` verdict must contain one or more open issue IDs and returns the application to Tailor.
6. Re-tailoring must explicitly address every open issue ID before another review is allowed.
7. An `approve` verdict cannot contain open issues.
8. The reviewer actor cannot be the same as the tailor actor.
9. Any CV edit after approval invalidates the approval hash and forces another review.
10. The final package remains `FAILED QA` until the latest CV revision is independently approved.

The default maximum is four Tailor and Review iterations. Reaching the limit blocks automatic release for manual diagnosis. It does not permit the pipeline to waive review findings.

## Page-length logic

One page is not the default for archetype CVs. Determine length from:

- years of relevant evidence;
- seniority;
- breadth of responsibilities;
- strategic depth;
- leadership expectations;
- evidence density.

Two pages are encouraged when they communicate materially more relevant evidence without filler. A second page must be materially used. Never shrink typography to force one page.

## Visual architecture

The approved one-column serif design remains stable. Archetypes may vary:

- section order;
- section labels;
- presence of Selected Impact;
- whether projects or experience lead;
- balance between technical and commercial evidence.

Stable section IDs are summary, impact, skills, experience, projects and education. Strategy CVs may use Executive Profile, Selected Impact, Commercial Expertise and Strategy Experience. Technical CVs may prioritise Technical Skills, Projects and Modelling evidence.

## Backward compatibility

Existing legacy payloads must continue to generate the current Forecasting Data Scientist, Data Engineer, Energy Market Analyst and Football Research Engineer CVs without regression. The new role identity layer sits above the existing evidence engine. Payloads without `role_identity` remain on the locked legacy quality and visual contracts.

The legacy rendering path remains supported, but the final application package still requires the Tailor and Review loop and application quality manifest.

## Canonical visual sources

Legacy:

- `cv_pipeline/templates/cv_template.html`
- `cv_pipeline/visual_contract.json`
- `cv_pipeline/visual_gate.py`

Archetype:

- `cv_pipeline/templates/cv_archetype_template.html`
- `cv_pipeline/archetype_visual_contract.json`
- `cv_pipeline/archetype_visual_gate.py`

All application PDFs must be generated through `cv_pipeline/render.py`.

## Application release contract

Every application run must create `application_manifest.json` using `jobhuntai-application-quality-v1` and pass `cv_pipeline/application_quality_gate.py`.

The release gate requires:

- apply or apply-lightly decision;
- saved job description;
- completed duplicate check;
- completed visa review;
- role identity and evidence ranking;
- non-empty CV payload, diagnostic and PDF;
- passed factual, positioning, visual and render checks;
- an approved Tailor and Review loop tied to the final CV hash;
- tracker mode and duplicate history recorded;
- Drive save verified rather than assumed.

A missing, failed, blocked or merely assumed item cannot be converted into `Ready to Apply` by prose or manual optimism.

## Quality gates

A CV fails when:

- the role is not classified before evidence selection;
- more than one professional identity competes for attention;
- headline, summary, section architecture, skills and evidence tell different stories;
- skills lack supporting evidence in the same document;
- evidence ranking is not archetype-aware;
- bullet emphasis does not match the archetype;
- projects do not support the professional thesis;
- page length lacks a recorded rationale;
- page one lacks identity, proof, operating context or consequence;
- a project has fewer than two bullets or lacks a direct GitHub repository link;
- any factual, evidence-control or visual-contract gate fails;
- no Tailor and Review loop exists;
- review was performed by the tailor actor;
- the latest review requests revision;
- review issues remain open;
- the final CV hash differs from the approved review hash;
- the final application quality gate has not passed.

## Tracking

Every serious role belongs in Jobs. Every confirmed submission belongs in Applications. Every networking person and action belongs in Networking.

## Outreach

For P0/P1 submitted applications, identify one recruiter or hiring contact and one relevant team contact unless outreach is inappropriate and documented.
