#!/usr/bin/env python3
"""Dispatch CV construction checks to the legacy or archetype contract."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import archetype_quality_gate
import quality_gate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cv")
    parser.add_argument("--diagnostic", required=True)
    parser.add_argument("--write-diagnostic", action="store_true")
    args = parser.parse_args()
    cv_path = Path(args.cv)
    payload = json.loads(cv_path.read_text(encoding="utf-8"))
    if payload.get("layout_contract") == "jobhuntai-archetype-v1" or "role_identity" in payload:
        return archetype_quality_gate.run(cv_path, Path(args.diagnostic), args.write_diagnostic)
    return quality_gate.run(cv_path, Path(args.diagnostic), args.write_diagnostic)


if __name__ == "__main__":
    sys.exit(main())
