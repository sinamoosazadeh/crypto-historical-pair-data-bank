# Data directory

This directory contains the English machine-readable research snapshot and catalogue outputs. It intentionally does not contain bulk historical candle archives.

## Source-of-truth snapshot tables

| File | Grain | Purpose |
|---|---|---|
| `source-catalog.csv` | One row per source route / product | Provider, product, access conditions, native intervals, schema notes, source links, evidence level, and limitations |
| `availability-matrix.csv` | One row per route × asset × interval | Pair/interval status, history statements, evidence, theoretical slots, count state, and source links |
| `target-assets.csv` | One row per requested asset | The 14-symbol project universe and scope notes |
| `source-claims-audit.csv` | One row per recorded claim | Separates publisher claims from independently measured results |
| `publisher-reported-counts.csv` | One row per public count claim | Publisher-displayed counts with explicit independent-count caveats |
| `binance-spot-calendar-slots.csv` | One row per Binance spot asset × interval | First-open observations and theoretical calendar boundaries; theoretical slots are not actual rows |
| `local-raw-data-inventory.csv` | One row per input-workspace inventory category | Reports what was actually downloaded and counted locally in the supplied research pass |
| `interval-reference.csv` | One row per token found in the matrix | Token inventory; native case and semantics must be retained by provider |
| `public-download-resources.csv` | One row per curated public-download candidate | Supplemental archive/repository entry points, data family, access caveats, terms, and next verification steps |
| `catalog/download-resources.json` / `.csv` | One row per curated download lead | Generated, searchable view of the supplemental resource register; entries are leads, not proof of anonymous download or completeness |
| `snapshot-summary.json` | One snapshot | Reproducible inventory totals and interpretation warnings |

The original filenames had date suffixes and UTF-8 byte-order marks. This project preserves their contents under consistent English filenames and removes BOM bytes so the repository remains clean for text tooling.

## Status semantics

- `VERIFIED`: a status assigned by the research snapshot under its recorded evidence basis. It must not be read as a full-history row-count verification.
- `NOT_CHECKED`: the relevant asset/product/interval combination was not checked to the matrix's required standard.
- `NOT_APPLICABLE`: marked outside the applicable product scope in the seed matrix.
- `NOT_MEASURED`: no actual raw-row count was recorded.
- `PUBLISHER_REPORTED_NOT_INDEPENDENTLY_COUNTED`: the count came from a provider or publisher statement, not a local archive count.

A blank count is unknown, not zero. A missing row does not establish that a dataset does not exist. A theoretical calendar count is not interchangeable with observed source rows.

## Rebuilding generated catalogues

From the repository root:

```bash
python scripts/build_catalog.py
python scripts/validate_catalog.py
```

The source snapshot tables are the preserved research input; `catalog/*.json`, `catalog/*.csv`, and `web/assets/catalog.js` are deterministic catalogue views generated for the UI and programmatic access. The download-resource directory is intentionally separate from the 92 source routes so its narrower, manually curated lead set cannot distort route-level coverage statistics.
