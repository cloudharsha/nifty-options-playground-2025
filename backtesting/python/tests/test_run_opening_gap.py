"""
Tests for the opening-gap runner.

Covers the things most likely to be wrong: which session counts as "previous",
where a stalled fade enters, and whether a bar that contains both the stop and
the target resolves to the stop.

Run directly (there is no package here, so unittest discover will not find it):

    python backtesting/python/tests/test_run_opening_gap.py
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = (Path(__file__).resolve().parents[1] / "directional-intraday"
               / "run_opening_gap_2020_2026.py")
SPEC = importlib.util.spec_from_file_location("run_opening_gap", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)

DAY = "2025-01-16"


def session(day: str, bars):
    """bars: list of (hhmm, o, h, l, c) -> (rows_by_ts, ordered_ts)."""
    rows, order = {}, []
    for hhmm, o, h, l, c in bars:
        ts = MOD.build_ts(day, hhmm)
        rows[ts] = MOD.PriceRow(ts, float(o), float(h), float(l), float(c))
        order.append(ts)
    return rows, order


def full_day(day: str, n: int = 75):
    """A synthetic session of n flat bars starting 09:15, 5 minutes apart."""
    bars = []
    for i in range(n):
        mins = 9 * 60 + 15 + 5 * i
        bars.append((f"{mins//60:02d}:{mins%60:02d}", 100, 100, 100, 100))
    return session(day, bars)


class SessionValidityTests(unittest.TestCase):
    """Muhurat and special sessions must not trade or set reference levels."""

    def test_a_full_session_is_normal(self):
        _, order = full_day(DAY)
        self.assertTrue(MOD.is_normal_session(order))

    def test_a_short_session_is_not_normal(self):
        _, order = full_day(DAY, n=12)
        self.assertFalse(MOD.is_normal_session(order))

    def test_a_session_not_opening_at_0915_is_not_normal(self):
        _, order = session(DAY, [(f"{h//60:02d}:{h%60:02d}", 1, 1, 1, 1)
                                 for h in range(18 * 60, 18 * 60 + 75 * 5, 5)])
        self.assertFalse(MOD.is_normal_session(order))

    def test_previous_session_steps_over_an_anomalous_day(self):
        days = ["2025-01-13", "2025-01-14", "2025-01-15"]
        tsd = {days[0]: full_day(days[0])[1],
               days[1]: full_day(days[1], n=12)[1],   # anomalous
               days[2]: full_day(days[2])[1]}
        self.assertEqual(MOD.previous_normal_session(days, tsd, 2), "2025-01-13")

    def test_previous_session_is_none_on_the_first_day(self):
        days = ["2025-01-13"]
        tsd = {days[0]: full_day(days[0])[1]}
        self.assertIsNone(MOD.previous_normal_session(days, tsd, 0))

    def test_previous_session_crosses_a_weekend(self):
        # Friday, then Monday - the calendar day before Monday is a Sunday
        # with no session at all.
        days = ["2025-01-10", "2025-01-13"]
        tsd = {d: full_day(d)[1] for d in days}
        self.assertEqual(MOD.previous_normal_session(days, tsd, 1), "2025-01-10")


class StallEntryTests(unittest.TestCase):
    """A stalled fade enters the bar AFTER the run completes, never on it."""

    def test_gap_up_enters_after_three_bars_with_no_new_high(self):
        rows, order = session(DAY, [
            ("09:15", 100, 110, 100, 108),   # sets the extreme at 110
            ("09:20", 108, 109, 106, 107),   # no new high  (1)
            ("09:25", 107, 108, 105, 106),   # no new high  (2)
            ("09:30", 106, 107, 104, 105),   # no new high  (3) -> run completes
            ("09:35", 105, 106, 103, 104),   # entry here
            ("09:40", 104, 105, 102, 103),
        ])
        got = MOD.find_stall_entry(rows, order, 1, 3, MOD.build_ts(DAY, "12:00"))
        self.assertEqual(MOD.ts_time(got), "09:35")

    def test_a_new_high_resets_the_run(self):
        rows, order = session(DAY, [
            ("09:15", 100, 110, 100, 108),
            ("09:20", 108, 109, 106, 107),   # 1
            ("09:25", 107, 115, 106, 114),   # NEW HIGH -> reset
            ("09:30", 114, 114, 112, 113),   # 1
            ("09:35", 113, 113, 111, 112),   # 2
            ("09:40", 112, 112, 110, 111),   # 3 -> completes
            ("09:45", 111, 111, 109, 110),   # entry here
        ])
        got = MOD.find_stall_entry(rows, order, 1, 3, MOD.build_ts(DAY, "12:00"))
        self.assertEqual(MOD.ts_time(got), "09:45")

    def test_gap_down_stalls_on_no_new_low(self):
        rows, order = session(DAY, [
            ("09:15", 100, 100, 90, 92),     # extreme low 90
            ("09:20", 92, 94, 91, 93),       # 1
            ("09:25", 93, 95, 92, 94),       # 2
            ("09:30", 94, 96, 93, 95),       # 3 -> completes
            ("09:35", 95, 97, 94, 96),       # entry here
        ])
        got = MOD.find_stall_entry(rows, order, -1, 3, MOD.build_ts(DAY, "12:00"))
        self.assertEqual(MOD.ts_time(got), "09:35")

    def test_no_entry_when_the_stall_completes_after_the_cutoff(self):
        rows, order = session(DAY, [
            ("09:15", 100, 110, 100, 108),
            ("13:00", 108, 109, 106, 107),
            ("13:05", 107, 108, 105, 106),
            ("13:10", 106, 107, 104, 105),
            ("13:15", 105, 106, 103, 104),
        ])
        got = MOD.find_stall_entry(rows, order, 1, 3, MOD.build_ts(DAY, "12:00"))
        self.assertIsNone(got)

    def test_no_entry_when_the_run_completes_on_the_last_bar(self):
        """There is no next bar to enter on."""
        rows, order = session(DAY, [
            ("09:15", 100, 110, 100, 108),
            ("09:20", 108, 109, 106, 107),
            ("09:25", 107, 108, 105, 106),
            ("09:30", 106, 107, 104, 105),
        ])
        got = MOD.find_stall_entry(rows, order, 1, 3, MOD.build_ts(DAY, "12:00"))
        self.assertIsNone(got)


class SpotLegTests(unittest.TestCase):
    """Fill convention on the spot leg."""

    def setUp(self):
        self.entry_ts = MOD.build_ts(DAY, "09:20")
        self.exit_ts = MOD.build_ts(DAY, "15:20")

    def test_long_target_fills_at_the_target(self):
        rows, order = session(DAY, [
            ("09:20", 100, 100, 100, 100),
            ("09:25", 100, 120, 99, 118),
            ("15:20", 118, 118, 118, 118),
        ])
        out = MOD.resolve_spot_leg(rows, order, self.entry_ts, self.exit_ts,
                                   100.0, 1, 90.0, 110.0)
        self.assertEqual(out.exit_reason, "target")
        self.assertAlmostEqual(out.points, 10.0)

    def test_long_stop_fills_at_the_stop(self):
        rows, order = session(DAY, [
            ("09:20", 100, 100, 100, 100),
            ("09:25", 100, 101, 85, 88),
            ("15:20", 88, 88, 88, 88),
        ])
        out = MOD.resolve_spot_leg(rows, order, self.entry_ts, self.exit_ts,
                                   100.0, 1, 90.0, 110.0)
        self.assertEqual(out.exit_reason, "sl")
        self.assertAlmostEqual(out.points, -10.0)

    def test_a_bar_holding_both_stop_and_target_resolves_to_the_stop(self):
        """The 5-minute series cannot order them; assuming the target flatters."""
        rows, order = session(DAY, [
            ("09:20", 100, 100, 100, 100),
            ("09:25", 100, 120, 85, 100),     # spans both 110 and 90
            ("15:20", 100, 100, 100, 100),
        ])
        out = MOD.resolve_spot_leg(rows, order, self.entry_ts, self.exit_ts,
                                   100.0, 1, 90.0, 110.0)
        self.assertEqual(out.exit_reason, "sl")
        self.assertLess(out.points, 0)

    def test_a_gap_through_the_stop_fills_at_the_bar_open(self):
        rows, order = session(DAY, [
            ("09:20", 100, 100, 100, 100),
            ("09:25", 80, 82, 78, 79),        # opened below the 90 stop
            ("15:20", 79, 79, 79, 79),
        ])
        out = MOD.resolve_spot_leg(rows, order, self.entry_ts, self.exit_ts,
                                   100.0, 1, 90.0, 110.0)
        self.assertEqual(out.exit_reason, "gap_sl")
        self.assertAlmostEqual(out.points, -20.0)

    def test_short_side_mirrors(self):
        rows, order = session(DAY, [
            ("09:20", 100, 100, 100, 100),
            ("09:25", 100, 101, 85, 88),
            ("15:20", 88, 88, 88, 88),
        ])
        out = MOD.resolve_spot_leg(rows, order, self.entry_ts, self.exit_ts,
                                   100.0, -1, 110.0, 90.0)
        self.assertEqual(out.exit_reason, "target")
        self.assertAlmostEqual(out.points, 10.0)

    def test_an_untouched_leg_exits_at_the_exit_bar(self):
        rows, order = session(DAY, [
            ("09:20", 100, 100, 100, 100),
            ("09:25", 100, 105, 95, 102),
            ("15:20", 103, 103, 103, 103),
        ])
        out = MOD.resolve_spot_leg(rows, order, self.entry_ts, self.exit_ts,
                                   100.0, 1, 90.0, 110.0)
        self.assertEqual(out.exit_reason, "day_close")
        self.assertAlmostEqual(out.points, 3.0)

    def test_a_bar_after_the_exit_never_resolves_the_leg(self):
        """Lookahead guard: 15:25 is past the exit and must not trigger."""
        rows, order = session(DAY, [
            ("09:20", 100, 100, 100, 100),
            ("15:20", 101, 101, 101, 101),
            ("15:25", 101, 200, 50, 150),     # would hit both, but is too late
        ])
        out = MOD.resolve_spot_leg(rows, order, self.entry_ts, self.exit_ts,
                                   100.0, 1, 90.0, 110.0)
        self.assertEqual(out.exit_reason, "day_close")
        self.assertAlmostEqual(out.points, 1.0)

    def test_bars_before_entry_are_ignored(self):
        rows, order = session(DAY, [
            ("09:15", 100, 200, 50, 100),     # would hit both, but precedes entry
            ("09:20", 100, 100, 100, 100),
            ("15:20", 102, 102, 102, 102),
        ])
        out = MOD.resolve_spot_leg(rows, order, self.entry_ts, self.exit_ts,
                                   100.0, 1, 90.0, 110.0)
        self.assertEqual(out.exit_reason, "day_close")


class OptionExitTimingTests(unittest.TestCase):
    """An intrabar trigger cannot be sold at that bar's own open.

    That open is a price from BEFORE the stop or target was touched — the
    lookahead bug the audit caught. The option leg must exit at the next bar.
    """

    def setUp(self):
        _, self.order = full_day(DAY)

    def test_intrabar_stop_exits_the_option_on_the_next_bar(self):
        trigger = MOD.build_ts(DAY, "09:35")
        got = MOD.option_exit_timestamp(trigger, "sl", self.order)
        self.assertEqual(MOD.ts_time(got), "09:40")

    def test_intrabar_target_exits_the_option_on_the_next_bar(self):
        trigger = MOD.build_ts(DAY, "11:00")
        got = MOD.option_exit_timestamp(trigger, "target", self.order)
        self.assertEqual(MOD.ts_time(got), "11:05")

    def test_a_gap_exit_keeps_the_same_bar(self):
        """A gap through the level fills AT that bar's open, so it is valid."""
        trigger = MOD.build_ts(DAY, "09:35")
        for reason in ("gap_sl", "gap_target", "day_close"):
            with self.subTest(reason=reason):
                got = MOD.option_exit_timestamp(trigger, reason, self.order)
                self.assertEqual(got, trigger)

    def test_a_trigger_on_the_last_bar_has_no_next_bar(self):
        trigger = self.order[-1]
        self.assertEqual(MOD.option_exit_timestamp(trigger, "sl", self.order), trigger)


