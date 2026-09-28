"""
Tests for the opening-range-breakout runner.

The two things most likely to be wrong here are the opening-range window
boundary (a bar stamped T closes at T+5) and the rule that direction comes from
whichever side breaks FIRST, not from where the day ended up.

Run directly:

    python backtesting/python/tests/test_run_opening_range_breakout.py
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = (Path(__file__).resolve().parents[1] / "directional-intraday"
               / "run_opening_range_breakout_2020_2026.py")
SPEC = importlib.util.spec_from_file_location("run_orb", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)

DAY = "2025-01-16"


def session(day: str, bars):
    rows, order = {}, []
    for hhmm, o, h, l, c in bars:
        ts = MOD.build_ts(day, hhmm)
        rows[ts] = MOD.PriceRow(ts, float(o), float(h), float(l), float(c))
        order.append(ts)
    return rows, order


def flat_day(day: str, n: int = 75):
    bars = []
    for i in range(n):
        mins = 9 * 60 + 15 + 5 * i
        bars.append((f"{mins//60:02d}:{mins%60:02d}", 100, 100, 100, 100))
    return session(day, bars)


class OpeningRangeWindowTests(unittest.TestCase):
    """A bar stamped T covers [T, T+5). The boundary bar is NOT inside."""

    def setUp(self):
        _, self.order = flat_day(DAY)

    def test_30_minute_range_ends_at_the_0940_bar(self):
        bars = MOD.opening_range_bars(self.order, 30)
        self.assertEqual(MOD.ts_time(bars[0]), "09:15")
        self.assertEqual(MOD.ts_time(bars[-1]), "09:40")
        self.assertEqual(len(bars), 6)

    def test_the_boundary_bar_is_excluded(self):
        """09:45 covers 09:45-09:50, which is beyond a 30-minute window."""
        bars = MOD.opening_range_bars(self.order, 30)
        self.assertNotIn(MOD.build_ts(DAY, "09:45"), bars)

    def test_15_minute_range_is_three_bars_ending_0925(self):
        bars = MOD.opening_range_bars(self.order, 15)
        self.assertEqual(len(bars), 3)
        self.assertEqual(MOD.ts_time(bars[-1]), "09:25")

    def test_60_minute_range_is_twelve_bars_ending_1010(self):
        bars = MOD.opening_range_bars(self.order, 60)
        self.assertEqual(len(bars), 12)
        self.assertEqual(MOD.ts_time(bars[-1]), "10:10")


class BreakoutDirectionTests(unittest.TestCase):
    """Direction is the FIRST break in time order."""

    def build(self, post_bars):
        bars = [("09:15", 100, 110, 90, 100),
                ("09:20", 100, 110, 90, 100),
                ("09:25", 100, 110, 90, 100),
                ("09:30", 100, 110, 90, 100),
                ("09:35", 100, 110, 90, 100),
                ("09:40", 100, 110, 90, 100)] + post_bars
        rows, order = session(DAY, bars)
        return rows, order, MOD.opening_range_bars(order, 30)

    def test_close_mode_enters_on_the_next_bar(self):
        rows, order, rb = self.build([
            ("09:45", 100, 115, 99, 112),     # closes above 110
            ("09:50", 113, 118, 112, 117),    # entry here, at its OPEN
        ])
        side, ts, px, intrabar = MOD.find_breakout(rows, order, rb, 110, 90,
                                                   "close", MOD.build_ts(DAY, "14:00"))
        self.assertEqual(side, "up")
        self.assertEqual(MOD.ts_time(ts), "09:50")
        self.assertAlmostEqual(px, 113.0)
        self.assertFalse(intrabar)

    def test_a_bar_that_pokes_above_but_closes_inside_is_not_a_close_break(self):
        rows, order, rb = self.build([
            ("09:45", 100, 120, 99, 105),     # high above 110, close inside
            ("09:50", 105, 108, 102, 106),
        ])
        got = MOD.find_breakout(rows, order, rb, 110, 90, "close",
                                MOD.build_ts(DAY, "14:00"))
        self.assertIsNone(got)

    def test_the_first_break_wins_even_when_the_day_reverses(self):
        """Down first, then a much bigger move up. Must still be short."""
        rows, order, rb = self.build([
            ("09:45", 100, 101, 80, 85),      # closes BELOW 90 first
            ("09:50", 85, 86, 84, 85),
            ("09:55", 85, 200, 84, 190),      # huge up-move later
            ("10:00", 190, 195, 185, 192),
        ])
        side, ts, px, _ = MOD.find_breakout(rows, order, rb, 110, 90, "close",
                                            MOD.build_ts(DAY, "14:00"))
        self.assertEqual(side, "down")
        self.assertEqual(MOD.ts_time(ts), "09:50")

    def test_touch_mode_fills_at_the_level(self):
        rows, order, rb = self.build([
            ("09:45", 100, 115, 99, 112),     # trades through 110 intrabar
        ])
        side, ts, px, intrabar = MOD.find_breakout(rows, order, rb, 110, 90,
                                                   "touch", MOD.build_ts(DAY, "14:00"))
        self.assertEqual(side, "up")
        self.assertEqual(MOD.ts_time(ts), "09:45")
        self.assertAlmostEqual(px, 110.0)
        self.assertTrue(intrabar)

    def test_touch_mode_gap_through_fills_at_the_bar_open(self):
        rows, order, rb = self.build([
            ("09:45", 130, 135, 128, 132),    # opened clean above 110
        ])
        side, ts, px, intrabar = MOD.find_breakout(rows, order, rb, 110, 90,
                                                   "touch", MOD.build_ts(DAY, "14:00"))
        self.assertAlmostEqual(px, 130.0)
        self.assertFalse(intrabar)

    def test_no_break_before_the_cutoff_is_no_trade(self):
        rows, order, rb = self.build([
            ("09:45", 100, 105, 95, 100),
            ("14:05", 100, 200, 50, 190),     # breaks, but after the cutoff
        ])
        got = MOD.find_breakout(rows, order, rb, 110, 90, "close",
                                MOD.build_ts(DAY, "14:00"))
        self.assertIsNone(got)

    def test_range_bars_themselves_never_trigger_a_break(self):
        """The range is built FROM those bars; they cannot also break it."""
        rows, order, rb = self.build([])
        got = MOD.find_breakout(rows, order, rb, 110, 90, "close",
                                MOD.build_ts(DAY, "14:00"))
        self.assertIsNone(got)


class SpotLegTests(unittest.TestCase):
    def setUp(self):
        self.entry_ts = MOD.build_ts(DAY, "09:50")
        self.exit_ts = MOD.build_ts(DAY, "15:20")

    def test_a_bar_holding_both_stop_and_target_resolves_to_the_stop(self):
        rows, order = session(DAY, [
            ("09:50", 100, 100, 100, 100),
            ("09:55", 100, 140, 80, 100),
            ("15:20", 100, 100, 100, 100),
        ])
        out = MOD.resolve_spot_leg(rows, order, self.entry_ts, self.exit_ts,
                                   100.0, 1, 90.0, 130.0, skip_entry_bar=False)
        self.assertEqual(out.exit_reason, "sl")

    def test_touch_entry_does_not_stop_out_on_its_own_bar(self):
        """That bar's low partly precedes the entry and cannot trigger the stop."""
        rows, order = session(DAY, [
            ("09:50", 100, 115, 85, 112),     # low 85 is below the 90 stop
            ("09:55", 112, 118, 111, 117),
            ("15:20", 120, 120, 120, 120),
        ])
        out = MOD.resolve_spot_leg(rows, order, self.entry_ts, self.exit_ts,
                                   110.0, 1, 90.0, 200.0, skip_entry_bar=True)
        self.assertEqual(out.exit_reason, "day_close")

    def test_without_the_skip_that_same_bar_would_stop_it_out(self):
        rows, order = session(DAY, [
            ("09:50", 100, 115, 85, 112),
            ("15:20", 120, 120, 120, 120),
        ])
        out = MOD.resolve_spot_leg(rows, order, self.entry_ts, self.exit_ts,
                                   110.0, 1, 90.0, 200.0, skip_entry_bar=False)
        self.assertEqual(out.exit_reason, "sl")

    def test_short_side_mirrors(self):
        rows, order = session(DAY, [
            ("09:50", 100, 100, 100, 100),
            ("09:55", 100, 101, 85, 88),
            ("15:20", 88, 88, 88, 88),
        ])
        out = MOD.resolve_spot_leg(rows, order, self.entry_ts, self.exit_ts,
                                   100.0, -1, 110.0, 90.0, skip_entry_bar=False)
        self.assertEqual(out.exit_reason, "target")
        self.assertAlmostEqual(out.points, 10.0)

    def test_a_bar_after_the_exit_never_resolves_the_leg(self):
        rows, order = session(DAY, [
            ("09:50", 100, 100, 100, 100),
            ("15:20", 101, 101, 101, 101),
            ("15:25", 101, 300, 10, 200),
        ])
        out = MOD.resolve_spot_leg(rows, order, self.entry_ts, self.exit_ts,
                                   100.0, 1, 90.0, 130.0, skip_entry_bar=False)
        self.assertEqual(out.exit_reason, "day_close")


