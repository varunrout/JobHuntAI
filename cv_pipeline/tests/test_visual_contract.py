import json
import sys
import tempfile
import unittest
from pathlib import Path

import fitz
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
            "linkedin": "www.linkedin.com/in/varunrout",
            "portfolio": "varunrout.com",
            "github": "github.com/varunrout",
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
                "link": "github.com/varunrout/sales-insight-agent",
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
            "The Data Scientist role is a strong fit with my background applying statistical modelling, machine learning and reliable data engineering to operational problems, while working closely with analysts, engineers and non-technical stakeholders to turn ambiguous questions into usable products. Across recent work I have focused on making analytical systems measurable and useful rather than simply technically interesting, with careful evaluation, reproducible workflows and a clear link between model outputs and the decision a stakeholder actually needs to make. I enjoy the point where a modelling question becomes a practical product question, because that is where choices around data quality, evaluation, communication and engineering discipline matter most.",
            "At E.ON Energy Markets, I built residual-load and forecasting workflows, improved forward-price-curve performance through held-out evaluation and supported commercial decisions with Python, SQL and analyst-facing tools. I also developed repeatable data pipelines and automation around market and operational inputs, giving analysts a more reliable route from raw data to evidence they could use. That combination of modelling, engineering and decision support is the part of the role that interests me most because it matches how I prefer to work: understand the problem, define what good performance means, test the approach honestly, document the trade-offs, and make the result accessible to the people responsible for the decision. The same approach has shaped my independent technical work since then, where reproducibility and clear benchmark comparison remain central.",
            "Alongside employment, I have continued building end-to-end analytical projects that deepen the same skills, including forecasting, applied machine learning, validation, data ingestion and analyst-facing delivery. Those projects have given me room to test methods carefully, strengthen software-engineering habits and make technical decisions explicit rather than hiding them behind a polished interface. I would bring that practical approach to Kainos, together with strong curiosity, comfort working across technical and non-technical teams, and a preference for clear evidence over unnecessary complexity. The opportunity to contribute to products used in real operational contexts is particularly appealing, and I would welcome the chance to discuss how my experience in evaluated modelling, reliable data workflows and decision-focused delivery could support the team and its users.",
        ],
        "sign_off": "Kind regards,",
    }


def render_html(template_text, payload, target):
    rendered = environment().from_string(template_text).render(**payload)
    HTML(string=rendered, base_url=str(ROOT / "templates")).write_pdf(str(target))
    return rendered


def persist_diagnostic(kind, failures):
    DIAGNOSTIC_PATH.write_text(json.dumps({"kind": kind, "failures": failures}, indent=2), encoding="utf-8")


def raw_span(text, x, y, size=10.4, character_width=4.5):
    chars = []
    current_x = x
    for character in text:
        width = character_width if character != " " else character_width / 2
        chars.append({"c": character, "bbox": [current_x, y, current_x + width, y + 10]})
        current_x += width
    return {"size": size, "chars": chars}


class FakeRawPage:
    def __init__(self, rawdict):
        self.rawdict = rawdict

    def get_text(self, mode):
        if mode != "rawdict":
            raise AssertionError(f"unexpected mode {mode}")
        return self.rawdict


def malformed_bullet_page():
    marker = raw_span("·", 37.0, 100.0)
    first_line = raw_span(" Built first line", 42.0, 100.0)
    continuation = raw_span("continuation shifted right", 58.0, 111.0)
    return FakeRawPage({
        "blocks": [
            {
                "type": 0,
                "lines": [
                    {"spans": [marker, first_line]},
                    {"spans": [continuation]},
                ],
            }
        ]
    })


def largest_rect(page, uri):
    matches = [link["from"] for link in page.get_links() if link.get("uri") == uri and link.get("from") is not None]
    return max(matches, key=lambda rect: rect.width * rect.height)


class VisualContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cv_html = CV_TEMPLATE.read_text(encoding="utf-8")
        cls.cl_html = CL_TEMPLATE.read_text(encoding="utf-8")

    def test_locked_templates_pass(self):
        self.assertEqual([], visual_gate.check_template_contract(self.cv_html, self.cl_html))

    def test_skills_binding_uses_explicit_dictionary_key(self):
        self.assertIn('{{ s["items"] }}', self.cv_html)
        self.assertNotIn("{{ s.items }}", self.cv_html)

    def test_retired_gold_and_non_contract_fallbacks_are_absent(self):
        combined = self.cv_html + self.cl_html
        for token in ("#c28d41", "#7d5411", "#facb8d", "DejaVu", "Liberation"):
            self.assertNotIn(token.lower(), combined.lower())

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

    def test_rendered_cv_passes_pdf_acceptance(self):
        data = cv_payload()
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / "cv.pdf"
            render_html(self.cv_html, data, pdf)
            failures = visual_gate.check_cv_pdf(pdf, data)
            persist_diagnostic("cv", failures)
            with fitz.open(pdf) as document:
                self.assertIn(len(document), (1, 2))
                rendered_text = "\n".join(page.get_text() for page in document)
                normalised = visual_gate.normalise(rendered_text)
                links = [link.get("uri") for page in document for link in page.get_links() if link.get("uri")]
                self.assertTrue(all(uri.startswith("https://") or uri.startswith("mailto:") for uri in links))
                self.assertIn("github.com/varunrout", rendered_text)
                self.assertIn("varunrout.com", rendered_text)
                self.assertIn("PROFESSIONAL SUMMARY", rendered_text)
                self.assertIn("EXPERIENCE", rendered_text)
                self.assertNotIn("P R O F E S S I O N A L", rendered_text)
                self.assertNotIn("E X P E R I E N C E", rendered_text)
                for role in data["experience"]:
                    for bullet in role["bullets"]:
                        self.assertIn(visual_gate.normalise(bullet), normalised)
                for project in data["projects"]:
                    for bullet in project["bullets"]:
                        self.assertIn(visual_gate.normalise(bullet), normalised)
            self.assertEqual([], failures)

    def test_cta_boxes_are_equal_one_line_links_with_gap(self):
        data = cv_payload()
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / "cv.pdf"
            render_html(self.cv_html, data, pdf)
            with fitz.open(pdf) as document:
                page = document[0]
                github = largest_rect(page, "https://github.com/varunrout")
                portfolio = largest_rect(page, "https://varunrout.com")
                self.assertAlmostEqual(github.width, portfolio.width, delta=0.75)
                self.assertAlmostEqual(github.height, portfolio.height, delta=0.75)
                self.assertGreater(portfolio.y0 - github.y1, 3.5)
                text = page.get_text()
                self.assertIn("github.com/varunrout", text)
                self.assertIn("varunrout.com", text)

    def test_optional_ctas_degrade_independently(self):
        for github, portfolio, expected in (
            ("", "", []),
            ("github.com/varunrout", "", ["github.com/varunrout"]),
            ("", "varunrout.com", ["varunrout.com"]),
        ):
            data = cv_payload()
            data["identity"] = dict(data["identity"], github=github, portfolio=portfolio)
            with self.subTest(github=github, portfolio=portfolio), tempfile.TemporaryDirectory() as temp:
                pdf = Path(temp) / "cv.pdf"
                html = render_html(self.cv_html, data, pdf)
                if not expected:
                    self.assertNotIn('<div class="cta-stack">', html)
                with fitz.open(pdf) as document:
                    text = document[0].get_text()
                    links = [link.get("uri") for link in document[0].get_links() if link.get("uri")]
                for label in ("github.com/varunrout", "varunrout.com"):
                    if label in expected:
                        self.assertIn(label, text)
                    else:
                        self.assertNotIn(label, text)
                identity_uris = {"https://github.com/varunrout", "https://varunrout.com"}
                present = identity_uris.intersection(links)
                self.assertEqual(len(expected), len(present))
                failures = visual_gate.check_cv_pdf(pdf, data)
                self.assertFalse(any(code.startswith("CTA_") for code, _ in failures), failures)

    def test_wrapped_bullet_extra_indent_is_blocked(self):
        contract = visual_gate.load_json(visual_gate.CONTRACT_PATH)
        failures = visual_gate._check_bullets(malformed_bullet_page(), contract)
        codes = {code for code, _ in failures}
        self.assertIn("BULLET_CONTINUATION_INDENT", codes)

    def test_rendered_cover_letter_passes_visual_geometry(self):
        data = cl_payload()
        words = sum(len(paragraph.split()) for paragraph in data["paragraphs"])
        self.assertGreaterEqual(words, 350)
        self.assertLessEqual(words, 450)
        self.assertEqual(3, len(data["paragraphs"]))
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / "cl.pdf"
            render_html(self.cl_html, data, pdf)
            failures = visual_gate.check_cover_letter_pdf(pdf, data)
            persist_diagnostic("cover_letter", failures)
            with fitz.open(pdf) as document:
                self.assertEqual(1, len(document))
                text = document[0].get_text()
                self.assertIn("github.com/varunrout", text)
                self.assertIn("varunrout.com", text)
                links = [link.get("uri") for link in document[0].get_links() if link.get("uri")]
                self.assertTrue(all(uri.startswith("https://") or uri.startswith("mailto:") for uri in links))
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
