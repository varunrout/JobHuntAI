import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import composition_gate


class FakeBox:
    def __init__(self, y=0, height=0, children=None):
        self.position_y = y
        self.height = height
        self.children = children or []


class FakePage:
    def __init__(self, height, lowest):
        self._page_box = FakeBox(0, height, [FakeBox(0, lowest)])


class FakeDocument:
    def __init__(self, fills):
        self.pages = [FakePage(1000, int(1000 * fill)) for fill in fills]


def payload(maximum_pages=2):
    return {
        "page_strategy": {"maximum_pages": maximum_pages},
        "experience": [
            {
                "org": "E.ON Energy Markets",
                "roles": [
                    {"title": "Quantitative Market Analyst", "bullets": ["a", "b"]},
                    {"title": "Quantitative Analysis Intern", "bullets": ["c"]},
                ],
            }
        ],
        "projects": [{"title": "Energy Market Tracker", "bullets": ["a", "b", "c"]}],
    }


class CompositionGateTests(unittest.TestCase):
    def test_employer_block_below_three_is_blocked(self):
        cv = payload()
        cv["experience"][0]["roles"][1]["bullets"] = []
        codes = {code for code, _ in composition_gate.check_payload_depth(cv)}
        self.assertIn("EXPERIENCE_BLOCK_UNDERFED", codes)
        self.assertIn("EMPTY_NESTED_SUBROLE", codes)

    def test_nested_subroles_may_be_one_or_two_when_parent_clears_floor(self):
        self.assertEqual([], composition_gate.check_payload_depth(payload()))

    def test_independent_practice_keeps_two_bullet_floor(self):
        cv = payload()
        cv["experience"] = [{
            "experience_type": "independent_practice",
            "org": "Independent Practice",
            "bullets": ["a", "b"],
        }]
        self.assertEqual([], composition_gate.check_payload_depth(cv))

    def test_two_page_project_with_two_bullets_is_blocked(self):
        cv = payload(2)
        cv["projects"][0]["bullets"] = ["a", "b"]
        codes = {code for code, _ in composition_gate.check_payload_depth(cv)}
        self.assertIn("PROJECT_BLOCK_UNDERFED", codes)

    def test_one_page_project_may_use_two_bullets(self):
        cv = payload(1)
        cv["projects"][0]["bullets"] = ["a", "b"]
        self.assertEqual([], composition_gate.check_payload_depth(cv))

    def test_two_page_fill_thresholds_pass_when_both_pages_are_dense(self):
        failures, fill = composition_gate.check_document_composition(FakeDocument([0.91, 0.78]))
        self.assertEqual([], failures)
        self.assertEqual([0.91, 0.78], fill)

    def test_page_one_underfill_is_hard_failure(self):
        failures, _ = composition_gate.check_document_composition(FakeDocument([0.72, 0.82]))
        self.assertIn("PAGE_ONE_UNDERFILLED", {code for code, _ in failures})

    def test_page_two_underfill_is_hard_failure(self):
        failures, _ = composition_gate.check_document_composition(FakeDocument([0.90, 0.55]))
        self.assertIn("SECOND_PAGE_UNDERFILLED", {code for code, _ in failures})

    def test_template_uses_breakable_blocks_and_welded_bullets(self):
        html = (ROOT / "templates" / "cv_archetype_template.html").read_text(encoding="utf-8")
        self.assertIn(".block { margin-bottom:1.15mm; break-inside:auto; page-break-inside:auto; }", html)
        self.assertIn(".subrole { margin-bottom:1mm; break-inside:auto; page-break-inside:auto; }", html)
        self.assertIn(".project { margin-bottom:.75mm; break-inside:auto; page-break-inside:auto; }", html)
        self.assertIn("break-inside:avoid;\n  page-break-inside:avoid;", html)
        self.assertIn("orphans:2;", html)
        self.assertIn("widows:2;", html)


if __name__ == "__main__":
    unittest.main()
