import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from positioning_pipeline import build_positioning_brief


class PositioningPipelineTests(unittest.TestCase):
    def test_classification_precedes_archetype_evidence_ranking(self):
        role = {
            "job_title": "Senior Analyst, Strategy & Innovation",
            "job_description": "Develop strategy, identify innovation opportunities and produce executive insight for commercial decisions.",
            "seniority": "senior",
            "industry": "football",
            "hiring_team": "Strategy and Innovation",
            "responsibilities": ["Develop business cases", "Prioritise initiatives", "Support executive decisions"],
            "success_metrics": ["Commercial impact", "Strategic priorities"],
            "candidate_context": {
                "relevant_years": 4,
                "breadth_of_responsibilities": "broad",
                "strategic_depth": "high",
                "leadership_expectations": "influence",
                "evidence_density": "high"
            }
        }
        evidence = [
            {
                "id": "technical-model",
                "text": "Developed a forecasting model with held-out evaluation and production monitoring.",
                "source": "MASTER_PROFILE.md",
                "source_type": "verified_employment",
                "claim_status": "measured",
                "dimensions": {"technical_depth": 5, "commercial_influence": 2, "strategic_thinking": 2, "evidence_strength": 5}
            },
            {
                "id": "commercial-decision",
                "text": "Produced commercial insight supporting executive prioritisation and pricing decisions.",
                "source": "MASTER_PROFILE.md",
                "source_type": "verified_employment",
                "claim_status": "verified",
                "dimensions": {"technical_depth": 2, "commercial_influence": 5, "strategic_thinking": 5, "stakeholder_engagement": 5, "evidence_strength": 5}
            }
        ]
        brief = build_positioning_brief(role, evidence)
        self.assertEqual("strategy_innovation_analyst", brief["role_identity"]["archetype"])
        self.assertEqual("commercial-decision", brief["ranked_evidence"][0]["id"])
        self.assertEqual("Executive Profile", brief["archetype_contract"]["section_labels"]["summary"])
        self.assertEqual(2, brief["page_strategy"]["recommended_page_length"])


if __name__ == "__main__":
    unittest.main()
