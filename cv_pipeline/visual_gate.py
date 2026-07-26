#!/usr/bin/env python3
"""Hard HTML and rendered-PDF visual contract for JobHuntAI artefacts."""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CONTRACT_PATH = ROOT / "visual_contract.json"
CV_TEMPLATE_PATH = ROOT / "templates" / "cv_template.html"
CL_TEMPLATE_PATH = ROOT / "templates" / "cover_letter_template.html"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def mm_to_pt(value: float) -> float:
    return value * 72.0 / 25.4


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value or "").lower()


def fmt(value: float) -> str:
    return f"{value:g}"


def css_rule(html: str, selector: str) -> dict[str, str]:
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", html, re.S)
    if not match:
        return {}
    out: dict[str, str] = {}
    for item in match.group(1).split(";"):
        if ":" in item:
            key, value = item.split(":", 1)
            out[key.strip().lower()] = value.strip()
    return out


def require(
    failures: list[tuple[str, str]],
    rule: dict[str, str],
    selector: str,
    key: str,
    expected: str,
) -> None:
    actual = rule.get(key)
    if actual is None:
        failures.append(("VISUAL_CSS_MISSING", f"{selector} is missing {key}"))
    elif compact(actual) != compact(expected):
        failures.append(("VISUAL_CSS_DRIFT", f"{selector} {key} is {actual!r}; expected {expected!r}"))


