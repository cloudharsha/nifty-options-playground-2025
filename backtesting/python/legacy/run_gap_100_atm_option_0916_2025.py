#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


IST_SUFFIX = "+05:30"
BASE_FILENAME = "gap_100_atm_option_0916_2025"
DAYWISE_FILENAME = f"{BASE_FILENAME}_daywise.csv"
TRADES_FILENAME = f"{BASE_FILENAME}_trades.csv"
SUMMARY_FILENAME = f"{BASE_FILENAME}_summary.md"
LOG_FILENAME = f"{BASE_FILENAME}.log"


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
class ContractData:
    path: Path
    rows_by_timestamp: Dict[str, PriceRow]


@dataclass
class TradeResult:
    entry_date: str
    status: str
    skip_reason: str
    expiry_date: str
    previous_trading_day: str
    previous_close_timestamp: str
    previous_close: str
    gap_timestamp: str
    gap_open: str
    gap_points: str
    gap_percent: str
    entry_timestamp: str
    spot_entry_open: str
    exit_timestamp: str
    atm_strike: str
    option_side: str
    contract_file: str
    option_entry_open: str
    option_exit_open: str
    raw_points_pnl: str
    raw_gross_pnl: str
    slippage_points: str
    slippage_loss: str
    brokerage: str
    net_pnl: str
    remarks: str


