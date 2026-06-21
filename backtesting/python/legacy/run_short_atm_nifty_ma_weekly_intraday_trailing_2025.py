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
TRADEWISE_FILENAME = "short_atm_nifty_ma_weekly_intraday_trailing_2025_trades.csv"
DAYWISE_FILENAME = "short_atm_nifty_ma_weekly_intraday_trailing_2025_daywise.csv"
SUMMARY_FILENAME = "short_atm_nifty_ma_weekly_intraday_trailing_2025_summary.md"
LOG_FILENAME = "short_atm_nifty_ma_weekly_intraday_trailing_2025.log"


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
class Spot15Data:
    rows_by_timestamp: Dict[str, PriceRow]
    ordered_rows: List[PriceRow]
    index_by_timestamp: Dict[str, int]
    trading_days: List[str]


@dataclass
class Spot1mData:
    rows_by_day: Dict[str, Dict[str, PriceRow]]


@dataclass
class OptionRow:
    timestamp: str
    open_value: float
    open_text: str


@dataclass
class ContractData:
    path: Path
    rows_by_timestamp: Dict[str, OptionRow]


@dataclass
class TradeResult:
    entry_date: str
    status: str
    skip_reason: str
    expiry_date: str
    signal_timestamp: str
    signal_close: str
    spot_sma_25: str
    spot_signal_relation: str
    entry_timestamp: str
    atm_strike: str
    sold_side: str
    contract_name: str
    option_entry_open: str
    exit_timestamp: str
    option_exit_open: str
    exit_reason: str
    exit_spot_ma: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


@dataclass
class DayResult:
    entry_date: str
    status: str
    skip_reason: str
    expiry_date: str
    trades: str
    ce_trades: str
    pe_trades: str
    stopped_trades: str
    day_close_trades: str
    skipped_signals: str
    orders_executed: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


