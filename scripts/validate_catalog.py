#!/usr/bin/env python3
"""Validate source snapshot integrity, normalized catalogues, and English-only repository text."""
from __future__ import annotations
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []
WARNINGS: list[str] = []
PERSIAN_ARABIC_SCRIPT = re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]")
EXPECTED_ASSETS = {"BTC", "ETH", "SOL", "BNB", "DOGE", "LTC", "XRP", "TRX", "BCH", "AVAX", "DASH", "SUI", "ARB", "ADA"}
EXPECTED_SOURCE_ROUTES = 92
EXPECTED_COVERAGE_ROWS = 10458
EXPECTED_STATUS_COUNTS = {"VERIFIED": 1110, "NOT_CHECKED": 9229, "NOT_APPLICABLE": 119}
TEXT_SUFFIXES = {".md", ".txt", ".csv", ".json", ".jsonl", ".py", ".js", ".html", ".css", ".svg", ".yml", ".yaml", ".cff", ".toml", ".sh", ".gitignore", ".gitattributes"}
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "venv"}


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        ERRORS.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
        return {}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            return list(reader.fieldnames or []), list(reader)
    except Exception as exc:
        ERRORS.append(f"{path.relative_to(ROOT)}: invalid CSV: {exc}")
        return [], []


def check_url(field: str, url: str, source_id: str) -> None:
    if not url:
        return
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        ERRORS.append(f"{source_id}: invalid {field}: {url}")


def check_english_only() -> None:
    checked = 0
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() == ".pyc":
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", "NOTICE"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            ERRORS.append(f"{rel}: text file is not valid UTF-8")
            continue
        except OSError as exc:
            ERRORS.append(f"{rel}: unable to read text file: {exc}")
            continue
        checked += 1
        match = PERSIAN_ARABIC_SCRIPT.search(text)
        if match:
            ERRORS.append(f"{rel}: non-English Arabic/Persian-script character U+{ord(match.group()):04X} found")
        if text.startswith("\ufeff"):
            ERRORS.append(f"{rel}: UTF-8 BOM is not allowed in repository text files")
    print(f"English-only source check: {checked} text files scanned")


def check_local_index_links() -> None:
    html_path = ROOT / "index.html"
    html = html_path.read_text(encoding="utf-8")
    for attr, value in re.findall(r"\b(href|src)=[\"']([^\"']+)[\"']", html):
        if value.startswith(("https://", "http://", "data:", "#", "mailto:", "javascript:")):
            continue
        local = ROOT / value.split("?", 1)[0].split("#", 1)[0]
        if value and not local.exists():
            ERRORS.append(f"index.html: missing local {attr} target: {value}")


def check_navigation_contract() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    ids = re.findall(r"\bid=[\"']([^\"']+)[\"']", html)
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        ERRORS.append("index.html: duplicate IDs: " + ", ".join(duplicates))
    views = set(re.findall(r"\bid=\"view-([^\"]+)\"", html))
    nav_views = set(re.findall(r"data-view=\"([^\"]+)\"", html))
    action_views = set(re.findall(r"data-go=\"([^\"]+)\"", html))
    for name in sorted(nav_views - views):
        ERRORS.append(f"index.html: navigation item has no panel: {name}")
    for name in sorted(action_views - views):
        ERRORS.append(f"index.html: action points to a missing panel: {name}")
    if "downloads" not in nav_views or "downloads" not in views:
        ERRORS.append("index.html: required Download directory navigation or panel is missing")
    for required_id in ("download-search", "download-access-filter", "download-status-filter", "download-family-filter", "download-resource-grid", "download-result-count", "export-download-resources"):
        if required_id not in ids:
            ERRORS.append(f"index.html: required Download directory control is missing: {required_id}")


