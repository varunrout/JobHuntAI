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


def canonical_https(value: str) -> str:
    clean = (value or "").strip()
    if not clean:
        return ""
    if clean.startswith("https://"):
        return clean
    if clean.startswith("http://"):
        return "https://" + clean[7:]
    return "https://" + clean


def url_label(value: str) -> str:
    clean = (value or "").strip()
    if clean.startswith("https://"):
        clean = clean[8:]
    elif clean.startswith("http://"):
        clean = clean[7:]
    return clean.rstrip("/")


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


def _contact_markup(html: str) -> str:
    match = re.search(r'<div class="contact">(.*?)</div>', html, re.S)
    return match.group(1) if match else ""


def _check_shared_template_markup(label: str, html: str, version: str) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    if f'data-visual-contract="{version}"' not in html:
        failures.append(("VISUAL_VERSION_MISSING", f"{label} template omits {version}"))
    if re.search(r"<table\b", html, re.I):
        failures.append(("VISUAL_TABLE_FORBIDDEN", f"{label} template contains a table"))
    for retired in ("#c28d41", "#7d5411", "#facb8d", "#fffdf9"):
        if retired in html.lower():
            failures.append(("RETIRED_COLOUR_PRESENT", f"{label} template still contains retired colour {retired}"))
    for fallback in ("DejaVu", "Liberation"):
        if fallback in html:
            failures.append(("SERIF_FALLBACK_DRIFT", f"{label} template contains non-contract fallback {fallback}"))
    for binding in ("identity.github", "identity.portfolio"):
        if binding not in html:
            failures.append(("CTA_BINDING_MISSING", f"{label} template omits {binding}"))
    if "github_value or portfolio_value" not in html:
        failures.append(("CTA_OPTIONALITY_MISSING", f"{label} does not independently gate the CTA stack"))
    contact = _contact_markup(html)
    if not contact:
        failures.append(("CONTACT_MARKUP_MISSING", f"{label} contact line is missing"))
    else:
        if "identity.github" in contact or "identity.portfolio" in contact:
            failures.append(("CONTACT_DUPLICATES_CTA", f"{label} contact line still carries GitHub or portfolio"))
        if "identity.phone" not in contact or "identity.email" not in contact or "identity.linkedin" not in contact:
            failures.append(("CONTACT_BINDING_DRIFT", f"{label} contact line must be phone | email | LinkedIn"))
    return failures


def _check_shared_css(html: str, version: str, shared: dict[str, Any], body_size: float, body_line_height: float) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    root = css_rule(html, ":root")
    for key, value in (
        ("--ink", shared["ink"]),
        ("--link", shared["link"]),
        ("--button-ground", shared["button_ground"]),
        ("--neutral-700", shared.get("neutral_700", "#605d5d")),
        ("--neutral-800", shared.get("neutral_800", "#444141")),
        ("--divider", shared.get("divider", "rgba(32,31,29,0.16)")),
        ("--surface", "#ffffff"),
        ("--font", '"Lora",Georgia,serif'),
        ("--font-heading", '"Cormorant Garamond",Georgia,serif'),
        ("--body-size", f"{body_size}pt"),
        ("--body-line-height", str(body_line_height)),
    ):
        require(failures, root, ":root", key, value)

    body = css_rule(html, f'body[data-visual-contract="{version}"]')
    for key, value in (
        ("font-family", "var(--font)"),
        ("font-size", "var(--body-size)"),
        ("line-height", "var(--body-line-height)"),
        ("text-align", "left"),
        ("hyphens", "none"),
    ):
        require(failures, body, "body", key, value)

    header = css_rule(html, "header")
    for key, value in (
        ("display", "grid"),
        ("grid-template-columns", "minmax(0,1fr) auto"),
        ("align-items", "start"),
        ("padding-bottom", "7px"),
        ("border-bottom", "2px solid var(--ink)"),
    ):
        require(failures, header, "header", key, value)

    name = css_rule(html, ".name")
    for key, value in (
        ("font-family", "var(--font-heading)"),
        ("font-size", f'{fmt(float(shared["name_size_pt"]))}pt'),
        ("font-weight", "400"),
        ("letter-spacing", ".06em"),
        ("text-transform", "uppercase"),
    ):
        require(failures, name, ".name", key, value)

    headline = css_rule(html, ".headline")
    for key, value in (
        ("font-size", f'{shared.get("headline_size_pt", 11.5)}pt'),
        ("letter-spacing", ".02em"),
        ("color", "var(--neutral-800)"),
    ):
        require(failures, headline, ".headline", key, value)
    require(failures, css_rule(html, ".location"), ".location", "white-space", "nowrap")

    contact = css_rule(html, ".contact")
    for key, value in (
        ("font-family", "var(--font)"),
        ("font-size", f'{shared.get("contact_size_pt", 8.8)}pt'),
        ("letter-spacing", ".01em"),
        ("color", "var(--neutral-700)"),
        ("white-space", "nowrap"),
        ("font-variant-numeric", "tabular-nums"),
    ):
        require(failures, contact, ".contact", key, value)
    require(failures, css_rule(html, ".contact .sep"), ".contact .sep", "padding", "0 2px")

    require(failures, css_rule(html, ".cta-stack"), ".cta-stack", "display", "block")
    cta = css_rule(html, ".cta-btn")
    for key, value in (
        ("display", "block"),
        ("padding", "3px 11px"),
        ("background", "#E9F0F8"),
        ("border", "1px solid #1A4F8B"),
        ("color", "#1A4F8B"),
        ("border-radius", "4px"),
        ("font-family", '"Lora",Georgia,serif'),
        ("font-weight", "600"),
        ("font-size", "9pt"),
        ("letter-spacing", ".01em"),
        ("line-height", "1.15"),
        ("white-space", "nowrap"),
    ):
        require(failures, cta, ".cta-btn", key, value)
    require(failures, css_rule(html, ".cta-btn + .cta-btn"), ".cta-btn + .cta-btn", "margin-top", "6px")
    ico = css_rule(html, ".cta-ico")
    for key, value in (("width", "12px"), ("height", "12px"), ("margin-right", "7px"), ("vertical-align", "-1px")):
        require(failures, ico, ".cta-ico", key, value)
    return failures


