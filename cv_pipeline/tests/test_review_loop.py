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

    def breakdown(self, lane, score, version="v4"):
        remaining = float(score)
        out = {}
        rubric = review_scoring.rubric_for(lane, version)
        for dimension, maximum in rubric.items():
            points = min(float(maximum), remaining)
            out[dimension] = points
            remaining = round(remaining - points, 1)
        self.assertAlmostEqual(0.0, remaining, places=1)
        return out

    def buying_intent(
        self,
        verdict="yes",
        ceiling="none",
        strong_shortlist=True,
        spend="worth_a_slot",
    ):
        return {
            "verdict": verdict,
            "ceiling": ceiling,
            "strong_candidate": True,
            "strong_document": True,
            "strong_fit": verdict in {"yes", "mostly"},
            "strong_shortlist": strong_shortlist,
            "spend_recommendation": spend,
            "realistic_competitor": (
                "A directly experienced candidate with comparable technical depth, target-domain delivery, "
                "and evidence of shipped work inside the employer operating environment."
            ),
            "likely_rejection_reason": (
                "The most credible rejection risk is a stronger directly experienced competitor with less domain-transfer burden."
            ),
            "rationale": (
                "The employer core buying intent was tested against the evidence hierarchy and a realistic competing candidate, "
                "with document-fixable weaknesses separated from candidate-history ceilings."
            ),
        }

    def report(self, lane, verdict="approve", issues=None, score=92, **overrides):
        report = {
            "lane": lane,
            "verdict": verdict,
            "score": score,
            "score_breakdown": self.breakdown(lane, score),
            "score_rationale": (
                "The fixed adversarial rubric was applied against the exact evidence and rendered document, "
                "with points withheld for specific residual weaknesses rather than cosmetic preference."
            ),
            "cv_sha256": review_loop.sha256_file(self.cv),
            "issues": issues or [],
            "summary": "Cold independent review complete",
        }
        if lane == "completeness":
            report["selection_audit"] = {
                "risk": "none",
                "strongest_unused_evidence": "none materially stronger",
                "rationale": (
                    "The strongest unused evidence was compared against the weakest included proof and no material selection loss was found."
                ),
            }
        elif lane == "defensibility":
            report["integrity_checks"] = {key: True for key in review_scoring.INTEGRITY_CHECKS}
            report["integrity_rationale"] = (
                "Metric scope, reader inference, attribution, generalisation and CV/CL consistency were challenged explicitly and remained bounded."
            )
        elif lane == "competitiveness":
            report["buying_intent"] = self.buying_intent()
        report.update(overrides)
        return report

    def v3_report(self, lane, verdict="approve", issues=None, score=92):
        return {
            "lane": lane,
            "verdict": verdict,
            "score": score,
            "score_breakdown": self.breakdown(lane, score, "v3"),
            "score_rationale": (
                "The historical v3 fixed rubric was applied against the exact CV evidence and rendered document."
            ),
            "cv_sha256": review_loop.sha256_file(self.cv),
            "issues": issues or [],
            "summary": "Historical scored review complete",
        }

    def legacy_report(self, verdict="approve", issues=None):
        return {
            "verdict": verdict,
            "cv_sha256": review_loop.sha256_file(self.cv),
            "issues": issues or [],
            "summary": "Cold independent review complete",
        }

    def approve_panel(self, state=None, scores=None, buying=None):
        state = state or self.state
        scores = scores or {"completeness": 90, "defensibility": 92, "competitiveness": 90}
        review_loop.record_review(
            state,
            self.report("completeness", score=scores["completeness"]),
            "review-completeness",
            "completeness",
        )
        review_loop.record_review(
            state,
            self.report("defensibility", score=scores["defensibility"]),
            "review-defensibility",
            "defensibility",
        )
        comp = self.report("competitiveness", score=scores["competitiveness"])
        if buying is not None:
            comp["buying_intent"] = buying
        review_loop.record_review(
            state,
            comp,
            "review-competitiveness",
            "competitiveness",
        )

    def latest_panel(self, state=None):
        state = state or self.state
        return [e for e in state["events"] if e.get("type") == "panel"][-1]

    def test_new_state_uses_adversarial_v4_contract(self):
        self.assertEqual("jobhuntai-review-panel-v4", self.state["contract"])
        self.assertEqual(
            {"completeness": 85.0, "defensibility": 90.0, "competitiveness": 85.0},
            self.state["score_policy"]["lane_minimums"],
        )
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

    def test_score_is_required_for_v4(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_review(self.state, self.legacy_report(), "review-a", "completeness")

    def test_breakdown_must_sum_to_score(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        report = self.report("completeness", score=90)
        report["score_breakdown"]["identity_coherence"] -= 1
        with self.assertRaises(review_loop.ReviewLoopError):
            review_loop.record_review(self.state, report, "review-a", "completeness")

    def test_defensibility_below_90_forces_revision(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        self.approve_panel(scores={"completeness": 90, "defensibility": 89, "competitiveness": 90})
        self.assertEqual("revision_required", self.state["status"])
        self.assertIn("SCORE-DEFENSIBILITY", {item["id"] for item in self.latest_panel()["blocking_issues"]})

    def test_competitiveness_below_85_forces_revision(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        self.approve_panel(scores={"completeness": 90, "defensibility": 92, "competitiveness": 84})
        self.assertEqual("revision_required", self.state["status"])
        self.assertIn("SCORE-COMPETITIVENESS", {item["id"] for item in self.latest_panel()["blocking_issues"]})

    def test_panel_average_below_88_forces_revision(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        self.approve_panel(scores={"completeness": 85, "defensibility": 90, "competitiveness": 85})
        panel = self.latest_panel()
        self.assertEqual("revision_required", self.state["status"])
        self.assertEqual(86.7, panel["panel_score"])
        self.assertIn("SCORE-PANEL", {item["id"] for item in panel["blocking_issues"]})

    def test_failed_integrity_check_blocks_without_zeroing_score(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        review_loop.record_review(self.state, self.report("completeness", score=94), "review-a", "completeness")
        report = self.report("defensibility", score=96)
        report["integrity_checks"]["metric_scope_preserved"] = False
        review_loop.record_review(self.state, report, "review-b", "defensibility")
        review_loop.record_review(self.state, self.report("competitiveness", score=94), "review-c", "competitiveness")
        panel = self.latest_panel()
        self.assertEqual(96.0, panel["lane_scores"]["defensibility"])
        self.assertEqual("revision_required", self.state["status"])
        self.assertIn("INTEGRITY-METRIC-SCOPE-PRESERVED", {item["id"] for item in panel["blocking_issues"]})

    def test_material_selection_omission_blocks_high_score(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        report = self.report("completeness", score=95)
        report["selection_audit"] = {
            "risk": "material",
            "strongest_unused_evidence": "Direct target-domain deployed evidence that is stronger than an included generic bullet",
            "rationale": (
                "The CV spends prime space on materially weaker proof while stronger directly relevant evidence remains unused."
            ),
        }
        review_loop.record_review(self.state, report, "review-a", "completeness")
        review_loop.record_review(self.state, self.report("defensibility", score=95), "review-b", "defensibility")
        review_loop.record_review(self.state, self.report("competitiveness", score=95), "review-c", "competitiveness")
        self.assertEqual("revision_required", self.state["status"])
        self.assertIn("SELECTION-MATERIAL-OMISSION", {item["id"] for item in self.latest_panel()["blocking_issues"]})

    def test_document_fixable_buying_intent_partly_blocks(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        buying = self.buying_intent(verdict="partly", ceiling="document", strong_shortlist=False)
        self.approve_panel(buying=buying)
        panel = self.latest_panel()
        self.assertEqual("revision_required", self.state["status"])
        self.assertIn("BUYING-INTENT-DOCUMENT", {item["id"] for item in panel["blocking_issues"]})

    def test_candidate_only_buying_intent_ceiling_does_not_create_endless_rewrite(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        buying = self.buying_intent(verdict="partly", ceiling="candidate", strong_shortlist=False)
        self.approve_panel(
            scores={"completeness": 90, "defensibility": 92, "competitiveness": 90},
            buying=buying,
        )
        panel = self.latest_panel()
        self.assertEqual("approved", self.state["status"])
        self.assertTrue(panel["application_release_approved"])
        self.assertFalse(panel["shortlist_certified"])
        self.assertEqual("candidate", panel["structural_risks"][0]["ceiling"])
        self.assertEqual([], review_loop.verify_release(self.state, self.cv))

    def test_panel_records_scores_and_shortlist_certification(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        self.approve_panel(scores={"completeness": 92, "defensibility": 96, "competitiveness": 94})
        panel = self.latest_panel()
        self.assertEqual(
            {"completeness": 92.0, "defensibility": 96.0, "competitiveness": 94.0},
            panel["lane_scores"],
        )
        self.assertEqual(94.0, panel["panel_score"])
        self.assertTrue(panel["shortlist_certified"])
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

    def test_changed_cv_after_panel_approval_fails_hash_lock(self):
        review_loop.record_tailor(self.state, self.cv, "tailor-agent")
        self.approve_panel()
        self.cv.write_text('{"version": 99}\n', encoding="utf-8")
        codes = {failure["code"] for failure in review_loop.verify_release(self.state, self.cv)}
        self.assertIn("APPROVED_HASH_STALE", codes)

    def test_v3_scored_contract_remains_readable(self):
        state = {
            "contract": review_loop.PANEL_V3_CONTRACT,
            "job_id": "JOB-V3",
            "status": "awaiting_tailor",
            "current_iteration": 0,
            "max_iterations": 2,
            "required_review_lanes": list(review_loop.REVIEW_LANES),
            "score_policy": {"lane_minimum": 85.0, "panel_minimum": 88.0},
            "approved_cv_sha256": None,
            "events": [],
        }
        review_loop.record_tailor(state, self.cv, "tailor-agent")
        review_loop.record_review(state, self.v3_report("completeness", score=92), "review-a", "completeness")
        review_loop.record_review(state, self.v3_report("defensibility", score=94), "review-b", "defensibility")
        review_loop.record_review(state, self.v3_report("competitiveness", score=91), "review-c", "competitiveness")
        self.assertEqual([], review_loop.verify_release(state, self.cv))

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
