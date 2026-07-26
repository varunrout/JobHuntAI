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
- a target professional headline for internal framing, separate from official employment titles;
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
- use the exact section heading `Projects`; `Selected Projects` is forbidden;
- default to the approved dense one-page serif layout, with a second page only when explicitly justified;
- prefer deleting lower-priority content or reducing project count over reducing typography.

## Authoritative visual source

The only visual source of truth is:

- `cv_pipeline/templates/shared_visual.css`;
- `cv_pipeline/templates/cv_template.html`;
- `cv_pipeline/templates/cover_letter_template.html`;
- `cv_pipeline/visual_contract.json`.

PDFs must be rendered directly from HTML. DOCX may exist only as a secondary editable export and must never become the render source or receive manual layout repairs.

## Approved visual system

The default CV and cover-letter design is the approved Simran-reference system:

- single-column A4 layout;
- Times New Roman or metrically compatible serif type;
- centred uppercase name and compact contact line;
- black text, blue underlined links and thin black section rules;
- title-case section headings;
- bold role titles, italic employer lines and right-aligned dates;
- one consistent left edge for section headings, role titles, employer lines and bullet text;
- wrapped bullet lines start under the first word of the bullet, never farther to the right;
- no decorative colour palette, cards, sidebars, icons, tables or oversized whitespace;
- cover-letter role, company/date row, greeting, paragraphs and sign-off share one content width.

## Quality gates

A CV or cover letter fails when:

- the locked HTML or CSS hash changes without an explicit visual-contract version update;
- headline framing, summary, capabilities and evidence tell different stories;
- more than one identity competes for attention;
- skills lack supporting evidence in the same document;
- the projects do not support the professional thesis;
- a project has fewer than two bullets or lacks a direct GitHub repository link;
- `Selected Projects` appears anywhere;
- page one lacks identity, stack, strongest result, operating context or consequence;
- a required contact link is missing, reordered or wraps awkwardly;
- a project or experience list stops using the shared evidence-list class;
- bullet font size, marker position or hanging alignment drifts;
- job titles, employer lines, bullets or dates do not align to the approved grid;
- a cover-letter element sits outside the shared content width;
- a heading or project title is stranded;
- any factual or evidence-control gate fails.

Each CV also produces an internal diagnostic with identity, headline, thesis, signature proof points, inclusion and exclusion rationale, bullet-order rationale, word count, page count and gate results.

## Tracking
Every serious role belongs in Jobs. Every confirmed submission belongs in Applications. Every networking person and action belongs in Networking.

## Outreach
For P0/P1 submitted applications, identify one recruiter or hiring contact and one relevant team contact unless outreach is inappropriate and documented.
