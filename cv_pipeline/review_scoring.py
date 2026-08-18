#!/usr/bin/env python3
"""Scoring and adversarial review contracts for the JobHuntAI three-reviewer panel."""
from __future__ import annotations

from typing import Any

PANEL_MIN_SCORE = 88.0
SCORE_TOLERANCE = 0.11

# v4 deliberately makes Defensibility harder than the other lanes. A factual-quality
# score and a blocking integrity gate are separate concepts: a single bad claim can
# block release without pretending the whole document has a quality score of zero.
LANE_MIN_SCORES: dict[str, float] = {
    "completeness": 85.0,
    "defensibility": 90.0,
    "competitiveness": 85.0,
}

LANE_RUBRICS: dict[str, dict[str, int]] = {
    "completeness": {
        "identity_coherence": 10,
        "evidence_coverage": 30,
        "block_depth_weighting": 15,
        "evidence_selection_omission": 25,
        "recruiter_comprehension": 20,
    },
    "defensibility": {
        "titles_dates_chronology": 10,
        "metrics_tools_provenance": 20,
        "metric_scope_context": 25,
        "inference_attribution": 25,
        "independent_practice_project_truth": 15,
        "rendered_source_parity": 5,
    },
    "competitiveness": {
        "buying_intent_alignment": 20,
        "proof_strength_vs_competitor": 20,
        "evidence_selection_omission": 20,
        "ten_second_identity_hierarchy": 15,
        "visual_scanability_pagination": 15,
        "readability_cta_links": 10,
    },
}

