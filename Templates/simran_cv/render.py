#!/usr/bin/env python3
"""Render a neutral Simran-style CV fixture to HTML and PDF."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jinja2 import Environment, StrictUndefined, select_autoescape
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "simran_cv_template.html"


def environment() -> Environment:
    return Environment(
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=("html", "xml"), default_for_string=True),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render(payload_path: Path, output_dir: Path) -> tuple[Path, Path]:
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    template = environment().from_string(TEMPLATE.read_text(encoding="utf-8"))
    html_text = template.render(**payload)

    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "cv.html"
    pdf_path = output_dir / "cv.pdf"
    html_path.write_text(html_text, encoding="utf-8")
    HTML(string=html_text, base_url=str(ROOT)).write_pdf(str(pdf_path))
    return html_path, pdf_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if not args.fixture.exists():
        parser.error(f"fixture does not exist: {args.fixture}")
    if not TEMPLATE.exists():
        parser.error(f"template does not exist: {TEMPLATE}")

    html_path, pdf_path = render(args.fixture, args.output_dir)
    print(f"HTML: {html_path}")
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
