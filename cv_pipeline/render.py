#!/usr/bin/env python3
"""Render JobHuntAI CVs and cover letters from canonical HTML templates.

Legacy and archetype payloads use separate content contracts but share the
same serif-blue document design and PDF acceptance checks.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

import composition_gate
from archetype_visual_gate import check_archetype_cv_pdf, check_archetype_template_contract
from visual_gate import check_cover_letter_pdf, check_cv_pdf, check_template_contract

ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = ROOT / "templates"
TEMPLATES = {"cv": "cv_template.html", "cl": "cover_letter_template.html"}
FONT_SOURCE_COMMIT = "352f6b7d9d6cc4fa9e242b931291d31b21a6dc84"
FONT_ASSETS = {
    "CormorantGaramond.ttf": f"https://raw.githubusercontent.com/google/fonts/{FONT_SOURCE_COMMIT}/ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf",
    "Lora.ttf": f"https://raw.githubusercontent.com/google/fonts/{FONT_SOURCE_COMMIT}/ofl/lora/Lora%5Bwght%5D.ttf",
    "Lora-Italic.ttf": f"https://raw.githubusercontent.com/google/fonts/{FONT_SOURCE_COMMIT}/ofl/lora/Lora-Italic%5Bwght%5D.ttf",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_archetype_cv(kind: str, payload: dict[str, Any]) -> bool:
    return kind == "cv" and payload.get("layout_contract") == "jobhuntai-archetype-v1"


def _font_cache_dir() -> Path:
    return Path.home() / ".cache" / "jobhuntai" / "fonts"


def _font_face_css() -> str:
    """Return deterministic @font-face rules, downloading pinned font assets once.

    If the network is unavailable the renderer falls back to installed
    Cormorant/Lora and then Georgia/serif. The PDF gate still prevents an
    unintended sans-serif fallback from shipping.
    """
    cache = _font_cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    try:
        for filename, url in FONT_ASSETS.items():
            target = cache / filename
            if not target.exists() or target.stat().st_size == 0:
                urllib.request.urlretrieve(url, target)
    except (OSError, urllib.error.URLError) as exc:
        print(f"FONT NOTICE: unable to refresh pinned serif assets ({exc}); using installed CSS fallbacks", file=sys.stderr)
        return ""

    cormorant = (cache / "CormorantGaramond.ttf").resolve().as_uri()
    lora = (cache / "Lora.ttf").resolve().as_uri()
    lora_italic = (cache / "Lora-Italic.ttf").resolve().as_uri()
    return f"""
<style data-jobhuntai-fonts="pinned-google-fonts-{FONT_SOURCE_COMMIT}">
@font-face {{ font-family:"Cormorant Garamond"; src:url("{cormorant}") format("truetype"); font-style:normal; font-weight:400; }}
@font-face {{ font-family:"Cormorant Garamond"; src:url("{cormorant}") format("truetype"); font-style:normal; font-weight:600; }}
@font-face {{ font-family:"Lora"; src:url("{lora}") format("truetype"); font-style:normal; font-weight:400; }}
@font-face {{ font-family:"Lora"; src:url("{lora}") format("truetype"); font-style:normal; font-weight:600; }}
@font-face {{ font-family:"Lora"; src:url("{lora_italic}") format("truetype"); font-style:italic; font-weight:400; }}
</style>
"""


def _write_composition_report(path: Path | None, report: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def render(
    kind: str,
    payload_path: Path,
    html_out: Path,
    pdf_out: Path,
    composition_out: Path | None = None,
) -> list[tuple[str, str]]:
    payload = load_json(payload_path)
    archetype_cv = is_archetype_cv(kind, payload)
    failures = check_archetype_template_contract() if archetype_cv else check_template_contract()
    if failures:
        return failures

    if archetype_cv:
        depth_failures = composition_gate.check_payload_depth(payload)
        if depth_failures:
            _write_composition_report(composition_out, composition_gate.composition_report(payload))
            return depth_failures

    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=("html", "xml"), default_for_string=True),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template_name = "cv_archetype_template.html" if archetype_cv else TEMPLATES[kind]
    rendered = environment.get_template(template_name).render(**payload)
    font_css = _font_face_css()
    if font_css:
        rendered = rendered.replace("</head>", font_css + "\n</head>", 1)

    html_out.parent.mkdir(parents=True, exist_ok=True)
    pdf_out.parent.mkdir(parents=True, exist_ok=True)
    html_out.write_text(rendered, encoding="utf-8")
    font_config = FontConfiguration()
    document = HTML(string=rendered, base_url=str(TEMPLATE_DIR)).render(font_config=font_config)

    composition_report: dict[str, Any] | None = None
    if archetype_cv:
        composition_report = composition_gate.composition_report(payload, document)
        failures.extend((item["code"], item["detail"]) for item in composition_report["failures"])
        _write_composition_report(composition_out, composition_report)

    document.write_pdf(str(pdf_out))

    if kind == "cv":
        failures.extend(check_archetype_cv_pdf(pdf_out, payload) if archetype_cv else check_cv_pdf(pdf_out, payload))
    else:
        failures.extend(check_cover_letter_pdf(pdf_out, payload))
    if failures:
        html_out.unlink(missing_ok=True)
        pdf_out.unlink(missing_ok=True)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a JobHuntAI application artefact")
    parser.add_argument("kind", choices=("cv", "cl"))
    parser.add_argument("payload")
    parser.add_argument("--html-out", required=True)
    parser.add_argument("--pdf-out", required=True)
    parser.add_argument("--composition-out", help="Optional JSON report with block-depth and per-page fill measurements")
    args = parser.parse_args()
    failures = render(
        args.kind,
        Path(args.payload),
        Path(args.html_out),
        Path(args.pdf_out),
        Path(args.composition_out) if args.composition_out else None,
    )
    if failures:
        print(f"RENDER BLOCKED - {len(failures)} failure(s):")
        for code, detail in failures:
            print(f"[{code}] {detail}")
        return 2
    print(f"RENDER CLEAN: {args.pdf_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
