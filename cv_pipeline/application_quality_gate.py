#!/usr/bin/env python3
"""Final fail-closed release gate for a JobHuntAI application package."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import cv_length_gate
import rendered_visual_gate
import review_loop

REQUIRED_CHECKS = (
    "preflight",
    "duplicate",
    "visa",
    "role_identity",
    "evidence",
    "cv_length",
    "factual",
    "positioning",
    "visual",
    "render",
    "rendered_visual_review",
)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def resolve(run_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else run_dir / path


def add_failure(failures: list[dict[str, str]], code: str, message: str) -> None:
    failures.append({"code": code, "message": message})


def _latest_review_actor(state: dict[str, Any] | None) -> str | None:
    if not isinstance(state, dict):
        return None
    if state.get("contract") in review_loop.PANEL_CONTRACTS:
        event = review_loop.latest_review_for_lane(state, "competitiveness")
        return str((event or {}).get("actor", "")).strip() or None
    reviews = [
        item for item in state.get("events", [])
        if isinstance(item, dict) and item.get("type") == "review"
    ]
    if not reviews:
        return None
    return str(reviews[-1].get("actor", "")).strip() or None


def _compare_page_fill(
    failures: list[dict[str, str]],
    audit: dict[str, Any],
    rendered_review: dict[str, Any],
) -> None:
    audited = audit.get("page_fill")
    pages = rendered_review.get("pages")
    if not isinstance(audited, list) or not isinstance(pages, list):
        add_failure(failures, "PAGE_FILL_SOURCE_MISSING", "CV-length audit and rendered review must both contain page-fill measurements")
        return
    actual = [page.get("meaningful_fill") for page in pages if isinstance(page, dict)]
    if len(audited) != len(actual):
        add_failure(failures, "PAGE_FILL_COUNT_MISMATCH", "CV-length page-fill count differs from the rendered-page review")
        return
    for index, (recorded, measured) in enumerate(zip(audited, actual), start=1):
        try:
            delta = abs(float(recorded) - float(measured))
        except (TypeError, ValueError):
            delta = 999
        if delta > rendered_visual_gate.METRIC_TOLERANCE:
            add_failure(
                failures,
                "PAGE_FILL_RENDER_MISMATCH",
                f"page {index} fill in cv_length_audit.json was not measured from the exact final PDF",
            )


def run(run_dir: Path, manifest_path: Path) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    if not manifest_path.is_file():
        return [{"code": "MANIFEST_MISSING", "message": f"application manifest not found: {manifest_path}"}]
    try:
        manifest = load_json(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [{"code": "MANIFEST_INVALID", "message": str(exc)}]

    if manifest.get("contract") != "jobhuntai-application-quality-v1":
        add_failure(failures, "MANIFEST_CONTRACT_INVALID", "application quality contract must be jobhuntai-application-quality-v1")

    decision = manifest.get("decision")
    if decision not in {"apply", "apply_lightly"}:
        add_failure(failures, "DECISION_NOT_APPLY", f"release is blocked for decision {decision!r}")

    artefacts = manifest.get("artefacts")
    if not isinstance(artefacts, dict):
        add_failure(failures, "ARTEFACT_MAP_MISSING", "manifest requires an artefacts object")
        artefacts = {}

    required_artifacts = {
        "job_description": False,
        "role_identity": True,
        "evidence_ranking": True,
        "cv": True,
        "cv_diagnostic": True,
        "cv_length_audit": True,
        "cv_pdf": False,
        "rendered_visual_review": True,
        "review_loop": True,
    }
    resolved: dict[str, Path] = {}
    for key, require_nonempty_json in required_artifacts.items():
        value = artefacts.get(key)
        if not isinstance(value, str) or not value.strip():
            add_failure(failures, f"{key.upper()}_PATH_MISSING", f"artefact path missing for {key}")
            continue
        path = resolve(run_dir, value)
        resolved[key] = path
        if not path.is_file():
            add_failure(failures, f"{key.upper()}_MISSING", f"required artefact not found: {path}")
            continue
        if path.stat().st_size == 0:
            add_failure(failures, f"{key.upper()}_EMPTY", f"required artefact is empty: {path}")
            continue
        if require_nonempty_json:
            try:
                if not load_json(path):
                    add_failure(failures, f"{key.upper()}_INVALID", f"required JSON artefact is empty: {path}")
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                add_failure(failures, f"{key.upper()}_INVALID", str(exc))

    checks = manifest.get("checks")
    if not isinstance(checks, dict):
        add_failure(failures, "CHECKS_MISSING", "manifest requires a checks object")
        checks = {}
    for check in REQUIRED_CHECKS:
        result = checks.get(check)
        if not isinstance(result, dict) or result.get("status") != "passed":
            add_failure(failures, f"{check.upper()}_NOT_PASSED", f"quality check {check} must be passed")

    duplicate = checks.get("duplicate", {}) if isinstance(checks.get("duplicate"), dict) else {}
    if duplicate.get("outcome") not in {"clear", "reapply_eligible"}:
        add_failure(failures, "DUPLICATE_BLOCKED", "duplicate outcome must be clear or reapply_eligible")

    visa = checks.get("visa", {}) if isinstance(checks.get("visa"), dict) else {}
    if visa.get("outcome") not in {"viable", "uncertain_with_rationale"}:
        add_failure(failures, "VISA_BLOCKED", "visa outcome must be viable or uncertain_with_rationale")
    if visa.get("outcome") == "uncertain_with_rationale" and not str(visa.get("rationale", "")).strip():
        add_failure(failures, "VISA_RATIONALE_MISSING", "uncertain visa outcome requires a rationale")

    tracker = manifest.get("tracker")
    if not isinstance(tracker, dict) or tracker.get("status") != "checked":
        add_failure(failures, "TRACKER_NOT_CHECKED", "tracker duplicate history must be checked")
    elif tracker.get("mode") not in {"read_only", "editable"}:
        add_failure(failures, "TRACKER_MODE_INVALID", "tracker mode must be read_only or editable")

    drive = manifest.get("drive_save")
    if not isinstance(drive, dict) or drive.get("status") != "verified":
        add_failure(failures, "DRIVE_SAVE_UNVERIFIED", "Drive save must be verified before release")

    state: dict[str, Any] | None = None
    if "review_loop" in resolved and "cv" in resolved and resolved["review_loop"].is_file() and resolved["cv"].is_file():
        try:
            state = load_json(resolved["review_loop"])
            failures.extend(review_loop.verify_release(state, resolved["cv"]))
        except (OSError, json.JSONDecodeError, ValueError, review_loop.ReviewLoopError) as exc:
            add_failure(failures, "REVIEW_LOOP_INVALID", str(exc))

    audit: dict[str, Any] | None = None
    if all(key in resolved and resolved[key].is_file() for key in ("cv", "cv_length_audit")):
        try:
            cv = load_json(resolved["cv"])
            audit = load_json(resolved["cv_length_audit"])
            failures.extend(cv_length_gate.validate(cv, audit, state))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            add_failure(failures, "CV_LENGTH_AUDIT_INVALID", str(exc))

    rendered_review: dict[str, Any] | None = None
    if all(key in resolved and resolved[key].is_file() for key in ("cv_pdf", "rendered_visual_review")):
        try:
            rendered_review = load_json(resolved["rendered_visual_review"])
            failures.extend(
                rendered_visual_gate.validate(
                    resolved["cv_pdf"],
                    rendered_review,
                    run_dir,
                    expected_reviewer_actor=_latest_review_actor(state),
                )
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            add_failure(failures, "RENDERED_VISUAL_REVIEW_INVALID", str(exc))

    if audit is not None and rendered_review is not None:
        _compare_page_fill(failures, audit, rendered_review)

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir")
    parser.add_argument("--manifest", default="application_manifest.json")
    parser.add_argument("--json-out")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    manifest_path = resolve(run_dir, args.manifest)
    failures = run(run_dir, manifest_path)
    result = {"passed": not failures, "status": "ready_to_apply" if not failures else "failed_qa", "failures": failures}
    if args.json_out:
        review_loop.write_json(Path(args.json_out), result)
    if failures:
        print(json.dumps(result, indent=2))
        return 1
    print("APPLICATION QUALITY GATE PASSED: READY TO APPLY.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
