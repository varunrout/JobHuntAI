#!/usr/bin/env python3
"""Hard visual contract gate for JobHuntAI CV and cover-letter artefacts.

The HTML templates are canonical. This gate blocks template drift and checks
rendered PDF geometry, typography, section labels, links, bullet continuation
alignment and cover-letter column alignment.
"""
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


def fmt_num(value: float) -> str:
    return f"{value:g}"


def compact_css(value: str) -> str:
    return re.sub(r"\s+", "", value or "").lower()


def css_rule(html: str, selector: str) -> dict[str, str]:
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", html, flags=re.S)
    if not match:
        return {}
    declarations: dict[str, str] = {}
    for item in match.group(1).split(";"):
        if ":" not in item:
            continue
        key, value = item.split(":", 1)
        declarations[key.strip().lower()] = value.strip()
    return declarations


def css_root_variables(html: str) -> dict[str, str]:
    return css_rule(html, ":root")


def require_decl(
    failures: list[tuple[str, str]],
    declarations: dict[str, str],
    selector: str,
    key: str,
    expected: str,
) -> None:
    actual = declarations.get(key)
    if actual is None:
        failures.append(("VISUAL_CSS_MISSING", f"{selector} is missing {key}"))
    elif compact_css(actual) != compact_css(expected):
        failures.append((
            "VISUAL_CSS_DRIFT",
            f"{selector} {key} is {actual!r}; locked value is {expected!r}",
        ))


