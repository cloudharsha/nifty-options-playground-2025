#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


IST_SUFFIX = "+05:30"
SIGNAL_CANDLE_TIMES = ("14:45", "15:00", "15:15")
DAYWISE_FILENAME = "nifty_last_3_green_overnight_15m_daywise.csv"
MONTHLY_FILENAME = "nifty_last_3_green_overnight_15m_monthly.csv"
YEARLY_FILENAME = "nifty_last_3_green_overnight_15m_yearly.csv"
SUMMARY_FILENAME = "nifty_last_3_green_overnight_15m_summary.md"
LOG_FILENAME = "nifty_last_3_green_overnight_15m.log"


@dataclass
class PriceRow:
    timestamp: str
    open_value: float
    open_text: str
    close_value: float
    close_text: str


@dataclass
class SpotData:
    rows_by_timestamp: Dict[str, PriceRow]
    trading_days: List[str]


@dataclass
class TradeResult:
    entry_date: str
    status: str
    skip_reason: str
    direction: str
    next_trading_day: str
    candle_1_timestamp: str
    candle_1_open: str
    candle_1_close: str
    candle_1_color: str
    candle_2_timestamp: str
    candle_2_open: str
    candle_2_close: str
    candle_2_color: str
    candle_3_timestamp: str
    candle_3_open: str
    candle_3_close: str
    candle_3_color: str
    entry_timestamp: str
    entry_price_points: str
    exit_timestamp: str
    exit_open_points: str
    points_pnl: str
    rupees_pnl: str
    remarks: str


@dataclass
class AggregateResult:
    period: str
    days: str
    trades: str
    skipped: str
    long_trades: str
    short_trades: str
    winning_trades: str
    losing_trades: str
    break_even_trades: str
    total_points: str
    total_rupees: str
    average_points: str
    max_profit_date: str
    max_profit_points: str
    max_profit_rupees: str
    max_loss_date: str
    max_loss_points: str
    max_loss_rupees: str
    max_consecutive_wins: str
    max_consecutive_losses: str
    max_drawdown_points: str
    max_drawdown_rupees: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Backtest a NIFTY spot overnight strategy that buys after three green "
            "final 15-minute candles and sells after three red final candles."
        ),
    )
    parser.add_argument(
        "--spot-file",
        type=Path,
        default=repo_root / "nifty" / "NIFTY50_INDEX_15m_last_4y.csv",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=repo_root / "backtesting" / "results",
    )
    parser.add_argument("--exit-time", default="09:15")
    parser.add_argument("--rupees-per-point", type=float, default=65.0)
    parser.add_argument("--start-date", default="")
    parser.add_argument("--end-date", default="")
    args = parser.parse_args()

    validate_optional_date(parser, args.start_date, "--start-date")
    validate_optional_date(parser, args.end_date, "--end-date")
    validate_time(parser, args.exit_time, "--exit-time")
    if args.start_date and args.end_date and args.start_date > args.end_date:
        parser.error("--start-date must be <= --end-date")
    if args.rupees_per_point <= 0:
        parser.error("--rupees-per-point must be positive")

    return args


def validate_optional_date(parser: argparse.ArgumentParser, value: str, name: str) -> None:
    if not value:
        return
    parts = value.split("-")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        parser.error(f"{name} must be YYYY-MM-DD")
    year, month, day = (int(part) for part in parts)
    if not (year >= 1900 and 1 <= month <= 12 and 1 <= day <= 31):
        parser.error(f"{name} must be YYYY-MM-DD")


def validate_time(parser: argparse.ArgumentParser, value: str, name: str) -> None:
    parts = value.split(":")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        parser.error(f"{name} must be HH:MM")
    hour, minute = (int(part) for part in parts)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        parser.error(f"{name} must be HH:MM")


def build_timestamp(day: str, time_text: str) -> str:
    parts = time_text.split(":")
    if len(parts) != 2:
        raise ValueError(f"Time must be HH:MM, got {time_text!r}")
    hour, minute = parts
    return f"{day}T{hour}:{minute}:00{IST_SUFFIX}"


