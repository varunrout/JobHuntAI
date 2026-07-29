#!/usr/bin/env python3
"""Build the positioning brief that must exist before CV drafting."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evidence_scoring import rank_evidence
from role_identity import classify_role, load_registry


def build_positioning_brief(role: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    registry = load_registry()
    role_identity = classify_role(role, registry)
    archetype = registry["archetypes"][role_identity["archetype"]]
    ranked = rank_evidence(evidence, role_identity, registry)
    allowed_dimensions = set(registry["bullet_optimisation_dimensions"])
    dimension_weights = {
        key: value for key, value in archetype["evidence_weights"].items()
        if key in allowed_dimensions
    }
    optimise_for = [
        key for key, _ in sorted(
            dimension_weights.items(), key=lambda item: (-item[1], item[0])
        )[:4]
    ]
    return {
        "role_identity": role_identity,
        "archetype_contract": {
            "label": archetype["label"],
            "professional_headline": archetype["professional_headline"],
            "executive_summary_style": archetype["executive_summary_style"],
            "section_order": archetype["section_order"],
            "section_labels": archetype["section_labels"],
            "evidence_priorities": archetype["evidence_priorities"],
            "technical_depth": archetype["technical_depth"],
            "commercial_emphasis": archetype["commercial_emphasis"],
            "leadership_emphasis": archetype["leadership_emphasis"],
            "stakeholder_language": archetype["stakeholder_language"],
            "preferred_verbs": archetype["preferred_verbs"],
            "bullet_style": archetype["bullet_style"],
            "project_importance": archetype["project_importance"],
            "skills_taxonomy": archetype["skills_taxonomy"],
            "layout_variant": archetype["layout_variant"],
        },
        "page_strategy": {
            "recommended_page_length": role_identity["recommended_page_length"],
            "maximum_pages": role_identity["recommended_page_length"],
            "rationale": role_identity["page_length_rationale"],
        },
        "bullet_strategy": {
            "optimise_for": optimise_for,
            "preferred_verbs": archetype["preferred_verbs"],
            "style": archetype["bullet_style"],
        },
        "ranked_evidence": ranked,
        "signature_candidates": ranked[:5],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify role identity and rank evidence before CV generation")
    parser.add_argument("role_json")
    parser.add_argument("evidence_json")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    role = json.loads(Path(args.role_json).read_text(encoding="utf-8"))
    evidence = json.loads(Path(args.evidence_json).read_text(encoding="utf-8"))
    try:
        result = build_positioning_brief(role, evidence)
    except (KeyError, ValueError) as exc:
        print(f"POSITIONING PIPELINE BLOCKED: {exc}")
        return 2
    Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"POSITIONING BRIEF CLEAN: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
