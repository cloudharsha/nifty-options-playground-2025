"""Guards for the Sleeve A pieces that silently rescale every reported number.

The engine's trade logic shows up in the cycle and leg CSVs, so a mistake there
is visible. The cost stack, the lot-size eras, the sizing formula and the VIX
lookback are not visible in the output at all - they just move the P/L. These
are the tests for those.
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import logging
import sys
import unittest
from pathlib import Path


MODULE_PATH = (Path(__file__).resolve().parents[1] / "adjusted-straddle-sleeve-a"
               / "run_adjusted_straddle_sleeve_a_2020_2026.py")
SPEC = importlib.util.spec_from_file_location("run_adjusted_straddle_sleeve_a", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def cost_args(**overrides) -> argparse.Namespace:
    """The cost-relevant defaults, matching parse_args."""
    base = dict(
        brokerage_per_order=20.0,
        exchange_rate=0.0003503,
        sebi_rate=0.000001,
        stamp_rate=0.00003,
        gst_rate=0.18,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


class SttEraTests(unittest.TestCase):
    def test_boundaries_are_the_statutory_dates(self):
        # 0.05% -> 0.0625% (2023-04-01) -> 0.10% (2024-10-01) -> 0.15% (2026-04-01)
        for date, expected in [
            ("2020-01-02", 0.000500),
            ("2023-03-31", 0.000500),
            ("2023-04-01", 0.000625),
            ("2024-09-30", 0.000625),
            ("2024-10-01", 0.001000),
            ("2026-03-31", 0.001000),
            ("2026-04-01", 0.001500),
        ]:
            with self.subTest(date=date):
                self.assertAlmostEqual(MODULE.stt_sell_rate(date), expected, places=9)


class OrderCostTests(unittest.TestCase):
    def test_sell_order_charges_stt_but_not_stamp(self):
        # price 100, 75 qty -> Rs 7,500 turnover, on a 0.10% STT date.
        got = MODULE.order_cost(cost_args(), 100.0, 75, True, "2025-01-02")
        exchange, sebi, stt = 0.0003503 * 7500, 0.000001 * 7500, 0.001 * 7500
        expected = 20.0 + exchange + sebi + stt + 0.18 * (20.0 + exchange + sebi)
        self.assertAlmostEqual(got, expected, places=6)
        self.assertAlmostEqual(got, 34.209005, places=6)

    def test_buy_order_charges_stamp_but_not_stt(self):
        got = MODULE.order_cost(cost_args(), 100.0, 75, False, "2025-01-02")
        exchange, sebi, stamp = 0.0003503 * 7500, 0.000001 * 7500, 0.00003 * 7500
        expected = 20.0 + exchange + sebi + stamp + 0.18 * (20.0 + exchange + sebi)
        self.assertAlmostEqual(got, expected, places=6)
        self.assertAlmostEqual(got, 26.934005, places=6)

    def test_cost_never_goes_negative_on_a_zero_price_fill(self):
        # Deep-OTM legs expire at 0.05-0.10; the slipped buy price stays positive,
        # but guard the floor anyway so a bad quote cannot credit the account.
        self.assertGreaterEqual(MODULE.order_cost(cost_args(), 0.0, 75, False, "2025-01-02"), 20.0)


class LotSizeEraTests(unittest.TestCase):
    def test_era_boundaries_use_the_expiry_date(self):
        for expiry, expected in [
            ("2020-01-02", 75),
            ("2021-10-06", 75),
            ("2021-10-07", 50),
            ("2024-04-25", 50),
            ("2024-05-02", 25),
            ("2024-11-21", 25),
            ("2024-11-28", 75),
            ("2025-12-30", 75),
            ("2026-01-06", 65),
        ]:
            with self.subTest(expiry=expiry):
                self.assertEqual(MODULE.get_lot_size(expiry), expected)


class SizingTests(unittest.TestCase):
    def lots(self, capital, spot, lot, margin):
        return max(1, int(capital // (spot * lot * margin)))

    def test_margin_rate_drives_the_lot_count(self):
        # Rs 10L, Nifty 24000, lot 75: 0.50 blocks Rs 9.0L -> 1 lot;
        # 0.19 blocks Rs 3.42L -> 2 lots.
        self.assertEqual(self.lots(10_00_000, 24000, 75, 0.50), 1)
        self.assertEqual(self.lots(10_00_000, 24000, 75, 0.19), 2)
        # The 25-lot era sizes far larger on the same capital.
        self.assertEqual(self.lots(10_00_000, 24000, 25, 0.50), 3)
        self.assertEqual(self.lots(10_00_000, 24000, 25, 0.19), 8)

    def test_never_sizes_below_one_lot(self):
        self.assertEqual(self.lots(10_00_000, 30000, 75, 0.90), 1)


class StrikeRoundingTests(unittest.TestCase):
    def test_rounds_to_the_nearest_50(self):
        self.assertEqual(MODULE.round_to_50(23629.65), 23650)   # observed 2025-01-01 entry
        self.assertEqual(MODULE.round_to_50(23624.99), 23600)
        self.assertEqual(MODULE.round_to_50(23625.0), 23650)    # exact half rounds up
        self.assertEqual(MODULE.round_to_50(23600.0), 23600)


class PrevVixTests(unittest.TestCase):
    def build_engine(self, vix: dict[str, float]) -> "MODULE.Engine":
        logger = logging.getLogger("sleeve_a_test")
        logger.addHandler(logging.NullHandler())
        empty = MODULE.ContractData(timestamps=[], closes=[])
        return MODULE.Engine(argparse.Namespace(), logger, empty, sorted(vix), vix)

    def test_reads_the_last_session_strictly_before_the_entry_date(self):
        eng = self.build_engine({"2023-07-03": 11.2, "2023-07-04": 13.5, "2023-07-06": 10.9})
        # Never the entry date's own close - that is not known at 09:20.
        self.assertAlmostEqual(eng.prev_vix("2023-07-04"), 11.2)
        # Skips the missing 2023-07-05 back to the previous available session.
        self.assertAlmostEqual(eng.prev_vix("2023-07-06"), 13.5)
        self.assertAlmostEqual(eng.prev_vix("2023-07-07"), 10.9)

    def test_returns_none_before_the_series_starts(self):
        eng = self.build_engine({"2023-07-03": 11.2})
        self.assertIsNone(eng.prev_vix("2023-07-03"))
        self.assertIsNone(eng.prev_vix("2020-01-01"))


class PriceLookupTests(unittest.TestCase):
    def test_marks_a_carried_forward_bar_as_stale(self):
        data = MODULE.ContractData(
            timestamps=["2025-01-02T09:20:00+05:30", "2025-01-02T09:22:00+05:30"],
            closes=[100.0, 110.0],
        )
        self.assertEqual(MODULE.price_at(data, "2025-01-02T09:20:00+05:30"), (100.0, False))
        self.assertEqual(MODULE.price_at(data, "2025-01-02T09:21:00+05:30"), (100.0, True))
        self.assertEqual(MODULE.price_at(data, "2025-01-02T09:22:00+05:30"), (110.0, False))
        self.assertIsNone(MODULE.price_at(data, "2025-01-02T09:19:00+05:30"))


class ExpirySuffixTests(unittest.TestCase):
    def test_matches_the_dataset_filename_convention(self):
        self.assertEqual(MODULE.expiry_suffix("2025-01-02"), "02_JAN_25")
        self.assertEqual(MODULE.expiry_suffix("2020-12-31"), "31_DEC_20")


class CycleScheduleTests(unittest.TestCase):
    def test_entry_is_the_session_after_the_previous_expiry(self):
        days = ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-06",
                "2025-01-07", "2025-01-08", "2025-01-09"]
        expiries = ["2025-01-02", "2025-01-09"]
        schedule = MODULE.build_expiry_cycles(days, expiries)
        self.assertEqual(len(schedule), 2)
        # Second cycle opens the day after the first expiry and runs to the next.
        entry, exit_, expiry, sessions = schedule[1]
        self.assertEqual((entry, exit_, expiry), ("2025-01-03", "2025-01-09", "2025-01-09"))
        self.assertEqual(sessions[0], "2025-01-03")
        self.assertEqual(sessions[-1], "2025-01-09")
        # No overlap: the first cycle ends where the second has not yet begun.
        self.assertLess(schedule[0][1], schedule[1][0])

    def test_ignores_expiries_with_no_trading_day_in_the_window(self):
        days = ["2025-01-02", "2025-01-03"]
        schedule = MODULE.build_expiry_cycles(days, ["2025-01-02", "2027-12-28"])
        self.assertEqual(len(schedule), 1)


if __name__ == "__main__":
    unittest.main()
