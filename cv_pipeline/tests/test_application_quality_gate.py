import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import application_quality_gate
import cv_length_gate
import rendered_visual_gate
import review_loop
import review_scoring


def scored_report(lane, cv_path, score=92):
    remaining = float(score)
    breakdown = {}
    for dimension, maximum in review_scoring.LANE_RUBRICS[lane].items():
        points = min(float(maximum), remaining)
        breakdown[dimension] = points
        remaining = round(remaining - points, 1)
    return {
        "lane": lane,
        "verdict": "approve",
        "score": score,
        "score_breakdown": breakdown,
        "score_rationale": "The exact final CV was scored against every fixed lane dimension, with points withheld where the evidence or presentation was less than perfect.",
        "cv_sha256": review_loop.sha256_file(cv_path),
        "issues": [],
        "summary": "Clean cold review",
    }


class ApplicationQualityGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temp.name)
        for name, content in {
            "job_description.md": "JD",
            "role_identity.json": '{"archetype": "data_scientist"}',
            "evidence_ranking.json": '{"ranked": []}',
            "cv.json": '{"candidate": "Varun", "summary": "Python SQL classification"}',
            "cv_diagnostic.json": '{"passed": true}',
        }.items():
            (self.run_dir / name).write_text(content, encoding="utf-8")

        import fitz

        pdf_path = self.run_dir / "cv.pdf"
        document = fitz.open()
        page = document.new_page(width=595, height=842)
        y = 40
        for heading in ("Professional Summary", "Technical Skills", "Experience", "Education"):
            page.insert_text((50, y), heading, fontsize=11)
            y += 22
            for _ in range(8):
                page.insert_text((50, y), "Evidence-backed role content with method, scale and result.", fontsize=10.2)
                y += 16
        while y < 750:
            page.insert_text((50, y), "Additional complete evidence for a readable one-page CV.", fontsize=10.2)
            y += 16
        document.save(pdf_path)

        docx_path = self.run_dir / "cv.docx"
        with zipfile.ZipFile(docx_path, "w") as archive:
            archive.writestr(
                "word/document.xml",
                '<w:document xmlns:w="x"><w:body><w:p><w:r><w:t>Text</w:t></w:r></w:p></w:body></w:document>',
            )

        state = review_loop.create_state("JOB-1")
        cv_path = self.run_dir / "cv.json"
        review_loop.record_tailor(state, cv_path, "tailor-agent")
        review_loop.record_review(state, scored_report("completeness", cv_path, 92), "review-completeness", "completeness")
        review_loop.record_review(state, scored_report("defensibility", cv_path, 94), "review-defensibility", "defensibility")
        review_loop.record_review(state, scored_report("competitiveness", cv_path, 92), "review-competitiveness", "competitiveness")
        review_loop.write_json(self.run_dir / "review_loop.json", state)

        visual_review_path = self.run_dir / "rendered_visual_review.json"
        rendered_visual_gate.capture(
            pdf_path,
            visual_review_path,
            self.run_dir / "rendered_pages",
            ["Professional Summary", "Technical Skills", "Experience", "Education"],
            "review-competitiveness",
            docx_path,
            "docx",
        )
        visual_review = json.loads(visual_review_path.read_text(encoding="utf-8"))
        visual_review["manual_review"].update({
            "outcome": "pass",
            "inspected_all_pages": True,
            "no_large_blank_areas": True,
            "no_duplicate_or_continued_headings": True,
            "readable_typography": True,
            "natural_pagination": True,
            "section_flow_coherent": True,
            "notes": "Inspected the complete page image at readable zoom; layout, typography and section flow are clean.",
        })
        visual_review_path.write_text(json.dumps(visual_review), encoding="utf-8")

        cv_length_audit = {
            "contract": cv_length_gate.CONTRACT,
            "strategy_decision": cv_length_gate.ONE_PAGE_ALLOWED,
            "strategy_rationale": "A narrow junior profile with one compact evidence set can be represented completely on one page.",
            "final_page_count": 1,
            "candidate_role_profile": {
                "seniority": "junior",
                "relevant_years": 1,
                "relevant_roles": 1,
                "relevant_projects": 0,
                "technical_breadth": 2,
                "domain_transfer_required": False,
            },
            "essential_evidence": [{"id": "python", "match_any": ["Python"]}],
            "omissions": [],
            "review_judgement": {
                "material_evidence_removed": False,
                "omission_audit_complete": True,
                "page_strategy_approved": True,
                "rationale": "The final one-page CV retains the complete role-critical evidence set without compression loss.",
                "review_actor": "review-completeness",
                "review_iteration": 1,
                "cv_sha256": review_loop.sha256_file(cv_path),
            },
            "page_transition": {},
            "page_fill": [visual_review["pages"][0]["meaningful_fill"]],
        }
        (self.run_dir / "cv_length_audit.json").write_text(json.dumps(cv_length_audit), encoding="utf-8")

        self.manifest = {
            "contract": "jobhuntai-application-quality-v1",
            "decision": "apply",
            "artefacts": {
                "job_description": "job_description.md",
                "role_identity": "role_identity.json",
                "evidence_ranking": "evidence_ranking.json",
                "cv": "cv.json",
                "cv_diagnostic": "cv_diagnostic.json",
                "cv_length_audit": "cv_length_audit.json",
                "cv_pdf": "cv.pdf",
                "rendered_visual_review": "rendered_visual_review.json",
                "review_loop": "review_loop.json",
            },
            "checks": {
                "preflight": {"status": "passed"},
                "duplicate": {"status": "passed", "outcome": "clear"},
                "visa": {"status": "passed", "outcome": "viable"},
                "role_identity": {"status": "passed"},
                "evidence": {"status": "passed"},
                "cv_length": {"status": "passed"},
                "factual": {"status": "passed"},
                "positioning": {"status": "passed"},
                "visual": {"status": "passed"},
                "render": {"status": "passed"},
                "rendered_visual_review": {"status": "passed"},
            },
            "tracker": {"status": "checked", "mode": "read_only"},
            "drive_save": {"status": "verified"},
        }
        (self.run_dir / "application_manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def run_gate(self):
        return application_quality_gate.run(self.run_dir, self.run_dir / "application_manifest.json")

    def write_manifest(self):
        (self.run_dir / "application_manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def test_clean_package_passes(self):
        self.assertEqual([], self.run_gate())

    def test_review_loop_is_mandatory(self):
        self.manifest["artefacts"].pop("review_loop")
        self.write_manifest()
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("REVIEW_LOOP_PATH_MISSING", codes)

    def test_cv_length_audit_is_mandatory(self):
        self.manifest["artefacts"].pop("cv_length_audit")
        self.write_manifest()
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("CV_LENGTH_AUDIT_PATH_MISSING", codes)

    def test_rendered_visual_review_is_mandatory(self):
        self.manifest["artefacts"].pop("rendered_visual_review")
        self.write_manifest()
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("RENDERED_VISUAL_REVIEW_PATH_MISSING", codes)

    def test_failed_cv_length_check_blocks_release(self):
        self.manifest["checks"]["cv_length"]["status"] = "failed"
        self.write_manifest()
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("CV_LENGTH_NOT_PASSED", codes)

    def test_failed_visual_check_blocks_release(self):
        self.manifest["checks"]["visual"]["status"] = "failed"
        self.write_manifest()
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("VISUAL_NOT_PASSED", codes)

    def test_stale_rendered_screenshot_blocks_release(self):
        review = json.loads((self.run_dir / "rendered_visual_review.json").read_text())
        (self.run_dir / review["pages"][0]["screenshot_path"]).write_bytes(b"stale")
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("RENDERED_SCREENSHOT_STALE", codes)

    def test_page_fill_must_come_from_exact_render(self):
        audit_path = self.run_dir / "cv_length_audit.json"
        audit = json.loads(audit_path.read_text())
        audit["page_fill"] = [0.10]
        audit_path.write_text(json.dumps(audit))
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("PAGE_FILL_RENDER_MISMATCH", codes)

    def test_duplicate_application_blocks_release(self):
        self.manifest["checks"]["duplicate"]["outcome"] = "existing_application"
        self.write_manifest()
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("DUPLICATE_BLOCKED", codes)

    def test_unverified_drive_save_blocks_release(self):
        self.manifest["drive_save"]["status"] = "assumed"
        self.write_manifest()
        codes = {failure["code"] for failure in self.run_gate()}
        self.assertIn("DRIVE_SAVE_UNVERIFIED", codes)


if __name__ == "__main__":
    unittest.main()
