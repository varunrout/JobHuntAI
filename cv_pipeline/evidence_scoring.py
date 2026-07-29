#!/usr/bin/env python3
"""Archetype-aware evidence reweighting for JobHuntAI CV generation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from role_identity import ROLE_OUTPUT_SCHEMA_PATH, load_registry, schema_errors

ROOT = Path(__file__).resolve().parent
EVIDENCE_SCHEMA_PATH = ROOT / "schemas" / "evidence_candidate.schema.json"

SOURCE_STRENGTH = {
    "verified_employment": 1.0,
    "verified_project": 0.9,
    "portfolio": 0.8,
    "inferred": 0.35,
}

CLAIM_STATUS_FACTOR = {
    "measured": 1.0,
    "verified": 0.95,
    "association_only": 0.75,
    "illustrative": 0.0,
    "unsupported": 0.0,
}


def score_evidence_item(item: dict[str, Any], archetype_id: str, secondary_archetypes: list[str] | None = None, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    validation = schema_errors(item, EVIDENCE_SCHEMA_PATH)
    if validation:
        raise ValueError("Invalid evidence candidate: " + "; ".join(validation))
    registry = registry or load_registry()
    archetypes = registry["archetypes"]
    if archetype_id not in archetypes:
        raise KeyError(f"Unknown archetype: {archetype_id}")
    secondary_archetypes = [key for key in (secondary_archetypes or []) if key in archetypes]
    dimensions = item.get("dimensions", {}) or {}
    primary_weights = archetypes[archetype_id]["evidence_weights"]
    blended = dict(primary_weights)
    if secondary_archetypes:
        for dimension in blended:
            secondary_average = sum(archetypes[key]["evidence_weights"].get(dimension, 0.0) for key in secondary_archetypes) / len(secondary_archetypes)
            blended[dimension] = primary_weights.get(dimension, 0.0) * 0.85 + secondary_average * 0.15
    weighted_total = 0.0
    weight_total = 0.0
    breakdown: dict[str, float] = {}
    for dimension, weight in blended.items():
        value = float(dimensions.get(dimension, 0.0))
        contribution = value * float(weight)
        breakdown[dimension] = round(contribution, 3)
        weighted_total += contribution
        weight_total += 5.0 * float(weight)
    source_factor = float(item.get("source_strength", SOURCE_STRENGTH.get(str(item.get("source_type", "inferred")), 0.5)))
    source_factor *= CLAIM_STATUS_FACTOR.get(str(item.get("claim_status", "verified")), 0.5)
    domain_bonus = min(1.0, float(dimensions.get("domain_relevance", 0.0)) / 5.0) * 5.0
    score = ((weighted_total / weight_total) * 95.0 if weight_total else 0.0) * source_factor + domain_bonus
    return {
        **item,
        "archetype_score": round(min(100.0, score), 2),
        "score_breakdown": breakdown,
        "source_factor": source_factor,
    }


def rank_evidence(items: list[dict[str, Any]], role_identity: dict[str, Any], registry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    identity_errors = schema_errors(role_identity, ROLE_OUTPUT_SCHEMA_PATH)
    if identity_errors:
        raise ValueError("Invalid role identity: " + "; ".join(identity_errors))
    scored = [
        score_evidence_item(
            item,
            role_identity["archetype"],
            role_identity.get("secondary_archetypes", []),
            registry,
        )
        for item in items
    ]
    return sorted(scored, key=lambda item: (-item["archetype_score"], str(item.get("id", ""))))


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank evidence after role identity classification")
    parser.add_argument("role_identity_json")
    parser.add_argument("evidence_json")
    parser.add_argument("--out")
    args = parser.parse_args()
    identity = json.loads(Path(args.role_identity_json).read_text(encoding="utf-8"))
    evidence = json.loads(Path(args.evidence_json).read_text(encoding="utf-8"))
    try:
        result = {"role_identity": identity, "ranked_evidence": rank_evidence(evidence, identity)}
    except (KeyError, ValueError) as exc:
        print(f"EVIDENCE RANKING BLOCKED: {exc}")
        return 2
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