def check_template_contract(
    cv_html: str | None = None,
    cl_html: str | None = None,
) -> list[tuple[str, str]]:
    contract = load_json(CONTRACT_PATH)
    cv_html = CV_TEMPLATE_PATH.read_text(encoding="utf-8") if cv_html is None else cv_html
    cl_html = CL_TEMPLATE_PATH.read_text(encoding="utf-8") if cl_html is None else cl_html
    failures: list[tuple[str, str]] = []
    version = contract["version"]
    shared, cv, cl = contract["shared"], contract["cv"], contract["cover_letter"]

    failures.extend(_check_shared_template_markup("CV", cv_html, version))
    failures.extend(_check_shared_template_markup("CL", cl_html, version))
    failures.extend(_check_shared_css(cv_html, version, shared, float(cv["body_size_pt"]), float(cv["body_line_height"])))
    failures.extend(_check_shared_css(cl_html, version, shared, float(cl["body_size_pt"]), float(cl["body_line_height"])))

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
        ("--bullet-text-indent", f'{cv["bullet_text_indent_mm"]}mm'),
        ("--bullet-marker-offset", f'{cv["bullet_marker_offset_mm"]}mm'),
    ):
        require(failures, root, ":root", key, value)
    require(failures, css_rule(cv_html, "@page"), "@page", "margin", "10mm")

    h2 = css_rule(cv_html, "h2")
    for key, value in (
        ("font-family", "var(--font-heading)"),
        ("font-size", f'{cv["heading_size_pt"]}pt'),
        ("font-weight", "600"),
        ("letter-spacing", ".03em"),
        ("text-transform", "uppercase"),
        ("color", "var(--ink)"),
        ("border-bottom", "1px solid var(--divider)"),
        ("padding-bottom", "3px"),
    ):
        require(failures, h2, "h2", key, value)

    content_column = css_rule(cv_html, ".content-column")
    for key, value in (("width", "100%"), ("margin", "0"), ("padding", "0")):
        require(failures, content_column, ".content-column", key, value)

    evidence = css_rule(cv_html, ".evidence-list")
    for key, value in (("list-style", "none"), ("font-size", "var(--body-size)"), ("line-height", "var(--body-line-height)")):
        require(failures, evidence, ".evidence-list", key, value)
    bullet = css_rule(cv_html, ".evidence-list li")
    for key, value in (("position", "relative"), ("padding-left", "var(--bullet-text-indent)"), ("text-indent", "0"), ("font-size", "var(--body-size)"), ("line-height", "var(--body-line-height)")):
        require(failures, bullet, ".evidence-list li", key, value)
    marker = css_rule(cv_html, ".evidence-list li::before")
    for key, value in (("content", '"·"'), ("position", "absolute"), ("left", "var(--bullet-marker-offset)"), ("color", "var(--ink)"), ("font-size", "var(--body-size)")):
        require(failures, marker, ".evidence-list li::before", key, value)
    require(failures, css_rule(cv_html, ".bullet-marker"), ".bullet-marker", "color", "var(--ink)")

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
    require(failures, css_rule(cl_html, "@page"), "CL @page", "margin", "10mm")
    letter_column = css_rule(cl_html, ".letter-column")
    for key, value in (("width", "100%"), ("margin", "0"), ("padding", "0")):
        require(failures, letter_column, ".letter-column", key, value)
    role = css_rule(cl_html, ".role")
    for key, value in (("width", "100%"), ("margin", "3mm 0 .6mm 0"), ("font-size", f'{cl["role_size_pt"]}pt')):
        require(failures, role, ".role", key, value)
    meta = css_rule(cl_html, ".meta")
    for key, value in (("width", "100%"), ("margin", "0 0 3mm 0"), ("padding", "0"), ("display", "grid"), ("grid-template-columns", "minmax(0,1fr) auto")):
        require(failures, meta, ".meta", key, value)
    paragraphs = css_rule(cl_html, ".letter-column p")
    for key, value in (("width", "100%"), ("margin", "0 0 2.2mm 0"), ("padding", "0"), ("text-align", "left")):
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
    return normalise(" ".join("".join(span.get("text", "") for span in line.get("spans", [])) for line in block.get("lines", [])))


