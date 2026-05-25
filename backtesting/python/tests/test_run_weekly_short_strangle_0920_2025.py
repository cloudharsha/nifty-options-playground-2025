from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "run_weekly_short_strangle_0920_2025.py"
SPEC = importlib.util.spec_from_file_location("run_weekly_short_strangle_0920_2025", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class WeeklyShortStrangle0920Tests(unittest.TestCase):
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
                sell_min_premium=20.0,
                sell_max_premium=30.0,
                sell_target_premium=25.0,
                stop_loss_multiple=2.0,
                target_premium=10.0,
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

    def test_selects_otm_legs_inside_20_to_30_premium_band(self) -> None:
        results, trade_rows = self.run_scenario(
            spot_rows=[
                spot("2025-01-06T09:20:00+05:30", 23673),
                spot("2025-01-06T09:21:00+05:30", 23680),
                spot("2025-01-06T15:20:00+05:30", 23640),
            ],
            contracts=[
                ("2025-01-09", 23700, "CE", option_day(31, 30, 28)),
                ("2025-01-09", 23750, "CE", option_day(24, 22, 15)),
                ("2025-01-09", 23800, "CE", option_day(26, 24, 18)),
                ("2025-01-09", 23600, "PE", option_day(22, 21, 14)),
                ("2025-01-09", 23550, "PE", option_day(25, 24, 12)),
            ],
        )

        self.assertEqual("TRADED", results[0].status)
        self.assertEqual("23650", results[0].atm_strike)
        self.assertEqual("23750", results[0].ce_strike)
        self.assertEqual("23550", results[0].pe_strike)
        self.assertEqual(["CE", "PE"], [row.side for row in trade_rows])

    def test_independent_target_and_stop_loss_exits(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[
                spot("2025-01-06T09:20:00+05:30", 23673),
                spot("2025-01-06T09:21:00+05:30", 23680),
                spot("2025-01-06T15:20:00+05:30", 23640),
            ],
            contracts=[
                (
                    "2025-01-09",
                    23700,
                    "CE",
                    [
                        opt("2025-01-06T09:20:00+05:30", 25, 25, 25),
                        opt("2025-01-06T09:21:00+05:30", 20, 22, 9),
                        opt("2025-01-06T15:20:00+05:30", 12, 14, 11),
                    ],
                ),
                (
                    "2025-01-09",
                    23600,
                    "PE",
                    [
                        opt("2025-01-06T09:20:00+05:30", 25, 25, 25),
                        opt("2025-01-06T09:21:00+05:30", 30, 51, 24),
                        opt("2025-01-06T15:20:00+05:30", 30, 31, 28),
                    ],
                ),
            ],
        )

        self.assertEqual("TRADED", results[0].status)
        self.assertEqual("target", results[0].ce_exit_reason)
        self.assertEqual("10.00", results[0].ce_exit_price)
        self.assertEqual("stop_loss", results[0].pe_exit_reason)
        self.assertEqual("50.00", results[0].pe_exit_price)
        self.assertEqual("-3640.00", results[0].gross_pnl)
        self.assertEqual("100.00", results[0].brokerage)
        self.assertEqual("-3740.00", results[0].net_pnl)

    def test_gap_stop_and_gap_target_use_candle_open(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[
                spot("2025-01-06T09:20:00+05:30", 23673),
                spot("2025-01-06T09:21:00+05:30", 23680),
                spot("2025-01-06T15:20:00+05:30", 23640),
            ],
            contracts=[
                (
                    "2025-01-09",
                    23700,
                    "CE",
                    [
                        opt("2025-01-06T09:20:00+05:30", 25, 25, 25),
                        opt("2025-01-06T09:21:00+05:30", 55, 56, 54),
                        opt("2025-01-06T15:20:00+05:30", 20, 22, 18),
                    ],
                ),
                (
                    "2025-01-09",
                    23600,
                    "PE",
                    [
                        opt("2025-01-06T09:20:00+05:30", 25, 25, 25),
                        opt("2025-01-06T09:21:00+05:30", 8, 12, 8),
                        opt("2025-01-06T15:20:00+05:30", 8, 9, 7),
                    ],
                ),
            ],
        )

        self.assertEqual("gap_stop_loss", results[0].ce_exit_reason)
        self.assertEqual("55.00", results[0].ce_exit_price)
        self.assertEqual("gap_target", results[0].pe_exit_reason)
        self.assertEqual("8.00", results[0].pe_exit_price)
        self.assertIn("candle open", results[0].remarks)

    def test_same_candle_stop_and_target_prefers_stop(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[
                spot("2025-01-06T09:20:00+05:30", 23673),
                spot("2025-01-06T09:21:00+05:30", 23680),
                spot("2025-01-06T15:20:00+05:30", 23640),
            ],
            contracts=[
                (
                    "2025-01-09",
                    23700,
                    "CE",
                    [
                        opt("2025-01-06T09:20:00+05:30", 25, 25, 25),
                        opt("2025-01-06T09:21:00+05:30", 25, 55, 9),
                        opt("2025-01-06T15:20:00+05:30", 20, 22, 18),
                    ],
                ),
                ("2025-01-09", 23600, "PE", option_day(25, 24, 20)),
            ],
        )

        self.assertEqual("stop_loss", results[0].ce_exit_reason)
        self.assertEqual("50.00", results[0].ce_exit_price)
        self.assertIn("stop-first", results[0].remarks)

    def test_no_valid_strangle_in_premium_band_skips_day(self) -> None:
        results, trade_rows = self.run_scenario(
            spot_rows=[
                spot("2025-01-06T09:20:00+05:30", 23673),
                spot("2025-01-06T15:20:00+05:30", 23640),
            ],
            contracts=[
                ("2025-01-09", 23700, "CE", option_day(25, 24, 20)),
                ("2025-01-09", 23600, "PE", option_day(35, 34, 30)),
            ],
        )

        self.assertEqual("SKIPPED", results[0].status)
        self.assertEqual("no_valid_strangle_in_premium_band", results[0].skip_reason)
        self.assertIn("No OTM PE contract satisfied", results[0].remarks)
        self.assertEqual([], trade_rows)


def spot(timestamp: str, open_value: float) -> dict[str, str]:
    return {
        "timestamp": timestamp,
        "open": f"{open_value:.2f}",
        "high": f"{open_value:.2f}",
        "low": f"{open_value:.2f}",
        "close": f"{open_value:.2f}",
        "volume": "0",
    }


def opt(timestamp: str, open_value: float, high_value: float, low_value: float) -> dict[str, str]:
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


def option_day(entry_value: float, monitor_value: float, exit_value: float) -> list[dict[str, str]]:
    return [
        opt("2025-01-06T09:20:00+05:30", entry_value, entry_value, entry_value),
        opt("2025-01-06T09:21:00+05:30", monitor_value, monitor_value, monitor_value),
        opt("2025-01-06T15:20:00+05:30", exit_value, exit_value, exit_value),
    ]


if __name__ == "__main__":
    unittest.main()
