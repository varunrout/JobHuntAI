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

## Current independent-practice rule

Varun has a user-confirmed period of independent technical work from **Jan 2026 - Present**. This period is genuine data science, research and engineering activity across verified technical projects, but it is not salaried employment, freelance client work, consulting or a company role unless separate evidence proves otherwise.

For CVs produced from 13 August 2026 onward, JobHuntAI should include this period at the top of Professional Experience by default using the locked entry defined in `cv_pipeline/independent_practice_policy.json`:

- title: `Independent Data Science Research & Engineering`;
- organisation/context: `Independent Practice`;
- dates: `Jan 2026 - Present`;
- `experience_type`: `independent_practice`.

The entry is a current-work chronology block, not a gap explanation. Do not label it Career Break, Upskilling, Between Roles, Job Search or equivalent. Do not tailor the title to imitate the target vacancy.

Every Independent Practice bullet must be traceable to verified project or repository evidence and the CV payload must include `evidence_refs` identifying the supporting evidence. Do not imply clients, paid work, consulting, employment, production deployment or commercial outcomes unless separately verified.

The Projects section remains the detailed proof layer. The same body of work may support both sections, but the Independent Practice block should describe current scope and practice while Projects provides named technical detail, methods, architecture, evaluation and repository links. Do not duplicate bullets verbatim.

Omit the Independent Practice block only when Varun explicitly requests omission or the review panel records a role-specific strategic reason. Omission must appear in the omission audit.

This rule does not authorise changes to any historical employment title or date.

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
- the candidate-role profile used to permit one or two pages;
- the essential evidence markers that must survive into the final CV;
- the omission audit for every relevant role, project or proof point excluded;
- the first-page evidence markers.

The submitted CV must:

- answer "What professional is this candidate?" within the first 10 seconds;
- keep official work titles and dates unchanged;
- include the locked Independent Practice current-work entry by default under the rule above, without representing it as employer or client work;
- use the selected archetype's summary style, skills taxonomy, evidence priorities, stakeholder language, verbs and bullet style;
- order sections and evidence by the positioning strategy rather than chronology alone;
- include no more evidence than is needed to prove the hiring case;
- retain every role-critical evidence marker recorded as essential;
- avoid defensive title, transition or gap-explaining language;
- include LinkedIn, `https://varunrout.com` and GitHub;
- include a direct GitHub link and three evidence bullets for every project on a two-page CV; a one-page CV may use two only when the project still earns its space;
- never use the heading `Selected Projects`;
- treat `Selected Impact` as forbidden by default for every Varun CV; it may appear only after Varun explicitly requests or approves it for that specific application run, with `selected_impact_approval.approved=true` and `selected_impact_approval.source="explicit_user_instruction"`; approval must not be inferred from archetype, evidence strength, page strategy, whitespace, templates, previous CVs or previous approvals;
- preserve the approved typography and bullet geometry.

### Block depth and editorial justice

An included block must earn the heading and reader attention it consumes.

- Every normal employer / salaried experience block must contain at least **3 JD-relevant evidence bullets** across the block as a whole. Default target is **3 to 5**, with the most JD-relevant block normally carrying 4 or 5 where the evidence supports it.
- For a multi-role employer such as E.ON, the floor is measured across the employer block. A nested sub-role may carry 1 or 2 bullets if the parent employer block still has at least 3 total and the sub-role independently earns its line.
- Independent Practice has a **2-bullet hard floor** because it is current-work chronology rather than an employer block; 3 to 5 remains the preferred depth when relevant evidence exists.
- A two-page project block has a **3-bullet floor**. A one-page project may use 2 when the one-page strategy is valid and both bullets materially support the hiring case.
- The floor binds revisions as well as first drafts. If cutting the locally weakest bullet would take its source block below the applicable floor, that cut is illegal; Tailor must fold the strongest fact into a surviving bullet and cut elsewhere, or reconsider whether the entire block belongs.
- Do not invent filler to satisfy a floor. If the evidence bank cannot feed an included block with truthful JD-relevant evidence, stop with `AUTHORING_REQUIRED` / a content decision rather than shipping a starved block.

## Mandatory Tailor and three-reviewer panel loop

Every new application CV must pass the executable `jobhuntai-review-panel-v2` loop before release. Historical `jobhuntai-tailor-review-v1` artefacts remain readable for backward compatibility but are not the standard for new runs.