def check_template_contract(
    cv_html: str | None = None,
    cl_html: str | None = None,
) -> list[tuple[str, str]]:
    contract = load_json(CONTRACT_PATH)
    cv_html = cv_html if cv_html is not None else CV_TEMPLATE_PATH.read_text(encoding="utf-8")
    cl_html = cl_html if cl_html is not None else CL_TEMPLATE_PATH.read_text(encoding="utf-8")
    failures: list[tuple[str, str]] = []
    version = contract["version"]

    for label, html in (("CV", cv_html), ("CL", cl_html)):
        if f'data-visual-contract="{version}"' not in html:
            failures.append(("VISUAL_VERSION_MISSING", f"{label} template does not declare {version}"))
        if re.search(r"<table\b", html, flags=re.I):
            failures.append(("VISUAL_TABLE_FORBIDDEN", f"{label} template contains a table"))
        for token in ("LinkedIn", "Portfolio", "GitHub"):
            if token not in html:
                failures.append(("CONTACT_LINK_MISSING", f"{label} template omits {token}"))
        if "{{ identity.portfolio }}" not in html:
            failures.append(("PORTFOLIO_BINDING_MISSING", f"{label} template omits identity.portfolio"))

    cv = contract["cv"]
    shared = contract["shared"]
    if "Selected Projects" in cv_html:
        failures.append(("PROJECT_HEADING_FORBIDDEN", "CV template contains 'Selected Projects'"))
    if cv_html.count("<h2>Projects</h2>") != 2:
        failures.append((
            "PROJECT_HEADING_DRIFT",
            "CV template must render the exact heading 'Projects' in both project-order branches",
        ))
    for section in ("summary", "skills", "experience", "projects", "education"):
        if f'data-section="{section}"' not in cv_html:
            failures.append(("SECTION_HOOK_MISSING", f"CV template omits data-section={section!r}"))
    if re.search(r"<ul(?![^>]*class=\"evidence-list\")", cv_html):
        failures.append(("UNCONTROLLED_LIST_STYLE", "Every CV bullet list must use evidence-list"))
    if "<main class=\"content-column\">" not in cv_html:
        failures.append(("CONTENT_COLUMN_MISSING", "CV template omits the locked content column"))

    root = css_root_variables(cv_html)
    require_decl(failures, root, ":root", "--ink", shared["ink"])
    require_decl(failures, root, ":root", "--link", shared["link"])
    require_decl(failures, root, ":root", "--rule", shared["rule"])
    require_decl(failures, root, ":root", "--body-size", f'{cv["body_size_pt"]}pt')
    require_decl(failures, root, ":root", "--body-line-height", str(cv["body_line_height"]))
    require_decl(failures, root, ":root", "--bullet-text-indent", f'{cv["bullet_text_indent_mm"]}mm')
    require_decl(failures, root, ":root", "--bullet-marker-offset", f'{cv["bullet_marker_offset_mm"]}mm')

    page = css_rule(cv_html, "@page")
    margins = cv["page_margin_mm"]
    require_decl(
        failures,
        page,
        "@page",
        "margin",
        f"{fmt_num(margins[0])}mm {fmt_num(margins[1])}mm {fmt_num(margins[2])}mm {fmt_num(margins[3])}mm",
    )
    body = css_rule(cv_html, f'body[data-visual-contract="{version}"]')
    require_decl(failures, body, "CV body", "font-family", "var(--font)")
    require_decl(failures, body, "CV body", "font-size", "var(--body-size)")
    require_decl(failures, body, "CV body", "line-height", "var(--body-line-height)")

    content_column = css_rule(cv_html, ".content-column")
    require_decl(failures, content_column, ".content-column", "width", "100%")
    require_decl(failures, content_column, ".content-column", "margin", "0")
    require_decl(failures, content_column, ".content-column", "padding", "0")

    evidence = css_rule(cv_html, ".evidence-list")
    require_decl(failures, evidence, ".evidence-list", "list-style", "none")
    require_decl(failures, evidence, ".evidence-list", "font-size", "var(--body-size)")
    require_decl(failures, evidence, ".evidence-list", "line-height", "var(--body-line-height)")

    li = css_rule(cv_html, ".evidence-list li")
    require_decl(failures, li, ".evidence-list li", "position", "relative")
    require_decl(failures, li, ".evidence-list li", "padding-left", "var(--bullet-text-indent)")
    require_decl(failures, li, ".evidence-list li", "text-indent", "0")
    require_decl(failures, li, ".evidence-list li", "font-size", "var(--body-size)")
    require_decl(failures, li, ".evidence-list li", "line-height", "var(--body-line-height)")

    marker = css_rule(cv_html, ".evidence-list li::before")
    require_decl(failures, marker, ".evidence-list li::before", "content", '"•"')
    require_decl(failures, marker, ".evidence-list li::before", "position", "absolute")
    require_decl(failures, marker, ".evidence-list li::before", "left", "var(--bullet-marker-offset)")
    require_decl(failures, marker, ".evidence-list li::before", "font-size", "var(--body-size)")

    cl = contract["cover_letter"]
    if "<main class=\"letter-column\">" not in cl_html:
        failures.append(("LETTER_COLUMN_MISSING", "Cover-letter template omits the locked letter column"))
    expected_order = [
        '<div class="role">{{ role_title }}</div>',
        '<div class="meta"><strong>{{ company }}</strong><span>{{ date }}</span></div>',
        '<p>{{ greeting }}</p>',
    ]
    positions = [cl_html.find(item) for item in expected_order]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        failures.append(("LETTER_STRUCTURE_DRIFT", "Role, company/date and greeting are not in locked order"))

    cl_root = css_root_variables(cl_html)
    require_decl(failures, cl_root, "CL :root", "--body-size", f'{cl["body_size_pt"]}pt')
    require_decl(failures, cl_root, "CL :root", "--body-line-height", str(cl["body_line_height"]))

    cl_page = css_rule(cl_html, "@page")
    cl_margins = cl["page_margin_mm"]
    require_decl(
        failures,
        cl_page,
        "CL @page",
        "margin",
        f"{fmt_num(cl_margins[0])}mm {fmt_num(cl_margins[1])}mm {fmt_num(cl_margins[2])}mm {fmt_num(cl_margins[3])}mm",
    )
    letter_column = css_rule(cl_html, ".letter-column")
    for key, expected in (("width", "100%"), ("margin", "0"), ("padding", "0")):
        require_decl(failures, letter_column, ".letter-column", key, expected)

    role = css_rule(cl_html, ".role")
    require_decl(failures, role, ".role", "width", "100%")
    require_decl(failures, role, ".role", "margin", "3mm 0 .6mm 0")
    require_decl(failures, role, ".role", "font-size", f'{cl["role_size_pt"]}pt')

    meta = css_rule(cl_html, ".meta")
    for key, expected in (
        ("width", "100%"),
        ("margin", "0 0 3mm 0"),
        ("padding", "0"),
        ("display", "grid"),
        ("grid-template-columns", "minmax(0,1fr) auto"),
    ):
        require_decl(failures, meta, ".meta", key, expected)

    paragraphs = css_rule(cl_html, ".letter-column p")
    require_decl(failures, paragraphs, ".letter-column p", "width", "100%")
    require_decl(failures, paragraphs, ".letter-column p", "margin", "0 0 2.2mm 0")
    require_decl(failures, paragraphs, ".letter-column p", "padding", "0")

    return failures


