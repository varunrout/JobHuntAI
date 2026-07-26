# Simran CV visual specification

## Basis

This specification captures the recurring layout grammar observed across the supplied Simran CV references. It deliberately separates source-derived patterns from measurements that still require rendered side-by-side validation.

## Source-derived recurring patterns

- A4 portrait, single-column layout.
- Serif body typography.
- Name centred at the top in bold uppercase.
- Contact information compressed into one centred line.
- Black body text with minimal decorative treatment.
- Section names are visually strong but compact.
- Thin rules separate or extend section headings.
- Dates align to the right edge while role, degree or project titles remain left aligned.
- Employer or institution text is subordinate to the role or degree line, commonly through italics.
- Bullet lists are dense, with restrained vertical gaps and consistent hanging indentation.
- Experience carries the largest share of the page.
- Skills are grouped by capability rather than shown as a tag cloud.
- Supporting sections such as education, projects, certifications, publications and volunteering compress cleanly and may continue onto page two.
- The system remains visually plain: no sidebar, cards, icons, profile photo or decorative colour palette.

## Initial implementation tokens

These are starting values, not claimed exact measurements from the PDFs.

| Token | Initial value |
|---|---:|
| Page top margin | 11.5 mm |
| Page side margins | 13 mm |
| Page bottom margin | 10.5 mm |
| Body font | Times New Roman compatible serif |
| Body size | 9.15 pt |
| Body line height | 1.14 |
| Name size | 16.8 pt |
| Contact size | 8.15 pt |
| Section size | 9.7 pt |
| Section top gap | 1.75 mm |
| Entry bottom gap | 1.05 mm |
| Bullet text indent | 3.5 mm |
| Rule width | 0.55 pt |

All tunable dimensions are CSS custom properties in `simran_cv_template.html`.

## Semantic structure

1. Header
   - name
   - compact contact line
2. Professional Summary
3. Skills
4. Experience
5. Education
6. Projects
7. Optional supporting sections
   - Certifications
   - Publications
   - Volunteering
   - Awards

The order is fixture-controlled except for the fixed primary section order in the first implementation. A later version may accept an explicit section-order array once visual behaviour is stable.

## Pagination rules

- No absolute positioning.
- No content tables.
- No default manual page break.
- Section headings should remain with the next content block.
- Individual entries and projects should avoid splitting where practical.
- A two-page CV should arise from content volume, not a preselected page target.
- The template must not reduce typography to solve overflow automatically.

## Comparison checklist

For each reference comparison, record:

- page count
- top, side and bottom whitespace
- name and contact baseline positions
- section heading baseline and rule position
- body line count per page
- date-column right edge
- bullet marker and continuation-line alignment
- average gap between role blocks
- location of the first page break
- last-page fill
- orphaned headings or stranded titles

## Open questions for the next pass

- Exact serif face used in the references.
- Whether section headings are consistently uppercase across every version or vary by tailored CV.
- Exact margin differences between one-page and two-page references.
- Whether dates use the same font size as body text or a slightly smaller size.
- Whether project and education blocks use identical spacing to experience blocks.
- How much of the perceived density comes from font metrics versus line height and margins.

## Acceptance criteria before pipeline integration

- Neutral one-page fixture renders without clipping or wrapping the contact line.
- Neutral two-page fixture paginates naturally with no sparse page caused by a forced break.
- All wrapped bullet lines align under the first word after the bullet.
- Dates remain aligned to a common right edge.
- Optional supporting sections can be omitted without leaving spacing artefacts.
- The rendered output survives Chromium and WeasyPrint comparison without material layout drift.
- A side-by-side review against all five references records the remaining differences explicitly.
