from __future__ import annotations

import unittest

from jobhuntai_core.doctor import run_doctor
from jobhuntai_core.ids import IdCollisionError, next_application_id, next_job_id
from jobhuntai_core.repository import PostWriteMismatch, validated_write
from jobhuntai_core.state import application_transition, job_transition
from jobhuntai_core.validators import validate_application, validate_job


class IdTests(unittest.TestCase):
    def test_job_allocator_scans_sheet_outputs_and_counter(self):
        job_id, seq = next_job_id(
            job_ids=["JOB-2026-000524"],
            folder_names=["JOB-2026-000525_Company_Role"],
            sequence=524,
        )
        self.assertEqual((job_id, seq), ("JOB-2026-000526", 526))

    def test_duplicate_job_id_blocks(self):
        with self.assertRaises(IdCollisionError):
            next_job_id(
                job_ids=["JOB-2026-000100", "JOB-2026-000100"],
                folder_names=[],
                sequence=100,
            )

    def test_application_allocator_is_monotonic(self):
        app_id, seq = next_application_id(
            application_ids=["APP-0001", "APP-0043"], sequence=43
        )
        self.assertEqual((app_id, seq), ("APP-0044", 44))


class ValidationTests(unittest.TestCase):
    def test_dangling_application_job_id_blocks(self):
        row = {
            "Application ID": "APP-0044",
            "Job ID": "JOB-2026-000999",
            "Company": "Example",
            "Role Title": "Analyst",
            "Status": "Applied",
            "Stage": "Application",
        }
        codes = {v.code for v in validate_application(row, existing_job_ids=set())}
        self.assertIn("DANGLING_JOB_ID", codes)

    def test_displaced_application_cells_are_detected_by_shape(self):
        row = {
            "Application ID": "APP-0013",
            "Job ID": "JOB-2026-000422",
            "Company": "Cobblestone Energy",
            "Role Title": "Junior Data Scientist",
            "Status": "Interviewing",
            "Stage": "Rejected",
            "Contact Email": "Rebecca Eyotaru",
            "Last Touch": "recruitment@cobblestoneenergy.com",
        }
        codes = {
            v.code
            for v in validate_application(
                row, existing_job_ids={"JOB-2026-000422"}
            )
        }
        self.assertIn("INVALID_APPLICATION_STAGE", codes)
        self.assertIn("INVALID_EMAIL_SHAPE", codes)
        self.assertIn("INVALID_DATE_FORMAT", codes)

    def test_noncanonical_date_blocks(self):
        row = {
            "Job ID": "JOB-2026-000010",
            "Company": "Pluto",
            "Role Title": "Data Scientist",
            "Status": "Applied",
            "Date Found": "29 Jul 2026",
            "CV Version Needed": "Applied_Data_Scientist",
        }
        codes = {v.code for v in validate_job(row)}
        self.assertIn("INVALID_DATE_FORMAT", codes)

    def test_strategic_score_in_fit_score_is_flagged(self):
        row = {
            "Job ID": "JOB-2026-000006",
            "Company": "Mustard Systems",
            "Role Title": "Quantitative Analyst",
            "Status": "Applied",
            "Fit Score": 29,
            "Notes": "Strategic fit 29/35.",
            "CV Version Needed": "Applied_Data_Scientist",
        }
        codes = {v.code for v in validate_job(row)}
        self.assertIn("FIT_SCORE_SCALE_AMBIGUOUS", codes)

    def test_unsanctioned_cv_mode_blocks(self):
        row = {
            "Job ID": "JOB-2026-000001",
            "Company": "Example",
            "Role Title": "Analyst",
            "Status": "Applied",
            "CV Version Needed": "Energy Forecasting & Risk CV",
        }
        codes = {v.code for v in validate_job(row)}
        self.assertIn("INVALID_CV_MODE", codes)


class StateTests(unittest.TestCase):
    def test_job_and_application_lattices_are_separate(self):
        self.assertTrue(job_transition("Saved", "Applied").allowed)
        self.assertTrue(application_transition("Applied", "Interviewing").allowed)
        self.assertFalse(application_transition("Interviewing", "Applied").allowed)

    def test_terminal_application_is_absorbing(self):
        transition = application_transition("Rejected", "Interviewing")
        self.assertFalse(transition.allowed)
        self.assertEqual(transition.kind, "frozen")


class RepositoryTests(unittest.TestCase):
    def test_success_is_reported_only_after_readback_matches(self):
        stored = {}
        audits = []
        row = {
            "Job ID": "JOB-2026-000525",
            "Company": "Example",
            "Role Title": "Data Analyst",
            "Status": "Saved",
            "CV Version Needed": "Commercial_Data_Analyst",
        }

        def write(payload):
            stored.update(payload)

        def read():
            return dict(stored)

        def audit(*args):
            audits.append(args)

        result = validated_write(
            entity="job",
            proposed_row=row,
            previous_row=None,
            existing_job_ids=set(),
            write_row=write,
            read_row=read,
            audit=audit,
            reason="test",
        )
        self.assertEqual(result.entity_id, "JOB-2026-000525")
        self.assertTrue(audits)

    def test_readback_mismatch_blocks_success(self):
        row = {
            "Job ID": "JOB-2026-000525",
            "Company": "Example",
            "Role Title": "Data Analyst",
            "Status": "Saved",
            "CV Version Needed": "Commercial_Data_Analyst",
        }

        with self.assertRaises(PostWriteMismatch):
            validated_write(
                entity="job",
                proposed_row=row,
                previous_row=None,
                existing_job_ids=set(),
                write_row=lambda payload: None,
                read_row=lambda: {**row, "Company": "Wrong Company"},
                audit=lambda *args: None,
                reason="test",
            )


class DoctorTests(unittest.TestCase):
    def test_doctor_finds_duplicate_output_prefix_and_legacy_name(self):
        jobs = [
            {
                "Job ID": "JOB-2026-000001",
                "Company": "Example",
                "Role Title": "Analyst",
                "Status": "Saved",
                "CV Version Needed": "Commercial_Data_Analyst",
            }
        ]
        findings = run_doctor(
            jobs=jobs,
            applications=[],
            output_folder_names=[
                "JOB-2026-000001_Example_Analyst",
                "JOB-2026-000001 - Example - Analyst",
                "ASOS - Applied Scientist, Forecasting",
            ],
        )
        codes = {f.code for f in findings}
        self.assertIn("DUPLICATE_OUTPUT_JOB_ID", codes)
        self.assertIn("NONCANONICAL_OUTPUT_NAME", codes)
        self.assertIn("UNLINKED_OUTPUT_FOLDER", codes)


if __name__ == "__main__":
    unittest.main()
