#!/usr/bin/env python3
"""Document-composition gates for archetype CVs.

This module turns two editorial rules into executable invariants:
1. a block that spends a heading must carry enough evidence to earn it;
2. a two-page CV must use the page, rather than hiding bad pagination behind
   technically valid output.

The renderer measures layout; it does not decide which evidence to add or cut.
Any failure routes back to Tailor / the composition controller.
"""
from __future__ import annotations

from typing import Any

EMPLOYER_MIN_BULLETS = 3
INDEPENDENT_PRACTICE_MIN_BULLETS = 2
TWO_PAGE_PROJECT_MIN_BULLETS = 3
ONE_PAGE_PROJECT_MIN_BULLETS = 2
FIRST_PAGE_MIN_FILL = 0.80
SECOND_PAGE_MIN_FILL = 0.70


def block_bullet_count(block: dict[str, Any]) -> int:
    """Count evidence bullets across a flat employer block or nested sub-roles."""
    flat = len(block.get("bullets", []) or [])
    nested = sum(len(role.get("bullets", []) or []) for role in block.get("roles", []) or [])
    return flat + nested


def is_independent_practice(block: dict[str, Any]) -> bool:
    return (
        str(block.get("experience_type", "")).strip() == "independent_practice"
        or str(block.get("org", "")).strip().lower() == "independent practice"
    )


def _one_page_target(payload: dict[str, Any]) -> bool:
    strategy = payload.get("page_strategy", {}) if isinstance(payload.get("page_strategy"), dict) else {}
    target = strategy.get("recommended_page_length", strategy.get("maximum_pages", 2))
    try:
        return int(target or 2) == 1
    except (TypeError, ValueError):
        return False


def check_payload_depth(payload: dict[str, Any]) -> list[tuple[str, str]]:
    """Reject starved employer/project blocks before rendering.

    Nested sub-roles may individually carry one or two bullets, but the parent
    employer block must still clear its floor. Independent Practice retains the
    explicit two-bullet floor from its policy because it is current-work
    chronology, not salaried employment.
    """
    failures: list[tuple[str, str]] = []
    one_page = _one_page_target(payload)

    for index, block in enumerate(payload.get("experience", []) or []):
        label = str(block.get("org") or block.get("title") or f"experience[{index}]")
        count = block_bullet_count(block)
        minimum = INDEPENDENT_PRACTICE_MIN_BULLETS if is_independent_practice(block) else EMPLOYER_MIN_BULLETS
        if count < minimum:
            failures.append((
                "EXPERIENCE_BLOCK_UNDERFED",
                f"{label!r} has {count} evidence bullet(s); minimum is {minimum}. Feed the block with JD-relevant evidence or omit it for a content reason.",
            ))

        for role_index, role in enumerate(block.get("roles", []) or []):
            role_count = len(role.get("bullets", []) or [])
            if role_count == 0:
                role_label = str(role.get("title") or f"role[{role_index}]")
                failures.append((
                    "EMPTY_NESTED_SUBROLE",
                    f"{label!r}/{role_label!r} spends a nested role line but carries no evidence.",
                ))

    project_minimum = ONE_PAGE_PROJECT_MIN_BULLETS if one_page else TWO_PAGE_PROJECT_MIN_BULLETS
    for index, project in enumerate(payload.get("projects", []) or []):
        label = str(project.get("title") or f"project[{index}]")
        count = len(project.get("bullets", []) or [])
        if count < project_minimum:
            failures.append((
                "PROJECT_BLOCK_UNDERFED",
                f"{label!r} has {count} evidence bullet(s); minimum is {project_minimum} for this page strategy.",
            ))

    return failures


def _lowest_edge(box: Any) -> float:
    """Return the lowest laid-out edge in a WeasyPrint box subtree."""
    y = float(getattr(box, "position_y", 0.0)) + float(getattr(box, "height", 0.0))
    for child in getattr(box, "children", []) or []:
        y = max(y, _lowest_edge(child))
    return y


def page_fill_ratios(document: Any) -> list[float]:
    """Measure each rendered page from its top to the lowest painted layout box."""
    ratios: list[float] = []
    for page in getattr(document, "pages", []) or []:
        page_box = getattr(page, "_page_box", None)
        if page_box is None:
            ratios.append(0.0)
            continue
        height = float(getattr(page_box, "height", 0.0) or 0.0)
        children = getattr(page_box, "children", []) or []
        if height <= 0 or not children:
            ratios.append(0.0)
            continue
        lowest = max(_lowest_edge(child) for child in children)
        ratios.append(max(0.0, min(lowest / height, 1.0)))
    return ratios


def check_document_composition(document: Any) -> tuple[list[tuple[str, str]], list[float]]:
    """Hard-fail materially sparse two-page composition.

    Page one uses a conservative 80% floor: this is intentionally a defect
    detector, not a demand for edge-to-edge text. Page two uses JobHuntAI's
    existing 70% substantive-fill contract.
    """
    failures: list[tuple[str, str]] = []
    fill = page_fill_ratios(document)
    if len(fill) == 2:
        if fill[0] < FIRST_PAGE_MIN_FILL:
            failures.append((
                "PAGE_ONE_UNDERFILLED",
                f"page one is {fill[0]:.0%} filled; minimum is {FIRST_PAGE_MIN_FILL:.0%}. Diagnose pagination atomicity before changing content.",
            ))
        if fill[1] < SECOND_PAGE_MIN_FILL:
            failures.append((
                "SECOND_PAGE_UNDERFILLED",
                f"page two is {fill[1]:.0%} filled; minimum is {SECOND_PAGE_MIN_FILL:.0%}. Restore relevant evidence or repair composition before reducing page count.",
            ))
    return failures, fill


def composition_report(payload: dict[str, Any], document: Any | None = None) -> dict[str, Any]:
    payload_failures = check_payload_depth(payload)
    layout_failures: list[tuple[str, str]] = []
    fill: list[float] = []
    if document is not None:
        layout_failures, fill = check_document_composition(document)
    failures = payload_failures + layout_failures
    return {
        "passed": not failures,
        "page_fill": fill,
        "failures": [{"code": code, "detail": detail} for code, detail in failures],
    }
