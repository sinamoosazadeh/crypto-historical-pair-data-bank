#!/usr/bin/env python3
"""Generate a deterministic-path inventory with byte size and SHA-256 for every project file.

MANIFEST.json intentionally does not hash itself; doing so would be recursive. It includes the source snapshot tables, generated catalogues, code, tests, and documentation.
Caches, virtual environments, Git internals, and this manifest itself are excluded.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {'.git', '__pycache__', '.pytest_cache', '.ruff_cache', '.venv', 'venv'}
EXCLUDED_NAMES = {'MANIFEST.json'}

def main() -> int:
    entries = []
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or path.name in EXCLUDED_NAMES:
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts) or path.suffix in {'.pyc', '.pyo'}:
            continue
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        entries.append({'path': relative.as_posix(), 'bytes': path.stat().st_size, 'sha256': digest.hexdigest()})
    manifest = {
        'project': 'Crypto Historical Pair Data Bank',
        'version': '0.3.0',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'hash_algorithm': 'SHA-256',
        'self_hash_excluded': True,
        'files': entries,
    }
    (ROOT / 'MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote MANIFEST.json for {len(entries)} files (manifest excludes its own hash).')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
