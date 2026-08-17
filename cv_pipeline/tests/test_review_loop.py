import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import review_loop


class ReviewLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cv = self.root / "cv.json"
        self.cv.write_text('{"version": 1}\n', encoding="utf-8")
        self.state = review_loop.create_state("JOB-1", max_iterations=3)

    def tearDown(self):
        self.temp.cleanup()

    def report(self, verdict="approve", issues=None):
        return {
            "verdict": verdict,
            "cv_sha256": review_loop.sha256_file(self.cv),
            "issues": issues or [],
            "summary": "Cold independent review complete",
        }

    def approve_panel(self, state=None):
        state = state or self.state
        review_loop.record_review(state, self.report(), "review-completeness", "completeness")
        review_loop.record_review(state, self.report(), "review-defensibility", "defensibility")
        review_loop.record_review(state, self.report(), "review-competitiveness", "competitiveness")

    def test_release_requires_all_three_cold_review_lanes(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report(), "review-a", "completeness")
        self.assertEqual("awaiting_reviews", self.state["status"])
        codes = {item["code"] for item in review_loop.verify_release(self.state, self.cv)}
        self.assertIn("REVIEW_PANEL_NOT_APPROVED", codes)
        review_loop.record_review(self.state, self.report(), "review-b", "defensibility")
        review_loop.record_review(self.state, self.report(), "review-c", "competitiveness")
        self.assertEqual([], review_loop.verify_release(self.state, self.cv))

    def test_tailor_and_reviewers_must_all_be_distinct(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_review(self.state, self.report(), "tailor-agent", "completeness")
        review_loop.record_review(self.state, self.report(), "review-a", "completeness")
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_review(self.state, self.report(), "review-a", "defensibility")

    def test_duplicate_lane_is_blocked(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report(), "review-a", "completeness")
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_review(self.state, self.report(), "review-b", "completeness")

    def test_major_issue_from_one_lane_forces_retailor(self):
        issue = {
            "id": "DEF-001",
            "severity": "major",
            "status": "open",
            "message": "One claim is not sufficiently evidenced",
            "required_action": "Replace it with banked evidence",
        }
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report(), "review-a", "completeness")
        review_loop.record_review(self.state, self.report("revise", [issue]), "review-b", "defensibility")
        review_loop.record_review(self.state, self.report(), "review-c", "competitiveness")
        self.assertEqual("revision_required", self.state["status"])
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        self.cv.write_text('{"version": 2}\n', encoding="utf-8")
        review_loop.record_tailor(self.state, self.cv, "tailor-agent", ["DEF-001"])
        self.approve_panel()
        self.assertEqual("approved", self.state["status"])
        self.assertEqual(2, self.state["current_iteration"])

    def test_open_minor_note_may_survive_panel_approval(self):
        minor = {
            "id": "COMP-009",
            "severity": "minor",
            "status": "open",
            "message": "A phrase could be slightly tighter",
            "required_action": "Optional wording polish",
        }
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report("approve", [minor]), "review-a", "completeness")
        review_loop.record_review(self.state, self.report(), "review-b", "defensibility")
        review_loop.record_review(self.state, self.report(), "review-c", "competitiveness")
        self.assertEqual("approved", self.state["status"])
        panel = [e for e in self.state["events"] if e.get("type") == "panel"][-1]
        self.assertEqual(1, len(panel["minor_open_issues"]))

    def test_changed_cv_after_panel_approval_fails_hash_lock(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        self.approve_panel()
        self.cv.write_text('{"version": 99}\n', encoding="utf-8")
        codes = {failure["code"] for failure in review_loop.verify_release(self.state, self.cv)}
        self.assertIn("APPROVED_HASH_STALE", codes)

    def test_iteration_exhaustion_sets_blocked_state(self):
        state = review_loop.create_state("JOB-2", max_iterations=1)
        review_loop.record_tailor(state, self.cv, "tailor-agent")
        issue = {
            "id": "COMP-001",
            "severity": "critical",
            "status": "open",
            "message": "Hiring case is incomplete",
            "required_action": "Restore missing role-critical evidence",
        }
        review_loop.record_review(state, self.report("revise", [issue]), "review-a", "completeness")
        review_loop.record_review(state, self.report(), "review-b", "defensibility")
        review_loop.record_review(state, self.report(), "review-c", "competitiveness")
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_tailor(state, self.cv, "tailor-agent", ["COMP-001"])
        self.assertEqual("blocked", state["status"])

    def test_legacy_single_reviewer_contract_remains_readable(self):
        state = {
            "contract": review_loop.LEGACY_CONTRACT,
            "job_id": "JOB-LEGACY",
            "status": "awaiting_tailor",
            "current_iteration": 0,
            "max_iterations": 2,
            "approved_cv_sha256": None,
            "events": [],
        }
        review_loop.record_tailor(state, self.cv, "tailor-agent")
        review_loop.record_review(state, self.report(), "review-agent")
        self.assertEqual([], review_loop.verify_release(state, self.cv))


if __name__ == "__main__":
    unittest.main()
