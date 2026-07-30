#!/usr/bin/env python3
"""Fail-closed CV page-length, evidence-retention and omission audit gate."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "schemas" / "cv_length_audit.schema.json"

CONTRACT = "jobhuntai-cv-length-audit-v1"
ONE_PAGE_ALLOWED = "ONE_PAGE_ALLOWED"
TWO_PAGE_PREFERRED = "TWO_PAGE_PREFERRED"
TWO_PAGE_REQUIRED = "TWO_PAGE_REQUIRED"
DECISIONS = {ONE_PAGE_ALLOWED, TWO_PAGE_PREFERRED, TWO_PAGE_REQUIRED}
REMEDIATION_ORDER = (
    "section_order",
    "restore_relevant_evidence",
    "improve_bullet_depth",
    "adjust_section_placement",
    "tune_spacing",
    "repair_breaks",
    "reduce_page_count",
)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def schema_errors(instance: dict[str, Any]) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["jsonschema is required to validate CV length audits"]
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    out: list[str] = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "root"
        out.append(f"{location}: {error.message}")
    return out


def _normalise(value: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9%£+./-]+", " ", str(value or "").lower())).strip()


def rendered_text(cv: dict[str, Any]) -> str:
    chunks: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, (str, int, float)):
            chunks.append(str(value))

    walk(cv)
    return _normalise("\n".join(chunks))


def add_failure(failures: list[dict[str, str]], code: str, message: str) -> None:
    failures.append({"code": code, "message": message})


def _ordered_subsequence(actual: list[str], required: tuple[str, ...]) -> bool:
    position = 0
    for item in actual:
        if position < len(required) and item == required[position]:
            position += 1
    return position == len(required)


def _one_page_permitted(profile: dict[str, Any], essential_count: int) -> bool:
    seniority = str(profile.get("seniority", "")).lower().strip()
    senior = seniority in {"senior", "lead", "principal", "manager", "head", "director"}
    relevant_years = float(profile.get("relevant_years", 0) or 0)
    relevant_roles = int(profile.get("relevant_roles", 0) or 0)
    relevant_projects = int(profile.get("relevant_projects", 0) or 0)
    technical_breadth = int(profile.get("technical_breadth", 0) or 0)
    domain_transfer = bool(profile.get("domain_transfer_required"))
    return (
        not senior
        and relevant_years <= 3
        and relevant_roles <= 2
        and relevant_projects <= 1
        and technical_breadth <= 3
        and essential_count <= 4
        and not domain_transfer
    )


def validate(
    cv: dict[str, Any],
    audit: dict[str, Any],
    review_state: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for error in schema_errors(audit):
        add_failure(failures, "CV_LENGTH_SCHEMA", error)
    if audit.get("contract") != CONTRACT:
        add_failure(failures, "CV_LENGTH_CONTRACT_INVALID", f"audit contract must be {CONTRACT}")

    decision = str(audit.get("strategy_decision", "")).strip()
    if decision not in DECISIONS:
        add_failure(failures, "CV_LENGTH_DECISION_INVALID", f"unsupported strategy_decision {decision!r}")

    rationale = str(audit.get("strategy_rationale", "")).strip()
    if len(rationale) < 40:
        add_failure(failures, "CV_LENGTH_RATIONALE_MISSING", "page-length strategy requires a specific rationale")

    final_pages = audit.get("final_page_count")
    if final_pages not in {1, 2}:
        add_failure(failures, "FINAL_PAGE_COUNT_INVALID", "final_page_count must be 1 or 2")
        final_pages = None

    cv_page_strategy = cv.get("page_strategy", {}) if isinstance(cv.get("page_strategy"), dict) else {}
    cv_target = cv_page_strategy.get("maximum_pages")
    if cv_target in {1, 2} and final_pages in {1, 2} and cv_target != final_pages:
        add_failure(failures, "CV_PAGE_TARGET_MISMATCH", "CV page strategy does not match the audited final page count")

    essential = audit.get("essential_evidence")
    if not isinstance(essential, list) or not essential:
        add_failure(failures, "ESSENTIAL_EVIDENCE_MAP_MISSING", "essential_evidence must contain the role-critical evidence map")
        essential = []

    text = rendered_text(cv)
    for index, item in enumerate(essential, start=1):
        if not isinstance(item, dict):
            add_failure(failures, "ESSENTIAL_EVIDENCE_INVALID", f"essential evidence item {index} must be an object")
            continue
        evidence_id = str(item.get("id", f"item-{index}"))
        markers = item.get("match_any", [])
        if not isinstance(markers, list) or not any(str(marker).strip() for marker in markers):
            add_failure(failures, "ESSENTIAL_EVIDENCE_MARKERS_MISSING", f"{evidence_id} requires one or more match_any markers")
            continue
        if not any(_normalise(marker) in text for marker in markers if str(marker).strip()):
            add_failure(failures, "ESSENTIAL_EVIDENCE_DROPPED", f"role-critical evidence {evidence_id!r} is absent from the final CV")

    omissions = audit.get("omissions")
    if not isinstance(omissions, list):
        add_failure(failures, "OMISSION_AUDIT_MISSING", "omissions must explicitly record what was excluded and why")
        omissions = []
    for index, item in enumerate(omissions, start=1):
        if not isinstance(item, dict):
            add_failure(failures, "OMISSION_AUDIT_INVALID", f"omission {index} must be an object")
            continue
        impact = item.get("impact")
        if impact not in {"harmless", "strategic_loss"}:
            add_failure(failures, "OMISSION_IMPACT_INVALID", f"omission {index} impact must be harmless or strategic_loss")
        if len(str(item.get("rationale", "")).strip()) < 20:
            add_failure(failures, "OMISSION_RATIONALE_MISSING", f"omission {index} requires a specific rationale")
        if impact == "strategic_loss":
            add_failure(failures, "STRATEGIC_EVIDENCE_OMITTED", f"omission {item.get('id', index)!r} weakens the hiring case")

    profile = audit.get("candidate_role_profile")
    if not isinstance(profile, dict):
        add_failure(failures, "CANDIDATE_ROLE_PROFILE_MISSING", "candidate_role_profile is required for page-length permission")
        profile = {}

    one_page_permitted = _one_page_permitted(profile, len(essential))
    exception = audit.get("one_page_exception") if isinstance(audit.get("one_page_exception"), dict) else {}
    if final_pages == 1:
        if decision == TWO_PAGE_REQUIRED:
            add_failure(failures, "ONE_PAGE_NOT_PERMITTED", "strategy requires two pages")
        elif decision == TWO_PAGE_PREFERRED and not bool(exception.get("approved")):
            add_failure(failures, "ONE_PAGE_EXCEPTION_REQUIRED", "two-page-preferred strategy needs an explicit one-page exception")
        elif decision == ONE_PAGE_ALLOWED and not one_page_permitted:
            add_failure(failures, "ONE_PAGE_NOT_PERMITTED", "candidate depth exceeds the one-page permission thresholds")

    review = audit.get("review_judgement")
    if not isinstance(review, dict):
        add_failure(failures, "PAGE_COUNT_REVIEW_MISSING", "independent review must answer the page-count evidence question")
        review = {}
    if review.get("material_evidence_removed") is not False:
        add_failure(failures, "PAGE_OPTIMISATION_WEAKENED_CASE", "review must confirm that page optimisation removed no material evidence")
    if review.get("omission_audit_complete") is not True:
        add_failure(failures, "OMISSION_AUDIT_UNAPPROVED", "review must confirm that the omission audit is complete")
    if review.get("page_strategy_approved") is not True:
        add_failure(failures, "PAGE_STRATEGY_UNAPPROVED", "independent reviewer must approve the page-length strategy")
    if len(str(review.get("rationale", "")).strip()) < 30:
        add_failure(failures, "PAGE_COUNT_REVIEW_RATIONALE_MISSING", "review judgement requires a specific rationale")

    if review_state is not None:
        events = review_state.get("events", []) if isinstance(review_state, dict) else []
        reviews = [item for item in events if isinstance(item, dict) and item.get("type") == "review"]
        latest_review = reviews[-1] if reviews else None
        if not latest_review:
            add_failure(failures, "PAGE_COUNT_REVIEW_NOT_TIED_TO_LOOP", "cv-length review judgement requires an independent review-loop event")
        else:
            if review.get("review_actor") != latest_review.get("actor"):
                add_failure(failures, "PAGE_COUNT_REVIEW_ACTOR_MISMATCH", "cv-length audit reviewer must match the latest independent reviewer")
            if review.get("review_iteration") != latest_review.get("iteration"):
                add_failure(failures, "PAGE_COUNT_REVIEW_ITERATION_MISMATCH", "cv-length audit must reference the latest reviewed iteration")
            if review.get("cv_sha256") != latest_review.get("cv_sha256"):
                add_failure(failures, "PAGE_COUNT_REVIEW_HASH_MISMATCH", "cv-length audit must be tied to the exact independently reviewed CV hash")
            if latest_review.get("verdict") != "approve":
                add_failure(failures, "PAGE_COUNT_REVIEW_NOT_APPROVED", "latest independent review must approve the audited CV")

    transition = audit.get("page_transition")
    if not isinstance(transition, dict):
        transition = {}
    previous_pages = transition.get("previous_page_count")
    page_reduced = previous_pages in {1, 2} and final_pages in {1, 2} and previous_pages > final_pages
    preferred_exception = decision == TWO_PAGE_PREFERRED and final_pages == 1
    if preferred_exception and previous_pages != 2:
        add_failure(
            failures,
            "ONE_PAGE_EXCEPTION_REMEDIATION_MISSING",
            "a two-page-preferred CV may use one page only after a recorded two-page remediation attempt",
        )
    if page_reduced or preferred_exception:
        steps = transition.get("remediation_steps", [])
        if not isinstance(steps, list) or not _ordered_subsequence([str(item) for item in steps], REMEDIATION_ORDER):
            add_failure(
                failures,
                "SPARSE_PAGE_REMEDIATION_SKIPPED",
                "page reduction is allowed only after the full ordered remediation sequence",
            )
        if transition.get("fresh_strategic_review") is not True:
            add_failure(failures, "PAGE_REDUCTION_REVIEW_REQUIRED", "page-count reduction requires a fresh strategic review")

    page_fill = audit.get("page_fill")
    if final_pages == 2:
        if not isinstance(page_fill, list) or len(page_fill) < 2:
            add_failure(failures, "PAGE_FILL_AUDIT_MISSING", "two-page CV requires page-fill measurements")
        else:
            try:
                second_fill = float(page_fill[1])
            except (TypeError, ValueError):
                second_fill = -1
            if second_fill < 0.70:
                add_failure(failures, "SECOND_PAGE_UNDERFILLED", "second page must be at least 70% meaningfully filled")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cv")
    parser.add_argument("audit")
    parser.add_argument("--json-out")
    args = parser.parse_args()
    failures = validate(load_json(Path(args.cv)), load_json(Path(args.audit)))
    result = {"passed": not failures, "failures": failures}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if failures:
        print(json.dumps(result, indent=2))
        return 1
    print("CV LENGTH AND EVIDENCE RETENTION GATE PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
