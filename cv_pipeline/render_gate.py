#!/usr/bin/env python3
"""Artefact-level page, first-page and locked-template checks for generated CV PDFs."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from visual_gate import check_contract as check_visual_contract


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def occurrences(text: str, markers: list[str]) -> int:
    low = normalise(text)
    return sum(1 for marker in markers if normalise(marker) in low)


def check(pdf_path: Path, cv_path: Path, diagnostic_path: Path) -> list[tuple[str, str]]:
    visual_failures = check_visual_contract()
    if visual_failures:
        return visual_failures

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        return [("DEPENDENCY", f"pypdf is required: {exc}")]

    cv = json.loads(cv_path.read_text(encoding="utf-8"))
    diagnostic = json.loads(diagnostic_path.read_text(encoding="utf-8"))
    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    failures: list[tuple[str, str]] = []

    exception = bool(cv.get("page_limit_exception"))
    if len(pages) > 2 and not exception:
        failures.append(("PAGE_OVERFLOW", f"rendered CV has {len(pages)} pages"))

    first = pages[0] if pages else ""
    markers = diagnostic.get("first_page_evidence_markers", {})
    if occurrences(first, [markers.get("target_identity", "")]) < 1:
        failures.append(("FIRST_PAGE_IDENTITY", "target identity is not established on page one"))
    if occurrences(first, markers.get("technical_stack", [])) < 2:
        failures.append(("FIRST_PAGE_STACK", "fewer than two technical-stack markers appear on page one"))
    for key, code in (("strongest_achievement", "FIRST_PAGE_ACHIEVEMENT"), ("operating_context", "FIRST_PAGE_CONTEXT"), ("consequence", "FIRST_PAGE_CONSEQUENCE")):
        value = markers.get(key, "")
        if value and occurrences(first, [value]) < 1:
            failures.append((code, f"{key.replace('_', ' ')} is not visible on page one"))

    total_chars = sum(len(normalise(page)) for page in pages) or 1
    if pages:
        last_share = len(normalise(pages[-1])) / total_chars
        if len(pages) > 1 and last_share < 0.20:
            failures.append(("FINAL_PAGE_UNDERFILLED", f"final page carries only {last_share:.0%} of extracted text"))

    result = diagnostic.setdefault("results", {})
    result["final_page_count"] = len(pages)
    result["first_page_sufficiency"] = "fail" if any(code.startswith("FIRST_PAGE") for code, _ in failures) else "pass"
    result["layout_quality"] = "fail" if failures else "pass"
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
    print("CV RENDER GATES CLEAN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
