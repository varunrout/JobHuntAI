#!/usr/bin/env python3
"""Positioning, evidence-selection and construction gates for archetype CVs."""
from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

from role_identity import load_registry

ROOT = Path(__file__).resolve().parent
CV_SCHEMA_PATH = ROOT / "schemas" / "archetype_cv.schema.json"
DIAG_SCHEMA_PATH = ROOT / "schemas" / "archetype_cv_diagnostic.schema.json"

DEFENSIVE_PHRASES = (
    "in all but title",
    "transitioning into",
    "looking to move into",
    "although my title was",
    "despite my title",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w£%+./-]+\b", text or "", flags=re.UNICODE))


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9%£]+", " ", (text or "").lower())).strip()


def schema_errors(instance: dict[str, Any], schema_path: Path) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["jsonschema is required to validate archetype CV payloads"]
    validator = Draft202012Validator(load_json(schema_path))
    out = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "root"
        out.append(f"{location}: {error.message}")
    return out


def iter_bullets(cv: dict[str, Any]) -> Iterable[tuple[str, str]]:
    for index, block in enumerate(cv.get("experience", [])):
        label = block.get("org") or block.get("title") or f"experience[{index}]"
        for bullet in block.get("bullets", []):
            yield label, str(bullet)
        for role in block.get("roles", []):
            role_label = f"{label}/{role.get('title', '?')}"
            for bullet in role.get("bullets", []):
                yield role_label, str(bullet)
    for project in cv.get("projects", []):
        for bullet in project.get("bullets", []):
            yield f"project:{project.get('title', '?')}", str(bullet)
    for impact in cv.get("selected_impact", []):
        for bullet in impact.get("bullets", []):
            yield f"impact:{impact.get('headline', '?')}", str(bullet)


def block_bullet_count(block: dict[str, Any]) -> int:
    return len(block.get("bullets", [])) + sum(len(role.get("bullets", [])) for role in block.get("roles", []))


def all_rendered_text(cv: dict[str, Any]) -> str:
    chunks = [str(cv.get("summary", ""))]
    identity = cv.get("identity", {})
    chunks.extend(str(identity.get(key, "")) for key in ("name", "headline", "location"))
    for skill in cv.get("skills", []):
        chunks.extend((str(skill.get("category", "")), str(skill.get("items", ""))))
    chunks.extend(text for _, text in iter_bullets(cv))
    return "\n".join(item for item in chunks if item)


def _section_has_content(cv: dict[str, Any], section: str) -> bool:
    mapping = {
        "summary": bool(cv.get("summary")),
        "impact": bool(cv.get("selected_impact")),
        "skills": bool(cv.get("skills")),
        "experience": bool(cv.get("experience")),
        "projects": bool(cv.get("projects")),
        "education": bool(cv.get("education")),
    }
    return mapping[section]


