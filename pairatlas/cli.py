"""Network-free discovery CLI. All counts describe the dated research snapshot."""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from functools import lru_cache
from importlib import resources
from pathlib import Path

from . import __version__


def catalog_root():
    checkout = Path(__file__).resolve().parents[1] / "catalog"
    return checkout if checkout.is_dir() else resources.files("pairatlas").joinpath("catalog")


@lru_cache(maxsize=8)
def load(name: str):
    return json.loads(catalog_root().joinpath(name + ".json").read_text(encoding="utf-8"))


def records(name: str, key: str) -> list[dict]:
    return load(name)[key]


def matches(row: dict, query: str) -> bool:
    text = " ".join(str(v) for v in row.values() if isinstance(v, (str, int, float))).lower()
    return all(term in text for term in query.lower().split())


def emit(rows: list[dict], format_name: str) -> None:
    if format_name == "json":
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    if not rows:
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        # Spreadsheet formula injection protection applies to CSV only, never JSON.
        safe = {}
        for key, value in row.items():
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                value = "'" + value
            safe[key] = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
        writer.writerow(safe)
    print(out.getvalue(), end="")


def add_output(parser):
    parser.add_argument("--format", choices=["table", "json", "csv"], default="table")
    parser.add_argument("--limit", type=int, default=20, help="Maximum rows; 0 means no limit")


def selected(rows, args):
    return rows if args.limit == 0 else rows[:args.limit]


def table(rows, columns):
    if not rows:
        print("No matching records. Unknown coverage is not evidence of unavailable data.")
        return
    widths = {c: min(52, max(len(c), *(len(str(r.get(c, ""))) for r in rows))) for c in columns}
    print("  ".join(c.ljust(widths[c]) for c in columns))
    print("  ".join("-" * widths[c] for c in columns))
    for row in rows:
        print("  ".join(str(row.get(c, ""))[:widths[c]].ljust(widths[c]) for c in columns))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pairatlas", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("stats", help="Show inventory counts and evidence limitations")
    find = sub.add_parser("find", help="Search source x asset x interval evidence")
    find.add_argument("query", nargs="?", default="")
    find.add_argument("--asset"); find.add_argument("--interval", help="Case-sensitive native token")
    find.add_argument("--source", help="Exact source route ID")
    find.add_argument("--status", choices=["VERIFIED", "NOT_CHECKED", "NOT_APPLICABLE"])
    add_output(find)
    sources = sub.add_parser("sources", help="Search provider routes")
    sources.add_argument("query", nargs="?", default=""); add_output(sources)
    downloads = sub.add_parser("downloads", help="Browse supplemental static-download leads")
    downloads.add_argument("query", nargs="?", default=""); add_output(downloads)
    show = sub.add_parser("show", help="Show one complete source record")
    show.add_argument("source_id")
    audit = sub.add_parser("audit", help="Audit a local CSV / CSV.GZ / ZIP; no network")
    audit.add_argument("paths", nargs="+"); audit.add_argument("--interval")
    audit.add_argument("--timestamp-unit", choices=["auto", "s", "ms", "us", "ns"], default="auto")
    audit.add_argument("--naive-timezone", choices=["reject", "UTC"], default="reject")
    audit.add_argument("--output", default="ohlcv_audit.jsonl")
    serve = sub.add_parser("serve", help="Serve the repository website locally")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args(argv)
    if hasattr(args, "limit") and args.limit < 0:
        parser.error("--limit must be nonnegative")
    try:
        if args.command == "stats":
            from collections import Counter
            coverage = records("coverage", "rows")
            summary = {"snapshot_date": load("sources")["snapshot_date"], "source_routes": len(records("sources", "sources")), "target_assets": len(records("assets", "assets")), "coverage_records": len(coverage), "status_counts": dict(Counter(r["status"] for r in coverage)), "download_leads": len(records("download-resources", "resources")), "raw_candle_archives_counted_in_seed_research": 0, "note": "Research metadata only. VERIFIED does not mean a complete archive was downloaded or counted."}
            print(json.dumps(summary, indent=2))
        elif args.command in {"find", "sources", "downloads"}:
            name, key = {"find": ("coverage", "rows"), "sources": ("sources", "sources"), "downloads": ("download-resources", "resources")}[args.command]
            rows = [r for r in records(name, key) if matches(r, args.query)]
            if args.command == "find":
                for field in ["asset", "interval", "source", "status"]:
                    value = getattr(args, field)
                    if value:
                        field = "source_id" if field == "source" else field
                        rows = [r for r in rows if r.get(field) == value]
                total = len(rows); rows = selected(rows, args)
                if args.format == "table":
                    table(rows, ["source_id", "asset", "interval", "status", "count_basis"])
                    print(f"\n{len(rows)} shown / {total} matches. Snapshot only; VERIFIED is not a full-archive count.")
                else:
                    emit(rows, args.format)
            else:
                rows = selected(rows, args)
                if args.format == "table":
                    table(rows, ["source_id" if args.command == "sources" else "resource_id", "name" if args.command == "sources" else "resource_name", "status" if args.command == "sources" else "eligibility_status"])
                else:
                    emit(rows, args.format)
        elif args.command == "show":
            row = next((r for r in records("sources", "sources") if r["source_id"] == args.source_id), None)
            if row is None:
                parser.error("Unknown source ID. Use: pairatlas sources --limit 0")
            print(json.dumps(row, indent=2, ensure_ascii=False))
        elif args.command == "audit":
            from pairatlas.audit import audit_file, discover, parse_interval_seconds
            cadence = parse_interval_seconds(args.interval, None)
            paths = discover(args.paths)
            if not paths:
                parser.error("No CSV, CSV.GZ or ZIP files found")
            reports = []
            for path in paths:
                reports.extend(audit_file(path, cadence, args.timestamp_unit, args.naive_timezone))
            Path(args.output).write_text("".join(json.dumps(r) + "\n" for r in reports), encoding="utf-8")
            print(f"Audited {len(reports)} datasets. Report: {args.output}")
        elif args.command == "serve":
            from .server import serve
            serve(Path(__file__).resolve().parents[1], args.host, args.port, "PairAtlas")
    except (OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