def check_template_contract(
    cv_html: str | None = None,
    cl_html: str | None = None,
) -> list[tuple[str, str]]:
    contract = load_json(CONTRACT_PATH)
    cv_html = CV_TEMPLATE_PATH.read_text(encoding="utf-8") if cv_html is None else cv_html
    cl_html = CL_TEMPLATE_PATH.read_text(encoding="utf-8") if cl_html is None else cl_html
    failures: list[tuple[str, str]] = []
    version = contract["version"]

    for label, html in (("CV", cv_html), ("CL", cl_html)):
        if f'data-visual-contract="{version}"' not in html:
            failures.append(("VISUAL_VERSION_MISSING", f"{label} template omits {version}"))
        if re.search(r"<table\b", html, re.I):
            failures.append(("VISUAL_TABLE_FORBIDDEN", f"{label} template contains a table"))
        for token in ("LinkedIn", "Portfolio", "GitHub"):
            if token not in html:
                failures.append(("CONTACT_LINK_MISSING", f"{label} template omits {token}"))
        if "{{ identity.portfolio }}" not in html:
            failures.append(("PORTFOLIO_BINDING_MISSING", f"{label} template omits identity.portfolio"))

    shared, cv, cl = contract["shared"], contract["cv"], contract["cover_letter"]
    if "Selected Projects" in cv_html:
        failures.append(("PROJECT_HEADING_FORBIDDEN", "CV template contains 'Selected Projects'"))
    if cv_html.count("<h2>Projects</h2>") != 2:
        failures.append(("PROJECT_HEADING_DRIFT", "Both project-order branches must use the exact heading 'Projects'"))
    for section in ("summary", "skills", "experience", "projects", "education"):
        if f'data-section="{section}"' not in cv_html:
            failures.append(("SECTION_HOOK_MISSING", f"CV template omits data-section={section!r}"))
    if re.search(r"<ul(?![^>]*class=\"evidence-list\")", cv_html):
        failures.append(("UNCONTROLLED_LIST_STYLE", "Every CV list must use evidence-list"))
    if '<main class="content-column">' not in cv_html:
        failures.append(("CONTENT_COLUMN_MISSING", "CV template omits content-column"))

    root = css_rule(cv_html, ":root")
    for key, value in (
        ("--ink", shared["ink"]),
        ("--link", shared["link"]),
        ("--rule", shared["rule"]),
        ("--body-size", f'{cv["body_size_pt"]}pt'),
        ("--body-line-height", str(cv["body_line_height"])),
        ("--bullet-text-indent", f'{cv["bullet_text_indent_mm"]}mm'),
        ("--bullet-marker-offset", f'{cv["bullet_marker_offset_mm"]}mm'),
    ):
        require(failures, root, ":root", key, value)

    require(
        failures,
        css_rule(cv_html, "@page"),
        "@page",
        "margin",
        " ".join(f"{fmt(value)}mm" for value in cv["page_margin_mm"]),
    )
    body = css_rule(cv_html, f'body[data-visual-contract="{version}"]')
    for key, value in (
        ("font-family", "var(--font)"),
        ("font-size", "var(--body-size)"),
        ("line-height", "var(--body-line-height)"),
    ):
        require(failures, body, "CV body", key, value)

    content_column = css_rule(cv_html, ".content-column")
    for key, value in (("width", "100%"), ("margin", "0"), ("padding", "0")):
        require(failures, content_column, ".content-column", key, value)

    evidence = css_rule(cv_html, ".evidence-list")
    for key, value in (
        ("list-style", "none"),
        ("font-size", "var(--body-size)"),
        ("line-height", "var(--body-line-height)"),
    ):
        require(failures, evidence, ".evidence-list", key, value)

    bullet = css_rule(cv_html, ".evidence-list li")
    for key, value in (
        ("position", "relative"),
        ("padding-left", "var(--bullet-text-indent)"),
        ("text-indent", "0"),
        ("font-size", "var(--body-size)"),
        ("line-height", "var(--body-line-height)"),
    ):
        require(failures, bullet, ".evidence-list li", key, value)

    marker = css_rule(cv_html, ".evidence-list li::before")
    for key, value in (
        ("content", '"•"'),
        ("position", "absolute"),
        ("left", "var(--bullet-marker-offset)"),
        ("font-size", "var(--body-size)"),
    ):
        require(failures, marker, ".evidence-list li::before", key, value)

    if '<main class="letter-column">' not in cl_html:
        failures.append(("LETTER_COLUMN_MISSING", "Cover-letter template omits letter-column"))
    locked_order = (
        '<div class="role">{{ role_title }}</div>',
        '<div class="meta"><strong>{{ company }}</strong><span>{{ date }}</span></div>',
        '<p>{{ greeting }}</p>',
    )
    positions = [cl_html.find(item) for item in locked_order]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        failures.append(("LETTER_STRUCTURE_DRIFT", "Role, company/date and greeting are not in locked order"))

    cl_root = css_rule(cl_html, ":root")
    require(failures, cl_root, "CL :root", "--body-size", f'{cl["body_size_pt"]}pt')
    require(failures, cl_root, "CL :root", "--body-line-height", str(cl["body_line_height"]))
    require(
        failures,
        css_rule(cl_html, "@page"),
        "CL @page",
        "margin",
        " ".join(f"{fmt(value)}mm" for value in cl["page_margin_mm"]),
    )
    letter_column = css_rule(cl_html, ".letter-column")
    for key, value in (("width", "100%"), ("margin", "0"), ("padding", "0")):
        require(failures, letter_column, ".letter-column", key, value)

    role = css_rule(cl_html, ".role")
    for key, value in (
        ("width", "100%"),
        ("margin", "3mm 0 .6mm 0"),
        ("font-size", f'{cl["role_size_pt"]}pt'),
    ):
        require(failures, role, ".role", key, value)

    meta = css_rule(cl_html, ".meta")
    for key, value in (
        ("width", "100%"),
        ("margin", "0 0 3mm 0"),
        ("padding", "0"),
        ("display", "grid"),
        ("grid-template-columns", "minmax(0,1fr) auto"),
    ):
        require(failures, meta, ".meta", key, value)

    paragraphs = css_rule(cl_html, ".letter-column p")
    for key, value in (("width", "100%"), ("margin", "0 0 2.2mm 0"), ("padding", "0")):
        require(failures, paragraphs, ".letter-column p", key, value)
    return failures


