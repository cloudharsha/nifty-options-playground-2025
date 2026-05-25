from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "run_gap_open_atm_straddle_0915_2025.py"
SPEC = importlib.util.spec_from_file_location("run_gap_open_atm_straddle_0915_2025", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class GapOpenAtmStraddle0915Tests(unittest.TestCase):
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
                entry_time="09:15",
                brokerage_per_order=25.0,
                lot_size=65,
                lots=4,
                slippage_points_per_order=2.0,
            )
            results = MODULE.run_backtest(args)
            return results, MODULE.trade_rows_from_results(results)

    def traded_result(self, results, entry_date: str):
        matches = [result for result in results if result.entry_date == entry_date]
        self.assertEqual(1, len(matches))
        self.assertEqual("TRADED", matches[0].status)
        return matches[0]

    def test_negative_gap_buys_long_straddle_from_previous_close(self) -> None:
        results, trade_rows = self.run_scenario(
            spot_rows=[
                spot("2025-01-03T15:29:00+05:30", 100, 100),
                spot("2025-01-06T09:15:00+05:30", 90, 92),
            ],
            contracts=[
                ("2025-01-09", 100, "CE", [opt("2025-01-06T09:15:00+05:30", 10, 16)]),
                ("2025-01-09", 100, "PE", [opt("2025-01-06T09:15:00+05:30", 20, 25)]),
            ],
        )

        result = self.traded_result(results, "2025-01-06")
        self.assertEqual("LONG_STRADDLE", result.strategy_direction)
        self.assertEqual("-10.00", result.gap_points)
        self.assertEqual("100", result.atm_strike)
        self.assertEqual("2860.00", result.raw_gross_pnl)
        self.assertEqual("2080.00", result.slippage_loss)
        self.assertEqual("100.00", result.brokerage)
        self.assertEqual("680.00", result.net_pnl)
        self.assertEqual(["LONG", "LONG"], [row.direction for row in trade_rows])

    def test_positive_gap_shorts_straddle(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[
                spot("2025-01-03T15:29:00+05:30", 100, 100),
                spot("2025-01-06T09:15:00+05:30", 110, 111),
            ],
            contracts=[
                ("2025-01-09", 100, "CE", [opt("2025-01-06T09:15:00+05:30", 10, 6)]),
                ("2025-01-09", 100, "PE", [opt("2025-01-06T09:15:00+05:30", 20, 17)]),
            ],
        )

        result = self.traded_result(results, "2025-01-06")
        self.assertEqual("SHORT_STRADDLE", result.strategy_direction)
        self.assertEqual("10.00", result.gap_points)
        self.assertEqual("1820.00", result.raw_gross_pnl)
        self.assertEqual("-360.00", result.net_pnl)
        self.assertEqual("SHORT", result.ce_direction)
        self.assertEqual("SHORT", result.pe_direction)

    def test_flat_open_skips_day(self) -> None:
        results, trade_rows = self.run_scenario(
            spot_rows=[
                spot("2025-01-03T15:29:00+05:30", 100, 100),
                spot("2025-01-06T09:15:00+05:30", 100, 101),
            ],
            contracts=[],
            expiries=["2025-01-09"],
        )

        result = [item for item in results if item.entry_date == "2025-01-06"][0]
        self.assertEqual("SKIPPED", result.status)
        self.assertEqual("flat_open", result.skip_reason)
        self.assertEqual([], trade_rows)

    def test_atm_nearest_50_uses_0915_open(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[
                spot("2025-01-03T15:29:00+05:30", 23600, 23600),
                spot("2025-01-06T09:15:00+05:30", 23675, 23680),
            ],
            contracts=[
                ("2025-01-09", 23700, "CE", [opt("2025-01-06T09:15:00+05:30", 50, 55)]),
                ("2025-01-09", 23700, "PE", [opt("2025-01-06T09:15:00+05:30", 60, 58)]),
            ],
        )

        result = self.traded_result(results, "2025-01-06")
        self.assertEqual("23700", result.atm_strike)
        self.assertEqual("2025-01-09", result.expiry_date)

    def test_first_trading_day_skips_without_previous_close(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[spot("2025-01-06T09:15:00+05:30", 100, 101)],
            contracts=[],
            expiries=["2025-01-09"],
        )

        self.assertEqual("SKIPPED", results[0].status)
        self.assertEqual("no_previous_close", results[0].skip_reason)

    def test_missing_option_file_skips_day(self) -> None:
        results, trade_rows = self.run_scenario(
            spot_rows=[
                spot("2025-01-03T15:29:00+05:30", 100, 100),
                spot("2025-01-06T09:15:00+05:30", 90, 91),
            ],
            contracts=[
                ("2025-01-09", 100, "CE", [opt("2025-01-06T09:15:00+05:30", 10, 16)]),
            ],
            expiries=["2025-01-09"],
        )

        result = [item for item in results if item.entry_date == "2025-01-06"][0]
        self.assertEqual("SKIPPED", result.status)
        self.assertEqual("missing_option_file", result.skip_reason)
        self.assertEqual([], trade_rows)

    def test_missing_0915_option_candle_skips_day(self) -> None:
        results, _ = self.run_scenario(
            spot_rows=[
                spot("2025-01-03T15:29:00+05:30", 100, 100),
                spot("2025-01-06T09:15:00+05:30", 90, 91),
            ],
            contracts=[
                ("2025-01-09", 100, "CE", [opt("2025-01-06T09:16:00+05:30", 10, 16)]),
                ("2025-01-09", 100, "PE", [opt("2025-01-06T09:15:00+05:30", 20, 25)]),
            ],
        )

        result = [item for item in results if item.entry_date == "2025-01-06"][0]
        self.assertEqual("SKIPPED", result.status)
        self.assertEqual("missing_option_timestamp", result.skip_reason)
        self.assertIn("missing 09:15 timestamp", result.remarks)


def spot(timestamp: str, open_value: float, close_value: float) -> dict[str, str]:
    return {
        "timestamp": timestamp,
        "open": f"{open_value:.2f}",
        "high": f"{max(open_value, close_value):.2f}",
        "low": f"{min(open_value, close_value):.2f}",
        "close": f"{close_value:.2f}",
        "volume": "0",
    }


def opt(timestamp: str, open_value: float, close_value: float) -> dict[str, str]:
    return {
        "timestamp": timestamp,
        "open": f"{open_value:.2f}",
        "high": f"{max(open_value, close_value):.2f}",
        "low": f"{min(open_value, close_value):.2f}",
        "close": f"{close_value:.2f}",
        "volume": "0",
        "oi": "0",
    }


if __name__ == "__main__":
    unittest.main()
