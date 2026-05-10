from __future__ import annotations

import csv
import importlib.util
import logging
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "run_nifty_ma_25_50_crossover_rr_15m.py"
SPEC = importlib.util.spec_from_file_location("run_nifty_ma_25_50_crossover_rr_15m", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class NiftyMa2550CrossoverRR15mTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.{self._testMethodName}")
        self.logger.handlers.clear()
        self.logger.addHandler(logging.NullHandler())
        self.logger.propagate = False

    def run_backtest(
        self,
        rows: list[dict[str, str]],
        reward_multiple: float = 1.0,
        start_date: str = "",
        end_date: str = "",
        fast_period: int = 2,
        slow_period: int = 3,
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "spot.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["timestamp", "open", "high", "low", "close", "volume"],
                )
                writer.writeheader()
                writer.writerows(rows)

            spot_data = MODULE.load_spot_data(csv_path)
            indicators = MODULE.build_indicator_series(spot_data, fast_period, slow_period)
            return MODULE.run_backtest_for_variant(
                spot_data=spot_data,
                indicators=indicators,
                reward_multiple=reward_multiple,
                start_date=start_date,
                end_date=end_date,
                rupees_per_point=65.0,
                logger=self.logger,
            )

    def assert_traded_results(self, run):
        traded = [result for result in run.trade_results if result.status == "TRADED"]
        skipped = [result for result in run.trade_results if result.status == "SKIPPED"]
        self.assertEqual([], skipped)
        return traded

    def test_bullish_crossover_enters_long_on_next_open(self) -> None:
        run = self.run_backtest(
            [
                row("2025-01-01T09:15:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T09:30:00+05:30", 9, 9.2, 8.8, 9),
                row("2025-01-01T09:45:00+05:30", 8, 8.2, 7.8, 8),
                row("2025-01-01T10:00:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T10:15:00+05:30", 11, 12.2, 7.0, 12),
                row("2025-01-01T10:30:00+05:30", 13, 14.2, 12.5, 14),
            ],
            reward_multiple=3.0,
        )

        traded = self.assert_traded_results(run)
        self.assertEqual(1, len(traded))
        self.assertEqual("LONG", traded[0].direction)
        self.assertEqual("CROSSOVER", traded[0].setup_type)
        self.assertEqual("2025-01-01T10:15:00+05:30", traded[0].signal_timestamp)
        self.assertEqual("2025-01-01T10:30:00+05:30", traded[0].entry_timestamp)

    def test_bearish_crossover_reverses_from_long_to_short(self) -> None:
        run = self.run_backtest(
            [
                row("2025-01-01T09:15:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T09:30:00+05:30", 9, 9.2, 8.8, 9),
                row("2025-01-01T09:45:00+05:30", 8, 8.2, 7.8, 8),
                row("2025-01-01T10:00:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T10:15:00+05:30", 11, 12.2, 7.0, 12),
                row("2025-01-01T10:30:00+05:30", 13, 13.5, 12.5, 13),
                row("2025-01-01T10:45:00+05:30", 12.2, 12.5, 11.5, 10),
                row("2025-01-01T11:00:00+05:30", 9.8, 10.0, 9.0, 9.5),
            ],
            reward_multiple=3.0,
        )

        traded = self.assert_traded_results(run)
        self.assertEqual(2, len(traded))
        self.assertEqual("reversal_exit", traded[0].exit_reason)
        self.assertEqual("SHORT", traded[1].direction)
        self.assertEqual("2025-01-01T11:00:00+05:30", traded[1].entry_timestamp)

    def test_target_exit_enables_later_pullback_reentry(self) -> None:
        run = self.run_backtest(
            [
                row("2025-01-01T09:15:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T09:30:00+05:30", 9, 9.2, 8.8, 9),
                row("2025-01-01T09:45:00+05:30", 8, 8.2, 7.8, 8),
                row("2025-01-01T10:00:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T10:15:00+05:30", 11, 12.2, 11.0, 12),
                row("2025-01-01T10:30:00+05:30", 13, 15.5, 12.5, 14.5),
                row("2025-01-01T10:45:00+05:30", 13.9, 14.4, 14.0, 14.2),
                row("2025-01-01T11:00:00+05:30", 14.3, 14.5, 14.1, 14.4),
            ],
            reward_multiple=1.0,
        )

        traded = self.assert_traded_results(run)
        self.assertEqual(["target", "end_of_data"], [result.exit_reason for result in traded])
        self.assertEqual("PULLBACK_REENTRY", traded[1].setup_type)
        self.assertEqual("2025-01-01T11:00:00+05:30", traded[1].entry_timestamp)

    def test_stop_exit_blocks_pullback_reentry_until_opposite_crossover(self) -> None:
        run = self.run_backtest(
            [
                row("2025-01-01T09:15:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T09:30:00+05:30", 9, 9.2, 8.8, 9),
                row("2025-01-01T09:45:00+05:30", 8, 8.2, 7.8, 8),
                row("2025-01-01T10:00:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T10:15:00+05:30", 11, 12.2, 11.0, 12),
                row("2025-01-01T10:30:00+05:30", 13, 13.2, 10.8, 12.6),
                row("2025-01-01T10:45:00+05:30", 12.3, 12.6, 12.2, 12.5),
                row("2025-01-01T11:00:00+05:30", 12.4, 12.4, 11.4, 11.5),
                row("2025-01-01T11:15:00+05:30", 11.4, 11.6, 11.0, 11.2),
            ],
            reward_multiple=1.0,
        )

        traded = self.assert_traded_results(run)
        self.assertEqual(2, len(traded))
        self.assertEqual("stop_loss", traded[0].exit_reason)
        self.assertEqual(["CROSSOVER", "CROSSOVER"], [result.setup_type for result in traded])
        self.assertEqual("SHORT", traded[1].direction)

    def test_gap_stop_exit(self) -> None:
        run = self.run_backtest(
            [
                row("2025-01-01T14:15:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T14:30:00+05:30", 9, 9.2, 8.8, 9),
                row("2025-01-01T14:45:00+05:30", 8, 8.2, 7.8, 8),
                row("2025-01-01T15:00:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T15:15:00+05:30", 11, 12.2, 11.0, 12),
                row("2025-01-02T09:15:00+05:30", 13, 13.3, 12.8, 13.1),
                row("2025-01-02T09:30:00+05:30", 10.5, 10.7, 10.2, 10.4),
            ],
            reward_multiple=3.0,
        )

        traded = self.assert_traded_results(run)
        self.assertEqual(1, len(traded))
        self.assertEqual("gap_stop", traded[0].exit_reason)
        self.assertEqual("2025-01-02T09:30:00+05:30", traded[0].exit_timestamp)

    def test_gap_target_exit(self) -> None:
        run = self.run_backtest(
            [
                row("2025-01-01T14:15:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T14:30:00+05:30", 9, 9.2, 8.8, 9),
                row("2025-01-01T14:45:00+05:30", 8, 8.2, 7.8, 8),
                row("2025-01-01T15:00:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T15:15:00+05:30", 11, 12.2, 11.0, 12),
                row("2025-01-02T09:15:00+05:30", 13, 13.3, 12.8, 13.1),
                row("2025-01-02T09:30:00+05:30", 15.2, 15.4, 15.0, 15.3),
            ],
            reward_multiple=1.0,
        )

        traded = self.assert_traded_results(run)
        self.assertEqual(1, len(traded))
        self.assertEqual("gap_target", traded[0].exit_reason)
        self.assertEqual("2025-01-02T09:30:00+05:30", traded[0].exit_timestamp)

    def test_same_candle_stop_and_target_prefers_stop(self) -> None:
        run = self.run_backtest(
            [
                row("2025-01-01T09:15:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T09:30:00+05:30", 9, 9.2, 8.8, 9),
                row("2025-01-01T09:45:00+05:30", 8, 8.2, 7.8, 8),
                row("2025-01-01T10:00:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T10:15:00+05:30", 11, 12.2, 11.0, 12),
                row("2025-01-01T10:30:00+05:30", 13, 15.5, 10.5, 14),
            ],
            reward_multiple=1.0,
        )

        traded = self.assert_traded_results(run)
        self.assertEqual(1, len(traded))
        self.assertEqual("stop_loss", traded[0].exit_reason)
        self.assertIn("stop-first", traded[0].remarks)

    def test_1515_signal_enters_on_next_available_trading_row(self) -> None:
        run = self.run_backtest(
            [
                row("2025-01-01T14:30:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T14:45:00+05:30", 9, 9.2, 8.8, 9),
                row("2025-01-01T15:00:00+05:30", 8, 8.2, 7.8, 8),
                row("2025-01-01T15:15:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T15:30:00+05:30", 11, 12.2, 11.0, 12),
                row("2025-01-02T09:15:00+05:30", 13, 13.4, 12.8, 13.2),
            ],
            reward_multiple=3.0,
        )

        traded = self.assert_traded_results(run)
        self.assertEqual(1, len(traded))
        self.assertEqual("2025-01-01T15:30:00+05:30", traded[0].signal_timestamp)
        self.assertEqual("2025-01-02T09:15:00+05:30", traded[0].entry_timestamp)

    def test_end_date_forces_end_of_range_exit(self) -> None:
        run = self.run_backtest(
            [
                row("2025-01-01T14:15:00+05:30", 10, 10.2, 9.8, 10),
                row("2025-01-01T14:30:00+05:30", 9, 9.2, 8.8, 9),
                row("2025-01-01T14:45:00+05:30", 8, 8.2, 7.8, 8),
                row("2025-01-01T15:00:00+05:30", 11, 12.2, 11.0, 12),
                row("2025-01-01T15:15:00+05:30", 13, 13.4, 12.8, 13.2),
                row("2025-01-02T09:15:00+05:30", 13, 13.2, 12.7, 13.1),
            ],
            reward_multiple=3.0,
            end_date="2025-01-01",
        )

        traded = self.assert_traded_results(run)
        self.assertEqual(1, len(traded))
        self.assertEqual("end_of_range", traded[0].exit_reason)
        self.assertEqual("2025-01-01T15:15:00+05:30", traded[0].exit_timestamp)


def row(timestamp: str, open_value: float, high_value: float, low_value: float, close_value: float) -> dict[str, str]:
    return {
        "timestamp": timestamp,
        "open": f"{open_value:.2f}",
        "high": f"{high_value:.2f}",
        "low": f"{low_value:.2f}",
        "close": f"{close_value:.2f}",
        "volume": "0",
    }


if __name__ == "__main__":
    unittest.main()