def _open_pdf(path: Path):
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(f"PyMuPDF is required: {exc}") from exc
    return fitz.open(str(path))


def _blocks(page) -> list[dict[str, Any]]:
    return [block for block in page.get_text("dict").get("blocks", []) if block.get("type") == 0]


def _block_text(block: dict[str, Any]) -> str:
    return normalise(" ".join(
        "".join(span.get("text", "") for span in line.get("spans", []))
        for line in block.get("lines", [])
    ))


def _find_block(page, needle: str, exact: bool = False) -> dict[str, Any] | None:
    target = normalise(needle).casefold()
    if not target:
        return None
    for block in _blocks(page):
        value = _block_text(block).casefold()
        if (value == target) if exact else (target in value):
            return block
    return None


def _span_sizes(block: dict[str, Any]) -> list[float]:
    return [
        float(span.get("size", 0))
        for line in block.get("lines", [])
        for span in line.get("spans", [])
        if span.get("text", "").strip()
    ]


def _check_size(
    failures: list[tuple[str, str]],
    label: str,
    sizes: list[float],
    expected: float,
    tolerance: float,
) -> None:
    if not sizes:
        failures.append(("VISUAL_TEXT_NOT_FOUND", f"No size evidence found for {label}"))
        return
    actual = statistics.median(sizes)
    if abs(actual - expected) > tolerance:
        failures.append(("VISUAL_FONT_SIZE", f"{label} is {actual:.2f} pt; expected {expected:.2f} pt"))


def _links(document) -> list[str]:
    return [
        link["uri"]
        for page in document
        for link in page.get_links()
        if link.get("uri")
    ]


def _font_names(document) -> set[str]:
    return {
        str(span.get("font", ""))
        for page in document
        for block in _blocks(page)
        for line in block.get("lines", [])
        for span in line.get("spans", [])
        if span.get("text", "").strip()
    }


def _check_fonts(
    failures: list[tuple[str, str]],
    document,
    allowed: list[str],
) -> None:
    bad = [
        name for name in _font_names(document)
        if name and not any(fragment.casefold() in name.casefold() for fragment in allowed)
    ]
    if bad:
        failures.append(("VISUAL_FONT_FAMILY", "Non-contract fonts: " + ", ".join(sorted(bad))))


def _raw_line_text(line: dict[str, Any]) -> str:
    return "".join(
        char.get("c", "")
        for span in line.get("spans", [])
        for char in span.get("chars", [])
    )


def _first_char_x(line: dict[str, Any], skip_bullet: bool = False) -> float | None:
    for span in line.get("spans", []):
        for char in span.get("chars", []):
            value = char.get("c", "")
            if not value.strip() or (skip_bullet and value == "•"):
                continue
            return float(char["bbox"][0])
    return None


def _check_bullets(page, contract: dict[str, Any]) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    body_size = float(contract["cv"]["body_size_pt"])
    align_tolerance = float(contract["cv"]["bullet_alignment_tolerance_pt"])
    font_tolerance = float(contract["shared"]["font_tolerance_pt"])
    measured = 0

    for block in page.get_text("rawdict").get("blocks", []):
        if block.get("type") != 0:
            continue
        lines = block.get("lines", [])
        if not any("•" in _raw_line_text(line) for line in lines):
            continue
        measured += 1
        bullet_xs, text_xs, sizes = [], [], []
        for line in lines:
            text = _raw_line_text(line)
            if "•" in text:
                x = _first_char_x(line)
                if x is not None:
                    bullet_xs.append(x)
            if text.strip() and text.strip() != "•":
                x = _first_char_x(line, skip_bullet=True)
                if x is not None:
                    text_xs.append(x)
                for span in line.get("spans", []):
                    chars = "".join(char.get("c", "") for char in span.get("chars", []))
                    if chars.strip() and chars.strip() != "•":
                        sizes.append(float(span.get("size", 0)))

        if not text_xs:
            failures.append(("BULLET_TEXT_MISSING", "Bullet marker has no measurable text"))
            continue
        first_x = text_xs[0]
        for continuation_x in text_xs[1:]:
            if abs(continuation_x - first_x) > align_tolerance:
                failures.append((
                    "BULLET_CONTINUATION_INDENT",
                    f"Wrapped line starts at {continuation_x:.2f} pt; first line starts at {first_x:.2f} pt",
                ))
        if bullet_xs and not all(x < first_x for x in bullet_xs):
            failures.append(("BULLET_MARKER_POSITION", "Bullet marker is not left of its text"))
        if sizes and abs(statistics.median(sizes) - body_size) > font_tolerance:
            failures.append(("BULLET_FONT_SIZE", f"Bullet text is {statistics.median(sizes):.2f} pt; expected {body_size:.2f} pt"))

    if measured == 0:
        failures.append(("BULLET_GEOMETRY_MISSING", "No measurable bullet blocks found"))
    return failures