def _open_pdf(path: Path):
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(f"PyMuPDF is required for visual PDF checks: {exc}") from exc
    return fitz.open(str(path))


def _block_text(block: dict[str, Any]) -> str:
    return normalise(" ".join(
        "".join(span.get("text", "") for span in line.get("spans", []))
        for line in block.get("lines", [])
    ))


def _text_blocks(page) -> list[dict[str, Any]]:
    return [
        block for block in page.get_text("dict").get("blocks", [])
        if block.get("type") == 0
    ]


def _find_block_exact(page, needle: str) -> dict[str, Any] | None:
    target = normalise(needle)
    if not target:
        return None
    for block in _text_blocks(page):
        if _block_text(block) == target:
            return block
    return None


def _find_block(page, needle: str) -> dict[str, Any] | None:
    target = normalise(needle)
    if not target:
        return None
    for block in _text_blocks(page):
        if target in _block_text(block):
            return block
    return None


def _span_sizes(block: dict[str, Any]) -> list[float]:
    sizes: list[float] = []
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            text = span.get("text", "")
            if text.strip():
                sizes.append(float(span.get("size", 0.0)))
    return sizes


def _pdf_link_uris(document) -> list[str]:
    uris: list[str] = []
    for page in document:
        for link in page.get_links():
            uri = link.get("uri")
            if uri:
                uris.append(uri)
    return uris


def _check_font_size(
    failures: list[tuple[str, str]],
    label: str,
    sizes: list[float],
    expected: float,
    tolerance: float,
) -> None:
    if not sizes:
        failures.append(("VISUAL_TEXT_NOT_FOUND", f"No font-size evidence found for {label}"))
        return
    actual = statistics.median(sizes)
    if abs(actual - expected) > tolerance:
        failures.append((
            "VISUAL_FONT_SIZE",
            f"{label} is {actual:.2f} pt; locked size is {expected:.2f} pt",
        ))


def _first_nonspace_char_x(line: dict[str, Any], exclude_bullet: bool = False) -> float | None:
    for span in line.get("spans", []):
        for char in span.get("chars", []):
            value = char.get("c", "")
            if not value.strip():
                continue
            if exclude_bullet and value == "•":
                continue
            return float(char["bbox"][0])
    return None


def _line_text_raw(line: dict[str, Any]) -> str:
    return "".join(
        char.get("c", "")
        for span in line.get("spans", [])
        for char in span.get("chars", [])
    )


def _check_bullet_geometry(page, body_size: float, contract: dict[str, Any]) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    raw = page.get_text("rawdict")
    tolerance = float(contract["cv"]["bullet_alignment_tolerance_pt"])
    font_tolerance = float(contract["shared"]["font_tolerance_pt"])
    bullet_blocks = 0

    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        lines = block.get("lines", [])
        if not any("•" in _line_text_raw(line) for line in lines):
            continue
        bullet_blocks += 1
        bullet_xs: list[float] = []
        text_lines: list[dict[str, Any]] = []
        text_sizes: list[float] = []

        for line in lines:
            text = _line_text_raw(line)
            if "•" in text:
                bullet_x = _first_nonspace_char_x(line)
                if bullet_x is not None:
                    bullet_xs.append(bullet_x)
            if text.strip() and text.strip() != "•":
                text_lines.append(line)
                for span in line.get("spans", []):
                    span_text = "".join(char.get("c", "") for char in span.get("chars", []))
                    if span_text.strip() and span_text.strip() != "•":
                        text_sizes.append(float(span.get("size", 0.0)))

        if not text_lines:
            failures.append(("BULLET_TEXT_MISSING", "A bullet marker has no text"))
            continue
        text_xs = [_first_nonspace_char_x(line, exclude_bullet=True) for line in text_lines]
        text_xs = [x for x in text_xs if x is not None]
        if not text_xs:
            failures.append(("BULLET_TEXT_MISSING", "Unable to locate bullet text start"))
            continue
        first_x = text_xs[0]
        for continuation_x in text_xs[1:]:
            if abs(continuation_x - first_x) > tolerance:
                failures.append((
                    "BULLET_CONTINUATION_INDENT",
                    f"Wrapped bullet line starts at {continuation_x:.2f} pt, first line at {first_x:.2f} pt",
                ))
        if bullet_xs and not all(bullet_x < first_x for bullet_x in bullet_xs):
            failures.append(("BULLET_MARKER_POSITION", "Bullet marker is not left of its text"))
        if text_sizes:
            actual_size = statistics.median(text_sizes)
            if abs(actual_size - body_size) > font_tolerance:
                failures.append((
                    "BULLET_FONT_SIZE",
                    f"Bullet text is {actual_size:.2f} pt; locked body size is {body_size:.2f} pt",
                ))

    if bullet_blocks == 0:
        failures.append(("BULLET_GEOMETRY_MISSING", "Rendered CV contains no measurable bullet blocks"))
    return failures


