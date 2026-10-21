#!/usr/bin/env python3
"""Build canonical UI metadata from the immutable, English research snapshot CSVs."""
from __future__ import annotations
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CATALOG = ROOT / "catalog"
SNAPSHOT_DATE = "2026-10-21"
URL_RE = re.compile(r"https?://[^\s<>\]\[()\"']+")
ASSETS = [
    ("BTC", "Bitcoin"), ("ETH", "Ethereum"), ("SOL", "Solana"),
    ("BNB", "BNB"), ("DOGE", "Dogecoin"), ("LTC", "Litecoin"),
    ("XRP", "XRP"), ("TRX", "TRON"), ("BCH", "Bitcoin Cash"),
    ("AVAX", "Avalanche"), ("DASH", "Dash"), ("SUI", "Sui"),
    ("ARB", "Arbitrum"), ("ADA", "Cardano"),
]
INTERVAL_LABELS = {
    "1s": "1 second", "10s": "10 seconds", "1m": "1 minute",
    "3m": "3 minutes", "5m": "5 minutes", "10m": "10 minutes",
    "15m": "15 minutes", "30m": "30 minutes", "1h": "1 hour",
    "2h": "2 hours", "3h": "3 hours", "4h": "4 hours",
    "6h": "6 hours", "8h": "8 hours", "12h": "12 hours",
    "24h": "24-hour native interval", "1d": "1 day", "2d": "2 days",
    "3d": "3 days", "7d": "7 days", "14d": "14 days",
    "15d": "15 days", "30d": "30 days", "1w": "1 week",
    "1y": "1 year", "1mo": "1 calendar month (native label)",
    "1mon": "1 calendar month (native label)",
    "1M": "Provider-native token; case-sensitive semantics must be confirmed",
    "3M": "Provider-native token; case-sensitive semantics must be confirmed",
    "1MM": "Unresolved provider-native token; do not normalize",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: normalize_csv_value(row.get(field, "")) for field in fields})


def normalize_csv_value(value):
    if isinstance(value, (list, tuple)):
        return "; ".join(str(x) for x in value)
    if value is None:
        return ""
    if isinstance(value, (dict, bool, int, float)):
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    return str(value).replace("\r\n", "\n").replace("\r", "\n")


def first_url(value: str) -> str:
    for candidate in URL_RE.findall(value or ""):
        candidate = candidate.rstrip(".,;:!?}")
        parsed = urlparse(candidate)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return candidate
    return ""


def all_urls(value: str) -> list[str]:
    out = []
    for candidate in URL_RE.findall(value or ""):
        candidate = candidate.rstrip(".,;:!?}")
        parsed = urlparse(candidate)
        if parsed.scheme in ("http", "https") and parsed.netloc and candidate not in out:
            out.append(candidate)
    return out


def list_levels(row: dict[str, str]) -> list[str]:
    text = " ".join(row.get(k, "") for k in (
        "Product / API version", "Source class", "Volume semantics / candle schema",
        "Access mode / endpoint or official route guide"
    )).lower()
    levels = []
    if any(term in text for term in ("ohlc", "candle", "kline", "candlestick", "bar data")):
        levels.append("Level 1 - OHLC / OHLCV")
    if any(term in text for term in ("trade", "tick", "order book", "order-book", "orderbook", "depth")):
        levels.append("Level 2 - Trades / ticks / order book")
    if any(term in text for term in ("funding", "open interest", "liquidation", "mark price", "index price", "basis", "derivative metric")):
        levels.append("Level 3 - Derived / derivatives metrics")
    return levels or ["Data level not determined from snapshot fields"]


def list_families(row: dict[str, str]) -> list[str]:
    text = " ".join(row.get(k, "") for k in (
        "Product / API version", "Source class", "Volume semantics / candle schema"
    )).lower()
    out = []
    checks = [
        ("OHLC / OHLCV candles", ("ohlc", "kline", "candle", "candlestick")),
        ("Trades / ticks", ("trade", "tick", "time and sales")),
        ("Order book / depth", ("order book", "order-book", "orderbook", "depth", "l2")),
        ("Funding / derivatives metrics", ("funding", "open interest", "liquidation", "perpetual", "futures", "derivative")),
        ("Aggregated / reference market metrics", ("aggregate", "index", "reference", "ticker", "24h")),
    ]
    for label, terms in checks:
        if any(term in text for term in terms):
            out.append(label)
    return out or ["Historical market data (family requires review)"]


