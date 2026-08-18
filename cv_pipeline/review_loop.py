#!/usr/bin/env python3
"""Fail-closed Tailor -> adversarial three-reviewer panel -> re-tailor state machine."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import review_scoring

CONTRACT = "jobhuntai-review-panel-v4"
PANEL_V3_CONTRACT = "jobhuntai-review-panel-v3"
PANEL_V2_CONTRACT = "jobhuntai-review-panel-v2"
LEGACY_CONTRACT = "jobhuntai-tailor-review-v1"
SCORED_CONTRACTS = {CONTRACT, PANEL_V3_CONTRACT}
PANEL_CONTRACTS = SCORED_CONTRACTS | {PANEL_V2_CONTRACT}
APPROVE = "approve"
REVISE = "revise"
REVIEW_LANES = ("completeness", "defensibility", "competitiveness")
BLOCKING_SEVERITIES = {"critical", "major"}


class ReviewLoopError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ReviewLoopError(f"{path} must contain a JSON object")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _v4_score_policy() -> dict[str, Any]:
    return {
        "lane_minimums": dict(review_scoring.LANE_MIN_SCORES),
        "panel_minimum": review_scoring.PANEL_MIN_SCORE,
        "shortlist_buying_intent": ["yes", "mostly"],
    }


def create_state(job_id: str, max_iterations: int = 4) -> dict[str, Any]:
    if not job_id.strip():
        raise ReviewLoopError("job_id is required")
    if max_iterations < 1:
        raise ReviewLoopError("max_iterations must be at least 1")
    now = utc_now()
    return {
        "contract": CONTRACT,
        "job_id": job_id,
        "status": "awaiting_tailor",
        "current_iteration": 0,
        "max_iterations": max_iterations,
        "required_review_lanes": list(REVIEW_LANES),
        "score_policy": _v4_score_policy(),
        "approved_cv_sha256": None,
        "events": [],
        "created_at": now,
        "updated_at": now,
    }


def _events(state: dict[str, Any]) -> list[dict[str, Any]]:
    events = state.get("events")
    if not isinstance(events, list):
        raise ReviewLoopError("events must be a list")
    return events


def _latest_event(state: dict[str, Any], event_type: str) -> dict[str, Any] | None:
    for event in reversed(_events(state)):
        if event.get("type") == event_type:
            return event
    return None


def _latest_tailor(state: dict[str, Any]) -> dict[str, Any] | None:
    return _latest_event(state, "tailor")


def _reviews_for_iteration(state: dict[str, Any], iteration: int) -> list[dict[str, Any]]:
    return [
        item
        for item in _events(state)
        if item.get("type") == "review" and item.get("iteration") == iteration
    ]


def _latest_panel(state: dict[str, Any]) -> dict[str, Any] | None:
    return _latest_event(state, "panel")


def _open_issues(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for review in reviews:
        lane = str(review.get("lane", ""))
        for issue in review.get("issues", []) or []:
            if not isinstance(issue, dict) or issue.get("status", "open") == "closed":
                continue
            enriched = dict(issue)
            enriched["lane"] = lane
            out.append(enriched)
    return out


def _blocking_open_issues(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        issue
        for issue in _open_issues(reviews)
        if issue.get("severity") in BLOCKING_SEVERITIES
    ]


def _required_issue_ids_for_retailor(state: dict[str, Any]) -> set[str]:
    panel = _latest_panel(state)
    if not panel or panel.get("verdict") != REVISE:
        return set()
    return {
        str(issue["id"])
        for issue in panel.get("blocking_issues", []) or []
        if isinstance(issue, dict) and issue.get("id")
    }


def validate_state_shape(state: dict[str, Any]) -> None:
    contract = state.get("contract")
    if contract not in PANEL_CONTRACTS | {LEGACY_CONTRACT}:
        raise ReviewLoopError(f"unsupported review-loop contract: {contract!r}")
    allowed = {
        "awaiting_tailor",
        "awaiting_review",
        "awaiting_reviews",
        "revision_required",
        "approved",
        "blocked",
    }
    if state.get("status") not in allowed:
        raise ReviewLoopError(f"invalid review-loop status: {state.get('status')!r}")
    if not isinstance(state.get("current_iteration"), int) or state["current_iteration"] < 0:
        raise ReviewLoopError("current_iteration must be a non-negative integer")
    if not isinstance(state.get("max_iterations"), int) or state["max_iterations"] < 1:
        raise ReviewLoopError("max_iterations must be a positive integer")
    if contract in PANEL_CONTRACTS and state.get("required_review_lanes") != list(REVIEW_LANES):
        raise ReviewLoopError(f"required_review_lanes must be {list(REVIEW_LANES)!r}")
    if contract == CONTRACT and state.get("score_policy") != _v4_score_policy():
        raise ReviewLoopError(f"score_policy must be {_v4_score_policy()!r}")
    if contract == PANEL_V3_CONTRACT:
        expected_v3 = {
            "lane_minimum": review_scoring.V3_LANE_MIN_SCORE,
            "panel_minimum": review_scoring.PANEL_MIN_SCORE,
        }
        if state.get("score_policy") != expected_v3:
            raise ReviewLoopError(f"score_policy must be {expected_v3!r}")
    _events(state)


def record_tailor(
    state: dict[str, Any],
    cv_path: Path,
    actor: str,
    addressed_issue_ids: list[str] | None = None,
) -> dict[str, Any]:
    validate_state_shape(state)
    actor = actor.strip()
    if not actor:
        raise ReviewLoopError("tailor actor is required")
    if state["status"] not in {"awaiting_tailor", "revision_required"}:
        raise ReviewLoopError(f"tailor is not allowed while status is {state['status']}")
    if not cv_path.is_file():
        raise ReviewLoopError(f"CV payload not found: {cv_path}")
    if state["current_iteration"] >= state["max_iterations"]:
        state["status"] = "blocked"
        state["updated_at"] = utc_now()
        raise ReviewLoopError("maximum tailor-review iterations reached")

    addressed = {item for item in (addressed_issue_ids or []) if item}
    if state["status"] == "revision_required":
        required = _required_issue_ids_for_retailor(state)
        if not required and state.get("contract") == LEGACY_CONTRACT:
            latest_review = _latest_event(state, "review") or {}
            required = {
                str(issue["id"])
                for issue in latest_review.get("issues", []) or []
                if isinstance(issue, dict)
                and issue.get("status", "open") != "closed"
                and issue.get("id")
            }
        missing = sorted(required - addressed)
        if missing:
            raise ReviewLoopError(
                "re-tailor must address every blocking review issue: " + ", ".join(missing)
            )

    iteration = state["current_iteration"] + 1
    event = {
        "type": "tailor",
        "iteration": iteration,
        "actor": actor,
        "cv_path": str(cv_path),
        "cv_sha256": sha256_file(cv_path),
        "addressed_issue_ids": sorted(addressed),
        "timestamp": utc_now(),
    }
    _events(state).append(event)
    state["current_iteration"] = iteration
    state["status"] = "awaiting_reviews" if state.get("contract") in PANEL_CONTRACTS else "awaiting_review"
    state["approved_cv_sha256"] = None
    state["updated_at"] = event["timestamp"]
    return state


def _normalise_issues(report: dict[str, Any]) -> list[dict[str, Any]]:
    raw = report.get("issues", [])
    if not isinstance(raw, list):
        raise ReviewLoopError("review issues must be a list")
    issues: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, issue in enumerate(raw, start=1):
        if not isinstance(issue, dict):
            raise ReviewLoopError(f"review issue {index} must be an object")
        issue_id = str(issue.get("id", "")).strip()
        if not issue_id:
            raise ReviewLoopError(f"review issue {index} requires an id")
        if issue_id in seen:
            raise ReviewLoopError(f"duplicate review issue id: {issue_id}")
        seen.add(issue_id)
        status = issue.get("status", "open")
        severity = issue.get("severity", "major")
        if status not in {"open", "closed"}:
            raise ReviewLoopError(f"invalid status for review issue {issue_id}: {status}")
        if severity not in {"critical", "major", "minor"}:
            raise ReviewLoopError(f"invalid severity for review issue {issue_id}: {severity}")
        message = str(issue.get("message", "")).strip()
        action = str(issue.get("required_action", "")).strip()
        if not message or not action:
            raise ReviewLoopError(f"review issue {issue_id} requires message and required_action")
        issues.append(
            {
                "id": issue_id,
                "severity": severity,
                "status": status,
                "message": message,
                "required_action": action,
            }
        )
    return issues


def _rubric_version(contract: str) -> str:
    return "v4" if contract == CONTRACT else "v3"


def _score_blocking_issues(
    reviews: list[dict[str, Any]], rubric_version: str
) -> tuple[list[dict[str, Any]], float]:
    calculated_panel_score = review_scoring.panel_score(reviews)
    issues: list[dict[str, Any]] = []
    for review in reviews:
        lane = str(review.get("lane", ""))
        score = float(review.get("score", 0))
        minimum = review_scoring.lane_minimum(lane, rubric_version)
        if score < minimum:
            weak = review_scoring.weakest_dimensions(
                lane,
                review.get("score_breakdown", {}),
                rubric_version=rubric_version,
            )
            issues.append(
                {
                    "id": f"SCORE-{lane.upper()}",
                    "severity": "major",
                    "status": "open",
                    "lane": lane,
                    "message": (
                        f"{lane} reviewer scored the CV {score:.1f}/100, below the "
                        f"{minimum:.0f}/100 lane release floor"
                    ),
                    "required_action": "Improve the weakest scoring dimensions: " + ", ".join(weak),
                }
            )
    if not issues and calculated_panel_score < review_scoring.PANEL_MIN_SCORE:
        issues.append(
            {
                "id": "SCORE-PANEL",
                "severity": "major",
                "status": "open",
                "lane": "panel",
                "message": (
                    f"panel average is {calculated_panel_score:.1f}/100, below the "
                    f"{review_scoring.PANEL_MIN_SCORE:.0f}/100 release floor"
                ),
                "required_action": (
                    "Raise overall quality by improving the lowest-scoring reviewer dimensions before release"
                ),
            }
        )
    return issues, calculated_panel_score


def _v4_policy_issues(reviews: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blocking: list[dict[str, Any]] = []
    structural: list[dict[str, Any]] = []
    by_lane = {str(item.get("lane", "")): item for item in reviews}

    completeness = by_lane.get("completeness", {})
    selection = completeness.get("selection_audit", {})
    if selection.get("risk") == "material":
        blocking.append(
            {
                "id": "SELECTION-MATERIAL-OMISSION",
                "severity": "major",
                "status": "open",
                "lane": "completeness",
                "message": "Completeness reviewer found a material evidence-selection or omission loss",
                "required_action": (
                    "Reallocate evidence using the strongest unused role-relevant proof before release"
                ),
            }
        )

    defensibility = by_lane.get("defensibility", {})
    checks = defensibility.get("integrity_checks", {})
    for key in review_scoring.INTEGRITY_CHECKS:
        if checks.get(key) is False:
            blocking.append(
                {
                    "id": f"INTEGRITY-{key.upper().replace('_', '-')}",
                    "severity": "major",
                    "status": "open",
                    "lane": "defensibility",
                    "message": f"Defensibility integrity check failed: {key}",
                    "required_action": (
                        "Correct the claim semantics, scope or attribution and rerun the full cold panel"
                    ),
                }
            )

    competitiveness = by_lane.get("competitiveness", {})
    buying = competitiveness.get("buying_intent", {})
    verdict = buying.get("verdict")
    ceiling = buying.get("ceiling")
    if verdict in {"partly", "no"}:
        risk = {
            "id": "BUYING-INTENT",
            "verdict": verdict,
            "ceiling": ceiling,
            "strong_candidate": buying.get("strong_candidate"),
            "strong_document": buying.get("strong_document"),
            "strong_fit": buying.get("strong_fit"),
            "strong_shortlist": buying.get("strong_shortlist"),
            "spend_recommendation": buying.get("spend_recommendation"),
            "likely_rejection_reason": buying.get("likely_rejection_reason"),
            "rationale": buying.get("rationale"),
        }
        if ceiling in {"document", "mixed"}:
            blocking.append(
                {
                    "id": "BUYING-INTENT-DOCUMENT",
                    "severity": "major",
                    "status": "open",
                    "lane": "competitiveness",
                    "message": (
                        f"Employer buying intent is only {verdict} and the reviewer says document execution contributes to the ceiling"
                    ),
                    "required_action": (
                        "Rebuild the hiring argument around what the employer is actually buying; fix evidence selection, ordering or framing before release"
                    ),
                }
            )
        else:
            structural.append(risk)
    return blocking, structural


def _aggregate_panel(state: dict[str, Any], tailor_event: dict[str, Any]) -> None:
    iteration = int(tailor_event["iteration"])
    reviews = _reviews_for_iteration(state, iteration)
    lanes = {str(item.get("lane", "")) for item in reviews}
    if lanes != set(REVIEW_LANES):
        state["status"] = "awaiting_reviews"
        state["updated_at"] = utc_now()
        return

    all_open = _open_issues(reviews)
    required_by_id = {
        str(issue["id"]): issue
        for issue in _blocking_open_issues(reviews)
        if issue.get("id")
    }
    revise_lanes = {
        str(review.get("lane", ""))
        for review in reviews
        if review.get("verdict") == REVISE
    }
    for issue in all_open:
        if issue.get("lane") in revise_lanes and issue.get("id"):
            required_by_id[str(issue["id"])] = issue

    lane_scores: dict[str, float] | None = None
    calculated_panel_score: float | None = None
    structural_risks: list[dict[str, Any]] = []
    if state.get("contract") in SCORED_CONTRACTS:
        version = _rubric_version(str(state.get("contract")))
        score_issues, calculated_panel_score = _score_blocking_issues(reviews, version)
        for issue in score_issues:
            required_by_id[str(issue["id"])] = issue
        lane_scores = {str(item["lane"]): float(item["score"]) for item in reviews}
        if state.get("contract") == CONTRACT:
            policy_issues, structural_risks = _v4_policy_issues(reviews)
            for issue in policy_issues:
                required_by_id[str(issue["id"])] = issue

    blocking = list(required_by_id.values())
    reviewer_revise = bool(revise_lanes)
    verdict = REVISE if blocking or reviewer_revise else APPROVE
    blocking_ids = set(required_by_id)
    panel_event: dict[str, Any] = {
        "type": "panel",
        "iteration": iteration,
        "cv_sha256": tailor_event["cv_sha256"],
        "verdict": verdict,
        "review_lanes": list(REVIEW_LANES),
        "review_actors": {str(item["lane"]): str(item["actor"]) for item in reviews},
        "blocking_issues": blocking,
        "minor_open_issues": [
            issue
            for issue in all_open
            if issue.get("severity") == "minor"
            and str(issue.get("id", "")) not in blocking_ids
        ],
        "timestamp": utc_now(),
    }
    if lane_scores is not None and calculated_panel_score is not None:
        if state.get("contract") == CONTRACT:
            score_policy = _v4_score_policy()
        else:
            score_policy = {
                "lane_minimum": review_scoring.V3_LANE_MIN_SCORE,
                "panel_minimum": review_scoring.PANEL_MIN_SCORE,
            }
        panel_event.update(
            {
                "lane_scores": lane_scores,
                "panel_score": calculated_panel_score,
                "score_policy": score_policy,
            }
        )
    if state.get("contract") == CONTRACT:
        competitiveness = next(item for item in reviews if item.get("lane") == "competitiveness")
        buying = dict(competitiveness.get("buying_intent", {}))
        shortlist_certified = bool(
            verdict == APPROVE
            and buying.get("verdict") in {"yes", "mostly"}
            and buying.get("strong_shortlist") is True
        )
        panel_event.update(
            {
                "buying_intent": buying,
                "shortlist_certified": shortlist_certified,
                "structural_risks": structural_risks,
                "application_release_approved": verdict == APPROVE,
            }
        )
    _events(state).append(panel_event)
    state["status"] = "approved" if verdict == APPROVE else "revision_required"
    state["approved_cv_sha256"] = tailor_event["cv_sha256"] if verdict == APPROVE else None
    state["updated_at"] = panel_event["timestamp"]


def record_review(
    state: dict[str, Any], report: dict[str, Any], actor: str, lane: str | None = None
) -> dict[str, Any]:
    validate_state_shape(state)
    actor = actor.strip()
    if not actor:
        raise ReviewLoopError("reviewer actor is required")
    if state.get("contract") == LEGACY_CONTRACT:
        return _record_legacy_review(state, report, actor)

    lane = str(lane or report.get("lane", "")).strip().lower()
    if lane not in REVIEW_LANES:
        raise ReviewLoopError(f"review lane must be one of: {', '.join(REVIEW_LANES)}")
    if state["status"] != "awaiting_reviews":
        raise ReviewLoopError(f"review is not allowed while status is {state['status']}")

    tailor_event = _latest_tailor(state)
    if not tailor_event:
        raise ReviewLoopError("review requires a preceding tailor event")
    if tailor_event.get("actor") == actor:
        raise ReviewLoopError("reviewer must be independent from the tailor actor")
    iteration_reviews = _reviews_for_iteration(state, int(tailor_event["iteration"]))
    if any(item.get("lane") == lane for item in iteration_reviews):
        raise ReviewLoopError(f"review lane {lane!r} already submitted for this iteration")
    if any(item.get("actor") == actor for item in iteration_reviews):
        raise ReviewLoopError("each review lane requires a distinct reviewer actor")

    verdict = str(report.get("verdict", "")).lower().strip()
    if verdict not in {APPROVE, REVISE}:
        raise ReviewLoopError("review verdict must be approve or revise")
    reviewed_hash = str(report.get("cv_sha256", "")).strip()
    if reviewed_hash != tailor_event.get("cv_sha256"):
        raise ReviewLoopError("review report does not match the latest tailored CV hash")

    scoring: dict[str, Any] = {}
    extensions: dict[str, Any] = {}
    if state.get("contract") in SCORED_CONTRACTS:
        version = _rubric_version(str(state.get("contract")))
        try:
            scoring = review_scoring.normalise_review_score(report, lane, version)
            if state.get("contract") == CONTRACT:
                extensions = review_scoring.normalise_v4_extensions(report, lane)
        except review_scoring.ReviewScoreError as exc:
            raise ReviewLoopError(str(exc)) from exc

    issues = _normalise_issues(report)
    blocking_open = [
        issue
        for issue in issues
        if issue["status"] != "closed" and issue["severity"] in BLOCKING_SEVERITIES
    ]
    if verdict == APPROVE and blocking_open:
        raise ReviewLoopError("approval cannot contain open critical or major review issues")
    if verdict == REVISE and not [issue for issue in issues if issue["status"] != "closed"]:
        raise ReviewLoopError("revision verdict requires at least one open issue")

    event: dict[str, Any] = {
        "type": "review",
        "lane": lane,
        "iteration": tailor_event["iteration"],
        "actor": actor,
        "cv_sha256": reviewed_hash,
        "verdict": verdict,
        "issues": issues,
        "summary": str(report.get("summary", "")).strip(),
        "timestamp": utc_now(),
    }
    event.update(scoring)
    event.update(extensions)
    _events(state).append(event)
    _aggregate_panel(state, tailor_event)
    return state


def _record_legacy_review(state: dict[str, Any], report: dict[str, Any], actor: str) -> dict[str, Any]:
    if state["status"] != "awaiting_review":
        raise ReviewLoopError(f"review is not allowed while status is {state['status']}")
    tailor_event = _latest_tailor(state)
    if not tailor_event:
        raise ReviewLoopError("review requires a preceding tailor event")
    if tailor_event.get("actor") == actor:
        raise ReviewLoopError("reviewer must be independent from the tailor actor")

    verdict = str(report.get("verdict", "")).lower().strip()
    if verdict not in {APPROVE, REVISE}:
        raise ReviewLoopError("review verdict must be approve or revise")
    reviewed_hash = str(report.get("cv_sha256", "")).strip()
    if reviewed_hash != tailor_event.get("cv_sha256"):
        raise ReviewLoopError("review report does not match the latest tailored CV hash")
    issues = _normalise_issues(report)
    open_issues = [issue for issue in issues if issue["status"] != "closed"]
    if verdict == APPROVE and open_issues:
        raise ReviewLoopError("approval cannot contain open review issues")
    if verdict == REVISE and not open_issues:
        raise ReviewLoopError("revision verdict requires at least one open issue")

    event = {
        "type": "review",
        "iteration": tailor_event["iteration"],
        "actor": actor,
        "cv_sha256": reviewed_hash,
        "verdict": verdict,
        "issues": issues,
        "summary": str(report.get("summary", "")).strip(),
        "timestamp": utc_now(),
    }
    _events(state).append(event)
    state["status"] = "approved" if verdict == APPROVE else "revision_required"
    state["approved_cv_sha256"] = reviewed_hash if verdict == APPROVE else None
    state["updated_at"] = event["timestamp"]
    return state


def latest_review_for_lane(state: dict[str, Any], lane: str) -> dict[str, Any] | None:
    lane = lane.strip().lower()
    tailor = _latest_tailor(state)
    if not tailor:
        return None
    for event in reversed(_events(state)):
        if (
            event.get("type") == "review"
            and event.get("iteration") == tailor.get("iteration")
            and event.get("lane") == lane
        ):
            return event
    return None


def verify_release(state: dict[str, Any], cv_path: Path) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    try:
        validate_state_shape(state)
    except ReviewLoopError as exc:
        return [{"code": "REVIEW_LOOP_INVALID", "message": str(exc)}]
    if state.get("contract") == LEGACY_CONTRACT:
        return _verify_legacy_release(state, cv_path)

    tailor = _latest_tailor(state)
    if not tailor:
        failures.append({"code": "TAILOR_MISSING", "message": "no tailor event recorded"})
    if state.get("status") != "approved":
        failures.append(
            {
                "code": "REVIEW_PANEL_NOT_APPROVED",
                "message": f"review-panel status is {state.get('status')}",
            }
        )
    if not cv_path.is_file():
        failures.append(
            {"code": "FINAL_CV_MISSING", "message": f"final CV payload not found: {cv_path}"}
        )
        return failures

    final_hash = sha256_file(cv_path)
    if state.get("approved_cv_sha256") != final_hash:
        failures.append(
            {
                "code": "APPROVED_HASH_STALE",
                "message": "final CV differs from the panel-approved revision",
            }
        )
    if not tailor:
        return failures

    iteration = int(tailor["iteration"])
    reviews = _reviews_for_iteration(state, iteration)
    by_lane = {str(item.get("lane", "")): item for item in reviews}
    missing = [lane for lane in REVIEW_LANES if lane not in by_lane]
    if missing:
        failures.append(
            {
                "code": "REVIEW_PANEL_INCOMPLETE",
                "message": "missing review lanes: " + ", ".join(missing),
            }
        )
    actors = [str(item.get("actor", "")) for item in reviews]
    if len(set(actors)) != len(actors):
        failures.append(
            {
                "code": "REVIEWER_ACTOR_REUSED",
                "message": "review lanes must use distinct reviewer actors",
            }
        )
    if tailor.get("actor") in actors:
        failures.append(
            {
                "code": "REVIEW_NOT_INDEPENDENT",
                "message": "tailor actor cannot review the same revision",
            }
        )

    for lane, review in by_lane.items():
        if review.get("cv_sha256") != tailor.get("cv_sha256"):
            failures.append(
                {
                    "code": "REVIEWED_HASH_MISMATCH",
                    "message": f"{lane} review is not tied to the latest tailored CV",
                }
            )
        if state.get("contract") in SCORED_CONTRACTS:
            version = _rubric_version(str(state.get("contract")))
            try:
                scored = review_scoring.normalise_review_score(review, lane, version)
                minimum = review_scoring.lane_minimum(lane, version)
                if scored["score"] < minimum:
                    failures.append(
                        {
                            "code": "REVIEW_LANE_SCORE_BELOW_FLOOR",
                            "message": f"{lane} score {scored['score']:.1f} is below {minimum:.0f}",
                        }
                    )
                if state.get("contract") == CONTRACT:
                    review_scoring.normalise_v4_extensions(review, lane)
            except review_scoring.ReviewScoreError as exc:
                failures.append({"code": "REVIEW_SCORE_INVALID", "message": f"{lane}: {exc}"})

    panel = _latest_panel(state)
    if not panel or panel.get("iteration") != iteration:
        failures.append(
            {
                "code": "REVIEW_PANEL_AGGREGATION_MISSING",
                "message": "latest review panel has not been aggregated",
            }
        )
    else:
        if panel.get("verdict") != APPROVE:
            failures.append(
                {
                    "code": "REVIEW_PANEL_REQUIRES_REVISION",
                    "message": "latest review panel did not approve release",
                }
            )
        if panel.get("cv_sha256") != tailor.get("cv_sha256"):
            failures.append(
                {
                    "code": "REVIEW_PANEL_HASH_MISMATCH",
                    "message": "panel approval is not tied to the latest CV hash",
                }
            )
        if panel.get("blocking_issues"):
            failures.append(
                {
                    "code": "OPEN_BLOCKING_REVIEW_ISSUES",
                    "message": "latest panel still contains open required review issues",
                }
            )
        if state.get("contract") in SCORED_CONTRACTS and len(by_lane) == len(REVIEW_LANES):
            expected_lane_scores = {
                lane: float(by_lane[lane].get("score", -1)) for lane in REVIEW_LANES
            }
            expected_panel_score = review_scoring.panel_score(list(by_lane.values()))
            if panel.get("lane_scores") != expected_lane_scores:
                failures.append(
                    {
                        "code": "REVIEW_PANEL_SCORE_MISMATCH",
                        "message": "panel lane scores do not match current reviewer events",
                    }
                )
            try:
                recorded_panel_score = float(panel.get("panel_score"))
            except (TypeError, ValueError):
                recorded_panel_score = -1
            if abs(recorded_panel_score - expected_panel_score) > review_scoring.SCORE_TOLERANCE:
                failures.append(
                    {
                        "code": "REVIEW_PANEL_SCORE_MISMATCH",
                        "message": "panel average does not match current reviewer scores",
                    }
                )
            if expected_panel_score < review_scoring.PANEL_MIN_SCORE:
                failures.append(
                    {
                        "code": "REVIEW_PANEL_SCORE_BELOW_FLOOR",
                        "message": (
                            f"panel score {expected_panel_score:.1f} is below "
                            f"{review_scoring.PANEL_MIN_SCORE:.0f}"
                        ),
                    }
                )
        if state.get("contract") == CONTRACT:
            if panel.get("application_release_approved") is not True:
                failures.append(
                    {
                        "code": "V4_APPLICATION_RELEASE_NOT_APPROVED",
                        "message": "v4 panel did not approve application release",
                    }
                )
            if "shortlist_certified" not in panel or "buying_intent" not in panel:
                failures.append(
                    {
                        "code": "V4_BUYING_INTENT_MISSING",
                        "message": "v4 panel is missing buying-intent/shortlist certification",
                    }
                )
    return failures


def _verify_legacy_release(state: dict[str, Any], cv_path: Path) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    events = _events(state)
    tailors = [event for event in events if event.get("type") == "tailor"]
    reviews = [event for event in events if event.get("type") == "review"]
    if not tailors:
        failures.append({"code": "TAILOR_MISSING", "message": "no tailor event recorded"})
    if not reviews:
        failures.append(
            {"code": "REVIEW_MISSING", "message": "no independent review event recorded"}
        )
    if state.get("status") != "approved":
        failures.append(
            {
                "code": "REVIEW_NOT_APPROVED",
                "message": f"review-loop status is {state.get('status')}",
            }
        )
    if not cv_path.is_file():
        failures.append(
            {"code": "FINAL_CV_MISSING", "message": f"final CV payload not found: {cv_path}"}
        )
        return failures

    final_hash = sha256_file(cv_path)
    if state.get("approved_cv_sha256") != final_hash:
        failures.append(
            {
                "code": "APPROVED_HASH_STALE",
                "message": "final CV differs from the independently approved revision",
            }
        )
    if tailors and reviews:
        latest_tailor, latest_review = tailors[-1], reviews[-1]
        if latest_review.get("iteration") != latest_tailor.get("iteration"):
            failures.append(
                {
                    "code": "LATEST_REVISION_UNREVIEWED",
                    "message": "latest tailor revision has not been reviewed",
                }
            )
        if latest_review.get("verdict") != APPROVE:
            failures.append(
                {
                    "code": "LATEST_REVIEW_REQUIRES_REVISION",
                    "message": "latest review did not approve release",
                }
            )
        if latest_review.get("actor") == latest_tailor.get("actor"):
            failures.append(
                {
                    "code": "REVIEW_NOT_INDEPENDENT",
                    "message": "latest reviewer and tailor actors are identical",
                }
            )
        if latest_review.get("cv_sha256") != latest_tailor.get("cv_sha256"):
            failures.append(
                {
                    "code": "REVIEWED_HASH_MISMATCH",
                    "message": "latest review is not tied to the latest tailored CV",
                }
            )
    return failures


def _parse_issue_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")
    p.add_argument("state")
    p.add_argument("--job-id", required=True)
    p.add_argument("--max-iterations", type=int, default=4)

    p = sub.add_parser("tailor")
    p.add_argument("state")
    p.add_argument("cv")
    p.add_argument("--actor", required=True)
    p.add_argument("--addressed-issues", default="")

    p = sub.add_parser("review")
    p.add_argument("state")
    p.add_argument("report")
    p.add_argument("--actor", required=True)
    p.add_argument("--lane", choices=REVIEW_LANES)

    p = sub.add_parser("verify")
    p.add_argument("state")
    p.add_argument("cv")
    p.add_argument("--json-out")

    args = parser.parse_args()
    state_path = Path(args.state)
    try:
        if args.command == "init":
            write_json(state_path, create_state(args.job_id, args.max_iterations))
            print(f"REVIEW PANEL INITIALISED: {state_path}")
            return 0

        state = load_json(state_path)
        if args.command == "tailor":
            record_tailor(
                state,
                Path(args.cv),
                args.actor,
                _parse_issue_ids(args.addressed_issues),
            )
            write_json(state_path, state)
            print(f"TAILOR ITERATION {state['current_iteration']} RECORDED")
            return 0
        if args.command == "review":
            record_review(state, load_json(Path(args.report)), args.actor, args.lane)
            write_json(state_path, state)
            print(f"REVIEW PANEL STATUS: {state['status'].upper()}")
            return 0

        failures = verify_release(state, Path(args.cv))
        result: dict[str, Any] = {"passed": not failures, "failures": failures}
        panel = _latest_panel(state)
        if state.get("contract") in SCORED_CONTRACTS and panel:
            result["lane_scores"] = panel.get("lane_scores")
            result["panel_score"] = panel.get("panel_score")
        if state.get("contract") == CONTRACT and panel:
            result["shortlist_certified"] = panel.get("shortlist_certified")
            result["buying_intent"] = panel.get("buying_intent")
            result["structural_risks"] = panel.get("structural_risks", [])
        if args.json_out:
            write_json(Path(args.json_out), result)
        if failures:
            print(json.dumps(result, indent=2))
            return 1
        if state.get("contract") == CONTRACT and panel:
            print(
                "ADVERSARIAL THREE-REVIEWER PANEL APPROVED: "
                f"{float(panel['panel_score']):.1f}/100; "
                f"shortlist_certified={str(bool(panel.get('shortlist_certified'))).lower()}"
            )
        elif state.get("contract") in SCORED_CONTRACTS and panel:
            print(f"SCORED THREE-REVIEWER PANEL APPROVED: {float(panel['panel_score']):.1f}/100")
        else:
            print("THREE-REVIEWER PANEL APPROVED.")
        return 0
    except (OSError, json.JSONDecodeError, ReviewLoopError) as exc:
        if args.command != "init" and "state" in locals() and isinstance(state, dict):
            write_json(state_path, state)
        print(f"REVIEW LOOP FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
