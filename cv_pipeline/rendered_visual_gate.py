#!/usr/bin/env python3
"""Fail-closed rendered-page review gate for final CV release artefacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "schemas" / "rendered_visual_review.schema.json"
CONTRACT = "jobhuntai-rendered-visual-review-v1"
MIN_BODY_FONT_PT = 9.5
MIN_ONE_PAGE_FILL = 0.72
MIN_FIRST_PAGE_FILL = 0.82
MIN_FINAL_PAGE_FILL = 0.70
MAX_INTERIOR_GAP = 0.18
METRIC_TOLERANCE = 0.025
FONT_TOLERANCE = 0.30
FORBIDDEN_CONTINUATION = re.compile(
    r"\b(?:professional\s+summary|skills|technical\s+skills|experience|projects|education)\s*(?:continued|cont\.?)\b",
    re.I,
)
FORBIDDEN_HEADING_TEXT = {"additional project evidence", "additional projects"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def schema_errors(instance: dict[str, Any]) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["jsonschema is required to validate rendered visual reviews"]
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    out: list[str] = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "root"
        out.append(f"{location}: {error.message}")
    return out


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _open_pdf(path: Path):
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(f"PyMuPDF is required: {exc}") from exc
    return fitz.open(str(path))


def page_png_bytes(page) -> bytes:
    import fitz

    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    return pix.tobytes("png")


def _weighted_median(values: list[tuple[float, int]]) -> float:
    if not values:
        return 0.0
    values = sorted(values, key=lambda item: item[0])
    total = sum(weight for _, weight in values)
    cursor = 0
    for value, weight in values:
        cursor += weight
        if cursor >= total / 2:
            return float(value)
    return float(values[-1][0])


def _merge_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not intervals:
        return []
    merged: list[tuple[float, float]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1] + 1.0:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def analyse_page(page) -> dict[str, float]:
    height = float(page.rect.height)
    content_top = max(24.0, height * 0.035)
    content_bottom = min(height - 24.0, height * 0.965)
    content_height = max(1.0, content_bottom - content_top)
    intervals: list[tuple[float, float]] = []
    font_values: list[tuple[float, int]] = []

    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text = "".join(span.get("text", "") for span in line.get("spans", []))
            if not text.strip():
                continue
            y0, y1 = float(line["bbox"][1]), float(line["bbox"][3])
            y0 = max(content_top, y0)
            y1 = min(content_bottom, y1)
            if y1 > y0:
                intervals.append((y0, y1))
            for span in line.get("spans", []):
                span_text = normalise(str(span.get("text", "")))
                size = float(span.get("size", 0) or 0)
                if len(span_text) >= 3 and 7.0 <= size <= 12.5:
                    font_values.append((size, max(1, len(span_text))))

    merged = _merge_intervals(intervals)
    if not merged:
        return {
            "meaningful_fill": 0.0,
            "bottom_reach": 0.0,
            "largest_blank_gap": 1.0,
            "body_font_median_pt": 0.0,
        }

    bottom_reach = max(0.0, min(1.0, (merged[-1][1] - content_top) / content_height))
    gaps = [max(0.0, merged[index + 1][0] - merged[index][1]) for index in range(len(merged) - 1)]
    largest_gap = (max(gaps) / content_height) if gaps else 0.0
    meaningful_fill = bottom_reach
    return {
        "meaningful_fill": round(meaningful_fill, 4),
        "bottom_reach": round(bottom_reach, 4),
        "largest_blank_gap": round(largest_gap, 4),
        "body_font_median_pt": round(_weighted_median(font_values), 2),
    }


def analyse_pdf(pdf_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    document = _open_pdf(pdf_path)
    pages: list[dict[str, Any]] = []
    lines: list[str] = []
    for index, page in enumerate(document, start=1):
        png = page_png_bytes(page)
        metrics = analyse_page(page)
        pages.append({"page": index, "screenshot_sha256": sha256_bytes(png), **metrics})
        lines.extend(normalise(line) for line in page.get_text("text").splitlines() if normalise(line))
    return pages, lines


def _resolve(run_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else run_dir / path


def _scan_explicit_page_breaks(path: Path, source_format: str) -> list[str]:
    if source_format == "docx":
        try:
            with zipfile.ZipFile(path) as archive:
                xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
        except (OSError, KeyError, zipfile.BadZipFile) as exc:
            return [f"unable to inspect DOCX pagination: {exc}"]
        findings = []
        if re.search(r"<w:pageBreakBefore(?:\s*/>|>.*?</w:pageBreakBefore>)", xml, re.S):
            findings.append("DOCX contains w:pageBreakBefore")
        if re.search(r"<w:br\b[^>]*w:type=[\"']page[\"']", xml, re.I):
            findings.append("DOCX contains an explicit page break")
        return findings
    if source_format == "html":
        text = path.read_text(encoding="utf-8", errors="replace")
        findings = []
        if re.search(r"page-break-before\s*:\s*always", text, re.I):
            findings.append("HTML contains page-break-before: always")
        if re.search(r"break-before\s*:\s*page", text, re.I):
            findings.append("HTML contains break-before: page")
        return findings
    return []


def add_failure(failures: list[dict[str, str]], code: str, message: str) -> None:
    failures.append({"code": code, "message": message})


def validate(
    pdf_path: Path,
    review: dict[str, Any],
    run_dir: Path,
    expected_reviewer_actor: str | None = None,
) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for error in schema_errors(review):
        add_failure(failures, "RENDERED_VISUAL_SCHEMA", error)
    if review.get("contract") != CONTRACT:
        add_failure(failures, "RENDERED_VISUAL_CONTRACT_INVALID", f"contract must be {CONTRACT}")
    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        return [{"code": "RENDERED_PDF_MISSING", "message": f"PDF not found or empty: {pdf_path}"}]

    actual_pdf_hash = sha256_file(pdf_path)
    if review.get("pdf_sha256") != actual_pdf_hash:
        add_failure(failures, "RENDERED_PDF_HASH_MISMATCH", "visual review is not tied to the exact final PDF")

    try:
        actual_pages, extracted_lines = analyse_pdf(pdf_path)
    except Exception as exc:
        return [{"code": "RENDERED_PDF_INVALID", "message": str(exc)}]

    page_count = len(actual_pages)
    if page_count not in {1, 2}:
        add_failure(failures, "RENDERED_PAGE_COUNT_INVALID", f"final CV must have 1 or 2 pages, found {page_count}")
    if review.get("page_count") != page_count:
        add_failure(failures, "RENDERED_PAGE_COUNT_MISMATCH", "visual review page count differs from the final PDF")

    recorded_pages = review.get("pages")
    if not isinstance(recorded_pages, list) or len(recorded_pages) != page_count:
        add_failure(failures, "RENDERED_PAGE_REVIEW_INCOMPLETE", "every rendered page requires one review record")
        recorded_pages = []

    for actual, recorded in zip(actual_pages, recorded_pages):
        page_number = actual["page"]
        if not isinstance(recorded, dict) or recorded.get("page") != page_number:
            add_failure(failures, "RENDERED_PAGE_RECORD_INVALID", f"page {page_number} review record is invalid")
            continue
        screenshot_path_value = recorded.get("screenshot_path")
        if not isinstance(screenshot_path_value, str) or not screenshot_path_value.strip():
            add_failure(failures, "RENDERED_SCREENSHOT_PATH_MISSING", f"page {page_number} screenshot path is missing")
        else:
            screenshot_path = _resolve(run_dir, screenshot_path_value)
            if not screenshot_path.is_file():
                add_failure(failures, "RENDERED_SCREENSHOT_MISSING", f"page {page_number} screenshot not found: {screenshot_path}")
            else:
                file_hash = sha256_file(screenshot_path)
                if file_hash != actual["screenshot_sha256"]:
                    add_failure(failures, "RENDERED_SCREENSHOT_STALE", f"page {page_number} screenshot does not match the exact PDF render")
        if recorded.get("screenshot_sha256") != actual["screenshot_sha256"]:
            add_failure(failures, "RENDERED_SCREENSHOT_HASH_MISMATCH", f"page {page_number} screenshot hash is stale")
        for metric in ("meaningful_fill", "bottom_reach", "largest_blank_gap"):
            try:
                delta = abs(float(recorded.get(metric)) - float(actual[metric]))
            except (TypeError, ValueError):
                delta = 999
            if delta > METRIC_TOLERANCE:
                add_failure(failures, "RENDERED_METRIC_MISMATCH", f"page {page_number} {metric} was not measured from the exact PDF")
        try:
            font_delta = abs(float(recorded.get("body_font_median_pt")) - float(actual["body_font_median_pt"]))
        except (TypeError, ValueError):
            font_delta = 999
        if font_delta > FONT_TOLERANCE:
            add_failure(failures, "RENDERED_FONT_METRIC_MISMATCH", f"page {page_number} font metric was not measured from the exact PDF")

        minimum_fill = MIN_ONE_PAGE_FILL if page_count == 1 else (MIN_FIRST_PAGE_FILL if page_number < page_count else MIN_FINAL_PAGE_FILL)
        if float(actual["meaningful_fill"]) < minimum_fill:
            code = "FIRST_PAGE_UNDERFILLED" if page_number == 1 and page_count == 2 else "FINAL_PAGE_UNDERFILLED"
            add_failure(failures, code, f"page {page_number} meaningful fill is {actual['meaningful_fill']:.0%}; minimum is {minimum_fill:.0%}")
        if float(actual["largest_blank_gap"]) > MAX_INTERIOR_GAP:
            add_failure(failures, "LARGE_INTERNAL_BLANK_GAP", f"page {page_number} contains an internal blank gap of {actual['largest_blank_gap']:.0%}")
        if float(actual["body_font_median_pt"]) < MIN_BODY_FONT_PT:
            add_failure(failures, "BODY_FONT_TOO_SMALL", f"page {page_number} body text median is {actual['body_font_median_pt']:.2f} pt; minimum is {MIN_BODY_FONT_PT:.2f} pt")

    expected_headings = review.get("expected_headings")
    if not isinstance(expected_headings, list) or not expected_headings:
        add_failure(failures, "SECTION_HEADING_AUDIT_MISSING", "expected_headings must list the final semantic sections")
        expected_headings = []
    normalised_lines = [normalise(line).casefold() for line in extracted_lines]
    for heading in expected_headings:
        target = normalise(str(heading)).casefold()
        count = sum(1 for line in normalised_lines if line == target)
        if count == 0:
            add_failure(failures, "SECTION_HEADING_MISSING", f"section heading {heading!r} is missing")
        elif count > 1:
            add_failure(failures, "DUPLICATE_SECTION_HEADING", f"section heading {heading!r} appears {count} times")
    for line in extracted_lines:
        if FORBIDDEN_CONTINUATION.search(line):
            add_failure(failures, "CONTINUED_HEADING_FORBIDDEN", f"forbidden continuation heading: {line!r}")
        if normalise(line).casefold() in FORBIDDEN_HEADING_TEXT:
            add_failure(failures, "ADDITIONAL_SECTION_HEADING_FORBIDDEN", f"non-canonical heading: {line!r}")

    manual = review.get("manual_review")
    if not isinstance(manual, dict):
        add_failure(failures, "MANUAL_RENDER_REVIEW_MISSING", "manual_review is required after inspecting every page image")
        manual = {}
    required_true = (
        "inspected_all_pages",
        "no_large_blank_areas",
        "no_duplicate_or_continued_headings",
        "readable_typography",
        "natural_pagination",
        "section_flow_coherent",
    )
    if manual.get("outcome") != "pass":
        add_failure(failures, "MANUAL_RENDER_REVIEW_NOT_PASSED", "manual rendered-page review must pass")
    for key in required_true:
        if manual.get(key) is not True:
            add_failure(failures, "MANUAL_RENDER_REVIEW_INCOMPLETE", f"manual review must explicitly confirm {key}")
    reviewer_actor = str(manual.get("reviewer_actor", "")).strip()
    if not reviewer_actor:
        add_failure(failures, "MANUAL_RENDER_REVIEWER_MISSING", "manual visual reviewer actor is required")
    if expected_reviewer_actor and reviewer_actor != expected_reviewer_actor:
        add_failure(failures, "MANUAL_RENDER_REVIEWER_MISMATCH", "rendered-page reviewer must match the latest independent review actor")
    if len(str(manual.get("notes", "")).strip()) < 40:
        add_failure(failures, "MANUAL_RENDER_REVIEW_NOTES_MISSING", "manual review requires page-specific notes")

    source = review.get("editable_source")
    if not isinstance(source, dict):
        add_failure(failures, "EDITABLE_SOURCE_AUDIT_MISSING", "editable_source audit is required")
        source = {}
    if source.get("native_google_doc_used_as_canonical") is not False:
        add_failure(failures, "NATIVE_GOOGLE_DOC_CANONICAL_FORBIDDEN", "native Google Docs conversion cannot be the canonical editable CV")
    source_format = str(source.get("format", "")).strip().lower()
    if source_format not in {"docx", "html", "pdf_only"}:
        add_failure(failures, "EDITABLE_SOURCE_FORMAT_INVALID", "editable source format must be docx, html or pdf_only")
    source_path_value = source.get("path")
    if source_format in {"docx", "html"}:
        if not isinstance(source_path_value, str) or not source_path_value.strip():
            add_failure(failures, "EDITABLE_SOURCE_PATH_MISSING", "editable source path is required")
        else:
            source_path = _resolve(run_dir, source_path_value)
            if not source_path.is_file():
                add_failure(failures, "EDITABLE_SOURCE_MISSING", f"editable source not found: {source_path}")
            else:
                for finding in _scan_explicit_page_breaks(source_path, source_format):
                    add_failure(failures, "EXPLICIT_PAGE_BREAK_FORBIDDEN", finding)

    return failures


def capture(
    pdf_path: Path,
    review_path: Path,
    screenshots_dir: Path,
    expected_headings: list[str],
    reviewer_actor: str,
    editable_source: Path | None,
    source_format: str,
) -> None:
    run_dir = review_path.parent
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    document = _open_pdf(pdf_path)
    analysed, _ = analyse_pdf(pdf_path)
    page_records = []
    for actual, page in zip(analysed, document):
        screenshot_path = screenshots_dir / f"page-{actual['page']}.png"
        screenshot_path.write_bytes(page_png_bytes(page))
        page_records.append({
            **actual,
            "screenshot_path": str(screenshot_path.relative_to(run_dir) if screenshot_path.is_relative_to(run_dir) else screenshot_path),
        })
    payload = {
        "contract": CONTRACT,
        "pdf_sha256": sha256_file(pdf_path),
        "page_count": len(page_records),
        "pages": page_records,
        "expected_headings": expected_headings,
        "manual_review": {
            "reviewer_actor": reviewer_actor,
            "outcome": "pending",
            "inspected_all_pages": False,
            "no_large_blank_areas": False,
            "no_duplicate_or_continued_headings": False,
            "readable_typography": False,
            "natural_pagination": False,
            "section_flow_coherent": False,
            "notes": "",
        },
        "editable_source": {
            "format": source_format,
            "path": str(editable_source.relative_to(run_dir) if editable_source and editable_source.is_relative_to(run_dir) else editable_source or ""),
            "native_google_doc_used_as_canonical": False,
        },
    }
    review_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    capture_parser = sub.add_parser("capture")
    capture_parser.add_argument("pdf")
    capture_parser.add_argument("review")
    capture_parser.add_argument("--screenshots-dir", required=True)
    capture_parser.add_argument("--heading", action="append", default=[])
    capture_parser.add_argument("--reviewer-actor", required=True)
    capture_parser.add_argument("--editable-source")
    capture_parser.add_argument("--source-format", choices=("docx", "html", "pdf_only"), default="pdf_only")
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("pdf")
    validate_parser.add_argument("review")
    validate_parser.add_argument("--run-dir", default=".")
    validate_parser.add_argument("--expected-reviewer-actor")
    args = parser.parse_args()

    if args.command == "capture":
        capture(
            Path(args.pdf),
            Path(args.review),
            Path(args.screenshots_dir),
            args.heading,
            args.reviewer_actor,
            Path(args.editable_source) if args.editable_source else None,
            args.source_format,
        )
        print(f"WROTE RENDERED VISUAL REVIEW DRAFT: {args.review}")
        return 0

    failures = validate(Path(args.pdf), load_json(Path(args.review)), Path(args.run_dir), args.expected_reviewer_actor)
    result = {"passed": not failures, "failures": failures}
    if failures:
        print(json.dumps(result, indent=2))
        return 1
    print("RENDERED VISUAL REVIEW GATE PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