def source_status(row: dict[str, str]) -> tuple[str, str]:
    access = (row.get("Free-access classification") or "").upper()
    source_class = (row.get("Source class") or "").lower()
    operational = (row.get("Operational status") or "").upper()
    direct_static = any(term in source_class for term in (
        "bulk", "archive", "download", "prebuilt", "repository", "third-party exchange-resolved",
        "public dataset", "static file", "file download", "public data"
    ))
    api_only = ("api" in source_class and not direct_static) or "api/freemium" in source_class
    if access == "FREE_PUBLIC" and direct_static and not api_only:
        explanation = "Public-file candidate: static archive or download is described, but exact pair coverage, anonymous access and full file counts still require artifact-level verification."
        return "qualified_candidate", explanation
    if access == "FREE_PUBLIC" and api_only:
        explanation = "Listed for completeness, but an API-only route is outside the strict static-download workflow; do not treat it as an eligible no-API archive."
        return "out_of_scope_or_unverified", explanation
    if "PAID" in access or "RETIRED" in access or access in {"RETIRED", "NOT_FREE", "OUT_OF_SCOPE"}:
        explanation = "The source snapshot describes paid, retired or otherwise ineligible access; retained for historical comparison, not as a qualifying free download."
        return "out_of_scope_or_unverified", explanation
    if access.startswith("UNVERIFIED") or "UNVERIFIED" in access or "UNCONFIRMED" in access or "HISTORICAL_ACCESS_UNVERIFIED" in access:
        return "needs_review", "Free access or current availability is unverified in the source snapshot; require a dated direct-download test."
    return "conditional", "Access classification is conditional, product-specific, historical or insufficiently confirmed; inspect terms and the exact file path."