def format_number(value: float) -> str:
    return f"{value:.2f}"


def candle_color(row: PriceRow) -> str:
    if row.close_value > row.open_value:
        return "GREEN"
    if row.close_value < row.open_value:
        return "RED"
    return "DOJI"


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("nifty_last_3_green_overnight_15m")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def load_spot_data(spot_file: Path) -> SpotData:
    rows_by_timestamp: Dict[str, PriceRow] = {}
    trading_days: List[str] = []
    seen_days: set[str] = set()

    with spot_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = row["timestamp"]
            price_row = PriceRow(
                timestamp=timestamp,
                open_value=float(row["open"]),
                open_text=row["open"],
                close_value=float(row["close"]),
                close_text=row["close"],
            )
            rows_by_timestamp[timestamp] = price_row

            day = timestamp[:10]
            if day not in seen_days:
                trading_days.append(day)
                seen_days.add(day)

    return SpotData(rows_by_timestamp=rows_by_timestamp, trading_days=trading_days)


def filtered_trading_days(trading_days: List[str], start_date: str, end_date: str) -> List[str]:
    days = trading_days
    if start_date:
        days = [day for day in days if day >= start_date]
    if end_date:
        days = [day for day in days if day <= end_date]
    return days


def empty_result(entry_date: str, status: str, skip_reason: str, remarks: str = "") -> TradeResult:
    return TradeResult(
        entry_date=entry_date,
        status=status,
        skip_reason=skip_reason,
        direction="",
        next_trading_day="",
        candle_1_timestamp="",
        candle_1_open="",
        candle_1_close="",
        candle_1_color="",
        candle_2_timestamp="",
        candle_2_open="",
        candle_2_close="",
        candle_2_color="",
        candle_3_timestamp="",
        candle_3_open="",
        candle_3_close="",
        candle_3_color="",
        entry_timestamp="",
        entry_price_points="",
        exit_timestamp="",
        exit_open_points="",
        points_pnl=format_number(0.0),
        rupees_pnl=format_number(0.0),
        remarks=remarks,
    )


