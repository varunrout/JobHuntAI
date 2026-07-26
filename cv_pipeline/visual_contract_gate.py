#!/usr/bin/env python3
"""Compatibility entrypoint for the canonical JobHuntAI visual contract."""
from __future__ import annotations

import sys

from visual_gate import check_template_contract


def main() -> int:
    failures = check_template_contract()
    if failures:
        print("VISUAL CONTRACT FAILED")
        for code, detail in failures:
            print(f"- [{code}] {detail}")
        return 2
    print("VISUAL CONTRACT CLEAN: CV and cover-letter HTML are locked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
