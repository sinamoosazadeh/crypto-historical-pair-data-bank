#!/usr/bin/env python3
"""Fail if repository text or paths contain Arabic-script characters.

The project is intentionally published in English only. The check targets readable text
files, not binary archive payloads. Extend TEXT_SUFFIXES when new text formats are added.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".md", ".csv", ".json", ".html", ".js", ".css", ".py", ".yml", ".yaml",
    ".toml", ".txt", ".cff", ".svg", ".xml", ".sh", ".webmanifest", ".ini",
}
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "venv"}
# Arabic Unicode blocks include Persian and Arabic presentation forms. The policy is stricter
# than checking only Persian-specific letters so Arabic-script prose cannot slip into the repo.
ARABIC_SCRIPT = re.compile(r"[\u0600-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")


def candidate_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def main() -> int:
    violations = []
    scanned = 0
    for path in candidate_files():
        scanned += 1
        rel = path.relative_to(ROOT).as_posix()
        name_matches = ARABIC_SCRIPT.findall(rel)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            violations.append(f"{rel}: not valid UTF-8 text ({exc})")
            continue
        matches = ARABIC_SCRIPT.findall(text)
        if name_matches or matches:
            preview = "".join(sorted(set(name_matches + matches))[:12])
            violations.append(f"{rel}: Arabic-script characters found ({len(matches) + len(name_matches)}; {preview!r})")
    if violations:
        for issue in violations:
            print(f"ERROR: {issue}", file=sys.stderr)
        print(f"English-only policy failed: {len(violations)} file(s) violated; scanned {scanned} text files.", file=sys.stderr)
        return 1
    print(f"English-only text policy passed: scanned {scanned} text files; no Arabic-script characters found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
