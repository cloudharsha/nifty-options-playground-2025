#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


IST_SUFFIX = "+05:30"
TRADES_FILENAME = "nifty_ma_intraday_trailing_15m_trades.csv"
DAYWISE_FILENAME = "nifty_ma_intraday_trailing_15m_daywise.csv"
MONTHLY_FILENAME = "nifty_ma_intraday_trailing_15m_monthly.csv"
YEARLY_FILENAME = "nifty_ma_intraday_trailing_15m_yearly.csv"
SUMMARY_FILENAME = "nifty_ma_intraday_trailing_15m_summary.md"
LOG_FILENAME = "nifty_ma_intraday_trailing_15m.log"


@dataclass
class PriceRow:
    timestamp: str
    open_value: float
    open_text: str
    high_value: float
    high_text: str
    low_value: float
    low_text: str
    close_value: float
    close_text: str


@dataclass
class SpotData:
    rows_by_timestamp: Dict[str, PriceRow]
    ordered_rows: List[PriceRow]
    index_by_timestamp: Dict[str, int]
    trading_days: List[str]


@dataclass
class ActiveTrade:
    entry_date: str
    signal_timestamp: str
    entry_timestamp: str
    signal_close: str
    direction: str
    entry_price: float
    entry_price_text: str
    entry_sma: float
    stop_sma: float


@dataclass
class TradeResult:
    entry_date: str
    status: str
    skip_reason: str
    signal_timestamp: str
    entry_timestamp: str
    signal_close: str
    direction: str
    entry_price_points: str
    entry_sma_25: str
    exit_candle_timestamp: str
    exit_timestamp: str
    exit_price_points: str
    exit_reason: str
    exit_sma_25: str
    points_pnl: str
    rupees_pnl: str
    remarks: str


@dataclass
class DayResult:
    entry_date: str
    status: str
    skip_reason: str
    trades: str
    skipped_rows: str
    long_trades: str
    short_trades: str
    stop_exits: str
    day_close_exits: str
    winning_trades: str
    losing_trades: str
    break_even_trades: str
    total_points: str
    total_rupees: str
    average_points: str
    max_profit_points: str
    max_loss_points: str
    max_consecutive_wins: str
    max_consecutive_losses: str
    max_drawdown_points: str
    max_drawdown_rupees: str
    remarks: str


@dataclass
class AggregateResult:
    period: str
    days: str
    skipped_days: str
    trades: str
    skipped_rows: str
    long_trades: str
    short_trades: str
    stop_exits: str
    day_close_exits: str
    winning_days: str
    losing_days: str
    break_even_days: str
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
        description="Backtest intraday NIFTY spot movement using a 15-minute 25-SMA trailing stop.",
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
    parser.add_argument("--entry-start-time", default="09:30")
    parser.add_argument("--last-entry-time", default="15:00")
    parser.add_argument("--exit-time", default="15:15")
    parser.add_argument("--ma-period", type=int, default=25)
    parser.add_argument("--rupees-per-point", type=float, default=65.0)
    parser.add_argument("--start-date", default="")
    parser.add_argument("--end-date", default="")
    args = parser.parse_args()

    validate_optional_date(parser, args.start_date, "--start-date")
    validate_optional_date(parser, args.end_date, "--end-date")
    if args.start_date and args.end_date and args.start_date > args.end_date:
        parser.error("--start-date must be <= --end-date")
    if not (args.entry_start_time <= args.last_entry_time < args.exit_time):
        parser.error("--entry-start-time must be <= --last-entry-time and --last-entry-time must be < --exit-time")
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


def timestamp_to_datetime(timestamp: str) -> datetime.datetime:
    return datetime.datetime.strptime(timestamp[:19], "%Y-%m-%dT%H:%M:%S")