class OptionTimingTests(unittest.TestCase):
    def setUp(self):
        _, self.order = flat_day(DAY)

    def test_intrabar_exit_sells_the_option_on_the_next_bar(self):
        trigger = MOD.build_ts(DAY, "10:00")
        self.assertEqual(MOD.ts_time(MOD.option_exit_timestamp(trigger, "sl", self.order)),
                         "10:05")

    def test_open_based_exits_keep_the_same_bar(self):
        trigger = MOD.build_ts(DAY, "10:00")
        for reason in ("gap_sl", "gap_target", "day_close"):
            with self.subTest(reason=reason):
                self.assertEqual(MOD.option_exit_timestamp(trigger, reason, self.order),
                                 trigger)

    def test_next_bar_on_the_last_bar_returns_itself(self):
        self.assertEqual(MOD.next_bar(self.order[-1], self.order), self.order[-1])

    def test_option_rejects_an_exit_before_its_entry(self):
        status, a, b = MOD.price_option(Path("."), "2025-01-16", 23000, "CE",
                                        MOD.build_ts(DAY, "10:00"),
                                        MOD.build_ts(DAY, "09:50"), {})
        self.assertEqual(status, "exit_before_entry")


class SessionAndLotTests(unittest.TestCase):
    def test_short_sessions_are_rejected(self):
        _, order = flat_day(DAY, n=12)
        self.assertFalse(MOD.is_normal_session(order))

    def test_full_sessions_are_accepted(self):
        _, order = flat_day(DAY)
        self.assertTrue(MOD.is_normal_session(order))

    def test_lot_size_eras(self):
        for expiry, expected in [("2020-01-02", 75), ("2021-10-07", 50),
                                 ("2024-05-02", 25), ("2024-11-28", 75),
                                 ("2026-01-06", 65)]:
            with self.subTest(expiry=expiry):
                self.assertEqual(MOD.lot_size_for(expiry), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
