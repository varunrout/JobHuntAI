"""Safe write contract used by connector adapters.

This module does not know Google APIs. A connector supplies write_row, read_row and
audit callbacks. That keeps the invariant testable while allowing ChatGPT, Apps
Script or another adapter to provide the actual transport.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .state import application_transition, job_transition
from .validators import Violation, require_valid, validate_application, validate_job


class PostWriteMismatch(RuntimeError):
    pass


@dataclass(frozen=True)
class WriteResult:
    entity: str
    entity_id: str
    verified_fields: tuple[str, ...]


WriteRow = Callable[[Mapping[str, Any]], None]
ReadRow = Callable[[], Mapping[str, Any]]
Audit = Callable[[str, str, str, Any, Any, str, str, str], None]


def _validate(
    entity: str,
    row: Mapping[str, Any],
    *,
    existing_job_ids: set[str] | frozenset[str],
) -> list[Violation]:
    if entity == "job":
        return validate_job(row)
    if entity == "application":
        return validate_application(row, existing_job_ids=existing_job_ids)
    raise ValueError(f"unknown entity {entity!r}")


def _require_legal_status_transition(
    entity: str,
    previous_row: Mapping[str, Any] | None,
    proposed_row: Mapping[str, Any],
) -> None:
    if not previous_row:
        return

    current = str(previous_row.get("Status", "") or "").strip()
    proposed = str(proposed_row.get("Status", "") or "").strip()
    if not current or not proposed or current == proposed:
        return

    if entity == "job":
        transition = job_transition(current, proposed)
    elif entity == "application":
        transition = application_transition(current, proposed)
    else:
        raise ValueError(f"unknown entity {entity!r}")

    if not transition.allowed:
        raise ValueError(
            "BLOCKED: ILLEGAL_STATE_TRANSITION:"
            f"{entity}:{current!r}->{proposed!r}:{transition.kind}:{transition.reason}"
        )


def validated_write(
    *,
    entity: str,
    proposed_row: Mapping[str, Any],
    previous_row: Mapping[str, Any] | None,
    existing_job_ids: set[str] | frozenset[str],
    write_row: WriteRow,
    read_row: ReadRow,
    audit: Audit,
    reason: str,
    source: str = "control-plane",
    actor: str = "JobHuntAI",
) -> WriteResult:
    """Validate, enforce lifecycle, write, re-read, compare, then audit.

    The connector must write by column name. Positional cell APIs belong inside the
    adapter and must never leak into workflow code. A transport success is not a
    JobHuntAI success: every proposed field must match the immediate read-back.
    """

    require_valid(_validate(entity, proposed_row, existing_job_ids=existing_job_ids))
    _require_legal_status_transition(entity, previous_row, proposed_row)

    write_row(proposed_row)
    persisted = dict(read_row())

    mismatches: list[str] = []
    for field, expected in proposed_row.items():
        actual = persisted.get(field)
        expected_text = "" if expected is None else str(expected)
        actual_text = "" if actual is None else str(actual)
        if actual_text != expected_text:
            mismatches.append(f"{field}: expected {expected_text!r}, got {actual_text!r}")

    if mismatches:
        raise PostWriteMismatch("POST-WRITE VERIFY FAILED: " + "; ".join(mismatches))

    entity_id_field = "Job ID" if entity == "job" else "Application ID"
    entity_id = str(proposed_row.get(entity_id_field, ""))
    old = previous_row or {}
    for field, new_value in proposed_row.items():
        old_value = old.get(field)
        if ("" if old_value is None else str(old_value)) == ("" if new_value is None else str(new_value)):
            continue
        audit(entity, entity_id, field, old_value, new_value, reason, source, actor)

    return WriteResult(entity, entity_id, tuple(proposed_row.keys()))
