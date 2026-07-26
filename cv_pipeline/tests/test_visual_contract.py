import json
import sys
import tempfile
import unittest
from pathlib import Path

from jinja2 import Environment, StrictUndefined, select_autoescape
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import visual_gate

CV_TEMPLATE = ROOT / "templates" / "cv_template.html"
CL_TEMPLATE = ROOT / "templates" / "cover_letter_template.html"
DIAGNOSTIC_PATH = ROOT / "visual-diagnostic.json"


def environment():
    return Environment(
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=("html", "xml"), default_for_string=True),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def cv_payload():
    return {
        "cv_identity_mode": "forecasting_data_scientist",
        "dominant_identity": "Forecasting Data Scientist",
        "identity": {
            "name": "Varun Rout",
            "headline": "Forecasting Data Scientist | Applied Machine Learning and Decision Support",
            "phone": "+44 7830 212139",
            "email": "varun_rout@outlook.com",
            "linkedin": "https://www.linkedin.com/in/varunrout",
            "portfolio": "https://varunrout.com",
            "github": "https://github.com/varunrout",
            "location": "Birmingham, UK",
        },
        "summary": "Forecasting data scientist with experience building evaluated machine-learning models, reliable Python and SQL pipelines, and analyst-facing decision tools across energy and retail settings. Strongest at translating ambiguous operational questions into measurable modelling work, comparing methods honestly and delivering outputs that stakeholders can use.",
        "skills": [
            {"category": "Modelling", "items": "forecasting, regression, classification, Scikit-learn and PyTorch"},
            {"category": "Engineering", "items": "Python, SQL, Azure, Snowflake and Git"},
            {"category": "Delivery", "items": "Streamlit, testing, monitoring and stakeholder communication"},
        ],
        "experience": [
            {
                "title": "Market Analyst",
                "org": "E.ON Energy Markets",
                "sub": "Coventry, UK",
                "dates": "Jan 2025 - Dec 2025",
                "bullets": [
                    "Built a residual-load modelling framework from demand, wind and solar inputs, with a deliberately long evidence sentence that wraps onto a continuation line so the visual gate can verify that every wrapped line begins under the first word rather than shifting farther to the right.",
                    "Improved forward-price-curve performance by 15% in far seasons through held-out evaluation and feature refinement.",
                ],
            },
            {
                "title": "Data Scientist",
                "org": "Manor Park Trading Company",
                "sub": "Birmingham, UK",
                "dates": "Jan 2024 - Jun 2024",
                "bullets": [
                    "Built multi-horizon demand forecasts across approximately 7,000 SKUs to support buying and replenishment decisions.",
                    "Automated segmentation and reporting workflows across Shopify, Amazon and eBay data sources.",
                ],
            },
        ],
        "projects": [
            {
                "title": "Sales Insight Agent",
                "tools": "Python, Scikit-learn, Plotly",
                "dates": "2026",
                "link": "https://github.com/varunrout/sales-insight-agent",
                "link_label": "GitHub",
                "bullets": [
                    "Built a deterministic analyst interface over evaluated regression models and synthetic sales data.",
                    "Added tests and GitHub Actions checks so model outputs and interface behaviour remain reproducible.",
                ],
            }
        ],
        "education": [
            {
                "degree": "MSc Business Analytics",
                "school": "University of Birmingham",
                "dates": "2023 - 2024",
            }
        ],
        "projects_lead": False,
    }


def cl_payload():
    return {
        "identity": cv_payload()["identity"],
        "role_title": "Data Scientist - Workday Products",
        "company": "Kainos",
        "date": "26 July 2026",
        "greeting": "Dear Kainos hiring team,",
        "paragraphs": [
            "The Data Scientist role is a strong fit with my background applying statistical modelling, machine learning and reliable data engineering to operational problems, while working closely with analysts, engineers and non-technical stakeholders to turn ambiguous questions into usable products.",
            "At E.ON Energy Markets, I built residual-load and forecasting workflows, improved forward-price-curve performance through held-out evaluation and supported commercial decisions with Python, SQL and analyst-facing tools.",
        ],
        "sign_off": "Kind regards,",
    }


