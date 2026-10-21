#!/usr/bin/env python3
"""Count physical candle rows in local CSV, CSV.GZ, or ZIP archives.

This is deliberately a local-file counter: it does not call exchange APIs,
fill missing candles, deduplicate overlaps, or decide whether a file is complete.
It emits one result per CSV member (for ZIP files) so monthly/daily overlaps are
visible rather than silently combined.

Examples:
  python count_candle_rows.py --header auto data/BTCUSDT-1m.zip
  python count_candle_rows.py --header no --timestamp-column 0 data/kraken.zip
  python count_candle_rows.py --output counts.csv archive_a.zip archive_b.zip
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import sys
import zipfile
from pathlib import Path
from typing import Iterable, TextIO

OUTPUT_FIELDS = [
    "input_path",
    "archive_member",
    "format",
    "rows_counted",
    "header_skipped",
    "first_timestamp_in_file_order",
    "last_timestamp_in_file_order",
    "timestamp_column",
    "file_sha256",
    "file_size_bytes",
    "count_method",
    "notes",
]

HEADER_WORDS = {
    "time",
    "timestamp",
    "open_time",
    "open time",
    "start_time",
    "start time",
    "date",
    "date_utc",
    "unix",
    "unix_open",
    "kline_open_time",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_csv_member(name: str) -> bool:
    lowered = name.lower()
    return lowered.endswith((".csv", ".csv.gz", ".tsv", ".txt"))


def detected_header(row: list[str]) -> bool:
    if not row:
        return False
    first = row[0].strip().lstrip("\ufeff").lower()
    normalized = first.replace("-", "_").replace(" ", "_")
    return first in HEADER_WORDS or normalized in HEADER_WORDS


def count_text_stream(
    text_stream: TextIO,
    *,
    header_mode: str,
    delimiter: str,
    timestamp_column: int,
) -> tuple[int, bool, str, str, int]:
    """Return rows, header-skipped, first/last timestamp, parse-error count."""
    reader = csv.reader(text_stream, delimiter=delimiter, strict=False)
    rows = 0
    skipped_header = False
    first_timestamp = ""
    last_timestamp = ""
    parse_errors = 0
    first_nonempty_seen = False

    while True:
        try:
            row = next(reader)
        except StopIteration:
            break
        except csv.Error:
            parse_errors += 1
            continue

        if not row or all(not value.strip() for value in row):
            continue

        if not first_nonempty_seen:
            first_nonempty_seen = True
            if header_mode == "yes" or (header_mode == "auto" and detected_header(row)):
                skipped_header = True
                continue

        rows += 1
        if 0 <= timestamp_column < len(row):
            value = row[timestamp_column].strip()
            if value:
                if not first_timestamp:
                    first_timestamp = value
                last_timestamp = value

    return rows, skipped_header, first_timestamp, last_timestamp, parse_errors


def open_member_text(archive: zipfile.ZipFile, member: str) -> TextIO:
    raw = archive.open(member, "r")
    if member.lower().endswith(".gz"):
        binary = gzip.GzipFile(fileobj=raw, mode="rb")
        return io.TextIOWrapper(binary, encoding="utf-8-sig", errors="replace", newline="")
    return io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")


def make_record(
    *,
    input_path: Path,
    archive_member: str,
    file_format: str,
    rows: int,
    header_skipped: bool,
    first_timestamp: str,
    last_timestamp: str,
    timestamp_column: int,
    digest: str,
    file_size: int,
    parse_errors: int,
) -> dict[str, str | int]:
    notes = ""
    if parse_errors:
        notes = f"CSV parser recovered from {parse_errors} malformed record(s); inspect source file."
    return {
        "input_path": str(input_path),
        "archive_member": archive_member,
        "format": file_format,
        "rows_counted": rows,
        "header_skipped": "YES" if header_skipped else "NO",
        "first_timestamp_in_file_order": first_timestamp,
        "last_timestamp_in_file_order": last_timestamp,
        "timestamp_column": timestamp_column,
        "file_sha256": digest,
        "file_size_bytes": file_size,
        "count_method": "Streaming count of non-empty parsed CSV records; no padding or deduplication.",
        "notes": notes,
    }


def count_path(
    path: Path,
    *,
    header_mode: str,
    delimiter: str,
    timestamp_column: int,
) -> list[dict[str, str | int]]:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(path)

    digest = sha256_file(path)
    size = path.stat().st_size
    records: list[dict[str, str | int]] = []

    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, "r") as archive:
            members = [
                info for info in archive.infolist()
                if not info.is_dir() and is_csv_member(info.filename)
            ]
            if not members:
                raise ValueError(f"No CSV/TSV members found in ZIP: {path}")
            for info in members:
                with open_member_text(archive, info.filename) as text:
                    rows, header, first_ts, last_ts, errors = count_text_stream(
                        text,
                        header_mode=header_mode,
                        delimiter=delimiter,
                        timestamp_column=timestamp_column,
                    )
                member_format = "CSV.GZ member" if info.filename.lower().endswith(".gz") else "CSV member"
                records.append(make_record(
                    input_path=path,
                    archive_member=info.filename,
                    file_format=member_format,
                    rows=rows,
                    header_skipped=header,
                    first_timestamp=first_ts,
                    last_timestamp=last_ts,
                    timestamp_column=timestamp_column,
                    digest=digest,
                    file_size=size,
                    parse_errors=errors,
                ))
        return records

    if path.suffix.lower() == ".gz":
        with gzip.open(path, "rt", encoding="utf-8-sig", errors="replace", newline="") as text:
            rows, header, first_ts, last_ts, errors = count_text_stream(
                text,
                header_mode=header_mode,
                delimiter=delimiter,
                timestamp_column=timestamp_column,
            )
        file_format = "CSV.GZ"
    else:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as text:
            rows, header, first_ts, last_ts, errors = count_text_stream(
                text,
                header_mode=header_mode,
                delimiter=delimiter,
                timestamp_column=timestamp_column,
            )
        file_format = "CSV/TSV text"

    records.append(make_record(
        input_path=path,
        archive_member="",
        file_format=file_format,
        rows=rows,
        header_skipped=header,
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        timestamp_column=timestamp_column,
        digest=digest,
        file_size=size,
        parse_errors=errors,
    ))
    return records


def write_records(records: Iterable[dict[str, str | int]], output: Path | None) -> None:
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        target: TextIO = output.open("w", encoding="utf-8-sig", newline="")
    else:
        target = sys.stdout
    try:
        writer = csv.DictWriter(target, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    finally:
        if output:
            target.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Local CSV, CSV.GZ, or ZIP archive(s).")
    parser.add_argument("--header", choices=("auto", "yes", "no"), default="auto",
                        help="Header policy. 'auto' recognizes common timestamp-column names (default).")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter (default: comma).")
    parser.add_argument("--timestamp-column", type=int, default=0,
                        help="Zero-based column index used only to report first/last timestamp values (default: 0).")
    parser.add_argument("--output", type=Path, help="Optional output CSV path; otherwise write to stdout.")
    args = parser.parse_args()

    if len(args.delimiter) != 1:
        parser.error("--delimiter must be exactly one character")
    if args.timestamp_column < 0:
        parser.error("--timestamp-column must be zero or greater")

    records: list[dict[str, str | int]] = []
    try:
        for path in args.paths:
            records.extend(count_path(
                path,
                header_mode=args.header,
                delimiter=args.delimiter,
                timestamp_column=args.timestamp_column,
            ))
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    write_records(records, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
