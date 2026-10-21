"""Contract tests for the public data catalogue and repository integrity."""
from __future__ import annotations
import csv
import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ASSETS = {"BTC", "ETH", "SOL", "BNB", "DOGE", "LTC", "XRP", "TRX", "BCH", "AVAX", "DASH", "SUI", "ARB", "ADA"}
SCRIPT_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]")


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class CatalogTest(unittest.TestCase):
    def test_download_resource_directory_matches_seed_leads(self):
        data = read_json("catalog/download-resources.json")
        rows = data["resources"]
        self.assertEqual(len(rows), 12)
        self.assertEqual(data["resource_count"], 12)
        self.assertEqual(len({row["resource_id"] for row in rows}), 12)
        self.assertTrue(all(row["verification_state"] == "seed_research_lead_not_live_download_tested" for row in rows))
        self.assertTrue(all(row["source_url"].startswith("https://") for row in rows))
        self.assertTrue(all(row["direct_download_or_index_url"].startswith("https://") for row in rows))

    def test_download_resource_json_csv_and_ui_bundle_agree(self):
        data = read_json("catalog/download-resources.json")
        with (ROOT / "catalog/download-resources.csv").open(encoding="utf-8", newline="") as stream:
            csv_rows = list(csv.DictReader(stream))
        ids_json = {row["resource_id"] for row in data["resources"]}
        ids_csv = {row["resource_id"] for row in csv_rows}
        self.assertEqual(ids_json, ids_csv)
        js_text = (ROOT / "web/assets/catalog.js").read_text(encoding="utf-8")
        payload = json.loads(js_text.removeprefix("window.CRYPTO_DATA_BANK = ").strip().rstrip(";"))
        self.assertEqual({row["resource_id"] for row in payload["downloadResources"]}, ids_json)

    def test_source_registry_has_unique_ids_and_expected_size(self):
        data = read_json("catalog/sources.json")
        ids = [source["source_id"] for source in data["sources"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 92)

    def test_asset_universe(self):
        data = read_json("catalog/assets.json")
        self.assertEqual({asset["symbol"] for asset in data["assets"]}, EXPECTED_ASSETS)

    def test_coverage_references_known_sources_and_has_expected_grain(self):
        sources = read_json("catalog/sources.json")["sources"]
        source_ids = {source["source_id"] for source in sources}
        rows = read_json("catalog/coverage.json")["rows"]
        self.assertEqual(len(rows), 10458)
        self.assertTrue(all(row.get("source_id") in source_ids for row in rows))
        self.assertEqual({row["asset"] for row in rows}, EXPECTED_ASSETS)
        bundle_text = (ROOT / "web/assets/coverage-data.js").read_text(encoding="utf-8")
        ui_rows = json.loads(bundle_text.removeprefix("window.CRYPTO_COVERAGE_DATA = ").strip().rstrip(";"))
        self.assertEqual(len(ui_rows), 10458)
        app_text = (ROOT / "web/assets/catalog.js").read_text(encoding="utf-8")
        app_payload = json.loads(app_text.removeprefix("window.CRYPTO_DATA_BANK = ").strip().rstrip(";"))
        self.assertEqual(app_payload["coverage"], [])

    def test_coverage_ui_loads_large_dataset_on_demand(self):
        app = (ROOT / "web/assets/app.js").read_text(encoding="utf-8")
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("function ensureCoverageLoaded()", app)
        self.assertIn("web/assets/coverage-data.js", app)
        self.assertIn("if(view==='coverage'&&!state.coverageReady)ensureCoverageLoaded()", app)
        self.assertNotIn('src="web/assets/coverage-data.js"', html)
        self.assertIn("if(!state.coverageReady)return", app)
        service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        shell = service_worker.split("const APP_SHELL = [", 1)[1].split("]", 1)[0]
        self.assertNotIn("coverage.json", shell)
        self.assertNotIn("coverage-data.js", shell)

    def test_status_counts_are_explicit_and_reproducible(self):
        with (ROOT / "data/availability-matrix.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        observed = {}
        for row in rows:
            status = row["Overall coverage status"]
            observed[status] = observed.get(status, 0) + 1
        self.assertEqual(observed, {"VERIFIED": 1110, "NOT_CHECKED": 9229, "NOT_APPLICABLE": 119})
        self.assertTrue(all(row.get("Actual raw rows counted locally", "") in {"NOT_MEASURED", "NOT_APPLICABLE"} for row in rows))

    def test_case_sensitive_interval_tokens_are_preserved(self):
        intervals = read_json("catalog/timeframes.json")["intervals"]
        by_code = {item["code"]: item for item in intervals}
        self.assertIn("1m", by_code)
        self.assertIn("1M", by_code)
        self.assertNotEqual(by_code["1m"]["code"], by_code["1M"]["code"])
        self.assertTrue(by_code["1M"]["provider_specific_semantics"])

    def test_calendar_month_is_not_assigned_a_fixed_duration(self):
        intervals = read_json("catalog/timeframes.json")["intervals"]
        month = next(item for item in intervals if item["code"] == "1mo")
        self.assertEqual(month["interval_kind"], "calendar")
        self.assertIsNone(month["nominal_seconds"])
        self.assertTrue(month["provider_specific_semantics"])

    def test_publisher_reported_count_has_qualified_provenance(self):
        coverage = read_json("catalog/coverage.json")["rows"]
        reported = [row for row in coverage if row.get("published_candle_count") is not None]
        self.assertTrue(reported)
        self.assertTrue(all("PUBLISHER_REPORTED" in row.get("count_basis", "") for row in reported))
        self.assertTrue(all("NOT_INDEPENDENTLY_COUNTED" in row.get("count_basis", "") for row in reported))

    def test_seed_snapshot_does_not_claim_local_raw_candle_counts(self):
        with (ROOT / "data/local-raw-data-inventory.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertTrue(rows)
        for row in rows:
            if "Local files found" in row:
                self.assertEqual(int(row["Local files found"] or 0), 0)
            if "Actual candle rows counted" in row:
                self.assertEqual(int(row["Actual candle rows counted"] or 0), 0)

    def test_repository_text_is_free_of_persian_or_arabic_script(self):
        ignored = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "venv"}
        allowed = {".md", ".txt", ".csv", ".json", ".jsonl", ".py", ".js", ".html", ".css", ".svg", ".yml", ".yaml", ".cff", ".toml", ".sh", ".gitignore", ".gitattributes"}
        inspected = 0
        for path in ROOT.rglob("*"):
            if not path.is_file() or any(part in ignored for part in path.relative_to(ROOT).parts):
                continue
            if path.suffix.lower() not in allowed and path.name not in {"LICENSE", "NOTICE"}:
                continue
            content = path.read_text(encoding="utf-8")
            self.assertIsNone(SCRIPT_RE.search(content), f"non-English script found in {path.relative_to(ROOT)}")
            self.assertFalse(content.startswith("\ufeff"), f"UTF-8 BOM found in {path.relative_to(ROOT)}")
            inspected += 1
        self.assertGreater(inspected, 30)

    def test_build_and_validate(self):
        subprocess.run([sys.executable, str(ROOT / "scripts/build_catalog.py")], check=True, capture_output=True, text=True)
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/validate_catalog.py")], check=True, capture_output=True, text=True)
        self.assertIn("validation passed", proc.stdout.lower())

    def test_manifest_hashes_match_tracked_files(self):
        manifest = read_json("MANIFEST.json")
        self.assertTrue(manifest.get("self_hash_excluded"))
        listed = {row["path"]: row for row in manifest["files"]}
        self.assertNotIn("MANIFEST.json", listed)
        self.assertIn("index.html", listed)
        for relative, row in listed.items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), f"manifest path missing: {relative}")
            self.assertEqual(path.stat().st_size, row["bytes"], f"byte size drift: {relative}")
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["sha256"], f"hash drift: {relative}")


if __name__ == "__main__":
    unittest.main()