@dataclass
class TradeRow:
    entry_date: str
    status: str
    expiry_date: str
    previous_trading_day: str
    previous_close: str
    gap_timestamp: str
    gap_open: str
    gap_points: str
    entry_timestamp: str
    spot_entry_open: str
    exit_timestamp: str
    atm_strike: str
    option_side: str
    contract_file: str
    option_entry_open: str
    option_exit_open: str
    raw_points_pnl: str
    raw_gross_pnl: str
    slippage_points: str
    slippage_loss: str
    brokerage: str
    net_pnl: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Backtest a 2025 100-point gap ATM option buy from 09:16 to 09:25.",
    )
    parser.add_argument(
        "--spot-file",
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
    parser.add_argument("--gap-time", default="09:15")
    parser.add_argument("--entry-time", default="09:16")
    parser.add_argument("--exit-time", default="09:25")
    parser.add_argument("--gap-threshold-points", type=float, default=100.0)
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--lot-size", type=int, default=65)
    parser.add_argument("--lots", type=int, default=4)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
    args = parser.parse_args()

    if args.gap_threshold_points <= 0:
        parser.error("--gap-threshold-points must be positive")
    if args.lot_size <= 0:
        parser.error("--lot-size must be positive")
    if args.lots <= 0:
        parser.error("--lots must be positive")
    if args.brokerage_per_order < 0:
        parser.error("--brokerage-per-order cannot be negative")
    if args.slippage_points_per_order < 0:
        parser.error("--slippage-points-per-order cannot be negative")

    return args


def build_timestamp(day: str, time_text: str) -> str:
    parts = time_text.split(":")
    if len(parts) != 2:
        raise ValueError(f"Time must be HH:MM, got {time_text!r}")
    hour, minute = parts
    return f"{day}T{hour}:{minute}:00{IST_SUFFIX}"


def round_to_nearest_50(price: float) -> int:
    remainder = price % 50
    rounded_down = int(price - remainder)
    return rounded_down if remainder < 25 else rounded_down + 50


def format_number(value: float) -> str:
    return f"{value:.2f}"


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger(BASE_FILENAME)
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def close_logger(logger: logging.Logger) -> None:
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()


def price_row_from_csv(row: Dict[str, str]) -> PriceRow:
    return PriceRow(
        timestamp=row["timestamp"],
        open_value=float(row["open"]),
        open_text=row["open"],
        high_value=float(row["high"]),
        high_text=row["high"],
        low_value=float(row["low"]),
        low_text=row["low"],
        close_value=float(row["close"]),
        close_text=row["close"],
    )


def load_spot_data(
    spot_file: Path,
) -> tuple[List[str], Dict[str, Dict[str, PriceRow]], Dict[str, List[str]]]:
    trading_days: List[str] = []
    rows_by_day: Dict[str, Dict[str, PriceRow]] = {}
    timestamps_by_day: Dict[str, List[str]] = {}

    with spot_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = row["timestamp"]
            if not timestamp.startswith("2025-"):
                continue
            day = timestamp[:10]
            if day not in rows_by_day:
                rows_by_day[day] = {}
                timestamps_by_day[day] = []
                trading_days.append(day)
            price_row = price_row_from_csv(row)
            rows_by_day[day][timestamp] = price_row
            timestamps_by_day[day].append(timestamp)

    return trading_days, rows_by_day, timestamps_by_day


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

    rows_by_timestamp: Dict[str, PriceRow] = {}
    with contract_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            price_row = price_row_from_csv(row)
            rows_by_timestamp[price_row.timestamp] = price_row

    contract_data = ContractData(path=contract_path, rows_by_timestamp=rows_by_timestamp)
    cache[contract_path] = contract_data
    return contract_data


def previous_close_for_day(
    trading_days: List[str],
    spot_rows_by_day: Dict[str, Dict[str, PriceRow]],
    timestamps_by_day: Dict[str, List[str]],
    day_index: int,
) -> Optional[tuple[str, PriceRow]]:
    if day_index == 0:
        return None
    previous_day = trading_days[day_index - 1]
    previous_timestamps = timestamps_by_day[previous_day]
    if not previous_timestamps:
        return None
    previous_row = spot_rows_by_day[previous_day][previous_timestamps[-1]]
    return previous_day, previous_row


def option_side_from_gap(gap_points: float, threshold_points: float) -> str:
    if gap_points >= threshold_points:
        return "CE"
    if gap_points <= -threshold_points:
        return "PE"
    return ""


def make_result(
    entry_date: str,
    status: str,
    skip_reason: str,
    expiry_date: str,
    previous_trading_day: str,
    previous_close_timestamp: str,
    previous_close: str,
    gap_timestamp: str,
    gap_open: str,
    gap_points: str,
    gap_percent: str,
    entry_timestamp: str,
    spot_entry_open: str,
    exit_timestamp: str,
    atm_strike: str,
    option_side: str,
    contract_file: str,
    option_entry_open: str,
    option_exit_open: str,
    raw_points_pnl: float,
    slippage_points: float,
    brokerage: float,
    contract_multiplier: int,
    remarks: str,
) -> TradeResult:
    raw_gross_pnl = raw_points_pnl * contract_multiplier if status == "TRADED" else 0.0
    slippage_loss = slippage_points * contract_multiplier if status == "TRADED" else 0.0
    net_pnl = raw_gross_pnl - slippage_loss - brokerage if status == "TRADED" else 0.0
    return TradeResult(
        entry_date=entry_date,
        status=status,
        skip_reason=skip_reason,
        expiry_date=expiry_date,
        previous_trading_day=previous_trading_day,
        previous_close_timestamp=previous_close_timestamp,
        previous_close=previous_close,
        gap_timestamp=gap_timestamp,
        gap_open=gap_open,
        gap_points=gap_points,
        gap_percent=gap_percent,
        entry_timestamp=entry_timestamp,
        spot_entry_open=spot_entry_open,
        exit_timestamp=exit_timestamp,
        atm_strike=atm_strike,
        option_side=option_side,
        contract_file=contract_file,
        option_entry_open=option_entry_open,
        option_exit_open=option_exit_open,
        raw_points_pnl=format_number(raw_points_pnl) if status == "TRADED" else "0.00",
        raw_gross_pnl=format_number(raw_gross_pnl),
        slippage_points=format_number(slippage_points) if status == "TRADED" else "0.00",
        slippage_loss=format_number(slippage_loss),
        brokerage=format_number(brokerage) if status == "TRADED" else "0.00",
        net_pnl=format_number(net_pnl),
        remarks=remarks,
    )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, spot_rows_by_day, timestamps_by_day = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    contract_cache: Dict[Path, ContractData] = {}
    results: List[TradeResult] = []
    contract_multiplier = args.lot_size * args.lots

    try:
        try:
            for day_index, entry_date in enumerate(trading_days):
                gap_timestamp = build_timestamp(entry_date, args.gap_time)
                entry_timestamp = build_timestamp(entry_date, args.entry_time)
                exit_timestamp = build_timestamp(entry_date, args.exit_time)
                previous_close = previous_close_for_day(
                    trading_days=trading_days,
                    spot_rows_by_day=spot_rows_by_day,
                    timestamps_by_day=timestamps_by_day,
                    day_index=day_index,
                )

                if previous_close is None:
                    result = make_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="no_previous_close",
                        expiry_date="",
                        previous_trading_day="",
                        previous_close_timestamp="",
                        previous_close="",
                        gap_timestamp=gap_timestamp,
                        gap_open="",
                        gap_points="",
                        gap_percent="",
                        entry_timestamp=entry_timestamp,
                        spot_entry_open="",
                        exit_timestamp=exit_timestamp,
                        atm_strike="",
                        option_side="",
                        contract_file="",
                        option_entry_open="",
                        option_exit_open="",
                        raw_points_pnl=0.0,
                        slippage_points=0.0,
                        brokerage=0.0,
                        contract_multiplier=contract_multiplier,
                        remarks="No previous trading day close exists in the dataset.",
                    )
                    results.append(result)
                    logger.info("SKIPPED date=%s reason=no_previous_close", entry_date)
                    continue

                previous_day, previous_close_row = previous_close
                spot_rows = spot_rows_by_day[entry_date]
                gap_row = spot_rows.get(gap_timestamp)
                entry_spot_row = spot_rows.get(entry_timestamp)
                missing_spot_parts: List[str] = []
                if gap_row is None:
                    missing_spot_parts.append(f"Missing spot gap timestamp {gap_timestamp}")
                if entry_spot_row is None:
                    missing_spot_parts.append(f"Missing spot entry timestamp {entry_timestamp}")
                if exit_timestamp not in spot_rows:
                    missing_spot_parts.append(f"Missing spot exit timestamp {exit_timestamp}")
                if missing_spot_parts:
                    result = make_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="missing_spot_timestamp",
                        expiry_date="",
                        previous_trading_day=previous_day,
                        previous_close_timestamp=previous_close_row.timestamp,
                        previous_close=previous_close_row.close_text,
                        gap_timestamp=gap_timestamp,
                        gap_open=gap_row.open_text if gap_row else "",
                        gap_points="",
                        gap_percent="",
                        entry_timestamp=entry_timestamp,
                        spot_entry_open=entry_spot_row.open_text if entry_spot_row else "",
                        exit_timestamp=exit_timestamp,
                        atm_strike="",
                        option_side="",
                        contract_file="",
                        option_entry_open="",
                        option_exit_open="",
                        raw_points_pnl=0.0,
                        slippage_points=0.0,
                        brokerage=0.0,
                        contract_multiplier=contract_multiplier,
                        remarks="; ".join(missing_spot_parts),
                    )
                    results.append(result)
                    logger.info("SKIPPED date=%s reason=missing_spot_timestamp", entry_date)
                    continue

                assert gap_row is not None
                assert entry_spot_row is not None
                gap_points_value = gap_row.open_value - previous_close_row.close_value
                gap_percent_value = (
                    (gap_points_value / previous_close_row.close_value) * 100
                    if previous_close_row.close_value
                    else 0.0
                )
                gap_points = format_number(gap_points_value)
                gap_percent = format_number(gap_percent_value)
                option_side = option_side_from_gap(gap_points_value, args.gap_threshold_points)

                if not option_side:
                    result = make_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="gap_below_threshold",
                        expiry_date="",
                        previous_trading_day=previous_day,
                        previous_close_timestamp=previous_close_row.timestamp,
                        previous_close=previous_close_row.close_text,
                        gap_timestamp=gap_timestamp,
                        gap_open=gap_row.open_text,
                        gap_points=gap_points,
                        gap_percent=gap_percent,
                        entry_timestamp=entry_timestamp,
                        spot_entry_open=entry_spot_row.open_text,
                        exit_timestamp=exit_timestamp,
                        atm_strike="",
                        option_side="",
                        contract_file="",
                        option_entry_open="",
                        option_exit_open="",
                        raw_points_pnl=0.0,
                        slippage_points=0.0,
                        brokerage=0.0,
                        contract_multiplier=contract_multiplier,
                        remarks=f"Absolute gap {abs(gap_points_value):.2f} is below {args.gap_threshold_points:.2f} points.",
                    )
                    results.append(result)
                    logger.info("SKIPPED date=%s reason=gap_below_threshold gap=%s", entry_date, gap_points)
                    continue

                expiry_date = first_expiry_on_or_after(expiries, entry_date)
                if expiry_date is None:
                    result = make_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="no_same_week_expiry",
                        expiry_date="",
                        previous_trading_day=previous_day,
                        previous_close_timestamp=previous_close_row.timestamp,
                        previous_close=previous_close_row.close_text,
                        gap_timestamp=gap_timestamp,
                        gap_open=gap_row.open_text,
                        gap_points=gap_points,
                        gap_percent=gap_percent,
                        entry_timestamp=entry_timestamp,
                        spot_entry_open=entry_spot_row.open_text,
                        exit_timestamp=exit_timestamp,
                        atm_strike="",
                        option_side=option_side,
                        contract_file="",
                        option_entry_open="",
                        option_exit_open="",
                        raw_points_pnl=0.0,
                        slippage_points=0.0,
                        brokerage=0.0,
                        contract_multiplier=contract_multiplier,
                        remarks="No expiry folder exists on or after this trade date.",
                    )
                    results.append(result)
                    logger.info("SKIPPED date=%s reason=no_same_week_expiry", entry_date)
                    continue

                atm_strike = round_to_nearest_50(entry_spot_row.open_value)
                strike_text = str(atm_strike)
                option_suffix = expiry_suffix(expiry_date)
                contract_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_{option_side}_{option_suffix}.csv"
                contract_data = load_contract(contract_path, contract_cache)
                if contract_data is None:
                    result = make_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="missing_option_file",
                        expiry_date=expiry_date,
                        previous_trading_day=previous_day,
                        previous_close_timestamp=previous_close_row.timestamp,
                        previous_close=previous_close_row.close_text,
                        gap_timestamp=gap_timestamp,
                        gap_open=gap_row.open_text,
                        gap_points=gap_points,
                        gap_percent=gap_percent,
                        entry_timestamp=entry_timestamp,
                        spot_entry_open=entry_spot_row.open_text,
                        exit_timestamp=exit_timestamp,
                        atm_strike=strike_text,
                        option_side=option_side,
                        contract_file=contract_path.name,
                        option_entry_open="",
                        option_exit_open="",
                        raw_points_pnl=0.0,
                        slippage_points=0.0,
                        brokerage=0.0,
                        contract_multiplier=contract_multiplier,
                        remarks=f"Missing option file: {contract_path.name}",
                    )
                    results.append(result)
                    logger.info("SKIPPED date=%s reason=missing_option_file", entry_date)
                    continue

                option_entry_row = contract_data.rows_by_timestamp.get(entry_timestamp)
                option_exit_row = contract_data.rows_by_timestamp.get(exit_timestamp)
                missing_option_parts: List[str] = []
                if option_entry_row is None:
                    missing_option_parts.append(f"{contract_path.name} missing entry timestamp {entry_timestamp}")
                if option_exit_row is None:
                    missing_option_parts.append(f"{contract_path.name} missing exit timestamp {exit_timestamp}")
                if missing_option_parts:
                    result = make_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="missing_option_timestamp",
                        expiry_date=expiry_date,
                        previous_trading_day=previous_day,
                        previous_close_timestamp=previous_close_row.timestamp,
                        previous_close=previous_close_row.close_text,
                        gap_timestamp=gap_timestamp,
                        gap_open=gap_row.open_text,
                        gap_points=gap_points,
                        gap_percent=gap_percent,
                        entry_timestamp=entry_timestamp,
                        spot_entry_open=entry_spot_row.open_text,
                        exit_timestamp=exit_timestamp,
                        atm_strike=strike_text,
                        option_side=option_side,
                        contract_file=contract_path.name,
                        option_entry_open=option_entry_row.open_text if option_entry_row else "",
                        option_exit_open=option_exit_row.open_text if option_exit_row else "",
                        raw_points_pnl=0.0,
                        slippage_points=0.0,
                        brokerage=0.0,
                        contract_multiplier=contract_multiplier,
                        remarks="; ".join(missing_option_parts),
                    )
                    results.append(result)
                    logger.info("SKIPPED date=%s reason=missing_option_timestamp", entry_date)
                    continue

                assert option_entry_row is not None
                assert option_exit_row is not None
                raw_points_pnl = option_exit_row.open_value - option_entry_row.open_value
                slippage_points = 2 * args.slippage_points_per_order
                brokerage = 2 * args.brokerage_per_order
                result = make_result(
                    entry_date=entry_date,
                    status="TRADED",
                    skip_reason="",
                    expiry_date=expiry_date,
                    previous_trading_day=previous_day,
                    previous_close_timestamp=previous_close_row.timestamp,
                    previous_close=previous_close_row.close_text,
                    gap_timestamp=gap_timestamp,
                    gap_open=gap_row.open_text,
                    gap_points=gap_points,
                    gap_percent=gap_percent,
                    entry_timestamp=entry_timestamp,
                    spot_entry_open=entry_spot_row.open_text,
                    exit_timestamp=exit_timestamp,
                    atm_strike=strike_text,
                    option_side=option_side,
                    contract_file=contract_path.name,
                    option_entry_open=option_entry_row.open_text,
                    option_exit_open=option_exit_row.open_text,
                    raw_points_pnl=raw_points_pnl,
                    slippage_points=slippage_points,
                    brokerage=brokerage,
                    contract_multiplier=contract_multiplier,
                    remarks="",
                )
                results.append(result)
                logger.info(
                    "TRADED date=%s side=%s expiry=%s strike=%s raw=%s slippage=%s brokerage=%s net=%s",
                    entry_date,
                    option_side,
                    expiry_date,
                    strike_text,
                    result.raw_gross_pnl,
                    result.slippage_loss,
                    result.brokerage,
                    result.net_pnl,
                )
        except Exception:
            logger.exception("ERROR unexpected failure while running the backtest")
            raise

        traded_count = sum(1 for result in results if result.status == "TRADED")
        skipped_count = sum(1 for result in results if result.status == "SKIPPED")
        logger.info("COMPLETED traded=%s skipped=%s total=%s", traded_count, skipped_count, len(results))
        return results
    finally:
        close_logger(logger)