def _find_block(page, needle: str, exact: bool = False) -> dict[str, Any] | None:
    target = normalise(needle).casefold()
    if not target:
        return None
    for block in _blocks(page):
        value = _block_text(block).casefold()
        if (value == target) if exact else (target in value):
            return block
    return None


def _find_block_prefix(page, needle: str, min_words: int = 8, max_words: int = 18) -> dict[str, Any] | None:
    """Locate the start block for long rendered text that may be split across PDF blocks."""
    block = _find_block(page, needle)
    if block is not None:
        return block
    words = normalise(needle).split()
    if len(words) < min_words:
        return None
    probe_lengths = sorted({min(len(words), max_words), 14, 10, min_words}, reverse=True)
    for count in probe_lengths:
        if count > len(words):
            continue
        block = _find_block(page, " ".join(words[:count]))
        if block is not None:
            return block
    return None


def _find_block_across_pages(document, needle: str, exact: bool = False):
    for page in document:
        block = _find_block(page, needle, exact=exact)
        if block is not None:
            return page, block
    return None, None


def _spacing_drift_present(document, needle: str) -> bool:
    target = re.sub(r"\s+", "", needle).casefold()
    for page in document:
        for block in _blocks(page):
            value = re.sub(r"\s+", "", _block_text(block)).casefold()
            if value == target and _block_text(block).casefold() != normalise(needle).casefold():
                return True
    return False


def _span_sizes(block: dict[str, Any]) -> list[float]:
    return [float(span.get("size", 0)) for line in block.get("lines", []) for span in line.get("spans", []) if span.get("text", "").strip()]


def _matching_span_sizes(page, needle: str) -> list[float]:
    target = normalise(needle).casefold()
    sizes: list[float] = []
    for block in _blocks(page):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                value = normalise(span.get("text", "")).casefold()
                if value == target:
                    sizes.append(float(span.get("size", 0)))
    return sizes


def _check_size(failures: list[tuple[str, str]], label: str, sizes: list[float], expected: float, tolerance: float) -> None:
    if not sizes:
        failures.append(("VISUAL_TEXT_NOT_FOUND", f"No size evidence found for {label}"))
        return
    actual = statistics.median(sizes)
    if abs(actual - expected) > tolerance:
        failures.append(("VISUAL_FONT_SIZE", f"{label} is {actual:.2f} pt; expected {expected:.2f} pt"))


def _links(document) -> list[str]:
    return [link["uri"] for page in document for link in page.get_links() if link.get("uri")]


def _font_names(document) -> set[str]:
    return {str(span.get("font", "")) for page in document for block in _blocks(page) for line in block.get("lines", []) for span in line.get("spans", []) if span.get("text", "").strip()}


def _check_fonts(failures: list[tuple[str, str]], document, allowed: list[str]) -> None:
    bad = [name for name in _font_names(document) if name and not any(fragment.casefold() in name.casefold() for fragment in allowed)]
    if bad:
        failures.append(("VISUAL_FONT_FAMILY", "Non-contract fonts: " + ", ".join(sorted(bad))))


def _check_link_schemes(failures: list[tuple[str, str]], document) -> None:
    for uri in _links(document):
        if not (uri.startswith("https://") or uri.startswith("mailto:")):
            failures.append(("UNSAFE_PDF_LINK", f"PDF link is not absolute https/mailto: {uri}"))


