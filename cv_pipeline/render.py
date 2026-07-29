#!/usr/bin/env python3
"""Render JobHuntAI CVs and cover letters from canonical HTML templates.

Legacy CV payloads continue through the locked classic-gold contract. Archetype
payloads opt into the separate jobhuntai-archetype-v1 contract.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from weasyprint import HTML

from archetype_visual_gate import check_archetype_cv_pdf, check_archetype_template_contract
from visual_gate import check_cover_letter_pdf, check_cv_pdf, check_template_contract

ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = ROOT / "templates"
TEMPLATES = {"cv": "cv_template.html", "cl": "cover_letter_template.html"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_archetype_cv(kind: str, payload: dict[str, Any]) -> bool:
    return kind == "cv" and payload.get("layout_contract") == "jobhuntai-archetype-v1"


def render(kind: str, payload_path: Path, html_out: Path, pdf_out: Path) -> list[tuple[str, str]]:
    payload = load_json(payload_path)
    archetype_cv = is_archetype_cv(kind, payload)
    failures = check_archetype_template_contract() if archetype_cv else check_template_contract()
    if failures:
        return failures

    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=("html", "xml"), default_for_string=True),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template_name = "cv_archetype_template.html" if archetype_cv else TEMPLATES[kind]
    rendered = environment.get_template(template_name).render(**payload)

    html_out.parent.mkdir(parents=True, exist_ok=True)
    pdf_out.parent.mkdir(parents=True, exist_ok=True)
    html_out.write_text(rendered, encoding="utf-8")
    HTML(string=rendered, base_url=str(TEMPLATE_DIR)).write_pdf(str(pdf_out))

    if kind == "cv":
        failures.extend(check_archetype_cv_pdf(pdf_out, payload) if archetype_cv else check_cv_pdf(pdf_out, payload))
    else:
        failures.extend(check_cover_letter_pdf(pdf_out, payload))
    if failures:
        html_out.unlink(missing_ok=True)
        pdf_out.unlink(missing_ok=True)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a JobHuntAI application artefact")
    parser.add_argument("kind", choices=("cv", "cl"))
    parser.add_argument("payload")
    parser.add_argument("--html-out", required=True)
    parser.add_argument("--pdf-out", required=True)
    args = parser.parse_args()
    failures = render(args.kind, Path(args.payload), Path(args.html_out), Path(args.pdf_out))
    if failures:
        print(f"RENDER BLOCKED - {len(failures)} failure(s):")
        for code, detail in failures:
            print(f"[{code}] {detail}")
        return 2
    print(f"RENDER CLEAN: {args.pdf_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