def trade_rows_from_results(results: List[TradeResult]) -> List[TradeRow]:
    trade_rows: List[TradeRow] = []
    for result in results:
        if result.status != "TRADED":
            continue
        trade_rows.append(
            TradeRow(
                entry_date=result.entry_date,
                status=result.status,
                expiry_date=result.expiry_date,
                previous_trading_day=result.previous_trading_day,
                previous_close=result.previous_close,
                gap_timestamp=result.gap_timestamp,
                gap_open=result.gap_open,
                gap_points=result.gap_points,
                entry_timestamp=result.entry_timestamp,
                spot_entry_open=result.spot_entry_open,
                exit_timestamp=result.exit_timestamp,
                atm_strike=result.atm_strike,
                option_side=result.option_side,
                contract_file=result.contract_file,
                option_entry_open=result.option_entry_open,
                option_exit_open=result.option_exit_open,
                raw_points_pnl=result.raw_points_pnl,
                raw_gross_pnl=result.raw_gross_pnl,
                slippage_points=result.slippage_points,
                slippage_loss=result.slippage_loss,
                brokerage=result.brokerage,
                net_pnl=result.net_pnl,
                remarks=result.remarks,
            )
        )
    return trade_rows


def write_daywise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "skip_reason",
        "expiry_date",
        "previous_trading_day",
        "previous_close_timestamp",
        "previous_close",
        "gap_timestamp",
        "gap_open",
        "gap_points",
        "gap_percent",
        "entry_timestamp",
        "spot_entry_open",
        "exit_timestamp",
        "atm_strike",
        "option_side",
        "contract_file",
        "option_entry_open",
        "option_exit_open",
        "raw_points_pnl",
        "raw_gross_pnl",
        "slippage_points",
        "slippage_loss",
        "brokerage",
        "net_pnl",
        "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)


