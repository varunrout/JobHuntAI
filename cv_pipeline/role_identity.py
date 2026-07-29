#!/usr/bin/env python3
"""Classify a role into a reusable JobHuntAI professional archetype.

This stage runs before evidence selection. It is deterministic, configuration-led
and intentionally independent of the candidate evidence bank.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "archetypes.json"
ROLE_INPUT_SCHEMA_PATH = ROOT / "schemas" / "role_input.schema.json"
ROLE_OUTPUT_SCHEMA_PATH = ROOT / "schemas" / "role_identity.schema.json"


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    configured = dict(registry.get("archetypes", {}))
    for relative_path in registry.get("archetype_files", []):
        configured.update(json.loads((path.parent / relative_path).read_text(encoding="utf-8")))
    defaults = registry.pop("archetype_defaults", {})
    registry["archetypes"] = {
        key: _deep_merge(defaults, value)
        for key, value in configured.items()
    }
    return registry


def schema_errors(instance: dict[str, Any], schema_path: Path) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        return [f"jsonschema is required: {exc}"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "root"
        errors.append(f"{location}: {error.message}")
    return errors


def _normalise(value: Any) -> str:
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    if isinstance(value, dict):
        value = " ".join(f"{key} {item}" for key, item in value.items())
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def _term_hits(text: str, terms: list[str]) -> int:
    hits = 0
    for term in terms:
        term = _normalise(term)
        if not term:
            continue
        hits += text.count(term)
    return hits


def score_archetypes(role: dict[str, Any], registry: dict[str, Any] | None = None) -> dict[str, float]:
    registry = registry or load_registry()
    field_weights = registry["classification"]["field_weights"]
    normalised = {field: _normalise(role.get(field, "")) for field in field_weights}
    scores: dict[str, float] = {}
    for archetype_id, archetype in registry["archetypes"].items():
        score = 0.0
        signals = archetype.get("classification_signals", {})
        for field, weight in field_weights.items():
            score += _term_hits(normalised[field], signals.get(field, [])) * float(weight)
        scores[archetype_id] = round(score, 4)
    return scores


def _softmax_confidence(scores: dict[str, float], winner: str) -> float:
    values = list(scores.values())
    if not values or max(values) <= 0:
        return 0.2
    peak = max(values)
    exps = {key: math.exp((value - peak) / 3.0) for key, value in scores.items()}
    probability = exps[winner] / sum(exps.values())
    return round(min(0.99, max(0.2, probability)), 3)


def _relevant_year_points(value: Any) -> int:
    try:
        years = float(value)
    except (TypeError, ValueError):
        return 0
    if years >= 8:
        return 3
    if years >= 5:
        return 2
    if years >= 3:
        return 1
    return 0


def recommend_page_length(role: dict[str, Any], archetype: dict[str, Any], registry: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    registry = registry or load_registry()
    context = role.get("candidate_context", {}) or {}
    policy = registry["page_length_policy"]
    factors = {
        "relevant_years": _relevant_year_points(context.get("relevant_years")),
        "seniority": policy["factors"]["seniority"].get(_normalise(role.get("seniority")) or "mid", 1),
        "breadth_of_responsibilities": policy["factors"]["breadth_of_responsibilities"].get(_normalise(context.get("breadth_of_responsibilities")) or "moderate", 1),
        "strategic_depth": policy["factors"]["strategic_depth"].get(_normalise(context.get("strategic_depth")) or "medium", 1),
        "leadership_expectations": policy["factors"]["leadership_expectations"].get(_normalise(context.get("leadership_expectations")) or "none", 0),
        "evidence_density": policy["factors"]["evidence_density"].get(_normalise(context.get("evidence_density")) or "medium", 1),
    }
    score = sum(factors.values())
    default_pages = int(archetype["expected_page_length"]["default"])
    recommended = 2 if score >= int(policy["two_page_threshold"]) else min(default_pages, 1)
    return recommended, {"score": score, "factors": factors}


def classify_role(role: dict[str, Any], registry: dict[str, Any] | None = None) -> dict[str, Any]:
    validation = schema_errors(role, ROLE_INPUT_SCHEMA_PATH)
    if validation:
        raise ValueError("Invalid role identity input: " + "; ".join(validation))
    registry = registry or load_registry()
    scores = score_archetypes(role, registry)
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    if not ranked or ranked[0][1] <= 0:
        raise ValueError("Role Identity Classification found no archetype signal; complete the role input rather than defaulting to Data Scientist or Data Analyst")
    winner = ranked[0][0]
    top_score = scores[winner]
    ratio = float(registry["classification"]["secondary_score_ratio"])
    minimum = float(registry["classification"]["minimum_secondary_score"])
    secondary = [
        key for key, value in ranked
        if key != winner and value >= minimum and value >= top_score * ratio
    ][:3]
    archetype = registry["archetypes"][winner]
    page_length, page_rationale = recommend_page_length(role, archetype, registry)
    strategy = (
        f"Position the candidate as a {archetype['label']} who {archetype['problem_class']}. "
        f"Lead with {', '.join(archetype['evidence_priorities'][:3]).replace('_', ' ')}, "
        f"use a {archetype['layout_variant']} layout, and keep secondary identities subordinate."
    )
    confidence = _softmax_confidence(scores, winner)
    result = {
        "archetype": winner,
        "confidence": confidence,
        "secondary_archetypes": secondary,
        "positioning_strategy": strategy,
        "recommended_page_length": page_length,
        "page_length_rationale": page_rationale,
        "classification_scores": scores,
        "requires_review": confidence < float(registry["classification"].get("review_confidence_threshold", 0.35)),
    }
    output_errors = schema_errors(result, ROLE_OUTPUT_SCHEMA_PATH)
    if output_errors:
        raise ValueError("Invalid role identity output: " + "; ".join(output_errors))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify a job into a JobHuntAI CV archetype")
    parser.add_argument("role_json")
    parser.add_argument("--out")
    args = parser.parse_args()
    role = json.loads(Path(args.role_json).read_text(encoding="utf-8"))
    try:
        result = classify_role(role)
    except ValueError as exc:
        print(f"ROLE IDENTITY BLOCKED: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
