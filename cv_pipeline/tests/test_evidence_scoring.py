import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_scoring import score_evidence_item


class EvidenceScoringTests(unittest.TestCase):
    def test_same_evidence_reweights_by_archetype(self):
        residual_load = {
            "id": "eon-residual-load",
            "text": "Residual-load model supporting forward-curve and shape decisions",
            "source": "MASTER_PROFILE.md §3 E.ON",
            "source_type": "verified_employment",
            "claim_status": "measured",
            "dimensions": {
                "technical_depth": 5,
                "commercial_influence": 5,
                "transformation": 2,
                "stakeholder_engagement": 4,
                "strategic_thinking": 4,
                "operational_optimisation": 3,
                "leadership": 1,
                "domain_relevance": 5,
                "quantified_impact": 4,
                "evidence_strength": 5
            }
        }
        data_science = score_evidence_item(residual_load, "data_scientist")
        strategy = score_evidence_item(residual_load, "strategy_innovation_analyst")
        self.assertNotEqual(data_science["archetype_score"], strategy["archetype_score"])
        self.assertGreater(data_science["score_breakdown"]["technical_depth"], strategy["score_breakdown"]["technical_depth"])
        self.assertGreater(strategy["score_breakdown"]["strategic_thinking"], data_science["score_breakdown"]["strategic_thinking"])

    def test_unsupported_evidence_is_heavily_discounted(self):
        item = {"id": "unsupported", "text": "Unsupported technical claim with no traceable evidence source.", "source": "none", "source_type": "inferred", "claim_status": "unsupported", "dimensions": {"technical_depth": 5, "evidence_strength": 5}}
        self.assertLess(score_evidence_item(item, "data_scientist")["archetype_score"], 10)


if __name__ == "__main__":
    unittest.main()
