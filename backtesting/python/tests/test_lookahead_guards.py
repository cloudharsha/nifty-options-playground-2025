"""
Regression guards for the three lookahead bugs found in the directional
(25-SMA) strategies, plus the CAGR blow-up they exposed.

Each test states the causality rule in its name. If one of these fails, a
backtest in this family is reading a price it could not have known at the
moment it claims to trade.

Run directly (there is no package here, so unittest discover will not find it):

    python backtesting/python/tests/test_lookahead_guards.py
"""
from __future__ import annotations

import datetime
import importlib.util
import sys
import unittest
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parents[1]


def load(relative_path: str, name: str):
    path = PYTHON_DIR / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


INTRADAY_BASE = load(
    "25ma-intraday/run_short_atm_nifty_ma_weekly_intraday_trailing_2020_2026.py",
    "_lookahead_intraday_base",
)
INTRADAY_0920 = load(
    "25ma-intraday/run_short_atm_nifty_ma_weekly_intraday_trailing_0920_random.py",
    "_lookahead_intraday_0920",
)
OVERNIGHT = load(
    "25ma-overnight/run_short_atm_nifty_ma_weekly_overnight_offsets_2020_2026.py",
    "_lookahead_overnight",
)


class SignalBarMustHaveClosedTests(unittest.TestCase):
    """A 15m bar stamped T covers T..T+15 and is only readable from T+15."""

    def test_0930_entry_reads_the_bar_that_closes_at_0930(self) -> None:
        sig = INTRADAY_BASE.signal_timestamp_for_entry("2025-06-10T09:30:00+05:30")
        self.assertEqual(sig, "2025-06-10T09:15:00+05:30")

    def test_0920_entry_does_not_read_the_0915_bar(self) -> None:
        # The 09:15 bar closes at 09:30. A 09:20 entry that reads it is using
        # ten minutes of future information.
        sig = INTRADAY_0920.signal_timestamp_for_entry(
            "2025-06-10T09:20:00+05:30", "2025-06-10", "2025-06-09"
        )
        self.assertNotEqual(sig, "2025-06-10T09:15:00+05:30")

    def test_0920_entry_reads_the_previous_sessions_last_closed_bar(self) -> None:
        sig = INTRADAY_0920.signal_timestamp_for_entry(
            "2025-06-10T09:20:00+05:30", "2025-06-10", "2025-06-09"
        )
        self.assertEqual(sig, "2025-06-09T15:15:00+05:30")

    def test_0920_entry_without_a_previous_session_yields_no_signal(self) -> None:
        sig = INTRADAY_0920.signal_timestamp_for_entry(
            "2025-06-10T09:20:00+05:30", "2025-06-10", None
        )
        self.assertEqual(sig, "")

    def test_later_entries_still_use_the_bar_that_just_closed(self) -> None:
        sig = INTRADAY_0920.signal_timestamp_for_entry(
            "2025-06-10T11:45:00+05:30", "2025-06-10", "2025-06-09"
        )
        self.assertEqual(sig, "2025-06-10T11:30:00+05:30")

    def test_overnight_signal_bar_closes_before_the_entry_minute(self) -> None:
        original_argv = sys.argv
        try:
            sys.argv = ["run_overnight_offsets"]
            args = OVERNIGHT.parse_args()
        finally:
            sys.argv = original_argv

        signal_close = datetime.datetime.strptime(
            args.signal_time, "%H:%M"
        ) + datetime.timedelta(minutes=15)
        entry = datetime.datetime.strptime(args.entry_time, "%H:%M")
        self.assertLessEqual(
            signal_close,
            entry,
            f"signal bar {args.signal_time} closes at {signal_close:%H:%M}, "
            f"after the {args.entry_time} entry",
        )


