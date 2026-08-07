#!/usr/bin/env python3
"""Block Selected Impact unless Varun explicitly approved it for this CV run."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


APPROVAL_SOURCE = "explicit_user_instruction"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payload(cv: dict[str, Any]) -> list[tuple[str, str]]:
    selected_impact = cv.get("selected_impact") or []
    if not selected_impact:
        return []

    approval = cv.get("selected_impact_approval")
    if not isinstance(approval, dict):
        return [(
            "SELECTED_IMPACT_EXPLICIT_APPROVAL_REQUIRED",
            "Selected Impact is forbidden by default. Record run-specific explicit user approval before including it.",
        )]

    if approval.get("approved") is not True or approval.get("source") != APPROVAL_SOURCE:
        return [(
            "SELECTED_IMPACT_EXPLICIT_APPROVAL_REQUIRED",
            "Selected Impact requires selected_impact_approval.approved=true and source='explicit_user_instruction'. Archetype, evidence strength, page strategy, layout pressure or prior CVs cannot authorise it.",
        )]

    return []


def run(cv_path: Path) -> int:
    failures = validate_payload(load_json(cv_path))
    if failures:
        print(f"SELECTED IMPACT BLOCKED - {len(failures)} failure(s):")
        for code, detail in failures:
            print(f"[{code}] {detail}")
        return 2
    print("SELECTED IMPACT POLICY CLEAN.")
    return 0