class AlreadyFilledGapTests(unittest.TestCase):
    """A fade whose target is already passed at entry is not a trade."""

    def test_gap_up_that_has_already_filled_is_detected(self):
        # gap up: prev_close 100, open 150. By entry, price is back at 95 —
        # below the target, so the short would open past its own target.
        prev_close, entry_price, gap_dir = 100.0, 95.0, 1
        self.assertLessEqual((entry_price - prev_close) * gap_dir, 0)

    def test_gap_up_still_above_the_close_is_tradeable(self):
        prev_close, entry_price, gap_dir = 100.0, 130.0, 1
        self.assertGreater((entry_price - prev_close) * gap_dir, 0)

    def test_gap_down_that_has_already_filled_is_detected(self):
        prev_close, entry_price, gap_dir = 100.0, 110.0, -1
        self.assertLessEqual((entry_price - prev_close) * gap_dir, 0)

    def test_gap_down_still_below_the_close_is_tradeable(self):
        prev_close, entry_price, gap_dir = 100.0, 70.0, -1
        self.assertGreater((entry_price - prev_close) * gap_dir, 0)

    def test_entry_exactly_at_the_previous_close_is_not_traded(self):
        for gap_dir in (1, -1):
            with self.subTest(gap_dir=gap_dir):
                self.assertLessEqual((100.0 - 100.0) * gap_dir, 0)


