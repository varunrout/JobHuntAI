#!/usr/bin/env python3
"""Render JobHuntAI CVs and cover letters from the canonical HTML templates.

PDF is the authoritative visual artefact. Rendering stops and removes outputs
when the hard visual contract fails.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from weasyprint import HTML

from visual_gate import check_cover_letter_pdf, check_cv_pdf, check_template_contract

ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = ROOT / "templates"
TEMPLATES = {
    "cv": "cv_template.html",
    "cl": "cover_letter_template.html",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render(kind: str, payload_path: Path, html_out: Path, pdf_out: Path) -> list[tuple[str, str]]:
    payload = load_json(payload_path)
    failures = check_template_contract()
    if failures:
        return failures

    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=("html", "xml"), default_for_string=True),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = environment.get_template(TEMPLATES[kind])
    rendered = template.render(**payload)

    html_out.parent.mkdir(parents=True, exist_ok=True)
    pdf_out.parent.mkdir(parents=True, exist_ok=True)
    html_out.write_text(rendered, encoding="utf-8")
    HTML(string=rendered, base_url=str(TEMPLATE_DIR)).write_pdf(str(pdf_out))

    if kind == "cv":
        failures.extend(check_cv_pdf(pdf_out, payload))
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

    failures = render(
        args.kind,
        Path(args.payload),
        Path(args.html_out),
        Path(args.pdf_out),
    )
    if failures:
        print(f"RENDER BLOCKED - {len(failures)} failure(s):")
        for code, detail in failures:
            print(f"[{code}] {detail}")
        return 2
    print(f"RENDER CLEAN: {args.pdf_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
