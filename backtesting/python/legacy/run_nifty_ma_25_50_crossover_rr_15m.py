#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


IST_SUFFIX = "+05:30"
BASE_FILENAME = "nifty_ma_25_50_crossover_rr_15m"
LOG_FILENAME = f"{BASE_FILENAME}.log"
SUMMARY_FILENAME = f"{BASE_FILENAME}_summary.md"


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
class IndicatorSeries:
    fast_period: int
    slow_period: int
    fast_values: List[Optional[float]]
    slow_values: List[Optional[float]]


@dataclass
class ScheduledEntry:
    reward_multiple: float
    setup_type: str
    direction: str
    signal_index: int
    entry_index: int
    signal_timestamp: str
    stop_price: float
    fast_sma: float
    slow_sma: float


@dataclass
class ActiveTrade:
    reward_multiple: float
    setup_type: str
    direction: str
    entry_date: str
    signal_timestamp: str
    entry_timestamp: str
    entry_price: float
    entry_price_text: str
    stop_price: float
    target_price: float
    fast_sma: float
    slow_sma: float


@dataclass
class ExitDecision:
    exit_price: float
    exit_price_text: str
    exit_timestamp: str
    exit_reason: str
    remarks: str = ""


@dataclass
class TradeResult:
    report_date: str
    entry_date: str
    exit_date: str
    status: str
    skip_reason: str
    reward_multiple: str
    setup_type: str
    direction: str
    signal_timestamp: str
    entry_timestamp: str
    entry_price_points: str
    stop_price_points: str
    target_price_points: str
    exit_timestamp: str
    exit_price_points: str
    exit_reason: str
    fast_sma_25: str
    slow_sma_50: str
    points_pnl: str
    rupees_pnl: str
    holding_days: str
    remarks: str


@dataclass
class DayResult:
    date: str
    status: str
    skip_reason: str
    trades: str
    skipped_rows: str
    crossover_entries: str
    pullback_reentries: str
    target_exits: str
    stop_exits: str
    gap_target_exits: str
    gap_stop_exits: str
    reversal_exits: str
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
    crossover_entries: str
    pullback_reentries: str
    target_exits: str
    stop_exits: str
    gap_target_exits: str
    gap_stop_exits: str
    reversal_exits: str
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


@dataclass
class BacktestRun:
    reward_multiple: float
    reward_suffix: str
    trade_results: List[TradeResult]
    candidate_days: List[str]
    held_days: set[str]


@dataclass
class VariantArtifacts:
    run: BacktestRun
    daywise_results: List[DayResult]
    monthly_results: List[AggregateResult]
    yearly_results: List[AggregateResult]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Backtest a carry-forward NIFTY spot strategy that trades 15-minute "
            "25/50 SMA crossovers with fixed R-multiple targets."
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
    parser.add_argument("--fast-ma-period", type=int, default=25)
    parser.add_argument("--slow-ma-period", type=int, default=50)
    parser.add_argument("--reward-multiples", default="1,2,3")
    parser.add_argument("--rupees-per-point", type=float, default=65.0)
    parser.add_argument("--start-date", default="")
    parser.add_argument("--end-date", default="")
    args = parser.parse_args()

    validate_optional_date(parser, args.start_date, "--start-date")
    validate_optional_date(parser, args.end_date, "--end-date")
    if args.start_date and args.end_date and args.start_date > args.end_date:
        parser.error("--start-date must be <= --end-date")
    if args.fast_ma_period <= 0:
        parser.error("--fast-ma-period must be positive")
    if args.slow_ma_period <= 0:
        parser.error("--slow-ma-period must be positive")
    if args.fast_ma_period >= args.slow_ma_period:
        parser.error("--fast-ma-period must be < --slow-ma-period")
    if args.rupees_per_point <= 0:
        parser.error("--rupees-per-point must be positive")

    args.reward_multiple_values = parse_reward_multiples(parser, args.reward_multiples)
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


def parse_reward_multiples(parser: argparse.ArgumentParser, value: str) -> List[float]:
    parsed: List[float] = []
    seen: set[str] = set()
    for part in value.split(","):
        trimmed = part.strip()
        if not trimmed:
            parser.error("--reward-multiples must be a comma-separated list of positive numbers")
        try:
            reward_multiple = float(trimmed)
        except ValueError as exc:
            parser.error(f"Invalid reward multiple {trimmed!r}: {exc}")
        if reward_multiple <= 0:
            parser.error("--reward-multiples values must be positive")
        normalized = format_reward_multiple(reward_multiple)
        if normalized in seen:
            continue
        seen.add(normalized)
        parsed.append(reward_multiple)
    if not parsed:
        parser.error("--reward-multiples must include at least one value")
    return parsed


