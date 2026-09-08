"""
Tests for the expiry-day straddle/strangle runner.

Covers the two things most likely to be wrong in this kind of script: where a
stopped leg fills, and which strikes the balance rule picks.

Run directly (there is no package here, so unittest discover will not find it):

    python backtesting/python/tests/test_run_expiry_day_straddle_strangle.py
"""
from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (Path(__file__).resolve().parents[1] / "expiry-day-short-premium"
               / "run_expiry_day_straddle_strangle_2020_2026.py")
SPEC = importlib.util.spec_from_file_location("run_expiry_day_straddle_strangle", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)

TS = "2025-01-16T09:20:00+05:30"
EXIT_TS = "2025-01-16T15:20:00+05:30"


def contract(bars):
    """bars: list of (hhmm, open, high)."""
    rows = {}
    for hhmm, o, h in bars:
        ts = MOD.build_ts("2025-01-16", hhmm)
        rows[ts] = MOD.PriceRow(ts, float(o), float(h))
    return MOD.ContractData(path=Path("NIFTY_23350_CE_16_JAN_25.csv"),
                            rows_by_timestamp=rows)


class StopFillTests(unittest.TestCase):
    """A resting stop fills at the stop price; a gap through it fills at the open."""

    def test_intrabar_touch_fills_at_the_stop_price(self):
        c = contract([("09:20", 100, 100), ("09:21", 100, 160), ("15:20", 20, 20)])
        out = MOD.resolve_leg(c, 100.0, TS, EXIT_TS, 1.50, 0.0, 1)
        self.assertEqual(out.exit_reason, "sl")
        self.assertAlmostEqual(out.exit_price, 150.0)
        self.assertAlmostEqual(out.points, -50.0)

    def test_gap_through_the_stop_fills_at_the_bar_open(self):
        c = contract([("09:20", 100, 100), ("09:21", 190, 200), ("15:20", 20, 20)])
        out = MOD.resolve_leg(c, 100.0, TS, EXIT_TS, 1.50, 0.0, 1)
        self.assertEqual(out.exit_reason, "gap_sl")
        self.assertAlmostEqual(out.exit_price, 190.0)
        self.assertAlmostEqual(out.points, -90.0)

    def test_a_gap_is_never_treated_as_a_stop_price_fill(self):
        # Filling a 190 gap at 150 would invent 40 points that were never available.
        c = contract([("09:20", 100, 100), ("09:21", 190, 200), ("15:20", 20, 20)])
        out = MOD.resolve_leg(c, 100.0, TS, EXIT_TS, 1.50, 0.0, 1)
        self.assertNotAlmostEqual(out.exit_price, 150.0)

    def test_untouched_leg_runs_to_the_close(self):
        c = contract([("09:20", 100, 120), ("09:21", 110, 140), ("15:20", 20, 20)])
        out = MOD.resolve_leg(c, 100.0, TS, EXIT_TS, 1.50, 0.0, 1)
        self.assertEqual(out.exit_reason, "day_close")
        self.assertAlmostEqual(out.exit_price, 20.0)
        self.assertAlmostEqual(out.points, 80.0)

    def test_stop_scales_with_the_factor(self):
        c = contract([("09:20", 100, 100), ("09:21", 100, 210), ("15:20", 20, 20)])
        out = MOD.resolve_leg(c, 100.0, TS, EXIT_TS, 2.00, 0.0, 1)
        self.assertAlmostEqual(out.exit_price, 200.0)

    def test_slippage_is_charged_both_ways(self):
        c = contract([("09:20", 100, 100), ("15:20", 20, 20)])
        out = MOD.resolve_leg(c, 100.0, TS, EXIT_TS, 1.50, 0.5, 1)
        self.assertAlmostEqual(out.points, 80.0 - 1.0)

    def test_pnl_scales_with_quantity(self):
        c = contract([("09:20", 100, 100), ("15:20", 20, 20)])
        out = MOD.resolve_leg(c, 100.0, TS, EXIT_TS, 1.50, 0.0, 300)
        self.assertAlmostEqual(out.gross, 80.0 * 300)


