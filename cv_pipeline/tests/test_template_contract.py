import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "cv_template.html"
CONTRACT = ROOT / "visual_contract.json"


class TemplateContractTests(unittest.TestCase):
    def test_projects_and_experience_use_one_bullet_class(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        body_size = contract["cv"]["body_size_pt"]

        self.assertIn(f"--body-size:{body_size}pt", text)
        self.assertIn(".evidence-list li", text)
        self.assertIn(".evidence-list li::before", text)
        self.assertGreaterEqual(text.count('class="evidence-list"'), 3)
        self.assertNotIn("<ul>{% for b in", text)


if __name__ == "__main__":
    unittest.main()
