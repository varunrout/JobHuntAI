import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import selected_impact_gate


class SelectedImpactGateTests(unittest.TestCase):
    def test_absent_selected_impact_is_allowed(self):
        self.assertEqual(selected_impact_gate.validate_payload({}), [])

    def test_selected_impact_without_explicit_approval_is_blocked(self):
        failures = selected_impact_gate.validate_payload({
            "selected_impact": [
                {"headline": "Impact", "bullets": ["Delivered a measurable outcome."]}
            ]
        })
        self.assertEqual(failures[0][0], "SELECTED_IMPACT_EXPLICIT_APPROVAL_REQUIRED")

    def test_selected_impact_cannot_be_authorised_by_inferred_source(self):
        failures = selected_impact_gate.validate_payload({
            "selected_impact": [
                {"headline": "Impact", "bullets": ["Delivered a measurable outcome."]}
            ],
            "selected_impact_approval": {
                "approved": True,
                "source": "archetype_default"
            }
        })
        self.assertEqual(failures[0][0], "SELECTED_IMPACT_EXPLICIT_APPROVAL_REQUIRED")

    def test_selected_impact_with_run_specific_explicit_user_approval_is_allowed(self):
        failures = selected_impact_gate.validate_payload({
            "selected_impact": [
                {"headline": "Impact", "bullets": ["Delivered a measurable outcome."]}
            ],
            "selected_impact_approval": {
                "approved": True,
                "source": "explicit_user_instruction"
            }
        })
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