def check_cv_pdf(pdf_path: Path, payload: dict[str, Any]) -> list[tuple[str, str]]:
    contract = load_json(CONTRACT_PATH)
    shared, cv = contract["shared"], contract["cv"]
    failures: list[tuple[str, str]] = []
    document = _open_pdf(pdf_path)
    max_pages = 2 if payload.get("page_limit_exception") else int(cv["default_max_pages"])
    if len(document) > max_pages:
        failures.append(("VISUAL_PAGE_COUNT", f"CV has {len(document)} pages; maximum is {max_pages}"))
    if not document:
        return [("VISUAL_EMPTY_PDF", "CV PDF has no pages")]

    _check_fonts(failures, document, shared["allowed_pdf_font_fragments"])
    page = document[0]
    text = normalise(page.get_text())
    for heading in cv["forbidden_headings"]:
        if heading in text:
            failures.append(("PROJECT_HEADING_FORBIDDEN", f"Rendered CV contains {heading!r}"))
    if payload.get("projects") and "Projects" not in text:
        failures.append(("PROJECT_HEADING_MISSING", "Rendered CV omits the exact heading 'Projects'"))

    expected_left = mm_to_pt(float(cv["page_margin_mm"][1]))
    tolerance = float(shared["geometry_tolerance_pt"])
    headings = ["Professional Summary", "Skills", "Experience", "Education"]
    if payload.get("projects"):
        headings.append("Projects")
    x_values = []
    for heading in headings:
        block = _find_block(page, heading, exact=True)
        if block is None:
            failures.append(("SECTION_HEADING_MISSING", f"Rendered CV omits {heading!r}"))
            continue
        x0 = float(block["bbox"][0])
        x_values.append(x0)
        if abs(x0 - expected_left) > tolerance:
            failures.append(("SECTION_LEFT_EDGE", f"{heading!r} starts at {x0:.2f} pt; expected {expected_left:.2f} pt"))
        _check_size(
            failures,
            f"heading {heading}",
            _span_sizes(block),
            float(cv["heading_size_pt"]),
            float(shared["font_tolerance_pt"]),
        )
    if x_values and max(x_values) - min(x_values) > tolerance:
        failures.append(("SECTION_GRID_DRIFT", "CV headings do not share one left edge"))

    name = str(payload.get("identity", {}).get("name", ""))
    name_block = _find_block(page, name)
    if name_block:
        _check_size(failures, "candidate name", _span_sizes(name_block), float(shared["name_size_pt"]), float(shared["font_tolerance_pt"]))
    else:
        failures.append(("NAME_MISSING", "Candidate name is not visible"))

    failures.extend(_check_bullets(page, contract))
    if not any(shared["portfolio_uri_contains"] in uri for uri in _links(document)):
        failures.append(("PORTFOLIO_LINK_MISSING", "Rendered CV has no clickable portfolio link"))
    return failures