def with_signal_candles(result: TradeResult, candle_rows: List[PriceRow]) -> TradeResult:
    if len(candle_rows) >= 1:
        result.candle_1_timestamp = candle_rows[0].timestamp
        result.candle_1_open = candle_rows[0].open_text
        result.candle_1_close = candle_rows[0].close_text
        result.candle_1_color = candle_color(candle_rows[0])
    if len(candle_rows) >= 2:
        result.candle_2_timestamp = candle_rows[1].timestamp
        result.candle_2_open = candle_rows[1].open_text
        result.candle_2_close = candle_rows[1].close_text
        result.candle_2_color = candle_color(candle_rows[1])
    if len(candle_rows) >= 3:
        result.candle_3_timestamp = candle_rows[2].timestamp
        result.candle_3_open = candle_rows[2].open_text
        result.candle_3_close = candle_rows[2].close_text
        result.candle_3_color = candle_color(candle_rows[2])
        result.entry_timestamp = candle_rows[2].timestamp
        result.entry_price_points = candle_rows[2].close_text
    return result


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    spot_data = load_spot_data(args.spot_file)
    candidate_days = filtered_trading_days(
        spot_data.trading_days,
        args.start_date,
        args.end_date,
    )
    next_day_by_day = {
        spot_data.trading_days[index]: spot_data.trading_days[index + 1] if index + 1 < len(spot_data.trading_days) else ""
        for index in range(len(spot_data.trading_days))
    }
    results: List[TradeResult] = []

    try:
        for entry_date in candidate_days:
            signal_timestamps = [build_timestamp(entry_date, time_text) for time_text in SIGNAL_CANDLE_TIMES]
            candle_rows: List[PriceRow] = []
            missing_timestamps: List[str] = []
            for timestamp in signal_timestamps:
                row = spot_data.rows_by_timestamp.get(timestamp)
                if row is None:
                    missing_timestamps.append(timestamp)
                else:
                    candle_rows.append(row)

            if missing_timestamps:
                result = empty_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="missing_signal_candle",
                    remarks="Missing signal candle(s): " + ", ".join(missing_timestamps),
                )
                with_signal_candles(result, candle_rows)
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            result = with_signal_candles(
                empty_result(entry_date=entry_date, status="SKIPPED", skip_reason=""),
                candle_rows,
            )
            colors = [candle_color(row) for row in candle_rows]
            if colors == ["GREEN", "GREEN", "GREEN"]:
                result.direction = "LONG"
            elif colors == ["RED", "RED", "RED"]:
                result.direction = "SHORT"
            else:
                result.skip_reason = "last_3_candles_not_same_direction"
                result.remarks = f"Signal candle colors were {', '.join(colors)}."
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s colors=%s", entry_date, result.skip_reason, ",".join(colors))
                continue

            next_trading_day = next_day_by_day[entry_date]
            result.next_trading_day = next_trading_day
            if not next_trading_day:
                result.status = "SKIPPED"
                result.skip_reason = "no_next_trading_day"
                result.remarks = "No next trading day exists in the dataset."
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            exit_timestamp = build_timestamp(next_trading_day, args.exit_time)
            result.exit_timestamp = exit_timestamp
            exit_row = spot_data.rows_by_timestamp.get(exit_timestamp)
            if exit_row is None:
                result.status = "SKIPPED"
                result.skip_reason = "missing_exit_timestamp"
                result.remarks = f"Missing NIFTY exit timestamp {exit_timestamp}."
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            entry_row = candle_rows[-1]
            if result.direction == "LONG":
                points_pnl = exit_row.open_value - entry_row.close_value
            else:
                points_pnl = entry_row.close_value - exit_row.open_value
            rupees_pnl = points_pnl * args.rupees_per_point
            result.status = "TRADED"
            result.skip_reason = ""
            result.exit_open_points = exit_row.open_text
            result.points_pnl = format_number(points_pnl)
            result.rupees_pnl = format_number(rupees_pnl)
            result.remarks = ""
            results.append(result)
            logger.info(
                "TRADED date=%s direction=%s next=%s entry=%s exit=%s points=%s rupees=%s",
                entry_date,
                result.direction,
                next_trading_day,
                result.entry_price_points,
                result.exit_open_points,
                result.points_pnl,
                result.rupees_pnl,
            )
    except Exception:
        logger.exception("ERROR unexpected failure while running the backtest")
        raise

    traded_count = sum(1 for result in results if result.status == "TRADED")
    skipped_count = sum(1 for result in results if result.status == "SKIPPED")
    logger.info("COMPLETED traded=%s skipped=%s total=%s", traded_count, skipped_count, len(results))
    return results


def write_daywise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "skip_reason",
        "direction",
        "next_trading_day",
        "candle_1_timestamp",
        "candle_1_open",
        "candle_1_close",
        "candle_1_color",
        "candle_2_timestamp",
        "candle_2_open",
        "candle_2_close",
        "candle_2_color",
        "candle_3_timestamp",
        "candle_3_open",
        "candle_3_close",
        "candle_3_color",
        "entry_timestamp",
        "entry_price_points",
        "exit_timestamp",
        "exit_open_points",
        "points_pnl",
        "rupees_pnl",
        "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)


def compute_max_consecutive_streaks(point_values: List[float]) -> Tuple[int, int]:
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    current_wins = 0
    current_losses = 0

    for points_pnl in point_values:
        if points_pnl > 0:
            current_wins += 1
            current_losses = 0
            max_consecutive_wins = max(max_consecutive_wins, current_wins)
        elif points_pnl < 0:
            current_losses += 1
            current_wins = 0
            max_consecutive_losses = max(max_consecutive_losses, current_losses)
        else:
            current_wins = 0
            current_losses = 0

    return max_consecutive_wins, max_consecutive_losses


def compute_max_drawdown(point_values: List[float]) -> float:
    cumulative_points = 0.0
    equity_peak = 0.0
    max_drawdown = 0.0

    for points_pnl in point_values:
        cumulative_points += points_pnl
        equity_peak = max(equity_peak, cumulative_points)
        max_drawdown = max(max_drawdown, equity_peak - cumulative_points)

    return max_drawdown


