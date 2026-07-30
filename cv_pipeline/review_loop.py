#!/usr/bin/env python3
"""Fail-closed Tailor -> Review -> Re-tailor state machine for JobHuntAI."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTRACT = "jobhuntai-tailor-review-v1"
APPROVE = "approve"
REVISE = "revise"


class ReviewLoopError(ValueError):
    """Raised when an invalid loop transition is attempted."""


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


def _open_issue_ids(review_event: dict[str, Any] | None) -> set[str]:
    if not review_event:
        return set()
    issues = review_event.get("issues", [])
    if not isinstance(issues, list):
        raise ReviewLoopError("review issues must be a list")
    return {
        str(issue["id"])
        for issue in issues
        if isinstance(issue, dict) and issue.get("status", "open") != "closed" and issue.get("id")
    }


def validate_state_shape(state: dict[str, Any]) -> None:
    if state.get("contract") != CONTRACT:
        raise ReviewLoopError(f"unsupported review-loop contract: {state.get('contract')!r}")
    if state.get("status") not in {"awaiting_tailor", "awaiting_review", "revision_required", "approved", "blocked"}:
        raise ReviewLoopError(f"invalid review-loop status: {state.get('status')!r}")
    if not isinstance(state.get("current_iteration"), int) or state["current_iteration"] < 0:
        raise ReviewLoopError("current_iteration must be a non-negative integer")
    if not isinstance(state.get("max_iterations"), int) or state["max_iterations"] < 1:
        raise ReviewLoopError("max_iterations must be a positive integer")
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
        required = _open_issue_ids(_latest_event(state, "review"))
        missing = sorted(required - addressed)
        if missing:
            raise ReviewLoopError("re-tailor must address every open review issue: " + ", ".join(missing))

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
    state["status"] = "awaiting_review"
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
        if status not in {"open", "closed"}:
            raise ReviewLoopError(f"invalid status for review issue {issue_id}: {status}")
        severity = issue.get("severity", "major")
        if severity not in {"critical", "major", "minor"}:
            raise ReviewLoopError(f"invalid severity for review issue {issue_id}: {severity}")
        message = str(issue.get("message", "")).strip()
        action = str(issue.get("required_action", "")).strip()
        if not message or not action:
            raise ReviewLoopError(f"review issue {issue_id} requires message and required_action")
        issues.append({
            "id": issue_id,
            "severity": severity,
            "status": status,
            "message": message,
            "required_action": action,
        })
    return issues


def record_review(state: dict[str, Any], report: dict[str, Any], actor: str) -> dict[str, Any]:
    validate_state_shape(state)
    actor = actor.strip()
    if not actor:
        raise ReviewLoopError("reviewer actor is required")
    if state["status"] != "awaiting_review":
        raise ReviewLoopError(f"review is not allowed while status is {state['status']}")

    tailor_event = _latest_event(state, "tailor")
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
    if verdict == APPROVE:
        state["status"] = "approved"
        state["approved_cv_sha256"] = reviewed_hash
    else:
        state["status"] = "revision_required"
        state["approved_cv_sha256"] = None
    state["updated_at"] = event["timestamp"]
    return state


def verify_release(state: dict[str, Any], cv_path: Path) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    try:
        validate_state_shape(state)
    except ReviewLoopError as exc:
        return [{"code": "REVIEW_LOOP_INVALID", "message": str(exc)}]

    events = _events(state)
    tailors = [event for event in events if event.get("type") == "tailor"]
    reviews = [event for event in events if event.get("type") == "review"]
    if not tailors:
        failures.append({"code": "TAILOR_MISSING", "message": "no tailor event recorded"})
    if not reviews:
        failures.append({"code": "REVIEW_MISSING", "message": "no independent review event recorded"})
    if state.get("status") != "approved":
        failures.append({"code": "REVIEW_NOT_APPROVED", "message": f"review-loop status is {state.get('status')}"})
    if not cv_path.is_file():
        failures.append({"code": "FINAL_CV_MISSING", "message": f"final CV payload not found: {cv_path}"})
        return failures

    final_hash = sha256_file(cv_path)
    if state.get("approved_cv_sha256") != final_hash:
        failures.append({"code": "APPROVED_HASH_STALE", "message": "final CV differs from the independently approved revision"})

    if tailors and reviews:
        latest_tailor = tailors[-1]
        latest_review = reviews[-1]
        if latest_review.get("iteration") != latest_tailor.get("iteration"):
            failures.append({"code": "LATEST_REVISION_UNREVIEWED", "message": "latest tailor revision has not been reviewed"})
        if latest_review.get("verdict") != APPROVE:
            failures.append({"code": "LATEST_REVIEW_REQUIRES_REVISION", "message": "latest review did not approve release"})
        if latest_review.get("actor") == latest_tailor.get("actor"):
            failures.append({"code": "REVIEW_NOT_INDEPENDENT", "message": "latest reviewer and tailor actors are identical"})
        if _open_issue_ids(latest_review):
            failures.append({"code": "OPEN_REVIEW_ISSUES", "message": "latest review still contains open issues"})
        if latest_review.get("cv_sha256") != latest_tailor.get("cv_sha256"):
            failures.append({"code": "REVIEWED_HASH_MISMATCH", "message": "latest review is not tied to the latest tailored CV"})

    expected = "tailor"
    for event in events:
        if event.get("type") != expected:
            failures.append({"code": "REVIEW_SEQUENCE_INVALID", "message": "events must alternate tailor then review"})
            break
        expected = "review" if expected == "tailor" else "tailor"
    return failures


def _parse_issue_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("state")
    init_parser.add_argument("--job-id", required=True)
    init_parser.add_argument("--max-iterations", type=int, default=4)

    tailor_parser = subparsers.add_parser("tailor")
    tailor_parser.add_argument("state")
    tailor_parser.add_argument("cv")
    tailor_parser.add_argument("--actor", required=True)
    tailor_parser.add_argument("--addressed-issues", default="")

    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("state")
    review_parser.add_argument("report")
    review_parser.add_argument("--actor", required=True)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("state")
    verify_parser.add_argument("cv")
    verify_parser.add_argument("--json-out")

    args = parser.parse_args()
    state_path = Path(args.state)
    try:
        if args.command == "init":
            write_json(state_path, create_state(args.job_id, args.max_iterations))
            print(f"REVIEW LOOP INITIALISED: {state_path}")
            return 0

        state = load_json(state_path)
        if args.command == "tailor":
            record_tailor(state, Path(args.cv), args.actor, _parse_issue_ids(args.addressed_issues))
            write_json(state_path, state)
            print(f"TAILOR ITERATION {state['current_iteration']} RECORDED")
            return 0
        if args.command == "review":
            record_review(state, load_json(Path(args.report)), args.actor)
            write_json(state_path, state)
            print(f"REVIEW {state['status'].upper()}")
            return 0

        failures = verify_release(state, Path(args.cv))
        result = {"passed": not failures, "failures": failures}
        if args.json_out:
            write_json(Path(args.json_out), result)
        if failures:
            print(json.dumps(result, indent=2))
            return 1
        print("TAILOR-REVIEW LOOP APPROVED.")
        return 0
    except (OSError, json.JSONDecodeError, ReviewLoopError) as exc:
        if args.command != "init" and "state" in locals() and isinstance(state, dict):
            write_json(state_path, state)
        print(f"REVIEW LOOP FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
