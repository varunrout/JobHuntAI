import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from role_identity import classify_role


class RoleIdentityTests(unittest.TestCase):
    def test_strategy_role_is_classified_before_evidence_selection(self):
        result = classify_role({
            "job_title": "Senior Analyst, Strategy & Innovation",
            "job_description": "Support strategic planning, innovation and transformation across the club.",
            "seniority": "senior",
            "industry": "football",
            "hiring_team": "Strategy and Innovation",
            "responsibilities": ["Produce executive insight", "Develop business cases", "Identify commercial opportunities"],
            "success_metrics": ["Strategic priorities", "Commercial impact"],
            "candidate_context": {
                "relevant_years": 4,
                "breadth_of_responsibilities": "broad",
                "strategic_depth": "high",
                "leadership_expectations": "influence",
                "evidence_density": "high"
            }
        })
        self.assertEqual("strategy_innovation_analyst", result["archetype"])
        self.assertEqual(2, result["recommended_page_length"])
        self.assertIn("Position the candidate as a Strategy & Innovation Analyst", result["positioning_strategy"])

    def test_analytics_engineer_role_is_not_collapsed_into_data_science(self):
        result = classify_role({
            "job_title": "Analytics Engineer",
            "job_description": "Build dbt models, governed metrics and a trusted semantic layer for reliable self-service analysis.",
            "seniority": "mid",
            "industry": "media",
            "hiring_team": "Data Platform",
            "responsibilities": ["Define metrics", "Create data quality tests", "Enable self service analytics"],
            "success_metrics": ["Metric consistency", "Data quality"],
            "candidate_context": {
                "relevant_years": 4,
                "breadth_of_responsibilities": "moderate",
                "strategic_depth": "medium",
                "leadership_expectations": "none",
                "evidence_density": "high"
            }
        })
        self.assertEqual("analytics_engineer", result["archetype"])
        self.assertNotEqual("data_scientist", result["archetype"])

    def test_all_supported_archetypes_classify_from_clear_signals(self):
        cases = {
            "data_scientist": ("Data Scientist", "Build machine learning predictive models and evaluate model performance", "Data Science", ["Train models", "Feature engineering"], ["RMSE", "Calibration"]),
            "analytics_engineer": ("Analytics Engineer", "Build dbt analytics models, semantic layers and trusted metrics", "Data Platform", ["Define metrics", "Data quality tests"], ["Metric consistency", "Adoption"]),
            "data_engineer": ("Data Engineer", "Build reliable ETL data pipelines and cloud data platforms", "Data Engineering", ["Ingest data", "Schema validation"], ["Freshness", "Reliability"]),
            "strategy_innovation_analyst": ("Strategy & Innovation Analyst", "Develop strategy, innovation and transformation priorities", "Strategy and Innovation", ["Develop strategy", "Identify opportunities"], ["Strategic priorities", "Transformation value"]),
            "commercial_analyst": ("Commercial Analyst", "Analyse revenue, margin and commercial performance", "Commercial", ["Forecast revenue", "Build business cases"], ["Revenue", "Margin"]),
            "football_performance_analyst": ("First Team Performance Analyst", "Deliver tactical, opposition and match analysis for coaches", "Performance Analysis", ["Analyse matches", "Prepare opposition reports"], ["Coach adoption", "Match preparation"]),
            "football_strategy_analyst": ("Football Strategy Analyst", "Support sporting strategy, recruitment strategy and football innovation", "Sporting Strategy", ["Support sporting strategy", "Evaluate opportunities"], ["Recruitment decisions", "Strategic priorities"]),
            "business_intelligence_analyst": ("Business Intelligence Analyst", "Build Power BI dashboards and business intelligence reporting", "Business Intelligence", ["Build dashboards", "Define KPIs"], ["KPI visibility", "Reporting time"]),
            "forecasting_pricing_analyst": ("Forecasting & Pricing Analyst", "Build demand forecasts and pricing models for forward curve decisions", "Pricing and Forecasting", ["Build forecasts", "Support pricing"], ["Forecast accuracy", "Pricing performance"]),
            "product_analytics": ("Product Analyst", "Use product analytics, experimentation and user behaviour data", "Product", ["Design experiments", "Funnel analysis"], ["Activation", "Retention"]),
            "marketing_analytics": ("Marketing Analytics Analyst", "Measure campaign performance, attribution and customer analytics", "Marketing Analytics", ["Measure campaigns", "Optimise spend"], ["ROAS", "CAC"]),
        }
        for expected, (title, description, team, responsibilities, metrics) in cases.items():
            with self.subTest(archetype=expected):
                result = classify_role({
                    "job_title": title,
                    "job_description": description + " with measurable decision outcomes and cross-functional delivery.",
                    "seniority": "mid",
                    "industry": "general",
                    "hiring_team": team,
                    "responsibilities": responsibilities,
                    "success_metrics": metrics,
                    "candidate_context": {
                        "relevant_years": 4,
                        "breadth_of_responsibilities": "moderate",
                        "strategic_depth": "medium",
                        "leadership_expectations": "none",
                        "evidence_density": "high"
                    }
                })
                self.assertEqual(expected, result["archetype"])

    def test_no_signal_is_blocked_instead_of_defaulting_to_data_science(self):
        with self.assertRaises(ValueError):
            classify_role({
                "job_title": "Generalist",
                "job_description": "General responsibilities with no recognised professional identity signals or measurable discipline-specific outcomes.",
                "seniority": "mid",
                "industry": "general",
                "hiring_team": "Operations",
                "responsibilities": ["Complete assigned work"],
                "success_metrics": ["General delivery"],
                "candidate_context": {
                    "relevant_years": 4,
                    "breadth_of_responsibilities": "moderate",
                    "strategic_depth": "medium",
                    "leadership_expectations": "none",
                    "evidence_density": "medium"
                }
            })


if __name__ == "__main__":
    unittest.main()