1. Initialise `review_loop.json` before the first CV draft.
2. Tailor writes the CV and records the exact SHA-256 hash of `cv.json`.
3. Freeze that revision and launch three separate cold reviewers against the same exact hash:
   - `completeness` — hiring case, evidence coverage, block depth, omission audit and page strategy;
   - `defensibility` — factual integrity, provenance, titles, dates, metrics, tools and claim scope;
   - `competitiveness` — recruiter clarity, competitive strength, rendered-page quality and visual composition.
4. Tailor and all three reviewer actors must be distinct. A reviewer actor cannot be reused across lanes.
5. Cold review means no Tailor drafting rationale and no other reviewer findings are provided before all three reports are recorded.
6. Reviewer A / Completeness owns `cv_length_audit.json.review_judgement` and must tie it to its actor, iteration and exact CV hash.
7. Reviewer B / Defensibility owns factual and provenance findings.
8. Reviewer C / Competitiveness owns `rendered_visual_review.json.manual_review` and must inspect every exact rendered-page image tied to the final PDF hash.
9. Any open `critical` or `major` issue forces panel verdict `revise`.
10. Any reviewer explicit `revise` verdict also forces panel `revise`, even when its issue is marked minor.
11. Open minor observations may remain non-blocking only when the issuing reviewer approves and they do not affect hiring-case completeness, factual integrity, page strategy, readability or recruiter comprehension.
12. A panel `revise` returns every blocking issue ID to Tailor.
13. Re-tailoring must explicitly address every blocking issue ID before another iteration is allowed.
14. Any CV edit creates a new hash, invalidates the complete panel and requires all three cold reviewers to rerun on the new revision.
15. Any page-count change requires a fresh Completeness review of the exact revised payload and a fresh Competitiveness review of the exact rerendered pages.
16. Panel approval requires all three lanes, three distinct reviewer actors, the exact current CV hash, no open blocking issue and no reviewer `revise` verdict.
17. The final package remains `FAILED QA` until the current panel is approved and the final application quality gate independently verifies the panel state.

The default maximum is four Tailor/panel iterations. Reaching the limit blocks automatic release for manual diagnosis. It does not permit the pipeline to waive findings.

## Page-length logic

One page is not the default for archetype CVs. Before tailoring, classify the strategy as:

- `ONE_PAGE_ALLOWED`;
- `TWO_PAGE_PREFERRED`;
- `TWO_PAGE_REQUIRED`.

Determine length from:

- years of relevant evidence;
- number of relevant roles and projects;
- seniority;
- breadth of responsibilities and technical capability;
- strategic depth;
- leadership expectations;
- evidence density;
- whether a domain-transfer case needs additional proof.

One page is permitted by default only for a narrow profile with no senior or leadership positioning, no more than three relevant years, no more than two relevant roles, no more than one relevant project, limited technical breadth, no more than four essential evidence items and no domain-transfer burden.

Two pages are preferred or required when they communicate materially more relevant evidence without filler. On a two-page CV, rendered Page 1 must reach at least **90%** of page height and Page 2 at least **70%**. These are composition repair floors, not permission to pad. An underfilled page blocks release until the cause is diagnosed and repaired.

A large blank area at a page foot must first be classified as either a **pagination / atomicity defect** or a **content-volume defect**. If allowing the next employer, nested sub-role or project block to break safely removes the gap, fix the page-break rule before changing evidence. Do not cut bullets to solve an atomic block problem.

When a page is sparse, Tailor must use the existing remediation sequence and record the steps. Relevant evidence and bullet depth are restored only when the problem is genuinely content volume; page-break defects are repaired in the template. Never shrink typography to force a page target. Never remove essential evidence to achieve visual compactness. Every omission must be classified as `harmless` or `strategic_loss`. A strategic-loss omission blocks release.

A `TWO_PAGE_PREFERRED` CV may use one page only through an explicit exception where every essential evidence marker remains, every omission is harmless, the complete sparse-page remediation sequence was attempted and the exact compressed revision passed fresh Completeness review. A `TWO_PAGE_REQUIRED` CV cannot be released as one page.

## Visual architecture

The approved one-column serif design remains stable. Archetypes may vary:

