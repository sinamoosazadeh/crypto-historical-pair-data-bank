# Research snapshot: provenance and limits

## Snapshot identity

- **Snapshot date:** 2026-10-21 (UTC)
- **Source route records:** 92
- **Target asset universe:** 14
- **Availability matrix rows:** 10,458
- **Local raw historical candle files downloaded and counted in the supplied research pass:** 0

The source data is preserved under [`data/`](../data/README.md). The snapshot is useful as a broad discovery and prioritization layer; it is not evidence that every listed product currently offers an anonymous static file or that every source-specific date partition exists.

## Interpreting the matrix

The matrix contains 1,110 `VERIFIED`, 9,229 `NOT_CHECKED`, and 119 `NOT_APPLICABLE` rows. These are the values recorded in the seed input. For some `VERIFIED` rows, the supporting basis is a one-row API sample, official interval documentation, or a derived interval boundary; prior raw response bodies were not retained for every assertion. Therefore `VERIFIED` is not a synonym for any of the following:

- an archive file was downloaded;
- all monthly / daily partitions were present;
- every row was parsed and independently counted;
- missing bars, duplicates, and malformed data were audited;
- the entire date range was verified for the exact instrument;
- current anonymous-download access or redistribution rights were tested.

The matrix's `NOT_CHECKED` value means unknown, not absent. `NOT_APPLICABLE` is a product-scope judgment from the source snapshot, not an exchange-wide statement.

## Count integrity

No raw candle archive was present in the supplied research workspace. The project does not claim locally counted exchange-wide candle totals. `publisher-reported-counts.csv` preserves publisher displays separately; these may become stale and are not independent counts. The theoretical calendar-slot table retains theoretical boundaries and sample notes, but those slots must never be presented as actual observed candles.

## Scope and source selection

The strict preferred workflow is free, anonymous, static file download without an API key or account. Public API routes are retained where useful for research completeness but flagged as outside the strict static-download criterion unless a separate downloadable archive is identified. Public repositories and mirrors need their own file-level audit, licensing review, checksums, and date/symbol completeness check.

The first-stage corpus mixes spot, centralized-exchange derivatives, decentralized-exchange products, third-party archives, API-only routes, and non-candle references. These are not interchangeable. The `source-catalog.csv` records product class and access notes; see the raw route and evidence fields before treating a source as eligible.

## Recommended promotion path

For a specific source × market × pair × interval × date partition, promote evidence in this order:

1. Documented data product and exact provider-native interval.
2. Exact object/directory entry observed.
3. Anonymous direct file download with HTTP result and checked UTC timestamp.
4. File size, archive integrity, and SHA-256 captured.
5. Columns and timestamp encoding inspected.
6. Actual records counted using a named deterministic script.
7. First/last event timestamps, duplicates, malformed rows, gaps, and no-trade semantics inspected.
8. Terms reviewed and an independent source / checksum / sample cross-check recorded.

The required evidence fields and example manifests are documented in [`QUALITY_MODEL.md`](QUALITY_MODEL.md), [`DOWNLOAD_WORKFLOW.md`](DOWNLOAD_WORKFLOW.md), and [`schemas/artifact-manifest.schema.json`](../schemas/artifact-manifest.schema.json).
