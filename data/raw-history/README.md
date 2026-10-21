# Raw historical data policy

Bulk candle, trade, and order-book data is not embedded in this repository by default. It can be large, continuously updated, and governed by provider-specific terms. The catalogue should prefer direct upstream download links and immutable file manifests over copying data without redistribution review.

A future raw-data artifact must have:

- an exact provider, market, instrument, interval / dataset family, and UTC date partition;
- canonical source and direct-download URLs;
- anonymous-access result and observation timestamp in UTC;
- content length, format, compression, schema version, and SHA-256;
- row count and deterministic count method for tabular artifacts;
- first and last timestamps, timestamp unit, monotonicity checks, duplicate / malformed row counts, and a gap policy;
- license / terms evidence and an explicit redistribution decision.

Do not store API secrets, private account exports, or data obtained in violation of access controls. Do not describe a calculated calendar capacity as observed record count.
