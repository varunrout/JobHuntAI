"""Permanent ID allocation.

Counters are monotonic and never decrement. The allocator also scans every observed
ID and Output-folder prefix before returning a candidate. This makes the counter a
floor, not a source that can silently overwrite reality.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from .schema import APPLICATION_ID_RE, JOB_ID_RE, OUTPUT_PREFIX_RE


class IdCollisionError(ValueError):
    pass


def _job_numbers(job_ids: Iterable[str]) -> list[int]:
    numbers: list[int] = []
    for value in job_ids:
        match = JOB_ID_RE.fullmatch((value or "").strip())
        if match:
            numbers.append(int(match.group(1)))
    return numbers


def output_job_ids(folder_names: Iterable[str]) -> list[str]:
    found: list[str] = []
    for name in folder_names:
        match = OUTPUT_PREFIX_RE.match((name or "").strip())
        if match:
            found.append(match.group(1))
    return found


def assert_unique_job_ids(job_ids: Iterable[str], folder_names: Iterable[str] = ()) -> None:
    sheet_ids = [x.strip() for x in job_ids if x and JOB_ID_RE.fullmatch(x.strip())]
    duplicates = sorted(k for k, n in Counter(sheet_ids).items() if n > 1)
    if duplicates:
        raise IdCollisionError(f"duplicate Job IDs in Jobs sheet: {duplicates}")

    folder_ids = output_job_ids(folder_names)
    folder_duplicates = sorted(k for k, n in Counter(folder_ids).items() if n > 1)
    if folder_duplicates:
        raise IdCollisionError(f"duplicate Job ID prefixes in Outputs: {folder_duplicates}")


def next_job_id(
    *, job_ids: Iterable[str], folder_names: Iterable[str], sequence: int
) -> tuple[str, int]:
    job_ids = list(job_ids)
    folder_names = list(folder_names)
    assert_unique_job_ids(job_ids, folder_names)

    observed = _job_numbers(job_ids)
    observed.extend(_job_numbers(output_job_ids(folder_names)))
    next_number = max([sequence, *observed], default=sequence) + 1
    candidate = f"JOB-2026-{next_number:06d}"

    all_seen = set(x.strip() for x in job_ids if x)
    all_seen.update(output_job_ids(folder_names))
    if candidate in all_seen:
        raise IdCollisionError(f"refusing to reuse existing Job ID {candidate}")
    return candidate, next_number


def next_application_id(*, application_ids: Iterable[str], sequence: int) -> tuple[str, int]:
    application_ids = list(application_ids)
    valid = [x.strip() for x in application_ids if x and APPLICATION_ID_RE.fullmatch(x.strip())]
    duplicates = sorted(k for k, n in Counter(valid).items() if n > 1)
    if duplicates:
        raise IdCollisionError(f"duplicate Application IDs: {duplicates}")

    observed = [int(APPLICATION_ID_RE.fullmatch(x).group(1)) for x in valid]
    next_number = max([sequence, *observed], default=sequence) + 1
    candidate = f"APP-{next_number:04d}"
    if candidate in set(valid):
        raise IdCollisionError(f"refusing to reuse existing Application ID {candidate}")
    return candidate, next_number
