# Crypto Historical Pair Data Bank

> An evidence-first catalogue and tooling platform for discovering, comparing, validating, and downloading historical cryptocurrency market-pair data.

[![CI](https://github.com/sinamoosazadeh/crypto-historical-pair-data-bank/actions/workflows/ci.yml/badge.svg)](https://github.com/sinamoosazadeh/crypto-historical-pair-data-bank/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Time standard: UTC](https://img.shields.io/badge/time-standard-UTC-5965e8)](docs/DATA_MODEL.md)
[![Evidence-first](https://img.shields.io/badge/research-evidence--first-247a7a)](docs/QUALITY_MODEL.md)

The ambition is to build one of the most comprehensive public indexes of historical cryptocurrency-pair datasets. The project does **not** claim to be the world's largest archive before a reproducible inventory proves that claim. Every coverage statement must distinguish documented capability, observed listings, anonymous file access, integrity checks, inspected content, independently counted rows, and cross-source verification.

## Open the control center

- **Interactive data explorer:** open [`index.html`](index.html) locally or publish with GitHub Pages. It supports source and public-download search, asset / market / interval / evidence filters, pagination, source links, theme switching, and filtered CSV export. The 10k-row coverage payload is loaded only when the coverage explorer is opened to keep initial page load light.
- **Full source registry:** [`catalog/sources.json`](catalog/sources.json) or [`catalog/sources.csv`](catalog/sources.csv).
- **Public download directory:** [`catalog/download-resources.json`](catalog/download-resources.json) or [`catalog/download-resources.csv`](catalog/download-resources.csv), with direct-link vs index distinctions, access states, terms, limitations, and next verification actions.
- **Coverage evidence grid:** [`catalog/coverage.json`](catalog/coverage.json) or [`catalog/coverage.csv`](catalog/coverage.csv).
- **Original research snapshot tables:** [`data/`](data/README.md), including the detailed source register, coverage matrix, claim audit, publisher-reported counts, and theoretical calendar-slot table.
- **Data model:** [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md).
- **Quality and evidence protocol:** [`docs/QUALITY_MODEL.md`](docs/QUALITY_MODEL.md).
- **Download and row-count workflow:** [`docs/DOWNLOAD_WORKFLOW.md`](docs/DOWNLOAD_WORKFLOW.md).
- **Research snapshot and limitations:** [`docs/RESEARCH_SNAPSHOT.md`](docs/RESEARCH_SNAPSHOT.md).
- **Roadmap:** [`ROADMAP.md`](ROADMAP.md).

## Research snapshot at a glance

The seed snapshot is dated **2026-10-21 UTC**. It is a research inventory, not a live audit of every link or a downloaded candle warehouse.

| Inventory | Snapshot value | Interpretation |
|---|---:|---|
| Source routes in the source register | 92 | Routes/products, not necessarily 92 independent providers |
| Target assets | 14 | BTC, ETH, SOL, BNB, DOGE, LTC, XRP, TRX, BCH, AVAX, DASH, SUI, ARB, ADA |
| Coverage matrix rows | 10,458 | Source × asset × interval evidence records |
| Distinct interval tokens in the matrix | 31 | Includes `UNRESOLVED`; case and provider-specific semantics must be preserved |
| Matrix status: `VERIFIED` | 1,110 | Inherited sample/documentation status; not a guarantee of complete downloadable history |
| Matrix status: `NOT_CHECKED` | 9,229 | Not examined to the required level; absence is not proven |
| Matrix status: `NOT_APPLICABLE` | 119 | Marked not applicable in the seed matrix |
| Raw historical files downloaded and independently counted in the supplied research pass | 0 | No row-countable raw candle archives were present in that input workspace |

A publisher-reported number is retained separately from a local row count. The seed research includes a publisher-displayed BCH/USDT 1-minute count of 3,557,191, but the corresponding archive was not downloaded and independently counted in the supplied pass. See [`data/publisher-reported-counts.csv`](data/publisher-reported-counts.csv).

## Project principles

1. **Evidence before claims.** A documented interval, an observed object, an anonymous download, and an independently counted archive are different states.
2. **Static downloads first for the strict anonymous-download workflow.** Public API-only routes remain catalogued for research completeness but are not silently treated as downloadable archives.
3. **Do not conflate products.** Spot, linear perpetuals, inverse contracts, dated futures, DEX pools, raw trades, order-book depth, funding, and derived metrics are distinct products.
4. **No synthetic candle-count claims.** Calendar bucket capacity is not a count of actual rows. Keep actual counts, publisher claims, and theoretical slots in separate fields.
5. **UTC everywhere.** Store and display timestamps in UTC; retain original timestamp units and anchor conventions as evidence.
6. **Respect upstream terms.** The repository's code license does not relicense upstream market data or grant rights to redistribute it.
7. **Build for audits and contributors.** Schemas, deterministic builds, tests, source proposal templates, link-audit jobs, issue templates, and versioned snapshots are part of the product.

## Data depth taxonomy

This is an operational taxonomy, not a universal formal standard:

- **Level 1 — bars and candles:** OHLC, OHLCV, quote volume, trade count, and candle metadata.
- **Level 2 — market microstructure:** raw trades/ticks and order-book snapshots or deltas, where available.
- **Level 3 — derived and derivatives metrics:** funding, open interest, liquidations, indices, mark prices, basis, and related computed series.

One provider may expose several levels in separate products. Never assume a source provides all levels merely because it is a derivatives venue.

## Run locally

Requirements: Python 3.10+ and a modern browser. The static UI does not need a frontend package install.

```bash
python -m http.server 8000
```

Open `http://127.0.0.1:8000`.

Validate the catalogue and run the unit tests:

```bash
python scripts/build_catalog.py
python scripts/validate_catalog.py
python scripts/check_english_only.py
python -m unittest discover -s tests -v
```

Refresh the file integrity manifest after intentional changes:

```bash
python scripts/build_manifest.py
```

The catalog JSON, CSV exports, and browser data bundle are deterministic build outputs generated from the English research snapshot CSVs. Edit the source data and source templates, not generated outputs by hand.

## Data collection scope

The initial universe is limited to the 14 target assets above but the data model supports more assets and provider-specific instruments. The project tracks:

- Spot markets and derivatives markets as distinct products;
- Pair and contract identities, quote / settlement currencies, and symbol aliases;
- Provider-native intervals, calendar boundaries, listing lifetimes, and retention limits;
- Static downloadable archives, community mirrors, and supporting research sources;
- OHLCV files and selected raw trade / book / derivative products;
- Exact artifact URLs, checksums, byte size, timestamp units, row-count method, gaps, duplicates, malformed rows, and license references as evidence becomes available.

Large raw historical archives are not committed by default. Git is used for code, schemas, source metadata, compact manifests, tests, and reproducible tooling—not as a universal multi-terabyte data transport. Future data releases should only be published when license and exchange terms permit it; otherwise provide source links and reproducible manifests.

## Contributing

Evidence-backed source submissions are especially valuable. Please include the exact market, provider-native symbol, interval, landing and direct-download URLs, whether anonymous download works, timestamp and schema details, a SHA-256 checksum, observed row count, date bounds, gap policy, and license / terms evidence. See [`CONTRIBUTING.md`](CONTRIBUTING.md) and the source proposal issue template.

## Important limitations

The snapshot is broad but uneven. `VERIFIED` is a status inherited from the supplied research matrix and may reflect limited samples or documented capability. It does not mean every partition was downloaded, the complete date range was inspected, or candle rows were independently counted. `NOT_CHECKED` means unknown. Provider APIs, source pages, file naming, and data terms can change; the exact artifact must be rechecked before relying on it.

This repository is data discovery and quality infrastructure, not investment advice and not a promise of data availability, representativeness, or trading performance.
