# JobHuntAI Rules

## Mission
Help Varun secure a sponsored role before 13 December 2026 through a focused, evidence-led and tracked search.

## Primary positioning
Energy data, forecasting, pricing, market risk, portfolio analysis and trading analytics are the main lane. Data engineering and football research engineering are controlled secondary identities when the evidence and target role support them.

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

## Controlled CV identities
1. Forecasting Data Scientist
2. Data Engineer
3. Energy Market Analyst
4. Football Research Engineer

Every application CV has one dominant identity. A hybrid is permitted only when the job genuinely requires it, and the dominant identity must remain clear.

## CV construction contract

Before drafting, select:

- the dominant identity;
- a target professional headline for the document header, separate from official employment titles;
- a one-sentence professional thesis;
- three to five signature proof points;
- the evidence and projects to include or exclude;
- the first-page evidence markers.

The submitted CV must:

- answer the professional-identity question within the first third of page one;
- use a 45 to 70 word summary carrying one argument;
- place a role-specific three-to-five-line skills map below the summary;
- order experience and project evidence by the selected identity;
- use no more evidence than is needed to prove the hiring case;
- keep official work titles and dates unchanged;
- avoid defensive title, transition or gap-explaining language;
- include the fixed contact links: LinkedIn, `https://varunrout.com` and GitHub;
- include a direct GitHub link and two or three evidence bullets for every project;
- use the exact section heading `Projects`; `Selected Projects` is never permitted;
- default to the approved dense one-page classical serif layout, with a second page only when explicitly justified;
- prefer deleting lower-priority content or reducing project count over reducing typography.

## Canonical visual source

The only authoritative visual sources are:

- `cv_pipeline/templates/cv_template.html`;
- `cv_pipeline/templates/cover_letter_template.html`;
- `cv_pipeline/visual_contract.json`.

All application PDFs must be generated through `cv_pipeline/render.py`. A DOCX, Google Doc or manually adjusted PDF is a convenience derivative only. It must never redefine headings, font sizes, margins, bullet behaviour or alignment.

## Approved visual system

The default CV and cover-letter design is the approved standalone-template system:

- single-column A4 layout;
- Cormorant Garamond and Lora visual hierarchy, with approved serif fallbacks when those fonts are unavailable;
- left-aligned uppercase name, visible role-specific professional headline and compact contact line;
- warm off-white surface, charcoal text, restrained gold accents and fine neutral rules;
- exact title-case CV section headings: Professional Summary, Skills, Experience, Projects and Education;
- strong role titles, italic employer or context lines and right-aligned dates;
- one consistent left edge for section headings, role titles, employer lines and bullet text;
- wrapped bullet lines begin directly under the first word after the bullet;
- cover-letter header, role subject, company/date row, greeting and body share one left and right content grid;
- no cards, sidebars, icons, tables, negative alignment offsets or oversized whitespace.

## Hard visual gate

No CV or cover letter may be released unless the HTML template gate and rendered PDF gate pass.

The hard gate blocks:

- `Selected Projects` or any project-heading variant other than `Projects`;
- changes to locked page margins, typography, line height, link colour, rules or bullet geometry;
- missing visual-contract hooks;
- non-contract font families or font sizes;
- project and experience bullets using different styles;
- continuation lines that do not align with the first word after the bullet;
- missing clickable Portfolio links;
- section-heading left-edge drift;
- cover-letter company/date rows that do not share the body grid;
- table-based layout;
- unexpected page counts.

A visual failure deletes or quarantines generated outputs. Manual approval cannot override a hard visual gate without a versioned change to the HTML contract and regression tests.

## Quality gates

A CV fails when:

- headline framing, summary, capabilities and evidence tell different stories;
- more than one identity competes for attention;
- skills lack supporting evidence in the same document;
- the projects do not support the professional thesis;
- a project has fewer than two bullets or lacks a direct GitHub repository link;
- page one lacks identity, stack, strongest result, operating context or consequence;
- a required contact link is missing or the contact line wraps awkwardly;
- job titles, employer lines, bullets or dates do not align to the approved grid;
- a heading or project title is stranded;
- any factual, evidence-control or visual-contract gate fails.

Each CV also produces an internal diagnostic with identity, headline, thesis, signature proof points, inclusion and exclusion rationale, bullet-order rationale, word count, page count, visual-contract result and gate results.

## Tracking
Every serious role belongs in Jobs. Every confirmed submission belongs in Applications. Every networking person and action belongs in Networking.

## Outreach
For P0/P1 submitted applications, identify one recruiter or hiring contact and one relevant team contact unless outreach is inappropriate and documented.
