# PairAtlas

**Find the pair. Follow the evidence.**

PairAtlas is the discovery layer for this historical crypto pair-data research bank. It helps you choose an asset, compare source routes and intervals, inspect evidence levels, and follow download leads — without pretending that a documented API is the same as a counted archive.

> Research snapshot: 2026-10-21. 92 source routes, 14 target assets, 10,458 coverage records, 12 download leads. No raw candle archive was independently counted in the seed research. `VERIFIED` is an evidence label, not a full-archive row count.

## Access modes

1. **Browse on GitHub** — read `catalog/`, `data/`, `docs/`, and `MANIFEST.json`.
2. **Static website** — `index.html` + `web/assets/` provide coverage filters, source registry, download directory, asset universe, evidence meter, shareable hash filters, CSV/JSON export, and light/dark themes. Deploy with GitHub Pages.
3. **Terminal CLI** — install `pairatlas` from a checkout or wheel and query the same catalog offline.
4. **Local server** — serve the static site from a checkout.

GitHub itself renders Markdown and hosts static files; it does not run the interactive explorer inside a README. GitHub Pages is the supported way to publish the UI from this repository.

## Install without a checkout

The GitHub release includes a self-contained metadata CLI wheel:

```bash
python -m pip install https://github.com/sinamoosazadeh/crypto-historical-pair-data-bank/releases/download/v0.4.0/crypto_historical_pair_data_bank-0.4.0-py3-none-any.whl
pairatlas stats
```

The wheel contains the catalog, not raw market archives or the website. Use a checkout for `serve`.

## Quick start

### Terminal

```bash
python -m pip install -e .
pairatlas stats
pairatlas find --asset BTC --interval 1m --limit 10
pairatlas sources --status qualified_candidate
pairatlas downloads --limit 10
pairatlas show BINANCE_SPOT
```

The legacy entry point remains available:

```bash
python -m pairatlas stats
python scripts/audit_ohlcv.py --help
```

### Website

```bash
pairatlas serve --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. For a container or remote preview, bind explicitly to `0.0.0.0` and proxy the port.

## What the numbers mean

| Measure | Value |
|---|---:|
| Source routes | 92 |
| Target assets | 14 |
| Coverage records | 10,458 |
| Download leads | 12 |
| `VERIFIED` coverage rows | 1,110 |
| `NOT_CHECKED` coverage rows | 9,229 |
| `NOT_APPLICABLE` coverage rows | 119 |
| Raw candle archives counted in seed research | 0 |

Coverage count basis is mostly `NOT_MEASURED`; one publisher-reported count exists for BCH/USDT 1m. Unknown does not mean unavailable. Partial evidence may be documentation or a limited sample.

## Data and provenance

- `catalog/` is the canonical machine-readable registry.
- `data/` holds snapshot summaries and interval reference material.
- `web/assets/catalog.js` and `coverage-data.js` are generated from the catalog for the browser.
- `MANIFEST.json` records SHA-256 hashes for the tracked snapshot files.
- Upstream datasets remain subject to their own terms; see `DATA_LICENSE.md`.
- Code is MIT; see `LICENSE`.

The UI does not download exchange archives, call live APIs, or infer completeness from a status badge. Source pagination, per-record JSON export, filtered CSV export, and safe external links are designed to keep provenance visible.

## Audit and validation

```bash
python scripts/validate_catalog.py
python scripts/check_english_only.py
python -m unittest discover -s tests -v
python scripts/build_manifest.py
pairatlas audit --help
```

`pairatlas audit` wraps the original OHLCV auditor for files you supply locally. It does not fetch data by itself.

## Project layout

```text
pairatlas/          installable CLI and audit wrapper
catalog/            canonical source, coverage, asset, interval, download records
data/               snapshot summary and interval reference
web/                static explorer assets
scripts/            validators, builders, auditors, publishing helpers
docs/               architecture, UI, methodology, data terms
tests/              catalog and CLI tests
MANIFEST.json       snapshot file hashes
```

## Limits and next steps

- 15 source routes have no coverage-matrix rows; they remain registry leads, not measured coverage.
- Interval tokens are provider-native and case-sensitive; `1M`, `1mo`, and `1mon` are not normalized blindly.
- Source status and coverage status are different axes.
- Anonymous link audits observe HTTP behavior, not legal rights or complete archive contents.

See `docs/` for the original research methodology and architecture notes.
