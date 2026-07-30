import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import rendered_visual_gate as gate


class RenderedVisualGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def make_pdf(self, *, underfill_first=False, continued=False, duplicate=False, tiny=False):
        import fitz

        path = self.run_dir / "cv.pdf"
        document = fitz.open()
        headings = ["Professional Summary", "Technical Skills", "Experience"]
        for page_index in range(2):
            page = document.new_page(width=595, height=842)
            size = 8.5 if tiny else 10.2
            y = 40
            if page_index == 0:
                for heading in headings:
                    page.insert_text((50, y), heading, fontsize=11)
                    y += 22
                    for _ in range(7):
                        page.insert_text((50, y), "Evidence-backed body text for the target role and production delivery.", fontsize=size)
                        y += 16
                if not underfill_first:
                    while y < 760:
                        page.insert_text((50, y), "Additional role evidence with quantified outcome and context.", fontsize=size)
                        y += 16
            else:
                page.insert_text((50, y), "Projects Continued" if continued else "Projects", fontsize=11)
                y += 22
                for _ in range(20):
                    page.insert_text((50, y), "Project and experience evidence with methods, scale and result.", fontsize=size)
                    y += 16
                page.insert_text((50, y), "Education", fontsize=11)
                y += 22
                while y < 735:
                    page.insert_text((50, y), "Education and supporting evidence.", fontsize=size)
                    y += 16
                if duplicate:
                    page.insert_text((50, y), "Experience", fontsize=11)
        document.save(path)
        return path

    def make_docx(self, forced=False):
        path = self.run_dir / "cv.docx"
        xml = '<w:document xmlns:w="x"><w:body><w:p><w:pPr>'
        if forced:
            xml += "<w:pageBreakBefore/>"
        xml += "</w:pPr><w:r><w:t>Text</w:t></w:r></w:p></w:body></w:document>"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", xml)
        return path

    def review_for(self, pdf, docx):
        screenshots = self.run_dir / "pages"
        review_path = self.run_dir / "rendered_visual_review.json"
        gate.capture(
            pdf,
            review_path,
            screenshots,
            ["Professional Summary", "Technical Skills", "Experience", "Projects", "Education"],
            "review-agent",
            docx,
            "docx",
        )
        review = json.loads(review_path.read_text())
        review["manual_review"].update({
            "outcome": "pass",
            "inspected_all_pages": True,
            "no_large_blank_areas": True,
            "no_duplicate_or_continued_headings": True,
            "readable_typography": True,
            "natural_pagination": True,
            "section_flow_coherent": True,
            "notes": "Reviewed page one and page two images at readable zoom; spacing, headings and flow are coherent.",
        })
        return review

    @staticmethod
    def codes(failures):
        return {item["code"] for item in failures}

    def test_clean_two_page_pdf_passes(self):
        pdf = self.make_pdf()
        review = self.review_for(pdf, self.make_docx())
        self.assertEqual([], gate.validate(pdf, review, self.run_dir, "review-agent"))

    def test_underfilled_first_page_blocks(self):
        pdf = self.make_pdf(underfill_first=True)
        review = self.review_for(pdf, self.make_docx())
        self.assertIn("FIRST_PAGE_UNDERFILLED", self.codes(gate.validate(pdf, review, self.run_dir, "review-agent")))

    def test_continued_heading_blocks(self):
        pdf = self.make_pdf(continued=True)
        review = self.review_for(pdf, self.make_docx())
        codes = self.codes(gate.validate(pdf, review, self.run_dir, "review-agent"))
        self.assertIn("CONTINUED_HEADING_FORBIDDEN", codes)
        self.assertIn("SECTION_HEADING_MISSING", codes)

    def test_duplicate_heading_blocks(self):
        pdf = self.make_pdf(duplicate=True)
        review = self.review_for(pdf, self.make_docx())
        self.assertIn("DUPLICATE_SECTION_HEADING", self.codes(gate.validate(pdf, review, self.run_dir, "review-agent")))

    def test_forced_docx_page_break_blocks(self):
        pdf = self.make_pdf()
        review = self.review_for(pdf, self.make_docx(forced=True))
        self.assertIn("EXPLICIT_PAGE_BREAK_FORBIDDEN", self.codes(gate.validate(pdf, review, self.run_dir, "review-agent")))

    def test_stale_screenshot_blocks(self):
        pdf = self.make_pdf()
        review = self.review_for(pdf, self.make_docx())
        screenshot = self.run_dir / review["pages"][0]["screenshot_path"]
        screenshot.write_bytes(b"stale")
        self.assertIn("RENDERED_SCREENSHOT_STALE", self.codes(gate.validate(pdf, review, self.run_dir, "review-agent")))

    def test_tiny_body_font_blocks(self):
        pdf = self.make_pdf(tiny=True)
        review = self.review_for(pdf, self.make_docx())
        self.assertIn("BODY_FONT_TOO_SMALL", self.codes(gate.validate(pdf, review, self.run_dir, "review-agent")))

    def test_native_google_doc_cannot_be_canonical(self):
        pdf = self.make_pdf()
        review = self.review_for(pdf, self.make_docx())
        review["editable_source"]["native_google_doc_used_as_canonical"] = True
        self.assertIn("NATIVE_GOOGLE_DOC_CANONICAL_FORBIDDEN", self.codes(gate.validate(pdf, review, self.run_dir, "review-agent")))


if __name__ == "__main__":
    unittest.main()
