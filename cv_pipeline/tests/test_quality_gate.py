import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import quality_gate


def valid_cv():
    return {
        "cv_identity_mode": "forecasting_data_scientist",
        "dominant_identity": "Forecasting Data Scientist",
        "hybrid_secondary_identity": None,
        "identity": {"name": "Candidate", "headline": "Forecasting Data Scientist | Demand Modelling, MLOps and Decision Support", "email": "candidate@example.com", "phone": "+44 0000 000000", "location": "Birmingham, United Kingdom", "linkedin": "linkedin.com/in/candidate", "github": "github.com/candidate"},
        "summary": "Forecasting data scientist solving demand and price uncertainty in live energy and retail environments. Built residual-load forecasts and multi-horizon demand models using held-out evaluation, production monitoring and reliable data pipelines. Strongest at connecting modelling choices to planning, pricing and resource decisions without overstating what the evidence shows.",
        "skills": [
            {"category": "Modelling", "items": "time-series forecasting, LightGBM, Random Forest"},
            {"category": "Evaluation", "items": "held-out testing, calibration, drift monitoring"},
            {"category": "Engineering", "items": "Python, SQL, Snowflake"},
            {"category": "Decision Support", "items": "pricing, risk and resource allocation"}
        ],
        "experience": [{"title": "Data Scientist", "org": "Manor Park Trading Company", "dates": "Jan 2024 - Jun 2024", "bullets": ["Built multi-horizon demand forecasts across retail channels, linking each horizon to replenishment and buying decisions."]}],
        "projects": [{"title": "Retail Growth Intelligence System", "tools": "Python, LightGBM, DuckDB", "dates": "2026", "bullets": ["Built an uplift-modelling workflow over a DuckDB mart, using an X-learner to handle treatment imbalance and evaluating ranking quality with Qini curves."]}],
        "education": [{"degree": "MSc Business Analytics", "school": "University of Birmingham", "dates": "2023 - 2024"}]
    }


def valid_diagnostic(cv):
    return {
        "cv_identity_mode": cv["cv_identity_mode"],
        "target_headline": cv["identity"]["headline"],
        "professional_thesis": "This candidate is a Forecasting Data Scientist who solves demand uncertainty using held-out modelling, proven by retail forecasting, production monitoring and evaluated project evidence.",
        "signature_proof_points": [
            {"label": "Retail demand forecasting", "source": "profile", "location": "experience[0].bullets[0]"},
            {"label": "Held-out evaluation", "source": "profile", "location": "skills[1]"},
            {"label": "Uplift modelling", "source": "profile", "location": "projects[0].bullets[0]"}
        ],
        "evidence_excluded": [],
        "projects_selected": [{"title": "Retail Growth Intelligence System", "reason": "Evaluated modelling evidence"}],
        "projects_excluded": [],
        "current_role_bullet_order_rationale": "Model and result lead, followed by evaluation and delivery evidence.",
        "first_page_evidence_markers": {"target_identity": "Forecasting Data Scientist", "technical_stack": ["Python", "SQL"], "strongest_achievement": "multi-horizon demand forecasts", "operating_context": "retail", "consequence": "replenishment decisions"},
        "results": {"final_word_count": None, "final_page_count": None, "first_page_sufficiency": "pending", "identity_consistency": "pending", "evidence_integrity": "pending", "layout_quality": "pending"}
    }


class IdentityGateTests(unittest.TestCase):
    def test_four_modes_encoded(self):
        self.assertEqual(set(quality_gate.modes()), {"forecasting_data_scientist", "data_engineer", "energy_market_analyst", "football_research_engineer"})

    def test_valid_payload_and_diagnostic_pass(self):
        cv = valid_cv()
        self.assertEqual([], quality_gate.validate_payload(cv))
        self.assertEqual([], quality_gate.validate_diagnostic(cv, valid_diagnostic(cv)))

    def test_defensive_positioning_is_blocked(self):
        cv = valid_cv()
        cv["summary"] = cv["summary"].replace("Forecasting data scientist", "Market analyst whose work has been data science in all but title")
        self.assertIn("DEFENSIVE_POSITIONING", {code for code, _ in quality_gate.validate_payload(cv)})

    def test_universal_taxonomy_is_blocked(self):
        cv = valid_cv()
        cv["skills"][0]["category"] = "Technical Skills"
        self.assertIn("UNCONTROLLED_CAPABILITY_TAXONOMY", {code for code, _ in quality_gate.validate_payload(cv)})

    def test_project_overload_is_blocked(self):
        cv = valid_cv()
        cv["projects"] = [copy.deepcopy(cv["projects"][0]) for _ in range(4)]
        self.assertIn("CV_SCHEMA", {code for code, _ in quality_gate.validate_payload(cv)})


if __name__ == "__main__":
    unittest.main()
