# Build Verification Report

**Package version:** 0.3.0  
**Research snapshot:** 2026-10-21  
**Repository publication:** Not yet published by this build; see `docs/TERMUX_PUBLISH.md` for the one-time repository creation and publishing hand-off.

## Snapshot inventory

- 92 source routes are retained in the source registry.
- The availability matrix contains 10,458 route/asset/interval records.
- The declared target asset universe contains 14 symbols: BTC, ETH, SOL, BNB, DOGE, LTC, XRP, TRX, BCH, AVAX, DASH, SUI, ARB, and ADA.
- The matrix snapshot contains 1,110 `VERIFIED`, 9,229 `NOT_CHECKED`, and 119 `NOT_APPLICABLE` rows. These are snapshot status labels, not evidence that every complete archive was downloaded or row-counted.
- The seed research pass recorded zero local raw candle archives and zero independently counted raw candle rows.
- Publisher-reported counts are retained only with explicit provenance labels and are not rebranded as local measurements.

## Automated checks

Run the following commands from the repository root:

```bash
python scripts/build_catalog.py
python scripts/validate_catalog.py
python -m unittest discover -s tests -v
python -m compileall -q scripts tests
```

The CI workflow also checks generated catalogue drift, source encoding, catalogue invariants, local UI assets, HTML internal references, the offline cache shell, and publishing-script syntax. The packaged baseline has 26 passing unit tests. URL checks should be run deliberately against an approved, rate-limited source list; a successful HTTP response is not proof of dataset completeness or license suitability.

## Interpretation boundary

This repository is a research index and reproducible catalogue snapshot. A `qualified_candidate` means a source appears to fit a public-static-download path based on the recorded source description; it is not a guarantee that every file is currently reachable, anonymous, license-compatible, complete, or available for all symbols and intervals. The project does not claim global completeness or world-leading rank. Those are goals that require ongoing source discovery, independent downloads, checksum verification, range inspection, row counting, gap analysis, schema normalization, and a visible audit trail.


## 0.3.0 verification additions

The download directory has its own generated JSON/CSV catalogue and the browser payload is checked against that register. The navigation validator confirms every `data-view` / `data-go` target exists and that the Download directory exposes its required filters and export control. Unit tests exercise timestamp normalization, naive timestamp rejection, case-sensitive interval handling, duplicate detection, OHLC consistency, negative-volume detection, and the caveat that cadence gaps may be omitted empty bars.
