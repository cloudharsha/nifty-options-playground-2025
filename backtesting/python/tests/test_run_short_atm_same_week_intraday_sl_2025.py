from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "run_short_atm_same_week_intraday_sl_2025.py"
SPEC = importlib.util.spec_from_file_location("run_short_atm_same_week_intraday_sl_2025", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ShortAtmSameWeekIntradaySlTests(unittest.TestCase):
    maxDiff = None

    def run_scenario(
        self,
        spot_rows: list[dict[str, str]],
        contracts: list[tuple[str, int, str, list[dict[str, str]]]],
        expiries: list[str] | None = None,
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spot_file = root / "spot.csv"
            options_dir = root / "Options_2025"
            results_dir = root / "results"
            options_dir.mkdir()

            with spot_file.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["timestamp", "open", "high", "low", "close", "volume"],
                )
                writer.writeheader()
                writer.writerows(spot_rows)

            for expiry in expiries or sorted({contract[0] for contract in contracts}):
                (options_dir / expiry).mkdir(parents=True, exist_ok=True)

            for expiry, strike, side, rows in contracts:
                suffix = MODULE.expiry_suffix(expiry)
                contract_path = options_dir / expiry / f"NIFTY_{strike}_{side}_{suffix}.csv"
                with contract_path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(
                        handle,
                        fieldnames=["timestamp", "open", "high", "low", "close", "volume", "oi"],
                    )
                    writer.writeheader()
                    writer.writerows(rows)

            args = argparse.Namespace(
                spot_file=spot_file,
                options_dir=options_dir,
                results_dir=results_dir,
                entry_time="09:20",
                exit_time="15:20",
                stop_loss_points=50.0,
                brokerage_per_order=25.0,
                lot_size=65,
                lots=4,
                slippage_points_per_order=1.0,
            )
            results = MODULE.run_backtest(args)
            trade_rows = MODULE.trade_rows_from_results(results)
            return results, trade_rows

    def test_first_expiry_on_or_after_uses_folder_dates(self) -> None:
        expiries = ["2025-01-02", "2025-01-09", "2025-01-16"]

        self.assertEqual("2025-01-02", MODULE.first_expiry_on_or_after(expiries, "2025-01-02"))
        self.assertEqual("2025-01-09", MODULE.first_expiry_on_or_after(expiries, "2025-01-03"))
        self.assertIsNone(MODULE.first_expiry_on_or_after(expiries, "2025-01-17"))

    def test_atm_rounding_uses_0920_spot_open(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[
                spot("2025-01-06T09:20:00+05:30", 23675),
                spot("2025-01-06T15:20:00+05:30", 23680),
            ],
            contracts=[
                ("2025-01-09", 23700, "CE", [opt("2025-01-06T09:20:00+05:30", 100, 120), opt("2025-01-06T15:20:00+05:30", 90, 95)]),
                ("2025-01-09", 23700, "PE", [opt("2025-01-06T09:20:00+05:30", 80, 90), opt("2025-01-06T15:20:00+05:30", 70, 75)]),
            ],
        )

        self.assertEqual("TRADED", results[0].status)
        self.assertEqual("23700", results[0].atm_strike)
        self.assertEqual("2025-01-09", results[0].expiry_date)

    def test_independent_stop_and_day_close_exits(self) -> None:
        results, trade_rows = self.run_scenario(
            spot_rows=[
                spot("2025-01-06T09:20:00+05:30", 23673),
                spot("2025-01-06T09:21:00+05:30", 23680),
                spot("2025-01-06T09:22:00+05:30", 23685),
                spot("2025-01-06T15:20:00+05:30", 23640),
            ],
            contracts=[
                (
                    "2025-01-09",
                    23650,
                    "CE",
                    [
                        opt("2025-01-06T09:20:00+05:30", 100, 120),
                        opt("2025-01-06T09:21:00+05:30", 120, 151),
                        opt("2025-01-06T15:20:00+05:30", 130, 140),
                    ],
                ),
                (
                    "2025-01-09",
                    23650,
                    "PE",
                    [
                        opt("2025-01-06T09:20:00+05:30", 80, 90),
                        opt("2025-01-06T09:21:00+05:30", 85, 100),
                        opt("2025-01-06T09:22:00+05:30", 75, 120),
                        opt("2025-01-06T15:20:00+05:30", 70, 200),
                    ],
                ),
            ],
        )

        self.assertEqual("TRADED", results[0].status)
        self.assertEqual("stop_loss", results[0].ce_exit_reason)
        self.assertEqual("2025-01-06T09:21:00+05:30", results[0].ce_exit_timestamp)
        self.assertEqual("150.00", results[0].ce_exit_price)
        self.assertEqual("day_close", results[0].pe_exit_reason)
        self.assertEqual("2025-01-06T15:20:00+05:30", results[0].pe_exit_timestamp)
        self.assertEqual("-11440.00", results[0].gross_pnl)
        self.assertEqual("100.00", results[0].brokerage)
        self.assertEqual("-11540.00", results[0].net_pnl)
        self.assertEqual(["CE", "PE"], [row.side for row in trade_rows])

    def test_scheduled_exit_when_no_stop_is_hit(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[
                spot("2025-01-06T09:20:00+05:30", 23673),
                spot("2025-01-06T09:21:00+05:30", 23670),
                spot("2025-01-06T15:20:00+05:30", 23640),
            ],
            contracts=[
                (
                    "2025-01-09",
                    23650,
                    "CE",
                    [
                        opt("2025-01-06T09:20:00+05:30", 100, 120),
                        opt("2025-01-06T09:21:00+05:30", 95, 125),
                        opt("2025-01-06T15:20:00+05:30", 85, 200),
                    ],
                ),
                (
                    "2025-01-09",
                    23650,
                    "PE",
                    [
                        opt("2025-01-06T09:20:00+05:30", 80, 100),
                        opt("2025-01-06T09:21:00+05:30", 82, 110),
                        opt("2025-01-06T15:20:00+05:30", 78, 200),
                    ],
                ),
            ],
        )

        self.assertEqual("TRADED", results[0].status)
        self.assertEqual("day_close", results[0].ce_exit_reason)
        self.assertEqual("85.00", results[0].ce_exit_price)
        self.assertEqual("day_close", results[0].pe_exit_reason)
        self.assertEqual("78.00", results[0].pe_exit_price)

    def test_gap_above_stop_uses_candle_open(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[
                spot("2025-01-06T09:20:00+05:30", 23673),
                spot("2025-01-06T09:21:00+05:30", 23680),
                spot("2025-01-06T15:20:00+05:30", 23640),
            ],
            contracts=[
                (
                    "2025-01-09",
                    23650,
                    "CE",
                    [
                        opt("2025-01-06T09:20:00+05:30", 100, 120),
                        opt("2025-01-06T09:21:00+05:30", 160, 165),
                        opt("2025-01-06T15:20:00+05:30", 80, 90),
                    ],
                ),
                (
                    "2025-01-09",
                    23650,
                    "PE",
                    [
                        opt("2025-01-06T09:20:00+05:30", 80, 90),
                        opt("2025-01-06T09:21:00+05:30", 82, 100),
                        opt("2025-01-06T15:20:00+05:30", 75, 90),
                    ],
                ),
            ],
        )

        self.assertEqual("gap_stop_loss", results[0].ce_exit_reason)
        self.assertEqual("160.00", results[0].ce_exit_price)
        self.assertIn("candle open", results[0].remarks)

    def test_missing_option_file_skips_day(self) -> None:
        results, trade_rows = self.run_scenario(
            spot_rows=[
                spot("2025-01-06T09:20:00+05:30", 23673),
                spot("2025-01-06T15:20:00+05:30", 23640),
            ],
            contracts=[
                ("2025-01-09", 23650, "CE", [opt("2025-01-06T09:20:00+05:30", 100, 120), opt("2025-01-06T15:20:00+05:30", 80, 90)]),
            ],
            expiries=["2025-01-09"],
        )

        self.assertEqual("SKIPPED", results[0].status)
        self.assertEqual("missing_option_file", results[0].skip_reason)
        self.assertEqual([], trade_rows)

    def test_missing_monitoring_timestamp_skips_day(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[
                spot("2025-01-06T09:20:00+05:30", 23673),
                spot("2025-01-06T09:21:00+05:30", 23680),
                spot("2025-01-06T15:20:00+05:30", 23640),
            ],
            contracts=[
                (
                    "2025-01-09",
                    23650,
                    "CE",
                    [
                        opt("2025-01-06T09:20:00+05:30", 100, 120),
                        opt("2025-01-06T15:20:00+05:30", 80, 90),
                    ],
                ),
                (
                    "2025-01-09",
                    23650,
                    "PE",
                    [
                        opt("2025-01-06T09:20:00+05:30", 80, 90),
                        opt("2025-01-06T09:21:00+05:30", 82, 100),
                        opt("2025-01-06T15:20:00+05:30", 75, 90),
                    ],
                ),
            ],
        )

        self.assertEqual("SKIPPED", results[0].status)
        self.assertEqual("missing_monitoring_timestamp", results[0].skip_reason)
        self.assertIn("missing monitoring timestamp", results[0].remarks)


def spot(timestamp: str, open_value: float) -> dict[str, str]:
    return {
        "timestamp": timestamp,
        "open": f"{open_value:.2f}",
        "high": f"{open_value:.2f}",
        "low": f"{open_value:.2f}",
        "close": f"{open_value:.2f}",
        "volume": "0",
    }


def opt(timestamp: str, open_value: float, high_value: float) -> dict[str, str]:
    low_value = min(open_value, high_value)
    close_value = open_value
    return {
        "timestamp": timestamp,
        "open": f"{open_value:.2f}",
        "high": f"{high_value:.2f}",
        "low": f"{low_value:.2f}",
        "close": f"{close_value:.2f}",
        "volume": "0",
        "oi": "0",
    }


if __name__ == "__main__":
    unittest.main()
