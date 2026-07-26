#!/usr/bin/env python3
"""Hard visual contract for JobHuntAI CV and cover-letter HTML templates.

The approved HTML templates are the only visual source of truth. This gate is
deliberately strict: any template, shared-style, section-label, alignment or
bullet-layout change must update the versioned visual contract explicitly.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CONTRACT_PATH = ROOT / "visual_contract.json"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_template(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


def _contact_order_failures(name: str, text: str, expected: list[str]) -> list[tuple[str, str]]:
    placeholders = {
        "phone": "identity.phone",
        "email": "identity.email",
        "linkedin": "identity.linkedin",
        "portfolio": "identity.portfolio",
        "github": "identity.github",
        "location": "identity.location",
    }
    positions: list[tuple[str, int]] = []
    failures: list[tuple[str, str]] = []
    for field in expected:
        marker = placeholders[field]
        index = text.find(marker)
        if index < 0:
            failures.append(("VISUAL_CONTACT_FIELD", f"{name} is missing {field}"))
        positions.append((field, index))
    if not failures:
        actual = [field for field, _ in sorted(positions, key=lambda item: item[1])]
        if actual != expected:
            failures.append((
                "VISUAL_CONTACT_ORDER",
                f"{name} contact order is {actual}; required {expected}",
            ))
    return failures


def check_texts(
    contract: dict[str, Any],
    shared_css: str,
    cv_html: str,
    cover_letter_html: str,
    *,
    enforce_hashes: bool = True,
) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []

    if contract.get("renderer") != "html":
        failures.append(("VISUAL_RENDERER", "visual source of truth must be html"))

    templates = contract["authoritative_templates"]
    contents = {
        "shared_css": shared_css,
        "cv": cv_html,
        "cover_letter": cover_letter_html,
    }
    if enforce_hashes:
        for key, text in contents.items():
            expected = templates[key]["sha256"]
            actual = sha256_text(text)
            if actual != expected:
                failures.append((
                    "VISUAL_HASH_MISMATCH",
                    f"{key} changed: expected {expected}, got {actual}",
                ))

    for name, html in (("cv", cv_html), ("cover_letter", cover_letter_html)):
        if not html.lstrip().startswith("<!DOCTYPE html>"):
            failures.append(("VISUAL_HTML_ONLY", f"{name} must be an HTML document"))
        if "<table" in html.lower():
            failures.append(("VISUAL_TABLE_FORBIDDEN", f"{name} must not use tables for layout"))
        if re.search(r"\sstyle\s*=", html, flags=re.I):
            failures.append(("VISUAL_INLINE_STYLE", f"{name} must not use inline style overrides"))
        failures.extend(_contact_order_failures(name, html, contract["contact_order"]))

    cv_spec = contract["cv"]
    for heading in cv_spec["required_headings"]:
        if f"<h2>{heading}</h2>" not in cv_html:
            failures.append(("VISUAL_CV_HEADING", f"CV is missing exact heading {heading!r}"))
    for forbidden in cv_spec["forbidden_text"]:
        if forbidden in cv_html:
            failures.append(("VISUAL_CV_FORBIDDEN", f"CV contains forbidden text {forbidden!r}"))
    for fragment in cv_spec["required_fragments"]:
        if fragment not in cv_html:
            failures.append(("VISUAL_CV_FRAGMENT", f"CV is missing locked fragment {fragment!r}"))

    unclassed_lists = re.findall(r"<ul(?!\s+class=\"evidence-list\")", cv_html)
    if unclassed_lists:
        failures.append((
            "VISUAL_BULLET_CLASS",
            "every CV evidence list must use class=\"evidence-list\"",
        ))
    if cv_html.count("<ul class=\"evidence-list\">") < 3:
        failures.append((
            "VISUAL_BULLET_CLASS",
            "experience and both project placements must use the shared evidence-list class",
        ))
    if cv_html.count("<h2>Projects</h2>") != 2:
        failures.append((
            "VISUAL_PROJECT_HEADING",
            "the template must contain exactly two conditional Projects headings",
        ))

    cl_spec = contract["cover_letter"]
    for forbidden in cl_spec["forbidden_text"]:
        if forbidden.lower() in cover_letter_html.lower():
            failures.append(("VISUAL_CL_FORBIDDEN", f"cover letter contains forbidden text {forbidden!r}"))
    for fragment in cl_spec["required_fragments"]:
        if fragment not in cover_letter_html:
            failures.append(("VISUAL_CL_FRAGMENT", f"cover letter is missing locked fragment {fragment!r}"))

    shared_required = (
        '--font:"Times New Roman","Liberation Serif",serif;',
        "--name-size:17pt;",
        "--contact-size:8.35pt;",
        "white-space:nowrap;",
        'content:" | ";',
    )
    for fragment in shared_required:
        if fragment not in shared_css:
            failures.append(("VISUAL_SHARED_FRAGMENT", f"shared CSS is missing {fragment!r}"))

    return failures


def check_contract(root: Path = ROOT, contract_path: Path = CONTRACT_PATH) -> list[tuple[str, str]]:
    contract = load_contract(contract_path)
    templates = contract["authoritative_templates"]
    shared_css = _read_template(root, templates["shared_css"]["path"])
    cv_html = _read_template(root, templates["cv"]["path"])
    cover_letter_html = _read_template(root, templates["cover_letter"]["path"])
    return check_texts(contract, shared_css, cv_html, cover_letter_html)


def main() -> int:
    failures = check_contract()
    if failures:
        print(f"VISUAL CONTRACT BLOCKED - {len(failures)} failure(s):")
        for code, detail in failures:
            print(f"[{code}] {detail}")
        return 2
    contract = load_contract()
    print(f"VISUAL CONTRACT CLEAN (v{contract['version']}, HTML source locked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
