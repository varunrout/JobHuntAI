#!/usr/bin/env python3
"""Fixed scoring rubrics for the JobHuntAI three-reviewer CV panel."""
from __future__ import annotations

from typing import Any

LANE_MIN_SCORE = 85.0
PANEL_MIN_SCORE = 88.0
SCORE_TOLERANCE = 0.11

LANE_RUBRICS: dict[str, dict[str, int]] = {
    "completeness": {
        "identity_coherence": 15,
        "evidence_coverage": 25,
        "block_depth_weighting": 20,
        "omission_page_strategy": 20,
        "recruiter_comprehension": 20,
    },
    "defensibility": {
        "titles_dates_chronology": 15,
        "metrics_tools_provenance": 25,
        "scope_attribution": 25,
        "independent_practice_project_truth": 20,
        "rendered_source_parity": 15,
    },
    "competitiveness": {
        "ten_second_identity": 15,
        "proof_strength_differentiation": 25,
        "evidence_hierarchy": 20,
        "visual_pagination": 25,
        "readability_cta_links": 15,
    },
}


class ReviewScoreError(ValueError):
    pass


def score_band(score: float) -> str:
    if score >= 95:
        return "exceptional"
    if score >= 90:
        return "excellent"
    if score >= LANE_MIN_SCORE:
        return "strong"
    if score >= 75:
        return "revision_required"
    return "weak"


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReviewScoreError(f"{label} must be numeric")
    return round(float(value), 1)


def normalise_review_score(report: dict[str, Any], lane: str) -> dict[str, Any]:
    if lane not in LANE_RUBRICS:
        raise ReviewScoreError(f"unsupported review lane: {lane!r}")
    score = _number(report.get("score"), "score")
    if not 0 <= score <= 100:
        raise ReviewScoreError("score must be between 0 and 100")

    raw_breakdown = report.get("score_breakdown")
    if not isinstance(raw_breakdown, dict):
        raise ReviewScoreError("score_breakdown must be an object")
    rubric = LANE_RUBRICS[lane]
    missing = sorted(set(rubric) - set(raw_breakdown))
    extra = sorted(set(raw_breakdown) - set(rubric))
    if missing:
        raise ReviewScoreError("score_breakdown is missing: " + ", ".join(missing))
    if extra:
        raise ReviewScoreError("score_breakdown contains unsupported dimensions: " + ", ".join(extra))

    breakdown: dict[str, float] = {}
    for dimension, maximum in rubric.items():
        points = _number(raw_breakdown.get(dimension), f"score_breakdown.{dimension}")
        if not 0 <= points <= maximum:
            raise ReviewScoreError(
                f"score_breakdown.{dimension} must be between 0 and {maximum}"
            )
        breakdown[dimension] = points

    calculated = round(sum(breakdown.values()), 1)
    if abs(calculated - score) > SCORE_TOLERANCE:
        raise ReviewScoreError(
            f"score {score:.1f} does not equal score_breakdown total {calculated:.1f}"
        )

    rationale = str(report.get("score_rationale", "")).strip()
    if len(rationale) < 30:
        raise ReviewScoreError("score_rationale must contain a specific evidence-based explanation")

    return {
        "score": score,
        "score_band": score_band(score),
        "score_breakdown": breakdown,
        "score_rationale": rationale,
    }


def weakest_dimensions(lane: str, breakdown: dict[str, Any], limit: int = 2) -> list[str]:
    rubric = LANE_RUBRICS[lane]
    ranked: list[tuple[float, str]] = []
    for dimension, maximum in rubric.items():
        try:
            points = float(breakdown.get(dimension, 0))
        except (TypeError, ValueError):
            points = 0.0
        ranked.append((points / maximum if maximum else 0.0, dimension))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return [dimension for _, dimension in ranked[:limit]]


def panel_score(reviews: list[dict[str, Any]]) -> float:
    if not reviews:
        return 0.0
    return round(sum(float(review.get("score", 0)) for review in reviews) / len(reviews), 1)
