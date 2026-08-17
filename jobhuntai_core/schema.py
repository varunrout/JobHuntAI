"""Canonical JobHuntAI control-plane schema.

This module is intentionally independent of Google APIs. Connectors and agents may
change, but every write must conform to these values before it reaches Sheets.

CV mode is deliberately not inferred from Role Lane alone. The live tracker proves
that lanes such as Pricing / Portfolio can legitimately map to different CV modes
in different domains. Historical migration must therefore use evidence or an
explicit approved mapping, never a guess.
"""

from __future__ import annotations

import re

JOB_ID_RE = re.compile(r"^JOB-2026-(\d{6})$")
APPLICATION_ID_RE = re.compile(r"^APP-(\d{4})$")
OUTPUT_PREFIX_RE = re.compile(r"^(JOB-2026-\d{6})(?:_|\s+-\s+)")
CANONICAL_OUTPUT_RE = re.compile(r"^JOB-2026-\d{6}_[A-Za-z0-9][A-Za-z0-9_]*$")
DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")

CV_MODES = frozenset(
    {
        "Energy_Forecasting_Risk",
        "Commercial_Data_Analyst",
        "Applied_Data_Scientist",
    }
)

JOB_STATUS = frozenset(
    {
        "Saved",
        "Screening",
        "Ready to apply",
        "Applied",
        "Interviewing",
        "Closed",
        "Do not apply",
    }
)

APPLICATION_STATUS = frozenset(
    {
        "Drafting",
        "Applied",
        "Recruiter Screen",
        "Assessment",
        "Interviewing",
        "Offer",
        "Rejected",
        "Withdrawn",
        "No response",
        "Closed",
    }
)

APPLICATION_STAGE = frozenset(
    {
        "Application",
        "Screen",
        "Assessment",
        "First Interview",
        "Final Interview",
        "Offer",
        "Background Check",
        "Closed",
    }
)

YES_NO_UNKNOWN = frozenset({"Yes", "No", "Partial", "Unknown"})
SPONSORSHIP_RESPONSE = frozenset(
    {
        "Confirmed can sponsor",
        "Likely can sponsor",
        "Needs checking",
        "Cannot sponsor",
        "Not asked",
        "No response",
    }
)
APPLICATION_OUTCOME = frozenset(
    {"Pending", "Rejected", "Interview", "Offer", "Withdrawn", "Closed"}
)

JOB_STATUS_RANK = {
    "Saved": 0,
    "Screening": 1,
    "Ready to apply": 2,
    "Applied": 3,
    "Interviewing": 4,
    "Closed": 5,
}
JOB_TERMINAL = frozenset({"Closed", "Do not apply"})

APPLICATION_STATUS_RANK = {
    "Drafting": 0,
    "Applied": 1,
    "Recruiter Screen": 2,
    "Assessment": 3,
    "Interviewing": 4,
    "Offer": 5,
}
APPLICATION_TERMINAL = frozenset({"Rejected", "Withdrawn", "No response", "Closed"})

JOB_REQUIRED_FIELDS = ("Job ID", "Company", "Role Title", "Status")
APPLICATION_REQUIRED_FIELDS = (
    "Application ID",
    "Job ID",
    "Company",
    "Role Title",
    "Status",
)

JOB_DATE_FIELDS = ("Date Found", "Deadline")
APPLICATION_DATE_FIELDS = (
    "Applied Date",
    "Last Touch",
    "Next Follow-up",
    "Interview Date",
)
