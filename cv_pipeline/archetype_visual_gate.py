#!/usr/bin/env python3
"""Visual contract for archetype-aware CVs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import visual_gate as legacy

ROOT = Path(__file__).resolve().parent
CONTRACT_PATH = ROOT / "archetype_visual_contract.json"
TEMPLATE_PATH = ROOT / "templates" / "cv_archetype_template.html"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check_archetype_template_contract(html: str | None = None) -> list[tuple[str, str]]:
    contract = load_json(CONTRACT_PATH)
    html = TEMPLATE_PATH.read_text(encoding="utf-8") if html is None else html
    failures: list[tuple[str, str]] = []
    version = contract["version"]
    cv, shared = contract["cv"], contract["shared"]

    failures.extend(legacy._check_shared_template_markup("archetype CV", html, version))
    failures.extend(legacy._check_shared_css(html, version, shared, float(cv["body_size_pt"]), float(cv["body_line_height"])))
    if "{% for section in section_order %}" not in html:
        failures.append(("DYNAMIC_SECTION_ORDER_MISSING", "template does not iterate through section_order"))
    for section in cv["section_ids"]:
        if f'data-section=\"{section}\"' not in html:
            failures.append(("SECTION_HOOK_MISSING", f"template omits data-section={section!r}"))
    if "Selected Projects" in html:
        failures.append(("PROJECT_HEADING_FORBIDDEN", "template contains Selected Projects"))
    if '{{ s["items"] }}' not in html:
        failures.append(("SKILLS_BINDING_DRIFT", "skills must use explicit dictionary-key binding"))

    root = legacy.css_rule(html, ":root")
    for key, value in (
        ("--bullet-text-indent", f'{cv["bullet_text_indent_mm"]}mm'),
        ("--bullet-marker-offset", f'{cv["bullet_marker_offset_mm"]}mm'),
    ):
        legacy.require(failures, root, ":root", key, value)
    legacy.require(failures, legacy.css_rule(html, "@page"), "@page", "margin", "10mm")
    h2 = legacy.css_rule(html, "h2")
    for key, value in (
        ("font-size", f'{cv["heading_size_pt"]}pt'),
        ("font-weight", "600"),
        ("letter-spacing", ".03em"),
        ("text-transform", "uppercase"),
        ("color", "var(--ink)"),
        ("border-bottom", "1px solid var(--divider)"),
        ("padding-bottom", "3px"),
    ):
        legacy.require(failures, h2, "h2", key, value)
    bullet = legacy.css_rule(html, ".evidence-list li")
    for key, value in (
        ("position", "relative"),
        ("padding-left", "var(--bullet-text-indent)"),
        ("text-indent", "0"),
        ("font-size", "var(--body-size)"),
        ("line-height", "var(--body-line-height)"),
    ):
        legacy.require(failures, bullet, ".evidence-list li", key, value)
    legacy.require(failures, legacy.css_rule(html, ".evidence-list li::before"), ".evidence-list li::before", "content", '"·"')
    legacy.require(failures, legacy.css_rule(html, ".bullet-marker"), ".bullet-marker", "color", "var(--ink)")
    if "border-left:1px solid var(--ink);" not in html:
        failures.append(("VISUAL_CSS_DRIFT", ".impact-item must use a black border-left"))
    return failures


def _find_block_across_pages(document, needle: str):
    return legacy._find_block_across_pages(document, needle, exact=True)


def check_archetype_cv_pdf(pdf_path: Path, payload: dict[str, Any]) -> list[tuple[str, str]]:
    contract = load_json(CONTRACT_PATH)
    failures = check_archetype_template_contract()
    document = legacy._open_pdf(pdf_path)
    if not document:
        return failures + [("VISUAL_EMPTY_PDF", "CV PDF has no pages")]
    minimum = int(contract["cv"]["minimum_pages"])
    maximum = int(contract["cv"]["maximum_pages"])
    if len(document) < minimum or len(document) > maximum:
        failures.append(("VISUAL_PAGE_COUNT", f"CV has {len(document)} pages; required range is 1-2"))

    shared, cv = contract["shared"], contract["cv"]
    legacy._check_fonts(failures, document, shared["allowed_pdf_font_fragments"])
    legacy._check_link_schemes(failures, document)
    legacy._check_ctas(failures, document, payload, shared)

    labels = payload.get("section_labels", {})
    order = payload.get("section_order", [])
    allowed = cv["allowed_section_labels"]
    expected_left = legacy.mm_to_pt(float(cv["page_margin_mm"][1]))
    tolerance = float(shared["geometry_tolerance_pt"])
    for section in order:
        if section == "impact" and not payload.get("selected_impact"):
            continue
        if section == "projects" and not payload.get("projects"):
            continue
        label = labels.get(section, "")
        if label not in allowed.get(section, []):
            failures.append(("SECTION_LABEL_UNCONTROLLED", f"{section} label {label!r} is not approved"))
            continue
        _, block = _find_block_across_pages(document, label)
        if block is None:
            if legacy._spacing_drift_present(document, label):
                failures.append(("SECTION_TEXT_LAYER_SPACING", f"{label!r} extracts with spaces between glyphs"))
            else:
                failures.append(("SECTION_HEADING_MISSING", f"rendered CV omits {label!r}"))
            continue
        x0 = float(block["bbox"][0])
        if abs(x0 - expected_left) > tolerance:
            failures.append(("SECTION_LEFT_EDGE", f"{label!r} starts at {x0:.2f} pt; expected {expected_left:.2f} pt"))
        legacy._check_size(failures, f"heading {label}", legacy._span_sizes(block), float(cv["heading_size_pt"]), float(shared["font_tolerance_pt"]))

    first_page = document[0]
    name = str(payload.get("identity", {}).get("name", ""))
    name_sizes = legacy._matching_span_sizes(first_page, name)
    if name_sizes:
        legacy._check_size(failures, "candidate name", name_sizes, float(shared["name_size_pt"]), float(shared["font_tolerance_pt"]))
    else:
        failures.append(("NAME_MISSING", "candidate name is not visible on page one"))

    bullet_pages = [page for page in document if any(line.lstrip().startswith("·") for line in page.get_text().splitlines())]
    if not bullet_pages:
        failures.append(("BULLET_GEOMETRY_MISSING", "No middle-dot bullets found in rendered CV"))
    else:
        for page in bullet_pages:
            failures.extend(legacy._check_bullets(page, {"shared": shared, "cv": cv}))

    text = legacy.normalise(" ".join(page.get_text() for page in document))
    for heading in cv["forbidden_headings"]:
        if heading in text:
            failures.append(("PROJECT_HEADING_FORBIDDEN", f"rendered CV contains {heading!r}"))
    return failures
