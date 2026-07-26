import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lint import lint_cv


class FactualGateTests(unittest.TestCase):
    def test_nested_role_body_supports_summary_number(self):
        cv = {
            "summary": "Forecasting work improved a measured outcome by 15%.",
            "experience": [{"org": "E.ON Energy Markets", "dates": "Jul 2024 - Dec 2025", "roles": [{"title": "Market Analyst", "dates": "Jan 2025 - Dec 2025", "bullets": ["Improved forward-price-curve performance by 15% in far seasons."]}]}],
            "projects": [], "skills": []
        }
        self.assertNotIn("SUMMARY_NUM_NOT_IN_BODY", {code for code, _ in lint_cv(cv)})

    def test_statsbomb_is_not_frame2threat_exclusive(self):
        cv = {
            "summary": "",
            "experience": [],
            "skills": [],
            "projects": [{"title": "Opponent-Adjusted Football Metrics", "tools": "Python, StatsBomb", "link": "github.com/varunrout/opponent-adjusted-metrics", "bullets": ["Built contextual metrics from StatsBomb event data."]}]
        }
        self.assertNotIn("ATTRIBUTION_ERROR", {code for code, _ in lint_cv(cv)})

    def test_frame2threat_architecture_remains_exclusive(self):
        cv = {
            "summary": "",
            "experience": [],
            "skills": [],
            "projects": [{"title": "Opponent-Adjusted Football Metrics", "tools": "Python", "link": "github.com/varunrout/opponent-adjusted-metrics", "bullets": ["Built PossessionGRU for sequence modelling."]}]
        }
        self.assertIn("ATTRIBUTION_ERROR", {code for code, _ in lint_cv(cv)})


if __name__ == "__main__":
    unittest.main()