def _largest_link_rect(page, uri: str):
    matches = [link.get("from") for link in page.get_links() if link.get("uri") == uri and link.get("from") is not None]
    if not matches:
        return None
    return max(matches, key=lambda rect: float(rect.width) * float(rect.height))


def _check_ctas(failures: list[tuple[str, str]], document, payload: dict[str, Any], shared: dict[str, Any]) -> None:
    if not document:
        return
    identity = payload.get("identity", {}) or {}
    github = str(identity.get("github", "") or "").strip()
    portfolio = str(identity.get("portfolio", "") or "").strip()
    first_page = document[0]
    page_text = first_page.get_text()
    expected: list[tuple[str, str, str]] = []
    if github:
        expected.append(("GitHub", canonical_https(github), url_label(github)))
    if portfolio:
        expected.append(("portfolio", canonical_https(portfolio), url_label(portfolio)))

    rects: dict[str, Any] = {}
    for label, uri, text_label in expected:
        if text_label not in page_text:
            failures.append(("CTA_TEXT_LAYER_MISSING", f"{label} CTA label {text_label!r} is not extractable text"))
        rect = _largest_link_rect(first_page, uri)
        if rect is None:
            failures.append(("CTA_LINK_MISSING", f"{label} CTA has no clickable {uri}"))
        else:
            rects[label] = rect

    if github and portfolio and "GitHub" in rects and "portfolio" in rects:
        g, p = rects["GitHub"], rects["portfolio"]
        tolerance = float(shared["cta_dimension_tolerance_pt"])
        if abs(float(g.width) - float(p.width)) > tolerance or abs(float(g.height) - float(p.height)) > tolerance:
            failures.append(("CTA_DIMENSION_MISMATCH", f"CTA outer boxes differ: GitHub {g.width:.2f}x{g.height:.2f} pt, portfolio {p.width:.2f}x{p.height:.2f} pt"))
        if float(g.y0) >= float(p.y0):
            failures.append(("CTA_ORDER_DRIFT", "GitHub CTA is not above portfolio CTA"))
        gap = float(p.y0) - float(g.y1)
        if gap < float(shared["cta_min_gap_pt"]):
            failures.append(("CTA_GAP_MISSING", f"CTA gap is {gap:.2f} pt"))


def _raw_line_text(line: dict[str, Any]) -> str:
    return "".join(char.get("c", "") for span in line.get("spans", []) for char in span.get("chars", []))


def _first_char_x(line: dict[str, Any], skip_bullet: bool = False) -> float | None:
    for span in line.get("spans", []):
        for char in span.get("chars", []):
            value = char.get("c", "")
            if not value.strip() or (skip_bullet and value == "·"):
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
        if not any(_raw_line_text(line).lstrip().startswith("·") for line in lines):
            continue
        measured += 1
        bullet_xs, text_xs, sizes = [], [], []
        for line in lines:
            text = _raw_line_text(line)
            if "·" in text:
                x = _first_char_x(line)
                if x is not None:
                    bullet_xs.append(x)
            if text.strip() and text.strip() != "·":
                x = _first_char_x(line, skip_bullet=True)
                if x is not None:
                    text_xs.append(x)
                for span in line.get("spans", []):
                    chars = "".join(char.get("c", "") for char in span.get("chars", []))
                    if chars.strip() and chars.strip() != "·":
                        sizes.append(float(span.get("size", 0)))
        if not text_xs:
            failures.append(("BULLET_TEXT_MISSING", "Bullet marker has no measurable text"))
            continue
        first_x = text_xs[0]
        for continuation_x in text_xs[1:]:
            if abs(continuation_x - first_x) > align_tolerance:
                failures.append(("BULLET_CONTINUATION_INDENT", f"Wrapped line starts at {continuation_x:.2f} pt; first line starts at {first_x:.2f} pt"))
        if bullet_xs and not all(x < first_x for x in bullet_xs):
            failures.append(("BULLET_MARKER_POSITION", "Bullet marker is not left of its text"))
        if sizes and abs(statistics.median(sizes) - body_size) > font_tolerance:
            failures.append(("BULLET_FONT_SIZE", f"Bullet text is {statistics.median(sizes):.2f} pt; expected {body_size:.2f} pt"))
    if measured == 0:
        failures.append(("BULLET_GEOMETRY_MISSING", "No measurable middle-dot bullet blocks found"))
    return failures


