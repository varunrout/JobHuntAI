# Simran CV visual specification

## Basis

This specification captures the recurring layout grammar across the supplied Blakbear, Clio, Expleo, Paires and Toyota CVs. The reference set contains both dense one-page CVs and longer two-page CVs, so the template must support both without changing its typography.

## Source-derived recurring patterns

- A4 portrait, single-column layout.
- Plain serif typography with a compact LaTeX-like density.
- Name centred at the top in bold uppercase.
- Contact information compressed into one centred line.
- Black body text with blue hyperlinks and almost no decoration.
- Section names are bold, title case and compact. The supplied references do not use decorative rules beside the headings.
- Dates share a right-aligned column while role, degree and project titles remain left aligned.
- Employer and location appear directly below the role line in regular text, not as a large or decorative subheading.
- Bullet lists use small solid markers, tight line spacing and a consistent hanging indent.
- Experience carries most of page one.
- Skills appear as labelled capability lines, not tags, columns or cards.
- Education and condensed achievements can close a one-page CV.
- Projects, publications, certifications and volunteering expand naturally onto page two in the longer references.
- No sidebar, icons, profile image, cards, coloured panels or layout tables.

## Tuned implementation tokens

These values were tuned after rendering neutral fixtures against the recurring proportions of the five references.

| Token | Tuned value |
|---|---:|
| Page top margin | 10 mm |
| Page side margins | 12.5 mm |
| Page bottom margin | 9.5 mm |
| Body font | Times New Roman compatible serif |
| Body size | 9 pt |
| Body line height | 1.12 |
| Name size | 16.5 pt |
| Contact size | 8.05 pt |
| Section size | 9.55 pt |
| Section top gap | 1.25 mm |
| Entry bottom gap | 0.72 mm |
| Bullet text indent | 3.15 mm |

All tunable dimensions remain CSS custom properties in `simran_cv_template.html`.

## Structural corrections from the first render

- Removed the experimental heading rules because they were not supported by the supplied references.
- Changed section headings from uppercase to title case.
- Removed default italics from employer, institution and supporting metadata.
- Reduced margins, line height and inter-block spacing to match the reference density.
- Changed dictionary access from attribute syntax to explicit keys for `skill["items"]` and `section["items"]`; the first implementation could render Python built-in method text instead of CV content.
- Replaced short demonstration payloads with realistic dense fixtures.

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
   - achievements and certifications
   - publications
   - volunteering
   - awards

The payload controls whether optional sections appear. The template does not create empty gaps for omitted content.

## Pagination rules

- No absolute positioning.
- No content tables.
- No default manual page break.
- Section headings remain with the next content block.
- Individual entries and projects avoid splitting where practical.
- The same typography is used for one-page and two-page output.
- A second page arises from content volume, not a selected page target.
- Content selection, not font shrinking, is the correct response to overflow.

## Current render QA

The tuned fixtures were rendered with WeasyPrint and rasterised for visual inspection.

- Dense fixture: 1 page, approximately 79% bottom-most vertical occupancy.
- Long fixture: 2 pages, approximately 95% occupancy on page one and 47% on page two.
- Contact line remains on one line.
- Dates share a common right edge.
- Bullet continuation lines align under the bullet text.
- No clipping, overlap, missing primary section or leaked Python method text was observed.

`qa_render.py` now blocks page-count drift, obviously sparse fixtures, missing primary sections and dictionary-method leakage.

## Remaining differences and limitations

- The original PDFs appear to use a LaTeX-style serif with slightly different glyph widths. The repository environment does not currently contain that exact face, so the implementation uses a metrically stable serif fallback chain.
- Exact source-PDF coordinates were not available as editable layout metadata. The tuned dimensions are based on rendered comparison and recurring visual proportions, not claimed source measurements.
- Chromium parity remains to be tested before this template can replace the live pipeline template.
- The two-page fixture is designed to test pagination and optional sections, not to reproduce the exact section break of any one reference CV.

## Acceptance criteria before pipeline integration

- `python Templates/simran_cv/qa_render.py` passes.
- Neutral one-page fixture renders without clipping or contact-line wrapping.
- Neutral two-page fixture paginates naturally and has a materially populated second page.
- Wrapped bullet lines align under the first word after the bullet.
- Dates remain aligned to a common right edge.
- Optional supporting sections can be omitted without spacing artefacts.
- Chromium and WeasyPrint show no material page-count or geometry drift.
- The template remains independent of candidate evidence and application-selection logic.
