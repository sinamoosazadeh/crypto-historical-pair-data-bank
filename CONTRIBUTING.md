# Contributing

Contributions are most valuable when they improve **coverage, evidence quality, reproducibility, accessibility or usability**.

## Source submission checklist

For each proposed source, please provide:

1. canonical landing page and exact direct file/object URL if available;
2. provider, venue, market type, symbol/pair, quote currency and contract type;
3. access class: anonymous static download, free account, API-only, paid or unknown;
4. supported intervals with a source citation; do not infer intervals from another provider;
5. earliest/latest observed timestamps and the date checked (UTC);
6. data level and raw fields;
7. file format, compression, partition cadence, checksums and row-count method;
8. license/terms and redistribution status;
9. known gaps, symbol migrations, delisted products, timezone conventions and caveats.

## Evidence vocabulary

- `DOCUMENTED`: the provider documents the capability, but a particular file may not have been checked.
- `LISTING_OBSERVED`: directory or listing entry was observed.
- `DIRECT_DOWNLOAD_VERIFIED`: a file was downloaded without a key/login during the stated test.
- `CONTENT_INSPECTED`: schema and representative rows were inspected.
- `ROWS_COUNTED`: records were counted from the concrete file; method and checksum are retained.
- `INDEPENDENTLY_CROSSCHECKED`: a second method or source was compared.
- `UNVERIFIED`: hypothesis, candidate mapping, stale evidence or untested path.

Do not collapse these states into a single "supported" badge.

## Development

```bash
python scripts/validate_catalog.py
python -m unittest discover -s tests -v
python scripts/build_catalog.py
```

Use UTC for all persisted timestamps. Keep secrets out of source control. Never include large archives in Git unless explicitly approved and size/license checks pass; link to the upstream canonical artifact instead.

## Pull requests

Use small, reviewable commits. Include tests for changes to validators and aggregators. Any coverage-statistic change must identify the input data and calculation. If you cannot verify a source live, explain the limitation instead of guessing.