def _check_heading(failures, document, heading: str, expected_left: float, size: float, shared: dict[str, Any]) -> None:
    _, block = _find_block_across_pages(document, heading, exact=True)
    if block is None:
        if _spacing_drift_present(document, heading):
            failures.append(("SECTION_TEXT_LAYER_SPACING", f"{heading!r} extracts with spaces between glyphs"))
        else:
            failures.append(("SECTION_HEADING_MISSING", f"Rendered document omits {heading!r}"))
        return
    x0 = float(block["bbox"][0])
    if abs(x0 - expected_left) > float(shared["geometry_tolerance_pt"]):
        failures.append(("SECTION_LEFT_EDGE", f"{heading!r} starts at {x0:.2f} pt; expected {expected_left:.2f} pt"))
    _check_size(failures, f"heading {heading}", _span_sizes(block), size, float(shared["font_tolerance_pt"]))


def check_cv_pdf(pdf_path: Path, payload: dict[str, Any]) -> list[tuple[str, str]]:
    contract = load_json(CONTRACT_PATH)
    shared, cv = contract["shared"], contract["cv"]
    failures: list[tuple[str, str]] = []
    document = _open_pdf(pdf_path)
    if not document:
        return [("VISUAL_EMPTY_PDF", "CV PDF has no pages")]
    if len(document) < int(cv["minimum_pages"]) or len(document) > int(cv["maximum_pages"]):
        failures.append(("VISUAL_PAGE_COUNT", f"CV has {len(document)} pages; required range is 1-2"))

    _check_fonts(failures, document, shared["allowed_pdf_font_fragments"])
    _check_link_schemes(failures, document)
    _check_ctas(failures, document, payload, shared)

    text = normalise(" ".join(page.get_text() for page in document))
    for heading in cv["forbidden_headings"]:
        if heading in text:
            failures.append(("PROJECT_HEADING_FORBIDDEN", f"Rendered CV contains {heading!r}"))
    headings = ["Professional Summary", "Skills", "Experience", "Education"]
    if payload.get("projects"):
        headings.append("Projects")
    expected_left = mm_to_pt(float(cv["page_margin_mm"][1]))
    for heading in headings:
        _check_heading(failures, document, heading, expected_left, float(cv["heading_size_pt"]), shared)

    page = document[0]
    name = str(payload.get("identity", {}).get("name", ""))
    name_sizes = _matching_span_sizes(page, name)
    if name_sizes:
        _check_size(failures, "candidate name", name_sizes, float(shared["name_size_pt"]), float(shared["font_tolerance_pt"]))
    else:
        failures.append(("NAME_MISSING", "Candidate name is not visible"))

    bullet_pages = [page for page in document if "·" in page.get_text()]
    if not bullet_pages:
        failures.append(("BULLET_GEOMETRY_MISSING", "No middle-dot bullets found in rendered CV"))
    else:
        for bullet_page in bullet_pages:
            failures.extend(_check_bullets(bullet_page, contract))
    return failures


def check_cover_letter_pdf(pdf_path: Path, payload: dict[str, Any]) -> list[tuple[str, str]]:
    contract = load_json(CONTRACT_PATH)
    shared, cl = contract["shared"], contract["cover_letter"]
    failures: list[tuple[str, str]] = []
    document = _open_pdf(pdf_path)
    if not document:
        return [("VISUAL_EMPTY_PDF", "Cover-letter PDF has no pages")]
    if len(document) != int(cl["required_pages"]):
        failures.append(("VISUAL_PAGE_COUNT", f"Cover letter has {len(document)} pages; required exactly 1"))

    _check_fonts(failures, document, shared["allowed_pdf_font_fragments"])
    _check_link_schemes(failures, document)
    _check_ctas(failures, document, payload, shared)
    page = document[0]
    left = mm_to_pt(float(cl["page_margin_mm"][1]))
    right = float(page.rect.width) - left
    tolerance = float(shared["geometry_tolerance_pt"])
    targets = [("role title", str(payload.get("role_title", ""))), ("company/date row", str(payload.get("company", ""))), ("greeting", str(payload.get("greeting", "")))]
    if payload.get("paragraphs"):
        targets.append(("first body paragraph", str(payload["paragraphs"][0])))
    found: dict[str, dict[str, Any]] = {}
    for label, value in targets:
        block = _find_block_prefix(page, value) if label == "first body paragraph" else _find_block(page, value)
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
    name_sizes = _matching_span_sizes(page, name)
    if name_sizes:
        # Header uses uppercase Cormorant at 23pt; the sign-off repeats the name at a smaller size.
        header_sizes = [size for size in name_sizes if abs(size - float(shared["name_size_pt"])) <= float(shared["font_tolerance_pt"])]
        _check_size(failures, "cover-letter candidate name", header_sizes or name_sizes, float(shared["name_size_pt"]), float(shared["font_tolerance_pt"]))
    else:
        failures.append(("NAME_MISSING", "Candidate name is not visible"))
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