class StrikeSelectionTests(unittest.TestCase):
    """Balance rules pick strikes; they must never invert or drift silently."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.opts = Path(self.tmp.name)
        (self.opts / "2025-01-16").mkdir(parents=True)
        self.cache = {}

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, strike, side, price):
        p = self.opts / "2025-01-16" / f"NIFTY_{strike}_{side}_16_JAN_25.csv"
        with p.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["timestamp", "open", "high", "low", "close", "volume", "oi"])
            w.writerow([TS, price, price, price, price, 1, 1])

    def test_centre_candidates_walk_outward_symmetrically(self):
        self.assertEqual(MOD.centre_candidates(23350, 2),
                         [23350, 23400, 23300, 23450, 23250])

    def test_balanced_atm_is_taken_without_shifting(self):
        self.write(23350, "CE", 100); self.write(23350, "PE", 100)
        got, reason = MOD.select_strikes(23350, 0, "2025-01-16", TS, self.opts,
                                         self.cache, 0.20, 5, False)
        self.assertEqual(reason, "")
        self.assertEqual(got["centre"], 23350)
        self.assertEqual(got["shift"], 0)

    def test_unbalanced_everywhere_is_skipped(self):
        for s, ce, pe in [(23350, 30, 55), (23400, 18, 95), (23300, 53, 28)]:
            self.write(s, "CE", ce); self.write(s, "PE", pe)
        got, reason = MOD.select_strikes(23350, 0, "2025-01-16", TS, self.opts,
                                         self.cache, 0.20, 1, False)
        self.assertIsNone(got)
        self.assertEqual(reason, "balance_filter")

    def test_fallback_takes_the_best_available_pair(self):
        for s, ce, pe in [(23350, 30, 55), (23400, 18, 95), (23300, 53, 28)]:
            self.write(s, "CE", ce); self.write(s, "PE", pe)
        got, reason = MOD.select_strikes(23350, 0, "2025-01-16", TS, self.opts,
                                         self.cache, 0.20, 1, True)
        self.assertEqual(reason, "")
        self.assertEqual(got["centre"], 23350)          # 0.545 beats 0.528 and 0.189

    def test_missing_contracts_report_no_priceable_pair(self):
        got, reason = MOD.select_strikes(23350, 0, "2025-01-16", TS, self.opts,
                                         self.cache, 0.20, 2, True)
        self.assertIsNone(got)
        self.assertEqual(reason, "no_priceable_pair")

    def test_strangle_centre_shift_keeps_legs_symmetric(self):
        self.write(23450, "CE", 100); self.write(23250, "PE", 100)
        got, _ = MOD.select_strikes(23350, 100, "2025-01-16", TS, self.opts,
                                    self.cache, 0.20, 0, False)
        self.assertEqual(got["ce_strike"] - got["centre"], 100)
        self.assertEqual(got["centre"] - got["pe_strike"], 100)

    def test_legs_mode_can_balance_where_centre_shift_cannot(self):
        # Nominal 100-wide pair is badly skewed; a wider CE matches the PE.
        self.write(23450, "CE", 30);  self.write(23250, "PE", 90)
        self.write(23500, "CE", 88)
        got, reason = MOD.select_strikes_legs(23350, 100, "2025-01-16", TS, self.opts,
                                              self.cache, 0.20, 1, False)
        self.assertEqual(reason, "")
        self.assertEqual((got["ce_strike"], got["pe_strike"]), (23500, 23250))
        self.assertGreaterEqual(got["ratio"], 0.80)

    def test_legs_mode_never_inverts_the_legs(self):
        for s in (23200, 23250, 23300):
            self.write(s, "CE", 50); self.write(s, "PE", 50)
        got, _ = MOD.select_strikes_legs(23250, 0, "2025-01-16", TS, self.opts,
                                         self.cache, 0.20, 1, True)
        self.assertGreaterEqual(got["ce_strike"], got["pe_strike"])


class MarginAndCagrTests(unittest.TestCase):

    def test_margin_nets_the_lighter_side(self):
        m = MOD.position_margin(23400, 23200, 300)
        heavy, light = 23400 * 300, 23200 * 300
        self.assertAlmostEqual(m, 0.10 * heavy + 0.30 * 0.10 * light)

    def test_total_loss_floors_at_minus_100(self):
        self.assertEqual(
            MOD.compute_cagr(-2_000_000.0, 1_000_000.0, "2020-01-01", "2026-06-16"),
            -100.0)

    def test_max_drawdown_is_peak_to_trough(self):
        self.assertAlmostEqual(MOD.max_drawdown([100, -30, -20, 50]), 50.0)

    def test_lot_size_is_keyed_to_the_expiry_era(self):
        self.assertEqual(MOD.lot_config("2021-01-07"), (75, 4))
        self.assertEqual(MOD.lot_config("2023-06-08"), (50, 6))
        self.assertEqual(MOD.lot_config("2024-06-06"), (25, 12))
        self.assertEqual(MOD.lot_config("2025-06-10"), (75, 4))
        self.assertEqual(MOD.lot_config("2026-01-06"), (65, 5))


if __name__ == "__main__":
    unittest.main(verbosity=2)
