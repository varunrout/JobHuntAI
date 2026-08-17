"""Read-only health checks for the JobHuntAI workspace."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .ids import output_job_ids
from .schema import CANONICAL_OUTPUT_RE, OUTPUT_PREFIX_RE
from .state import validate_job_application_semantics
from .validators import validate_application, validate_job


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    entity: str
    entity_id: str
    detail: str


def run_doctor(
    *,
    jobs: Iterable[Mapping[str, Any]],
    applications: Iterable[Mapping[str, Any]],
    output_folder_names: Iterable[str],
) -> list[Finding]:
    jobs = list(jobs)
    applications = list(applications)
    folders = list(output_folder_names)
    findings: list[Finding] = []

    job_ids = [str(row.get("Job ID", "")).strip() for row in jobs if row.get("Job ID")]
    app_ids = [
        str(row.get("Application ID", "")).strip()
        for row in applications
        if row.get("Application ID")
    ]
    job_id_set = set(job_ids)

    for value, count in Counter(job_ids).items():
        if count > 1:
            findings.append(Finding("BLOCK", "DUPLICATE_JOB_ID", "job", value, f"appears {count} times"))
    for value, count in Counter(app_ids).items():
        if count > 1:
            findings.append(
                Finding("BLOCK", "DUPLICATE_APPLICATION_ID", "application", value, f"appears {count} times")
            )

    folder_job_ids = output_job_ids(folders)
    for value, count in Counter(folder_job_ids).items():
        if count > 1:
            findings.append(
                Finding("BLOCK", "DUPLICATE_OUTPUT_JOB_ID", "output", value, f"prefix appears {count} times")
            )

    for row in jobs:
        job_id = str(row.get("Job ID", "")).strip()
        for violation in validate_job(row):
            findings.append(Finding("BLOCK", violation.code, "job", job_id, f"{violation.field}: {violation.detail}"))

    application_job_ids: set[str] = set()
    for row in applications:
        app_id = str(row.get("Application ID", "")).strip()
        job_id = str(row.get("Job ID", "")).strip()
        if job_id:
            application_job_ids.add(job_id)
        for violation in validate_application(row, existing_job_ids=job_id_set):
            findings.append(
                Finding("BLOCK", violation.code, "application", app_id, f"{violation.field}: {violation.detail}")
            )

    for row in jobs:
        job_id = str(row.get("Job ID", "")).strip()
        status = str(row.get("Status", "")).strip()
        for detail in validate_job_application_semantics(status, job_id in application_job_ids):
            findings.append(Finding("BLOCK", "JOB_APPLICATION_STATUS_CONFLICT", "job", job_id, detail))

    for name in folders:
        clean = (name or "").strip()
        if clean.startswith("JOB-") and not CANONICAL_OUTPUT_RE.fullmatch(clean):
            job_match = OUTPUT_PREFIX_RE.match(clean)
            entity_id = job_match.group(1) if job_match else ""
            findings.append(Finding("WARN", "NONCANONICAL_OUTPUT_NAME", "output", entity_id, clean))
        elif not clean.startswith("JOB-") and clean.upper().startswith("VALIDATION_"):
            continue
        elif not clean.startswith("JOB-"):
            findings.append(Finding("WARN", "UNLINKED_OUTPUT_FOLDER", "output", "", clean))

    return findings