def validate_payload(cv: dict[str, Any]) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = [("CV_SCHEMA", error) for error in schema_errors(cv, CV_SCHEMA_PATH)]
    registry = load_registry()
    archetype_id = cv.get("archetype")
    archetype = registry["archetypes"].get(archetype_id)
    if not archetype:
        failures.append(("UNKNOWN_ARCHETYPE", repr(archetype_id)))
        return failures

    role_identity = cv.get("role_identity", {})
    if role_identity.get("archetype") != archetype_id:
        failures.append(("ROLE_IDENTITY_MISMATCH", "role_identity.archetype must match cv.archetype"))
    if role_identity.get("requires_review") and not cv.get("classification_review"):
        failures.append(("LOW_CONFIDENCE_IDENTITY_REVIEW_REQUIRED", "low-confidence role classification requires a recorded classification_review"))
    page_strategy = cv.get("page_strategy", {})
    if page_strategy.get("recommended_page_length") != role_identity.get("recommended_page_length"):
        failures.append(("PAGE_STRATEGY_MISMATCH", "page strategy and role identity recommend different lengths"))
    if page_strategy.get("maximum_pages") != page_strategy.get("recommended_page_length") and not cv.get("page_limit_exception"):
        failures.append(("PAGE_MAXIMUM_MISMATCH", "maximum_pages must match the recommended page length unless a page-limit exception is recorded"))

    headline = str(cv.get("identity", {}).get("headline", ""))
    label_tokens = {token for token in _normalise(archetype["label"]).split() if len(token) > 3}
    if label_tokens and not label_tokens.intersection(_normalise(headline).split()):
        failures.append(("HEADLINE_ARCHETYPE_MISSING", f"headline does not establish {archetype['label']!r}"))

    summary = str(cv.get("summary", ""))
    summary_words = word_count(summary)
    minimum, maximum = (45, 85) if archetype["layout_variant"] == "technical" else (50, 95)
    if not minimum <= summary_words <= maximum:
        failures.append(("SUMMARY_LENGTH", f"summary is {summary_words} words; required range is {minimum} to {maximum}"))
    for phrase in DEFENSIVE_PHRASES:
        if phrase in f"{headline}\n{summary}".lower():
            failures.append(("DEFENSIVE_POSITIONING", f"remove defensive phrase {phrase!r}"))

    categories = [str(item.get("category", "")) for item in cv.get("skills", [])]
    unknown = [item for item in categories if item not in set(archetype["skills_taxonomy"])]
    if unknown:
        failures.append(("UNCONTROLLED_SKILLS_TAXONOMY", f"categories not allowed for {archetype['label']}: {', '.join(unknown)}"))
    if len(categories) != len(set(categories)):
        failures.append(("DUPLICATE_SKILL_CATEGORY", "skill category names must be unique"))

    layout_override = cv.get("layout_override_reason")
    if cv.get("layout_variant") != archetype["layout_variant"] and not layout_override:
        failures.append(("ARCHETYPE_LAYOUT_VARIANT", f"expected layout variant {archetype['layout_variant']!r}"))
    labels = cv.get("section_labels", {})
    label_drift = [section for section, label in archetype["section_labels"].items() if labels.get(section) != label]
    if label_drift and not layout_override:
        failures.append(("ARCHETYPE_SECTION_LABELS", "section labels differ from the selected archetype: " + ", ".join(label_drift)))

    section_order = cv.get("section_order", [])
    if section_order and section_order[0] != "summary":
        failures.append(("SECTION_ORDER_SUMMARY", "summary must remain the first section"))
    missing_non_empty = [section for section in ("impact", "skills", "experience", "projects", "education") if _section_has_content(cv, section) and section not in section_order]
    if missing_non_empty:
        failures.append(("SECTION_ORDER_OMISSION", "non-empty sections omitted from section_order: " + ", ".join(missing_non_empty)))
    expected_order = [section for section in archetype["section_order"] if _section_has_content(cv, section)]
    actual_order = [section for section in section_order if _section_has_content(cv, section)]
    if actual_order != expected_order and not layout_override:
        failures.append(("ARCHETYPE_SECTION_ORDER", f"expected {expected_order}, received {actual_order}; record layout_override_reason for a justified deviation"))

    one_page = cv.get("page_strategy", {}).get("maximum_pages") == 1
    for index, block in enumerate(cv.get("experience", [])):
        maximum_bullets = 6 if index == 0 else (3 if one_page else 4)
        count = block_bullet_count(block)
        if count > maximum_bullets:
            label = block.get("org") or block.get("title") or f"experience[{index}]"
            failures.append(("ROLE_SPACE_ALLOCATION", f"{label!r} has {count} bullets; maximum is {maximum_bullets}"))

    project_limit = 3 if int(archetype["project_importance"]) >= 4 else 2
    if len(cv.get("projects", [])) > project_limit:
        failures.append(("PROJECT_ARCHETYPE_OVERLOAD", f"{archetype['label']} permits at most {project_limit} projects by default"))

    bullets = list(iter_bullets(cv))
    for label, bullet in bullets:
        count = word_count(bullet)
        if count > 48:
            failures.append(("BULLET_TOO_LONG", f"{label} bullet is {count} words"))
    normalised = [(label, _normalise(bullet)) for label, bullet in bullets if bullet]
    for index, (label_a, text_a) in enumerate(normalised):
        if len(text_a) < 30:
            continue
        for label_b, text_b in normalised[index + 1:]:
            if len(text_b) >= 30 and SequenceMatcher(None, text_a, text_b).ratio() >= 0.88:
                failures.append(("REPEATED_ACHIEVEMENT", f"near-duplicate evidence appears in {label_a!r} and {label_b!r}"))

    bullet_strategy = cv.get("bullet_strategy", {})
    dimensions = bullet_strategy.get("optimise_for", [])
    allowed_dimensions = set(registry["bullet_optimisation_dimensions"])
    if any(item not in allowed_dimensions for item in dimensions):
        failures.append(("UNKNOWN_BULLET_DIMENSION", "bullet strategy contains an unsupported optimisation dimension"))
    archetype_dimension_weights = {key: value for key, value in archetype["evidence_weights"].items() if key in allowed_dimensions}
    priority_dimensions = {key for key, _ in sorted(archetype_dimension_weights.items(), key=lambda item: (-item[1], item[0]))[:4]}
    if len(priority_dimensions.intersection(dimensions)) < 2:
        failures.append(("ARCHETYPE_BULLET_EMPHASIS", "bullet strategy must include at least two of the archetype's highest-priority dimensions"))
    configured_verbs = {item.lower() for item in archetype["preferred_verbs"]}
    supplied_verbs = {str(item).lower() for item in bullet_strategy.get("preferred_verbs", [])}
    if not configured_verbs.intersection(supplied_verbs):
        failures.append(("ARCHETYPE_VERB_MISMATCH", "preferred verbs do not reflect the selected archetype"))
    return failures


