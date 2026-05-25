from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "run_gap_100_atm_option_0916_2025.py"
SPEC = importlib.util.spec_from_file_location("run_gap_100_atm_option_0916_2025", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class Gap100AtmOption0916Tests(unittest.TestCase):
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
                gap_time="09:15",
                entry_time="09:16",
                exit_time="09:25",
                gap_threshold_points=100.0,
                brokerage_per_order=25.0,
                lot_size=65,
                lots=4,
                slippage_points_per_order=1.0,
            )
            results = MODULE.run_backtest(args)
            return results, MODULE.trade_rows_from_results(results)

    def result_for(self, results, entry_date: str):
        matches = [result for result in results if result.entry_date == entry_date]
        self.assertEqual(1, len(matches))
        return matches[0]

    def test_gap_up_at_least_100_buys_atm_call(self) -> None:
        results, trade_rows = self.run_scenario(
            spot_rows=[
                spot("2025-01-03T15:29:00+05:30", 1000, 1000),
                spot("2025-01-06T09:15:00+05:30", 1100, 1105),
                spot("2025-01-06T09:16:00+05:30", 1124, 1120),
                spot("2025-01-06T09:25:00+05:30", 1130, 1131),
            ],
            contracts=[
                (
                    "2025-01-09",
                    1100,
                    "CE",
                    [
                        opt("2025-01-06T09:16:00+05:30", 50),
                        opt("2025-01-06T09:25:00+05:30", 70),
                    ],
                )
            ],
            expiries=["2025-01-09"],
        )

        result = self.result_for(results, "2025-01-06")
        self.assertEqual("TRADED", result.status)
        self.assertEqual("CE", result.option_side)
        self.assertEqual("100.00", result.gap_points)
        self.assertEqual("1100", result.atm_strike)
        self.assertEqual("5200.00", result.raw_gross_pnl)
        self.assertEqual("520.00", result.slippage_loss)
        self.assertEqual("50.00", result.brokerage)
        self.assertEqual("4630.00", result.net_pnl)
        self.assertEqual(1, len(trade_rows))

    def test_gap_down_at_least_100_buys_atm_put(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[
                spot("2025-01-03T15:29:00+05:30", 1000, 1000),
                spot("2025-01-06T09:15:00+05:30", 899, 900),
                spot("2025-01-06T09:16:00+05:30", 876, 880),
                spot("2025-01-06T09:25:00+05:30", 860, 861),
            ],
            contracts=[
                (
                    "2025-01-09",
                    900,
                    "PE",
                    [
                        opt("2025-01-06T09:16:00+05:30", 45),
                        opt("2025-01-06T09:25:00+05:30", 60),
                    ],
                )
            ],
            expiries=["2025-01-09"],
        )

        result = self.result_for(results, "2025-01-06")
        self.assertEqual("TRADED", result.status)
        self.assertEqual("PE", result.option_side)
        self.assertEqual("-101.00", result.gap_points)
        self.assertEqual("900", result.atm_strike)
        self.assertEqual("3330.00", result.net_pnl)

    def test_gap_below_threshold_is_skipped(self) -> None:
        results, trade_rows = self.run_scenario(
            spot_rows=[
                spot("2025-01-03T15:29:00+05:30", 1000, 1000),
                spot("2025-01-06T09:15:00+05:30", 1099, 1100),
                spot("2025-01-06T09:16:00+05:30", 1105, 1106),
                spot("2025-01-06T09:25:00+05:30", 1110, 1111),
            ],
            contracts=[],
            expiries=["2025-01-09"],
        )

        result = self.result_for(results, "2025-01-06")
        self.assertEqual("SKIPPED", result.status)
        self.assertEqual("gap_below_threshold", result.skip_reason)
        self.assertEqual([], trade_rows)

    def test_first_day_skips_without_previous_close(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[
                spot("2025-01-06T09:15:00+05:30", 1100, 1101),
                spot("2025-01-06T09:16:00+05:30", 1105, 1106),
                spot("2025-01-06T09:25:00+05:30", 1110, 1111),
            ],
            contracts=[],
            expiries=["2025-01-09"],
        )

        self.assertEqual("SKIPPED", results[0].status)
        self.assertEqual("no_previous_close", results[0].skip_reason)

    def test_missing_option_file_skips_qualified_day(self) -> None:
        results, trade_rows = self.run_scenario(
            spot_rows=[
                spot("2025-01-03T15:29:00+05:30", 1000, 1000),
                spot("2025-01-06T09:15:00+05:30", 1100, 1101),
                spot("2025-01-06T09:16:00+05:30", 1105, 1106),
                spot("2025-01-06T09:25:00+05:30", 1110, 1111),
            ],
            contracts=[],
            expiries=["2025-01-09"],
        )

        result = self.result_for(results, "2025-01-06")
        self.assertEqual("SKIPPED", result.status)
        self.assertEqual("missing_option_file", result.skip_reason)
        self.assertEqual([], trade_rows)

    def test_missing_option_exit_timestamp_skips_qualified_day(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[
                spot("2025-01-03T15:29:00+05:30", 1000, 1000),
                spot("2025-01-06T09:15:00+05:30", 1100, 1101),
                spot("2025-01-06T09:16:00+05:30", 1105, 1106),
                spot("2025-01-06T09:25:00+05:30", 1110, 1111),
            ],
            contracts=[
                ("2025-01-09", 1100, "CE", [opt("2025-01-06T09:16:00+05:30", 50)])
            ],
            expiries=["2025-01-09"],
        )

        result = self.result_for(results, "2025-01-06")
        self.assertEqual("SKIPPED", result.status)
        self.assertEqual("missing_option_timestamp", result.skip_reason)
        self.assertIn("missing exit timestamp", result.remarks)


def spot(timestamp: str, open_value: float, close_value: float) -> dict[str, str]:
    return {
        "timestamp": timestamp,
        "open": f"{open_value:.2f}",
        "high": f"{max(open_value, close_value):.2f}",
        "low": f"{min(open_value, close_value):.2f}",
        "close": f"{close_value:.2f}",
        "volume": "0",
    }


def opt(timestamp: str, open_value: float) -> dict[str, str]:
    return {
        "timestamp": timestamp,
        "open": f"{open_value:.2f}",
        "high": f"{open_value:.2f}",
        "low": f"{open_value:.2f}",
        "close": f"{open_value:.2f}",
        "volume": "0",
        "oi": "0",
    }


if __name__ == "__main__":
    unittest.main()
