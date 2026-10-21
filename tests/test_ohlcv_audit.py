"""Regression tests for the local, network-free OHLCV audit helper."""
from __future__ import annotations
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_ohlcv import audit_file, parse_interval_seconds, parse_timestamp


class OHLCVAuditTests(unittest.TestCase):
    def write_csv(self, root: Path, rows: list[list[str]]) -> Path:
        path = root / "sample.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerows(rows)
        return path

    def test_duplicate_timestamps_ohlc_and_volume_are_reported(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_csv(Path(td), [
                ["timestamp", "open", "high", "low", "close", "volume"],
                ["1700000000", "1", "2", "0.5", "1.5", "10"],
                ["1700000060", "1.5", "2", "1", "1.8", "11"],
                ["1700000060", "1.5", "2", "1", "1.8", "12"],
                ["1700000240", "1.8", "1.7", "1.6", "2.0", "-1"],
            ])
            result = audit_file(path, 60, "auto", "reject")[0]
            self.assertEqual(result["rows_observed_excluding_header"], 4)
            self.assertEqual(result["unique_timestamp_count"], 3)
            self.assertEqual(result["duplicate_timestamp_rows"], 1)
            self.assertEqual(result["invalid_ohlc_rows"], 1)
            self.assertEqual(result["invalid_or_negative_volume_rows"], 1)
            self.assertEqual(result["observed_timestamp_gaps_over_interval"], 1)
            self.assertEqual(result["aligned_missing_bucket_candidates"], 2)
            self.assertEqual(len(result["sha256_on_disk"]), 64)

    def test_naive_iso_timestamp_is_rejected_unless_utc_assumption_is_explicit(self):
        _, error, mode = parse_timestamp("2026-01-01T00:00:00", "auto", "reject")
        self.assertEqual(error, "NAIVE_DATETIME_REQUIRES_EXPLICIT_UTC_ASSUMPTION")
        self.assertEqual(mode, "iso_naive")
        dt, error, mode = parse_timestamp("2026-01-01T00:00:00", "auto", "UTC")
        self.assertIsNone(error)
        self.assertEqual(mode, "iso_naive_assumed_utc")
        self.assertEqual(dt.isoformat(), "2026-01-01T00:00:00+00:00")

    def test_offset_timestamp_is_normalized_to_utc(self):
        dt, error, _ = parse_timestamp("2026-01-01T03:00:00+03:00", "auto", "reject")
        self.assertIsNone(error)
        self.assertEqual(dt.isoformat(), "2026-01-01T00:00:00+00:00")

    def test_fixed_intervals_are_case_sensitive_and_calendar_month_is_not_fixed(self):
        self.assertEqual(parse_interval_seconds("1m", None), 60)
        with self.assertRaises(ValueError):
            parse_interval_seconds("1M", None)
        with self.assertRaises(ValueError):
            parse_interval_seconds("1mo", None)

    def test_empty_candle_policy_is_not_inferred_from_a_gap(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_csv(Path(td), [
                ["timestamp", "open", "high", "low", "close"],
                ["1700000000", "1", "2", "0.5", "1.5"],
                ["1700000180", "1.5", "2", "1", "1.8"],
            ])
            result = audit_file(path, 60, "auto", "reject")[0]
            self.assertEqual(result["aligned_missing_bucket_candidates"], 2)
            self.assertTrue(any("may omit empty/no-trade candles" in note for note in result["limitations"]))


if __name__ == "__main__":
    unittest.main()
