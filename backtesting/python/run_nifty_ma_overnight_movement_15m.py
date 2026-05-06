#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


IST_SUFFIX = "+05:30"
DAYWISE_FILENAME = "nifty_ma_overnight_movement_15m_daywise.csv"
MONTHLY_FILENAME = "nifty_ma_overnight_movement_15m_monthly.csv"
YEARLY_FILENAME = "nifty_ma_overnight_movement_15m_yearly.csv"
SUMMARY_FILENAME = "nifty_ma_overnight_movement_15m_summary.md"
LOG_FILENAME = "nifty_ma_overnight_movement_15m.log"


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
    ordered_rows: List[PriceRow]
    index_by_timestamp: Dict[str, int]
    trading_days: List[str]


@dataclass
class TradeResult:
    entry_date: str
    status: str
    skip_reason: str
    next_trading_day: str
    signal_timestamp: str
    signal_close: str
    spot_sma_25: str
    signal_relation: str
    direction: str
    entry_price_points: str
    exit_timestamp: str
    exit_open_points: str
    points_pnl: str
    rupees_pnl: str
    remarks: str


@dataclass
class AggregateResult:
    period: str
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
        description="Backtest overnight NIFTY spot movement using a 15-minute 25-SMA signal.",
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
    parser.add_argument("--signal-time", default="15:15")
    parser.add_argument("--exit-time", default="09:15")
    parser.add_argument("--ma-period", type=int, default=25)
    parser.add_argument("--rupees-per-point", type=float, default=65.0)
    parser.add_argument("--start-date", default="")
    parser.add_argument("--end-date", default="")
    args = parser.parse_args()

    validate_optional_date(parser, args.start_date, "--start-date")
    validate_optional_date(parser, args.end_date, "--end-date")
    if args.start_date and args.end_date and args.start_date > args.end_date:
        parser.error("--start-date must be <= --end-date")
    if args.ma_period <= 0:
        parser.error("--ma-period must be positive")
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
    if not (1 <= month <= 12 and 1 <= day <= 31 and year >= 1900):
        parser.error(f"{name} must be YYYY-MM-DD")


def build_timestamp(day: str, time_text: str) -> str:
    parts = time_text.split(":")
    if len(parts) != 2:
        raise ValueError(f"Time must be HH:MM, got {time_text!r}")
    hour, minute = parts
    return f"{day}T{hour}:{minute}:00{IST_SUFFIX}"


def format_number(value: float) -> str:
    return f"{value:.2f}"


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("nifty_ma_overnight_movement_15m")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def load_spot_data(spot_file: Path) -> SpotData:
    rows_by_timestamp: Dict[str, PriceRow] = {}
    ordered_rows: List[PriceRow] = []
    index_by_timestamp: Dict[str, int] = {}
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
            index_by_timestamp[timestamp] = len(ordered_rows)
            ordered_rows.append(price_row)
            rows_by_timestamp[timestamp] = price_row

            day = timestamp[:10]
            if day not in seen_days:
                trading_days.append(day)
                seen_days.add(day)

    return SpotData(
        rows_by_timestamp=rows_by_timestamp,
        ordered_rows=ordered_rows,
        index_by_timestamp=index_by_timestamp,
        trading_days=trading_days,
    )


def compute_spot_sma_including_current(
    spot_data: SpotData,
    timestamp: str,
    ma_period: int,
) -> Tuple[Optional[float], int]:
    index = spot_data.index_by_timestamp.get(timestamp)
    if index is None:
        return None, 0
    observed_count = index + 1
    if observed_count < ma_period:
        return None, observed_count
    window = spot_data.ordered_rows[index - ma_period + 1 : index + 1]
    sma = sum(row.close_value for row in window) / ma_period
    return sma, observed_count


def make_result(
    entry_date: str,
    status: str,
    skip_reason: str,
    next_trading_day: str = "",
    signal_timestamp: str = "",
    signal_close: str = "",
    spot_sma_25: str = "",
    signal_relation: str = "",
    direction: str = "",
    entry_price_points: str = "",
    exit_timestamp: str = "",
    exit_open_points: str = "",
    points_pnl: float = 0.0,
    rupees_pnl: float = 0.0,
    remarks: str = "",
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date,
        status=status,
        skip_reason=skip_reason,
        next_trading_day=next_trading_day,
        signal_timestamp=signal_timestamp,
        signal_close=signal_close,
        spot_sma_25=spot_sma_25,
        signal_relation=signal_relation,
        direction=direction,
        entry_price_points=entry_price_points,
        exit_timestamp=exit_timestamp,
        exit_open_points=exit_open_points,
        points_pnl=format_number(points_pnl),
        rupees_pnl=format_number(rupees_pnl),
        remarks=remarks,
    )