def main() -> None:
    source_rows = read_csv(DATA / "source-catalog.csv")
    matrix_rows = read_csv(DATA / "availability-matrix.csv")
    asset_rows = read_csv(DATA / "target-assets.csv")
    count_rows = read_csv(DATA / "publisher-reported-counts.csv")
    download_resource_rows = read_csv(DATA / "public-download-resources.csv")
    source_ids = [row.get("Route ID", "").strip() for row in source_rows]
    if len(source_ids) != len(set(source_ids)):
        raise SystemExit("Source catalog has duplicate Route ID values; resolve before building the UI catalog.")
    if not source_rows or not matrix_rows:
        raise SystemExit("Source catalog or availability matrix is empty.")

    sources = []
    for row in source_rows:
        status, status_note = source_status(row)
        urls = all_urls(row.get("Source / documentation URLs", ""))
        access_urls = all_urls(row.get("Access mode / endpoint or official route guide", ""))
        url = first_url(row.get("Source / documentation URLs", ""))
        download_url = access_urls[0] if access_urls else ""
        access_summary = row.get("Access mode / endpoint or official route guide", "")
        eligibility = f"{row.get('Free-access classification','')}: {row.get('Free-access conditions and request cap','')} {status_note}".strip()
        evidence_note = " | ".join(part for part in [
            f"Operational status: {row.get('Operational status','')}",
            f"Evidence level: {row.get('Evidence level','')}",
            f"14-asset summary: {row.get('14-asset coverage summary','')}",
            f"Audit notes: {row.get('Audit notes','')}",
        ] if part and not part.endswith(": "))
        source = {
            "source_id": row.get("Route ID", "").strip(),
            "name": f"{row.get('Provider','').strip()} - {row.get('Product / API version','').strip()}".strip(" -"),
            "provider": row.get("Provider", ""),
            "source_class": row.get("Source class", ""),
            "status": status,
            "market_scope": row.get("Market type", ""),
            "quote_settlement": row.get("Quote / settlement", ""),
            "data_families": list_families(row),
            "data_levels": list_levels(row),
            "timeframes_note": row.get("Native intervals documented", ""),
            "intervals_in_free_tier_matrix": row.get("Intervals included in free-tier matrix", ""),
            "interval_evidence_status": row.get("Interval evidence status", ""),
            "schema_format": row.get("Volume semantics / candle schema", ""),
            "access_mechanism": access_summary,
            "landing_url": url,
            "download_url": download_url,
            "all_source_urls": urls,
            "snapshot_date": SNAPSHOT_DATE,
            "last_reviewed": SNAPSHOT_DATE,
            "verification_state": "research_snapshot_not_live_probe",
            "evidence_level": row.get("Evidence level", ""),
            "confidence": ("Official documentation recorded" if "OFFICIAL" in row.get("Evidence level", "").upper() else "Research snapshot; not counted locally"),
            "eligibility_note": eligibility,
            "coverage_evidence_and_limits": evidence_note,
            "free_access_classification": row.get("Free-access classification", ""),
            "operational_status": row.get("Operational status", ""),
            "documented_history": row.get("Documented history / retention", ""),
            "publisher_reported_totals": row.get("Publisher-reported dataset totals (not local counts)", ""),
            "local_rows_counted": row.get("Actual raw rows counted locally", ""),
        }
        sources.append(source)

    asset_name = dict(ASSETS)
    assets = []
    for symbol, name in ASSETS:
        original = next((r for r in asset_rows if (r.get("Asset") or "").strip().upper() == symbol), {})
        assets.append({
            "asset_id": symbol.lower(), "symbol": symbol, "name": name,
            "aliases": [symbol], "notes": original.get("Scope note", "Instrument availability is exchange- and market-specific."),
            "verification_state": "target_asset_scope_only_not_universal_listing_confirmation",
        })

    interval_counts = Counter((row.get("Interval") or "").strip() for row in matrix_rows)
    interval_codes = sorted(code for code in interval_counts if code and code != "UNRESOLVED")
    intervals = []
    for code in interval_codes:
        label = INTERVAL_LABELS.get(code, "Provider-native label; verify exact semantics before normalization")
        if code in {"1M", "3M", "1MM"}:
            kind = "provider_native_case_sensitive"
        elif code.lower().endswith(("mo", "mon", "mth")):
            kind = "calendar"
        elif code.lower().endswith(("s", "m", "h")):
            kind = "fixed_or_provider_native"
        elif code.lower().endswith(("d", "w", "y")):
            kind = "calendar_or_provider_native"
        else:
            kind = "provider_native_unresolved"
        nominal_seconds = None
        if kind == "fixed_or_provider_native":
            unit = code[-1].lower()
            try:
                amount = int(code[:-1])
            except ValueError:
                amount = 0
            seconds_per_unit = {"s": 1, "m": 60, "h": 3600}.get(unit)
            if amount > 0 and seconds_per_unit is not None:
                nominal_seconds = amount * seconds_per_unit
        elif code == "24h":
            nominal_seconds = 24 * 60 * 60
        intervals.append({"code": code, "label": label, "interval_kind": kind,
                          "nominal_seconds": nominal_seconds,
                          "matrix_rows": interval_counts[code], "provider_specific_semantics": True})

    publisher_map = {}
    for row in count_rows:
        try:
            n = int(str(row.get("Publisher-displayed records", "")).replace(",", ""))
        except (ValueError, TypeError):
            n = None
        key = (row.get("Provider", "").strip().lower(), row.get("Asset", "").strip().upper(),
               row.get("Interval", "").strip())
        if n is not None:
            publisher_map[key] = {"count": n, "basis": "PUBLISHER_REPORTED_NOT_INDEPENDENTLY_COUNTED",
                                  "source_url": row.get("Source URL", ""), "caveat": row.get("Caveat", "")}

    coverage = []
    for row in matrix_rows:
        route = row.get("Route ID", "").strip()
        provider = row.get("Provider", "").strip()
        asset = row.get("Asset", "").strip().upper()
        interval = row.get("Interval", "").strip()
        raw_count = (row.get("Actual raw rows counted locally") or "").strip()
        count = None
        count_basis = row.get("Count status", "NOT_MEASURED") or "NOT_MEASURED"
        try:
            parsed = int(raw_count.replace(",", ""))
            if parsed >= 0 and row.get("Count status", "").upper() not in {"NOT_MEASURED", "NOT_APPLICABLE"}:
                count = parsed
                count_basis = "LOCAL_ROW_COUNT_RECORDED_IN_SOURCE_SNAPSHOT"
        except ValueError:
            pass
        pub = publisher_map.get((provider.lower(), asset, interval))
        if pub:
            count = pub["count"]
            count_basis = pub["basis"]
        status = row.get("Overall coverage status", "NOT_CHECKED").strip() or "NOT_CHECKED"
        if pub:
            evidence_summary = "Publisher-displayed count only; the source artifact was not downloaded and the count was not independently reproduced. See the full matrix and publisher count register."
        elif status == "VERIFIED":
            evidence_summary = f"Seed status is VERIFIED (pair: {row.get('Asset-pair status','')}; interval: {row.get('Interval status','')}); actual rows remain {row.get('Count status','NOT_MEASURED')}. This is not a full-history verification. See the full matrix for the recorded evidence basis."
        elif status == "NOT_APPLICABLE":
            evidence_summary = "Marked not applicable in the seed research matrix; inspect the detailed record before generalizing beyond the specific product scope."
        else:
            evidence_summary = "This combination was not checked to the required standard in the seed research. Unknown does not mean unavailable. See the full matrix for source notes and access conditions."
        coverage.append({
            "source_id": route, "provider": provider, "product_endpoint": row.get("Product / endpoint", ""),
            "market_type": row.get("Market type", ""), "asset": asset,
            "candidate_symbol": row.get("Symbol / pair (confirmed only when noted)", ""),
            "quote_settlement": row.get("Quote / settlement / pool denomination", ""),
            "interval": interval, "interval_label": INTERVAL_LABELS.get(interval, ""),
            "status": status, "asset_pair_status": row.get("Asset-pair status", ""),
            "interval_status": row.get("Interval status", ""),
            "published_candle_count": count, "count_basis": count_basis,
            "first_open_utc": row.get("First open UTC (if measured/observed)", ""),
            "last_open_or_theoretical_boundary": row.get("Last open / boundary (theoretical for Binance; not actual)", ""),
            "theoretical_slots_not_actual": row.get("Theoretical slots (not actual rows)", ""),
            "per_request_cap": row.get("Per-request cap", ""),
            "history_statement": row.get("History / retention statement", ""),
            "free_access_condition": row.get("Free-access condition", ""),
            "source_urls": row.get("Source URL(s)", ""),
            "evidence_or_limitation": evidence_summary,
        })

    eligibility_map = {
        "STATIC_PUBLIC_DOWNLOAD_CANDIDATE": "static_download_candidate",
        "FREE_PUBLIC_FILE_CANDIDATE_VERIFY_PER_FILE": "file_verification_required",
        "PUBLIC_GITHUB_DATASET_CANDIDATE": "community_archive_candidate",
        "PUBLIC_GITHUB_ARCHIVE_CANDIDATE": "community_archive_candidate",
        "UNVERIFIED_PUBLIC_ROOT_CANDIDATE": "unverified_public_root",
        "FREE_CLAIM_DIRECT_FILE_NOT_VERIFIED": "access_not_verified",
        "CONDITIONAL_ACCESS_NOT_ANONYMOUSLY_VERIFIED": "conditional_or_excluded",
        "CONDITIONAL_REQUESTER_PAYS_OR_ENDPOINT_SPECIFIC": "conditional_or_excluded",
        "COMPLEMENTARY_NOT_CANDLE_SUBSTITUTE": "complementary_not_pair_candles",
        "EXCLUDED_UNTIL_ACCESS_TERMS_CONFIRMED": "conditional_or_excluded",
    }
    resource_fields = [
        "resource_id", "provider", "resource_name", "data_family", "market_scope",
        "access_classification", "intervals_or_granularity", "source_url",
        "direct_download_or_index_url", "reported_coverage", "evidence_state",
        "license_or_terms", "known_limitations", "next_verification_step",
    ]
    download_resources = []
    seen_resource_ids = set()
    for row in download_resource_rows:
        rid = (row.get("resource_id") or "").strip()
        if not rid or rid in seen_resource_ids:
            raise SystemExit(f"Download resource registry has a missing or duplicate resource_id: {rid!r}")
        seen_resource_ids.add(rid)
        item = {key: (row.get(key) or "").strip() for key in resource_fields}
        item["eligibility_status"] = eligibility_map.get(item["access_classification"], "needs_manual_classification")
        item["verification_state"] = "seed_research_lead_not_live_download_tested"
        item["snapshot_date"] = SNAPSHOT_DATE
        download_resources.append(item)

    CATALOG.mkdir(exist_ok=True)
    (CATALOG / "sources.json").write_text(json.dumps({"schema_version": "2.0.0", "snapshot_date": SNAPSHOT_DATE,
        "snapshot_only": True, "source_count": len(sources), "sources": sources}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (CATALOG / "assets.json").write_text(json.dumps({"schema_version": "2.0.0", "assets": assets}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (CATALOG / "timeframes.json").write_text(json.dumps({"schema_version": "2.0.0", "snapshot_note": "Observed interval tokens from the snapshot, not a universal provider support list. Preserve case and provider semantics.", "intervals": intervals}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (CATALOG / "download-resources.json").write_text(json.dumps({
        "schema_version": "1.0.0", "snapshot_date": SNAPSHOT_DATE,
        "snapshot_only": True, "resource_count": len(download_resources),
        "note": "Static-download discovery leads; not all entries are proven anonymous, direct, complete, or free at artifact level.",
        "resources": download_resources,
    }, ensure_ascii=True, separators=(",", ":")) + "\n", encoding="utf-8")
    write_csv(CATALOG / "download-resources.csv", download_resources,
              resource_fields + ["eligibility_status", "verification_state", "snapshot_date"])
    # The detailed CSV remains the full row-level export. The JSON is a compact, stable
    # discovery API so the web UI does not duplicate long source notes and source URLs 10k times.
    compact_coverage_fields = [
        "source_id", "provider", "product_endpoint", "market_type", "asset", "candidate_symbol",
        "quote_settlement", "interval", "interval_label", "status", "asset_pair_status",
        "interval_status", "published_candle_count", "count_basis", "first_open_utc",
        "last_open_or_theoretical_boundary", "theoretical_slots_not_actual", "per_request_cap",
        "history_statement", "free_access_condition", "evidence_summary",
    ]
    compact_coverage = [{key: row.get(key) for key in compact_coverage_fields} for row in coverage]
    (CATALOG / "coverage.json").write_text(json.dumps({"schema_version": "2.1.0", "generated_at": SNAPSHOT_DATE + "T00:00:00Z", "snapshot_only": True,
        "detail_csv": "coverage.csv", "source_matrix_csv": "../data/availability-matrix.csv",
        "row_count": len(compact_coverage), "rows": compact_coverage}, ensure_ascii=True, separators=(",", ":")) + "\n", encoding="utf-8")

    source_export = []
    source_fields = ["source_id", "name", "provider", "source_class", "status", "market_scope", "quote_settlement",
        "data_families", "data_levels", "timeframes_note", "schema_format", "access_mechanism", "landing_url",
        "download_url", "free_access_classification", "operational_status", "verification_state", "last_reviewed",
        "eligibility_note", "coverage_evidence_and_limits"]
    for s in sources: source_export.append(s)
    write_csv(CATALOG / "sources.csv", source_export, source_fields)
    coverage_fields = ["source_id", "provider", "product_endpoint", "market_type", "asset", "candidate_symbol",
        "quote_settlement", "interval", "interval_label", "status", "asset_pair_status", "interval_status",
        "published_candle_count", "count_basis", "first_open_utc", "last_open_or_theoretical_boundary",
        "theoretical_slots_not_actual", "per_request_cap", "history_statement", "free_access_condition",
        "source_urls", "evidence_summary", "evidence_or_limitation"]
    write_csv(CATALOG / "coverage.csv", coverage, coverage_fields)

    # Keep the browser bundle lean. Full notes stay in source registry and CSV exports.
    ui_coverage_fields = [
        "source_id", "provider", "market_type", "asset", "candidate_symbol", "quote_settlement",
        "interval", "interval_label", "status", "asset_pair_status", "interval_status",
        "published_candle_count", "count_basis", "evidence_summary",
    ]
    ui_coverage = [{key: row.get(key) for key in ui_coverage_fields} for row in coverage]
    payload = {
        "generatedAt": SNAPSHOT_DATE,
        "snapshotLabel": "Research snapshot; not a live, full-history audit",
        "sources": sources, "assets": assets, "timeframes": intervals, "coverage": [],
        "downloadResources": download_resources,
        "researchRows": len(coverage),
        "snapshotSummary": {
            "sourceRoutes": len(sources), "targetAssets": len(assets), "coverageRows": len(coverage),
            "intervalTokens": len(intervals), "downloadResources": len(download_resources),
            "coverageStatusCounts": dict(Counter(r["status"] for r in coverage)),
            "countStatusCounts": dict(Counter(r.get("count_basis", "") for r in coverage)),
            "rawCandleFilesDownloadedAndCounted": 0,
        },
    }
    # Load the heavy 10k-row coverage bundle only when a visitor opens the coverage explorer.
    # This keeps the landing page responsive on mobile networks and lower-memory devices.
    (ROOT / "web/assets/catalog.js").write_text("window.CRYPTO_DATA_BANK = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    (ROOT / "web/assets/coverage-data.js").write_text(
        "window.CRYPTO_COVERAGE_DATA = " + json.dumps(ui_coverage, ensure_ascii=True, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    write_csv(DATA / "interval-reference.csv", intervals,
              ["code", "label", "interval_kind", "nominal_seconds", "matrix_rows", "provider_specific_semantics"])
    summary = {
        "project": "Crypto Historical Pair Data Bank", "snapshot_date": SNAPSHOT_DATE,
        "source_routes": len(sources), "target_assets": len(assets), "coverage_records": len(coverage),
        "public_download_resource_leads": len(download_resources),
        "distinct_matrix_interval_tokens": len(interval_counts),
        "matrix_intervals_including_unresolved": sorted(interval_counts),
        "coverage_status_counts": dict(Counter(r["Overall coverage status"] for r in matrix_rows)),
        "asset_pair_status_counts": dict(Counter(r["Asset-pair status"] for r in matrix_rows)),
        "interval_status_counts": dict(Counter(r["Interval status"] for r in matrix_rows)),
        "count_status_counts": dict(Counter(r["Count status"] for r in matrix_rows)),
        "raw_historical_files_downloaded_and_counted_in_input_research": 0,
        "counts_note": "Published totals remain publisher claims unless a specific local artifact and row-count method are recorded.",
        "limitations": [
            "VERIFIED is inherited from the research matrix and may mean a limited sample or documented capability; it does not mean the full archive was downloaded or counted.",
            "A NOT_CHECKED row is unknown, not negative evidence.",
            "Theoretical calendar slots are not actual candle rows.",
            "The source registry has more routes than the matrix expands; missing route rows are not proof of no data.",
        ],
    }
    (DATA / "snapshot-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Built catalog: {len(sources)} source routes | {len(assets)} assets | {len(coverage)} coverage records | {len(intervals)} interval tokens | {len(download_resources)} download leads")
    print("Coverage status:", dict(Counter(r["Overall coverage status"] for r in matrix_rows)))
    print("Raw historical files downloaded and counted in seed research: 0")

if __name__ == "__main__":
    main()