def datetime_to_timestamp(value: datetime.datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:00") + IST_SUFFIX


def shift_timestamp(timestamp: str, minutes: int) -> str:
    return datetime_to_timestamp(timestamp_to_datetime(timestamp) + datetime.timedelta(minutes=minutes))


def build_intraday_boundaries(day: str, start_time: str, end_time: str, step_minutes: int = 15) -> List[str]:
    start_dt = datetime.datetime.strptime(f"{day} {start_time}", "%Y-%m-%d %H:%M")
    end_dt = datetime.datetime.strptime(f"{day} {end_time}", "%Y-%m-%d %H:%M")
    timestamps: List[str] = []
    current_dt = start_dt
    while current_dt <= end_dt:
        timestamps.append(datetime_to_timestamp(current_dt))
        current_dt += datetime.timedelta(minutes=step_minutes)
    return timestamps


def signal_timestamp_for_boundary(boundary_timestamp: str) -> str:
    return shift_timestamp(boundary_timestamp, -15)


def format_number(value: float) -> str:
    return f"{value:.2f}"


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("nifty_ma_intraday_trailing_15m")
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
                high_value=float(row["high"]),
                high_text=row["high"],
                low_value=float(row["low"]),
                low_text=row["low"],
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


def filtered_trading_days(trading_days: List[str], start_date: str, end_date: str) -> List[str]:
    days = trading_days
    if start_date:
        days = [day for day in days if day >= start_date]
    if end_date:
        days = [day for day in days if day <= end_date]
    return days


def make_skipped_trade(entry_date: str, skip_reason: str, remarks: str) -> TradeResult:
    return TradeResult(
        entry_date=entry_date,
        status="SKIPPED",
        skip_reason=skip_reason,
        signal_timestamp="",
        entry_timestamp="",
        signal_close="",
        direction="",
        entry_price_points="",
        entry_sma_25="",
        exit_candle_timestamp="",
        exit_timestamp="",
        exit_price_points="",
        exit_reason="",
        exit_sma_25="",
        points_pnl="0.00",
        rupees_pnl="0.00",
        remarks=remarks,
    )


def make_traded_result(
    active_trade: ActiveTrade,
    exit_candle_timestamp: str,
    exit_timestamp: str,
    exit_price: float,
    exit_reason: str,
    exit_sma: float,
    rupees_per_point: float,
) -> TradeResult:
    if active_trade.direction == "LONG":
        points_pnl = exit_price - active_trade.entry_price
    else:
        points_pnl = active_trade.entry_price - exit_price
    points_pnl_text = format_number(points_pnl)
    rupees_pnl = float(points_pnl_text) * rupees_per_point

    return TradeResult(
        entry_date=active_trade.entry_date,
        status="TRADED",
        skip_reason="",
        signal_timestamp=active_trade.signal_timestamp,
        entry_timestamp=active_trade.entry_timestamp,
        signal_close=active_trade.signal_close,
        direction=active_trade.direction,
        entry_price_points=active_trade.entry_price_text,
        entry_sma_25=format_number(active_trade.entry_sma),
        exit_candle_timestamp=exit_candle_timestamp,
        exit_timestamp=exit_timestamp,
        exit_price_points=format_number(exit_price),
        exit_reason=exit_reason,
        exit_sma_25=format_number(exit_sma),
        points_pnl=points_pnl_text,
        rupees_pnl=format_number(rupees_pnl),
        remarks="",
    )


def missing_required_timestamps(
    spot_data: SpotData,
    day: str,
    entry_start_time: str,
    exit_time: str,
) -> List[str]:
    first_required = signal_timestamp_for_boundary(build_timestamp(day, entry_start_time))
    last_required = signal_timestamp_for_boundary(build_timestamp(day, exit_time))
    required_timestamps = build_intraday_boundaries(
        day,
        first_required[11:16],
        last_required[11:16],
    )
    return [
        timestamp
        for timestamp in required_timestamps
        if timestamp not in spot_data.rows_by_timestamp
    ]


def summarize_timestamps(label: str, timestamps: List[str], edge_count: int = 5) -> str:
    if len(timestamps) <= edge_count * 2:
        return f"{label}: " + ", ".join(timestamps)
    first_values = ", ".join(timestamps[:edge_count])
    last_values = ", ".join(timestamps[-edge_count:])
    return (
        f"{label}: {len(timestamps)} missing timestamps from {timestamps[0]} through {timestamps[-1]}; "
        f"first {edge_count}: {first_values}; last {edge_count}: {last_values}"
    )


def evaluate_entry(
    spot_data: SpotData,
    day: str,
    boundary_timestamp: str,
    ma_period: int,
) -> Tuple[Optional[ActiveTrade], str, str]:
    signal_timestamp = signal_timestamp_for_boundary(boundary_timestamp)
    signal_row = spot_data.rows_by_timestamp.get(signal_timestamp)
    if signal_row is None:
        return None, "missing_signal_timestamp", f"Missing NIFTY signal timestamp {signal_timestamp}"

    entry_sma, observed_count = compute_spot_sma_including_current(
        spot_data,
        signal_timestamp,
        ma_period,
    )
    if entry_sma is None:
        return (
            None,
            "insufficient_spot_history",
            f"{signal_timestamp} has {observed_count} spot bars including the signal bar; needs {ma_period}",
        )

    if signal_row.close_value > entry_sma:
        direction = "LONG"
    elif signal_row.close_value < entry_sma:
        direction = "SHORT"
    else:
        return (
            None,
            "equal_close_and_sma",
            f"NIFTY close {signal_row.close_text} equals {ma_period}-SMA {format_number(entry_sma)} at {signal_timestamp}",
        )

    return (
        ActiveTrade(
            entry_date=day,
            signal_timestamp=signal_timestamp,
            entry_timestamp=boundary_timestamp,
            signal_close=signal_row.close_text,
            direction=direction,
            entry_price=signal_row.close_value,
            entry_price_text=signal_row.close_text,
            entry_sma=entry_sma,
            stop_sma=entry_sma,
        ),
        "",
        "",
    )


def run_day(
    spot_data: SpotData,
    day: str,
    args: argparse.Namespace,
    logger: logging.Logger,
) -> List[TradeResult]:
    missing_timestamps = missing_required_timestamps(
        spot_data,
        day,
        args.entry_start_time,
        args.exit_time,
    )
    if missing_timestamps:
        return [
            make_skipped_trade(
                entry_date=day,
                skip_reason="missing_required_session_timestamp",
                remarks=summarize_timestamps("Missing required NIFTY timestamps", missing_timestamps),
            )
        ]

    close_boundaries = build_intraday_boundaries(
        day,
        args.entry_start_time,
        args.exit_time,
    )
    entry_end_timestamp = build_timestamp(day, args.last_entry_time)
    exit_timestamp = build_timestamp(day, args.exit_time)
    active_trade: Optional[ActiveTrade] = None
    next_allowed_entry = close_boundaries[0]
    day_results: List[TradeResult] = []
    saw_valid_sma = False
    saw_equal_signal = False
    last_entry_failure = ""

    for boundary_timestamp in close_boundaries:
        if active_trade is not None and boundary_timestamp > active_trade.entry_timestamp:
            exit_candle_timestamp = signal_timestamp_for_boundary(boundary_timestamp)
            exit_candle_row = spot_data.rows_by_timestamp[exit_candle_timestamp]
            stop_hit = (
                exit_candle_row.low_value <= active_trade.stop_sma
                if active_trade.direction == "LONG"
                else exit_candle_row.high_value >= active_trade.stop_sma
            )
            if stop_hit:
                result = make_traded_result(
                    active_trade=active_trade,
                    exit_candle_timestamp=exit_candle_timestamp,
                    exit_timestamp=boundary_timestamp,
                    exit_price=active_trade.stop_sma,
                    exit_reason="stop_loss_ma_touch",
                    exit_sma=active_trade.stop_sma,
                    rupees_per_point=args.rupees_per_point,
                )
                day_results.append(result)
                logger.info(
                    "TRADED date=%s direction=%s entry=%s exit=%s reason=%s points=%s",
                    day,
                    active_trade.direction,
                    active_trade.entry_timestamp,
                    boundary_timestamp,
                    result.exit_reason,
                    result.points_pnl,
                )
                active_trade = None
                next_allowed_entry = shift_timestamp(boundary_timestamp, 15)
            else:
                updated_sma, _ = compute_spot_sma_including_current(
                    spot_data,
                    exit_candle_timestamp,
                    args.ma_period,
                )
                if updated_sma is None:
                    result = make_skipped_trade(
                        entry_date=day,
                        skip_reason="insufficient_stop_sma",
                        remarks=f"{exit_candle_timestamp} does not have enough history to update stop SMA",
                    )
                    day_results.append(result)
                    active_trade = None
                    break
                active_trade.stop_sma = updated_sma

                if boundary_timestamp == exit_timestamp:
                    result = make_traded_result(
                        active_trade=active_trade,
                        exit_candle_timestamp=exit_candle_timestamp,
                        exit_timestamp=boundary_timestamp,
                        exit_price=exit_candle_row.close_value,
                        exit_reason="day_close",
                        exit_sma=updated_sma,
                        rupees_per_point=args.rupees_per_point,
                    )
                    day_results.append(result)
                    logger.info(
                        "TRADED date=%s direction=%s entry=%s exit=%s reason=%s points=%s",
                        day,
                        active_trade.direction,
                        active_trade.entry_timestamp,
                        boundary_timestamp,
                        result.exit_reason,
                        result.points_pnl,
                    )
                    active_trade = None

        if (
            active_trade is None
            and boundary_timestamp <= entry_end_timestamp
            and boundary_timestamp >= next_allowed_entry
        ):
            candidate_trade, skip_reason, remarks = evaluate_entry(
                spot_data,
                day,
                boundary_timestamp,
                args.ma_period,
            )
            if candidate_trade is None:
                last_entry_failure = skip_reason or last_entry_failure
                if skip_reason == "equal_close_and_sma":
                    saw_equal_signal = True
                continue

            saw_valid_sma = True
            active_trade = candidate_trade

    if day_results:
        return day_results

    if not saw_valid_sma and last_entry_failure == "insufficient_spot_history":
        return [
            make_skipped_trade(
                entry_date=day,
                skip_reason="insufficient_spot_history",
                remarks=f"No entry signal had {args.ma_period} completed SMA bars between {args.entry_start_time} and {args.last_entry_time}.",
            )
        ]

    if saw_equal_signal:
        return [
            make_skipped_trade(
                entry_date=day,
                skip_reason="equal_close_and_sma",
                remarks="All valid entry signals were equal to the SMA.",
            )
        ]

    return [
        make_skipped_trade(
            entry_date=day,
            skip_reason="no_entry_signal",
            remarks="No completed trade was produced for this date.",
        )
    ]


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
    results: List[TradeResult] = []

    try:
        for day in candidate_days:
            day_results = run_day(spot_data, day, args, logger)
            results.extend(day_results)
            if all(result.status == "SKIPPED" for result in day_results):
                logger.info("SKIPPED date=%s reason=%s", day, day_results[0].skip_reason)
    except Exception:
        logger.exception("ERROR unexpected failure while running the backtest")
        raise

    traded_count = sum(1 for result in results if result.status == "TRADED")
    skipped_count = sum(1 for result in results if result.status == "SKIPPED")
    logger.info("COMPLETED traded=%s skipped_rows=%s total_rows=%s", traded_count, skipped_count, len(results))
    return results


def write_trades_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "skip_reason",
        "signal_timestamp",
        "entry_timestamp",
        "signal_close",
        "direction",
        "entry_price_points",
        "entry_sma_25",
        "exit_candle_timestamp",
        "exit_timestamp",
        "exit_price_points",
        "exit_reason",
        "exit_sma_25",
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


def summarize_trade_results(results: List[TradeResult], rupees_per_point: float) -> Dict[str, object]:
    traded_results = [result for result in results if result.status == "TRADED"]
    skipped_results = [result for result in results if result.status == "SKIPPED"]
    points_values = [float(result.points_pnl) for result in traded_results]
    total_points = sum(points_values)
    max_consecutive_wins, max_consecutive_losses = compute_max_consecutive_streaks(points_values)
    max_drawdown_points = compute_max_drawdown(points_values)

    return {
        "traded_results": traded_results,
        "skipped_results": skipped_results,
        "trades": len(traded_results),
        "skipped_rows": len(skipped_results),
        "long_trades": sum(1 for result in traded_results if result.direction == "LONG"),
        "short_trades": sum(1 for result in traded_results if result.direction == "SHORT"),
        "stop_exits": sum(1 for result in traded_results if result.exit_reason == "stop_loss_ma_touch"),
        "day_close_exits": sum(1 for result in traded_results if result.exit_reason == "day_close"),
        "winning_trades": sum(1 for value in points_values if value > 0),
        "losing_trades": sum(1 for value in points_values if value < 0),
        "break_even_trades": sum(1 for value in points_values if value == 0),
        "total_points": total_points,
        "total_rupees": total_points * rupees_per_point,
        "average_points": total_points / len(traded_results) if traded_results else 0.0,
        "max_profit": max(traded_results, key=lambda result: float(result.points_pnl), default=None),
        "max_loss": min(traded_results, key=lambda result: float(result.points_pnl), default=None),
        "max_consecutive_wins": max_consecutive_wins,
        "max_consecutive_losses": max_consecutive_losses,
        "max_drawdown_points": max_drawdown_points,
        "max_drawdown_rupees": max_drawdown_points * rupees_per_point,
    }


def make_day_result(day: str, results: List[TradeResult], rupees_per_point: float) -> DayResult:
    metrics = summarize_trade_results(results, rupees_per_point)
    max_profit: Optional[TradeResult] = metrics["max_profit"]  # type: ignore[assignment]
    max_loss: Optional[TradeResult] = metrics["max_loss"]  # type: ignore[assignment]
    skipped_results: List[TradeResult] = metrics["skipped_results"]  # type: ignore[assignment]
    status = "TRADED" if metrics["trades"] else "SKIPPED"
    skip_reasons = sorted({result.skip_reason for result in skipped_results if result.skip_reason})
    remarks = "; ".join(result.remarks for result in skipped_results if result.remarks)

    return DayResult(
        entry_date=day,
        status=status,
        skip_reason=";".join(skip_reasons),
        trades=str(metrics["trades"]),
        skipped_rows=str(metrics["skipped_rows"]),
        long_trades=str(metrics["long_trades"]),
        short_trades=str(metrics["short_trades"]),
        stop_exits=str(metrics["stop_exits"]),
        day_close_exits=str(metrics["day_close_exits"]),
        winning_trades=str(metrics["winning_trades"]),
        losing_trades=str(metrics["losing_trades"]),
        break_even_trades=str(metrics["break_even_trades"]),
        total_points=format_number(metrics["total_points"]),
        total_rupees=format_number(metrics["total_rupees"]),
        average_points=format_number(metrics["average_points"]),
        max_profit_points=max_profit.points_pnl if max_profit else "",
        max_loss_points=max_loss.points_pnl if max_loss else "",
        max_consecutive_wins=str(metrics["max_consecutive_wins"]),
        max_consecutive_losses=str(metrics["max_consecutive_losses"]),
        max_drawdown_points=format_number(metrics["max_drawdown_points"]),
        max_drawdown_rupees=format_number(metrics["max_drawdown_rupees"]),
        remarks=remarks,
    )


def build_daywise_results(trade_results: List[TradeResult], rupees_per_point: float) -> List[DayResult]:
    grouped_results: Dict[str, List[TradeResult]] = {}
    for result in trade_results:
        grouped_results.setdefault(result.entry_date, []).append(result)

    return [
        make_day_result(day, grouped_results[day], rupees_per_point)
        for day in sorted(grouped_results)
    ]


def write_daywise_csv(results: List[DayResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "skip_reason",
        "trades",
        "skipped_rows",
        "long_trades",
        "short_trades",
        "stop_exits",
        "day_close_exits",
        "winning_trades",
        "losing_trades",
        "break_even_trades",
        "total_points",
        "total_rupees",
        "average_points",
        "max_profit_points",
        "max_loss_points",
        "max_consecutive_wins",
        "max_consecutive_losses",
        "max_drawdown_points",
        "max_drawdown_rupees",
        "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)


def aggregate_day_results(period: str, results: List[DayResult], rupees_per_point: float) -> AggregateResult:
    traded_days = [result for result in results if int(result.trades) > 0]
    skipped_days = [result for result in results if int(result.trades) == 0]
    point_values = [float(result.total_points) for result in traded_days]
    total_points = sum(point_values)
    total_rupees = total_points * rupees_per_point
    max_profit = max(traded_days, key=lambda result: float(result.total_points), default=None)
    max_loss = min(traded_days, key=lambda result: float(result.total_points), default=None)
    max_consecutive_wins, max_consecutive_losses = compute_max_consecutive_streaks(point_values)
    max_drawdown_points = compute_max_drawdown(point_values)

    return AggregateResult(
        period=period,
        days=str(len(results)),
        skipped_days=str(len(skipped_days)),
        trades=str(sum(int(result.trades) for result in results)),
        skipped_rows=str(sum(int(result.skipped_rows) for result in results)),
        long_trades=str(sum(int(result.long_trades) for result in results)),
        short_trades=str(sum(int(result.short_trades) for result in results)),
        stop_exits=str(sum(int(result.stop_exits) for result in results)),
        day_close_exits=str(sum(int(result.day_close_exits) for result in results)),
        winning_days=str(sum(1 for value in point_values if value > 0)),
        losing_days=str(sum(1 for value in point_values if value < 0)),
        break_even_days=str(sum(1 for value in point_values if value == 0)),
        total_points=format_number(total_points),
        total_rupees=format_number(total_rupees),
        average_points=format_number(total_points / len(traded_days) if traded_days else 0.0),
        max_profit_date=max_profit.entry_date if max_profit else "",
        max_profit_points=max_profit.total_points if max_profit else "",
        max_profit_rupees=format_number(float(max_profit.total_points) * rupees_per_point) if max_profit else "",
        max_loss_date=max_loss.entry_date if max_loss else "",
        max_loss_points=max_loss.total_points if max_loss else "",
        max_loss_rupees=format_number(float(max_loss.total_points) * rupees_per_point) if max_loss else "",
        max_consecutive_wins=str(max_consecutive_wins),
        max_consecutive_losses=str(max_consecutive_losses),
        max_drawdown_points=format_number(max_drawdown_points),
        max_drawdown_rupees=format_number(max_drawdown_points * rupees_per_point),
    )


def aggregate_by_period(results: List[DayResult], period_length: int, rupees_per_point: float) -> List[AggregateResult]:
    grouped_results: Dict[str, List[DayResult]] = {}
    for result in results:
        period = result.entry_date[:period_length]
        grouped_results.setdefault(period, []).append(result)

    return [
        aggregate_day_results(period, grouped_results[period], rupees_per_point)
        for period in sorted(grouped_results)
    ]


def write_aggregate_csv(results: List[AggregateResult], output_path: Path) -> None:
    fieldnames = [
        "period",
        "days",
        "skipped_days",
        "trades",
        "skipped_rows",
        "long_trades",
        "short_trades",
        "stop_exits",
        "day_close_exits",
        "winning_days",
        "losing_days",
        "break_even_days",
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
        "| Period | Days | Skipped Days | Trades | Long | Short | Stops | Day Close | Win Days | Loss Days | Points | Rupees | Avg Points | Max Profit | Max Loss | Max DD Points | Max DD Rupees |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.period} | "
            f"{row.days} | "
            f"{row.skipped_days} | "
            f"{row.trades} | "
            f"{row.long_trades} | "
            f"{row.short_trades} | "
            f"{row.stop_exits} | "
            f"{row.day_close_exits} | "
            f"{row.winning_days} | "
            f"{row.losing_days} | "
            f"{row.total_points} | "
            f"{row.total_rupees} | "
            f"{row.average_points} | "
            f"{row.max_profit_points} | "
            f"{row.max_loss_points} | "
            f"{row.max_drawdown_points} | "
            f"{row.max_drawdown_rupees} |"
        )
    return lines


def write_summary(
    trade_results: List[TradeResult],
    daywise_results: List[DayResult],
    monthly_results: List[AggregateResult],
    yearly_results: List[AggregateResult],
    output_path: Path,
    args: argparse.Namespace,
) -> None:
    overall = aggregate_day_results("Overall", daywise_results, args.rupees_per_point)
    skipped_trade_results = [result for result in trade_results if result.status == "SKIPPED"]
    first_date = daywise_results[0].entry_date if daywise_results else "N/A"
    last_date = daywise_results[-1].entry_date if daywise_results else "N/A"

    lines: List[str] = [
        "# NIFTY 25-SMA Intraday Trailing Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Dataset: `{args.spot_file}`",
        f"- Tested date range: `{first_date}` through `{last_date}`",
        "- Signal source: NIFTY 15-minute close",
        f"- Entry window: `{args.entry_start_time}` through `{args.last_entry_time}`",
        f"- Scheduled exit: `{args.exit_time}`",
        f"- MA rule: {args.ma_period}-SMA of 15-minute closes including the completed signal candle",
        "- Timing rule: rows are candle starts; entry/exit timestamps are candle-close boundaries.",
        "- Direction rule: above SMA -> long NIFTY; below SMA -> short NIFTY; equal -> no entry",
        "- Stop rule: long exits when candle low touches MA; short exits when candle high touches MA",
        "- Stop execution: current trailing MA level",
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

    if skipped_trade_results:
        for result in skipped_trade_results:
            lines.append(f"- `{result.entry_date}`: `{result.skip_reason}`. {result.remarks}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Remarks",
            "",
            "- Exact timestamp matching is required; no nearest-candle fallback is allowed.",
            f"- The `{args.entry_start_time}` entry uses the prior 15-minute row close.",
            f"- The `{args.exit_time}` scheduled exit uses the prior 15-minute row close.",
            "- After a stop, the next possible entry is from the next completed candle after the stop candle.",
            "- Yearly and monthly results are grouped by entry date.",
            "- Period max drawdown is calculated from cumulative daywise point P/L.",
            "- Partial years are included when present in the source data.",
        ]
    )

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    trade_results = run_backtest(args)
    daywise_results = build_daywise_results(trade_results, args.rupees_per_point)
    monthly_results = aggregate_by_period(daywise_results, 7, args.rupees_per_point)
    yearly_results = aggregate_by_period(daywise_results, 4, args.rupees_per_point)

    write_trades_csv(trade_results, args.results_dir / TRADES_FILENAME)
    write_daywise_csv(daywise_results, args.results_dir / DAYWISE_FILENAME)
    write_aggregate_csv(monthly_results, args.results_dir / MONTHLY_FILENAME)
    write_aggregate_csv(yearly_results, args.results_dir / YEARLY_FILENAME)
    write_summary(
        trade_results,
        daywise_results,
        monthly_results,
        yearly_results,
        args.results_dir / SUMMARY_FILENAME,
        args,
    )


if __name__ == "__main__":
    main()
