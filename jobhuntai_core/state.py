"""State-transition rules for Jobs and Applications.

The two scopes intentionally use different lattices. Employer outcomes belong to
Applications. A pre-application decline is `Do not apply` on Jobs.
"""

from __future__ import annotations

from dataclasses import dataclass

from .schema import (
    APPLICATION_STATUS_RANK,
    APPLICATION_TERMINAL,
    JOB_STATUS_RANK,
    JOB_TERMINAL,
)


@dataclass(frozen=True)
class Transition:
    allowed: bool
    kind: str
    reason: str


def _transition(current: str, proposed: str, rank: dict[str, int], terminal: frozenset[str]) -> Transition:
    if current == proposed:
        return Transition(True, "noop", "state unchanged")
    if current in terminal:
        return Transition(False, "frozen", f"terminal state {current!r} is absorbing")
    if proposed in terminal:
        return Transition(True, "terminal", "entering a terminal state is allowed")
    if current not in rank or proposed not in rank:
        return Transition(False, "unknown", "state is not in the controlled vocabulary")
    if rank[proposed] < rank[current]:
        return Transition(False, "regress", f"{proposed!r} is behind {current!r}")
    return Transition(True, "advance", "forward transition")


def job_transition(current: str, proposed: str) -> Transition:
    return _transition(current, proposed, JOB_STATUS_RANK, JOB_TERMINAL)


def application_transition(current: str, proposed: str) -> Transition:
    return _transition(current, proposed, APPLICATION_STATUS_RANK, APPLICATION_TERMINAL)


def validate_job_application_semantics(job_status: str, has_application: bool) -> list[str]:
    problems: list[str] = []
    if has_application and job_status == "Do not apply":
        problems.append("job has an application but is marked Do not apply")
    if has_application and job_status not in {"Applied", "Interviewing", "Closed"}:
        problems.append(
            "job with an Applications row must remain Applied/Interviewing/Closed; "
            "employer outcomes belong on the Applications row"
        )
    return problems
