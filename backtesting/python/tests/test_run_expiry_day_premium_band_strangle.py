"""
Tests for the expiry-day premium-band strangle runner.

Covers the two things most likely to be wrong in this kind of script: which
strike the premium band picks, and where a stopped leg fills.

Run directly (there is no package here, so unittest discover will not find it):

    python backtesting/python/tests/test_run_expiry_day_premium_band_strangle.py
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (Path(__file__).resolve().parents[1] / "expiry-day-short-premium"
               / "run_expiry_day_premium_band_strangle_2020_2026.py")
SPEC = importlib.util.spec_from_file_location(
    "run_expiry_day_premium_band_strangle", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)

DAY = "2025-01-16"
TS = "2025-01-16T10:00:00+05:30"
EXIT_TS = "2025-01-16T15:20:00+05:30"


def contract(bars):
    """bars: list of (hhmm, open, high)."""
    rows = {}
    for hhmm, o, h in bars:
        ts = MOD.build_ts(DAY, hhmm)
        rows[ts] = MOD.PriceRow(ts, float(o), float(h))
    return MOD.ContractData(path=Path("NIFTY_23350_CE_16_JAN_25.csv"),
                            rows_by_timestamp=rows)


def chain(tmp: Path, prices):
    """Write a one-day option chain.

    prices: {(strike, "CE"|"PE"): entry_price_or_None}. None writes a
    header-only file, which is what a never-traded deep-OTM contract looks like
    in the real dataset.
    """
    folder = tmp / DAY
    folder.mkdir(parents=True, exist_ok=True)
    suffix = MOD.expiry_suffix(DAY)
    for (strike, side), price in prices.items():
        path = folder / f"NIFTY_{strike}_{side}_{suffix}.csv"
        lines = ["timestamp,open,high,low,close,volume,oi"]
        if price is not None:
            lines.append(f"{TS},{price},{price},{price},{price},100,1000")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tmp


class BandSelectionTests(unittest.TestCase):
    """The band picks by premium, aiming at the midpoint of [5, 10] = 7.5."""

    def pick(self, prices, side="CE", atm=23000, lo=5.0, hi=10.0, depth=60):
        with tempfile.TemporaryDirectory() as td:
            root = chain(Path(td), prices)
            return MOD.scan_side(atm, side, DAY, TS, root, {}, lo, hi, depth)

    def test_picks_the_strike_nearest_the_band_midpoint(self):
        # 9.8 is nearest ATM, 5.2 is cheapest, 7.4 is nearest 7.5.
        got = self.pick({(23050, "CE"): 9.8,
                         (23100, "CE"): 7.4,
                         (23150, "CE"): 5.2})
        self.assertEqual(got["strike"], 23100)
        self.assertTrue(got["in_band"])

    def test_does_not_just_take_the_first_strike_in_band(self):
        """A nearer strike that is in band still loses to a better-centred one."""
        got = self.pick({(23050, "CE"): 10.0, (23100, "CE"): 7.5})
        self.assertEqual(got["strike"], 23100)

    def test_tie_on_midpoint_distance_goes_to_the_nearer_strike(self):
        # 6.5 and 8.5 are both 1.0 from the midpoint; the nearer strike wins.
        got = self.pick({(23050, "CE"): 8.5, (23100, "CE"): 6.5})
        self.assertEqual(got["strike"], 23050)

    def test_pe_side_scans_downward(self):
        got = self.pick({(22950, "PE"): 9.9, (22900, "PE"): 7.5}, side="PE")
        self.assertEqual(got["strike"], 22900)
        self.assertTrue(got["in_band"])

    def test_skips_strikes_with_no_bar_at_the_entry_minute(self):
        """A header-only contract is not a candidate - no stale quote is used."""
        got = self.pick({(23050, "CE"): None, (23100, "CE"): 7.5})
        self.assertEqual(got["strike"], 23100)


class BandFallbackTests(unittest.TestCase):
    """Out of band, take the nearest to the band - never skip the day."""

    def pick(self, prices, side="CE", atm=23000):
        with tempfile.TemporaryDirectory() as td:
            root = chain(Path(td), prices)
            return MOD.scan_side(atm, side, DAY, TS, root, {}, 5.0, 10.0, 60)

    def test_whole_chain_above_the_band_takes_the_cheapest(self):
        got = self.pick({(23050, "CE"): 40.0, (23100, "CE"): 25.0,
                         (23150, "CE"): 12.0})
        self.assertEqual(got["strike"], 23150)
        self.assertFalse(got["in_band"])

    def test_whole_chain_below_the_band_takes_the_dearest(self):
        got = self.pick({(23050, "CE"): 4.0, (23100, "CE"): 1.0})
        self.assertEqual(got["strike"], 23050)
        self.assertFalse(got["in_band"])

    def test_the_first_below_band_strike_is_recorded_before_the_scan_breaks(self):
        """The scan stops one strike AFTER dropping under the band.

        If it broke on sight of a cheap strike without recording it, a chain
        that opens entirely under Rs 5 would have no fallback at all and the
        day would be skipped.
        """
        got = self.pick({(23050, "CE"): 4.9, (23100, "CE"): 0.5})
        self.assertIsNotNone(got)
        self.assertEqual(got["strike"], 23050)

    def test_any_in_band_strike_beats_every_out_of_band_one(self):
        got = self.pick({(23050, "CE"): 10.1, (23100, "CE"): 5.0,
                         (23150, "CE"): 4.9})
        self.assertEqual(got["strike"], 23100)
        self.assertTrue(got["in_band"])

    def test_nothing_priceable_returns_none(self):
        got = self.pick({(23050, "CE"): None, (23100, "CE"): None})
        self.assertIsNone(got)

    def test_zero_priced_contracts_are_not_candidates(self):
        got = self.pick({(23050, "CE"): 0.0, (23100, "CE"): 7.5})
        self.assertEqual(got["strike"], 23100)


class BothLegsTests(unittest.TestCase):
    """CE and PE are chosen independently and can never invert."""

    def test_legs_are_selected_independently(self):
        with tempfile.TemporaryDirectory() as td:
            root = chain(Path(td), {
                (23050, "CE"): 20.0, (23100, "CE"): 7.6,     # CE 2 strikes out
                (22950, "PE"): 7.4,                          # PE 1 strike out
            })
            chosen, reason = MOD.select_premium_band(
                23000, DAY, TS, root, {}, 5.0, 10.0, 60)
        self.assertEqual(reason, "")
        self.assertEqual(chosen["ce"]["strike"], 23100)
        self.assertEqual(chosen["pe"]["strike"], 22950)
        self.assertGreater(chosen["ce"]["strike"], chosen["pe"]["strike"])

    def test_missing_pe_side_skips_the_day(self):
        with tempfile.TemporaryDirectory() as td:
            root = chain(Path(td), {(23100, "CE"): 7.5})
            chosen, reason = MOD.select_premium_band(
                23000, DAY, TS, root, {}, 5.0, 10.0, 60)
        self.assertIsNone(chosen)
        self.assertEqual(reason, "no_pe_candidate")

    def test_search_depth_is_respected(self):
        """A strike beyond --max-search-strikes is never reached."""
        with tempfile.TemporaryDirectory() as td:
            root = chain(Path(td), {(23500, "CE"): 7.5})   # 10 strikes out
            got = MOD.scan_side(23000, "CE", DAY, TS, root, {}, 5.0, 10.0, 5)
        self.assertIsNone(got)


class StopFillTests(unittest.TestCase):
    """A resting stop fills at the stop price; a gap through it fills at the open."""

    def test_intrabar_touch_fills_at_the_2x_stop(self):
        c = contract([("10:00", 8, 8), ("10:01", 9, 16), ("15:20", 1, 1)])
        out = MOD.resolve_leg(c, 8.0, TS, EXIT_TS, 2.0, 0.0, 1)
        self.assertEqual(out.exit_reason, "sl")
        self.assertAlmostEqual(out.exit_price, 16.0)
        self.assertAlmostEqual(out.points, -8.0)

    def test_gap_through_the_stop_fills_at_the_bar_open(self):
        c = contract([("10:00", 8, 8), ("10:01", 22, 25), ("15:20", 1, 1)])
        out = MOD.resolve_leg(c, 8.0, TS, EXIT_TS, 2.0, 0.0, 1)
        self.assertEqual(out.exit_reason, "gap_sl")
        self.assertAlmostEqual(out.exit_price, 22.0)
        self.assertAlmostEqual(out.points, -14.0)

    def test_a_gap_is_never_credited_at_the_stop_price(self):
        """Filling a 22 gap at 16 would invent 6 points that never existed."""
        c = contract([("10:00", 8, 8), ("10:01", 22, 25), ("15:20", 1, 1)])
        out = MOD.resolve_leg(c, 8.0, TS, EXIT_TS, 2.0, 0.0, 1)
        self.assertLess(out.points, -8.0)

    def test_an_untouched_leg_runs_to_the_exit_bar(self):
        c = contract([("10:00", 8, 8), ("12:00", 6, 12), ("15:20", 0.5, 0.5)])
        out = MOD.resolve_leg(c, 8.0, TS, EXIT_TS, 2.0, 0.0, 1)
        self.assertEqual(out.exit_reason, "day_close")
        self.assertAlmostEqual(out.points, 7.5)

    def test_slippage_is_charged_on_both_entry_and_exit(self):
        c = contract([("10:00", 8, 8), ("15:20", 0.0, 0.0)])
        out = MOD.resolve_leg(c, 8.0, TS, EXIT_TS, 2.0, 0.50, 75)
        self.assertAlmostEqual(out.points, 8.0 - 1.0)       # 2 * 0.50
        self.assertAlmostEqual(out.gross, 7.0 * 75)

    def test_a_bar_after_the_exit_never_resolves_the_leg(self):
        """Lookahead guard: 15:25 is past the exit and must not trigger a stop."""
        c = contract([("10:00", 8, 8), ("15:20", 1, 1), ("15:25", 50, 60)])
        out = MOD.resolve_leg(c, 8.0, TS, EXIT_TS, 2.0, 0.0, 1)
        self.assertEqual(out.exit_reason, "day_close")
        self.assertAlmostEqual(out.exit_price, 1.0)


class LotSizeTests(unittest.TestCase):
    """Lot size is keyed to the EXPIRY date, not the trade date."""

    def test_every_era_boundary(self):
        cases = [
            ("2020-01-02", 75), ("2021-10-06", 75),
            ("2021-10-07", 50), ("2024-04-25", 50),
            ("2024-05-02", 25), ("2024-11-21", 25),
            ("2024-11-28", 75), ("2025-12-30", 75),
            ("2026-01-06", 65), ("2026-06-16", 65),
        ]
        for expiry, expected in cases:
            with self.subTest(expiry=expiry):
                self.assertEqual(MOD.lot_size_for(expiry), expected)


class CostReportingTests(unittest.TestCase):
    """Slippage lives inside gross_pnl, so the cost ratio has to rebuild it."""

    def test_slippage_rs_counts_two_orders_on_each_of_two_legs(self):
        row = MOD.blank_row(DAY, "Thursday")
        row.status = "TRADED"
        row.qty = "75"
        # 0.50/order x 2 orders x 2 legs x 75 = Rs 150
        self.assertAlmostEqual(MOD.slippage_rs([row], 0.50), 150.0)

    def test_skipped_days_pay_no_slippage(self):
        row = MOD.blank_row(DAY, "Thursday", qty="75")
        self.assertAlmostEqual(MOD.slippage_rs([row], 0.50), 0.0)


class OutputTagTests(unittest.TestCase):
    """Two runs that differ in cost model must not overwrite each other."""

    def test_zero_slippage_gets_its_own_tag(self):
        import argparse
        base = dict(sl_factor=2.0, min_premium=5.0, max_premium=10.0, lots=1,
                    entry_time="10:00")
        full = MOD.output_tag(argparse.Namespace(slippage_per_order=0.50, **base))
        zero = MOD.output_tag(argparse.Namespace(slippage_per_order=0.0, **base))
        self.assertEqual(full, "sl200_prem5-10_lots1_e1000")
        self.assertEqual(zero, "sl200_prem5-10_lots1_e1000_slip0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
