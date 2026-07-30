import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import application_quality_gate
import review_loop


class LiveApplicationReleaseSmokeTest(unittest.TestCase):
    def write_json(self, path, payload):
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_review_failure_retailor_approval_and_release_hash_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            cv_path = run_dir / "cv.json"
            state_path = run_dir / "review_loop.json"

            self.write_json(cv_path, {"version": 1, "summary": "Initial tailored CV"})
            state = review_loop.create_state("SMOKE-JOB-1", max_iterations=4)
            review_loop.record_tailor(state, cv_path, "tailor-agent")

            first_hash = review_loop.sha256_file(cv_path)
            review_loop.record_review(
                state,
                {
                    "verdict": "revise",
                    "cv_sha256": first_hash,
                    "summary": "Title and positioning require correction",
                    "issues": [
                        {
                            "id": "FACT-1",
                            "severity": "critical",
                            "status": "open",
                            "message": "Official title is incorrect",
                            "required_action": "Restore the canonical title",
                        },
                        {
                            "id": "POS-1",
                            "severity": "major",
                            "status": "open",
                            "message": "Professional identity is unclear",
                            "required_action": "Align headline, summary and first proof points",
                        },
                    ],
                },
                "independent-review-agent",
            )
            self.assertEqual("revision_required", state["status"])

            self.write_json(cv_path, {"version": 2, "summary": "Corrected and consistently positioned CV"})
            review_loop.record_tailor(state, cv_path, "tailor-agent", ["FACT-1", "POS-1"])
            final_hash = review_loop.sha256_file(cv_path)
            review_loop.record_review(
                state,
                {
                    "verdict": "approve",
                    "cv_sha256": final_hash,
                    "summary": "Factual, positioning and visual review passed",
                    "issues": [],
                },
                "independent-review-agent",
            )
            review_loop.write_json(state_path, state)
            self.assertEqual([], review_loop.verify_release(state, cv_path))

            self.write_json(run_dir / "role_identity.json", {"archetype": "forecasting_pricing_analyst"})
            self.write_json(run_dir / "evidence_ranking.json", {"ranked": ["verified-evidence"]})
            self.write_json(run_dir / "cv_diagnostic.json", {"status": "passed"})
            (run_dir / "job_description.txt").write_text("Smoke test job description\n", encoding="utf-8")
            (run_dir / "cv.pdf").write_bytes(b"%PDF-1.4 smoke-test")

            passed = {"status": "passed"}
            manifest = {
                "contract": "jobhuntai-application-quality-v1",
                "decision": "apply",
                "artefacts": {
                    "job_description": "job_description.txt",
                    "role_identity": "role_identity.json",
                    "evidence_ranking": "evidence_ranking.json",
                    "cv": "cv.json",
                    "cv_diagnostic": "cv_diagnostic.json",
                    "cv_pdf": "cv.pdf",
                    "review_loop": "review_loop.json",
                },
                "checks": {
                    "preflight": dict(passed),
                    "duplicate": {"status": "passed", "outcome": "clear"},
                    "visa": {"status": "passed", "outcome": "viable"},
                    "role_identity": dict(passed),
                    "evidence": dict(passed),
                    "factual": dict(passed),
                    "positioning": dict(passed),
                    "visual": dict(passed),
                    "render": dict(passed),
                },
                "tracker": {"status": "checked", "mode": "read_only"},
                "drive_save": {"status": "verified"},
            }
            manifest_path = run_dir / "application_manifest.json"
            self.write_json(manifest_path, manifest)
            self.assertEqual([], application_quality_gate.run(run_dir, manifest_path))

            self.write_json(cv_path, {"version": 3, "summary": "Unreviewed post-approval edit"})
            codes = {item["code"] for item in application_quality_gate.run(run_dir, manifest_path)}
            self.assertIn("APPROVED_HASH_STALE", codes)


if __name__ == "__main__":
    unittest.main()
