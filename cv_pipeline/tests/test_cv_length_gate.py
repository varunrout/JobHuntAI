import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cv_length_gate


def hsbc_cv(page_count=2):
    return {
        "page_strategy": {"maximum_pages": page_count},
        "summary": "Data scientist with production model monitoring, Python and SQL delivery and evaluated binary classification evidence.",
        "experience": [
            {"title": "Market Analyst", "bullets": ["Implemented continuous drift monitoring and feature-distribution alerts.", "Built Python and SQL data pipelines with operational controls."]},
            {"title": "Costing and Risk Intern", "bullets": ["Built Monte Carlo scenarios for commercial risk decisions."]},
            {"title": "Systems Engineer", "bullets": ["Documented data structures, dependencies and operational controls."]},
            {"title": "Business Analytics Consultant", "bullets": ["Translated analysis into stakeholder planning decisions."]},
        ],
        "projects": [{"title": "Opponent-Adjusted Football Metrics", "bullets": ["Evaluated binary classification with Brier score, log loss and ROC AUC."]}],
        "education": [{"degree": "MSc Business Analytics"}],
    }


def hsbc_audit(page_count=2):
    return {
        "contract": cv_length_gate.CONTRACT,
        "strategy_decision": cv_length_gate.TWO_PAGE_PREFERRED,
        "strategy_rationale": "Four relevant roles, production model evidence, classification proof and a domain-transfer case require depth beyond a compressed one-page document.",
        "final_page_count": page_count,
        "candidate_role_profile": {
            "seniority": "mid",
            "relevant_years": 4,
            "relevant_roles": 4,
            "relevant_projects": 1,
            "technical_breadth": 6,
            "domain_transfer_required": True,
        },
        "essential_evidence": [
            {"id": "classification", "match_any": ["Brier score", "binary classification"]},
            {"id": "monitoring", "match_any": ["drift monitoring"]},
            {"id": "python_sql", "match_any": ["Python and SQL"]},
            {"id": "documentation", "match_any": ["documented data structures"]},
            {"id": "stakeholders", "match_any": ["stakeholder planning decisions"]},
        ],
        "omissions": [{"id": "minor-tool", "impact": "harmless", "rationale": "A low-priority tool list was omitted because stronger production evidence already proves the requirement."}],
        "review_judgement": {
            "material_evidence_removed": False,
            "omission_audit_complete": True,
            "page_strategy_approved": True,
            "rationale": "The two-page structure retains every role-critical proof point and uses the second page for relevant supporting evidence rather than filler.",
            "review_actor": "review-agent",
            "review_iteration": 1,
            "cv_sha256": "a" * 64,
        },
        "page_transition": {"previous_page_count": 2, "remediation_steps": [], "fresh_strategic_review": False},
        "page_fill": [0.96, 0.76],
    }


