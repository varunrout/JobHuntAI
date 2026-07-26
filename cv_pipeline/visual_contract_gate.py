#!/usr/bin/env python3
"""Hard gate for the approved JobHuntAI CV and cover-letter HTML design.

This gate is intentionally strict. Changes to layout-critical selectors, values,
section names or structural classes must update this contract explicitly and pass
review. It prevents silent visual drift in generated application documents.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CV_TEMPLATE = ROOT / "templates" / "cv_template.html"
CL_TEMPLATE = ROOT / "templates" / "cover_letter_template.html"


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def require(text: str, fragments: list[str], scope: str) -> list[str]:
    failures: list[str] = []
    normalised = compact(text)
    for fragment in fragments:
        if compact(fragment) not in normalised:
            failures.append(f"{scope}: missing locked visual fragment: {fragment}")
    return failures


def forbid(text: str, fragments: list[str], scope: str) -> list[str]:
    failures: list[str] = []
    normalised = compact(text)
    for fragment in fragments:
        if compact(fragment) in normalised:
            failures.append(f"{scope}: forbidden visual fragment present: {fragment}")
    return failures


def check_cv(text: str) -> list[str]:
    required = [
        '--font:"Times New Roman","Liberation Serif",serif;',
        '--body-size:9.25pt;',
        '--bullet-text-indent:3.8mm;',
        '--bullet-marker-offset:.45mm;',
        '@page { size:A4; margin:12mm 13mm 11mm; }',
        'body { font-family:var(--font); font-size:var(--body-size); line-height:1.17; color:var(--ink); }',
        '.name { font-size:17pt; font-weight:700; letter-spacing:.01em; text-transform:uppercase; }',
        '.contact { font-size:8.35pt; margin-top:1mm; white-space:nowrap; }',
        'h2 { font-size:10.7pt;',
        'border-bottom:.55pt solid var(--rule);',
        '.row { display:grid; grid-template-columns:minmax(0,1fr) auto; column-gap:4mm; align-items:baseline;',
        '.org { font-style:italic; margin-top:.05mm; break-after:avoid; }',
        '.evidence-list { list-style:none; margin:.25mm 0 0 0; padding:0; font-family:var(--font); font-size:var(--body-size); line-height:1.17; }',
        '.evidence-list li { position:relative; margin:0 0 .15mm 0; padding-left:var(--bullet-text-indent); font-family:var(--font); font-size:var(--body-size); line-height:1.17;',
        '.evidence-list li::before { content:"•"; position:absolute; left:var(--bullet-marker-offset); top:0;',
        '<section><h2>Professional Summary</h2>',
        '<section class="capabilities"><h2>Skills</h2>',
        '<section><h2>Experience</h2>',
        '<section><h2>Projects</h2>',
        '<section class="education"><h2>Education</h2>',
        '<ul class="evidence-list">',
        '<a href="{{ identity.portfolio }}">Portfolio</a>',
        '<a href="{{ identity.github }}">GitHub</a>',
    ]
    failures = require(text, required, "CV")
    failures += forbid(
        text,
        [
            "Selected Projects",
            "Core Capabilities",
            "display:flex",
            "<table",
            "list-style:disc",
            "font-family:sans-serif",
        ],
        "CV",
    )
    if text.count('<h2>Projects</h2>') != 2:
        failures.append("CV: both project-placement branches must render the exact heading 'Projects'")
    if text.count('class="evidence-list"') < 3:
        failures.append("CV: every experience and project list must use the shared evidence-list class")
    return failures


def check_cl(text: str) -> list[str]:
    required = [
        '--font:"Times New Roman","Liberation Serif",serif;',
        '@page { size:A4; margin:14mm 17mm 14mm; }',
        'body { font-family:var(--font); font-size:10.2pt; line-height:1.28; color:var(--ink); }',
        '.name { font-size:17pt; font-weight:700; letter-spacing:.01em; text-transform:uppercase; }',
        '.contact { font-size:8.35pt; margin-top:1mm; white-space:nowrap; }',
        '.role { font-size:11.5pt; font-weight:700; border-bottom:.55pt solid var(--rule); padding-bottom:.5mm; margin:3mm 0 .6mm; }',
        '.meta { display:grid; grid-template-columns:minmax(0,1fr) auto; column-gap:4mm; align-items:baseline; margin-bottom:3mm; }',
        'p { margin:0 0 2.2mm 0; text-align:justify; }',
        '<div class="role">{{ role_title }}</div>',
        '<div class="meta"><strong>{{ company }}</strong><span>{{ date }}</span></div>',
        '<a href="{{ identity.portfolio }}">Portfolio</a>',
        '<a href="{{ identity.github }}">GitHub</a>',
    ]
    failures = require(text, required, "CL")
    failures += forbid(text, ["<table", "margin-left:", "padding-left:"], "CL")
    return failures


def main() -> int:
    failures: list[str] = []
    failures.extend(check_cv(CV_TEMPLATE.read_text(encoding="utf-8")))
    failures.extend(check_cl(CL_TEMPLATE.read_text(encoding="utf-8")))
    if failures:
        print("VISUAL CONTRACT FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 2
    print("VISUAL CONTRACT CLEAN: CV and cover-letter HTML are locked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
