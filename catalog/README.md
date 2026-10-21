# Generated catalogue outputs

- `sources.json` / `sources.csv`: normalized source-route registry derived from `data/source-catalog.csv`.
- `assets.json`: the 14 requested target assets; it does not assert that every venue lists every asset.
- `timeframes.json`: 30 distinct interval tokens in the matrix, excluding the `UNRESOLVED` sentinel. Case is preserved and cross-provider semantics must not be assumed.
- `coverage.json` / `coverage.csv`: normalized source × asset × interval evidence records derived from `data/availability-matrix.csv`.

The source-of-truth research tables live in `data/`. Regenerate all normalized outputs with `python scripts/build_catalog.py`; do not edit generated exports manually. The JSON and CSV outputs contain the same compact evidence summaries while the original matrix preserves all source-supplied fields and notes.

A source being listed, or marked as a qualified candidate, does not mean all files are currently accessible or that all rows have been independently counted. Check the access classification and evidence caveats on every specific route.