- section order;
- section labels;
- presence of Selected Impact only when the run contains recorded explicit user approval;
- whether projects or experience lead;
- balance between technical and commercial evidence.

Stable section IDs are summary, impact, skills, experience, projects and education. Strategy CVs may use Executive Profile, Commercial Expertise and Strategy Experience. `Selected Impact` remains unavailable unless the run-specific explicit-approval rule is satisfied. Technical CVs may prioritise Technical Skills, Projects and Modelling evidence.

Employer blocks, nested sub-roles and projects are breakable across pages. The template must instead weld the joints that may not split: section headings to following content, role/project headings to their first evidence, descriptors to evidence, and each individual bullet internally. Pagination must never be fixed by per-application font, margin or spacing changes.

## Backward compatibility

Existing legacy payloads must continue to generate the current Forecasting Data Scientist, Data Engineer, Energy Market Analyst and Football Research Engineer CVs without regression. The new role identity layer sits above the existing evidence engine. Payloads without `role_identity` remain on the locked legacy quality and visual contracts.

The legacy rendering path remains supported. Historical review-loop v1 artefacts remain readable, but new application runs use the three-reviewer panel contract.

## Canonical visual sources

Legacy:

- `cv_pipeline/templates/cv_template.html`
- `cv_pipeline/visual_contract.json`
- `cv_pipeline/visual_gate.py`

Archetype:

- `cv_pipeline/templates/cv_archetype_template.html`
- `cv_pipeline/archetype_visual_contract.json`
- `cv_pipeline/archetype_visual_gate.py`
- `cv_pipeline/composition_gate.py`

All application PDFs must be generated through `cv_pipeline/render.py`.

## Application release contract

Every application run must create `application_manifest.json` using `jobhuntai-application-quality-v1` and pass `cv_pipeline/application_quality_gate.py`.

The release gate requires:

- apply or apply-lightly decision;
- saved job description;
- completed duplicate check;
- completed visa review;
- role identity and evidence ranking;
- non-empty CV payload, diagnostic, CV-length audit and PDF;
- passed CV-length, factual, positioning, visual, composition and render checks;
- an approved three-reviewer panel tied to the exact final CV hash;
- a Completeness-owned CV-length judgement tied to the same iteration and hash;
- a Competitiveness-owned rendered visual review tied to the exact final PDF and page images;
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
- a normal employer block has fewer than 3 total evidence bullets;
- Independent Practice has fewer than 2 evidence bullets;
- a two-page project has fewer than 3 bullets, or a one-page project has fewer than 2;
- the Independent Practice entry changes its locked title, organisation/context or dates, lacks evidence refs, implies unsupported employment/client work, or contains claims that cannot be traced to verified current technical evidence;
- the Independent Practice entry is omitted without explicit Varun instruction or a recorded role-specific panel rationale;
- `Selected Impact` appears without run-specific explicit user approval recorded as `selected_impact_approval.approved=true` and `selected_impact_approval.source="explicit_user_instruction"`;
- page length lacks a recorded rationale;
- one page is used when the candidate-role profile exceeds one-page permission thresholds;
- a two-page-preferred or two-page-required strategy is compressed without an allowed exception;
- essential evidence is absent from the final CV;
- an omission is classified as a strategic loss;
- sparse-page remediation steps were skipped;
- page count changed without a fresh Completeness and Competitiveness review;
- Page 1 of a two-page CV is under 90% rendered fill;
- Page 2 of a two-page CV is under 70% rendered fill;
- page one lacks identity, proof, operating context or consequence;
- a project lacks a direct GitHub repository link;
- any factual, evidence-control, composition or visual-contract gate fails;
- the three-reviewer panel is missing or incomplete;
- Tailor and reviewer actors are not all distinct;
- any reviewer is tied to a stale CV hash;
- any open critical/major review issue remains;
- any reviewer verdict is `revise`;
- the CV-length review judgement does not match the Completeness reviewer, iteration and hash;
- the rendered visual manual review does not match the Competitiveness reviewer and exact PDF/screenshots;
- the final CV hash differs from the panel-approved hash;
- the final application quality gate has not passed.

## Tracking

Every serious role belongs in Jobs. Every confirmed submission belongs in Applications. Every networking person and action belongs in Networking.

## Outreach

For P0/P1 submitted applications, identify one recruiter or hiring contact and one relevant team contact unless outreach is inappropriate and documented.
