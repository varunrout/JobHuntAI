import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "cv_template.html"


class TemplateContractTests(unittest.TestCase):
    def test_projects_and_experience_use_one_bullet_class(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("--body-size:9.25pt", text)
        self.assertIn(".evidence-list li", text)
        self.assertIn(".evidence-list li::before", text)
        self.assertGreaterEqual(text.count('class="evidence-list"'), 3)
        self.assertNotIn("<ul>{% for b in", text)


if __name__ == "__main__":
    unittest.main()
