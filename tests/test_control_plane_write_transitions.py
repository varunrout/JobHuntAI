from __future__ import annotations

import unittest

from jobhuntai_core.repository import validated_write


class WriteTransitionTests(unittest.TestCase):
    def test_illegal_job_status_regression_blocks_before_transport(self):
        writes = []
        previous = {
            "Job ID": "JOB-2026-000525",
            "Company": "Example",
            "Role Title": "Analyst",
            "Status": "Applied",
            "CV Version Needed": "Commercial_Data_Analyst",
        }
        proposed = {**previous, "Status": "Saved"}

        with self.assertRaisesRegex(ValueError, "ILLEGAL_STATE_TRANSITION"):
            validated_write(
                entity="job",
                proposed_row=proposed,
                previous_row=previous,
                existing_job_ids={"JOB-2026-000525"},
                write_row=lambda payload: writes.append(dict(payload)),
                read_row=lambda: proposed,
                audit=lambda *args: None,
                reason="regression attempt",
            )

        self.assertEqual([], writes)

    def test_terminal_application_transition_is_allowed_and_audit_carries_provenance(self):
        stored = {}
        audits = []
        previous = {
            "Application ID": "APP-0044",
            "Job ID": "JOB-2026-000525",
            "Company": "Example",
            "Role Title": "Analyst",
            "Status": "Applied",
            "Stage": "Application",
            "Outcome": "Pending",
            "CV Version Used": "Commercial_Data_Analyst",
        }
        proposed = {
            **previous,
            "Status": "Rejected",
            "Stage": "Closed",
            "Outcome": "Rejected",
        }

        result = validated_write(
            entity="application",
            proposed_row=proposed,
            previous_row=previous,
            existing_job_ids={"JOB-2026-000525"},
            write_row=lambda payload: stored.update(payload),
            read_row=lambda: dict(stored),
            audit=lambda *args: audits.append(args),
            reason="mail outcome refresh",
            source="Gmail",
            actor="JobHuntAI",
        )

        self.assertEqual("APP-0044", result.entity_id)
        self.assertTrue(audits)
        self.assertTrue(all(event[-3:] == ("mail outcome refresh", "Gmail", "JobHuntAI") for event in audits))


if __name__ == "__main__":
    unittest.main()