def validate_diagnostic(cv: dict[str, Any], diagnostic: dict[str, Any]) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = [("DIAGNOSTIC_SCHEMA", error) for error in schema_errors(diagnostic, DIAG_SCHEMA_PATH)]
    if diagnostic.get("role_identity", {}).get("archetype") != cv.get("archetype"):
        failures.append(("DIAGNOSTIC_ARCHETYPE_MISMATCH", "diagnostic and CV archetypes differ"))
    dimensions = set(diagnostic.get("bullet_optimisation", {}).get("dimensions", []))
    planned = set(cv.get("bullet_strategy", {}).get("optimise_for", []))
    if dimensions != planned:
        failures.append(("BULLET_STRATEGY_DIAGNOSTIC_MISMATCH", "diagnostic bullet dimensions differ from the CV strategy"))
    scores = [float(item.get("archetype_score", 0.0)) for item in diagnostic.get("evidence_ranking", [])]
    if scores != sorted(scores, reverse=True):
        failures.append(("EVIDENCE_RANKING_ORDER", "evidence_ranking must be sorted from highest to lowest archetype score"))
    locations = [str(item.get("location", "")) for item in diagnostic.get("signature_proof_points", [])]
    if len(locations) != len(set(locations)):
        failures.append(("DUPLICATE_SIGNATURE_LOCATION", "signature proof points must map to distinct CV locations"))
    return failures


def update_diagnostic_results(cv: dict[str, Any], diagnostic: dict[str, Any], failures: list[tuple[str, str]]) -> None:
    results = diagnostic.setdefault("results", {})
    results["final_word_count"] = word_count(all_rendered_text(cv))
    results.setdefault("final_page_count", None)
    results.setdefault("first_page_sufficiency", "pending")
    results["positioning_consistency"] = "fail" if failures else "pass"
    results.setdefault("evidence_integrity", "pending")
    results.setdefault("layout_quality", "pending")
    results["construction_gate_failures"] = [{"code": code, "detail": detail} for code, detail in failures]


def run(cv_path: Path, diagnostic_path: Path, write_diagnostic: bool = False) -> int:
    cv = load_json(cv_path)
    diagnostic = load_json(diagnostic_path)
    failures = validate_payload(cv) + validate_diagnostic(cv, diagnostic)
    update_diagnostic_results(cv, diagnostic, failures)
    if write_diagnostic:
        diagnostic_path.write_text(json.dumps(diagnostic, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        print(f"ARCHETYPE CONSTRUCTION BLOCKED - {len(failures)} failure(s):")
        for code, detail in failures:
            print(f"[{code}] {detail}")
        return 2
    print("ARCHETYPE CONSTRUCTION CLEAN.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cv")
    parser.add_argument("--diagnostic", required=True)
    parser.add_argument("--write-diagnostic", action="store_true")
    args = parser.parse_args()
    return run(Path(args.cv), Path(args.diagnostic), args.write_diagnostic)


if __name__ == "__main__":
    sys.exit(main())