def aggregate_results(period: str, results: List[TradeResult], rupees_per_point: float) -> AggregateResult:
    traded_results = [result for result in results if result.status == "TRADED"]
    skipped_results = [result for result in results if result.status == "SKIPPED"]
    point_values = [float(result.points_pnl) for result in traded_results]
    total_points = sum(point_values)
    total_rupees = total_points * rupees_per_point
    average_points = total_points / len(traded_results) if traded_results else 0.0
    winning_trades = sum(1 for value in point_values if value > 0)
    losing_trades = sum(1 for value in point_values if value < 0)
    break_even_trades = sum(1 for value in point_values if value == 0)
    long_trades = sum(1 for result in traded_results if result.direction == "LONG")
    short_trades = sum(1 for result in traded_results if result.direction == "SHORT")
    max_profit = max(traded_results, key=lambda result: float(result.points_pnl), default=None)
    max_loss = min(traded_results, key=lambda result: float(result.points_pnl), default=None)
    max_consecutive_wins, max_consecutive_losses = compute_max_consecutive_streaks(point_values)
    max_drawdown_points = compute_max_drawdown(point_values)

    return AggregateResult(
        period=period,
        days=str(len(results)),
        trades=str(len(traded_results)),
        skipped=str(len(skipped_results)),
        long_trades=str(long_trades),
        short_trades=str(short_trades),
        winning_trades=str(winning_trades),
        losing_trades=str(losing_trades),
        break_even_trades=str(break_even_trades),
        total_points=format_number(total_points),
        total_rupees=format_number(total_rupees),
        average_points=format_number(average_points),
        max_profit_date=max_profit.entry_date if max_profit else "",
        max_profit_points=max_profit.points_pnl if max_profit else "",
        max_profit_rupees=format_number(float(max_profit.points_pnl) * rupees_per_point) if max_profit else "",
        max_loss_date=max_loss.entry_date if max_loss else "",
        max_loss_points=max_loss.points_pnl if max_loss else "",
        max_loss_rupees=format_number(float(max_loss.points_pnl) * rupees_per_point) if max_loss else "",
        max_consecutive_wins=str(max_consecutive_wins),
        max_consecutive_losses=str(max_consecutive_losses),
        max_drawdown_points=format_number(max_drawdown_points),
        max_drawdown_rupees=format_number(max_drawdown_points * rupees_per_point),
    )


def aggregate_by_period(results: List[TradeResult], period_length: int, rupees_per_point: float) -> List[AggregateResult]:
    grouped_results: Dict[str, List[TradeResult]] = {}
    for result in results:
        period = result.entry_date[:period_length]
        grouped_results.setdefault(period, []).append(result)

    return [
        aggregate_results(period, grouped_results[period], rupees_per_point)
        for period in sorted(grouped_results)
    ]


def write_aggregate_csv(results: List[AggregateResult], output_path: Path) -> None:
    fieldnames = [
        "period",
        "days",
        "trades",
        "skipped",
        "long_trades",
        "short_trades",
        "winning_trades",
        "losing_trades",
        "break_even_trades",
        "total_points",
        "total_rupees",
        "average_points",
        "max_profit_date",
        "max_profit_points",
        "max_profit_rupees",
        "max_loss_date",
        "max_loss_points",
        "max_loss_rupees",
        "max_consecutive_wins",
        "max_consecutive_losses",
        "max_drawdown_points",
        "max_drawdown_rupees",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)


