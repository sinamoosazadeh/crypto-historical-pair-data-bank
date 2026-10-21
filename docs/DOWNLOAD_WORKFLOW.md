# Repeatable archive inspection workflow

This project does not fetch huge datasets automatically as part of ordinary validation. For each source and query, use a bounded, auditable workflow:

1. Resolve the exact instrument, market and interval from provider-specific documentation.
2. Identify a static listing or canonical direct artifact path.
3. Record an observation in UTC before downloading.
4. Enforce explicit max bytes/files, timeouts and retries.
5. Stream the archive; save the original checksum and byte count.
6. Inspect compression, header/schema and timestamp units.
7. Count rows after excluding headers and malformed rows under a documented policy.
8. Compare the earliest/latest actual timestamps to file naming and expected interval.
9. Preserve gaps; classify them where evidence is available.
10. Record license/terms and whether storing or mirroring the file is permitted.

For very large collections, create a `manifest.jsonl` with one record per file and allow resumable processing. Never report a source-wide candle total by multiplying a date span by a timeframe unless you explicitly label it theoretical bucket capacity; it is not an observed row count.


## Local OHLCV integrity audit

Use the network-free audit helper after obtaining a permitted archive:

```bash
python scripts/audit_ohlcv.py /path/to/file.csv --interval 1m --output report.jsonl
python scripts/audit_ohlcv.py /path/to/archive.zip --interval 5m --output report.jsonl
python scripts/audit_ohlcv.py /path/to/file.csv.gz --timestamp-unit ms --output report.jsonl
```

The tool records the artifact SHA-256, observed rows, required columns, timestamp interpretation, UTC bounds, duplicate timestamps, out-of-order pairs, malformed values, OHLC inconsistencies, negative or invalid volume, and candidate cadence gaps. Numeric timestamp auto-detection is a heuristic; use the provider-documented `--timestamp-unit` where possible. Naive datetimes are rejected unless `--naive-timezone UTC` is explicitly supplied. A gap is not proof of a missing candle because some providers omit empty intervals. Calendar intervals such as `1mo` and ambiguous case-sensitive tokens such as `1M` intentionally require source-specific handling.
