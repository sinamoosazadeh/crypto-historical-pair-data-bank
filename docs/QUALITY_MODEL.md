# Evidence and data-quality model

## Separate capability from verification

A provider page that describes 1-minute klines proves documented capability at the page's scope; it does not prove that `FOO/BAR` exists, that its earliest month is downloadable, or that every monthly file is complete.

Use separate fields for:

- `capability_status`: documented / not_documented / unknown;
- `listing_status`: observed / not_found / not_checked;
- `download_status`: anonymous_success / login_required / key_required / paid / failed / not_checked;
- `content_status`: schema_inspected / rows_counted / cross_checked / not_checked;
- `terms_status`: reviewed / ambiguous / redistribution_prohibited / not_checked;
- `freshness_status`: current / stale / expired / not_checked.

## Recommended evidence ladder

1. Search result or secondary claim — discovery hint only.
2. Provider documentation — documented capability.
3. Exact directory/object listing — a listing was seen.
4. Unauthenticated direct request — download path checked at a timestamp.
5. File metadata — size, checksum, content type, compression validated.
6. Content inspected — fields and timestamps read.
7. Rows counted — exact file and method recorded.
8. Independent cross-check — second path/tool/method compared.

Keep the highest reached state per evidence dimension, not a single universal confidence score.

## Minimum artifact manifest

For each concrete file, capture: source_id, venue, market_type, provider_symbol, dataset_family, interval, partition_key, canonical_url, final_url, checked_at_utc, HTTP status, bytes, ETag or Last-Modified if available, checksum algorithm/value, format, compression, schema_version, row_count, row-count method, first/last timestamp, timestamp unit, duplicate count, malformed row count and license/terms reference.

## Data-quality checks

- required columns and data types;
- monotonic timestamps where expected;
- duplicates under a documented uniqueness key;
- invalid OHLC relationships (`low <= min(open, close) <= max(open, close) <= high` subject to source semantics);
- nonnegative volume/trade count when the schema expects it;
- integer timestamp unit and UTC parse correctness;
- observed first/last timestamp vs manifest;
- expected interval gaps reported separately from actual missing source rows;
- checksum and decompression integrity;
- source licensing and attribution policy.

## Confidence display

Avoid labels such as “100% complete” unless the denominator, expected schedule, source lifecycle and exceptions are all defined. Prefer concrete claims such as “38 monthly files listed; 38 downloaded; 38 parsed; 18,423,991 rows; 0 parse failures; 4 calendar gaps retained”.
