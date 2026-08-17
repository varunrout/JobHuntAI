import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import review_loop
import review_scoring


class ReviewLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cv = self.root / "cv.json"
        self.cv.write_text('{"version": 1}\n', encoding="utf-8")
        self.state = review_loop.create_state("JOB-1", max_iterations=3)

    def tearDown(self):
        self.temp.cleanup()

    def breakdown(self, lane, score):
        remaining = float(score)
        out = {}
        for dimension, maximum in review_scoring.LANE_RUBRICS[lane].items():
            points = min(float(maximum), remaining)
            out[dimension] = points
            remaining = round(remaining - points, 1)
        self.assertAlmostEqual(0.0, remaining, places=1)
        return out

    def report(self, lane, verdict="approve", issues=None, score=92):
        return {
            "lane": lane,
            "verdict": verdict,
            "score": score,
            "score_breakdown": self.breakdown(lane, score),
            "score_rationale": "The fixed rubric was applied against the exact CV evidence and rendered document, with points withheld where appropriate.",
            "cv_sha256": review_loop.sha256_file(self.cv),
            "issues": issues or [],
            "summary": "Cold independent review complete",
        }

    def legacy_report(self, verdict="approve", issues=None):
        return {
            "verdict": verdict,
            "cv_sha256": review_loop.sha256_file(self.cv),
            "issues": issues or [],
            "summary": "Cold independent review complete",
        }

    def approve_panel(self, state=None, scores=None):
        state = state or self.state
        scores = scores or {"completeness": 92, "defensibility": 94, "competitiveness": 91}
        review_loop.record_review(state, self.report("completeness", score=scores["completeness"]), "review-completeness", "completeness")
        review_loop.record_review(state, self.report("defensibility", score=scores["defensibility"]), "review-defensibility", "defensibility")
        review_loop.record_review(state, self.report("competitiveness", score=scores["competitiveness"]), "review-competitiveness", "competitiveness")

    def test_new_state_uses_scored_v3_contract(self):
        self.assertEqual("jobhuntai-review-panel-v3", self.state["contract"])
        self.assertEqual(85.0, self.state["score_policy"]["lane_minimum"])
        self.assertEqual(88.0, self.state["score_policy"]["panel_minimum"])

    def test_release_requires_all_three_cold_review_lanes(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report("completeness"), "review-a", "completeness")
        self.assertEqual("awaiting_reviews", self.state["status"])
        codes = {item["code"] for item in review_loop.verify_release(self.state, self.cv)}
        self.assertIn("REVIEW_PANEL_NOT_APPROVED", codes)
        review_loop.record_review(self.state, self.report("defensibility"), "review-b", "defensibility")
        review_loop.record_review(self.state, self.report("competitiveness"), "review-c", "competitiveness")
        self.assertEqual([], review_loop.verify_release(self.state, self.cv))

    def test_tailor_and_reviewers_must_all_be_distinct(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_review(self.state, self.report("completeness"), "tailor-agent", "completeness")
        review_loop.record_review(self.state, self.report("completeness"), "review-a", "completeness")
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_review(self.state, self.report("defensibility"), "review-a", "defensibility")

    def test_duplicate_lane_is_blocked(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report("completeness"), "review-a", "completeness")
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_review(self.state, self.report("completeness"), "review-b", "completeness")

    def test_score_is_required_for_v3(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_review(self.state, self.legacy_report(), "review-a", "completeness")

    def test_breakdown_must_sum_to_score(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        report = self.report("completeness", score=92)
        report["score_breakdown"]["identity_coherence"] -= 1
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_review(self.state, report, "review-a", "completeness")

    def test_lane_score_below_85_forces_revision_even_with_approve(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report("completeness", score=82), "review-a", "completeness")
        review_loop.record_review(self.state, self.report("defensibility", score=94), "review-b", "defensibility")
        review_loop.record_review(self.state, self.report("competitiveness", score=92), "review-c", "competitiveness")
        self.assertEqual("revision_required", self.state["status"])
        panel = [e for e in self.state["events"] if e.get("type") == "panel"][-1]
        self.assertIn("SCORE-COMPLETENESS", {item["id"] for item in panel["blocking_issues"]})

    def test_panel_average_below_88_forces_revision(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report("completeness", score=85), "review-a", "completeness")
        review_loop.record_review(self.state, self.report("defensibility", score=85), "review-b", "defensibility")
        review_loop.record_review(self.state, self.report("competitiveness", score=90), "review-c", "competitiveness")
        self.assertEqual("revision_required", self.state["status"])
        panel = [e for e in self.state["events"] if e.get("type") == "panel"][-1]
        self.assertEqual(86.7, panel["panel_score"])
        self.assertIn("SCORE-PANEL", {item["id"] for item in panel["blocking_issues"]})

    def test_panel_records_lane_scores_and_average(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        self.approve_panel(scores={"completeness": 92, "defensibility": 96, "competitiveness": 94})
        panel = [e for e in self.state["events"] if e.get("type") == "panel"][-1]
        self.assertEqual({"completeness": 92.0, "defensibility": 96.0, "competitiveness": 94.0}, panel["lane_scores"])
        self.assertEqual(94.0, panel["panel_score"])
        self.assertEqual("approved", self.state["status"])

    def test_major_issue_from_one_lane_forces_retailor(self):
        issue = {
            "id": "DEF-001",
            "severity": "major",
            "status": "open",
            "message": "One claim is not sufficiently evidenced",
            "required_action": "Replace it with banked evidence",
        }
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report("completeness"), "review-a", "completeness")
        review_loop.record_review(self.state, self.report("defensibility", "revise", [issue]), "review-b", "defensibility")
        review_loop.record_review(self.state, self.report("competitiveness"), "review-c", "competitiveness")
        self.assertEqual("revision_required", self.state["status"])
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        self.cv.write_text('{"version": 2}\n', encoding="utf-8")
        review_loop.record_tailor(self.state, self.cv, "tailor-agent", ["DEF-001"])
        self.approve_panel()
        self.assertEqual("approved", self.state["status"])
        self.assertEqual(2, self.state["current_iteration"])

    def test_explicit_revise_minor_issue_is_required_on_retailor(self):
        issue = {
            "id": "COMPET-009",
            "severity": "minor",
            "status": "open",
            "message": "Reviewer explicitly requires a small recruiter-clarity change",
            "required_action": "Tighten the opening phrase before release",
        }
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report("completeness"), "review-a", "completeness")
        review_loop.record_review(self.state, self.report("defensibility"), "review-b", "defensibility")
        review_loop.record_review(self.state, self.report("competitiveness", "revise", [issue]), "review-c", "competitiveness")
        self.assertEqual("revision_required", self.state["status"])
        panel = [e for e in self.state["events"] if e.get("type") == "panel"][-1]
        self.assertEqual(["COMPET-009"], [item["id"] for item in panel["blocking_issues"]])
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        self.cv.write_text('{"version": 2}\n', encoding="utf-8")
        review_loop.record_tailor(self.state, self.cv, "tailor-agent", ["COMPET-009"])

    def test_open_minor_note_may_survive_panel_approval(self):
        minor = {
            "id": "COMP-009",
            "severity": "minor",
            "status": "open",
            "message": "A phrase could be slightly tighter",
            "required_action": "Optional wording polish",
        }
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report("completeness", "approve", [minor]), "review-a", "completeness")
        review_loop.record_review(self.state, self.report("defensibility"), "review-b", "defensibility")
        review_loop.record_review(self.state, self.report("competitiveness"), "review-c", "competitiveness")
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
        review_loop.record_review(state, self.report("completeness", "revise", [issue]), "review-a", "completeness")
        review_loop.record_review(state, self.report("defensibility"), "review-b", "defensibility")
        review_loop.record_review(state, self.report("competitiveness"), "review-c", "competitiveness")
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_tailor(state, self.cv, "tailor-agent", ["COMP-001"])
        self.assertEqual("blocked", state["status"])

    def test_v2_three_reviewer_contract_remains_readable(self):
        state = {
            "contract": review_loop.PANEL_V2_CONTRACT,
            "job_id": "JOB-V2",
            "status": "awaiting_tailor",
            "current_iteration": 0,
            "max_iterations": 2,
            "required_review_lanes": list(review_loop.REVIEW_LANES),
            "approved_cv_sha256": None,
            "events": [],
        }
        review_loop.record_tailor(state, self.cv, "tailor-agent")
        review_loop.record_review(state, self.legacy_report(), "review-a", "completeness")
        review_loop.record_review(state, self.legacy_report(), "review-b", "defensibility")
        review_loop.record_review(state, self.legacy_report(), "review-c", "competitiveness")
        self.assertEqual([], review_loop.verify_release(state, self.cv))

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
        review_loop.record_review(state, self.legacy_report(), "review-agent")
        self.assertEqual([], review_loop.verify_release(state, self.cv))


if __name__ == "__main__":
    unittest.main()
