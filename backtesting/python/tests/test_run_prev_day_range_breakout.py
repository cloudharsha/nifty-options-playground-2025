"""
Tests for the previous-day high/low breakout runner.

The new machinery here is ATR — nothing else in this repo computes one — plus
the retest rule, which the spec flags as a lookahead magnet.

Run directly:

    python backtesting/python/tests/test_run_prev_day_range_breakout.py
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = (Path(__file__).resolve().parents[1] / "directional-intraday"
               / "run_prev_day_range_breakout_2020_2026.py")
SPEC = importlib.util.spec_from_file_location("run_pdh", MODULE_PATH)
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


def spotdata(bars_by_day):
    """bars_by_day: {day: [(hhmm,o,h,l,c), ...]} -> SpotData."""
    days, rbd, tsd, ordered = [], {}, {}, []
    for day in sorted(bars_by_day):
        rows, order = session(day, bars_by_day[day])
        days.append(day)
        rbd[day], tsd[day] = rows, order
        ordered.extend(rows[t] for t in order)
    ordered.sort(key=lambda r: r.timestamp)
    return MOD.SpotData(days, rbd, tsd, ordered,
                        {r.timestamp: i for i, r in enumerate(ordered)})


class TrueRangeTests(unittest.TestCase):
    def test_true_range_uses_the_widest_of_the_three(self):
        row = MOD.PriceRow("x", 100, 110, 95, 105)
        # own range 15; |110-80|=30 is wider
        self.assertAlmostEqual(MOD.true_range(row, 80.0), 30.0)

    def test_gap_down_uses_the_low_against_the_previous_close(self):
        row = MOD.PriceRow("x", 100, 110, 95, 105)
        self.assertAlmostEqual(MOD.true_range(row, 130.0), 35.0)

    def test_without_a_previous_close_it_is_the_bar_range(self):
        row = MOD.PriceRow("x", 100, 110, 95, 105)
        self.assertAlmostEqual(MOD.true_range(row, None), 15.0)

    def test_an_inside_bar_uses_its_own_range(self):
        row = MOD.PriceRow("x", 100, 110, 95, 105)
        self.assertAlmostEqual(MOD.true_range(row, 103.0), 15.0)


class AtrTests(unittest.TestCase):
    def setUp(self):
        # Ten bars, each exactly 10 points high-to-low, closing flat at 100,
        # so every true range is 10 and the ATR must be 10.
        bars = [(f"{(9*60+15+5*i)//60:02d}:{(9*60+15+5*i)%60:02d}", 100, 105, 95, 100)
                for i in range(10)]
        self.spot = spotdata({DAY: bars})
        self.order = self.spot.timestamps_by_day[DAY]

    def test_atr_over_a_uniform_series(self):
        self.assertAlmostEqual(MOD.atr_at(self.spot, self.order[9], 5), 10.0)

    def test_atr_is_none_before_enough_bars_have_closed(self):
        self.assertIsNone(MOD.atr_at(self.spot, self.order[2], 5))

    def test_atr_is_available_exactly_at_the_period_boundary(self):
        self.assertIsNotNone(MOD.atr_at(self.spot, self.order[4], 5))

    def test_atr_is_causal_later_bars_do_not_change_an_earlier_value(self):
        """The decisive property. A huge bar at the end must not affect the
        ATR computed at an earlier timestamp."""
        early = MOD.atr_at(self.spot, self.order[5], 5)
        bars = [(f"{(9*60+15+5*i)//60:02d}:{(9*60+15+5*i)%60:02d}", 100, 105, 95, 100)
                for i in range(9)] + [("10:00", 100, 900, 10, 500)]
        spot2 = spotdata({DAY: bars})
        early2 = MOD.atr_at(spot2, spot2.timestamps_by_day[DAY][5], 5)
        self.assertAlmostEqual(early, early2)

    def test_an_unknown_timestamp_returns_none(self):
        self.assertIsNone(MOD.atr_at(self.spot, MOD.build_ts(DAY, "23:00"), 5))


class OpenClassificationTests(unittest.TestCase):
    def test_open_above_pdh(self):
        self.assertEqual(MOD.classify_open(120, 110, 90), "above_pdh")

    def test_open_below_pdl(self):
        self.assertEqual(MOD.classify_open(80, 110, 90), "below_pdl")

    def test_open_inside_the_range(self):
        self.assertEqual(MOD.classify_open(100, 110, 90), "inside")

    def test_open_exactly_on_a_level_counts_as_inside(self):
        self.assertEqual(MOD.classify_open(110, 110, 90), "inside")


class BreakoutTests(unittest.TestCase):
    def test_entry_is_the_next_bar_after_the_confirming_close(self):
        rows, order = session(DAY, [
            ("09:15", 100, 105, 95, 100),
            ("09:20", 100, 115, 99, 112),     # closes above 110
            ("09:25", 113, 118, 112, 117),    # entry at this OPEN
        ])
        side, ts, px = MOD.find_breakout(rows, order, 110, 90, 0.0,
                                         MOD.build_ts(DAY, "14:00"), order[0])
        self.assertEqual(side, "up")
        self.assertEqual(MOD.ts_time(ts), "09:25")
        self.assertAlmostEqual(px, 113.0)

    def test_the_first_break_wins_even_when_the_day_reverses(self):
        rows, order = session(DAY, [
            ("09:15", 100, 105, 95, 100),
            ("09:20", 100, 101, 80, 85),      # closes below 90 FIRST
            ("09:25", 85, 86, 84, 85),
            ("09:30", 85, 300, 84, 290),      # much bigger up-move later
            ("09:35", 290, 295, 285, 292),
        ])
        side, ts, _ = MOD.find_breakout(rows, order, 110, 90, 0.0,
                                        MOD.build_ts(DAY, "14:00"), order[0])
        self.assertEqual(side, "down")
        self.assertEqual(MOD.ts_time(ts), "09:25")

    def test_the_buffer_must_be_cleared(self):
        rows, order = session(DAY, [
            ("09:15", 100, 105, 95, 100),
            ("09:20", 100, 115, 99, 112),     # above 110 but not above 110+20
            ("09:25", 113, 118, 112, 117),
        ])
        self.assertIsNone(MOD.find_breakout(rows, order, 110, 90, 20.0,
                                            MOD.build_ts(DAY, "14:00"), order[0]))

    def test_a_break_after_the_cutoff_is_not_taken(self):
        rows, order = session(DAY, [
            ("09:15", 100, 105, 95, 100),
            ("14:05", 100, 200, 99, 190),
            ("14:10", 190, 195, 185, 192),
        ])
        self.assertIsNone(MOD.find_breakout(rows, order, 110, 90, 0.0,
                                            MOD.build_ts(DAY, "14:00"), order[0]))


class RetestTests(unittest.TestCase):
    """The spec calls retest a lookahead magnet — the hold must CLOSE first."""

    def test_a_touch_that_holds_enters_on_the_next_bar(self):
        rows, order = session(DAY, [
            ("09:15", 120, 125, 118, 122),
            ("09:20", 122, 123, 109, 114),    # touches 110 from above, closes above
            ("09:25", 115, 119, 114, 118),    # entry here
        ])
        got = MOD.find_retest(rows, order, 110, "up", MOD.build_ts(DAY, "14:00"))
        self.assertIsNotNone(got)
        self.assertEqual(MOD.ts_time(got[0]), "09:25")
        self.assertAlmostEqual(got[1], 115.0)

    def test_a_touch_that_fails_to_hold_is_not_an_entry(self):
        rows, order = session(DAY, [
            ("09:15", 120, 125, 118, 122),
            ("09:20", 122, 123, 100, 104),    # touched 110 but CLOSED below it
            ("09:25", 104, 106, 102, 105),
        ])
        self.assertIsNone(MOD.find_retest(rows, order, 110, "up",
                                          MOD.build_ts(DAY, "14:00")))

    def test_never_touching_the_level_is_not_an_entry(self):
        rows, order = session(DAY, [
            ("09:15", 120, 125, 118, 122),
            ("09:20", 122, 128, 121, 127),
        ])
        self.assertIsNone(MOD.find_retest(rows, order, 110, "up",
                                          MOD.build_ts(DAY, "14:00")))

    def test_the_down_side_mirrors(self):
        rows, order = session(DAY, [
            ("09:15", 80, 82, 75, 78),
            ("09:20", 78, 91, 77, 86),        # touches 90 from below, closes below
            ("09:25", 85, 87, 83, 84),
        ])
        got = MOD.find_retest(rows, order, 90, "down", MOD.build_ts(DAY, "14:00"))
        self.assertIsNotNone(got)
        self.assertEqual(MOD.ts_time(got[0]), "09:25")


class SpotLegTests(unittest.TestCase):
    def test_a_bar_holding_both_stop_and_target_resolves_to_the_stop(self):
        rows, order = session(DAY, [
            ("09:25", 100, 100, 100, 100),
            ("09:30", 100, 140, 80, 100),
            ("15:20", 100, 100, 100, 100),
        ])
        out = MOD.resolve_spot_leg(rows, order, order[0], order[-1],
                                   100.0, 1, 90.0, 130.0)
        self.assertEqual(out.exit_reason, "sl")

    def test_a_bar_after_the_exit_never_resolves_the_leg(self):
        rows, order = session(DAY, [
            ("09:25", 100, 100, 100, 100),
            ("15:20", 101, 101, 101, 101),
            ("15:25", 101, 400, 5, 300),
        ])
        out = MOD.resolve_spot_leg(rows, order, order[0],
                                   MOD.build_ts(DAY, "15:20"), 100.0, 1, 90.0, 130.0)
        self.assertEqual(out.exit_reason, "day_close")


class SessionTests(unittest.TestCase):
    def test_previous_session_steps_over_an_anomalous_day(self):
        days = ["2025-01-13", "2025-01-14", "2025-01-15"]
        tsd = {days[0]: [MOD.build_ts(days[0], f"{(9*60+15+5*i)//60:02d}:{(9*60+15+5*i)%60:02d}")
                         for i in range(75)],
               days[1]: [MOD.build_ts(days[1], "18:00")],
               days[2]: [MOD.build_ts(days[2], f"{(9*60+15+5*i)//60:02d}:{(9*60+15+5*i)%60:02d}")
                         for i in range(75)]}
        self.assertEqual(MOD.previous_normal_session(days, tsd, 2), "2025-01-13")

    def test_lot_size_eras(self):
        for expiry, expected in [("2020-01-02", 75), ("2021-10-07", 50),
                                 ("2024-05-02", 25), ("2024-11-28", 75),
                                 ("2026-01-06", 65)]:
            with self.subTest(expiry=expiry):
                self.assertEqual(MOD.lot_size_for(expiry), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
