#!/usr/bin/env python3
"""Identity, selection and construction gates for JobHuntAI CVs.

This module deliberately sits beside lint.py rather than replacing it.
lint.py remains the factual-integrity gate. This file enforces the user's
pipeline-level CV construction contract: one dominant identity, a concise
summary, a role-specific capability map, selective evidence, disciplined space
allocation and a complete diagnostic sidecar.

Usage:
    python quality_gate.py runs/<job_id>/cv.json \
        --diagnostic runs/<job_id>/cv_diagnostic.json --write-diagnostic

Exit 0 = construction clean. Exit 2 = blocked.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent
MODES_PATH = ROOT / "identity_modes.json"
CV_SCHEMA_PATH = ROOT / "schemas" / "cv.schema.json"
DIAG_SCHEMA_PATH = ROOT / "schemas" / "cv_diagnostic.schema.json"

DEFENSIVE_PHRASES = (
    "data science in all but title",
    "data scientist in all but title",
    "transitioning into",
    "looking to move into",
    "although my title was",
    "despite my title",
    "not a data scientist by title",
)

PROJECT_MOTIVATION_PHRASES = (
    "wanted to measure",
    "set out to prove",
    "built on my own time to keep",
    "created to keep my skills current",
    "keep my skills current",
    "keep working with",
)

OFFICIAL_TITLES = {
    "market analyst",
    "costing and risk intern",
    "data scientist",
    "systems engineer",
    "business analytics consultant",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def modes() -> dict[str, Any]:
    return load_json(MODES_PATH)["modes"]


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w£%+./-]+\b", text or "", flags=re.UNICODE))


def iter_role_bullets(cv: dict[str, Any]) -> Iterable[tuple[str, str]]:
    for idx, block in enumerate(cv.get("experience", [])):
        label = block.get("org") or block.get("title") or f"experience[{idx}]"
        for bullet in block.get("bullets", []):
            yield label, bullet
        for role in block.get("roles", []):
            role_label = f"{label}/{role.get('title', '?')}"
            for bullet in role.get("bullets", []):
                yield role_label, bullet


def block_bullet_count(block: dict[str, Any]) -> int:
    return len(block.get("bullets", [])) + sum(
        len(role.get("bullets", [])) for role in block.get("roles", [])
    )


def all_rendered_text(cv: dict[str, Any]) -> str:
    chunks: list[str] = []
    identity = cv.get("identity", {})
    chunks.extend(str(identity.get(key, "")) for key in ("name", "headline", "location"))
    chunks.append(str(cv.get("summary", "")))
    for skill in cv.get("skills", []):
        chunks.extend([str(skill.get("category", "")), str(skill.get("items", ""))])
    for block in cv.get("experience", []):
        chunks.extend(str(block.get(key, "")) for key in ("title", "org", "dates", "sub"))
        chunks.extend(str(b) for b in block.get("bullets", []))
        for role in block.get("roles", []):
            chunks.extend(str(role.get(key, "")) for key in ("title", "dates"))
            chunks.extend(str(b) for b in role.get("bullets", []))
    for project in cv.get("projects", []):
        chunks.extend(str(project.get(key, "")) for key in ("title", "tools", "dates"))
        chunks.extend(str(b) for b in project.get("bullets", []))
    for education in cv.get("education", []):
        chunks.extend(str(education.get(key, "")) for key in ("degree", "school", "dates"))
    return "\n".join(chunk for chunk in chunks if chunk)


def _normalise(text: str) -> str:
    text = re.sub(r"[^a-z0-9%£]+", " ", (text or "").lower())
    return re.sub(r"\s+", " ", text).strip()


def schema_errors(instance: dict[str, Any], schema_path: Path) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["jsonschema is required to validate CV payloads"]
    validator = Draft202012Validator(load_json(schema_path))
    out = []
    for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        location = ".".join(str(p) for p in error.path) or "root"
        out.append(f"{location}: {error.message}")
    return out


def validate_payload(cv: dict[str, Any]) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    for error in schema_errors(cv, CV_SCHEMA_PATH):
        failures.append(("CV_SCHEMA", error))

    mode_id = cv.get("cv_identity_mode")
    mode = modes().get(mode_id)
    if not mode:
        failures.append(("UNKNOWN_IDENTITY_MODE", repr(mode_id)))
        return failures

    dominant = cv.get("dominant_identity") or mode["label"]
    if dominant != mode["label"]:
        failures.append((
            "DOMINANT_IDENTITY_MISMATCH",
            f"dominant_identity must be {mode['label']!r} for mode {mode_id!r}",
        ))

    secondary = cv.get("hybrid_secondary_identity")
    if secondary == mode_id:
        failures.append(("INVALID_HYBRID", "secondary identity duplicates the dominant identity"))

    headline = str(cv.get("identity", {}).get("headline", ""))
    low_headline = headline.lower()
    if mode["label"].lower() not in low_headline:
        failures.append((
            "HEADLINE_IDENTITY_MISSING",
            f"headline must state the selected professional identity {mode['label']!r}",
        ))
    if _normalise(headline) in OFFICIAL_TITLES:
        failures.append((
            "HEADLINE_REPEATS_OFFICIAL_TITLE",
            "the target headline must be separate from official work-experience titles",
        ))

    summary = str(cv.get("summary", ""))
    summary_words = word_count(summary)
    if not 45 <= summary_words <= 70:
        failures.append((
            "SUMMARY_LENGTH",
            f"summary is {summary_words} words; required range is 45 to 70",
        ))

    headline_and_summary = f"{headline}\n{summary}".lower()
    for phrase in DEFENSIVE_PHRASES:
        if phrase in headline_and_summary:
            failures.append((
                "DEFENSIVE_POSITIONING",
                f"remove defensive or gap-explaining phrase {phrase!r}; evidence must establish fit directly",
            ))

    skills = cv.get("skills", [])
    categories = [str(item.get("category", "")) for item in skills]
    allowed_categories = set(mode["capability_categories"])
    unknown = [category for category in categories if category not in allowed_categories]
    if unknown:
        failures.append((
            "UNCONTROLLED_CAPABILITY_TAXONOMY",
            f"categories not allowed for {mode['label']}: {', '.join(unknown)}",
        ))
    if len(categories) != len(set(categories)):
        failures.append(("DUPLICATE_CAPABILITY_CATEGORY", "capability category names must be unique"))

    experience = cv.get("experience", [])
    for index, block in enumerate(experience):
        count = block_bullet_count(block)
        maximum = 6 if index == 0 else 3
        if count > maximum:
            label = block.get("org") or block.get("title") or f"experience[{index}]"
            failures.append((
                "ROLE_SPACE_ALLOCATION",
                f"{label!r} has {count} bullets; maximum is {maximum} for this position in the CV",
            ))

    bullets: list[tuple[str, str]] = list(iter_role_bullets(cv))
    for project in cv.get("projects", []):
        project_bullets = project.get("bullets", [])
        if len(project_bullets) > 3:
            failures.append((
                "PROJECT_SPACE_ALLOCATION",
                f"project {project.get('title')!r} has {len(project_bullets)} bullets; maximum is 3",
            ))
        for bullet in project_bullets:
            bullets.append((f"project:{project.get('title', '?')}", bullet))
            low = str(bullet).lower()
            for phrase in PROJECT_MOTIVATION_PHRASES:
                if phrase in low:
                    failures.append((
                        "PROJECT_MOTIVATION_LANGUAGE",
                        f"project {project.get('title')!r} uses motivation-led opening {phrase!r}",
                    ))

    for label, bullet in bullets:
        count = word_count(str(bullet))
        if count > 45:
            failures.append((
                "BULLET_TOO_LONG",
                f"{label} bullet is {count} words; rewrite to one action, one method and one outcome",
            ))

    normalised = [(label, _normalise(str(bullet))) for label, bullet in bullets if bullet]
    for i, (label_a, text_a) in enumerate(normalised):
        if len(text_a) < 30:
            continue
        for label_b, text_b in normalised[i + 1:]:
            if len(text_b) < 30:
                continue
            ratio = SequenceMatcher(None, text_a, text_b).ratio()
            if ratio >= 0.88:
                failures.append((
                    "REPEATED_ACHIEVEMENT",
                    f"near-duplicate evidence appears in {label_a!r} and {label_b!r} ({ratio:.0%} similar)",
                ))

    return failures


def validate_diagnostic(cv: dict[str, Any], diagnostic: dict[str, Any]) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    for error in schema_errors(diagnostic, DIAG_SCHEMA_PATH):
        failures.append(("DIAGNOSTIC_SCHEMA", error))

    mode_id = cv.get("cv_identity_mode")
    mode = modes().get(mode_id, {})
    if diagnostic.get("cv_identity_mode") != mode_id:
        failures.append(("DIAGNOSTIC_IDENTITY_MISMATCH", "diagnostic and CV identity modes differ"))
    headline = cv.get("identity", {}).get("headline")
    if diagnostic.get("target_headline") != headline:
        failures.append(("DIAGNOSTIC_HEADLINE_MISMATCH", "diagnostic target headline differs from CV headline"))

    thesis = str(diagnostic.get("professional_thesis", ""))
    thesis_low = thesis.lower()
    required_thesis_terms = [mode.get("label", "").lower(), "solves", "using", "proven by"]
    missing_terms = [term for term in required_thesis_terms if term and term not in thesis_low]
    if missing_terms:
        failures.append((
            "PROFESSIONAL_THESIS_INCOMPLETE",
            "thesis must state identity, problem class, approach and proof; missing: " + ", ".join(missing_terms),
        ))

    cv_project_titles = {str(project.get("title", "")) for project in cv.get("projects", [])}
    selected_titles = {
        str(item.get("title", ""))
        for item in diagnostic.get("projects_selected", [])
        if isinstance(item, dict)
    }
    if selected_titles != cv_project_titles:
        failures.append((
            "PROJECT_SELECTION_DIAGNOSTIC_MISMATCH",
            f"diagnostic selected projects {sorted(selected_titles)} do not match CV projects {sorted(cv_project_titles)}",
        ))

    excluded_titles = {
        str(item.get("title", ""))
        for item in diagnostic.get("projects_excluded", [])
        if isinstance(item, dict)
    }
    overlap = cv_project_titles & excluded_titles
    if overlap:
        failures.append((
            "PROJECT_SELECTED_AND_EXCLUDED",
            "projects cannot be both selected and excluded: " + ", ".join(sorted(overlap)),
        ))

    proof_locations = [str(item.get("location", "")) for item in diagnostic.get("signature_proof_points", [])]
    if len(proof_locations) != len(set(proof_locations)):
        failures.append(("DUPLICATE_SIGNATURE_LOCATION", "signature proof points must map to distinct CV locations"))

    return failures


def update_diagnostic_results(
    cv: dict[str, Any],
    diagnostic: dict[str, Any],
    failures: list[tuple[str, str]],
) -> dict[str, Any]:
    results = diagnostic.setdefault("results", {})
    results["final_word_count"] = word_count(all_rendered_text(cv))
    results.setdefault("final_page_count", None)
    results.setdefault("first_page_sufficiency", "pending")
    results["identity_consistency"] = "fail" if failures else "pass"
    results.setdefault("evidence_integrity", "pending")
    results.setdefault("layout_quality", "pending")
    results["construction_gate_failures"] = [
        {"code": code, "detail": detail} for code, detail in failures
    ]
    return diagnostic


def run(cv_path: Path, diagnostic_path: Path, write_diagnostic: bool = False) -> int:
    cv = load_json(cv_path)
    diagnostic = load_json(diagnostic_path)
    failures = validate_payload(cv) + validate_diagnostic(cv, diagnostic)
    update_diagnostic_results(cv, diagnostic, failures)
    if write_diagnostic:
        diagnostic_path.write_text(
            json.dumps(diagnostic, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    if failures:
        print(f"BLOCKED - {len(failures)} CV construction failure(s):\n")
        for code, detail in failures:
            print(f"  [{code}] {detail}")
        return 2

    print("CV CONSTRUCTION CLEAN.")
    print(f"  identity: {cv['cv_identity_mode']}")
    print(f"  summary: {word_count(cv.get('summary', ''))} words")
    print(f"  capabilities: {len(cv.get('skills', []))}")
    print(f"  projects: {len(cv.get('projects', []))}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CV identity and construction gates")
    parser.add_argument("cv")
    parser.add_argument("--diagnostic", required=True)
    parser.add_argument("--write-diagnostic", action="store_true")
    args = parser.parse_args()
    return run(Path(args.cv), Path(args.diagnostic), args.write_diagnostic)


if __name__ == "__main__":
    sys.exit(main())
