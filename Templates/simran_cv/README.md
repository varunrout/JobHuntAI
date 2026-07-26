# Simran-style CV template

Standalone HTML-to-PDF template workbench based on the recurring visual grammar in the supplied Simran CV references.

This directory is deliberately separate from `cv_pipeline/`. It is a visual-template project first. No application-specific evidence, identity selection or tailoring logic belongs here.

## Files

- `simran_cv_template.html`: semantic Jinja2 HTML and locked print CSS.
- `fixtures/one_page.json`: neutral one-page stress fixture.
- `fixtures/two_page.json`: neutral two-page stress fixture.
- `render.py`: renders a fixture to HTML and PDF with WeasyPrint.
- `VISUAL_SPEC.md`: initial source-derived design specification and open measurement questions.

## Render

```bash
python Templates/simran_cv/render.py \
  Templates/simran_cv/fixtures/one_page.json \
  --output-dir build/simran-one-page

python Templates/simran_cv/render.py \
  Templates/simran_cv/fixtures/two_page.json \
  --output-dir build/simran-two-page
```

The renderer creates `cv.html` and `cv.pdf`.

## Current design principles

- A4, single column and print-first.
- Dense serif typography with restrained spacing.
- Centred uppercase name and compact contact line.
- Section labels use small uppercase text and a thin horizontal rule.
- Role title and employer remain visually distinct from dates.
- Experience and project bullets share one geometry.
- Supporting sections are optional and flow naturally.
- No manual page break is required by the template.
- No tables, cards, icons, sidebars or decorative colour blocks.

## Status

This is the first implementation scaffold. Geometry is intentionally expressed through CSS variables so it can be tuned after rendered side-by-side comparison with the references. It is not yet wired into the JobHuntAI application pipeline.
