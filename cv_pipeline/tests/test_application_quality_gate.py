import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import application_quality_gate
import cv_length_gate
import review_loop


class ApplicationQualityGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temp.name)
        for name, content in {
            "job_description.md": "JD",
            "role_identity.json": '{"archetype": "data_scientist"}',
            "evidence_ranking.json": '{"ranked": []}',
            "cv.json": '{"candidate": "Varun", "summary": "Python SQL classification"}',
            "cv_diagnostic.json": '{"passed": true}',
            "cv.pdf": "%PDF-test",
        }.items():
            (self.run_dir / name).write_text(content, encoding="utf-8")

        state = review_loop.create_state("JOB-1")
        cv_path = self.run_dir / "cv.json"
        review_loop.record_tailor(state, cv_path, "tailor-agent")
        report = {
            "verdict": "approve",
            "cv_sha256": review_loop.sha256_file(cv_path),
            "issues": [],
            "summary": "Clean",
        }
        review_loop.record_review(state, report, "review-agent")
        review_loop.write_json(self.run_dir / "review_loop.json", state)

        cv_length_audit = {
            "contract": cv_length_gate.CONTRACT,
            "strategy_decision": cv_length_gate.ONE_PAGE_ALLOWED,
            "strategy_rationale": "A narrow junior profile with one compact evidence set can be represented completely on one page.",
            "final_page_count": 1,
            "candidate_role_profile": {
                "seniority": "junior",
                "relevant_years": 1,
                "relevant_roles": 1,
                "relevant_projects": 0,
                "technical_breadth": 2,
                "domain_transfer_required": False,
            },
            "essential_evidence": [{"id": "python", "match_any": ["Python"]}],
            "omissions": [],
            "review_judgement": {
                "material_evidence_removed": False,
                "omission_audit_complete": True,
                "page_strategy_approved": True,
                "rationale": "The final one-page CV retains the complete role-critical evidence set without compression loss.",
                "review_actor": "review-agent",
                "review_iteration": 1,
                "cv_sha256": review_loop.sha256_file(cv_path),
            },
            "page_transition": {},
            "page_fill": [0.9],
        }
        (self.run_dir / "cv_length_audit.json").write_text(json.dumps(cv_length_audit), encoding="utf-8")

        self.manifest = {
            "contract": "jobhuntai-application-quality-v1",
            "decision": "apply",
            "artefacts": {
                "job_description": "job_description.md",
                "role_identity": "role_identity.json",
                "evidence_ranking": "evidence_ranking.json",
                "cv": "cv.json",
                "cv_diagnostic": "cv_diagnostic.json",
                "cv_length_audit": "cv_length_audit.json",
                "cv_pdf": "cv.pdf",
                "review_loop": "review_loop.json",
            },
            "checks": {
                "preflight": {"status": "passed"},
                "duplicate": {"status": "passed", "outcome": "clear"},
                "visa": {"status": "passed", "outcome": "viable"},
                "role_identity": {"status": "passed"},
                "evidence": {"status": "passed"},
                "cv_length": {"status": "passed"},
                "factual": {"status": "passed"},
                "positioning": {"status": "passed"},
                "visual": {"status": "passed"},
                "render": {"status": "passed"},
            },
            "tracker": {"status": "checked", "mode": "read_only"},
            "drive_save": {"status": "verified"},
        }
        (self.run_dir / "application_manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def run_gate(self):
        return application_quality_gate.run(self.run_dir, self.run_dir / "application_manifest.json")

    def write_manifest(self):
        (self.run_dir / "application_manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def test_clean_package_passes(self):
        self.assertEqual([], self.run_gate())

    def test_review_loop_is_mandatory(self):
        self.manifest["artefacts"].pop("review_loop")
        self.write_manifest()
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("REVIEW_LOOP_PATH_MISSING", codes)

    def test_cv_length_audit_is_mandatory(self):
        self.manifest["artefacts"].pop("cv_length_audit")
        self.write_manifest()
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("CV_LENGTH_AUDIT_PATH_MISSING", codes)

    def test_failed_cv_length_check_blocks_release(self):
        self.manifest["checks"]["cv_length"]["status"] = "failed"
        self.write_manifest()
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("CV_LENGTH_NOT_PASSED", codes)

    def test_failed_visual_check_blocks_release(self):
        self.manifest["checks"]["visual"]["status"] = "failed"
        self.write_manifest()
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("VISUAL_NOT_PASSED", codes)

    def test_duplicate_application_blocks_release(self):
        self.manifest["checks"]["duplicate"]["outcome"] = "existing_application"
        self.write_manifest()
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("DUPLICATE_BLOCKED", codes)

    def test_unverified_drive_save_blocks_release(self):
        self.manifest["drive_save"]["status"] = "assumed"
        self.write_manifest()
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("DRIVE_SAVE_UNVERIFIED", codes)


if __name__ == "__main__":
    unittest.main()