def main() -> int:
    source_header, source_rows = read_csv(ROOT / "data/source-catalog.csv")
    matrix_header, matrix_rows = read_csv(ROOT / "data/availability-matrix.csv")
    required_source_columns = {"Route ID", "Provider", "Product / API version", "Free-access classification", "Source / documentation URLs"}
    required_matrix_columns = {"Route ID", "Provider", "Asset", "Interval", "Overall coverage status", "Actual raw rows counted locally", "Source URL(s)"}
    for col in sorted(required_source_columns - set(source_header)):
        ERRORS.append(f"data/source-catalog.csv: missing required column {col}")
    for col in sorted(required_matrix_columns - set(matrix_header)):
        ERRORS.append(f"data/availability-matrix.csv: missing required column {col}")

    route_ids = [row.get("Route ID", "").strip() for row in source_rows]
    if len(route_ids) != len(set(route_ids)):
        ERRORS.append("data/source-catalog.csv: duplicate Route ID values")
    source_id_set = set(route_ids)
    if len(source_rows) != EXPECTED_SOURCE_ROUTES:
        ERRORS.append(f"data/source-catalog.csv: expected {EXPECTED_SOURCE_ROUTES} rows, got {len(source_rows)}")
    matrix_route_ids = {row.get("Route ID", "").strip() for row in matrix_rows}
    unknown_routes = sorted(matrix_route_ids - source_id_set)
    if unknown_routes:
        ERRORS.append("availability matrix references unknown source routes: " + ", ".join(unknown_routes))
    if len(matrix_rows) != EXPECTED_COVERAGE_ROWS:
        ERRORS.append(f"data/availability-matrix.csv: expected {EXPECTED_COVERAGE_ROWS} rows, got {len(matrix_rows)}")
    status_counts = Counter(row.get("Overall coverage status", "") for row in matrix_rows)
    if dict(status_counts) != EXPECTED_STATUS_COUNTS:
        ERRORS.append(f"coverage status counts changed: expected {EXPECTED_STATUS_COUNTS}, got {dict(status_counts)}")
    matrix_assets = {row.get("Asset", "").strip().upper() for row in matrix_rows}
    if not matrix_assets.issubset(EXPECTED_ASSETS):
        ERRORS.append("availability matrix contains an out-of-scope asset symbol: " + ", ".join(sorted(matrix_assets - EXPECTED_ASSETS)))

    src_doc = read_json(ROOT / "catalog/sources.json")
    sources = src_doc.get("sources", [])
    src_json_ids = [source.get("source_id") for source in sources]
    if len(src_json_ids) != len(set(src_json_ids)):
        ERRORS.append("catalog/sources.json: duplicate source_id")
    if set(src_json_ids) != source_id_set:
        ERRORS.append("catalog/sources.json route IDs do not match data/source-catalog.csv")
    allowed_source_status = {"qualified_candidate", "conditional", "out_of_scope_or_unverified", "needs_review"}
    for source in sources:
        sid = source.get("source_id", "<missing>")
        if not source.get("name"):
            ERRORS.append(f"{sid}: missing source name")
        if source.get("status") not in allowed_source_status:
            ERRORS.append(f"{sid}: invalid eligibility status {source.get('status')!r}")
        check_url("landing_url", source.get("landing_url", ""), sid)
        check_url("download_url", source.get("download_url", ""), sid)
        if source.get("verification_state") != "research_snapshot_not_live_probe":
            WARNINGS.append(f"{sid}: review verification_state and snapshot provenance")

    download_csv_fields, download_csv_rows = read_csv(ROOT / "catalog/download-resources.csv")
    required_download_fields = {"resource_id", "provider", "resource_name", "access_classification", "source_url", "direct_download_or_index_url", "eligibility_status", "verification_state"}
    for col in sorted(required_download_fields - set(download_csv_fields)):
        ERRORS.append(f"catalog/download-resources.csv: missing required column {col}")
    download_ids = [row.get("resource_id", "").strip() for row in download_csv_rows]
    if len(download_ids) != len(set(download_ids)):
        ERRORS.append("catalog/download-resources.csv: duplicate resource_id")
    if len(download_csv_rows) != 12:
        ERRORS.append(f"catalog/download-resources.csv: expected 12 seed leads, got {len(download_csv_rows)}")
    download_doc = read_json(ROOT / "catalog/download-resources.json")
    download_resources = download_doc.get("resources", [])
    json_resource_ids = [row.get("resource_id") for row in download_resources]
    if len(download_resources) != len(download_csv_rows) or set(json_resource_ids) != set(download_ids):
        ERRORS.append("catalog/download-resources.json IDs/count do not match catalog/download-resources.csv")
    allowed_download_states = {"static_download_candidate", "file_verification_required", "community_archive_candidate", "unverified_public_root", "access_not_verified", "conditional_or_excluded", "complementary_not_pair_candles", "needs_manual_classification"}
    for resource in download_resources:
        rid = resource.get("resource_id", "<missing>")
        if resource.get("eligibility_status") not in allowed_download_states:
            ERRORS.append(f"{rid}: invalid download resource eligibility state {resource.get('eligibility_status')!r}")
        check_url("source_url", resource.get("source_url", ""), rid)
        check_url("direct_download_or_index_url", resource.get("direct_download_or_index_url", ""), rid)
        if resource.get("verification_state") != "seed_research_lead_not_live_download_tested":
            WARNINGS.append(f"{rid}: resource verification state needs review")

    assets_doc = read_json(ROOT / "catalog/assets.json")
    assets = assets_doc.get("assets", [])
    asset_symbols = [item.get("symbol") for item in assets]
    if len(asset_symbols) != len(set(asset_symbols)):
        ERRORS.append("catalog/assets.json: duplicate asset symbol")
    if set(asset_symbols) != EXPECTED_ASSETS:
        ERRORS.append(f"catalog/assets.json asset universe mismatch: {sorted(set(asset_symbols))}")

    interval_doc = read_json(ROOT / "catalog/timeframes.json")
    intervals = interval_doc.get("intervals", [])
    interval_codes = [item.get("code") for item in intervals]
    if len(interval_codes) != len(set(interval_codes)):
        ERRORS.append("catalog/timeframes.json: duplicate interval code")
    if not {"1m", "1M"}.issubset(set(interval_codes)):
        ERRORS.append("catalog/timeframes.json must preserve both 1m and 1M as distinct provider-native tokens")

    coverage_doc = read_json(ROOT / "catalog/coverage.json")
    coverage = coverage_doc.get("rows", [])
    if len(coverage) != len(matrix_rows):
        ERRORS.append(f"catalog/coverage.json: expected {len(matrix_rows)} rows, got {len(coverage)}")
    for idx, row in enumerate(coverage):
        if row.get("source_id") not in source_id_set:
            ERRORS.append(f"catalog/coverage.json row {idx}: unknown source_id {row.get('source_id')!r}")
        if row.get("asset") not in EXPECTED_ASSETS:
            ERRORS.append(f"catalog/coverage.json row {idx}: invalid asset {row.get('asset')!r}")
        count = row.get("published_candle_count")
        basis = row.get("count_basis", "")
        if count is not None and "PUBLISHER_REPORTED" not in basis and "LOCAL_ROW_COUNT" not in basis:
            ERRORS.append(f"coverage row {idx}: count has no qualified provenance")

    inventory_fields, inventory_rows = read_csv(ROOT / "data/local-raw-data-inventory.csv")
    if inventory_rows and "Local files found" in inventory_rows[0]:
        for row in inventory_rows:
            try:
                files = int(row.get("Local files found", "0"))
                rows = int(row.get("Actual candle rows counted", "0"))
            except ValueError:
                continue
            if files == 0 and rows != 0:
                ERRORS.append("local raw data inventory is internally inconsistent")

    bundle_path = ROOT / "web/assets/catalog.js"
    if not bundle_path.is_file():
        ERRORS.append("missing web/assets/catalog.js")
    else:
        text = bundle_path.read_text(encoding="utf-8")
        prefix = "window.CRYPTO_DATA_BANK = "
        if not text.startswith(prefix):
            ERRORS.append("catalog.js does not begin with expected assignment")
        else:
            try:
                payload = json.loads(text[len(prefix):].strip().rstrip(";"))
                if len(payload.get("sources", [])) != len(sources):
                    ERRORS.append("catalog.js source count is out of sync")
                if payload.get("coverage") not in ([], None):
                    ERRORS.append("catalog.js should not embed the heavy coverage grid; it must remain lazy-loaded")
                if payload.get("researchRows") != len(matrix_rows):
                    ERRORS.append("catalog.js researchRows does not match the matrix")
                if len(payload.get("downloadResources", [])) != len(download_resources):
                    ERRORS.append("catalog.js downloadResources count is out of sync")
            except Exception as exc:
                ERRORS.append(f"catalog.js payload invalid: {exc}")

    coverage_bundle_path = ROOT / "web/assets/coverage-data.js"
    if not coverage_bundle_path.is_file():
        ERRORS.append("missing web/assets/coverage-data.js; lazy-loaded coverage data is required")
    else:
        coverage_bundle_text = coverage_bundle_path.read_text(encoding="utf-8")
        coverage_prefix = "window.CRYPTO_COVERAGE_DATA = "
        if not coverage_bundle_text.startswith(coverage_prefix):
            ERRORS.append("coverage-data.js does not begin with the expected assignment")
        else:
            try:
                ui_rows = json.loads(coverage_bundle_text[len(coverage_prefix):].strip().rstrip(";"))
                if len(ui_rows) != len(matrix_rows):
                    ERRORS.append(f"coverage-data.js: expected {len(matrix_rows)} rows, got {len(ui_rows)}")
                if any(row.get("source_id") not in source_id_set for row in ui_rows):
                    ERRORS.append("coverage-data.js contains unknown source IDs")
            except Exception as exc:
                ERRORS.append(f"coverage-data.js payload invalid: {exc}")

    check_local_index_links()
    check_navigation_contract()
    check_english_only()
    print(f"Source routes: {len(source_rows)} | Target assets: {len(assets)} | Interval tokens: {len(intervals)} | Coverage rows: {len(matrix_rows)} | Download leads: {len(download_resources)}")
    print("Coverage status counts:", dict(status_counts))
    print("Matrix routes absent from source matrix expansion:", len(source_id_set - matrix_route_ids), "(not evidence of unavailable data)")
    print("Local raw candle archive rows verified by the supplied research pass: 0")
    if WARNINGS:
        print(f"Warnings: {len(WARNINGS)} (first 5 shown)")
        for warning in WARNINGS[:5]:
            print("WARNING:", warning)
    if ERRORS:
        for error in ERRORS:
            print("ERROR:", error, file=sys.stderr)
        print(f"Validation failed with {len(ERRORS)} error(s).", file=sys.stderr)
        return 1
    print("Catalog validation passed. This validates repository metadata and encoding, not live source availability or archive completeness.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
