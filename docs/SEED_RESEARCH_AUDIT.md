# Seed Research Archive Audit

## Input artifact

- Original filename: `crypto_historical_candles_research_2026-10-21.zip`
- SHA-256: `249f329cbccd1b50bc19ddc9d235af1f1942674c64ac1bed1d6cca4fe654f091`
- Archive integrity: `unzip -t` completed without errors.
- Internal file checksums: all 15 entries covered by the supplied SHA-256 sidecar matched.
- Snapshot date stated by the source package: `2026-10-21`.

The original ZIP is not copied into this repository. Its workbook and narrative reports contain non-English script, which conflicts with the repository's English-only content policy. The machine-readable research tables were integrated into the canonical CSV snapshot, and key methodology and limitations were carried forward in English documentation.

## Integrated contents

| Input artifact | Repository destination | Treatment |
|---|---|---|
| `crypto_free_source_catalog_2026-10-21.csv` | `data/source-catalog.csv` | Imported as the 92-route source register |
| `crypto_availability_matrix_2026-10-21.csv` | `data/availability-matrix.csv` | Imported as the 10,458-row source × asset × interval evidence grid |
| `crypto_target_assets_2026-10-21.csv` | `data/target-assets.csv` | Preserved as the 14-asset scope list |
| `binance_spot_14_calendar_slots_2026-10-20.csv` | `data/binance-spot-calendar-slots.csv` | Preserved; theoretical slots are not actual candle counts |
| `crypto_source_claims_audit_2026-10-21.csv` | `data/source-claims-audit.csv` | Preserved with claim provenance and caveats |
| `publisher_reported_candle_counts_2026-10-21.csv` | `data/publisher-reported-counts.csv` | Kept separate from independent local counts |
| `local_raw_data_inventory_2026-10-21.csv` | `data/local-raw-data-inventory.csv` | Preserved as the raw-data measurement baseline |
| `count_candle_rows.py` | `scripts/count_candle_rows.py` | Reviewed and represented by the maintained counting tools; do not execute the archive's package-builder blindly |
| `crypto_kline_research_notes_2026-10-21_FA.md` | `docs/RESEARCH_SNAPSHOT.md` and `docs/REFERENCES.md` | Key scope, source findings, and limitations re-expressed in English |
| `crypto_methodology_audit_2026-10-21_FA.md` | `docs/QUALITY_MODEL.md` and `docs/DOWNLOAD_WORKFLOW.md` | Methodology and evidence states re-expressed in English |

The workbook and the large package-builder script are intentionally not committed as source-of-truth inputs. The original builder is a generated research artifact; the maintained deterministic builder in `scripts/build_catalog.py` is the project's authoritative transformation layer. The supplemental 12-row `public-download-resources.csv` register is exposed as its own searchable `catalog/download-resources.json` / `.csv` directory; it remains separate from the 92-route matrix and is not presented as an anonymous-access pass.

## Findings that must remain visible

- Target assets: 14.
- Source routes: 92. Routes are products or source paths, not necessarily independent vendors.
- Matrix rows: 10,458.
- Input matrix statuses: 1,110 `VERIFIED`, 9,229 `NOT_CHECKED`, and 119 `NOT_APPLICABLE`.
- Actual raw candle files downloaded and counted during the source research pass: zero.
- Curated public-download leads carried into the separate directory: 12; none should be promoted to anonymous-download-verified solely because it appears in this list.
- All row counts from provider pages remain publisher claims unless a particular artifact was independently downloaded, hashed, and counted.
- The Binance calendar-slot table is theoretical capacity only; it must not be displayed as observed candles.
- `NOT_CHECKED` means unknown, not absent. `VERIFIED` may describe documented capability or a limited sample and does not prove full-history availability.

## Reproduction

From the repository root:

```bash
python scripts/build_catalog.py
python scripts/validate_catalog.py
python scripts/check_english_only.py
python -m unittest discover -s tests -v
```

The source CSVs are the retained evidence snapshot. The generated catalog files are reproducible derivatives. A future live audit must add dated per-object observations, HTTP outcomes, file byte sizes, SHA-256 values, parsed schema, observed row counts, timestamp bounds, gap/duplicate checks, and license review; this import alone does not satisfy those later evidence levels.