def aggregate_table_lines(rows: List[AggregateResult]) -> List[str]:
    lines = [
        "| Period | Days | Trades | Skipped | Long | Short | Wins | Losses | BE | Points | Rupees | Avg Points | Max Profit | Max Loss | Win Streak | Loss Streak | Max DD Points | Max DD Rupees |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.period} | "
            f"{row.days} | "
            f"{row.trades} | "
            f"{row.skipped} | "
            f"{row.long_trades} | "
            f"{row.short_trades} | "
            f"{row.winning_trades} | "
            f"{row.losing_trades} | "
            f"{row.break_even_trades} | "
            f"{row.total_points} | "
            f"{row.total_rupees} | "
            f"{row.average_points} | "
            f"{row.max_profit_points} | "
            f"{row.max_loss_points} | "
            f"{row.max_consecutive_wins} | "
            f"{row.max_consecutive_losses} | "
            f"{row.max_drawdown_points} | "
            f"{row.max_drawdown_rupees} |"
        )
    return lines


def skip_reason_lines(results: List[TradeResult]) -> List[str]:
    counts = Counter(result.skip_reason for result in results if result.status == "SKIPPED")
    if not counts:
        return ["- None"]
    return [f"- `{reason}`: `{count}`" for reason, count in sorted(counts.items())]


def exception_lines(results: List[TradeResult]) -> List[str]:
    exceptions = [
        result
        for result in results
        if result.status == "SKIPPED" and result.skip_reason != "last_3_candles_not_same_direction"
    ]
    if not exceptions:
        return ["- None"]
    return [f"- `{result.entry_date}`: `{result.skip_reason}`. {result.remarks}" for result in exceptions]


def write_summary(
    daywise_results: List[TradeResult],
    monthly_results: List[AggregateResult],
    yearly_results: List[AggregateResult],
    output_path: Path,
    args: argparse.Namespace,
) -> None:
    overall = aggregate_results("Overall", daywise_results, args.rupees_per_point)
    first_date = daywise_results[0].entry_date if daywise_results else "N/A"
    last_date = daywise_results[-1].entry_date if daywise_results else "N/A"
    entry_time = SIGNAL_CANDLE_TIMES[-1]

    lines: List[str] = [
        "# NIFTY Last 3 Same-Color Candles Overnight Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Dataset: `{args.spot_file}`",
        f"- Tested date range: `{first_date}` through `{last_date}`",
        "- Signal source: NIFTY 15-minute candles",
        "- Long signal: the `14:45`, `15:00`, and `15:15` candles must all close above their opens",
        "- Short signal: the `14:45`, `15:00`, and `15:15` candles must all close below their opens",
        f"- Entry rule: long or short NIFTY at the `{entry_time}` candle close",
        f"- Exit rule: close the trade at the next trading day `{args.exit_time}` open",
        f"- Rupee conversion: 1 point = Rs {format_number(args.rupees_per_point)}",
        "- No brokerage, slippage, lots, or option data are used.",
        "",
        "## Overall Results",
        "",
        *aggregate_table_lines([overall]),
        "",
        "## Yearly Results",
        "",
        *aggregate_table_lines(yearly_results),
        "",
        "## Monthly Results",
        "",
        *aggregate_table_lines(monthly_results),
        "",
        "## Skip Reasons",
        "",
        *skip_reason_lines(daywise_results),
        "",
        "## Data Exceptions",
        "",
        *exception_lines(daywise_results),
        "",
        "## Remarks",
        "",
        "- Exact timestamp matching is required; no nearest-candle fallback is allowed.",
        "- The `15:15` timestamp represents the 15:15-15:30 candle in this dataset.",
        "- Yearly and monthly results are grouped by entry date.",
        "- Max drawdown is calculated from cumulative point P/L within each reported period.",
        "- Partial years are included when present in the source data.",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    daywise_results = run_backtest(args)
    monthly_results = aggregate_by_period(daywise_results, 7, args.rupees_per_point)
    yearly_results = aggregate_by_period(daywise_results, 4, args.rupees_per_point)

    write_daywise_csv(daywise_results, args.results_dir / DAYWISE_FILENAME)
    write_aggregate_csv(monthly_results, args.results_dir / MONTHLY_FILENAME)
    write_aggregate_csv(yearly_results, args.results_dir / YEARLY_FILENAME)
    write_summary(
        daywise_results,
        monthly_results,
        yearly_results,
        args.results_dir / SUMMARY_FILENAME,
        args,
    )


if __name__ == "__main__":
    main()
