import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import visual_gate


class VisualContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = visual_gate.load_contract()
        templates = cls.contract["authoritative_templates"]
        cls.shared = (ROOT / templates["shared_css"]["path"]).read_text(encoding="utf-8")
        cls.cv = (ROOT / templates["cv"]["path"]).read_text(encoding="utf-8")
        cls.cl = (ROOT / templates["cover_letter"]["path"]).read_text(encoding="utf-8")

    def check_mutation(self, *, shared=None, cv=None, cl=None):
        return visual_gate.check_texts(
            self.contract,
            self.shared if shared is None else shared,
            self.cv if cv is None else cv,
            self.cl if cl is None else cl,
            enforce_hashes=False,
        )

    def test_locked_templates_pass(self):
        self.assertEqual([], visual_gate.check_contract())

    def test_selected_projects_is_blocked(self):
        failures = self.check_mutation(cv=self.cv.replace("<h2>Projects</h2>", "<h2>Selected Projects</h2>", 1))
        self.assertIn("VISUAL_CV_FORBIDDEN", {code for code, _ in failures})
        self.assertIn("VISUAL_PROJECT_HEADING", {code for code, _ in failures})

    def test_unclassed_bullet_list_is_blocked(self):
        failures = self.check_mutation(cv=self.cv.replace('<ul class="evidence-list">', "<ul>", 1))
        self.assertIn("VISUAL_BULLET_CLASS", {code for code, _ in failures})

    def test_bullet_indent_drift_is_blocked(self):
        failures = self.check_mutation(cv=self.cv.replace("--bullet-text-indent:2.2mm;", "--bullet-text-indent:3.8mm;"))
        self.assertIn("VISUAL_CV_FRAGMENT", {code for code, _ in failures})

    def test_cover_letter_table_layout_is_blocked(self):
        failures = self.check_mutation(cl=self.cl.replace('<div class="meta">', "<table><tr><td>", 1))
        self.assertIn("VISUAL_TABLE_FORBIDDEN", {code for code, _ in failures})

    def test_cover_letter_justification_is_blocked(self):
        failures = self.check_mutation(cl=self.cl.replace("text-align:left;", "text-align:justify;"))
        self.assertIn("VISUAL_CL_FORBIDDEN", {code for code, _ in failures})

    def test_contact_order_drift_is_blocked(self):
        changed = self.cv.replace(
            '<span><a href="{{ identity.linkedin }}">LinkedIn</a></span><span><a href="{{ identity.portfolio }}">Portfolio</a></span>',
            '<span><a href="{{ identity.portfolio }}">Portfolio</a></span><span><a href="{{ identity.linkedin }}">LinkedIn</a></span>',
        )
        failures = self.check_mutation(cv=changed)
        self.assertIn("VISUAL_CONTACT_ORDER", {code for code, _ in failures})

    def test_hash_change_is_blocked(self):
        failures = visual_gate.check_texts(
            self.contract,
            self.shared,
            self.cv + "\n",
            self.cl,
            enforce_hashes=True,
        )
        self.assertIn("VISUAL_HASH_MISMATCH", {code for code, _ in failures})


if __name__ == "__main__":
    unittest.main()
