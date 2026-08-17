import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import application_quality_gate
import cv_length_gate
import review_loop


class ReviewPanelIntegrationTests(unittest.TestCase):
    def panel_state(self):
        return {
            "contract": review_loop.CONTRACT,
            "events": [
                {"type": "tailor", "iteration": 1, "actor": "tailor-agent", "cv_sha256": "a" * 64},
                {"type": "review", "lane": "defensibility", "iteration": 1, "actor": "review-defensibility", "cv_sha256": "a" * 64, "verdict": "approve"},
                {"type": "review", "lane": "completeness", "iteration": 1, "actor": "review-completeness", "cv_sha256": "a" * 64, "verdict": "approve"},
                {"type": "review", "lane": "competitiveness", "iteration": 1, "actor": "review-competitiveness", "cv_sha256": "a" * 64, "verdict": "approve"},
            ],
        }

    def test_cv_length_judgement_is_owned_by_completeness(self):
        event = cv_length_gate._length_review_event(self.panel_state())
        self.assertEqual("review-completeness", event["actor"])

    def test_rendered_visual_review_is_owned_by_competitiveness(self):
        self.assertEqual("review-competitiveness", application_quality_gate._latest_review_actor(self.panel_state()))

    def test_legacy_visual_actor_still_uses_latest_review(self):
        state = {"contract": review_loop.LEGACY_CONTRACT, "events": [{"type": "review", "actor": "legacy-reviewer"}]}
        self.assertEqual("legacy-reviewer", application_quality_gate._latest_review_actor(state))


if __name__ == "__main__":
    unittest.main()