@dataclass
class ExitOutcome:
    status: str
    skip_reason: str
    exit_timestamp: str
    option_exit_open: str
    exit_reason: str
    exit_spot_ma: str
    gross_pnl: float
    brokerage: float
    net_pnl: float
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Backtest the 2025 intraday weekly directional ATM short option strategy "
            "using a NIFTY 25-SMA signal and 1-minute NIFTY trailing stop."
        ),
    )
    parser.add_argument(
        "--spot-15m-file",
        type=Path,
        default=repo_root / "nifty" / "NIFTY50_INDEX_15m_last_4y.csv",
    )
    parser.add_argument(
        "--spot-1m-file",
        type=Path,
        default=repo_root / "nifty" / "NIFTY50_INDEX_1m_2025.csv",
    )
    parser.add_argument(
        "--options-dir",
        type=Path,
        default=repo_root / "Options_2025",
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
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--lot-size", type=int, default=65)
    parser.add_argument("--lots", type=int, default=4)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
    args = parser.parse_args()

    if not (args.entry_start_time <= args.last_entry_time < args.exit_time):
        parser.error("--entry-start-time must be <= --last-entry-time and --last-entry-time must be < --exit-time")

    return args


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


def build_intraday_timestamps(day: str, start_time: str, end_time: str, step_minutes: int) -> List[str]:
    start_dt = datetime.datetime.strptime(f"{day} {start_time}", "%Y-%m-%d %H:%M")
    end_dt = datetime.datetime.strptime(f"{day} {end_time}", "%Y-%m-%d %H:%M")
    timestamps: List[str] = []
    current_dt = start_dt
    while current_dt <= end_dt:
        timestamps.append(datetime_to_timestamp(current_dt))
        current_dt += datetime.timedelta(minutes=step_minutes)
    return timestamps


def signal_timestamp_for_entry(entry_timestamp: str) -> str:
    entry_dt = timestamp_to_datetime(entry_timestamp)
    return datetime_to_timestamp(entry_dt - datetime.timedelta(minutes=15))


def latest_completed_signal_timestamp(minute_timestamp: str) -> str:
    minute_dt = timestamp_to_datetime(minute_timestamp)
    floored_minute = (minute_dt.minute // 15) * 15
    boundary_dt = minute_dt.replace(minute=floored_minute, second=0)
    return datetime_to_timestamp(boundary_dt - datetime.timedelta(minutes=15))


def next_15m_boundary_after(timestamp: str) -> datetime.datetime:
    current_dt = timestamp_to_datetime(timestamp)
    base_dt = current_dt.replace(second=0, microsecond=0)
    minutes_since_midnight = base_dt.hour * 60 + base_dt.minute
    next_minutes = ((minutes_since_midnight // 15) + 1) * 15
    return base_dt.replace(hour=0, minute=0) + datetime.timedelta(minutes=next_minutes)


def round_to_nearest_50(price: float) -> int:
    remainder = price % 50
    rounded_down = int(price - remainder)
    return rounded_down if remainder < 25 else rounded_down + 50


def format_money(value: float) -> str:
    return f"{value:.2f}"


def format_optional_money(value: Optional[float]) -> str:
    return "" if value is None else format_money(value)


def leg_pnl_after_slippage(raw_points_pnl: float, slippage_points_per_order: float) -> float:
    return raw_points_pnl - (2 * slippage_points_per_order)


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("short_atm_nifty_ma_weekly_intraday_trailing_2025")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def join_remarks(parts: List[str]) -> str:
    return "; ".join(part for part in parts if part)


def summarize_timestamps(label: str, timestamps: List[str], edge_count: int = 5) -> str:
    if len(timestamps) <= edge_count * 2:
        return f"{label}: " + ", ".join(timestamps)
    first_values = ", ".join(timestamps[:edge_count])
    last_values = ", ".join(timestamps[-edge_count:])
    return (
        f"{label}: {len(timestamps)} missing timestamps from {timestamps[0]} through {timestamps[-1]}; "
        f"first {edge_count}: {first_values}; last {edge_count}: {last_values}"
    )


def load_spot_15m_data(spot_file: Path) -> Spot15Data:
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

            if timestamp.startswith("2025-"):
                day = timestamp[:10]
                if day not in seen_days:
                    trading_days.append(day)
                    seen_days.add(day)

    return Spot15Data(
        rows_by_timestamp=rows_by_timestamp,
        ordered_rows=ordered_rows,
        index_by_timestamp=index_by_timestamp,
        trading_days=trading_days,
    )


def load_spot_1m_data(spot_file: Path) -> Spot1mData:
    rows_by_day: Dict[str, Dict[str, PriceRow]] = {}

    with spot_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = row["timestamp"]
            if not timestamp.startswith("2025-"):
                continue
            day = timestamp[:10]
            if day not in rows_by_day:
                rows_by_day[day] = {}
            rows_by_day[day][timestamp] = PriceRow(
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

    return Spot1mData(rows_by_day=rows_by_day)


def load_expiry_folders(options_dir: Path) -> List[str]:
    return sorted(path.name for path in options_dir.iterdir() if path.is_dir())


def first_expiry_on_or_after(expiries: List[str], entry_date: str) -> Optional[str]:
    for expiry in expiries:
        if expiry >= entry_date:
            return expiry
    return None


def expiry_suffix(expiry_date: str) -> str:
    expiry_dt = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
    return expiry_dt.strftime("%d_%b_%y").upper()


def load_contract(contract_path: Path, cache: Dict[Path, ContractData]) -> Optional[ContractData]:
    if contract_path in cache:
        return cache[contract_path]
    if not contract_path.exists():
        return None

    rows_by_timestamp: Dict[str, OptionRow] = {}
    with contract_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = row["timestamp"]
            rows_by_timestamp[timestamp] = OptionRow(
                timestamp=timestamp,
                open_value=float(row["open"]),
                open_text=row["open"],
            )

    contract_data = ContractData(path=contract_path, rows_by_timestamp=rows_by_timestamp)
    cache[contract_path] = contract_data
    return contract_data


def compute_spot_sma_including_current(
    spot_data: Spot15Data,
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


def make_skipped_trade(
    entry_date: str,
    skip_reason: str,
    expiry_date: str = "",
    signal_timestamp: str = "",
    signal_close: str = "",
    spot_sma_25: str = "",
    spot_signal_relation: str = "",
    entry_timestamp: str = "",
    atm_strike: str = "",
    sold_side: str = "",
    contract_name: str = "",
    option_entry_open: str = "",
    exit_timestamp: str = "",
    option_exit_open: str = "",
    exit_reason: str = "",
    exit_spot_ma: str = "",
    remarks: str = "",
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date,
        status="SKIPPED",
        skip_reason=skip_reason,
        expiry_date=expiry_date,
        signal_timestamp=signal_timestamp,
        signal_close=signal_close,
        spot_sma_25=spot_sma_25,
        spot_signal_relation=spot_signal_relation,
        entry_timestamp=entry_timestamp,
        atm_strike=atm_strike,
        sold_side=sold_side,
        contract_name=contract_name,
        option_entry_open=option_entry_open,
        exit_timestamp=exit_timestamp,
        option_exit_open=option_exit_open,
        exit_reason=exit_reason,
        exit_spot_ma=exit_spot_ma,
        gross_pnl="0.00",
        brokerage="0.00",
        net_pnl="0.00",
        remarks=remarks,
    )


def make_traded_result(
    entry_date: str,
    expiry_date: str,
    signal_timestamp: str,
    signal_close: str,
    spot_sma_25: str,
    spot_signal_relation: str,
    entry_timestamp: str,
    atm_strike: str,
    sold_side: str,
    contract_name: str,
    option_entry_open: str,
    exit_timestamp: str,
    option_exit_open: str,
    exit_reason: str,
    exit_spot_ma: str,
    gross_pnl: float,
    brokerage: float,
    net_pnl: float,
    remarks: str = "",
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date,
        status="TRADED",
        skip_reason="",
        expiry_date=expiry_date,
        signal_timestamp=signal_timestamp,
        signal_close=signal_close,
        spot_sma_25=spot_sma_25,
        spot_signal_relation=spot_signal_relation,
        entry_timestamp=entry_timestamp,
        atm_strike=atm_strike,
        sold_side=sold_side,
        contract_name=contract_name,
        option_entry_open=option_entry_open,
        exit_timestamp=exit_timestamp,
        option_exit_open=option_exit_open,
        exit_reason=exit_reason,
        exit_spot_ma=exit_spot_ma,
        gross_pnl=format_money(gross_pnl),
        brokerage=format_money(brokerage),
        net_pnl=format_money(net_pnl),
        remarks=remarks,
    )


def resolve_trade_exit(
    entry_row: OptionRow,
    contract_data: ContractData,
    spot_1m_rows: Dict[str, PriceRow],
    spot_15m_data: Spot15Data,
    day: str,
    entry_timestamp: str,
    exit_time: str,
    sold_side: str,
    ma_period: int,
    slippage_points_per_order: float,
    brokerage_per_order: float,
    contract_multiplier: int,
) -> ExitOutcome:
    entry_dt = timestamp_to_datetime(entry_timestamp)
    final_exit_timestamp = build_timestamp(day, exit_time)
    final_exit_dt = timestamp_to_datetime(final_exit_timestamp)
    current_dt = entry_dt + datetime.timedelta(minutes=1)

    while current_dt < final_exit_dt:
        spot_timestamp = datetime_to_timestamp(current_dt)
        spot_row = spot_1m_rows.get(spot_timestamp)
        if spot_row is None:
            return ExitOutcome(
                status="SKIPPED",
                skip_reason="missing_spot_1m_timestamp",
                exit_timestamp=spot_timestamp,
                option_exit_open="",
                exit_reason="",
                exit_spot_ma="",
                gross_pnl=0.0,
                brokerage=0.0,
                net_pnl=0.0,
                remarks=f"Missing 1-minute NIFTY monitoring timestamp {spot_timestamp}",
            )

        stop_signal_timestamp = latest_completed_signal_timestamp(spot_timestamp)
        stop_sma, observed_count = compute_spot_sma_including_current(
            spot_15m_data,
            stop_signal_timestamp,
            ma_period,
        )
        if stop_sma is None:
            return ExitOutcome(
                status="SKIPPED",
                skip_reason="missing_or_insufficient_stop_sma",
                exit_timestamp=spot_timestamp,
                option_exit_open="",
                exit_reason="",
                exit_spot_ma="",
                gross_pnl=0.0,
                brokerage=0.0,
                net_pnl=0.0,
                remarks=(
                    f"{stop_signal_timestamp} has {observed_count} spot bars including the stop bar; "
                    f"needs {ma_period}"
                ),
            )

        stop_hit = (
            spot_row.low_value <= stop_sma
            if sold_side == "PE"
            else spot_row.high_value >= stop_sma
        )
        if stop_hit:
            exit_row = contract_data.rows_by_timestamp.get(spot_timestamp)
            if exit_row is None:
                return ExitOutcome(
                    status="SKIPPED",
                    skip_reason="missing_option_exit_timestamp",
                    exit_timestamp=spot_timestamp,
                    option_exit_open="",
                    exit_reason="stop_loss_ma_touch",
                    exit_spot_ma=format_money(stop_sma),
                    gross_pnl=0.0,
                    brokerage=0.0,
                    net_pnl=0.0,
                    remarks=f"{contract_data.path.name} missing stop exit timestamp {spot_timestamp}",
                )

            gross_pnl = (
                leg_pnl_after_slippage(
                    entry_row.open_value - exit_row.open_value,
                    slippage_points_per_order,
                )
                * contract_multiplier
            )
            brokerage = brokerage_per_order * 2
            net_pnl = gross_pnl - brokerage
            return ExitOutcome(
                status="TRADED",
                skip_reason="",
                exit_timestamp=spot_timestamp,
                option_exit_open=exit_row.open_text,
                exit_reason="stop_loss_ma_touch",
                exit_spot_ma=format_money(stop_sma),
                gross_pnl=gross_pnl,
                brokerage=brokerage,
                net_pnl=net_pnl,
                remarks="",
            )

        current_dt += datetime.timedelta(minutes=1)

    exit_row = contract_data.rows_by_timestamp.get(final_exit_timestamp)
    if exit_row is None:
        return ExitOutcome(
            status="SKIPPED",
            skip_reason="missing_option_exit_timestamp",
            exit_timestamp=final_exit_timestamp,
            option_exit_open="",
            exit_reason="day_close",
            exit_spot_ma="",
            gross_pnl=0.0,
            brokerage=0.0,
            net_pnl=0.0,
            remarks=f"{contract_data.path.name} missing scheduled exit timestamp {final_exit_timestamp}",
        )

    final_stop_signal_timestamp = signal_timestamp_for_entry(final_exit_timestamp)
    final_sma, _ = compute_spot_sma_including_current(
        spot_15m_data,
        final_stop_signal_timestamp,
        ma_period,
    )
    gross_pnl = (
        leg_pnl_after_slippage(
            entry_row.open_value - exit_row.open_value,
            slippage_points_per_order,
        )
        * contract_multiplier
    )
    brokerage = brokerage_per_order * 2
    net_pnl = gross_pnl - brokerage
    return ExitOutcome(
        status="TRADED",
        skip_reason="",
        exit_timestamp=final_exit_timestamp,
        option_exit_open=exit_row.open_text,
        exit_reason="day_close",
        exit_spot_ma=format_optional_money(final_sma),
        gross_pnl=gross_pnl,
        brokerage=brokerage,
        net_pnl=net_pnl,
        remarks="",
    )


def aggregate_day_result(entry_date: str, expiry_date: str, trade_results: List[TradeResult]) -> DayResult:
    traded_results = [result for result in trade_results if result.status == "TRADED"]
    skipped_results = [result for result in trade_results if result.status == "SKIPPED"]
    gross_total = sum(float(result.gross_pnl) for result in traded_results)
    brokerage_total = sum(float(result.brokerage) for result in traded_results)
    net_total = sum(float(result.net_pnl) for result in traded_results)
    ce_trades = sum(1 for result in traded_results if result.sold_side == "CE")
    pe_trades = sum(1 for result in traded_results if result.sold_side == "PE")
    stopped_trades = sum(1 for result in traded_results if result.exit_reason == "stop_loss_ma_touch")
    day_close_trades = sum(1 for result in traded_results if result.exit_reason == "day_close")
    skipped_reasons = [result.skip_reason for result in skipped_results if result.skip_reason]
    skipped_remarks = [result.remarks for result in skipped_results if result.remarks]

    if traded_results:
        status = "TRADED"
        skip_reason = ";".join(sorted(set(skipped_reasons)))
    else:
        status = "SKIPPED"
        skip_reason = ";".join(sorted(set(skipped_reasons))) if skipped_reasons else "no_completed_trade"

    return DayResult(
        entry_date=entry_date,
        status=status,
        skip_reason=skip_reason,
        expiry_date=expiry_date,
        trades=str(len(traded_results)),
        ce_trades=str(ce_trades),
        pe_trades=str(pe_trades),
        stopped_trades=str(stopped_trades),
        day_close_trades=str(day_close_trades),
        skipped_signals=str(len(skipped_results)),
        orders_executed=str(2 * len(traded_results)),
        gross_pnl=format_money(gross_total),
        brokerage=format_money(brokerage_total),
        net_pnl=format_money(net_total),
        remarks=join_remarks(skipped_remarks),
    )


def run_backtest(args: argparse.Namespace) -> Tuple[List[TradeResult], List[DayResult]]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    spot_15m_data = load_spot_15m_data(args.spot_15m_file)
    spot_1m_data = load_spot_1m_data(args.spot_1m_file)
    expiries = load_expiry_folders(args.options_dir)
    contract_cache: Dict[Path, ContractData] = {}
    trade_results: List[TradeResult] = []
    day_results: List[DayResult] = []
    contract_multiplier = args.lot_size * args.lots

    try:
        for entry_date in spot_15m_data.trading_days:
            day_trade_results: List[TradeResult] = []
            expiry_date = first_expiry_on_or_after(expiries, entry_date) or ""
            minute_timestamps = build_intraday_timestamps(
                entry_date,
                args.entry_start_time,
                args.exit_time,
                step_minutes=1,
            )
            entry_timestamps = build_intraday_timestamps(
                entry_date,
                args.entry_start_time,
                args.last_entry_time,
                step_minutes=15,
            )
            spot_1m_rows = spot_1m_data.rows_by_day.get(entry_date, {})
            missing_minute_timestamps = [
                timestamp for timestamp in minute_timestamps if timestamp not in spot_1m_rows
            ]

            if missing_minute_timestamps:
                remarks = summarize_timestamps(
                    "Missing 1-minute NIFTY monitoring timestamps",
                    missing_minute_timestamps,
                )
                result = make_skipped_trade(
                    entry_date=entry_date,
                    skip_reason="missing_spot_1m_timestamp",
                    expiry_date=expiry_date,
                    entry_timestamp=build_timestamp(entry_date, args.entry_start_time),
                    remarks=remarks,
                )
                day_trade_results.append(result)
                trade_results.append(result)
                day_result = aggregate_day_result(entry_date, expiry_date, day_trade_results)
                day_results.append(day_result)
                logger.info("SKIPPED date=%s reason=missing_spot_1m_timestamp", entry_date)
                continue

            if not expiry_date:
                result = make_skipped_trade(
                    entry_date=entry_date,
                    skip_reason="no_same_week_expiry",
                    entry_timestamp=build_timestamp(entry_date, args.entry_start_time),
                    remarks="No expiry folder exists on or after this trade date.",
                )
                day_trade_results.append(result)
                trade_results.append(result)
                day_result = aggregate_day_result(entry_date, "", day_trade_results)
                day_results.append(day_result)
                logger.info("SKIPPED date=%s reason=no_same_week_expiry", entry_date)
                continue

            option_suffix = expiry_suffix(expiry_date)
            next_allowed_entry_dt = timestamp_to_datetime(entry_timestamps[0])
            stop_processing_day = False

            for entry_timestamp in entry_timestamps:
                if timestamp_to_datetime(entry_timestamp) < next_allowed_entry_dt:
                    continue

                signal_timestamp = signal_timestamp_for_entry(entry_timestamp)
                signal_row = spot_15m_data.rows_by_timestamp.get(signal_timestamp)
                if signal_row is None:
                    result = make_skipped_trade(
                        entry_date=entry_date,
                        skip_reason="missing_spot_signal_timestamp",
                        expiry_date=expiry_date,
                        signal_timestamp=signal_timestamp,
                        entry_timestamp=entry_timestamp,
                        remarks=f"Missing 15-minute NIFTY signal timestamp {signal_timestamp}",
                    )
                    day_trade_results.append(result)
                    trade_results.append(result)
                    logger.info("SKIPPED date=%s entry=%s reason=missing_spot_signal_timestamp", entry_date, entry_timestamp)
                    continue

                spot_sma_25, observed_count = compute_spot_sma_including_current(
                    spot_15m_data,
                    signal_timestamp,
                    args.ma_period,
                )
                if spot_sma_25 is None:
                    result = make_skipped_trade(
                        entry_date=entry_date,
                        skip_reason="insufficient_spot_history",
                        expiry_date=expiry_date,
                        signal_timestamp=signal_timestamp,
                        signal_close=signal_row.close_text,
                        entry_timestamp=entry_timestamp,
                        remarks=(
                            f"{signal_timestamp} has {observed_count} spot bars including the signal bar; "
                            f"needs {args.ma_period}"
                        ),
                    )
                    day_trade_results.append(result)
                    trade_results.append(result)
                    logger.info("SKIPPED date=%s entry=%s reason=insufficient_spot_history", entry_date, entry_timestamp)
                    continue

                spot_sma_text = format_money(spot_sma_25)
                atm_strike = round_to_nearest_50(signal_row.close_value)
                strike_text = str(atm_strike)

                if signal_row.close_value > spot_sma_25:
                    spot_signal_relation = "ABOVE_SMA"
                    sold_side = "PE"
                elif signal_row.close_value < spot_sma_25:
                    spot_signal_relation = "BELOW_SMA"
                    sold_side = "CE"
                else:
                    result = make_skipped_trade(
                        entry_date=entry_date,
                        skip_reason="equal_close_and_sma",
                        expiry_date=expiry_date,
                        signal_timestamp=signal_timestamp,
                        signal_close=signal_row.close_text,
                        spot_sma_25=spot_sma_text,
                        spot_signal_relation="EQUAL_SMA",
                        entry_timestamp=entry_timestamp,
                        atm_strike=strike_text,
                        remarks=(
                            f"NIFTY close {signal_row.close_text} equals {args.ma_period}-SMA "
                            f"{spot_sma_text} at {signal_timestamp}"
                        ),
                    )
                    day_trade_results.append(result)
                    trade_results.append(result)
                    logger.info("SKIPPED date=%s entry=%s reason=equal_close_and_sma", entry_date, entry_timestamp)
                    continue

                contract_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_{sold_side}_{option_suffix}.csv"
                contract_data = load_contract(contract_path, contract_cache)
                if contract_data is None:
                    result = make_skipped_trade(
                        entry_date=entry_date,
                        skip_reason="missing_option_file",
                        expiry_date=expiry_date,
                        signal_timestamp=signal_timestamp,
                        signal_close=signal_row.close_text,
                        spot_sma_25=spot_sma_text,
                        spot_signal_relation=spot_signal_relation,
                        entry_timestamp=entry_timestamp,
                        atm_strike=strike_text,
                        sold_side=sold_side,
                        contract_name=contract_path.name,
                        remarks=f"Missing option file: {contract_path.name}",
                    )
                    day_trade_results.append(result)
                    trade_results.append(result)
                    logger.info(
                        "SKIPPED date=%s entry=%s expiry=%s side=%s strike=%s reason=missing_option_file",
                        entry_date,
                        entry_timestamp,
                        expiry_date,
                        sold_side,
                        strike_text,
                    )
                    continue

                entry_row = contract_data.rows_by_timestamp.get(entry_timestamp)
                if entry_row is None:
                    remarks = (
                        f"{contract_path.name} is header-only"
                        if not contract_data.rows_by_timestamp
                        else f"{contract_path.name} missing entry timestamp {entry_timestamp}"
                    )
                    result = make_skipped_trade(
                        entry_date=entry_date,
                        skip_reason="missing_option_entry_timestamp",
                        expiry_date=expiry_date,
                        signal_timestamp=signal_timestamp,
                        signal_close=signal_row.close_text,
                        spot_sma_25=spot_sma_text,
                        spot_signal_relation=spot_signal_relation,
                        entry_timestamp=entry_timestamp,
                        atm_strike=strike_text,
                        sold_side=sold_side,
                        contract_name=contract_path.name,
                        remarks=remarks,
                    )
                    day_trade_results.append(result)
                    trade_results.append(result)
                    logger.info(
                        "SKIPPED date=%s entry=%s expiry=%s side=%s strike=%s reason=missing_option_entry_timestamp",
                        entry_date,
                        entry_timestamp,
                        expiry_date,
                        sold_side,
                        strike_text,
                    )
                    continue

                exit_outcome = resolve_trade_exit(
                    entry_row=entry_row,
                    contract_data=contract_data,
                    spot_1m_rows=spot_1m_rows,
                    spot_15m_data=spot_15m_data,
                    day=entry_date,
                    entry_timestamp=entry_timestamp,
                    exit_time=args.exit_time,
                    sold_side=sold_side,
                    ma_period=args.ma_period,
                    slippage_points_per_order=args.slippage_points_per_order,
                    brokerage_per_order=args.brokerage_per_order,
                    contract_multiplier=contract_multiplier,
                )

                if exit_outcome.status == "SKIPPED":
                    result = make_skipped_trade(
                        entry_date=entry_date,
                        skip_reason=exit_outcome.skip_reason,
                        expiry_date=expiry_date,
                        signal_timestamp=signal_timestamp,
                        signal_close=signal_row.close_text,
                        spot_sma_25=spot_sma_text,
                        spot_signal_relation=spot_signal_relation,
                        entry_timestamp=entry_timestamp,
                        atm_strike=strike_text,
                        sold_side=sold_side,
                        contract_name=contract_path.name,
                        option_entry_open=entry_row.open_text,
                        exit_timestamp=exit_outcome.exit_timestamp,
                        option_exit_open=exit_outcome.option_exit_open,
                        exit_reason=exit_outcome.exit_reason,
                        exit_spot_ma=exit_outcome.exit_spot_ma,
                        remarks=exit_outcome.remarks,
                    )
                    day_trade_results.append(result)
                    trade_results.append(result)
                    stop_processing_day = True
                    logger.info(
                        "SKIPPED_ACTIVE_TRADE date=%s entry=%s expiry=%s side=%s strike=%s reason=%s",
                        entry_date,
                        entry_timestamp,
                        expiry_date,
                        sold_side,
                        strike_text,
                        exit_outcome.skip_reason,
                    )
                    break

                result = make_traded_result(
                    entry_date=entry_date,
                    expiry_date=expiry_date,
                    signal_timestamp=signal_timestamp,
                    signal_close=signal_row.close_text,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation=spot_signal_relation,
                    entry_timestamp=entry_timestamp,
                    atm_strike=strike_text,
                    sold_side=sold_side,
                    contract_name=contract_path.name,
                    option_entry_open=entry_row.open_text,
                    exit_timestamp=exit_outcome.exit_timestamp,
                    option_exit_open=exit_outcome.option_exit_open,
                    exit_reason=exit_outcome.exit_reason,
                    exit_spot_ma=exit_outcome.exit_spot_ma,
                    gross_pnl=exit_outcome.gross_pnl,
                    brokerage=exit_outcome.brokerage,
                    net_pnl=exit_outcome.net_pnl,
                    remarks=exit_outcome.remarks,
                )
                day_trade_results.append(result)
                trade_results.append(result)
                logger.info(
                    "TRADED date=%s entry=%s exit=%s expiry=%s side=%s strike=%s gross=%s brokerage=%s net=%s reason=%s",
                    entry_date,
                    entry_timestamp,
                    exit_outcome.exit_timestamp,
                    expiry_date,
                    sold_side,
                    strike_text,
                    result.gross_pnl,
                    result.brokerage,
                    result.net_pnl,
                    exit_outcome.exit_reason,
                )

                if exit_outcome.exit_reason == "day_close":
                    stop_processing_day = True
                    break

                next_allowed_entry_dt = next_15m_boundary_after(exit_outcome.exit_timestamp)

            if stop_processing_day:
                logger.info("DAY_STOPPED date=%s", entry_date)

            if not day_trade_results:
                result = make_skipped_trade(
                    entry_date=entry_date,
                    skip_reason="no_entry_signal",
                    expiry_date=expiry_date,
                    entry_timestamp=build_timestamp(entry_date, args.entry_start_time),
                    remarks="No completed trades or material skipped signals were produced for this date.",
                )
                day_trade_results.append(result)
                trade_results.append(result)

            day_result = aggregate_day_result(entry_date, expiry_date, day_trade_results)
            day_results.append(day_result)

    except Exception:
        logger.exception("ERROR unexpected failure while running the backtest")
        raise

    traded_count = sum(1 for result in trade_results if result.status == "TRADED")
    skipped_count = sum(1 for result in trade_results if result.status == "SKIPPED")
    traded_days = sum(1 for result in day_results if int(result.trades) > 0)
    skipped_days = len(day_results) - traded_days
    logger.info(
        "COMPLETED trades=%s skipped_trade_rows=%s traded_days=%s skipped_days=%s total_days=%s",
        traded_count,
        skipped_count,
        traded_days,
        skipped_days,
        len(day_results),
    )
    return trade_results, day_results


def write_tradewise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "skip_reason",
        "expiry_date",
        "signal_timestamp",
        "signal_close",
        "spot_sma_25",
        "spot_signal_relation",
        "entry_timestamp",
        "atm_strike",
        "sold_side",
        "contract_name",
        "option_entry_open",
        "exit_timestamp",
        "option_exit_open",
        "exit_reason",
        "exit_spot_ma",
        "gross_pnl",
        "brokerage",
        "net_pnl",
        "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)


def write_daywise_csv(results: List[DayResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "skip_reason",
        "expiry_date",
        "trades",
        "ce_trades",
        "pe_trades",
        "stopped_trades",
        "day_close_trades",
        "skipped_signals",
        "orders_executed",
        "gross_pnl",
        "brokerage",
        "net_pnl",
        "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)


def compute_max_consecutive_streaks(net_pnl_values: List[float]) -> Tuple[int, int]:
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    current_wins = 0
    current_losses = 0

    for net_pnl in net_pnl_values:
        if net_pnl > 0:
            current_wins += 1
            current_losses = 0
            max_consecutive_wins = max(max_consecutive_wins, current_wins)
        elif net_pnl < 0:
            current_losses += 1
            current_wins = 0
            max_consecutive_losses = max(max_consecutive_losses, current_losses)
        else:
            current_wins = 0
            current_losses = 0

    return max_consecutive_wins, max_consecutive_losses


def compute_max_drawdown(net_pnl_values: List[float]) -> float:
    cumulative_net = 0.0
    equity_peak = 0.0
    max_drawdown = 0.0

    for net_pnl in net_pnl_values:
        cumulative_net += net_pnl
        equity_peak = max(equity_peak, cumulative_net)
        max_drawdown = max(max_drawdown, equity_peak - cumulative_net)

    return max_drawdown


def write_summary(
    trade_results: List[TradeResult],
    day_results: List[DayResult],
    output_path: Path,
    args: argparse.Namespace,
) -> None:
    traded_trade_results = [result for result in trade_results if result.status == "TRADED"]
    skipped_trade_results = [result for result in trade_results if result.status == "SKIPPED"]
    traded_day_results = [result for result in day_results if int(result.trades) > 0]
    skipped_day_results = [result for result in day_results if int(result.trades) == 0]
    gross_total = sum(float(result.gross_pnl) for result in traded_day_results)
    brokerage_total = sum(float(result.brokerage) for result in traded_day_results)
    net_total = sum(float(result.net_pnl) for result in traded_day_results)
    ce_sell_count = sum(1 for result in traded_trade_results if result.sold_side == "CE")
    pe_sell_count = sum(1 for result in traded_trade_results if result.sold_side == "PE")
    stopped_count = sum(1 for result in traded_trade_results if result.exit_reason == "stop_loss_ma_touch")
    day_close_count = sum(1 for result in traded_trade_results if result.exit_reason == "day_close")
    net_pnl_values = [float(result.net_pnl) for result in traded_day_results]
    winning_days = sum(1 for net_pnl in net_pnl_values if net_pnl > 0)
    losing_days = sum(1 for net_pnl in net_pnl_values if net_pnl < 0)
    break_even_days = sum(1 for net_pnl in net_pnl_values if net_pnl == 0)
    max_consecutive_wins, max_consecutive_losses = compute_max_consecutive_streaks(net_pnl_values)
    max_drawdown = compute_max_drawdown(net_pnl_values)
    max_profit_day = max(traded_day_results, key=lambda result: float(result.net_pnl), default=None)
    max_loss_day = min(traded_day_results, key=lambda result: float(result.net_pnl), default=None)

    lines: List[str] = [
        "# 2025 Intraday Weekly Short ATM NIFTY 25-SMA Trailing Backtest",
        "",
        "## Strategy Details",
        "",
        "- Signal source: NIFTY 15-minute close",
        f"- Entry window: `{args.entry_start_time}` through `{args.last_entry_time}`",
        f"- Exit time: `{args.exit_time}`",
        f"- MA rule: {args.ma_period}-SMA of 15-minute NIFTY closes including the signal candle",
        "- Signal timing: each entry uses the completed 15-minute candle ending at that entry timestamp",
        "- Direction rule: above SMA -> short ATM PE; below SMA -> short ATM CE; equal -> no trade",
        "- Stop source: NIFTY 1-minute candles",
        "- Stop rule: short PE exits when 1-minute NIFTY low touches the trailing MA; short CE exits when high touches it",
        "- Trailing MA rule: latest completed 15-minute NIFTY SMA stays fixed until the next 15-minute close",
        "- Re-entry rule: one active trade at a time; after a stop, the next entry can only use a later 15-minute close",
        "- Expiry rule: first weekly expiry folder on or after the trade date",
        "- ATM rule: nearest 50 using the signal candle close",
        "- Pricing rule: exact option open price at exact timestamps",
        f"- Contract multiplier: {args.lot_size} x {args.lots} = {args.lot_size * args.lots} rupees per option point",
        f"- Execution slippage: {format_money(args.slippage_points_per_order)} point per order, applied against every entry and exit",
        (
            f"- Brokerage rule: Rs {int(args.brokerage_per_order)} per order, "
            f"so one completed short leg pays Rs {int(args.brokerage_per_order * 2)}"
        ),
        "",
        "## Results Summary",
        "",
        f"- Traded days: `{len(traded_day_results)}`",
        f"- Skipped days: `{len(skipped_day_results)}`",
        f"- Completed trades: `{len(traded_trade_results)}`",
        f"- Skipped trade/signal rows: `{len(skipped_trade_results)}`",
        f"- CE-sell count: `{ce_sell_count}`",
        f"- PE-sell count: `{pe_sell_count}`",
        f"- Stop-loss exits: `{stopped_count}`",
        f"- Day-close exits: `{day_close_count}`",
        f"- Winning days: `{winning_days}`",
        f"- Losing days: `{losing_days}`",
        f"- Break-even days: `{break_even_days}`",
        (
            f"- Max profit day: `{max_profit_day.entry_date}` with net P/L "
            f"`{max_profit_day.net_pnl}`"
            if max_profit_day
            else "- Max profit day: `N/A`"
        ),
        (
            f"- Max loss day: `{max_loss_day.entry_date}` with net P/L "
            f"`{max_loss_day.net_pnl}`"
            if max_loss_day
            else "- Max loss day: `N/A`"
        ),
        f"- Max consecutive wins: `{max_consecutive_wins}`",
        f"- Max consecutive losses: `{max_consecutive_losses}`",
        f"- Max drawdown: `{format_money(max_drawdown)}`",
        f"- Total Profit/Loss: `{format_money(net_total)}`",
        f"- Total Brokerage: `{format_money(brokerage_total)}`",
        f"- Profit/Loss without Brokerage: `{format_money(gross_total)}`",
        "",
        "## Exceptions",
        "",
    ]

    exception_rows = [result for result in day_results if result.skip_reason or result.remarks]
    if exception_rows:
        for result in exception_rows:
            lines.append(f"- `{result.entry_date}`: `{result.skip_reason}`. {result.remarks}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Remarks",
            "",
            "- Exact timestamp matching is required; no nearest-candle fallback is allowed.",
            "- The 15-minute NIFTY rows are treated as candle-start timestamps.",
            f"- The `{args.entry_start_time}` entry uses the prior `{signal_timestamp_for_entry(build_timestamp('2025-01-01', args.entry_start_time))[11:16]}` signal row.",
            "- Stop checking starts from the minute after entry and excludes the scheduled day-close timestamp.",
            f"- `{args.exit_time}` is the scheduled day-close execution proxy.",
            "- The NIFTY 15-minute spot file is the source of truth for the trading calendar.",
            "- Expiry folder dates are used as truth, which naturally handles Tuesday special expiries and holiday shifts.",
        ]
    )

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    trade_results, day_results = run_backtest(args)
    write_tradewise_csv(trade_results, args.results_dir / TRADEWISE_FILENAME)
    write_daywise_csv(day_results, args.results_dir / DAYWISE_FILENAME)
    write_summary(trade_results, day_results, args.results_dir / SUMMARY_FILENAME, args)


if __name__ == "__main__":
    main()
