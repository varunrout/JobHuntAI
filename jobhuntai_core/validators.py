"""Fail-closed validation for JobHuntAI rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Iterable, Mapping, Any

from .schema import (
    APPLICATION_DATE_FIELDS,
    APPLICATION_ID_RE,
    APPLICATION_OUTCOME,
    APPLICATION_REQUIRED_FIELDS,
    APPLICATION_STAGE,
    APPLICATION_STATUS,
    CV_MODES,
    DATE_RE,
    JOB_DATE_FIELDS,
    JOB_ID_RE,
    JOB_REQUIRED_FIELDS,
    JOB_STATUS,
    SPONSORSHIP_RESPONSE,
    YES_NO_UNKNOWN,
)


@dataclass(frozen=True)
class Violation:
    code: str
    field: str
    detail: str


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _is_empty(value: Any) -> bool:
    return _text(value) == ""


def _validate_date(field: str, value: Any) -> list[Violation]:
    raw = _text(value)
    if not raw:
        return []
    if not DATE_RE.fullmatch(raw):
        return [Violation("INVALID_DATE_FORMAT", field, f"{raw!r} is not DD/MM/YYYY")]
    try:
        datetime.strptime(raw, "%d/%m/%Y")
    except ValueError:
        return [Violation("INVALID_DATE", field, f"{raw!r} is not a real calendar date")]
    return []


def _validate_required(row: Mapping[str, Any], fields: Iterable[str]) -> list[Violation]:
    out: list[Violation] = []
    for field in fields:
        if _is_empty(row.get(field)):
            out.append(Violation("REQUIRED_FIELD_MISSING", field, "required field is blank"))
    return out


def _validate_fit_score(row: Mapping[str, Any]) -> list[Violation]:
    value = row.get("Fit Score")
    if _is_empty(value):
        return []
    raw = _text(value)
    try:
        number = float(raw)
    except ValueError:
        return [Violation("INVALID_FIT_SCORE", "Fit Score", f"{raw!r} is not numeric")]
    if not number.is_integer() or not 0 <= number <= 100:
        return [Violation("INVALID_FIT_SCORE", "Fit Score", "must be an integer from 0 to 100")]

    score = int(number)
    notes = _text(row.get("Notes"))
    strategic = re.search(
        r"(?:Strategic(?:\s+fit|\s+score)?|Fit\s+score)\s*:?[ ]*(\d{1,2})/35",
        notes,
        flags=re.IGNORECASE,
    )
    if strategic and int(strategic.group(1)) == score and not re.search(
        rf"\b{score}/100\b", notes
    ):
        return [
            Violation(
                "FIT_SCORE_SCALE_AMBIGUOUS",
                "Fit Score",
                f"{score} matches the recorded /35 strategic score; a /100 fit score is required",
            )
        ]
    return []


def validate_job(row: Mapping[str, Any]) -> list[Violation]:
    out = _validate_required(row, JOB_REQUIRED_FIELDS)

    job_id = _text(row.get("Job ID"))
    if job_id and not JOB_ID_RE.fullmatch(job_id):
        out.append(Violation("INVALID_JOB_ID", "Job ID", job_id))

    status = _text(row.get("Status"))
    if status and status not in JOB_STATUS:
        out.append(Violation("INVALID_JOB_STATUS", "Status", status))

    for field in JOB_DATE_FIELDS:
        out.extend(_validate_date(field, row.get(field)))

    out.extend(_validate_fit_score(row))

    cv_mode = _text(row.get("CV Version Needed"))
    if cv_mode and cv_mode not in CV_MODES:
        out.append(Violation("INVALID_CV_MODE", "CV Version Needed", cv_mode))

    return out


def validate_application(
    row: Mapping[str, Any], *, existing_job_ids: set[str] | frozenset[str]
) -> list[Violation]:
    out = _validate_required(row, APPLICATION_REQUIRED_FIELDS)

    app_id = _text(row.get("Application ID"))
    if app_id and not APPLICATION_ID_RE.fullmatch(app_id):
        out.append(Violation("INVALID_APPLICATION_ID", "Application ID", app_id))

    job_id = _text(row.get("Job ID"))
    if job_id and not JOB_ID_RE.fullmatch(job_id):
        out.append(Violation("INVALID_JOB_ID", "Job ID", job_id))
    elif job_id and job_id not in existing_job_ids:
        out.append(Violation("DANGLING_JOB_ID", "Job ID", job_id))

    status = _text(row.get("Status"))
    if status and status not in APPLICATION_STATUS:
        out.append(Violation("INVALID_APPLICATION_STATUS", "Status", status))

    stage = _text(row.get("Stage"))
    if stage and stage not in APPLICATION_STAGE:
        out.append(Violation("INVALID_APPLICATION_STAGE", "Stage", stage))

    for field in APPLICATION_DATE_FIELDS:
        out.extend(_validate_date(field, row.get(field)))

    email = _text(row.get("Contact Email"))
    if email and "@" not in email:
        out.append(Violation("INVALID_EMAIL_SHAPE", "Contact Email", email))

    sponsorship_asked = _text(row.get("Sponsorship Asked?"))
    if sponsorship_asked and sponsorship_asked not in YES_NO_UNKNOWN:
        out.append(
            Violation("INVALID_SPONSORSHIP_ASKED", "Sponsorship Asked?", sponsorship_asked)
        )

    sponsorship_response = _text(row.get("Sponsorship Response"))
    if sponsorship_response and sponsorship_response not in SPONSORSHIP_RESPONSE:
        out.append(
            Violation(
                "INVALID_SPONSORSHIP_RESPONSE",
                "Sponsorship Response",
                sponsorship_response,
            )
        )

    outcome = _text(row.get("Outcome"))
    if outcome and outcome not in APPLICATION_OUTCOME:
        out.append(Violation("INVALID_APPLICATION_OUTCOME", "Outcome", outcome))

    cv_mode = _text(row.get("CV Version Used"))
    if cv_mode and cv_mode not in CV_MODES:
        out.append(Violation("INVALID_CV_MODE", "CV Version Used", cv_mode))

    return out


def require_valid(violations: Iterable[Violation]) -> None:
    problems = list(violations)
    if not problems:
        return
    detail = "; ".join(f"{v.code}:{v.field}:{v.detail}" for v in problems)
    raise ValueError(f"BLOCKED: {detail}")