def filtered_trading_days(trading_days: List[str], start_date: str, end_date: str) -> List[str]:
    days = trading_days
    if start_date:
        days = [day for day in days if day >= start_date]
    if end_date:
        days = [day for day in days if day <= end_date]
    return days


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
            signal_timestamp = build_timestamp(entry_date, args.signal_time)
            signal_row = spot_data.rows_by_timestamp.get(signal_timestamp)
            if signal_row is None:
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="missing_signal_timestamp",
                    signal_timestamp=signal_timestamp,
                    remarks=f"Missing NIFTY signal timestamp {signal_timestamp}",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            spot_sma_25, observed_count = compute_spot_sma_including_current(
                spot_data,
                signal_timestamp,
                args.ma_period,
            )
            if spot_sma_25 is None:
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="insufficient_spot_history",
                    signal_timestamp=signal_timestamp,
                    signal_close=signal_row.close_text,
                    remarks=(
                        f"{signal_timestamp} has {observed_count} spot bars including the signal bar; "
                        f"needs {args.ma_period}"
                    ),
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            signal_close = signal_row.close_text
            spot_sma_text = format_number(spot_sma_25)
            entry_price = signal_row.close_value
            next_trading_day = next_day_by_day[entry_date]
            if not next_trading_day:
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="no_next_trading_day",
                    signal_timestamp=signal_timestamp,
                    signal_close=signal_close,
                    spot_sma_25=spot_sma_text,
                    entry_price_points=signal_close,
                    remarks="No next trading day exists in the dataset.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            exit_timestamp = build_timestamp(next_trading_day, args.exit_time)
            exit_row = spot_data.rows_by_timestamp.get(exit_timestamp)
            if exit_row is None:
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="missing_exit_timestamp",
                    next_trading_day=next_trading_day,
                    signal_timestamp=signal_timestamp,
                    signal_close=signal_close,
                    spot_sma_25=spot_sma_text,
                    entry_price_points=signal_close,
                    exit_timestamp=exit_timestamp,
                    remarks=f"Missing NIFTY exit timestamp {exit_timestamp}",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            if signal_row.close_value > spot_sma_25:
                signal_relation = "ABOVE_SMA"
                direction = "LONG"
                points_pnl = exit_row.open_value - entry_price
            elif signal_row.close_value < spot_sma_25:
                signal_relation = "BELOW_SMA"
                direction = "SHORT"
                points_pnl = entry_price - exit_row.open_value
            else:
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="equal_close_and_sma",
                    next_trading_day=next_trading_day,
                    signal_timestamp=signal_timestamp,
                    signal_close=signal_close,
                    spot_sma_25=spot_sma_text,
                    signal_relation="EQUAL_SMA",
                    entry_price_points=signal_close,
                    exit_timestamp=exit_timestamp,
                    exit_open_points=exit_row.open_text,
                    remarks=(
                        f"NIFTY close {signal_close} equals {args.ma_period}-SMA "
                        f"{spot_sma_text} at {signal_timestamp}"
                    ),
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            rupees_pnl = points_pnl * args.rupees_per_point
            result = make_result(
                entry_date=entry_date,
                status="TRADED",
                skip_reason="",
                next_trading_day=next_trading_day,
                signal_timestamp=signal_timestamp,
                signal_close=signal_close,
                spot_sma_25=spot_sma_text,
                signal_relation=signal_relation,
                direction=direction,
                entry_price_points=signal_close,
                exit_timestamp=exit_timestamp,
                exit_open_points=exit_row.open_text,
                points_pnl=points_pnl,
                rupees_pnl=rupees_pnl,
            )
            results.append(result)
            logger.info(
                "TRADED date=%s direction=%s next=%s points=%s rupees=%s",
                entry_date,
                direction,
                next_trading_day,
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
        "next_trading_day",
        "signal_timestamp",
        "signal_close",
        "spot_sma_25",
        "signal_relation",
        "direction",
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
    points_values = [float(result.points_pnl) for result in traded_results]
    total_points = sum(points_values)
    total_rupees = total_points * rupees_per_point
    average_points = total_points / len(traded_results) if traded_results else 0.0
    winning_trades = sum(1 for value in points_values if value > 0)
    losing_trades = sum(1 for value in points_values if value < 0)
    break_even_trades = sum(1 for value in points_values if value == 0)
    long_trades = sum(1 for result in traded_results if result.direction == "LONG")
    short_trades = sum(1 for result in traded_results if result.direction == "SHORT")
    max_profit = max(traded_results, key=lambda result: float(result.points_pnl), default=None)
    max_loss = min(traded_results, key=lambda result: float(result.points_pnl), default=None)
    max_consecutive_wins, max_consecutive_losses = compute_max_consecutive_streaks(points_values)
    max_drawdown_points = compute_max_drawdown(points_values)

    return AggregateResult(
        period=period,
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
        "| Period | Trades | Skipped | Long | Short | Wins | Losses | BE | Points | Rupees | Avg Points | Max Profit | Max Loss | Win Streak | Loss Streak | Max DD Points | Max DD Rupees |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.period} | "
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


def write_summary(
    daywise_results: List[TradeResult],
    monthly_results: List[AggregateResult],
    yearly_results: List[AggregateResult],
    output_path: Path,
    args: argparse.Namespace,
) -> None:
    overall = aggregate_results("Overall", daywise_results, args.rupees_per_point)
    skipped_results = [result for result in daywise_results if result.status == "SKIPPED"]
    first_date = daywise_results[0].entry_date if daywise_results else "N/A"
    last_date = daywise_results[-1].entry_date if daywise_results else "N/A"

    lines: List[str] = [
        "# NIFTY 25-SMA Overnight Movement Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Dataset: `{args.spot_file}`",
        f"- Tested date range: `{first_date}` through `{last_date}`",
        "- Signal source: NIFTY 15-minute close",
        f"- Signal time: `{args.signal_time}`",
        f"- Exit time: next trading day `{args.exit_time}` open",
        f"- MA rule: {args.ma_period}-SMA of 15-minute closes including the signal candle",
        "- Direction rule: above SMA -> long NIFTY; below SMA -> short NIFTY; equal -> no trade",
        "- Entry price: signal candle close",
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
        "## Exceptions",
        "",
    ]

    if skipped_results:
        for result in skipped_results:
            lines.append(f"- `{result.entry_date}`: `{result.skip_reason}`. {result.remarks}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Remarks",
            "",
            "- Exact timestamp matching is required; no nearest-candle fallback is allowed.",
            "- Special sessions without the normal signal or exit timestamp are skipped.",
            "- Yearly and monthly results are grouped by entry date.",
            "- Max drawdown is calculated from cumulative point P/L within each reported period.",
            "- Partial years are included when present in the source data.",
        ]
    )

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
