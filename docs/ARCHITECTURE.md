# Architecture and data flow

## Components

- `data/*.csv`: preserved research snapshot tables; this is the source material for the current evidence inventory.
- `catalog/*.json`: normalized machine-readable registry, asset universe, interval vocabulary, and coverage grid.
- `catalog/*.csv`: flat exports for query tools and spreadsheets.
- `web/assets/catalog.js`: deterministic payload loaded by the static browser application.
- `index.html` and `web/assets/*`: responsive control center with search, filters, evidence-aware status displays, and CSV export.
- `scripts/`: deterministic build, validation, URL-audit and archive-row-count utilities.
- `schemas/` and `templates/`: machine-checkable source and artifact contracts.
- `.github/workflows/`: validation, Pages publishing, and scheduled source-link auditing.

## Build path

`data/source-catalog.csv` + `data/availability-matrix.csv` + supporting snapshot tables
→ `scripts/build_catalog.py`
→ `catalog/*.json`, `catalog/*.csv`, `web/assets/catalog.js`
→ `scripts/validate_catalog.py` + tests
→ GitHub Pages deployment.

## Design constraints

The browser catalog is static and has no runtime API key or server-side secret. Bulk raw files are not committed by default. New archive acquisitions should be an explicitly bounded job with resumable downloads and artifact manifests, not an unbounded action triggered by opening the UI. Large binary data should live only in destinations where terms, size, and public access make sense.

## Future service boundary

A future optional backend may index public object listings, queue bounded anonymous downloads, compute checksums and row statistics, and publish immutable manifests. It must not require exchange API keys for the repository's strict static-download tier; API-backed sources remain a separate research category. Any background crawler must use conservative concurrency, retry budgets, request caps, observability, and explicit source-specific policies.


## Public download lead directory

`data/public-download-resources.csv` is a supplemental, hand-curated lead table, separate from the 92-route source matrix. `scripts/build_catalog.py` generates `catalog/download-resources.json` and `.csv` and embeds the records into `web/assets/catalog.js` for the `Download directory` UI. This separation prevents a short curated list from being mistaken for the complete provider-route census. Eligibility states encode the current evidence status and must never be interpreted as successful live tests.
