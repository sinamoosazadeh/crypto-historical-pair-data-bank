# Changelog

## 0.3.0 — 2026-10-22

- Added a separate, filterable download-resource directory with eligibility labels, cadence, scope, reported coverage, terms, limitations, and next verification steps.
- Exposed the download lead register as generated JSON and CSV, with metadata-to-UI consistency checks and deterministic CI drift checks.
- Extended the offline shell cache to include the resource directory and upgraded the cache version.
- Split the heavy coverage-grid bundle from the landing-page payload and load it on demand to improve startup performance on mobile connections.
- Added local OHLCV audit tooling for timestamps, duplicate rows, ordering, schema, OHLC integrity, volume checks, cadence gaps, and artifact hashes.

## 0.2.0 — 2026-10-22

- Integrated the dated English source catalog and availability matrix from the supplied research archive.
- Expanded the normalized registry from an initial small draft to 92 source routes and 10,458 route × asset × interval evidence records.
- Added source-claim audit, publisher-reported count register, Binance calendar-slot table, raw-file inventory, interval reference, and curated download-resource register.
- Reworked catalogue generation and validation around preserved CSV inputs; reduced the browser bundle by keeping detailed provenance in downloadable source tables.
- Updated the coverage UI to mark inherited `VERIFIED` rows as partial evidence and explicitly qualify publisher-reported candle counts.
- Removed non-English-language research artifacts so every repository text file and user-facing asset can remain English-only.
- Expanded repository validation to check route IDs, matrix status distribution, count provenance, local links, and Unicode script constraints.

## 0.1.0 — 2026-10-22

- Created a responsive static catalogue interface, source and asset models, evidence terminology, archive-count tooling, unit tests, CI, GitHub Pages deployment workflow, and contribution templates.

## Known work not yet completed

- The 92-route snapshot is not a current live probe of every source.
- No full raw historical candle archive was downloaded and independently row-counted in the supplied research pass.
- Exact anonymous-download behavior, per-file checksums, date-partition completeness, and redistribution terms still require source-by-source verification.