class CVLengthGateTests(unittest.TestCase):
    def test_hsbc_two_page_cv_passes(self):
        self.assertEqual([], cv_length_gate.validate(hsbc_cv(), hsbc_audit()))

    def test_hsbc_one_page_overcompression_is_blocked(self):
        cv = hsbc_cv(page_count=1)
        cv["experience"] = cv["experience"][:3]
        cv["experience"][0]["bullets"] = ["Built Python and SQL data pipelines with operational controls."]
        audit = hsbc_audit(page_count=1)
        audit["omissions"] = [{"id": "consulting", "impact": "strategic_loss", "rationale": "Consultancy and monitoring evidence were removed to make the CV fit on one page."}]
        audit["review_judgement"]["material_evidence_removed"] = True
        audit["page_transition"] = {
            "previous_page_count": 2,
            "remediation_steps": ["reduce_page_count"],
            "fresh_strategic_review": False,
        }
        codes = {item["code"] for item in cv_length_gate.validate(cv, audit)}
        self.assertIn("ONE_PAGE_EXCEPTION_REQUIRED", codes)
        self.assertIn("ESSENTIAL_EVIDENCE_DROPPED", codes)
        self.assertIn("STRATEGIC_EVIDENCE_OMITTED", codes)
        self.assertIn("SPARSE_PAGE_REMEDIATION_SKIPPED", codes)
        self.assertIn("PAGE_REDUCTION_REVIEW_REQUIRED", codes)
        self.assertIn("PAGE_OPTIMISATION_WEAKENED_CASE", codes)

    def test_one_page_allowed_only_for_narrow_profile(self):
        cv = {"page_strategy": {"maximum_pages": 1}, "summary": "Python SQL modelling"}
        audit = {
            "contract": cv_length_gate.CONTRACT,
            "strategy_decision": cv_length_gate.ONE_PAGE_ALLOWED,
            "strategy_rationale": "Early-career profile with one relevant role and a small essential evidence set is complete on one page.",
            "final_page_count": 1,
            "candidate_role_profile": {"seniority": "junior", "relevant_years": 2, "relevant_roles": 1, "relevant_projects": 0, "technical_breadth": 2, "domain_transfer_required": False},
            "essential_evidence": [{"id": "python", "match_any": ["Python"]}, {"id": "sql", "match_any": ["SQL"]}],
            "omissions": [],
            "review_judgement": {
                "material_evidence_removed": False,
                "omission_audit_complete": True,
                "page_strategy_approved": True,
                "rationale": "All role-critical evidence is retained and the profile is narrow enough for one page.",
                "review_actor": "review-agent",
                "review_iteration": 1,
                "cv_sha256": "b" * 64,
            },
            "page_transition": {},
            "page_fill": [0.92],
        }
        self.assertEqual([], cv_length_gate.validate(cv, audit))
        audit["candidate_role_profile"]["relevant_roles"] = 4
        codes = {item["code"] for item in cv_length_gate.validate(cv, audit)}
        self.assertIn("ONE_PAGE_NOT_PERMITTED", codes)

    def test_two_page_underfill_is_investigated_not_compressed(self):
        audit = hsbc_audit()
        audit["page_fill"] = [0.95, 0.52]
        codes = {item["code"] for item in cv_length_gate.validate(hsbc_cv(), audit)}
        self.assertIn("SECOND_PAGE_UNDERFILLED", codes)
        self.assertNotIn("ONE_PAGE_NOT_PERMITTED", codes)

    def test_first_page_underfill_is_blocked(self):
        audit = hsbc_audit()
        audit["page_fill"] = [0.86, 0.78]
        codes = {item["code"] for item in cv_length_gate.validate(hsbc_cv(), audit)}
        self.assertIn("PAGE_ONE_UNDERFILLED", codes)
        self.assertNotIn("SECOND_PAGE_UNDERFILLED", codes)

    def test_review_judgement_must_match_independent_review_loop(self):
        cv = hsbc_cv()
        audit = hsbc_audit()
        reviewed_hash = "c" * 64
        audit["review_judgement"].update({
            "review_actor": "review-agent",
            "review_iteration": 2,
            "cv_sha256": reviewed_hash,
        })
        state = {
            "events": [{
                "type": "review",
                "actor": "review-agent",
                "iteration": 2,
                "cv_sha256": reviewed_hash,
                "verdict": "approve",
            }]
        }
        self.assertEqual([], cv_length_gate.validate(cv, audit, state))
        audit["review_judgement"]["review_actor"] = "tailor-agent"
        codes = {item["code"] for item in cv_length_gate.validate(cv, audit, state)}
        self.assertIn("PAGE_COUNT_REVIEW_ACTOR_MISMATCH", codes)

    def test_two_page_preferred_exception_requires_full_repair_history(self):
        cv = hsbc_cv(page_count=1)
        audit = hsbc_audit(page_count=1)
        audit["one_page_exception"] = {
            "approved": True,
            "rationale": "All essential evidence remains and the independently reviewed final one-page layout is materially stronger.",
        }
        audit["page_fill"] = [0.94]
        audit["page_transition"] = {
            "previous_page_count": 2,
            "remediation_steps": ["reduce_page_count"],
            "fresh_strategic_review": True,
        }
        codes = {item["code"] for item in cv_length_gate.validate(cv, audit)}
        self.assertIn("SPARSE_PAGE_REMEDIATION_SKIPPED", codes)

        audit["page_transition"]["remediation_steps"] = list(cv_length_gate.REMEDIATION_ORDER)
        self.assertEqual([], cv_length_gate.validate(cv, audit))


if __name__ == "__main__":
    unittest.main()