def format_number(value: float) -> str:
    return f"{value:.2f}"


def format_reward_multiple(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def sanitize_reward_multiple_suffix(value: float) -> str:
    label = format_reward_multiple(value)
    return f"r{label.replace('.', '_')}"


def holding_days(entry_date: str, exit_date: str) -> str:
    start_date = datetime.date.fromisoformat(entry_date)
    end_date = datetime.date.fromisoformat(exit_date)
    return str((end_date - start_date).days)


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger(BASE_FILENAME)
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


def compute_sma_series(rows: Sequence[PriceRow], period: int) -> List[Optional[float]]:
    values: List[Optional[float]] = [None] * len(rows)
    rolling_sum = 0.0
    for index, row in enumerate(rows):
        rolling_sum += row.close_value
        if index >= period:
            rolling_sum -= rows[index - period].close_value
        if index + 1 >= period:
            values[index] = rolling_sum / period
    return values


def build_indicator_series(spot_data: SpotData, fast_period: int, slow_period: int) -> IndicatorSeries:
    return IndicatorSeries(
        fast_period=fast_period,
        slow_period=slow_period,
        fast_values=compute_sma_series(spot_data.ordered_rows, fast_period),
        slow_values=compute_sma_series(spot_data.ordered_rows, slow_period),
    )


def filtered_trading_days(trading_days: List[str], start_date: str, end_date: str) -> List[str]:
    days = trading_days
    if start_date:
        days = [day for day in days if day >= start_date]
    if end_date:
        days = [day for day in days if day <= end_date]
    return days


def index_bounds(spot_data: SpotData, start_date: str, end_date: str) -> Tuple[Optional[int], Optional[int]]:
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    for index, row in enumerate(spot_data.ordered_rows):
        day = row.timestamp[:10]
        if start_index is None and (not start_date or day >= start_date):
            start_index = index
        if not end_date or day <= end_date:
            end_index = index
    return start_index, end_index


def detect_crossover(indicators: IndicatorSeries, index: int) -> Optional[str]:
    if index <= 0:
        return None
    previous_fast = indicators.fast_values[index - 1]
    previous_slow = indicators.slow_values[index - 1]
    current_fast = indicators.fast_values[index]
    current_slow = indicators.slow_values[index]
    if None in (previous_fast, previous_slow, current_fast, current_slow):
        return None
    if previous_fast <= previous_slow and current_fast > current_slow:
        return "LONG"
    if previous_fast >= previous_slow and current_fast < current_slow:
        return "SHORT"
    return None


def pullback_reentry_signal(
    row: PriceRow,
    fast_sma: Optional[float],
    slow_sma: Optional[float],
    direction: str,
) -> bool:
    if fast_sma is None or slow_sma is None:
        return False
    if direction == "LONG":
        return (
            fast_sma > slow_sma
            and row.low_value <= fast_sma <= row.high_value
            and row.close_value > row.open_value
        )
    return (
        fast_sma < slow_sma
        and row.low_value <= fast_sma <= row.high_value
        and row.close_value < row.open_value
    )


def build_scheduled_entry(
    reward_multiple: float,
    setup_type: str,
    direction: str,
    signal_index: int,
    entry_index: int,
    signal_row: PriceRow,
    fast_sma: float,
    slow_sma: float,
) -> ScheduledEntry:
    stop_price = signal_row.low_value if direction == "LONG" else signal_row.high_value
    return ScheduledEntry(
        reward_multiple=reward_multiple,
        setup_type=setup_type,
        direction=direction,
        signal_index=signal_index,
        entry_index=entry_index,
        signal_timestamp=signal_row.timestamp,
        stop_price=stop_price,
        fast_sma=fast_sma,
        slow_sma=slow_sma,
    )


def resolve_gap_exit(active_trade: ActiveTrade, row: PriceRow) -> Optional[ExitDecision]:
    if active_trade.direction == "LONG":
        if row.open_value <= active_trade.stop_price:
            return ExitDecision(
                exit_price=row.open_value,
                exit_price_text=row.open_text,
                exit_timestamp=row.timestamp,
                exit_reason="gap_stop",
            )
        if row.open_value >= active_trade.target_price:
            return ExitDecision(
                exit_price=row.open_value,
                exit_price_text=row.open_text,
                exit_timestamp=row.timestamp,
                exit_reason="gap_target",
            )
        return None

    if row.open_value >= active_trade.stop_price:
        return ExitDecision(
            exit_price=row.open_value,
            exit_price_text=row.open_text,
            exit_timestamp=row.timestamp,
            exit_reason="gap_stop",
        )
    if row.open_value <= active_trade.target_price:
        return ExitDecision(
            exit_price=row.open_value,
            exit_price_text=row.open_text,
            exit_timestamp=row.timestamp,
            exit_reason="gap_target",
        )
    return None


def resolve_intrabar_exit(active_trade: ActiveTrade, row: PriceRow) -> Optional[ExitDecision]:
    if active_trade.direction == "LONG":
        stop_hit = row.low_value <= active_trade.stop_price
        target_hit = row.high_value >= active_trade.target_price
    else:
        stop_hit = row.high_value >= active_trade.stop_price
        target_hit = row.low_value <= active_trade.target_price

    if stop_hit and target_hit:
        return ExitDecision(
            exit_price=active_trade.stop_price,
            exit_price_text=format_number(active_trade.stop_price),
            exit_timestamp=row.timestamp,
            exit_reason="stop_loss",
            remarks="Stop and target both hit inside one candle; conservative stop-first fill applied.",
        )
    if stop_hit:
        return ExitDecision(
            exit_price=active_trade.stop_price,
            exit_price_text=format_number(active_trade.stop_price),
            exit_timestamp=row.timestamp,
            exit_reason="stop_loss",
        )
    if target_hit:
        return ExitDecision(
            exit_price=active_trade.target_price,
            exit_price_text=format_number(active_trade.target_price),
            exit_timestamp=row.timestamp,
            exit_reason="target",
        )
    return None


def make_traded_result(
    active_trade: ActiveTrade,
    exit_decision: ExitDecision,
    rupees_per_point: float,
) -> TradeResult:
    if active_trade.direction == "LONG":
        points_pnl = exit_decision.exit_price - active_trade.entry_price
    else:
        points_pnl = active_trade.entry_price - exit_decision.exit_price
    points_pnl_text = format_number(points_pnl)
    rupees_pnl = float(points_pnl_text) * rupees_per_point
    exit_date = exit_decision.exit_timestamp[:10]

    return TradeResult(
        report_date=exit_date,
        entry_date=active_trade.entry_date,
        exit_date=exit_date,
        status="TRADED",
        skip_reason="",
        reward_multiple=format_reward_multiple(active_trade.reward_multiple),
        setup_type=active_trade.setup_type,
        direction=active_trade.direction,
        signal_timestamp=active_trade.signal_timestamp,
        entry_timestamp=active_trade.entry_timestamp,
        entry_price_points=active_trade.entry_price_text,
        stop_price_points=format_number(active_trade.stop_price),
        target_price_points=format_number(active_trade.target_price),
        exit_timestamp=exit_decision.exit_timestamp,
        exit_price_points=exit_decision.exit_price_text,
        exit_reason=exit_decision.exit_reason,
        fast_sma_25=format_number(active_trade.fast_sma),
        slow_sma_50=format_number(active_trade.slow_sma),
        points_pnl=points_pnl_text,
        rupees_pnl=format_number(rupees_pnl),
        holding_days=holding_days(active_trade.entry_date, exit_date),
        remarks=exit_decision.remarks,
    )


def make_skipped_result(
    reward_multiple: float,
    setup_type: str,
    direction: str,
    signal_timestamp: str,
    report_date: str,
    skip_reason: str,
    remarks: str,
    fast_sma: Optional[float],
    slow_sma: Optional[float],
) -> TradeResult:
    return TradeResult(
        report_date=report_date,
        entry_date=report_date,
        exit_date=report_date,
        status="SKIPPED",
        skip_reason=skip_reason,
        reward_multiple=format_reward_multiple(reward_multiple),
        setup_type=setup_type,
        direction=direction,
        signal_timestamp=signal_timestamp,
        entry_timestamp="",
        entry_price_points="",
        stop_price_points="",
        target_price_points="",
        exit_timestamp="",
        exit_price_points="",
        exit_reason="",
        fast_sma_25="" if fast_sma is None else format_number(fast_sma),
        slow_sma_50="" if slow_sma is None else format_number(slow_sma),
        points_pnl="0.00",
        rupees_pnl="0.00",
        holding_days="0",
        remarks=remarks,
    )


def materialize_entry(
    scheduled_entry: ScheduledEntry,
    row: PriceRow,
) -> Tuple[Optional[ActiveTrade], Optional[TradeResult]]:
    if scheduled_entry.direction == "LONG":
        risk_distance = row.open_value - scheduled_entry.stop_price
        target_price = row.open_value + (scheduled_entry.reward_multiple * risk_distance)
    else:
        risk_distance = scheduled_entry.stop_price - row.open_value
        target_price = row.open_value - (scheduled_entry.reward_multiple * risk_distance)

    if risk_distance <= 0:
        skipped_result = make_skipped_result(
            reward_multiple=scheduled_entry.reward_multiple,
            setup_type=scheduled_entry.setup_type,
            direction=scheduled_entry.direction,
            signal_timestamp=scheduled_entry.signal_timestamp,
            report_date=row.timestamp[:10],
            skip_reason="entry_open_beyond_stop",
            remarks=(
                f"Entry open {row.open_text} invalidated the {scheduled_entry.direction} setup stop "
                f"{format_number(scheduled_entry.stop_price)}."
            ),
            fast_sma=scheduled_entry.fast_sma,
            slow_sma=scheduled_entry.slow_sma,
        )
        return None, skipped_result

    return (
        ActiveTrade(
            reward_multiple=scheduled_entry.reward_multiple,
            setup_type=scheduled_entry.setup_type,
            direction=scheduled_entry.direction,
            entry_date=row.timestamp[:10],
            signal_timestamp=scheduled_entry.signal_timestamp,
            entry_timestamp=row.timestamp,
            entry_price=row.open_value,
            entry_price_text=row.open_text,
            stop_price=scheduled_entry.stop_price,
            target_price=target_price,
            fast_sma=scheduled_entry.fast_sma,
            slow_sma=scheduled_entry.slow_sma,
        ),
        None,
    )


def next_entry_allowed(
    rows: Sequence[PriceRow],
    entry_index: int,
    end_date: str,
) -> bool:
    if entry_index >= len(rows):
        return False
    if end_date and rows[entry_index].timestamp[:10] > end_date:
        return False
    return True


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
        "crossover_entries": sum(1 for result in traded_results if result.setup_type == "CROSSOVER"),
        "pullback_reentries": sum(1 for result in traded_results if result.setup_type == "PULLBACK_REENTRY"),
        "target_exits": sum(1 for result in traded_results if result.exit_reason == "target"),
        "stop_exits": sum(1 for result in traded_results if result.exit_reason == "stop_loss"),
        "gap_target_exits": sum(1 for result in traded_results if result.exit_reason == "gap_target"),
        "gap_stop_exits": sum(1 for result in traded_results if result.exit_reason == "gap_stop"),
        "reversal_exits": sum(1 for result in traded_results if result.exit_reason == "reversal_exit"),
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


def make_day_result(
    day: str,
    results: List[TradeResult],
    rupees_per_point: float,
    default_status: str,
    default_remarks: str,
) -> DayResult:
    metrics = summarize_trade_results(results, rupees_per_point)
    max_profit: Optional[TradeResult] = metrics["max_profit"]  # type: ignore[assignment]
    max_loss: Optional[TradeResult] = metrics["max_loss"]  # type: ignore[assignment]
    skipped_results: List[TradeResult] = metrics["skipped_results"]  # type: ignore[assignment]

    if metrics["trades"] and metrics["skipped_rows"]:
        status = "MIXED"
    elif metrics["trades"]:
        status = "TRADED"
    elif metrics["skipped_rows"]:
        status = "SKIPPED"
    else:
        status = default_status

    skip_reasons = sorted({result.skip_reason for result in skipped_results if result.skip_reason})
    remarks = "; ".join(result.remarks for result in skipped_results if result.remarks)
    if not remarks:
        remarks = default_remarks

    return DayResult(
        date=day,
        status=status,
        skip_reason=";".join(skip_reasons),
        trades=str(metrics["trades"]),
        skipped_rows=str(metrics["skipped_rows"]),
        crossover_entries=str(metrics["crossover_entries"]),
        pullback_reentries=str(metrics["pullback_reentries"]),
        target_exits=str(metrics["target_exits"]),
        stop_exits=str(metrics["stop_exits"]),
        gap_target_exits=str(metrics["gap_target_exits"]),
        gap_stop_exits=str(metrics["gap_stop_exits"]),
        reversal_exits=str(metrics["reversal_exits"]),
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


def build_daywise_results(
    trade_results: List[TradeResult],
    candidate_days: List[str],
    held_days: set[str],
    rupees_per_point: float,
) -> List[DayResult]:
    grouped_results: Dict[str, List[TradeResult]] = {}
    for result in trade_results:
        grouped_results.setdefault(result.report_date, []).append(result)

    report_days = sorted(set(candidate_days) | set(grouped_results))
    return [
        make_day_result(
            day,
            grouped_results.get(day, []),
            rupees_per_point,
            "HELD" if day in held_days else "FLAT",
            "Open position carried through this date with no realized exit." if day in held_days else "",
        )
        for day in report_days
    ]


def aggregate_day_results(period: str, results: List[DayResult], rupees_per_point: float) -> AggregateResult:
    traded_days = [result for result in results if int(result.trades) > 0]
    skipped_days = [result for result in results if int(result.skipped_rows) > 0]
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
        crossover_entries=str(sum(int(result.crossover_entries) for result in results)),
        pullback_reentries=str(sum(int(result.pullback_reentries) for result in results)),
        target_exits=str(sum(int(result.target_exits) for result in results)),
        stop_exits=str(sum(int(result.stop_exits) for result in results)),
        gap_target_exits=str(sum(int(result.gap_target_exits) for result in results)),
        gap_stop_exits=str(sum(int(result.gap_stop_exits) for result in results)),
        reversal_exits=str(sum(int(result.reversal_exits) for result in results)),
        winning_days=str(sum(1 for value in point_values if value > 0)),
        losing_days=str(sum(1 for value in point_values if value < 0)),
        break_even_days=str(sum(1 for value in point_values if value == 0)),
        total_points=format_number(total_points),
        total_rupees=format_number(total_rupees),
        average_points=format_number(total_points / len(traded_days) if traded_days else 0.0),
        max_profit_date=max_profit.date if max_profit else "",
        max_profit_points=max_profit.total_points if max_profit else "",
        max_profit_rupees=format_number(float(max_profit.total_points) * rupees_per_point) if max_profit else "",
        max_loss_date=max_loss.date if max_loss else "",
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
        grouped_results.setdefault(result.date[:period_length], []).append(result)

    return [
        aggregate_day_results(period, grouped_results[period], rupees_per_point)
        for period in sorted(grouped_results)
    ]


def aggregate_table_lines(rows: List[AggregateResult]) -> List[str]:
    lines = [
        "| Period | Days | Trades | Crossovers | Pullbacks | Targets | Stops | Gap Targets | Gap Stops | Reversals | Points | Rupees | Avg Points | Max DD Points | Max DD Rupees |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.period} | "
            f"{row.days} | "
            f"{row.trades} | "
            f"{row.crossover_entries} | "
            f"{row.pullback_reentries} | "
            f"{row.target_exits} | "
            f"{row.stop_exits} | "
            f"{row.gap_target_exits} | "
            f"{row.gap_stop_exits} | "
            f"{row.reversal_exits} | "
            f"{row.total_points} | "
            f"{row.total_rupees} | "
            f"{row.average_points} | "
            f"{row.max_drawdown_points} | "
            f"{row.max_drawdown_rupees} |"
        )
    return lines


def comparison_table_lines(
    overall_rows: List[Tuple[str, AggregateResult]],
) -> List[str]:
    lines = [
        "| Reward | Days | Trades | Crossovers | Pullbacks | Targets | Stops | Gap Targets | Gap Stops | Reversals | Points | Rupees | Avg Points | Max DD Points |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for reward_label, row in overall_rows:
        lines.append(
            "| "
            f"{reward_label} | "
            f"{row.days} | "
            f"{row.trades} | "
            f"{row.crossover_entries} | "
            f"{row.pullback_reentries} | "
            f"{row.target_exits} | "
            f"{row.stop_exits} | "
            f"{row.gap_target_exits} | "
            f"{row.gap_stop_exits} | "
            f"{row.reversal_exits} | "
            f"{row.total_points} | "
            f"{row.total_rupees} | "
            f"{row.average_points} | "
            f"{row.max_drawdown_points} |"
        )
    return lines


def write_trades_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "report_date",
        "entry_date",
        "exit_date",
        "status",
        "skip_reason",
        "reward_multiple",
        "setup_type",
        "direction",
        "signal_timestamp",
        "entry_timestamp",
        "entry_price_points",
        "stop_price_points",
        "target_price_points",
        "exit_timestamp",
        "exit_price_points",
        "exit_reason",
        "fast_sma_25",
        "slow_sma_50",
        "points_pnl",
        "rupees_pnl",
        "holding_days",
        "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)


def write_daywise_csv(results: List[DayResult], output_path: Path) -> None:
    fieldnames = [
        "date",
        "status",
        "skip_reason",
        "trades",
        "skipped_rows",
        "crossover_entries",
        "pullback_reentries",
        "target_exits",
        "stop_exits",
        "gap_target_exits",
        "gap_stop_exits",
        "reversal_exits",
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


def write_aggregate_csv(results: List[AggregateResult], output_path: Path) -> None:
    fieldnames = [
        "period",
        "days",
        "skipped_days",
        "trades",
        "skipped_rows",
        "crossover_entries",
        "pullback_reentries",
        "target_exits",
        "stop_exits",
        "gap_target_exits",
        "gap_stop_exits",
        "reversal_exits",
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


def variant_filename(suffix: str, kind: str) -> str:
    return f"{BASE_FILENAME}_{suffix}_{kind}.csv"


def run_backtest_for_variant(
    spot_data: SpotData,
    indicators: IndicatorSeries,
    reward_multiple: float,
    start_date: str,
    end_date: str,
    rupees_per_point: float,
    logger: logging.Logger,
) -> BacktestRun:
    candidate_days = filtered_trading_days(spot_data.trading_days, start_date, end_date)
    start_index, end_index = index_bounds(spot_data, start_date, end_date)
    reward_suffix = sanitize_reward_multiple_suffix(reward_multiple)

    if start_index is None or end_index is None or start_index > end_index:
        return BacktestRun(
            reward_multiple=reward_multiple,
            reward_suffix=reward_suffix,
            trade_results=[],
            candidate_days=[],
            held_days=set(),
        )

    results: List[TradeResult] = []
    active_trade: Optional[ActiveTrade] = None
    scheduled_entry: Optional[ScheduledEntry] = None
    held_days: set[str] = set()
    eligible_pullback_direction: Optional[str] = None
    eligible_pullback_start_index = -1

    rows = spot_data.ordered_rows

    for index in range(start_index, end_index + 1):
        row = rows[index]
        day = row.timestamp[:10]
        current_scheduled = scheduled_entry if scheduled_entry and scheduled_entry.entry_index == index else None
        if current_scheduled is not None:
            scheduled_entry = None

        if active_trade is not None:
            gap_exit = resolve_gap_exit(active_trade, row)
            if gap_exit is not None:
                results.append(make_traded_result(active_trade, gap_exit, rupees_per_point))
                logger.info(
                    "TRADED variant=%s direction=%s entry=%s exit=%s reason=%s",
                    reward_suffix,
                    active_trade.direction,
                    active_trade.entry_timestamp,
                    gap_exit.exit_timestamp,
                    gap_exit.exit_reason,
                )
                if gap_exit.exit_reason == "gap_target":
                    eligible_pullback_direction = active_trade.direction
                    eligible_pullback_start_index = index
                else:
                    eligible_pullback_direction = None
                    eligible_pullback_start_index = -1
                active_trade = None
            elif current_scheduled is not None and current_scheduled.setup_type == "CROSSOVER" and current_scheduled.direction != active_trade.direction:
                reversal_exit = ExitDecision(
                    exit_price=row.open_value,
                    exit_price_text=row.open_text,
                    exit_timestamp=row.timestamp,
                    exit_reason="reversal_exit",
                )
                results.append(make_traded_result(active_trade, reversal_exit, rupees_per_point))
                logger.info(
                    "TRADED variant=%s direction=%s entry=%s exit=%s reason=%s",
                    reward_suffix,
                    active_trade.direction,
                    active_trade.entry_timestamp,
                    reversal_exit.exit_timestamp,
                    reversal_exit.exit_reason,
                )
                active_trade = None
                eligible_pullback_direction = None
                eligible_pullback_start_index = -1

        if current_scheduled is not None and active_trade is None:
            active_trade, skipped_result = materialize_entry(current_scheduled, row)
            if skipped_result is not None:
                results.append(skipped_result)
                logger.info(
                    "SKIPPED variant=%s signal=%s direction=%s reason=%s",
                    reward_suffix,
                    skipped_result.signal_timestamp,
                    skipped_result.direction,
                    skipped_result.skip_reason,
                )
            elif active_trade is not None:
                logger.info(
                    "ENTERED variant=%s setup=%s direction=%s signal=%s entry=%s entry_price=%s stop=%s target=%s",
                    reward_suffix,
                    active_trade.setup_type,
                    active_trade.direction,
                    active_trade.signal_timestamp,
                    active_trade.entry_timestamp,
                    active_trade.entry_price_text,
                    format_number(active_trade.stop_price),
                    format_number(active_trade.target_price),
                )

        if active_trade is not None:
            intrabar_exit = resolve_intrabar_exit(active_trade, row)
            if intrabar_exit is not None:
                results.append(make_traded_result(active_trade, intrabar_exit, rupees_per_point))
                logger.info(
                    "TRADED variant=%s direction=%s entry=%s exit=%s reason=%s",
                    reward_suffix,
                    active_trade.direction,
                    active_trade.entry_timestamp,
                    intrabar_exit.exit_timestamp,
                    intrabar_exit.exit_reason,
                )
                if intrabar_exit.exit_reason == "target":
                    eligible_pullback_direction = active_trade.direction
                    eligible_pullback_start_index = index
                else:
                    eligible_pullback_direction = None
                    eligible_pullback_start_index = -1
                active_trade = None
            else:
                held_days.add(day)

        if index == end_index:
            continue

        fast_sma = indicators.fast_values[index]
        slow_sma = indicators.slow_values[index]
        crossover_direction = detect_crossover(indicators, index)

        if crossover_direction is not None and fast_sma is not None and slow_sma is not None:
            if next_entry_allowed(rows, index + 1, end_date):
                scheduled_entry = build_scheduled_entry(
                    reward_multiple=reward_multiple,
                    setup_type="CROSSOVER",
                    direction=crossover_direction,
                    signal_index=index,
                    entry_index=index + 1,
                    signal_row=row,
                    fast_sma=fast_sma,
                    slow_sma=slow_sma,
                )
                eligible_pullback_direction = None
                eligible_pullback_start_index = -1
            else:
                results.append(
                    make_skipped_result(
                        reward_multiple=reward_multiple,
                        setup_type="CROSSOVER",
                        direction=crossover_direction,
                        signal_timestamp=row.timestamp,
                        report_date=day,
                        skip_reason="no_next_bar_for_entry",
                        remarks=(
                            f"{crossover_direction} crossover at {row.timestamp} had no eligible next bar "
                            "inside the requested range."
                        ),
                        fast_sma=fast_sma,
                        slow_sma=slow_sma,
                    )
                )
            continue

        if (
            active_trade is None
            and eligible_pullback_direction is not None
            and index > eligible_pullback_start_index
            and pullback_reentry_signal(row, fast_sma, slow_sma, eligible_pullback_direction)
            and fast_sma is not None
            and slow_sma is not None
        ):
            if next_entry_allowed(rows, index + 1, end_date):
                scheduled_entry = build_scheduled_entry(
                    reward_multiple=reward_multiple,
                    setup_type="PULLBACK_REENTRY",
                    direction=eligible_pullback_direction,
                    signal_index=index,
                    entry_index=index + 1,
                    signal_row=row,
                    fast_sma=fast_sma,
                    slow_sma=slow_sma,
                )
            else:
                results.append(
                    make_skipped_result(
                        reward_multiple=reward_multiple,
                        setup_type="PULLBACK_REENTRY",
                        direction=eligible_pullback_direction,
                        signal_timestamp=row.timestamp,
                        report_date=day,
                        skip_reason="no_next_bar_for_entry",
                        remarks=(
                            f"Pullback re-entry at {row.timestamp} had no eligible next bar inside the "
                            "requested range."
                        ),
                        fast_sma=fast_sma,
                        slow_sma=slow_sma,
                    )
                )

    if active_trade is not None:
        final_row = rows[end_index]
        exit_reason = "end_of_range" if end_date else "end_of_data"
        end_exit = ExitDecision(
            exit_price=final_row.close_value,
            exit_price_text=final_row.close_text,
            exit_timestamp=final_row.timestamp,
            exit_reason=exit_reason,
        )
        results.append(make_traded_result(active_trade, end_exit, rupees_per_point))
        logger.info(
            "TRADED variant=%s direction=%s entry=%s exit=%s reason=%s",
            reward_suffix,
            active_trade.direction,
            active_trade.entry_timestamp,
            end_exit.exit_timestamp,
            end_exit.exit_reason,
        )

    traded_count = sum(1 for result in results if result.status == "TRADED")
    skipped_count = sum(1 for result in results if result.status == "SKIPPED")
    logger.info(
        "COMPLETED variant=%s traded=%s skipped=%s total_rows=%s",
        reward_suffix,
        traded_count,
        skipped_count,
        len(results),
    )
    return BacktestRun(
        reward_multiple=reward_multiple,
        reward_suffix=reward_suffix,
        trade_results=results,
        candidate_days=candidate_days,
        held_days=held_days,
    )


def variant_section_lines(
    artifacts: VariantArtifacts,
    args: argparse.Namespace,
) -> List[str]:
    overall = aggregate_day_results("Overall", artifacts.daywise_results, args.rupees_per_point)
    skipped_results = [result for result in artifacts.run.trade_results if result.status == "SKIPPED"]
    reward_label = format_reward_multiple(artifacts.run.reward_multiple)

    lines: List[str] = [
        f"## Reward Multiple {reward_label}R",
        "",
        *aggregate_table_lines([overall]),
        "",
        "### Yearly Results",
        "",
        *aggregate_table_lines(artifacts.yearly_results),
        "",
        "### Monthly Results",
        "",
        *aggregate_table_lines(artifacts.monthly_results),
        "",
        "### Exceptions",
        "",
    ]

    if skipped_results:
        for result in skipped_results:
            lines.append(
                f"- `{result.report_date}`: `{result.skip_reason}` on `{result.signal_timestamp}`. {result.remarks}"
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "### Remarks",
            "",
            "- Trades are evaluated on 15-minute OHLC candles only; exact intrabar order is unknown.",
            "- Same-candle stop/target conflicts are resolved as stop-first.",
            "- After a target exit, only later candles can trigger a pullback re-entry.",
            "- After any stop exit, pullback re-entry is disabled until the next opposite crossover.",
            "- Reversal entries use the next candle open after the opposite crossover signal.",
        ]
    )
    return lines


def write_summary(
    variant_artifacts: List[VariantArtifacts],
    output_path: Path,
    args: argparse.Namespace,
    spot_data: SpotData,
) -> None:
    overall_rows = [
        (
            f"{format_reward_multiple(artifacts.run.reward_multiple)}R",
            aggregate_day_results("Overall", artifacts.daywise_results, args.rupees_per_point),
        )
        for artifacts in variant_artifacts
    ]

    first_date = spot_data.trading_days[0] if spot_data.trading_days else "N/A"
    last_date = spot_data.trading_days[-1] if spot_data.trading_days else "N/A"

    lines: List[str] = [
        "# NIFTY 25/50 SMA Crossover R-Multiple Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Dataset: `{args.spot_file}`",
        f"- Dataset date span: `{first_date}` through `{last_date}`",
        f"- Tested date range: `{args.start_date or first_date}` through `{args.end_date or last_date}`",
        "- Signal source: NIFTY 15-minute OHLC candles",
        f"- Fast MA rule: `{args.fast_ma_period}`-SMA of 15-minute closes",
        f"- Slow MA rule: `{args.slow_ma_period}`-SMA of 15-minute closes",
        "- Bullish crossover: previous fast MA <= slow MA and current fast MA > slow MA",
        "- Bearish crossover: previous fast MA >= slow MA and current fast MA < slow MA",
        "- Entry timing: next available 15-minute candle open after the completed signal candle",
        "- Stop basis: setup candle low for longs, setup candle high for shorts",
        "- Target basis: fixed reward multiple of the initial 1R distance",
        "- Carry-forward rule: no routine day-end exit; positions are held until stop, target, reversal, range end, or end of data",
        "- Pullback rule: after target only, re-enter on a later 25-SMA touch with a directional candle while the regime remains intact",
        "- Gap handling: next candle open can exit at gap-stop or gap-target before other logic",
        f"- Reward multiples tested: `{', '.join(format_reward_multiple(value) for value in args.reward_multiple_values)}`",
        f"- Rupee conversion: 1 point = Rs {format_number(args.rupees_per_point)}",
        "- No brokerage, slippage, lots, or option data are used.",
        "",
        "## Overall Comparison",
        "",
        *comparison_table_lines(overall_rows),
        "",
    ]

    for artifacts in variant_artifacts:
        lines.extend(variant_section_lines(artifacts, args))
        lines.append("")

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    spot_data = load_spot_data(args.spot_file)
    indicators = build_indicator_series(spot_data, args.fast_ma_period, args.slow_ma_period)
    variant_artifacts: List[VariantArtifacts] = []

    for reward_multiple in args.reward_multiple_values:
        run = run_backtest_for_variant(
            spot_data=spot_data,
            indicators=indicators,
            reward_multiple=reward_multiple,
            start_date=args.start_date,
            end_date=args.end_date,
            rupees_per_point=args.rupees_per_point,
            logger=logger,
        )
        daywise_results = build_daywise_results(
            run.trade_results,
            run.candidate_days,
            run.held_days,
            args.rupees_per_point,
        )
        monthly_results = aggregate_by_period(daywise_results, 7, args.rupees_per_point)
        yearly_results = aggregate_by_period(daywise_results, 4, args.rupees_per_point)

        write_trades_csv(
            run.trade_results,
            args.results_dir / variant_filename(run.reward_suffix, "trades"),
        )
        write_daywise_csv(
            daywise_results,
            args.results_dir / variant_filename(run.reward_suffix, "daywise"),
        )
        write_aggregate_csv(
            monthly_results,
            args.results_dir / variant_filename(run.reward_suffix, "monthly"),
        )
        write_aggregate_csv(
            yearly_results,
            args.results_dir / variant_filename(run.reward_suffix, "yearly"),
        )

        variant_artifacts.append(
            VariantArtifacts(
                run=run,
                daywise_results=daywise_results,
                monthly_results=monthly_results,
                yearly_results=yearly_results,
            )
        )

    write_summary(
        variant_artifacts=variant_artifacts,
        output_path=args.results_dir / SUMMARY_FILENAME,
        args=args,
        spot_data=spot_data,
    )


if __name__ == "__main__":
    main()
