#!/usr/bin/env python3
"""Render both neutral fixtures and enforce the first visual regression gates."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import fitz
from jinja2 import Environment, StrictUndefined, select_autoescape
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "simran_cv_template.html"
FIXTURES = {
    "one_page": (ROOT / "fixtures" / "one_page.json", 1),
    "two_page": (ROOT / "fixtures" / "two_page.json", 2),
}


def render(fixture: Path, target: Path) -> None:
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    env = Environment(
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=("html", "xml"), default_for_string=True),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    html = env.from_string(TEMPLATE.read_text(encoding="utf-8")).render(**payload)
    HTML(string=html, base_url=str(ROOT)).write_pdf(str(target))


def page_fill(page: fitz.Page) -> float:
    blocks = [block for block in page.get_text("blocks") if block[4].strip()]
    return max((block[3] for block in blocks), default=0.0) / page.rect.height


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir)
        for name, (fixture, expected_pages) in FIXTURES.items():
            pdf = output / f"{name}.pdf"
            render(fixture, pdf)
            with fitz.open(pdf) as document:
                text = "\n".join(page.get_text() for page in document)
                fills = [page_fill(page) for page in document]
                if len(document) != expected_pages:
                    failures.append(f"{name}: expected {expected_pages} page(s), got {len(document)}")
                if "<built-in method" in text or "of dict object" in text:
                    failures.append(f"{name}: dictionary method leaked into rendered text")
                if "Professional Summary" not in text or "Skills" not in text or "Experience" not in text:
                    failures.append(f"{name}: a primary section is missing")
                if name == "one_page" and fills[0] < 0.70:
                    failures.append(f"{name}: fixture is too sparse ({fills[0]:.0%} vertical fill)")
                if name == "two_page" and fills[-1] < 0.40:
                    failures.append(f"{name}: final page is too sparse ({fills[-1]:.0%} vertical fill)")
                print(f"{name}: pages={len(document)}, fill={[round(value, 3) for value in fills]}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 2
    print("SIMRAN TEMPLATE RENDER QA CLEAN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
