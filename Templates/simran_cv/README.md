# Simran-style CV template workbench

This directory contains a standalone HTML/CSS CV template derived from the recurring visual grammar across the supplied Simran CV references. It is intentionally separate from candidate evidence, vacancy tailoring and the live `cv_pipeline/` templates.

## Files

- `simran_cv_template.html` - semantic Jinja2 template and print CSS
- `render.py` - renders one JSON payload to HTML and PDF with WeasyPrint
- `qa_render.py` - renders both fixtures and checks page count, density, section presence and template leakage
- `fixtures/one_page.json` - dense one-page neutral fixture
- `fixtures/two_page.json` - naturally paginating two-page neutral fixture
- `VISUAL_SPEC.md` - source-derived layout rules, tuned tokens and remaining limitations

## Render

```bash
python Templates/simran_cv/render.py \
  Templates/simran_cv/fixtures/one_page.json \
  --output-dir build/simran-one-page

python Templates/simran_cv/render.py \
  Templates/simran_cv/fixtures/two_page.json \
  --output-dir build/simran-two-page
```

Each command writes `cv.html` and `cv.pdf` into the selected output directory.

## QA

```bash
python Templates/simran_cv/qa_render.py
```

The QA script currently enforces:

- one-page fixture remains one page;
- two-page fixture remains two pages;
- dense fixture is not obviously sparse;
- final page of the long fixture carries material content;
- primary sections render;
- dictionary-method text cannot leak into the PDF.

## Visual principles

- A4 portrait, one column
- compact serif typography
- centred uppercase name and one-line contact details
- bold title-case section headings without decorative rules
- labelled skill lines
- role and date on one row, employer and location immediately below
- compact bullets with a stable hanging indent
- natural pagination without manual page breaks
- no sidebars, cards, icons, profile photos or layout tables

## Boundary

This is a visual-template workbench, not yet the production template. Do not connect it to `cv_pipeline/` until WeasyPrint and Chromium parity has been tested and the visual contract has been versioned around the final geometry.