def check_cover_letter_pdf(pdf_path: Path, payload: dict[str, Any]) -> list[tuple[str, str]]:
    contract = load_json(CONTRACT_PATH)
    shared, cl = contract["shared"], contract["cover_letter"]
    failures: list[tuple[str, str]] = []
    document = _open_pdf(pdf_path)
    if len(document) > int(cl["default_max_pages"]):
        failures.append(("VISUAL_PAGE_COUNT", f"Cover letter has {len(document)} pages; maximum is 1"))
    if not document:
        return [("VISUAL_EMPTY_PDF", "Cover-letter PDF has no pages")]

    _check_fonts(failures, document, shared["allowed_pdf_font_fragments"])
    page = document[0]
    left = mm_to_pt(float(cl["page_margin_mm"][1]))
    right = float(page.rect.width) - left
    tolerance = float(shared["geometry_tolerance_pt"])
    targets = [
        ("role title", str(payload.get("role_title", ""))),
        ("company/date row", str(payload.get("company", ""))),
        ("greeting", str(payload.get("greeting", ""))),
    ]
    if payload.get("paragraphs"):
        targets.append(("first body paragraph", str(payload["paragraphs"][0])))

    found: dict[str, dict[str, Any]] = {}
    for label, value in targets:
        block = _find_block(page, value)
        if block is None:
            failures.append(("LETTER_TEXT_MISSING", f"Unable to locate {label}"))
            continue
        found[label] = block
        if abs(float(block["bbox"][0]) - left) > tolerance:
            failures.append(("LETTER_LEFT_EDGE", f"{label} starts at {float(block['bbox'][0]):.2f} pt; expected {left:.2f} pt"))

    meta = found.get("company/date row")
    if meta and abs(float(meta["bbox"][2]) - right) > tolerance:
        failures.append(("LETTER_RIGHT_EDGE", f"Company/date row ends at {float(meta['bbox'][2]):.2f} pt; expected {right:.2f} pt"))
    if found.get("role title"):
        _check_size(failures, "cover-letter role title", _span_sizes(found["role title"]), float(cl["role_size_pt"]), float(shared["font_tolerance_pt"]))
    if found.get("first body paragraph"):
        _check_size(failures, "cover-letter body", _span_sizes(found["first body paragraph"]), float(cl["body_size_pt"]), float(shared["font_tolerance_pt"]))

    name = str(payload.get("identity", {}).get("name", ""))
    name_block = _find_block(page, name)
    if name_block:
        _check_size(failures, "cover-letter candidate name", _span_sizes(name_block), float(shared["name_size_pt"]), float(shared["font_tolerance_pt"]))
    else:
        failures.append(("NAME_MISSING", "Candidate name is not visible"))
    if not any(shared["portfolio_uri_contains"] in uri for uri in _links(document)):
        failures.append(("PORTFOLIO_LINK_MISSING", "Rendered cover letter has no clickable portfolio link"))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="JobHuntAI hard visual contract gate")
    parser.add_argument("--cv-pdf")
    parser.add_argument("--cv-json")
    parser.add_argument("--cl-pdf")
    parser.add_argument("--cl-json")
    args = parser.parse_args()

    failures = check_template_contract()
    if args.cv_pdf or args.cv_json:
        if not (args.cv_pdf and args.cv_json):
            failures.append(("ARGUMENT_ERROR", "--cv-pdf and --cv-json are required together"))
        else:
            failures.extend(check_cv_pdf(Path(args.cv_pdf), load_json(Path(args.cv_json))))
    if args.cl_pdf or args.cl_json:
        if not (args.cl_pdf and args.cl_json):
            failures.append(("ARGUMENT_ERROR", "--cl-pdf and --cl-json are required together"))
        else:
            failures.extend(check_cover_letter_pdf(Path(args.cl_pdf), load_json(Path(args.cl_json))))

    if failures:
        print(f"VISUAL CONTRACT BLOCKED - {len(failures)} failure(s):")
        for code, detail in failures:
            print(f"[{code}] {detail}")
        return 2
    print("VISUAL CONTRACT CLEAN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