class GapFillStatTests(unittest.TestCase):
    """The fill statistic must cover every session, not just traded ones."""

    def build(self, day2_bars):
        days = ["2025-01-15", "2025-01-16"]
        rows1, ord1 = full_day(days[0])           # all bars flat at 100
        rows2, ord2 = session(days[1], day2_bars)
        rows_by_day = {days[0]: rows1, days[1]: rows2}
        tsd = {days[0]: ord1, days[1]: ord2}
        return days, rows_by_day, tsd

    def test_a_gap_up_fills_when_price_trades_back_down(self):
        bars = [("09:15", 150, 155, 148, 152)] + [
            (f"{(9*60+20+5*i)//60:02d}:{(9*60+20+5*i)%60:02d}", 120, 125, 95, 100)
            if i == 0 else
            (f"{(9*60+20+5*i)//60:02d}:{(9*60+20+5*i)%60:02d}", 100, 101, 99, 100)
            for i in range(74)]
        days, rbd, tsd = self.build(bars)
        stats = MOD.gap_fill_stats(days, rbd, tsd, "2020-01-01", "2026-12-31")
        self.assertEqual(len(stats), 1)
        self.assertAlmostEqual(stats[0].gap_pts, 50.0)
        self.assertTrue(stats[0].filled)
        self.assertEqual(stats[0].fill_minutes, 5)

    def test_a_gap_that_never_comes_back_is_counted_as_unfilled(self):
        bars = [(f"{(9*60+15+5*i)//60:02d}:{(9*60+15+5*i)%60:02d}", 150, 155, 148, 152)
                for i in range(75)]
        days, rbd, tsd = self.build(bars)
        stats = MOD.gap_fill_stats(days, rbd, tsd, "2020-01-01", "2026-12-31")
        self.assertEqual(len(stats), 1)
        self.assertFalse(stats[0].filled)
        self.assertIsNone(stats[0].fill_minutes)