def _pdf_font_names(document) -> set[str]:
    names: set[str] = set()
    for page in document:
        for block in _text_blocks(page):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span.get("text", "").strip():
                        names.add(str(span.get("font", "")))
    return names


def _check_pdf_fonts(
    failures: list[tuple[str, str]],
    document,
    allowed_fragments: list[str],
) -> None:
    names = _pdf_font_names(document)
    disallowed = [
        name for name in names
        if name and not any(fragment.lower() in name.lower() for fragment in allowed_fragments)
    ]
    if disallowed:
        failures.append((
            "VISUAL_FONT_FAMILY",
            "Rendered PDF contains non-contract fonts: " + ", ".join(sorted(disallowed)),
        ))


def check_cv_pdf(
    pdf_path: Path,
    cv: dict[str, Any],
) -> list[tuple[str, str]]:
    contract = load_json(CONTRACT_PATH)
    shared = contract["shared"]
    cv_contract = contract["cv"]
    failures: list[tuple[str, str]] = []
    document = _open_pdf(pdf_path)

    max_pages = int(cv_contract["default_max_pages"])
    if cv.get("page_limit_exception"):
        max_pages = 2
    if len(document) > max_pages:
        failures.append(("VISUAL_PAGE_COUNT", f"CV has {len(document)} pages; maximum is {max_pages}"))
    if not document:
        return [("VISUAL_EMPTY_PDF", "CV PDF has no pages")]

    _check_pdf_fonts(failures, document, shared["allowed_pdf_font_fragments"])
    first = document[0]
    text = normalise(first.get_text())
    for forbidden in cv_contract["forbidden_headings"]:
        if forbidden in text:
            failures.append(("PROJECT_HEADING_FORBIDDEN", f"Rendered CV contains {forbidden!r}"))
    if cv.get("projects") and "Projects" not in text:
        failures.append(("PROJECT_HEADING_MISSING", "Rendered CV does not contain the exact heading 'Projects'"))

    expected_left = mm_to_pt(float(cv_contract["page_margin_mm"][1]))
    geometry_tolerance = float(shared["geometry_tolerance_pt"])
    required_headings = ["Professional Summary", "Skills", "Experience", "Education"]
    if cv.get("projects"):
        required_headings.append("Projects")
    heading_xs: list[float] = []
    for heading in required_headings:
        block = _find_block_exact(first, heading)
        if block is None:
            failures.append(("SECTION_HEADING_MISSING", f"Rendered CV omits {heading!r}"))
            continue
        x0 = float(block["bbox"][0])
        heading_xs.append(x0)
        if abs(x0 - expected_left) > geometry_tolerance:
            failures.append((
                "SECTION_LEFT_EDGE",
                f"{heading!r} starts at {x0:.2f} pt; locked left edge is {expected_left:.2f} pt",
            ))
        _check_font_size(
            failures,
            f"heading {heading}",
            _span_sizes(block),
            float(cv_contract["heading_size_pt"]),
            float(shared["font_tolerance_pt"]),
        )
    if heading_xs and max(heading_xs) - min(heading_xs) > geometry_tolerance:
        failures.append(("SECTION_GRID_DRIFT", "CV section headings do not share one left edge"))

    name = str(cv.get("identity", {}).get("name", ""))
    name_block = _find_block(first, name)
    if name_block:
        _check_font_size(
            failures,
            "candidate name",
            _span_sizes(name_block),
            float(shared["name_size_pt"]),
            float(shared["font_tolerance_pt"]),
        )
    else:
        failures.append(("NAME_MISSING", "Candidate name is not visible in the CV PDF"))

    failures.extend(_check_bullet_geometry(first, float(cv_contract["body_size_pt"]), contract))

    uris = _pdf_link_uris(document)
    if not any(shared["portfolio_uri_contains"] in uri for uri in uris):
        failures.append(("PORTFOLIO_LINK_MISSING", "Rendered CV has no clickable portfolio link"))
    return failures


