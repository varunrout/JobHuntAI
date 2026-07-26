#!/usr/bin/env python3
"""Hard visual gate for a rendered JobHuntAI cover letter."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from visual_gate import check_cover_letter_pdf, check_template_contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("payload")
    args = parser.parse_args()

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    failures = check_template_contract()
    failures.extend(check_cover_letter_pdf(Path(args.pdf), payload))
    if failures:
        for code, detail in failures:
            print(f"[{code}] {detail}")
        return 2
    print("COVER-LETTER VISUAL GATE CLEAN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
