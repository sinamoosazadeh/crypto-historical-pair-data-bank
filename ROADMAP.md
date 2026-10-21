# Roadmap

This roadmap describes goals and acceptance criteria. A checked box means the repository contains the listed project component; it does not mean every underlying source claim is fully verified.

## Phase 0 — Research foundation and public catalogue

- [x] Preserve the dated research source register, availability matrix, source-claim audit, publisher-count register, and theoretical calendar-slot table.
- [x] Normalize 92 source routes, 14 target assets, and 10,458 route × asset × interval evidence rows for the UI.
- [x] Distinguish static-download candidates from API-only, paid, retired, conditional, and unverified routes.
- [x] Publish a responsive, searchable static catalogue with filters, pagination, source links, theme switching, and CSV export.
- [x] Add schemas, deterministic build tooling, source contribution templates, CI, GitHub Pages workflow, and a file hash manifest.
- [x] Include an archive row-count utility and tests for CSV, gzip, and ZIP member counting.

## Phase 1 — File-level availability and integrity verification

- [ ] Probe candidate static index and direct-download URLs with conservative request budgets and UTC observation timestamps.
- [ ] Capture HTTP status, final URL, content type, bytes, ETag / Last-Modified, and access-control outcome.
- [ ] Resolve exact symbols, market product, and file partitions for each of the 14 target assets.
- [ ] Download a bounded sample of each qualifying archive family, verify its checksum, and inspect schema / timestamp units.
- [ ] Row-count actual raw files and preserve the command, checksum, parse policy, first/last timestamps, duplicate count, malformed-row count, and gap interpretation.
- [ ] Upgrade source and matrix statuses only with stored evidence; add downgrade history when links or terms change.

## Phase 2 — Source-specific adapters and instrument identity

- [ ] Add provider-specific symbol normalization while preserving native identifiers and aliases.
- [ ] Model listings, delistings, redenominations, contract migrations, quote currencies, settlement assets, and product IDs.
- [ ] Make candle anchors and interval semantics explicit for fixed bars, weeks, months, and provider-specific labels.
- [ ] Add independent schema adapters for CSV, CSV.GZ, ZIP, JSONL, Parquet, and source-specific manifests.
- [ ] Separate raw candles, raw trades, order-book snapshots/deltas, and derivatives metrics in schemas and UI filters.

## Phase 3 — Reproducible downloads and derived datasets

- [ ] Add a query planner that resolves provider × market × symbol × interval × date range into exact archive paths.
- [ ] Add resumable bounded file transfer with timeouts, retry caps, size limits, checksums, and a local cache.
- [ ] Support optional Parquet / Arrow conversion while preserving the original bytes and their hashes.
- [ ] Add per-source gap heatmaps, pair histories, and date-range overlap views.
- [ ] Aggregate trades into candles only under a versioned specification for timezone, order, trade filtering, and empty-bar handling.

## Phase 4 — Scale and release engineering

- [ ] Publish immutable source snapshots and signed small metadata releases.
- [ ] Add a scheduled link monitor with source-specific robots, retry, and rate policies.
- [ ] Add release changelogs showing which claims were added, promoted, downgraded, or retired.
- [ ] Evaluate object storage or a federated index for large raw datasets; publish data only when license and terms permit.
- [ ] Benchmark static UI performance and move to a partitioned index or search worker if the dataset grows materially.

## Non-goals

- A trading bot, alpha signal service, or investment recommendation engine.
- A claim that every listed source allows redistribution of its market data.
- A claim of world's largest coverage without a defined comparison set and independently reproducible audit.