def check_cover_letter_pdf(
    pdf_path: Path,
    payload: dict[str, Any],
) -> list[tuple[str, str]]:
    contract = load_json(CONTRACT_PATH)
    shared = contract["shared"]
    cl_contract = contract["cover_letter"]
    failures: list[tuple[str, str]] = []
    document = _open_pdf(pdf_path)

    if len(document) > int(cl_contract["default_max_pages"]):
        failures.append(("VISUAL_PAGE_COUNT", f"Cover letter has {len(document)} pages; maximum is 1"))
    if not document:
        return [("VISUAL_EMPTY_PDF", "Cover-letter PDF has no pages")]

    _check_pdf_fonts(failures, document, shared["allowed_pdf_font_fragments"])
    first = document[0]
    expected_left = mm_to_pt(float(cl_contract["page_margin_mm"][1]))
    expected_right = float(first.rect.width) - expected_left
    tolerance = float(shared["geometry_tolerance_pt"])

    targets = [
        ("role title", str(payload.get("role_title", ""))),
        ("company/date row", str(payload.get("company", ""))),
        ("greeting", str(payload.get("greeting", ""))),
    ]
    paragraphs = payload.get("paragraphs", [])
    if paragraphs:
        targets.append(("first body paragraph", str(paragraphs[0])))

    blocks: dict[str, dict[str, Any]] = {}
    for label, text in targets:
        block = _find_block(first, text)
        if block is None:
            failures.append(("LETTER_TEXT_MISSING", f"Unable to locate {label}"))
            continue
        blocks[label] = block
        x0 = float(block["bbox"][0])
        if abs(x0 - expected_left) > tolerance:
            failures.append((
                "LETTER_LEFT_EDGE",
                f"{label} starts at {x0:.2f} pt; locked left edge is {expected_left:.2f} pt",
            ))

    meta_block = blocks.get("company/date row")
    if meta_block is not None:
        x1 = float(meta_block["bbox"][2])
        if abs(x1 - expected_right) > tolerance:
            failures.append((
                "LETTER_RIGHT_EDGE",
                f"Company/date row ends at {x1:.2f} pt; locked right edge is {expected_right:.2f} pt",
            ))

    role_block = blocks.get("role title")
    if role_block is not None:
        _check_font_size(
            failures,
            "cover-letter role title",
            _span_sizes(role_block),
            float(cl_contract["role_size_pt"]),
            float(shared["font_tolerance_pt"]),
        )
    paragraph_block = blocks.get("first body paragraph")
    if paragraph_block is not None:
        _check_font_size(
            failures,
            "cover-letter body",
            _span_sizes(paragraph_block),
            float(cl_contract["body_size_pt"]),
            float(shared["font_tolerance_pt"]),
        )

    name = str(payload.get("identity", {}).get("name", ""))
    name_block = _find_block(first, name)
    if name_block:
        _check_font_size(
            failures,
            "cover-letter candidate name",
            _span_sizes(name_block),
            float(shared["name_size_pt"]),
            float(shared["font_tolerance_pt"]),
        )
    else:
        failures.append(("NAME_MISSING", "Candidate name is not visible in the cover-letter PDF"))

    uris = _pdf_link_uris(document)
    if not any(shared["portfolio_uri_contains"] in uri for uri in uris):
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
            failures.append(("ARGUMENT_ERROR", "--cv-pdf and --cv-json must be provided together"))
        else:
            failures.extend(check_cv_pdf(Path(args.cv_pdf), load_json(Path(args.cv_json))))
    if args.cl_pdf or args.cl_json:
        if not (args.cl_pdf and args.cl_json):
            failures.append(("ARGUMENT_ERROR", "--cl-pdf and --cl-json must be provided together"))
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
