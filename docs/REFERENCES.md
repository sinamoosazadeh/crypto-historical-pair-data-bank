# Primary references and discovery sources

This page records high-value public references used to seed the research inventory. It is not a claim that every linked object has been downloaded, that all symbols and partitions exist, or that all access controls were tested anonymously. Recheck current terms and exact object paths before using or redistributing any dataset.

## Official or provider-owned archive references

1. **Binance Public Data repository** — https://github.com/binance/binance-public-data
   - Documents public downloadable data, file layouts, checksums, and product-specific paths.
   - Public archive landing/index: https://data.binance.vision/
   - Caveat: the symbol, market, interval, and date partition must be checked individually. Timestamp units can vary by product and time period.

2. **Kraken OHLCVT archive documentation** — https://support.kraken.com/in/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data
   - Documents downloadable open/high/low/close/volume/trade-count files and the provider's interval set.
   - SHA-256 list linked from the provider archive: https://assets.kraken.com/marketing/institutions/OHLCVT_Full_PARTS_SHA256SUMS.txt
   - Caveat: empty/no-trade periods may be omitted. Multipart archives must be assembled and checked with the provided checksums.

3. **Kraken time-and-sales archive documentation** — https://support.kraken.com/articles/360047543791-downloadable-historical-market-data-time-and-sales-
   - Documents raw trade history, full archive distribution and quarterly update files.
   - Example quarter file: https://assets.kraken.com/marketing/institutions/Kraken_Trades_2026Q1.zip
   - Caveat: trades are raw events, not candles. Derived candle outputs must document aggregation, timezone, and empty-bar rules.

4. **OKX Historical Market Data** — https://www.okx.com/historical-data
   - A portal for several market-data families, including candle and order-book products.
   - Caveat: each download's login, cost, instrument coverage, and file-level behavior must be verified. Portal visibility is not proof of qualifying anonymous access.

5. **Bybit public data root** — https://public.bybit.com/
   - Discovery entry point for public archive paths.
   - Caveat: a root directory is not a validated pair/timeframe inventory and raw trade files are not prebuilt candles.

## Third-party and community archives

6. **CryptoDataDownload** — https://www.cryptodatadownload.com/data/
   - The public site describes historical CSV files, daily/hourly/1-minute products, and multiple market sources.
   - Caveat: public landing pages do not prove anonymous access for each symbol and file. Verify per-file requirements and the stated CC BY-NC-SA 4.0 terms before reuse.

7. **Speirsy11/crypto-dataset** — https://github.com/Speirsy11/crypto-dataset
   - A public Binance-derived Parquet mirror. Its README snapshot has published symbol, interval, file, and candle statistics.
   - Caveat: published totals are dynamic and were not independently recounted in the seed research. Check the current data license and scope.

8. **TradeMonkey-io/historic-crypto-data** — https://github.com/TradeMonkey-io/historic-crypto-data
   - A public community repository described as daily-partitioned 1-minute market data.
   - Caveat: current activity, exact file count, date completeness, and repository license need a separate audit.

9. **Hyperliquid data tooling** — https://github.com/bond-labs-dev/hyperliquid-data
   - Useful discovery tooling for historical data and archive paths.
   - Caveat: some S3 paths can be requester-pays, so public does not necessarily mean zero-cost. Test each path and record potential charges.

10. **CryptoArchive** — https://www.cryptoarchive.com.au/
    - A third-party exchange-resolved market-history candidate; the seed research contains a publisher-displayed BCH/USDT 1-minute count.
    - Caveat: that number was not independently recounted from a locally downloaded raw file. Do not present it as an independently measured row total.

11. **Coin Metrics public data repository** — https://github.com/coinmetrics/data
    - A complementary public data repository for selected asset-level metrics.
    - Caveat: asset-level metrics are not a substitute for exact exchange-symbol candles.

12. **Coin Metrics market-candles download service** — https://download.coinmetrics.io/market-candles
    - A candidate for additional market data.
    - Caveat: account, key, and product gating are not established here; it remains outside the strict anonymous-static-download tier until proven otherwise.

## Method for citing these sources

Each promoted artifact should cite the exact source page and direct file URL, capture the UTC observation time, save a checksum, inspect the actual file, count rows with a versioned method, and record license/terms evidence. A link in this list is a research pointer, not a guarantee of current availability.
