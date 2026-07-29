import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import archetype_quality_gate


def valid_cv():
    role_identity = {
        "archetype": "strategy_innovation_analyst",
        "confidence": 0.78,
        "secondary_archetypes": ["commercial_analyst"],
        "positioning_strategy": "Position the candidate as a Strategy & Innovation Analyst who turns ambiguous questions into evidence-backed priorities.",
        "recommended_page_length": 2,
        "page_length_rationale": {"score": 8, "factors": {"relevant_years": 1}},
        "classification_scores": {"strategy_innovation_analyst": 18.0, "commercial_analyst": 11.0},
        "requires_review": False
    }
    return {
        "layout_contract": "jobhuntai-archetype-v1",
        "archetype": "strategy_innovation_analyst",
        "role_identity": role_identity,
        "identity": {
            "name": "Candidate",
            "headline": "Strategy & Innovation Analyst | Commercial Insight, Transformation and Decision Support",
            "email": "candidate@example.com",
            "phone": "+44 0000 000000",
            "location": "Birmingham, UK",
            "linkedin": "https://linkedin.com/in/candidate",
            "portfolio": "https://candidate.example.com",
            "github": "https://github.com/candidate"
        },
        "summary": "Strategy and innovation analyst translating complex market, operational and commercial evidence into clear priorities for senior stakeholders. Brings forecasting, scenario analysis and transformation delivery experience, with a record of connecting analytical methods to pricing, planning and operating decisions. Strongest when structuring ambiguous questions, testing trade-offs and producing concise recommendations that teams can implement.",
        "selected_impact": [{
            "headline": "Commercial decision support",
            "context": "Energy-market planning",
            "bullets": ["Produced residual-load and forward-curve insight that supported commercial shape discussions and pricing decisions."]
        }],
        "skills": [
            {"category": "Strategy and Insight", "items": "strategic analysis, opportunity assessment, scenario framing"},
            {"category": "Commercial Analysis", "items": "pricing, forecasting, market drivers, business cases"},
            {"category": "Transformation", "items": "workflow redesign, automation, adoption"},
            {"category": "Executive Communication", "items": "decision papers, stakeholder workshops, concise recommendations"}
        ],
        "experience": [{
            "title": "Market Analyst",
            "org": "E.ON Energy Markets",
            "dates": "Jan 2025 - Dec 2025",
            "bullets": [
                "Produced commercial insight from demand, renewable generation and market-price drivers to support weekly shape and pricing decisions.",
                "Prioritised forecasting and automation improvements by combining model evidence with stakeholder requirements and operational constraints."
            ]
        }],
        "projects": [],
        "education": [{"degree": "MSc Business Analytics", "school": "University of Birmingham", "dates": "2023 - 2024"}],
        "section_order": ["summary", "impact", "skills", "experience", "education", "projects"],
        "section_labels": {
            "summary": "Executive Profile", "impact": "Selected Impact", "skills": "Commercial Expertise",
            "experience": "Strategy Experience", "projects": "Projects", "education": "Education"
        },
        "layout_variant": "strategy",
        "page_strategy": {
            "recommended_page_length": 2,
            "maximum_pages": 2,
            "rationale": "Broad senior responsibilities and high evidence density justify two pages without filler.",
            "factors": {"relevant_years": 1, "seniority": 2, "breadth": 2}
        },
        "bullet_strategy": {
            "optimise_for": ["commercial_influence", "strategic_thinking", "stakeholder_engagement", "transformation"],
            "preferred_verbs": ["shaped", "advised", "produced", "prioritised"],
            "style": "Lead with the decision or strategic question, then the insight, influence and consequence."
        }
    }


def valid_diagnostic(cv):
    return {
        "role_identity": cv["role_identity"],
        "professional_thesis": "This candidate is a Strategy & Innovation Analyst who solves ambiguous commercial questions using forecasting and structured analysis, proven by pricing support, transformation delivery and stakeholder influence.",
        "signature_proof_points": [
            {"label": "Pricing support", "source": "profile", "location": "experience[0].bullets[0]"},
            {"label": "Transformation", "source": "profile", "location": "experience[0].bullets[1]"},
            {"label": "Commercial impact", "source": "profile", "location": "selected_impact[0]"}
        ],
        "evidence_ranking": [
            {"id": "pricing", "archetype_score": 92.0},
            {"id": "transformation", "archetype_score": 84.0},
            {"id": "stakeholders", "archetype_score": 77.0}
        ],
        "evidence_excluded": [], "projects_selected": [], "projects_excluded": [],
        "section_order_rationale": "Executive profile and selected impact establish positioning before capabilities and experience.",
        "bullet_optimisation": {"dimensions": cv["bullet_strategy"]["optimise_for"], "rationale": "The role prioritises commercial influence, strategy, stakeholders and transformation."},
        "first_page_evidence_markers": {
            "professional_identity": "Strategy & Innovation Analyst",
            "proof_markers": ["residual-load", "forecasting"],
            "operating_context": "Energy-market",
            "consequence": "pricing decisions"
        },
        "results": {"final_word_count": None, "final_page_count": None, "first_page_sufficiency": "pending", "positioning_consistency": "pending", "evidence_integrity": "pending", "layout_quality": "pending"}
    }


class ArchetypeQualityGateTests(unittest.TestCase):
    def test_valid_strategy_payload_passes(self):
        cv = valid_cv()
        self.assertEqual([], archetype_quality_gate.validate_payload(cv))
        self.assertEqual([], archetype_quality_gate.validate_diagnostic(cv, valid_diagnostic(cv)))

    def test_wrong_skills_taxonomy_is_blocked(self):
        cv = valid_cv()
        cv["skills"][0]["category"] = "Machine Learning"
        self.assertIn("UNCONTROLLED_SKILLS_TAXONOMY", {code for code, _ in archetype_quality_gate.validate_payload(cv)})

    def test_strategy_layout_without_rationale_is_blocked_when_reordered(self):
        cv = valid_cv()
        cv["section_order"] = ["summary", "skills", "impact", "experience", "education", "projects"]
        self.assertIn("ARCHETYPE_SECTION_ORDER", {code for code, _ in archetype_quality_gate.validate_payload(cv)})

    def test_page_strategy_must_match_classification(self):
        cv = valid_cv()
        cv["page_strategy"]["recommended_page_length"] = 1
        self.assertIn("PAGE_STRATEGY_MISMATCH", {code for code, _ in archetype_quality_gate.validate_payload(cv)})

    def test_low_confidence_identity_requires_recorded_review(self):
        cv = valid_cv()
        cv["role_identity"]["requires_review"] = True
        self.assertIn("LOW_CONFIDENCE_IDENTITY_REVIEW_REQUIRED", {code for code, _ in archetype_quality_gate.validate_payload(cv)})
        cv["classification_review"] = "Reviewed against the full role and retained Strategy & Innovation Analyst as the dominant identity."
        self.assertNotIn("LOW_CONFIDENCE_IDENTITY_REVIEW_REQUIRED", {code for code, _ in archetype_quality_gate.validate_payload(cv)})

    def test_archetype_layout_and_language_contracts_are_enforced(self):
        cv = valid_cv()
        cv["layout_variant"] = "technical"
        cv["bullet_strategy"]["preferred_verbs"] = ["coded", "trained", "deployed"]
        codes = {code for code, _ in archetype_quality_gate.validate_payload(cv)}
        self.assertIn("ARCHETYPE_LAYOUT_VARIANT", codes)
        self.assertIn("ARCHETYPE_VERB_MISMATCH", codes)


if __name__ == "__main__":
    unittest.main()
