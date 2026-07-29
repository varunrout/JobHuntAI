#!/usr/bin/env python3
"""Visual contract for archetype-aware CVs."""
from __future__ import annotations

import json
import re
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
    if f'data-visual-contract="{version}"' not in html:
        failures.append(("ARCHETYPE_VISUAL_VERSION_MISSING", f"template omits {version}"))
    if re.search(r"<table\b", html, re.I):
        failures.append(("VISUAL_TABLE_FORBIDDEN", "archetype template contains a table"))
    for token in ("LinkedIn", "Portfolio", "GitHub"):
        if token not in html:
            failures.append(("CONTACT_LINK_MISSING", f"archetype template omits {token}"))
    if "{% for section in section_order %}" not in html:
        failures.append(("DYNAMIC_SECTION_ORDER_MISSING", "template does not iterate through section_order"))
    for section in contract["cv"]["section_ids"]:
        if f'data-section=\"{section}\"' not in html:
            failures.append(("SECTION_HOOK_MISSING", f"template omits data-section={section!r}"))
    if "Selected Projects" in html:
        failures.append(("PROJECT_HEADING_FORBIDDEN", "template contains Selected Projects"))
    if '{{ s["items"] }}' not in html:
        failures.append(("SKILLS_BINDING_DRIFT", "skills must use explicit dictionary-key binding"))

    root = legacy.css_rule(html, ":root")
    cv = contract["cv"]
    shared = contract["shared"]
    for key, value in (
        ("--ink", shared["ink"]),
        ("--link", shared["link"]),
        ("--rule", shared["rule"]),
        ("--body-size", f'{cv["body_size_pt"]}pt'),
        ("--body-line-height", str(cv["body_line_height"])),
        ("--bullet-text-indent", f'{cv["bullet_text_indent_mm"]}mm'),
        ("--bullet-marker-offset", f'{cv["bullet_marker_offset_mm"]}mm'),
    ):
        legacy.require(failures, root, ":root", key, value)
    legacy.require(
        failures,
        legacy.css_rule(html, "@page"),
        "@page",
        "margin",
        " ".join(f"{legacy.fmt(value)}mm" for value in cv["page_margin_mm"]),
    )
    bullet = legacy.css_rule(html, ".evidence-list li")
    for key, value in (
        ("position", "relative"),
        ("padding-left", "var(--bullet-text-indent)"),
        ("text-indent", "0"),
        ("font-size", "var(--body-size)"),
        ("line-height", "var(--body-line-height)"),
    ):
        legacy.require(failures, bullet, ".evidence-list li", key, value)
    return failures


def _find_block_across_pages(document, needle: str):
    for page in document:
        block = legacy._find_block(page, needle, exact=True)
        if block is not None:
            return page, block
    return None, None


def check_archetype_cv_pdf(pdf_path: Path, payload: dict[str, Any]) -> list[tuple[str, str]]:
    contract = load_json(CONTRACT_PATH)
    failures = check_archetype_template_contract()
    document = legacy._open_pdf(pdf_path)
    if not document:
        return failures + [("VISUAL_EMPTY_PDF", "CV PDF has no pages")]
    maximum = int(payload.get("page_strategy", {}).get("maximum_pages", contract["cv"]["maximum_pages_without_exception"]))
    if payload.get("page_limit_exception"):
        maximum = max(maximum, 3)
    if len(document) > maximum:
        failures.append(("VISUAL_PAGE_COUNT", f"CV has {len(document)} pages; maximum is {maximum}"))

    legacy._check_fonts(failures, document, contract["shared"]["allowed_pdf_font_fragments"])
    labels = payload.get("section_labels", {})
    order = payload.get("section_order", [])
    allowed = contract["cv"]["allowed_section_labels"]
    expected_left = legacy.mm_to_pt(float(contract["cv"]["page_margin_mm"][1]))
    tolerance = float(contract["shared"]["geometry_tolerance_pt"])
    for section in order:
        if section == "impact" and not payload.get("selected_impact"):
            continue
        if section == "projects" and not payload.get("projects"):
            continue
        label = labels.get(section, "")
        if label not in allowed.get(section, []):
            failures.append(("SECTION_LABEL_UNCONTROLLED", f"{section} label {label!r} is not approved"))
            continue
        page, block = _find_block_across_pages(document, label)
        if block is None:
            failures.append(("SECTION_HEADING_MISSING", f"rendered CV omits {label!r}"))
            continue
        x0 = float(block["bbox"][0])
        if abs(x0 - expected_left) > tolerance:
            failures.append(("SECTION_LEFT_EDGE", f"{label!r} starts at {x0:.2f} pt; expected {expected_left:.2f} pt"))
        legacy._check_size(
            failures,
            f"heading {label}",
            legacy._span_sizes(block),
            float(contract["cv"]["heading_size_pt"]),
            float(contract["shared"]["font_tolerance_pt"]),
        )

    first_page = document[0]
    name = str(payload.get("identity", {}).get("name", ""))
    name_block = legacy._find_block(first_page, name)
    if name_block:
        legacy._check_size(failures, "candidate name", legacy._span_sizes(name_block), float(contract["shared"]["name_size_pt"]), float(contract["shared"]["font_tolerance_pt"]))
    else:
        failures.append(("NAME_MISSING", "candidate name is not visible on page one"))
    for page in document:
        if "•" in page.get_text():
            failures.extend(legacy._check_bullets(page, contract))
    if not any(contract["shared"]["portfolio_uri_contains"] in uri for uri in legacy._links(document)):
        failures.append(("PORTFOLIO_LINK_MISSING", "rendered CV has no clickable portfolio link"))
    text = legacy.normalise(" ".join(page.get_text() for page in document))
    for heading in contract["cv"]["forbidden_headings"]:
        if heading in text:
            failures.append(("PROJECT_HEADING_FORBIDDEN", f"rendered CV contains {heading!r}"))
    return failures
