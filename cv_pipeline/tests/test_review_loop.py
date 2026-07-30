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
            "summary": "Independent review complete",
        }

    def test_approval_requires_tailor_then_independent_review(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report(), "review-agent")
        self.assertEqual([], review_loop.verify_release(self.state, self.cv))

    def test_same_actor_cannot_review_own_tailoring(self):
        review_loop.record_tailor(self.state, self.cv, "agent")
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_review(self.state, self.report(), "agent")

    def test_revision_forces_retailor_and_issue_closure(self):
        issue = {
            "id": "FACT-1",
            "severity": "critical",
            "status": "open",
            "message": "Official title is wrong",
            "required_action": "Restore the canonical title",
        }
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report("revise", [issue]), "review-agent")
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        self.cv.write_text('{"version": 2}\n', encoding="utf-8")
        review_loop.record_tailor(self.state, self.cv, "tailor-agent", ["FACT-1"])
        review_loop.record_review(self.state, self.report(), "review-agent")
        self.assertEqual("approved", self.state["status"])
        self.assertEqual(2, self.state["current_iteration"])

    def test_changed_cv_after_approval_fails_hash_lock(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report(), "review-agent")
        self.cv.write_text('{"version": 99}\n', encoding="utf-8")
        codes = {failure["code"] for failure in review_loop.verify_release(self.state, self.cv)}
        self.assertIn("APPROVED_HASH_STALE", codes)

    def test_approval_cannot_hide_open_issues(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        issue = {
            "id": "VIS-1",
            "severity": "major",
            "status": "open",
            "message": "Second page is sparse",
            "required_action": "Rebalance relevant evidence",
        }
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_review(self.state, self.report("approve", [issue]), "review-agent")


if __name__ == "__main__":
    unittest.main()
