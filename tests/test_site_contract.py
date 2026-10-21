"""Static site navigation and offline-shell contract tests."""
from __future__ import annotations
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.append(values["id"])
        key = "href" if tag in {"a", "link"} else "src" if tag in {"script", "img"} else None
        if key and values.get(key):
            self.links.append((tag, values[key]))


class SiteContractTests(unittest.TestCase):
    def test_html_ids_and_internal_references(self):
        parser = SiteParser()
        parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        ids = set(parser.ids)
        duplicates = {value for value in parser.ids if parser.ids.count(value) > 1}
        self.assertFalse(duplicates, f"duplicate HTML ids: {sorted(duplicates)}")
        broken = []
        for tag, value in parser.links:
            if value.startswith(("https://", "http://", "mailto:", "data:", "javascript:")):
                continue
            if value.startswith("#"):
                if value[1:] and value[1:] not in ids:
                    broken.append((tag, value, "anchor"))
                continue
            local_path = unquote(urlparse(value).path)
            if local_path and not (ROOT / local_path).is_file():
                broken.append((tag, value, "file"))
        self.assertFalse(broken, f"broken local links/assets: {broken}")

    def test_service_worker_shell_has_only_existing_files_and_defers_large_payloads(self):
        text = (ROOT / "sw.js").read_text(encoding="utf-8")
        shell_text = text.split("const APP_SHELL = [", 1)[1].split("]", 1)[0]
        paths = re.findall(r"'([^']+)'", shell_text)
        missing = [item for item in paths if not (ROOT / item.removeprefix("./")).exists()]
        self.assertFalse(missing, f"service worker pre-cache files are missing: {missing}")
        self.assertNotIn("coverage.json", shell_text)
        self.assertNotIn("coverage-data.js", shell_text)
        self.assertIn("crypto-pair-data-bank-shell-v3", text)

    def test_publish_helper_never_reads_a_token_from_command_arguments(self):
        script = (ROOT / "scripts/termux_publish.sh").read_text(encoding="utf-8")
        self.assertIn("read -r -s", script)
        self.assertIn("gh auth login --with-token", script)
        self.assertNotIn("gh auth login --with-token \"$GH_TOKEN\"", script)
        self.assertIn("already has one or more branches", script)


if __name__ == "__main__":
    unittest.main()
