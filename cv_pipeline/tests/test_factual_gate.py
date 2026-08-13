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

    def test_locked_independent_practice_is_not_treated_as_employment_title(self):
        cv = {
            "summary": "",
            "experience": [{
                "experience_type": "independent_practice",
                "title": "Independent Data Science Research & Engineering",
                "org": "Independent Practice",
                "dates": "Jan 2026 - Present",
                "evidence_refs": ["frame2threat", "energy-market-tracker"],
                "bullets": [
                    "Developing reproducible modelling and analytical workflows across independently maintained technical projects.",
                    "Using benchmark comparison and documented evaluation to test whether more complex modelling adds useful analytical value."
                ]
            }],
            "projects": [],
            "skills": []
        }
        codes = {code for code, _ in lint_cv(cv)}
        self.assertNotIn("BAD_TITLE", codes)
        self.assertNotIn("DS_TITLE_MISUSE", codes)
        self.assertNotIn("BAD_INDEPENDENT_TITLE", codes)
        self.assertNotIn("INDEPENDENT_EVIDENCE_REFS", codes)
        self.assertNotIn("INDEPENDENT_UNKNOWN_REF", codes)

    def test_independent_practice_title_is_locked(self):
        cv = {
            "summary": "",
            "experience": [{
                "experience_type": "independent_practice",
                "title": "Independent Data Scientist",
                "org": "Independent Practice",
                "dates": "Jan 2026 - Present",
                "evidence_refs": ["frame2threat", "energy-market-tracker"],
                "bullets": ["Developing independently maintained data science projects with reproducible evaluation."]
            }],
            "projects": [],
            "skills": []
        }
        self.assertIn("BAD_INDEPENDENT_TITLE", {code for code, _ in lint_cv(cv)})

    def test_independent_practice_requires_traceable_refs(self):
        cv = {
            "summary": "",
            "experience": [{
                "experience_type": "independent_practice",
                "title": "Independent Data Science Research & Engineering",
                "org": "Independent Practice",
                "dates": "Jan 2026 - Present",
                "evidence_refs": ["made-up-project"],
                "bullets": ["Developing independently maintained data science projects with reproducible evaluation."]
            }],
            "projects": [],
            "skills": []
        }
        codes = {code for code, _ in lint_cv(cv)}
        self.assertIn("INDEPENDENT_EVIDENCE_REFS", codes)
        self.assertIn("INDEPENDENT_UNKNOWN_REF", codes)

    def test_independent_practice_does_not_allow_client_implication(self):
        cv = {
            "summary": "",
            "experience": [{
                "experience_type": "independent_practice",
                "title": "Independent Data Science Research & Engineering",
                "org": "Independent Practice",
                "dates": "Jan 2026 - Present",
                "evidence_refs": ["frame2threat", "energy-market-tracker"],
                "bullets": ["Delivered client projects across forecasting and sports analytics."]
            }],
            "projects": [],
            "skills": []
        }
        self.assertIn("INDEPENDENT_CLIENT_IMPLICATION", {code for code, _ in lint_cv(cv)})

    def test_independent_ref_allows_attributed_project_anchor(self):
        cv = {
            "summary": "",
            "experience": [{
                "experience_type": "independent_practice",
                "title": "Independent Data Science Research & Engineering",
                "org": "Independent Practice",
                "dates": "Jan 2026 - Present",
                "evidence_refs": ["frame2threat", "energy-market-tracker"],
                "bullets": ["Developing sequence-modelling research using PossessionGRU within the verified Frame2Threat workstream."]
            }],
            "projects": [],
            "skills": []
        }
        self.assertNotIn("ATTRIBUTION_ERROR", {code for code, _ in lint_cv(cv)})


if __name__ == "__main__":
    unittest.main()