class StopFillMustFollowTheTouchTests(unittest.TestCase):
    """
    The MA touch is detected from a 5m bar's high/low, so it happens at or
    after that bar's open. Filling at that same open is a price from before
    the stop existed.
    """

    def make_exit(self, module, low_at_1000: float, stop_bar_open: float,
                  next_bar_open: float):
        day = "2025-06-10"

        def ts(hhmm: str) -> str:
            return f"{day}T{hhmm}:00+05:30"

        # Spot: flat at 100 until 10:00, where the low pierces the MA at 90.
        spot_5m = {}
        for hhmm in ["09:35", "09:40", "09:45", "09:50", "09:55", "10:00",
                     "10:05", "10:10"]:
            low = low_at_1000 if hhmm == "10:00" else 100.0
            spot_5m[ts(hhmm)] = module.PriceRow(
                timestamp=ts(hhmm), open_value=100.0, open_text="100.00",
                high_value=100.0, high_text="100.00",
                low_value=low, low_text=f"{low:.2f}",
                close_value=100.0, close_text="100.00",
            )

        # 15m spot history: two prior-session bars so a 2-period SMA is
        # already defined at 09:15, then the session's own bars. All at 90.
        ordered, by_ts, idx_by_ts = [], {}, {}
        stamps = [
            "2025-06-09T15:00:00+05:30", "2025-06-09T15:15:00+05:30",
            ts("09:15"), ts("09:30"), ts("09:45"), ts("10:00"),
        ]
        for i, stamp in enumerate(stamps):
            row = module.PriceRow(
                timestamp=stamp, open_value=90.0, open_text="90.00",
                high_value=90.0, high_text="90.00",
                low_value=90.0, low_text="90.00",
                close_value=90.0, close_text="90.00",
            )
            ordered.append(row)
            by_ts[stamp] = row
            idx_by_ts[stamp] = i
        spot_15m = module.Spot15Data(
            rows_by_timestamp=by_ts, ordered_rows=ordered,
            index_by_timestamp=idx_by_ts, trading_days=["2025-06-09", day],
        )

        option_rows = {
            ts("09:30"): module.OptionRow(ts("09:30"), 50.0, "50.00"),
            ts("10:00"): module.OptionRow(ts("10:00"), stop_bar_open,
                                          f"{stop_bar_open:.2f}"),
            ts("10:05"): module.OptionRow(ts("10:05"), next_bar_open,
                                          f"{next_bar_open:.2f}"),
            ts("10:15"): module.OptionRow(ts("10:15"), 10.0, "10.00"),
        }
        contract = module.ContractData(
            path=Path("NIFTY_25000_PE_10_JUN_25.csv"),
            rows_by_timestamp=option_rows,
        )
        return module.resolve_trade_exit(
            entry_row=option_rows[ts("09:30")], contract_data=contract,
            spot_5m_rows=spot_5m, spot_15m_data=spot_15m, day=day,
            entry_timestamp=ts("09:30"), exit_time="10:15", sold_side="PE",
            ma_period=2, slippage_points_per_order=0.0,
            brokerage_per_order=0.0, contract_multiplier=1,
        )

    def test_stop_fills_at_the_next_bar_not_the_triggering_bar(self) -> None:
        for module in (INTRADAY_BASE, INTRADAY_0920):
            with self.subTest(module=module.__name__):
                outcome = self.make_exit(
                    module, low_at_1000=80.0, stop_bar_open=60.0,
                    next_bar_open=75.0,
                )
                self.assertEqual(outcome.exit_reason, "stop_loss_ma_touch")
                self.assertEqual(
                    outcome.exit_timestamp, "2025-06-10T10:05:00+05:30",
                    "stop must fill on the bar after the touch is observed",
                )
                # Short PE entered at 50, filled at 75 -> a 25-point loss.
                self.assertAlmostEqual(outcome.gross_pnl, -25.0)

    def test_stop_does_not_fill_at_the_pre_trigger_price(self) -> None:
        # The triggering bar opens at 60 (a profit) but runs to 75 (a loss).
        # Filling at 60 would book the profit the old code booked.
        outcome = self.make_exit(
            INTRADAY_BASE, low_at_1000=80.0, stop_bar_open=60.0,
            next_bar_open=75.0,
        )
        self.assertNotAlmostEqual(outcome.gross_pnl, -10.0)

    def test_untouched_ma_exits_at_day_close(self) -> None:
        outcome = self.make_exit(
            INTRADAY_BASE, low_at_1000=100.0, stop_bar_open=60.0,
            next_bar_open=75.0,
        )
        self.assertEqual(outcome.exit_reason, "day_close")
        self.assertEqual(outcome.exit_timestamp, "2025-06-10T10:15:00+05:30")


class CagrStaysRealTests(unittest.TestCase):
    """
    (1 + net/capital) ** (365.25/days) returns a complex number once losses
    exceed the capital base. A wiped-out account floors at -100%.
    """

    def test_total_loss_floors_at_minus_100(self) -> None:
        for module in (INTRADAY_BASE, INTRADAY_0920, OVERNIGHT):
            with self.subTest(module=module.__name__):
                cagr = module.compute_cagr(
                    -14_15_087.0, 10_00_000.0, "2020-01-01", "2026-06-19"
                )
                self.assertIsInstance(cagr, float)
                self.assertEqual(cagr, -100.0)

    def test_exact_wipeout_floors_at_minus_100(self) -> None:
        cagr = INTRADAY_BASE.compute_cagr(
            -10_00_000.0, 10_00_000.0, "2020-01-01", "2026-06-19"
        )
        self.assertEqual(cagr, -100.0)

    def test_ordinary_profit_is_unchanged(self) -> None:
        cagr = INTRADAY_BASE.compute_cagr(
            10_00_000.0, 10_00_000.0, "2020-01-01", "2021-12-31"
        )
        self.assertIsInstance(cagr, float)
        self.assertAlmostEqual(cagr, 41.45, places=1)

    def test_partial_loss_is_negative_but_above_the_floor(self) -> None:
        cagr = INTRADAY_BASE.compute_cagr(
            -5_00_000.0, 10_00_000.0, "2020-01-01", "2026-06-19"
        )
        self.assertLess(cagr, 0.0)
        self.assertGreater(cagr, -100.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