# v3 remains readable for historical packs.
V3_LANE_MIN_SCORE = 85.0
V3_LANE_RUBRICS: dict[str, dict[str, int]] = {
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

INTEGRITY_CHECKS = (
    "metric_scope_preserved",
    "inference_integrity",
    "cross_document_consistency",
    "generalisation_boundaries",
    "attribution_integrity",
)
BUYING_INTENT_VALUES = {"yes", "mostly", "partly", "no"}
CEILING_VALUES = {"none", "document", "candidate", "mixed"}
SPEND_VALUES = {"worth_a_slot", "low_priority", "do_not_apply"}


class ReviewScoreError(ValueError):
    pass


def score_band(score: float) -> str:
    if score >= 95:
        return "exceptional"
    if score >= 90:
        return "excellent"
    if score >= 85:
        return "strong"
    if score >= 75:
        return "revision_required"
    if score >= 60:
        return "material_weakness"
    return "weak"


def lane_minimum(lane: str, rubric_version: str = "v4") -> float:
    if rubric_version == "v3":
        return V3_LANE_MIN_SCORE
    try:
        return LANE_MIN_SCORES[lane]
    except KeyError as exc:
        raise ReviewScoreError(f"unsupported review lane: {lane!r}") from exc


def rubric_for(lane: str, rubric_version: str = "v4") -> dict[str, int]:
    rubrics = V3_LANE_RUBRICS if rubric_version == "v3" else LANE_RUBRICS
    if lane not in rubrics:
        raise ReviewScoreError(f"unsupported review lane: {lane!r}")
    return rubrics[lane]


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReviewScoreError(f"{label} must be numeric")
    return round(float(value), 1)


def _required_text(value: Any, label: str, minimum: int = 30) -> str:
    text = str(value or "").strip()
    if len(text) < minimum:
        raise ReviewScoreError(f"{label} must contain a specific evidence-based explanation")
    return text


def normalise_review_score(
    report: dict[str, Any], lane: str, rubric_version: str = "v4"
) -> dict[str, Any]:
    rubric = rubric_for(lane, rubric_version)
    score = _number(report.get("score"), "score")
    if not 0 <= score <= 100:
        raise ReviewScoreError("score must be between 0 and 100")

    raw_breakdown = report.get("score_breakdown")
    if not isinstance(raw_breakdown, dict):
        raise ReviewScoreError("score_breakdown must be an object")
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

    rationale = _required_text(report.get("score_rationale"), "score_rationale")
    return {
        "score": score,
        "score_band": score_band(score),
        "score_breakdown": breakdown,
        "score_rationale": rationale,
    }


def normalise_integrity_checks(report: dict[str, Any]) -> dict[str, Any]:
    raw = report.get("integrity_checks")
    if not isinstance(raw, dict):
        raise ReviewScoreError("defensibility report requires integrity_checks")
    missing = sorted(set(INTEGRITY_CHECKS) - set(raw))
    extra = sorted(set(raw) - set(INTEGRITY_CHECKS))
    if missing:
        raise ReviewScoreError("integrity_checks is missing: " + ", ".join(missing))
    if extra:
        raise ReviewScoreError("integrity_checks contains unsupported checks: " + ", ".join(extra))

    checks: dict[str, bool] = {}
    for key in INTEGRITY_CHECKS:
        if not isinstance(raw[key], bool):
            raise ReviewScoreError(f"integrity_checks.{key} must be boolean")
        checks[key] = raw[key]
    rationale = _required_text(report.get("integrity_rationale"), "integrity_rationale", 40)
    return {"integrity_checks": checks, "integrity_rationale": rationale}


def normalise_buying_intent(report: dict[str, Any]) -> dict[str, Any]:
    raw = report.get("buying_intent")
    if not isinstance(raw, dict):
        raise ReviewScoreError("competitiveness report requires buying_intent")

    verdict = str(raw.get("verdict", "")).strip().lower()
    ceiling = str(raw.get("ceiling", "")).strip().lower()
    spend = str(raw.get("spend_recommendation", "")).strip().lower()
    if verdict not in BUYING_INTENT_VALUES:
        raise ReviewScoreError("buying_intent.verdict must be yes, mostly, partly or no")
    if ceiling not in CEILING_VALUES:
        raise ReviewScoreError("buying_intent.ceiling must be none, document, candidate or mixed")
    if spend not in SPEND_VALUES:
        raise ReviewScoreError(
            "buying_intent.spend_recommendation must be worth_a_slot, low_priority or do_not_apply"
        )
    if verdict in {"partly", "no"} and ceiling == "none":
        raise ReviewScoreError("partly/no buying intent requires a document, candidate or mixed ceiling")

    booleans: dict[str, bool] = {}
    for key in ("strong_candidate", "strong_document", "strong_fit", "strong_shortlist"):
        value = raw.get(key)
        if not isinstance(value, bool):
            raise ReviewScoreError(f"buying_intent.{key} must be boolean")
        booleans[key] = value
    if verdict in {"partly", "no"} and booleans["strong_shortlist"]:
        raise ReviewScoreError("buying_intent strong_shortlist cannot be true when verdict is partly/no")

    competitor = _required_text(raw.get("realistic_competitor"), "buying_intent.realistic_competitor", 50)
    rejection = _required_text(raw.get("likely_rejection_reason"), "buying_intent.likely_rejection_reason", 25)
    rationale = _required_text(raw.get("rationale"), "buying_intent.rationale", 60)
    return {
        "buying_intent": {
            "verdict": verdict,
            "ceiling": ceiling,
            "spend_recommendation": spend,
            "realistic_competitor": competitor,
            "likely_rejection_reason": rejection,
            "rationale": rationale,
            **booleans,
        }
    }


def normalise_v4_extensions(report: dict[str, Any], lane: str) -> dict[str, Any]:
    if lane == "defensibility":
        return normalise_integrity_checks(report)
    if lane == "competitiveness":
        return normalise_buying_intent(report)
    if lane == "completeness":
        selection = report.get("selection_audit")
        if not isinstance(selection, dict):
            raise ReviewScoreError("completeness report requires selection_audit")
        risk = str(selection.get("risk", "")).strip().lower()
        if risk not in {"none", "minor", "material"}:
            raise ReviewScoreError("selection_audit.risk must be none, minor or material")
        strongest = str(selection.get("strongest_unused_evidence", "")).strip()
        rationale = _required_text(selection.get("rationale"), "selection_audit.rationale", 40)
        return {
            "selection_audit": {
                "risk": risk,
                "strongest_unused_evidence": strongest or "none",
                "rationale": rationale,
            }
        }
    raise ReviewScoreError(f"unsupported review lane: {lane!r}")


def weakest_dimensions(
    lane: str, breakdown: dict[str, Any], limit: int = 2, rubric_version: str = "v4"
) -> list[str]:
    rubric = rubric_for(lane, rubric_version)
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