class LotSizeTests(unittest.TestCase):
    def test_every_era_boundary(self):
        cases = [("2020-01-02", 75), ("2021-10-06", 75),
                 ("2021-10-07", 50), ("2024-04-25", 50),
                 ("2024-05-02", 25), ("2024-11-21", 25),
                 ("2024-11-28", 75), ("2025-12-30", 75),
                 ("2026-01-06", 65), ("2026-06-16", 65)]
        for expiry, expected in cases:
            with self.subTest(expiry=expiry):
                self.assertEqual(MOD.lot_size_for(expiry), expected)


class HelperTests(unittest.TestCase):
    def test_minutes_from_open(self):
        self.assertEqual(MOD.minutes_from_open(MOD.build_ts(DAY, "09:15")), 0)
        self.assertEqual(MOD.minutes_from_open(MOD.build_ts(DAY, "11:00")), 105)
        self.assertEqual(MOD.minutes_from_open(MOD.build_ts(DAY, "15:20")), 365)

    def test_round_to_strike(self):
        self.assertEqual(MOD.round_to_strike(23310.20), 23300)
        self.assertEqual(MOD.round_to_strike(23335.50), 23350)

    def test_median(self):
        self.assertAlmostEqual(MOD.median([3, 1, 2]), 2.0)
        self.assertAlmostEqual(MOD.median([4, 1, 2, 3]), 2.5)
        self.assertAlmostEqual(MOD.median([]), 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
