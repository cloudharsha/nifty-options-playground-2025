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
TRADEWISE_FILENAME = "expiry_itm100_ma_short_0920_2025_trades.csv"
DAYWISE_FILENAME = "expiry_itm100_ma_short_0920_2025_daywise.csv"
SUMMARY_FILENAME = "expiry_itm100_ma_short_0920_2025_summary.md"
LOG_FILENAME = "expiry_itm100_ma_short_0920_2025.log"


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
    exit_timestamp: str
    atm_strike: str
    itm_strike: str
    itm_distance_points: str
    sold_side: str
    contract_name: str
    option_entry_open: str
    option_exit_open: str
    exit_reason: str
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
    orders_executed: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Backtest a 2025 expiry-day-only directional short ITM option strategy "
            "using a NIFTY 25-SMA signal."
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
    parser.add_argument("--entry-time", default="09:20")
    parser.add_argument("--exit-time", default="15:00")
    parser.add_argument(
        "--signal-time",
        default="09:15",
        help="15-minute NIFTY row used when --signal-mode=signal-15m-row.",
    )
    parser.add_argument(
        "--signal-mode",
        choices=["live-entry", "signal-15m-row"],
        default="live-entry",
        help=(
            "live-entry uses the entry-time 1-minute NIFTY open as the current "
            "15-minute candle value; signal-15m-row uses --signal-time 15-minute close."
        ),
    )
    parser.add_argument("--ma-period", type=int, default=25)
    parser.add_argument("--itm-distance-points", type=int, default=100)
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--lot-size", type=int, default=65)
    parser.add_argument("--lots", type=int, default=4)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
    args = parser.parse_args()

    if not args.entry_time < args.exit_time:
        parser.error("--entry-time must be before --exit-time")
    if args.itm_distance_points <= 0:
        parser.error("--itm-distance-points must be positive")
    if args.ma_period <= 0:
        parser.error("--ma-period must be positive")

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


