#!/usr/bin/env python3
"""Count actual CSV rows from local files and emit an auditable JSONL manifest.

No network access is performed. For ZIPs, each CSV member is reported separately.
The checksum is for the original on-disk artifact, not for decompressed content.
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, TextIO

TIMESTAMP_CANDIDATES = {
    'timestamp', 'time', 'date', 'datetime', 'open_time', 'opentime',
    'timestamp_utc', 'unix', 'unix_timestamp', 'start_time', 'starttime'
}

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def _count_text_stream(stream: TextIO, artifact_path: str, member: str | None,
                       artifact_bytes: int, artifact_sha256: str) -> dict:
    reader = csv.DictReader(stream)
    if not reader.fieldnames:
        raise ValueError(f'{artifact_path}: no CSV header found')
    normalized = {name.strip().lower().replace(' ', '_'): name for name in reader.fieldnames if name}
    timestamp_col = next((normalized[name] for name in TIMESTAMP_CANDIDATES if name in normalized), None)
    row_count = malformed = 0
    first_ts = last_ts = None
    for row in reader:
        if not row or not any(v not in (None, '') for v in row.values()):
            continue
        row_count += 1
        if None in row:
            malformed += 1
        if timestamp_col:
            value = row.get(timestamp_col)
            if value not in (None, ''):
                if first_ts is None:
                    first_ts = value
                last_ts = value
    return {
        'artifact_path': artifact_path,
        'archive_member': member,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'bytes_on_disk': artifact_bytes,
        'sha256_on_disk': artifact_sha256,
        'csv_header': reader.fieldnames,
        'timestamp_column_candidate': timestamp_col,
        'row_count_observed': row_count,
        'rows_with_extra_fields': malformed,
        'first_timestamp_value_in_file_order': first_ts,
        'last_timestamp_value_in_file_order': last_ts,
        'timestamp_semantics': 'raw field values; units/timezone not inferred',
        'count_method': 'csv.DictReader; header excluded; blank records skipped; rows with surplus fields counted separately',
        'warning': 'Row count is not proof of completeness; inspect timestamp unit, ordering, gaps, duplicate keys and source terms.'
    }

def count_csv(path: Path) -> list[dict]:
    digest = sha256_file(path)
    size = path.stat().st_size
    suffix = ''.join(path.suffixes).lower()
    if suffix.endswith('.csv.gz'):
        with gzip.open(path, 'rt', encoding='utf-8-sig', errors='replace', newline='') as stream:
            return [_count_text_stream(stream, str(path), None, size, digest)]
    if path.suffix.lower() == '.csv':
        with path.open('r', encoding='utf-8-sig', errors='replace', newline='') as stream:
            return [_count_text_stream(stream, str(path), None, size, digest)]
    if path.suffix.lower() == '.zip':
        results=[]
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                if member.is_dir() or not member.filename.lower().endswith('.csv'):
                    continue
                with archive.open(member, 'r') as raw:
                    import io
                    stream=io.TextIOWrapper(raw,encoding='utf-8-sig',errors='replace',newline='')
                    results.append(_count_text_stream(stream,str(path),member.filename,size,digest))
        if not results:
            raise ValueError(f'{path}: ZIP contains no CSV members')
        return results
    raise ValueError(f'Unsupported file type: {path} (expected .csv, .csv.gz or .zip)')

def discover(paths: list[Path]) -> list[Path]:
    found=[]
    for item in paths:
        if item.is_file():
            found.append(item)
        elif item.is_dir():
            found.extend(p for p in item.rglob('*') if p.is_file() and (p.suffix.lower()=='.csv' or p.suffix.lower()=='.zip' or ''.join(p.suffixes).lower().endswith('.csv.gz')))
        else:
            raise FileNotFoundError(item)
    return sorted(set(found))

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths',nargs='+',help='CSV, CSV.GZ, ZIP files or directories')
    parser.add_argument('--output',default='archive_count_manifest.jsonl',help='Output JSONL path (default: archive_count_manifest.jsonl)')
    args=parser.parse_args()
    paths=discover([Path(p) for p in args.paths])
    if not paths:
        parser.error('No supported files found')
    rows=[]; errors=[]
    for path in paths:
        try: rows.extend(count_csv(path))
        except (OSError, ValueError, zipfile.BadZipFile, EOFError) as exc: errors.append({'path':str(path),'error':str(exc)})
    out=Path(args.output)
    out.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),encoding='utf-8')
    print(f'Artifacts inspected: {len(paths)} | CSV members counted: {len(rows)} | errors: {len(errors)}')
    print(f'Manifest: {out} ({out.stat().st_size} bytes)')
    for err in errors: print('ERROR:',json.dumps(err,ensure_ascii=False))
    return 1 if errors else 0

if __name__=='__main__':
    raise SystemExit(main())