def write_trades_csv(trade_rows: List[TradeRow], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "expiry_date",
        "previous_trading_day",
        "previous_close",
        "gap_timestamp",
        "gap_open",
        "gap_points",
        "entry_timestamp",
        "spot_entry_open",
        "exit_timestamp",
        "atm_strike",
        "option_side",
        "contract_file",
        "option_entry_open",
        "option_exit_open",
        "raw_points_pnl",
        "raw_gross_pnl",
        "slippage_points",
        "slippage_loss",
        "brokerage",
        "net_pnl",
        "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in trade_rows:
            writer.writerow(row.__dict__)


def write_summary(results: List[TradeResult], output_path: Path, args: argparse.Namespace) -> None:
    traded_results = [result for result in results if result.status == "TRADED"]
    skipped_results = [result for result in results if result.status == "SKIPPED"]
    ce_count = sum(1 for result in traded_results if result.option_side == "CE")
    pe_count = sum(1 for result in traded_results if result.option_side == "PE")
    winning_trades = sum(1 for result in traded_results if float(result.net_pnl) > 0)
    losing_trades = sum(1 for result in traded_results if float(result.net_pnl) < 0)
    raw_total = sum(float(result.raw_gross_pnl) for result in traded_results)
    slippage_total = sum(float(result.slippage_loss) for result in traded_results)
    brokerage_total = sum(float(result.brokerage) for result in traded_results)
    net_total = sum(float(result.net_pnl) for result in traded_results)
    max_profit_trade = max(traded_results, key=lambda result: float(result.net_pnl), default=None)
    max_loss_trade = min(traded_results, key=lambda result: float(result.net_pnl), default=None)

    lines: List[str] = [
        "# 2025 100-Point Gap ATM Option 09:16 Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Gap check time: `{args.gap_time}`",
        f"- Entry time: `{args.entry_time}` option open",
        f"- Exit time: `{args.exit_time}` option open",
        "- Gap rule: compare NIFTY gap-time open with the previous trading day's last close",
        f"- Gap-up rule: if gap is at least `{format_number(args.gap_threshold_points)}` points, buy ATM CE",
        f"- Gap-down rule: if gap is at most `-{format_number(args.gap_threshold_points)}` points, buy ATM PE",
        "- Non-qualifying gap days are skipped",
        "- ATM rule: nearest 50 using NIFTY entry-time open",
        "- Expiry rule: first expiry folder on or after the trade date",
        "- Pricing rule: option open at exact entry and exit timestamps",
        f"- Contract multiplier: {args.lot_size} x {args.lots} = {args.lot_size * args.lots} rupees per option point",
        (
            f"- Slippage: {format_number(args.slippage_points_per_order)} point per order, "
            f"{format_number(args.slippage_points_per_order * 2)} points per trade round trip"
        ),
        (
            f"- Brokerage: Rs {format_number(args.brokerage_per_order)} per order, "
            f"Rs {format_number(args.brokerage_per_order * 2)} per completed trade"
        ),
        "",
        "## Results Summary",
        "",
        f"- Total traded days: `{len(traded_results)}`",
        f"- Total skipped days: `{len(skipped_results)}`",
        f"- CE trades: `{ce_count}`",
        f"- PE trades: `{pe_count}`",
        f"- Winning trades: `{winning_trades}`",
        f"- Losing trades: `{losing_trades}`",
        f"- Raw Profit/Loss before costs: `{format_number(raw_total)}`",
        f"- Slippage loss: `{format_number(slippage_total)}`",
        f"- Brokerage: `{format_number(brokerage_total)}`",
        f"- Net Profit/Loss: `{format_number(net_total)}`",
        (
            f"- Max profit trade: `{max_profit_trade.entry_date}` `{max_profit_trade.option_side}` "
            f"with net P/L `{max_profit_trade.net_pnl}`"
            if max_profit_trade
            else "- Max profit trade: `N/A`"
        ),
        (
            f"- Max loss trade: `{max_loss_trade.entry_date}` `{max_loss_trade.option_side}` "
            f"with net P/L `{max_loss_trade.net_pnl}`"
            if max_loss_trade
            else "- Max loss trade: `N/A`"
        ),
        "",
        "## Output Files",
        "",
        f"- Daywise file: `{DAYWISE_FILENAME}`",
        f"- Trades file: `{TRADES_FILENAME}`",
        f"- Log file: `{LOG_FILENAME}`",
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
            "- The NIFTY spot file is the source of truth for trading days and previous-close detection.",
            "- Raw 1-minute option candles from `Options_2025` are used directly.",
            "- Slippage and brokerage are reported separately and deducted from net P/L.",
            "- Expiry folder dates are used as truth, which naturally handles non-Thursday expiry weeks.",
        ]
    )

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    results = run_backtest(args)
    trade_rows = trade_rows_from_results(results)
    write_daywise_csv(results, args.results_dir / DAYWISE_FILENAME)
    write_trades_csv(trade_rows, args.results_dir / TRADES_FILENAME)
    write_summary(results, args.results_dir / SUMMARY_FILENAME, args)


if __name__ == "__main__":
    main()