def render_html(template_text, payload, target):
    rendered = environment().from_string(template_text).render(**payload)
    HTML(string=rendered, base_url=str(ROOT / "templates")).write_pdf(str(target))


def persist_diagnostic(kind, failures):
    DIAGNOSTIC_PATH.write_text(
        json.dumps({"kind": kind, "failures": failures}, indent=2),
        encoding="utf-8",
    )


class VisualContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cv_html = CV_TEMPLATE.read_text(encoding="utf-8")
        cls.cl_html = CL_TEMPLATE.read_text(encoding="utf-8")

    def test_locked_templates_pass(self):
        self.assertEqual([], visual_gate.check_template_contract(self.cv_html, self.cl_html))

    def test_selected_projects_is_blocked(self):
        mutated = self.cv_html.replace("<h2>Projects</h2>", "<h2>Selected Projects</h2>", 1)
        codes = {code for code, _ in visual_gate.check_template_contract(mutated, self.cl_html)}
        self.assertIn("PROJECT_HEADING_FORBIDDEN", codes)
        self.assertIn("PROJECT_HEADING_DRIFT", codes)

    def test_bullet_css_drift_is_blocked(self):
        mutated = self.cv_html.replace("text-indent:0;", "text-indent:-2mm;", 1)
        codes = {code for code, _ in visual_gate.check_template_contract(mutated, self.cl_html)}
        self.assertIn("VISUAL_CSS_DRIFT", codes)

    def test_cover_letter_table_is_blocked(self):
        mutated = self.cl_html.replace("<main class=\"letter-column\">", "<table><tr><td>bad</td></tr></table><main class=\"letter-column\">")
        codes = {code for code, _ in visual_gate.check_template_contract(self.cv_html, mutated)}
        self.assertIn("VISUAL_TABLE_FORBIDDEN", codes)

    def test_rendered_cv_passes_visual_geometry(self):
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / "cv.pdf"
            render_html(self.cv_html, cv_payload(), pdf)
            failures = visual_gate.check_cv_pdf(pdf, cv_payload())
            persist_diagnostic("cv", failures)
            self.assertEqual([], failures)

    def test_wrapped_bullet_extra_indent_is_blocked(self):
        malformed = self.cv_html.replace("text-indent:0;", "text-indent:-4mm;", 1)
        payload = cv_payload()
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / "bad-cv.pdf"
            render_html(malformed, payload, pdf)
            codes = {code for code, _ in visual_gate.check_cv_pdf(pdf, payload)}
            bullet_failures = {
                "BULLET_CONTINUATION_INDENT",
                "BULLET_TEXT_MISSING",
                "BULLET_GEOMETRY_MISSING",
                "BULLET_MARKER_POSITION",
            }
            self.assertTrue(codes & bullet_failures, codes)

    def test_rendered_cover_letter_passes_visual_geometry(self):
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / "cl.pdf"
            render_html(self.cl_html, cl_payload(), pdf)
            failures = visual_gate.check_cover_letter_pdf(pdf, cl_payload())
            persist_diagnostic("cover_letter", failures)
            self.assertEqual([], failures)

    def test_shifted_cover_letter_meta_row_is_blocked(self):
        malformed = self.cl_html.replace("margin:0 0 3mm 0;", "margin:0 0 3mm -3mm;", 1)
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / "bad-cl.pdf"
            render_html(malformed, cl_payload(), pdf)
            codes = {code for code, _ in visual_gate.check_cover_letter_pdf(pdf, cl_payload())}
            self.assertIn("LETTER_LEFT_EDGE", codes)


if __name__ == "__main__":
    unittest.main()
