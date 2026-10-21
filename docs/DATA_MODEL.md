# Data model and canonical vocabulary

## Core entities

- **Venue:** legal/brand/operator identity. A brand can operate several markets.
- **Market:** spot, margin, perpetual, dated futures, options or another explicit product family.
- **Instrument:** venue-specific symbol with base, quote, settlement asset, contract size, linear/inverse nature and lifecycle.
- **Dataset family:** klines/OHLCV, trades, aggregate trades, order book, funding, open interest, liquidation, mark/index/premium price or another precisely named series.
- **Interval:** native provider interval or an explicitly derived interval.
- **Artifact:** one concrete file/object/partition, with canonical upstream URL, byte size, compression, observed date range, row count and checksum.
- **Observation:** a time-stamped verification event recording how the artifact or capability was inspected.
- **Coverage assertion:** statement scoped to an exact venue, market, symbol, interval, data family and time window.

## Three practical data levels

This repository uses an operational taxonomy; there is no single universal standard that makes these level numbers official:

1. **Level 1 — bars/quotes:** OHLC, OHLCV, candle trade-count fields; clarify whether quote-volume, taker volumes or open interest are included.
2. **Level 2 — market microstructure:** raw trades/ticks, aggregate trades, quote updates and order-book depth/snapshots/deltas. State sampling and sequencing limits.
3. **Level 3 — derived/contract metrics:** funding rates, open interest, liquidations, basis, mark/index/premium prices, venue statistics or vendor-computed indicators. List the actual raw fields rather than relying on the level name.

A dataset can span multiple families. Store field-level definitions and cadence; do not assume that every product labeled Level 2 includes a full reconstructable order book.

## Canonical instrument identity

Use a stable internal `instrument_id` and preserve provider symbols verbatim. Recommended fields:

```json
{
  "instrument_id": "venue:market:base-quote:contract",
  "venue_id": "binance",
  "market_type": "spot",
  "provider_symbol": "BTCUSDT",
  "base_asset": "BTC",
  "quote_asset": "USDT",
  "settlement_asset": null,
  "contract_type": null,
  "linear_or_inverse": null,
  "listing_time_utc": null,
  "delisting_time_utc": null,
  "symbol_mapping_state": "unverified"
}
```

The sample is illustrative. Do not assume the symbol exists at every exchange, in every market or in every time period. Symbol reuse, migrations and delisted pairs require lifecycle records.

## Time rules

- Persist all timestamps in UTC.
- Store original integer timestamps and their declared unit when available; do not guess seconds vs milliseconds vs microseconds.
- Record candle-open and candle-close semantics explicitly.
- Fixed intervals and calendar intervals are different. `1mo` is a calendar month, not a fixed count of seconds.
- Record week anchor and session boundary when provider conventions differ.
- Missing candles can mean no trades, omitted empty intervals, listing before first trade, delisting, archival gaps or a retrieval failure. Never translate every gap to data loss without evidence.

## Count semantics

Every count should identify its exact grain: rows, candles, trades, files, bytes or time buckets. A derived *expected bucket count* is not the same as observed candle rows. For fixed interval duration `Δ` and an inclusive/exclusive range convention, the idealized bucket count is computed only after defining the range and anchor. Actual source rows must be counted independently.