def current_15m_candle_start_timestamp(timestamp: str) -> str:
    value = timestamp_to_datetime(timestamp)
    floored_minute = (value.minute // 15) * 15
    return datetime_to_timestamp(value.replace(minute=floored_minute, second=0, microsecond=0))


def round_to_nearest_50(price: float) -> int:
    remainder = price % 50
    rounded_down = int(price - remainder)
    return rounded_down if remainder < 25 else rounded_down + 50


def format_money(value: float) -> str:
    return f"{value:.2f}"


def leg_pnl_after_slippage(raw_points_pnl: float, slippage_points_per_order: float) -> float:
    return raw_points_pnl - (2 * slippage_points_per_order)


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("expiry_itm100_ma_short_0920_2025")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def join_remarks(parts: List[str]) -> str:
    return "; ".join(part for part in parts if part)


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


def compute_live_entry_sma(
    spot_data: Spot15Data,
    entry_timestamp: str,
    entry_spot_value: float,
    ma_period: int,
) -> Tuple[Optional[float], int, str]:
    current_15m_start = current_15m_candle_start_timestamp(entry_timestamp)
    current_index = spot_data.index_by_timestamp.get(current_15m_start)
    if current_index is None:
        return None, 0, current_15m_start

    previous_count_needed = ma_period - 1
    observed_count = current_index + 1
    if current_index < previous_count_needed:
        return None, observed_count, current_15m_start

    previous_window = spot_data.ordered_rows[current_index - previous_count_needed : current_index]
    sma = (sum(row.close_value for row in previous_window) + entry_spot_value) / ma_period
    return sma, observed_count, current_15m_start


def make_skipped_trade(
    entry_date: str,
    skip_reason: str,
    expiry_date: str = "",
    signal_timestamp: str = "",
    signal_close: str = "",
    spot_sma_25: str = "",
    spot_signal_relation: str = "",
    entry_timestamp: str = "",
    exit_timestamp: str = "",
    atm_strike: str = "",
    itm_strike: str = "",
    itm_distance_points: str = "",
    sold_side: str = "",
    contract_name: str = "",
    option_entry_open: str = "",
    option_exit_open: str = "",
    exit_reason: str = "",
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
        exit_timestamp=exit_timestamp,
        atm_strike=atm_strike,
        itm_strike=itm_strike,
        itm_distance_points=itm_distance_points,
        sold_side=sold_side,
        contract_name=contract_name,
        option_entry_open=option_entry_open,
        option_exit_open=option_exit_open,
        exit_reason=exit_reason,
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
    exit_timestamp: str,
    atm_strike: str,
    itm_strike: str,
    itm_distance_points: str,
    sold_side: str,
    contract_name: str,
    option_entry_open: str,
    option_exit_open: str,
    gross_pnl: float,
    brokerage: float,
    net_pnl: float,
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
        exit_timestamp=exit_timestamp,
        atm_strike=atm_strike,
        itm_strike=itm_strike,
        itm_distance_points=itm_distance_points,
        sold_side=sold_side,
        contract_name=contract_name,
        option_entry_open=option_entry_open,
        option_exit_open=option_exit_open,
        exit_reason="scheduled_exit",
        gross_pnl=format_money(gross_pnl),
        brokerage=format_money(brokerage),
        net_pnl=format_money(net_pnl),
        remarks="",
    )


def itm_strike_for_signal(atm_strike: int, sold_side: str, distance_points: int) -> int:
    if sold_side == "PE":
        return atm_strike + distance_points
    if sold_side == "CE":
        return atm_strike - distance_points
    raise ValueError(f"Unsupported side {sold_side!r}")


def aggregate_day_result(entry_date: str, expiry_date: str, trade_results: List[TradeResult]) -> DayResult:
    traded_results = [result for result in trade_results if result.status == "TRADED"]
    skipped_results = [result for result in trade_results if result.status == "SKIPPED"]
    gross_total = sum(float(result.gross_pnl) for result in traded_results)
    brokerage_total = sum(float(result.brokerage) for result in traded_results)
    net_total = sum(float(result.net_pnl) for result in traded_results)
    ce_trades = sum(1 for result in traded_results if result.sold_side == "CE")
    pe_trades = sum(1 for result in traded_results if result.sold_side == "PE")
    skipped_reasons = [result.skip_reason for result in skipped_results if result.skip_reason]
    skipped_remarks = [result.remarks for result in skipped_results if result.remarks]

    if traded_results:
        status = "TRADED"
        skip_reason = ""
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
    expiry_dates = load_expiry_folders(args.options_dir)
    trading_day_set = set(spot_15m_data.trading_days)
    expiry_trade_dates = [expiry for expiry in expiry_dates if expiry in trading_day_set]
    contract_cache: Dict[Path, ContractData] = {}
    trade_results: List[TradeResult] = []
    day_results: List[DayResult] = []
    contract_multiplier = args.lot_size * args.lots

    try:
        for entry_date in expiry_trade_dates:
            expiry_date = entry_date
            entry_timestamp = build_timestamp(entry_date, args.entry_time)
            exit_timestamp = build_timestamp(entry_date, args.exit_time)
            option_suffix = expiry_suffix(expiry_date)

            if args.signal_mode == "live-entry":
                entry_spot_row = spot_1m_data.rows_by_day.get(entry_date, {}).get(entry_timestamp)
                if entry_spot_row is None:
                    result = make_skipped_trade(
                        entry_date=entry_date,
                        skip_reason="missing_spot_entry_timestamp",
                        expiry_date=expiry_date,
                        signal_timestamp=entry_timestamp,
                        entry_timestamp=entry_timestamp,
                        exit_timestamp=exit_timestamp,
                        remarks=f"Missing 1-minute NIFTY entry timestamp {entry_timestamp}",
                    )
                    trade_results.append(result)
                    day_results.append(aggregate_day_result(entry_date, expiry_date, [result]))
                    logger.info("SKIPPED date=%s reason=missing_spot_entry_timestamp", entry_date)
                    continue
                signal_timestamp = entry_timestamp
                signal_value = entry_spot_row.open_value
                signal_text = entry_spot_row.open_text
                spot_sma_25, observed_count, current_15m_start = compute_live_entry_sma(
                    spot_15m_data,
                    entry_timestamp,
                    signal_value,
                    args.ma_period,
                )
                signal_source_note = (
                    f"Live entry signal uses {entry_timestamp} 1-minute open with prior "
                    f"{args.ma_period - 1} completed 15-minute closes; current 15-minute row is {current_15m_start}."
                )
            else:
                signal_timestamp = build_timestamp(entry_date, args.signal_time)
                signal_row = spot_15m_data.rows_by_timestamp.get(signal_timestamp)
                if signal_row is None:
                    result = make_skipped_trade(
                        entry_date=entry_date,
                        skip_reason="missing_spot_signal_timestamp",
                        expiry_date=expiry_date,
                        signal_timestamp=signal_timestamp,
                        entry_timestamp=entry_timestamp,
                        exit_timestamp=exit_timestamp,
                        remarks=f"Missing 15-minute NIFTY signal timestamp {signal_timestamp}",
                    )
                    trade_results.append(result)
                    day_results.append(aggregate_day_result(entry_date, expiry_date, [result]))
                    logger.info("SKIPPED date=%s reason=missing_spot_signal_timestamp", entry_date)
                    continue
                signal_value = signal_row.close_value
                signal_text = signal_row.close_text
                spot_sma_25, observed_count = compute_spot_sma_including_current(
                    spot_15m_data,
                    signal_timestamp,
                    args.ma_period,
                )
                signal_source_note = f"Signal row close from {signal_timestamp}."

            if spot_sma_25 is None:
                result = make_skipped_trade(
                    entry_date=entry_date,
                    skip_reason="insufficient_spot_history",
                    expiry_date=expiry_date,
                    signal_timestamp=signal_timestamp,
                    signal_close=signal_text,
                    entry_timestamp=entry_timestamp,
                    exit_timestamp=exit_timestamp,
                    remarks=(
                        f"{signal_timestamp} has {observed_count} spot bars including the signal context; "
                        f"needs {args.ma_period}"
                    ),
                )
                trade_results.append(result)
                day_results.append(aggregate_day_result(entry_date, expiry_date, [result]))
                logger.info("SKIPPED date=%s reason=insufficient_spot_history", entry_date)
                continue

            spot_sma_text = format_money(spot_sma_25)
            atm_strike = round_to_nearest_50(signal_value)
            atm_strike_text = str(atm_strike)

            if signal_value > spot_sma_25:
                spot_signal_relation = "ABOVE_SMA"
                sold_side = "PE"
            elif signal_value < spot_sma_25:
                spot_signal_relation = "BELOW_SMA"
                sold_side = "CE"
            else:
                result = make_skipped_trade(
                    entry_date=entry_date,
                    skip_reason="equal_close_and_sma",
                    expiry_date=expiry_date,
                    signal_timestamp=signal_timestamp,
                    signal_close=signal_text,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation="EQUAL_SMA",
                    entry_timestamp=entry_timestamp,
                    exit_timestamp=exit_timestamp,
                    atm_strike=atm_strike_text,
                    remarks=(
                        f"NIFTY signal value {signal_text} equals {args.ma_period}-SMA "
                        f"{spot_sma_text} at {signal_timestamp}. {signal_source_note}"
                    ),
                )
                trade_results.append(result)
                day_results.append(aggregate_day_result(entry_date, expiry_date, [result]))
                logger.info("SKIPPED date=%s reason=equal_close_and_sma", entry_date)
                continue

            itm_strike = itm_strike_for_signal(atm_strike, sold_side, args.itm_distance_points)
            itm_strike_text = str(itm_strike)
            contract_path = args.options_dir / expiry_date / f"NIFTY_{itm_strike}_{sold_side}_{option_suffix}.csv"
            contract_data = load_contract(contract_path, contract_cache)
            if contract_data is None:
                result = make_skipped_trade(
                    entry_date=entry_date,
                    skip_reason="missing_option_file",
                    expiry_date=expiry_date,
                    signal_timestamp=signal_timestamp,
                    signal_close=signal_text,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation=spot_signal_relation,
                    entry_timestamp=entry_timestamp,
                    exit_timestamp=exit_timestamp,
                    atm_strike=atm_strike_text,
                    itm_strike=itm_strike_text,
                    itm_distance_points=str(args.itm_distance_points),
                    sold_side=sold_side,
                    contract_name=contract_path.name,
                    remarks=f"Missing option file: {contract_path.name}. {signal_source_note}",
                )
                trade_results.append(result)
                day_results.append(aggregate_day_result(entry_date, expiry_date, [result]))
                logger.info(
                    "SKIPPED date=%s expiry=%s side=%s strike=%s reason=missing_option_file",
                    entry_date,
                    expiry_date,
                    sold_side,
                    itm_strike_text,
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
                    signal_close=signal_text,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation=spot_signal_relation,
                    entry_timestamp=entry_timestamp,
                    exit_timestamp=exit_timestamp,
                    atm_strike=atm_strike_text,
                    itm_strike=itm_strike_text,
                    itm_distance_points=str(args.itm_distance_points),
                    sold_side=sold_side,
                    contract_name=contract_path.name,
                    remarks=join_remarks([remarks, signal_source_note]),
                )
                trade_results.append(result)
                day_results.append(aggregate_day_result(entry_date, expiry_date, [result]))
                logger.info(
                    "SKIPPED date=%s expiry=%s side=%s strike=%s reason=missing_option_entry_timestamp",
                    entry_date,
                    expiry_date,
                    sold_side,
                    itm_strike_text,
                )
                continue

            exit_row = contract_data.rows_by_timestamp.get(exit_timestamp)
            if exit_row is None:
                result = make_skipped_trade(
                    entry_date=entry_date,
                    skip_reason="missing_option_exit_timestamp",
                    expiry_date=expiry_date,
                    signal_timestamp=signal_timestamp,
                    signal_close=signal_text,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation=spot_signal_relation,
                    entry_timestamp=entry_timestamp,
                    exit_timestamp=exit_timestamp,
                    atm_strike=atm_strike_text,
                    itm_strike=itm_strike_text,
                    itm_distance_points=str(args.itm_distance_points),
                    sold_side=sold_side,
                    contract_name=contract_path.name,
                    option_entry_open=entry_row.open_text,
                    exit_reason="scheduled_exit",
                    remarks=f"{contract_path.name} missing exit timestamp {exit_timestamp}. {signal_source_note}",
                )
                trade_results.append(result)
                day_results.append(aggregate_day_result(entry_date, expiry_date, [result]))
                logger.info(
                    "SKIPPED date=%s expiry=%s side=%s strike=%s reason=missing_option_exit_timestamp",
                    entry_date,
                    expiry_date,
                    sold_side,
                    itm_strike_text,
                )
                continue

            gross_pnl = (
                leg_pnl_after_slippage(
                    entry_row.open_value - exit_row.open_value,
                    args.slippage_points_per_order,
                )
                * contract_multiplier
            )
            brokerage = args.brokerage_per_order * 2
            net_pnl = gross_pnl - brokerage
            result = make_traded_result(
                entry_date=entry_date,
                expiry_date=expiry_date,
                signal_timestamp=signal_timestamp,
                signal_close=signal_text,
                spot_sma_25=spot_sma_text,
                spot_signal_relation=spot_signal_relation,
                entry_timestamp=entry_timestamp,
                exit_timestamp=exit_timestamp,
                atm_strike=atm_strike_text,
                itm_strike=itm_strike_text,
                itm_distance_points=str(args.itm_distance_points),
                sold_side=sold_side,
                contract_name=contract_path.name,
                option_entry_open=entry_row.open_text,
                option_exit_open=exit_row.open_text,
                gross_pnl=gross_pnl,
                brokerage=brokerage,
                net_pnl=net_pnl,
            )
            trade_results.append(result)
            day_results.append(aggregate_day_result(entry_date, expiry_date, [result]))
            logger.info(
                "TRADED date=%s entry=%s exit=%s expiry=%s side=%s strike=%s gross=%s brokerage=%s net=%s",
                entry_date,
                entry_timestamp,
                exit_timestamp,
                expiry_date,
                sold_side,
                itm_strike_text,
                result.gross_pnl,
                result.brokerage,
                result.net_pnl,
            )

    except Exception:
        logger.exception("ERROR unexpected failure while running the backtest")
        raise

    traded_count = sum(1 for result in trade_results if result.status == "TRADED")
    skipped_count = sum(1 for result in trade_results if result.status == "SKIPPED")
    logger.info(
        "COMPLETED expiry_days=%s trades=%s skipped_trade_rows=%s",
        len(day_results),
        traded_count,
        skipped_count,
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
        "exit_timestamp",
        "atm_strike",
        "itm_strike",
        "itm_distance_points",
        "sold_side",
        "contract_name",
        "option_entry_open",
        "option_exit_open",
        "exit_reason",
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
    net_pnl_values = [float(result.net_pnl) for result in traded_day_results]
    winning_days = sum(1 for net_pnl in net_pnl_values if net_pnl > 0)
    losing_days = sum(1 for net_pnl in net_pnl_values if net_pnl < 0)
    break_even_days = sum(1 for net_pnl in net_pnl_values if net_pnl == 0)
    max_consecutive_wins, max_consecutive_losses = compute_max_consecutive_streaks(net_pnl_values)
    max_drawdown = compute_max_drawdown(net_pnl_values)
    max_profit_day = max(traded_day_results, key=lambda result: float(result.net_pnl), default=None)
    max_loss_day = min(traded_day_results, key=lambda result: float(result.net_pnl), default=None)
    win_rate = (winning_days / len(traded_day_results) * 100) if traded_day_results else 0.0

    lines: List[str] = [
        "# 2025 Expiry-Day Short ITM 100 NIFTY 25-SMA Backtest",
        "",
        "## Strategy Details",
        "",
        "- Signal source: NIFTY spot versus 15-minute NIFTY SMA",
        f"- Trading days: expiry dates only from `{args.options_dir}` that overlap the 2025 spot calendar",
        f"- Entry time: `{args.entry_time}`",
        f"- Exit time: `{args.exit_time}`",
        f"- Signal mode: `{args.signal_mode}`",
        (
            f"- Signal value: `{args.entry_time}` 1-minute NIFTY open on the expiry date"
            if args.signal_mode == "live-entry"
            else f"- Signal value: `{args.signal_time}` 15-minute NIFTY close on the expiry date"
        ),
        (
            f"- MA rule: prior {args.ma_period - 1} completed 15-minute NIFTY closes plus the entry signal value"
            if args.signal_mode == "live-entry"
            else f"- MA rule: {args.ma_period}-SMA of 15-minute NIFTY closes including the signal row"
        ),
        "- Direction rule: above SMA -> short ITM PE; below SMA -> short ITM CE; equal -> no trade",
        f"- ITM rule: PE strike = ATM + {args.itm_distance_points}; CE strike = ATM - {args.itm_distance_points}",
        "- ATM rule: nearest 50 using the signal value",
        "- Expiry rule: trade only the option expiring that same day",
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
        f"- Expiry days tested: `{len(day_results)}`",
        f"- Traded days: `{len(traded_day_results)}`",
        f"- Skipped expiry days: `{len(skipped_day_results)}`",
        f"- Completed trades: `{len(traded_trade_results)}`",
        f"- Skipped trade rows: `{len(skipped_trade_results)}`",
        f"- CE-sell count: `{ce_sell_count}`",
        f"- PE-sell count: `{pe_sell_count}`",
        f"- Winning days: `{winning_days}`",
        f"- Losing days: `{losing_days}`",
        f"- Break-even days: `{break_even_days}`",
        f"- Win rate: `{win_rate:.2f}%`",
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
            (
                f"- The `{args.entry_time}` entry avoids using the unfinished `{args.signal_time}` 15-minute close "
                "by default; `--signal-mode signal-15m-row` can reproduce that alternate interpretation."
                if args.signal_mode == "live-entry"
                else f"- The `{args.entry_time}` entry uses the `{args.signal_time}` 15-minute row as the signal proxy."
            ),
            f"- `{args.exit_time}` is the scheduled expiry-day square-off proxy.",
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
