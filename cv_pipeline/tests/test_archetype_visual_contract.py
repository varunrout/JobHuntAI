import sys
import tempfile
import unittest
from pathlib import Path

from jinja2 import Environment, StrictUndefined, select_autoescape
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import archetype_visual_gate

TEMPLATE = ROOT / "templates" / "cv_archetype_template.html"


def payload():
    return {
        "layout_contract": "jobhuntai-archetype-v1",
        "archetype": "strategy_innovation_analyst",
        "layout_variant": "strategy",
        "identity": {
            "name": "Varun Rout",
            "headline": "Strategy & Innovation Analyst | Commercial Insight and Transformation",
            "phone": "+44 7830 212139",
            "email": "varun_rout@outlook.com",
            "linkedin": "https://www.linkedin.com/in/varunrout",
            "portfolio": "https://varunrout.com",
            "github": "https://github.com/varunrout",
            "location": "Birmingham, UK"
        },
        "summary": "Strategy and innovation analyst translating complex market, operational and commercial evidence into clear priorities for senior stakehlders. Brings forecasting, scenario analysis and transformation delivery experience, with a record of connecting analytical methods to pricing, planning and operating decisions. Strongest when structuring ambiguous questions, testing trade-offs and producing concise recommendations that teams can implement.",
        "selected_impact": [{
            "headline": "Commercial decision support",
            "context": "Energy-market planning",
            "bullets": ["Produced residual-load and forward-curve insight that supported commercial shape discussions and pricing decisions."]
        }],
        "skills": [
            {"category": "Strategy and Insight", "items": "strategic analysis, opportunity assessment and scenario framing"},
            {"category": "Commercial Analysis", "items": "pricing, forecasting, market drivers and business cases"},
            {"category": "Transformation", "items": "workflow redesign, automation and adoption"}
        ],
        "experience": [{"title": "Market Analyst", "org": "E.ON Energy Markets", "sub": "Coventry, UK", "dates": "Jan 2025 - Dec 2025", "bullets": ["Produced commercial insight from demand, renewable generation and market-price drivers to support weekly shape and pricing decisions.", "Prioritised forecasting and automation improvements by combining model evidence with stakeholder requirements and operational constraints."]}],
        "projects": [{"title": "Energy Market Tracker", "tools": "Python, APIs, Streamlit", "dates": "2026", "link": "https://github.com/varunrout/energy-market-tracker", "link_label": "GitHub", "bullets": ["Built an analyst-facing market monitor around Elexon data and explicit volatility diagnostics.", "Separated observed market evidence from forecast claims so the interface remained honest and decision-ready."]}],
        "education": [{"degree": "MSc Business Analytics", "school": "University of Birmingham", "dates": "2023 - 2024"}],
        "section_order": ["summary", "impact", "skills", "experience", "education", "projects"],
        "section_labels": {"summary": "Executive Profile", "impact": "Selected Impact", "skills": "Commercial Expertise", "experience": "Strategy Experience", "projects": "Projects", "education": "Education"},
        "page_strategy": {"recommended_page_length": 2, "maximum_pages": 2, "rationale": "Broad evidence and strategic depth justify two pages.", "factors": {}}
    }


def render(template_text, data, target):
    env = Environment(undefined=StrictUndefined, autoescape=select_autoescape(enabled_extensions=("html", "xml"), default_for_string=True), trim_blocks=True, lstrip_blocks=True)
    html = env.from_string(template_text).render(**data)
    HTML(string=html, base_url=str(ROOT / "templates")).write_pdf(str(target))
    return html


class ArchetypeVisualContractTests(unittest.TestCase):
    def test_dynamic_template_contract_passes(self):
        self.assertEqual([], archetype_visual_gate.check_archetype_template_contract(TEMPLATE.read_text(encoding="utf-8")))

    def test_strategy_section_order_and_labels_render(self):
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / "strategy.pdf"
            html = render(TEMPLATE.read_text(encoding="utf-8"), payload(), pdf)
            self.assertLess(html.index("Executive Profile"), html.index("Selected Impact"))
            self.assertLess(html.index("Selected Impact"), html.index("Commercial Expertise"))
            self.assertEqual([], archetype_visual_gate.check_archetype_cv_pdf(pdf, payload()))

    def test_selected_projects_remains_forbidden(self):
        data = payload()
        data["section_labels"]["projects"] = "Selected Projects"
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / "bad.pdf"
            render(TEMPLATE.read_text(encoding="utf-8"), data, pdf)
            codes = {code for code, _ in archetype_visual_gate.check_archetype_cv_pdf(pdf, data)}
            self.assertIn("SECTION_LABEL_UNCONTROLLED", codes)
            self.assertIn("PROJECT_HEADING_FORBIDDEN", codes)


if __name__ == "__main__":
    unittest.main()
