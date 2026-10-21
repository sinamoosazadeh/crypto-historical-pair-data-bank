#!/usr/bin/env python3
"""Audit local candle CSV files for row, timestamp, OHLC and cadence anomalies.

No network requests are made. This reports observations, not guarantees of dataset completeness.
A time gap can mean omitted empty bars, no trades, a delisting, or collection failure; the tool
cannot distinguish these without source-specific semantics and independent evidence.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

FIXED_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
HEADER_ALIASES = {
    "timestamp": {"timestamp", "timestamputc", "time", "datetime", "date", "opentime", "open_time", "starttime", "start_time", "ts", "t", "unix", "unixtimestamp", "unix_timestamp"},
    "open": {"open", "o", "openprice", "open_price"},
    "high": {"high", "h", "highprice", "high_price"},
    "low": {"low", "l", "lowprice", "low_price"},
    "close": {"close", "c", "closeprice", "close_price"},
    "volume": {"volume", "vol", "basevolume", "base_volume", "quotevolume", "quote_volume"},
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").strip().lower())


def column_map(fieldnames: list[str] | None) -> dict[str, str]:
    available = {normalized_header(name): name for name in (fieldnames or []) if name}
    result = {}
    for meaning, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            norm = normalized_header(alias)
            if norm in available:
                result[meaning] = available[norm]
                break
    return result


def parse_interval_seconds(token: str | None, custom_seconds: int | None) -> int | None:
    if custom_seconds is not None:
        if custom_seconds <= 0:
            raise ValueError("--interval-seconds must be a positive integer")
        return custom_seconds
    if not token:
        return None
    # Case-sensitive provider labels such as 1M are intentionally not normalized to 1m.
    match = re.fullmatch(r"([1-9]\d*)(s|m|h|d|w)", token)
    if not match:
        raise ValueError(
            f"Interval {token!r} is not a supported fixed interval token. "
            "Use lowercase s/m/h/d/w or provide --interval-seconds only when the source defines a fixed cadence."
        )
    amount, unit = int(match.group(1)), match.group(2)
    return amount * FIXED_UNITS[unit]


def parse_timestamp(value: str, unit: str, naive_timezone: str) -> tuple[datetime | None, str | None, str | None]:
    text = (value or "").strip()
    if not text:
        return None, "EMPTY_TIMESTAMP", None
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", text):
        try:
            numeric = float(text)
            effective_unit = unit
            if effective_unit == "auto":
                magnitude = abs(numeric)
                if magnitude < 1e11:
                    effective_unit = "s"
                elif magnitude < 1e14:
                    effective_unit = "ms"
                elif magnitude < 1e17:
                    effective_unit = "us"
                else:
                    effective_unit = "ns"
            scale = {"s": 1, "ms": 1_000, "us": 1_000_000, "ns": 1_000_000_000}[effective_unit]
            dt = datetime.fromtimestamp(numeric / scale, tz=timezone.utc)
            return dt, None, f"numeric_{effective_unit}" if unit == "auto" else f"numeric_{unit}"
        except (ValueError, OverflowError, OSError):
            return None, "INVALID_NUMERIC_TIMESTAMP", None
    try:
        normalized = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            if naive_timezone != "UTC":
                return None, "NAIVE_DATETIME_REQUIRES_EXPLICIT_UTC_ASSUMPTION", "iso_naive"
            dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc), None, "iso_naive_assumed_utc"
        return dt.astimezone(timezone.utc), None, "iso_with_offset"
    except (ValueError, OverflowError):
        return None, "INVALID_DATETIME_TIMESTAMP", None


def maybe_float(value: str | None) -> float | None:
    try:
        if value is None or not value.strip():
            return None
        result = float(value.strip())
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def audit_stream(stream: TextIO, artifact: Path, member: str | None, artifact_bytes: int, digest: str,
                 interval_seconds: int | None, timestamp_unit: str, naive_timezone: str) -> dict:
    reader = csv.DictReader(stream)
    fields = reader.fieldnames or []
    columns = column_map(fields)
    missing = [key for key in ("timestamp", "open", "high", "low", "close") if key not in columns]
    rows_seen = blank_rows = surplus_rows = malformed_timestamps = naive_timestamps = 0
    invalid_ohlc = invalid_volume = 0
    parsed_times: list[datetime] = []
    time_modes = Counter()
    first_values = []
    previous_in_file: datetime | None = None
    out_of_order_pairs = 0
    for row in reader:
        if row is None or not any(value not in (None, "") for value in row.values()):
            blank_rows += 1
            continue
        rows_seen += 1
        if None in row:
            surplus_rows += 1
        if "timestamp" in columns:
            dt, error, mode = parse_timestamp(row.get(columns["timestamp"], ""), timestamp_unit, naive_timezone)
            if error:
                malformed_timestamps += 1
                if error.startswith("NAIVE_DATETIME"):
                    naive_timestamps += 1
            elif dt is not None:
                parsed_times.append(dt)
                time_modes[mode or "unknown"] += 1
                if previous_in_file is not None and dt < previous_in_file:
                    out_of_order_pairs += 1
                previous_in_file = dt
                if len(first_values) < 1:
                    first_values.append(dt)
        if all(key in columns for key in ("open", "high", "low", "close")):
            o = maybe_float(row.get(columns["open"]))
            h = maybe_float(row.get(columns["high"]))
            lo = maybe_float(row.get(columns["low"]))
            c = maybe_float(row.get(columns["close"]))
            if None in (o, h, lo, c) or h < max(o, c, lo) or lo > min(o, c, h):
                invalid_ohlc += 1
        if "volume" in columns:
            v = maybe_float(row.get(columns["volume"]))
            if v is None or v < 0:
                invalid_volume += 1

    counts = Counter(parsed_times)
    duplicate_rows = sum(n - 1 for n in counts.values() if n > 1)
    unique_sorted = sorted(counts)
    observed_gaps = aligned_missing_candidates = unaligned_deltas = 0
    max_gap_seconds = None
    if interval_seconds and len(unique_sorted) > 1:
        deltas = [(unique_sorted[i] - unique_sorted[i-1]).total_seconds() for i in range(1, len(unique_sorted))]
        positive = [d for d in deltas if d > 0]
        if positive:
            max_gap_seconds = max(positive)
        for delta in positive:
            if delta > interval_seconds:
                observed_gaps += 1
                ratio = delta / interval_seconds
                nearest = round(ratio)
                if nearest >= 2 and abs(ratio - nearest) < 1e-8:
                    aligned_missing_candidates += nearest - 1
                else:
                    unaligned_deltas += 1

    return {
        "artifact_path": str(artifact),
        "archive_member": member,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "bytes_on_disk": artifact_bytes,
        "sha256_on_disk": digest,
        "csv_header": fields,
        "mapped_columns": columns,
        "missing_required_columns": missing,
        "timestamp_unit_argument": timestamp_unit,
        "timestamp_parse_modes": dict(time_modes),
        "rows_observed_excluding_header": rows_seen,
        "blank_rows_skipped": blank_rows,
        "rows_with_extra_fields": surplus_rows,
        "timestamp_parse_errors_or_rejected_values": malformed_timestamps,
        "naive_timestamps_rejected_without_explicit_utc_assumption": naive_timestamps,
        "first_timestamp_utc": min(parsed_times).isoformat().replace("+00:00", "Z") if parsed_times else None,
        "last_timestamp_utc": max(parsed_times).isoformat().replace("+00:00", "Z") if parsed_times else None,
        "unique_timestamp_count": len(counts),
        "duplicate_timestamp_rows": duplicate_rows,
        "out_of_order_timestamp_pairs_in_file_order": out_of_order_pairs,
        "invalid_ohlc_rows": invalid_ohlc if all(key in columns for key in ("open", "high", "low", "close")) else None,
        "invalid_or_negative_volume_rows": invalid_volume if "volume" in columns else None,
        "interval_seconds_for_gap_check": interval_seconds,
        "observed_timestamp_gaps_over_interval": observed_gaps,
        "aligned_missing_bucket_candidates": aligned_missing_candidates,
        "unaligned_long_deltas": unaligned_deltas,
        "max_observed_delta_seconds": max_gap_seconds,
        "limitations": [
            "Physical CSV records are not proof of full-history completeness.",
            "Time gaps are candidates only; an exchange may omit empty/no-trade candles.",
            "Source-specific timestamp units, candle anchors and bar inclusion policies must be verified.",
            "A local checksum identifies the inspected artifact but does not prove source authenticity.",
        ],
    }


def discover(inputs: list[str]) -> list[Path]:
    found: list[Path] = []
    supported = {".csv", ".zip"}
    for raw in inputs:
        path = Path(raw)
        if path.is_file():
            if path.suffix.lower() == ".csv" or path.suffix.lower() == ".zip" or "".join(path.suffixes).lower().endswith(".csv.gz"):
                found.append(path)
            else:
                raise ValueError(f"Unsupported file type: {path}; expected CSV, CSV.GZ, or ZIP")
        elif path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and (candidate.suffix.lower() == ".csv" or candidate.suffix.lower() == ".zip" or "".join(candidate.suffixes).lower().endswith(".csv.gz")):
                    found.append(candidate)
        else:
            raise FileNotFoundError(path)
    return sorted(set(found))


def audit_file(path: Path, interval_seconds: int | None, timestamp_unit: str, naive_timezone: str) -> list[dict]:
    digest = sha256_file(path)
    size = path.stat().st_size
    suffixes = "".join(path.suffixes).lower()
    if suffixes.endswith(".csv.gz"):
        with gzip.open(path, "rt", encoding="utf-8-sig", errors="replace", newline="") as stream:
            return [audit_stream(stream, path, None, size, digest, interval_seconds, timestamp_unit, naive_timezone)]
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as stream:
            return [audit_stream(stream, path, None, size, digest, interval_seconds, timestamp_unit, naive_timezone)]
    results = []
    with zipfile.ZipFile(path) as archive:
        members = [m for m in archive.infolist() if not m.is_dir() and m.filename.lower().endswith(".csv")]
        if not members:
            raise ValueError(f"{path}: ZIP contains no CSV members")
        for member in members:
            with archive.open(member, "r") as raw:
                stream = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
                results.append(audit_stream(stream, path, member.filename, size, digest, interval_seconds, timestamp_unit, naive_timezone))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="CSV, CSV.GZ, ZIP files or directories")
    parser.add_argument("--interval", help="Known fixed interval token such as 1m, 5m, 1h, 1d; do not use case-ambiguous month tokens")
    parser.add_argument("--interval-seconds", type=int, help="Source-confirmed fixed cadence in seconds, for nonstandard labels")
    parser.add_argument("--timestamp-unit", choices=["auto", "s", "ms", "us", "ns"], default="auto")
    parser.add_argument("--naive-timezone", choices=["reject", "UTC"], default="reject", help="Whether timestamps lacking timezone offsets may be assumed to be UTC")
    parser.add_argument("--output", default="ohlcv_audit.jsonl", help="JSONL output path")
    args = parser.parse_args()
    try:
        interval_seconds = parse_interval_seconds(args.interval, args.interval_seconds)
        files = discover(args.paths)
        if not files:
            parser.error("No supported files found")
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))

    reports = []
    errors = []
    for path in files:
        try:
            reports.extend(audit_file(path, interval_seconds, args.timestamp_unit, args.naive_timezone))
        except (OSError, ValueError, zipfile.BadZipFile, EOFError) as exc:
            errors.append({"path": str(path), "error": str(exc)})
    output = Path(args.output)
    output.write_text("".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in reports), encoding="utf-8")
    print(f"Artifacts inspected: {len(files)} | CSV datasets audited: {len(reports)} | errors: {len(errors)}")
    print(f"Report written: {output} ({output.stat().st_size} bytes)")
    for report in reports:
        print(f"- {report['artifact_path']}" + (f"::{report['archive_member']}" if report['archive_member'] else "") + f": {report['rows_observed_excluding_header']} rows; {report['duplicate_timestamp_rows']} duplicate timestamp rows; {report['invalid_ohlc_rows']} invalid OHLC rows")
    for error in errors:
        print("ERROR: " + json.dumps(error, ensure_ascii=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
