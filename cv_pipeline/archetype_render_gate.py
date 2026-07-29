#!/usr/bin/env python3
"""Rendered-PDF sufficiency and page checks for archetype-aware CVs."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from archetype_visual_gate import check_archetype_cv_pdf


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def occurs(text: str, marker: str) -> bool:
    return bool(marker and normalise(marker) in normalise(text))


def check(pdf_path: Path, cv_path: Path, diagnostic_path: Path) -> list[tuple[str, str]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        return [("DEPENDENCY", f"pypdf is required: {exc}")]
    cv = json.loads(cv_path.read_text(encoding="utf-8"))
    diagnostic = json.loads(diagnostic_path.read_text(encoding="utf-8"))
    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    failures = check_archetype_cv_pdf(pdf_path, cv)
    maximum = int(cv.get("page_strategy", {}).get("maximum_pages", 2))
    if len(pages) > maximum and not cv.get("page_limit_exception"):
        failures.append(("PAGE_OVERFLOW", f"rendered CV has {len(pages)} pages; maximum is {maximum}"))
    first = pages[0] if pages else ""
    markers = diagnostic.get("first_page_evidence_markers", {})
    if not occurs(first, markers.get("professional_identity", "")):
        failures.append(("FIRST_PAGE_IDENTITY", "professional identity is not established on page one"))
    proof_count = sum(1 for marker in markers.get("proof_markers", []) if occurs(first, marker))
    if proof_count < 2:
        failures.append(("FIRST_PAGE_PROOF", "fewer than two signature proof markers appear on page one"))
    for key, code in (("operating_context", "FIRST_PAGE_CONTEXT"), ("consequence", "FIRST_PAGE_CONSEQUENCE")):
        if not occurs(first, markers.get(key, "")):
            failures.append((code, f"{key.replace('_', ' ')} is not visible on page one"))
    total_chars = sum(len(normalise(page)) for page in pages) or 1
    if len(pages) > 1:
        final_share = len(normalise(pages[-1])) / total_chars
        if final_share < 0.20:
            failures.append(("FINAL_PAGE_UNDERFILLED", f"final page carries only {final_share:.0%} of extracted text"))
    results = diagnostic.setdefault("results", {})
    results["final_page_count"] = len(pages)
    results["first_page_sufficiency"] = "fail" if any(code.startswith("FIRST_PAGE") for code, _ in failures) else "pass"
    results["layout_quality"] = "fail" if failures else "pass"
    results["visual_contract"] = "fail" if any(code.startswith(("VISUAL", "SECTION", "BULLET", "PORTFOLIO", "PROJECT")) for code, _ in failures) else "pass"
    diagnostic_path.write_text(json.dumps(diagnostic, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("cv")
    parser.add_argument("diagnostic")
    args = parser.parse_args()
    failures = check(Path(args.pdf), Path(args.cv), Path(args.diagnostic))
    if failures:
        for code, detail in failures:
            print(f"[{code}] {detail}")
        return 2
    print("ARCHETYPE CV RENDER AND VISUAL GATES CLEAN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
