#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


IST_SUFFIX = "+05:30"
BASE_FILENAME = "weekly_short_strangle_0920_2025"
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
class OptionCandidate:
    side: str
    strike: int
    contract: ContractData
    entry_row: PriceRow
    premium_gap: float
    strike_distance: int


@dataclass
class LegResolution:
    side: str
    strike: str
    contract_file: str
    entry_timestamp: str
    entry_price: str
    stop_price: str
    target_price: str
    exit_timestamp: str
    exit_price: str
    exit_reason: str
    points_pnl: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    failure_reason: str
    remarks: str


@dataclass
class DayResult:
    entry_date: str
    status: str
    skip_reason: str
    expiry_date: str
    spot_entry_timestamp: str
    spot_entry_open: str
    exit_timestamp: str
    atm_strike: str
    ce_strike: str
    ce_contract_file: str
    ce_entry_timestamp: str
    ce_entry_open: str
    ce_stop_price: str
    ce_target_price: str
    ce_exit_timestamp: str
    ce_exit_price: str
    ce_exit_reason: str
    ce_points_pnl: str
    ce_gross_pnl: str
    ce_brokerage: str
    ce_net_pnl: str
    pe_strike: str
    pe_contract_file: str
    pe_entry_timestamp: str
    pe_entry_open: str
    pe_stop_price: str
    pe_target_price: str
    pe_exit_timestamp: str
    pe_exit_price: str
    pe_exit_reason: str
    pe_points_pnl: str
    pe_gross_pnl: str
    pe_brokerage: str
    pe_net_pnl: str
    orders_executed: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


@dataclass
class TradeRow:
    entry_date: str
    status: str
    expiry_date: str
    side: str
    strike: str
    contract_file: str
    spot_entry_timestamp: str
    spot_entry_open: str
    atm_strike: str
    entry_timestamp: str
    entry_price: str
    stop_price: str
    target_price: str
    exit_timestamp: str
    exit_price: str
    exit_reason: str
    points_pnl: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Backtest a 2025 intraday weekly short strangle from 09:20 to 15:20.",
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
    parser.add_argument("--entry-time", default="09:20")
    parser.add_argument("--exit-time", default="15:20")
    parser.add_argument("--sell-min-premium", type=float, default=20.0)
    parser.add_argument("--sell-max-premium", type=float, default=30.0)
    parser.add_argument("--sell-target-premium", type=float, default=25.0)
    parser.add_argument("--stop-loss-multiple", type=float, default=2.0)
    parser.add_argument("--target-premium", type=float, default=10.0)
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--lot-size", type=int, default=65)
    parser.add_argument("--lots", type=int, default=4)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
    args = parser.parse_args()

    if args.sell_min_premium <= 0:
        parser.error("--sell-min-premium must be positive")
    if args.sell_max_premium < args.sell_min_premium:
        parser.error("--sell-max-premium must be greater than or equal to --sell-min-premium")
    if not (args.sell_min_premium <= args.sell_target_premium <= args.sell_max_premium):
        parser.error("--sell-target-premium must sit inside the sell premium band")
    if args.stop_loss_multiple <= 1:
        parser.error("--stop-loss-multiple must be greater than 1")
    if args.target_premium < 0:
        parser.error("--target-premium cannot be negative")
    if args.target_premium >= args.sell_min_premium:
        parser.error("--target-premium must be below --sell-min-premium for a short option target")
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


def join_remarks(parts: List[str]) -> str:
    return "; ".join(part for part in parts if part)


def short_leg_points_pnl(
    entry_price: float,
    exit_price: float,
    slippage_points_per_order: float,
) -> float:
    return entry_price - exit_price - (2 * slippage_points_per_order)


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
) -> Tuple[List[str], Dict[str, Dict[str, PriceRow]], Dict[str, List[str]]]:
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


def index_option_strikes(options_dir: Path, expiries: List[str]) -> Dict[Tuple[str, str], List[int]]:
    indexed: Dict[Tuple[str, str], List[int]] = {}
    pattern = re.compile(r"^NIFTY_(\d+)_(CE|PE)_[A-Z0-9_]+\.csv$")
    for expiry in expiries:
        ce_strikes: List[int] = []
        pe_strikes: List[int] = []
        for contract_path in (options_dir / expiry).iterdir():
            if not contract_path.is_file():
                continue
            match = pattern.match(contract_path.name)
            if not match:
                continue
            strike = int(match.group(1))
            side = match.group(2)
            if side == "CE":
                ce_strikes.append(strike)
            else:
                pe_strikes.append(strike)
        indexed[(expiry, "CE")] = sorted(ce_strikes)
        indexed[(expiry, "PE")] = sorted(pe_strikes)
    return indexed


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


def load_contract_row(
    contract_path: Path,
    timestamp: str,
    cache: Dict[Tuple[Path, str], Optional[PriceRow]],
) -> Optional[PriceRow]:
    key = (contract_path, timestamp)
    if key in cache:
        return cache[key]
    if not contract_path.exists():
        cache[key] = None
        return None

    with contract_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_timestamp = row["timestamp"]
            if row_timestamp == timestamp:
                price_row = price_row_from_csv(row)
                cache[key] = price_row
                return price_row
            if row_timestamp > timestamp:
                break

    cache[key] = None
    return None


def candidate_strikes_for_side(strikes: List[int], side: str, reference_strike: int) -> List[int]:
    if side == "CE":
        return [strike for strike in strikes if strike > reference_strike]
    return [strike for strike in reversed(strikes) if strike < reference_strike]


def select_short_candidate(
    expiry_date: str,
    side: str,
    reference_strike: int,
    entry_timestamp: str,
    options_dir: Path,
    contract_cache: Dict[Path, ContractData],
    entry_row_cache: Dict[Tuple[Path, str], Optional[PriceRow]],
    strike_index: Dict[Tuple[str, str], List[int]],
    min_premium: float,
    max_premium: float,
    target_premium: float,
) -> Tuple[Optional[OptionCandidate], str]:
    suffix = expiry_suffix(expiry_date)
    strikes = strike_index.get((expiry_date, side), [])
    candidate_strikes = candidate_strikes_for_side(strikes, side, reference_strike)
    if not candidate_strikes:
        return None, f"No OTM {side} contracts were found beyond strike {reference_strike}."

    best_candidate: Optional[OptionCandidate] = None
    best_contract_path: Optional[Path] = None
    best_entry_row: Optional[PriceRow] = None
    best_key: Optional[Tuple[float, int, int]] = None
    for strike in candidate_strikes:
        contract_path = options_dir / expiry_date / f"NIFTY_{strike}_{side}_{suffix}.csv"
        entry_row = load_contract_row(contract_path, entry_timestamp, entry_row_cache)
        if entry_row is None:
            continue
        if not (min_premium <= entry_row.open_value <= max_premium):
            continue

        tie_break = strike if side == "CE" else -strike
        candidate_key = (
            abs(entry_row.open_value - target_premium),
            abs(strike - reference_strike),
            tie_break,
        )
        if best_key is None or candidate_key < best_key:
            best_candidate = None
            best_contract_path = contract_path
            best_entry_row = entry_row
            best_key = candidate_key

    if best_contract_path is not None and best_entry_row is not None and best_key is not None:
        contract_data = load_contract(best_contract_path, contract_cache)
        if contract_data is None:
            return None, f"Missing selected {side} option file: {best_contract_path.name}"
        best_candidate = OptionCandidate(
            side=side,
            strike=int(best_contract_path.name.split("_")[1]),
            contract=contract_data,
            entry_row=best_entry_row,
            premium_gap=best_key[0],
            strike_distance=best_key[1],
        )
        return best_candidate, ""
    return (
        None,
        (
            f"No OTM {side} contract satisfied the sell premium band "
            f"{format_number(min_premium)}-{format_number(max_premium)} at {entry_timestamp}."
        ),
    )


def empty_leg(side: str, strike: str = "", contract_file: str = "", remarks: str = "") -> LegResolution:
    return LegResolution(
        side=side,
        strike=strike,
        contract_file=contract_file,
        entry_timestamp="",
        entry_price="",
        stop_price="",
        target_price="",
        exit_timestamp="",
        exit_price="",
        exit_reason="",
        points_pnl="0.00",
        gross_pnl="0.00",
        brokerage="0.00",
        net_pnl="0.00",
        failure_reason="",
        remarks=remarks,
    )


def build_successful_leg(
    candidate: OptionCandidate,
    stop_price: float,
    target_price: float,
    exit_timestamp: str,
    exit_price: float,
    exit_price_text: str,
    exit_reason: str,
    slippage_points_per_order: float,
    contract_multiplier: int,
    brokerage_per_order: float,
    remarks: str,
) -> LegResolution:
    points_pnl = short_leg_points_pnl(
        entry_price=candidate.entry_row.open_value,
        exit_price=exit_price,
        slippage_points_per_order=slippage_points_per_order,
    )
    gross_pnl = points_pnl * contract_multiplier
    brokerage = brokerage_per_order * 2
    net_pnl = gross_pnl - brokerage
    return LegResolution(
        side=candidate.side,
        strike=str(candidate.strike),
        contract_file=candidate.contract.path.name,
        entry_timestamp=candidate.entry_row.timestamp,
        entry_price=candidate.entry_row.open_text,
        stop_price=format_number(stop_price),
        target_price=format_number(target_price),
        exit_timestamp=exit_timestamp,
        exit_price=exit_price_text,
        exit_reason=exit_reason,
        points_pnl=format_number(points_pnl),
        gross_pnl=format_number(gross_pnl),
        brokerage=format_number(brokerage),
        net_pnl=format_number(net_pnl),
        failure_reason="",
        remarks=remarks,
    )


def resolve_leg(
    candidate: OptionCandidate,
    day_timestamps: List[str],
    entry_timestamp: str,
    exit_timestamp: str,
    stop_loss_multiple: float,
    target_price: float,
    slippage_points_per_order: float,
    contract_multiplier: int,
    brokerage_per_order: float,
) -> LegResolution:
    entry_row = candidate.contract.rows_by_timestamp.get(entry_timestamp)
    if entry_row is None:
        remarks = (
            f"{candidate.contract.path.name} is header-only"
            if not candidate.contract.rows_by_timestamp
            else f"{candidate.contract.path.name} missing entry timestamp {entry_timestamp}"
        )
        return LegResolution(
            side=candidate.side,
            strike=str(candidate.strike),
            contract_file=candidate.contract.path.name,
            entry_timestamp="",
            entry_price="",
            stop_price="",
            target_price="",
            exit_timestamp="",
            exit_price="",
            exit_reason="",
            points_pnl="0.00",
            gross_pnl="0.00",
            brokerage="0.00",
            net_pnl="0.00",
            failure_reason="missing_entry_timestamp",
            remarks=remarks,
        )

    entry_index = day_timestamps.index(entry_timestamp)
    exit_index = day_timestamps.index(exit_timestamp)
    stop_price = entry_row.open_value * stop_loss_multiple

    for timestamp in day_timestamps[entry_index:exit_index]:
        row = candidate.contract.rows_by_timestamp.get(timestamp)
        if row is None:
            return LegResolution(
                side=candidate.side,
                strike=str(candidate.strike),
                contract_file=candidate.contract.path.name,
                entry_timestamp=entry_row.timestamp,
                entry_price=entry_row.open_text,
                stop_price=format_number(stop_price),
                target_price=format_number(target_price),
                exit_timestamp="",
                exit_price="",
                exit_reason="",
                points_pnl="0.00",
                gross_pnl="0.00",
                brokerage="0.00",
                net_pnl="0.00",
                failure_reason="missing_monitoring_timestamp",
                remarks=f"{candidate.contract.path.name} missing monitoring timestamp {timestamp}",
            )

        if row.open_value >= stop_price:
            return build_successful_leg(
                candidate=candidate,
                stop_price=stop_price,
                target_price=target_price,
                exit_timestamp=row.timestamp,
                exit_price=row.open_value,
                exit_price_text=row.open_text,
                exit_reason="gap_stop_loss",
                slippage_points_per_order=slippage_points_per_order,
                contract_multiplier=contract_multiplier,
                brokerage_per_order=brokerage_per_order,
                remarks=f"Stop {format_number(stop_price)} crossed by candle open {row.open_text}.",
            )

        if row.open_value <= target_price:
            return build_successful_leg(
                candidate=candidate,
                stop_price=stop_price,
                target_price=target_price,
                exit_timestamp=row.timestamp,
                exit_price=row.open_value,
                exit_price_text=row.open_text,
                exit_reason="gap_target",
                slippage_points_per_order=slippage_points_per_order,
                contract_multiplier=contract_multiplier,
                brokerage_per_order=brokerage_per_order,
                remarks=f"Target {format_number(target_price)} crossed by candle open {row.open_text}.",
            )

        stop_hit = row.high_value >= stop_price
        target_hit = row.low_value <= target_price
        if stop_hit:
            remarks = (
                "Stop and target were both touched in the same candle; stop-first fill used."
                if target_hit
                else ""
            )
            return build_successful_leg(
                candidate=candidate,
                stop_price=stop_price,
                target_price=target_price,
                exit_timestamp=row.timestamp,
                exit_price=stop_price,
                exit_price_text=format_number(stop_price),
                exit_reason="stop_loss",
                slippage_points_per_order=slippage_points_per_order,
                contract_multiplier=contract_multiplier,
                brokerage_per_order=brokerage_per_order,
                remarks=remarks,
            )

        if target_hit:
            return build_successful_leg(
                candidate=candidate,
                stop_price=stop_price,
                target_price=target_price,
                exit_timestamp=row.timestamp,
                exit_price=target_price,
                exit_price_text=format_number(target_price),
                exit_reason="target",
                slippage_points_per_order=slippage_points_per_order,
                contract_multiplier=contract_multiplier,
                brokerage_per_order=brokerage_per_order,
                remarks="",
            )

    exit_row = candidate.contract.rows_by_timestamp.get(exit_timestamp)
    if exit_row is None:
        return LegResolution(
            side=candidate.side,
            strike=str(candidate.strike),
            contract_file=candidate.contract.path.name,
            entry_timestamp=entry_row.timestamp,
            entry_price=entry_row.open_text,
            stop_price=format_number(stop_price),
            target_price=format_number(target_price),
            exit_timestamp="",
            exit_price="",
            exit_reason="",
            points_pnl="0.00",
            gross_pnl="0.00",
            brokerage="0.00",
            net_pnl="0.00",
            failure_reason="missing_exit_timestamp",
            remarks=f"{candidate.contract.path.name} missing scheduled exit timestamp {exit_timestamp}",
        )

    return build_successful_leg(
        candidate=candidate,
        stop_price=stop_price,
        target_price=target_price,
        exit_timestamp=exit_row.timestamp,
        exit_price=exit_row.open_value,
        exit_price_text=exit_row.open_text,
        exit_reason="day_close",
        slippage_points_per_order=slippage_points_per_order,
        contract_multiplier=contract_multiplier,
        brokerage_per_order=brokerage_per_order,
        remarks="",
    )


def make_day_result(
    entry_date: str,
    status: str,
    skip_reason: str,
    expiry_date: str,
    spot_entry_timestamp: str,
    spot_entry_open: str,
    exit_timestamp: str,
    atm_strike: str,
    ce_leg: LegResolution,
    pe_leg: LegResolution,
    remarks: str,
) -> DayResult:
    traded_legs = [leg for leg in (ce_leg, pe_leg) if leg.entry_timestamp and leg.exit_timestamp]
    orders_executed = 2 * len(traded_legs) if status == "TRADED" else 0
    gross_pnl = sum(float(leg.gross_pnl) for leg in traded_legs) if status == "TRADED" else 0.0
    brokerage = sum(float(leg.brokerage) for leg in traded_legs) if status == "TRADED" else 0.0
    net_pnl = gross_pnl - brokerage

    return DayResult(
        entry_date=entry_date,
        status=status,
        skip_reason=skip_reason,
        expiry_date=expiry_date,
        spot_entry_timestamp=spot_entry_timestamp,
        spot_entry_open=spot_entry_open,
        exit_timestamp=exit_timestamp,
        atm_strike=atm_strike,
        ce_strike=ce_leg.strike,
        ce_contract_file=ce_leg.contract_file,
        ce_entry_timestamp=ce_leg.entry_timestamp,
        ce_entry_open=ce_leg.entry_price,
        ce_stop_price=ce_leg.stop_price,
        ce_target_price=ce_leg.target_price,
        ce_exit_timestamp=ce_leg.exit_timestamp,
        ce_exit_price=ce_leg.exit_price,
        ce_exit_reason=ce_leg.exit_reason,
        ce_points_pnl=ce_leg.points_pnl if status == "TRADED" else "0.00",
        ce_gross_pnl=ce_leg.gross_pnl if status == "TRADED" else "0.00",
        ce_brokerage=ce_leg.brokerage if status == "TRADED" else "0.00",
        ce_net_pnl=ce_leg.net_pnl if status == "TRADED" else "0.00",
        pe_strike=pe_leg.strike,
        pe_contract_file=pe_leg.contract_file,
        pe_entry_timestamp=pe_leg.entry_timestamp,
        pe_entry_open=pe_leg.entry_price,
        pe_stop_price=pe_leg.stop_price,
        pe_target_price=pe_leg.target_price,
        pe_exit_timestamp=pe_leg.exit_timestamp,
        pe_exit_price=pe_leg.exit_price,
        pe_exit_reason=pe_leg.exit_reason,
        pe_points_pnl=pe_leg.points_pnl if status == "TRADED" else "0.00",
        pe_gross_pnl=pe_leg.gross_pnl if status == "TRADED" else "0.00",
        pe_brokerage=pe_leg.brokerage if status == "TRADED" else "0.00",
        pe_net_pnl=pe_leg.net_pnl if status == "TRADED" else "0.00",
        orders_executed=str(orders_executed),
        gross_pnl=format_number(gross_pnl),
        brokerage=format_number(brokerage),
        net_pnl=format_number(net_pnl),
        remarks=remarks,
    )


def validate_intraday_window(
    day_timestamps: List[str],
    entry_timestamp: str,
    exit_timestamp: str,
) -> Optional[str]:
    if entry_timestamp not in day_timestamps:
        return f"Missing spot entry timestamp {entry_timestamp}"
    if exit_timestamp not in day_timestamps:
        return f"Missing spot exit timestamp {exit_timestamp}"
    if day_timestamps.index(entry_timestamp) >= day_timestamps.index(exit_timestamp):
        return f"Entry timestamp {entry_timestamp} must be before exit timestamp {exit_timestamp}"
    return None


def run_backtest(args: argparse.Namespace) -> List[DayResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, spot_rows_by_day, timestamps_by_day = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    strike_index = index_option_strikes(args.options_dir, expiries)
    contract_cache: Dict[Path, ContractData] = {}
    entry_row_cache: Dict[Tuple[Path, str], Optional[PriceRow]] = {}
    cached_expiry = ""
    results: List[DayResult] = []
    contract_multiplier = args.lot_size * args.lots

    try:
        try:
            for entry_date in trading_days:
                entry_timestamp = build_timestamp(entry_date, args.entry_time)
                exit_timestamp = build_timestamp(entry_date, args.exit_time)
                day_timestamps = timestamps_by_day[entry_date]
                window_error = validate_intraday_window(day_timestamps, entry_timestamp, exit_timestamp)
                if window_error:
                    result = make_day_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="missing_spot_timestamp",
                        expiry_date="",
                        spot_entry_timestamp=entry_timestamp,
                        spot_entry_open="",
                        exit_timestamp=exit_timestamp,
                        atm_strike="",
                        ce_leg=empty_leg("CE"),
                        pe_leg=empty_leg("PE"),
                        remarks=window_error,
                    )
                    results.append(result)
                    logger.info("SKIPPED date=%s reason=%s", entry_date, window_error)
                    continue

                spot_entry_row = spot_rows_by_day[entry_date][entry_timestamp]
                expiry_date = first_expiry_on_or_after(expiries, entry_date)
                if expiry_date is None:
                    result = make_day_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="no_same_week_expiry",
                        expiry_date="",
                        spot_entry_timestamp=entry_timestamp,
                        spot_entry_open=spot_entry_row.open_text,
                        exit_timestamp=exit_timestamp,
                        atm_strike="",
                        ce_leg=empty_leg("CE"),
                        pe_leg=empty_leg("PE"),
                        remarks="No expiry folder exists on or after this trade date.",
                    )
                    results.append(result)
                    logger.info("SKIPPED date=%s reason=no_same_week_expiry", entry_date)
                    continue

                if expiry_date != cached_expiry:
                    contract_cache.clear()
                    entry_row_cache.clear()
                    cached_expiry = expiry_date

                atm_strike = round_to_nearest_50(spot_entry_row.open_value)
                strike_text = str(atm_strike)
                ce_candidate, ce_error = select_short_candidate(
                    expiry_date=expiry_date,
                    side="CE",
                    reference_strike=atm_strike,
                    entry_timestamp=entry_timestamp,
                    options_dir=args.options_dir,
                    contract_cache=contract_cache,
                    entry_row_cache=entry_row_cache,
                    strike_index=strike_index,
                    min_premium=args.sell_min_premium,
                    max_premium=args.sell_max_premium,
                    target_premium=args.sell_target_premium,
                )
                pe_candidate, pe_error = select_short_candidate(
                    expiry_date=expiry_date,
                    side="PE",
                    reference_strike=atm_strike,
                    entry_timestamp=entry_timestamp,
                    options_dir=args.options_dir,
                    contract_cache=contract_cache,
                    entry_row_cache=entry_row_cache,
                    strike_index=strike_index,
                    min_premium=args.sell_min_premium,
                    max_premium=args.sell_max_premium,
                    target_premium=args.sell_target_premium,
                )
                if ce_candidate is None or pe_candidate is None:
                    result = make_day_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="no_valid_strangle_in_premium_band",
                        expiry_date=expiry_date,
                        spot_entry_timestamp=entry_timestamp,
                        spot_entry_open=spot_entry_row.open_text,
                        exit_timestamp=exit_timestamp,
                        atm_strike=strike_text,
                        ce_leg=empty_leg("CE", remarks=ce_error),
                        pe_leg=empty_leg("PE", remarks=pe_error),
                        remarks=join_remarks([ce_error, pe_error]),
                    )
                    results.append(result)
                    logger.info(
                        "SKIPPED date=%s expiry=%s strike=%s reason=%s",
                        entry_date,
                        expiry_date,
                        strike_text,
                        result.remarks,
                    )
                    continue

                ce_leg = resolve_leg(
                    candidate=ce_candidate,
                    day_timestamps=day_timestamps,
                    entry_timestamp=entry_timestamp,
                    exit_timestamp=exit_timestamp,
                    stop_loss_multiple=args.stop_loss_multiple,
                    target_price=args.target_premium,
                    slippage_points_per_order=args.slippage_points_per_order,
                    contract_multiplier=contract_multiplier,
                    brokerage_per_order=args.brokerage_per_order,
                )
                pe_leg = resolve_leg(
                    candidate=pe_candidate,
                    day_timestamps=day_timestamps,
                    entry_timestamp=entry_timestamp,
                    exit_timestamp=exit_timestamp,
                    stop_loss_multiple=args.stop_loss_multiple,
                    target_price=args.target_premium,
                    slippage_points_per_order=args.slippage_points_per_order,
                    contract_multiplier=contract_multiplier,
                    brokerage_per_order=args.brokerage_per_order,
                )

                failures = [leg for leg in (ce_leg, pe_leg) if leg.failure_reason]
                if failures:
                    result = make_day_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason=failures[0].failure_reason,
                        expiry_date=expiry_date,
                        spot_entry_timestamp=entry_timestamp,
                        spot_entry_open=spot_entry_row.open_text,
                        exit_timestamp=exit_timestamp,
                        atm_strike=strike_text,
                        ce_leg=ce_leg,
                        pe_leg=pe_leg,
                        remarks=join_remarks([ce_leg.remarks, pe_leg.remarks]),
                    )
                    results.append(result)
                    logger.info(
                        "SKIPPED date=%s expiry=%s strike=%s reason=%s",
                        entry_date,
                        expiry_date,
                        strike_text,
                        result.remarks,
                    )
                    continue

                result = make_day_result(
                    entry_date=entry_date,
                    status="TRADED",
                    skip_reason="",
                    expiry_date=expiry_date,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    exit_timestamp=exit_timestamp,
                    atm_strike=strike_text,
                    ce_leg=ce_leg,
                    pe_leg=pe_leg,
                    remarks=join_remarks([ce_leg.remarks, pe_leg.remarks]),
                )
                results.append(result)
                logger.info(
                    "TRADED date=%s expiry=%s atm=%s ce=%s pe=%s gross=%s brokerage=%s net=%s",
                    entry_date,
                    expiry_date,
                    strike_text,
                    ce_leg.strike,
                    pe_leg.strike,
                    result.gross_pnl,
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


def trade_rows_from_results(results: List[DayResult]) -> List[TradeRow]:
    trade_rows: List[TradeRow] = []
    for result in results:
        if result.status != "TRADED":
            continue
        trade_rows.append(
            TradeRow(
                entry_date=result.entry_date,
                status=result.status,
                expiry_date=result.expiry_date,
                side="CE",
                strike=result.ce_strike,
                contract_file=result.ce_contract_file,
                spot_entry_timestamp=result.spot_entry_timestamp,
                spot_entry_open=result.spot_entry_open,
                atm_strike=result.atm_strike,
                entry_timestamp=result.ce_entry_timestamp,
                entry_price=result.ce_entry_open,
                stop_price=result.ce_stop_price,
                target_price=result.ce_target_price,
                exit_timestamp=result.ce_exit_timestamp,
                exit_price=result.ce_exit_price,
                exit_reason=result.ce_exit_reason,
                points_pnl=result.ce_points_pnl,
                gross_pnl=result.ce_gross_pnl,
                brokerage=result.ce_brokerage,
                net_pnl=result.ce_net_pnl,
                remarks="",
            )
        )
        trade_rows.append(
            TradeRow(
                entry_date=result.entry_date,
                status=result.status,
                expiry_date=result.expiry_date,
                side="PE",
                strike=result.pe_strike,
                contract_file=result.pe_contract_file,
                spot_entry_timestamp=result.spot_entry_timestamp,
                spot_entry_open=result.spot_entry_open,
                atm_strike=result.atm_strike,
                entry_timestamp=result.pe_entry_timestamp,
                entry_price=result.pe_entry_open,
                stop_price=result.pe_stop_price,
                target_price=result.pe_target_price,
                exit_timestamp=result.pe_exit_timestamp,
                exit_price=result.pe_exit_price,
                exit_reason=result.pe_exit_reason,
                points_pnl=result.pe_points_pnl,
                gross_pnl=result.pe_gross_pnl,
                brokerage=result.pe_brokerage,
                net_pnl=result.pe_net_pnl,
                remarks="",
            )
        )
    return trade_rows


def write_daywise_csv(results: List[DayResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "skip_reason",
        "expiry_date",
        "spot_entry_timestamp",
        "spot_entry_open",
        "exit_timestamp",
        "atm_strike",
        "ce_strike",
        "ce_contract_file",
        "ce_entry_timestamp",
        "ce_entry_open",
        "ce_stop_price",
        "ce_target_price",
        "ce_exit_timestamp",
        "ce_exit_price",
        "ce_exit_reason",
        "ce_points_pnl",
        "ce_gross_pnl",
        "ce_brokerage",
        "ce_net_pnl",
        "pe_strike",
        "pe_contract_file",
        "pe_entry_timestamp",
        "pe_entry_open",
        "pe_stop_price",
        "pe_target_price",
        "pe_exit_timestamp",
        "pe_exit_price",
        "pe_exit_reason",
        "pe_points_pnl",
        "pe_gross_pnl",
        "pe_brokerage",
        "pe_net_pnl",
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


def write_trades_csv(trade_rows: List[TradeRow], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "expiry_date",
        "side",
        "strike",
        "contract_file",
        "spot_entry_timestamp",
        "spot_entry_open",
        "atm_strike",
        "entry_timestamp",
        "entry_price",
        "stop_price",
        "target_price",
        "exit_timestamp",
        "exit_price",
        "exit_reason",
        "points_pnl",
        "gross_pnl",
        "brokerage",
        "net_pnl",
        "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in trade_rows:
            writer.writerow(row.__dict__)


def write_summary(results: List[DayResult], output_path: Path, args: argparse.Namespace) -> None:
    traded_results = [result for result in results if result.status == "TRADED"]
    skipped_results = [result for result in results if result.status == "SKIPPED"]
    trade_rows = trade_rows_from_results(results)
    gross_total = sum(float(result.gross_pnl) for result in traded_results)
    brokerage_total = sum(float(result.brokerage) for result in traded_results)
    net_total = sum(float(result.net_pnl) for result in traded_results)
    target_count = sum(1 for row in trade_rows if row.exit_reason == "target")
    gap_target_count = sum(1 for row in trade_rows if row.exit_reason == "gap_target")
    stop_loss_count = sum(1 for row in trade_rows if row.exit_reason == "stop_loss")
    gap_stop_loss_count = sum(1 for row in trade_rows if row.exit_reason == "gap_stop_loss")
    day_close_count = sum(1 for row in trade_rows if row.exit_reason == "day_close")
    winning_days = sum(1 for result in traded_results if float(result.net_pnl) > 0)
    losing_days = sum(1 for result in traded_results if float(result.net_pnl) < 0)
    max_profit_day = max(traded_results, key=lambda result: float(result.net_pnl), default=None)
    max_loss_day = min(traded_results, key=lambda result: float(result.net_pnl), default=None)

    lines: List[str] = [
        "# 2025 Weekly Short Strangle 09:20 Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Entry time: `{args.entry_time}` option open",
        f"- Exit time: `{args.exit_time}` option open",
        "- Spot ATM rule: nearest 50 using the NIFTY entry-time open",
        "- Expiry rule: first expiry folder on or after the trade date",
        (
            f"- Short selection rule: sell OTM CE and OTM PE with each entry premium in the "
            f"`{format_number(args.sell_min_premium)}`-`{format_number(args.sell_max_premium)}` band, "
            f"choosing closest to `{format_number(args.sell_target_premium)}`"
        ),
        f"- Stop rule: independent stop at `{format_number(args.stop_loss_multiple)}x` each sold option's entry premium",
        (
            f"- Target rule: independent target when each option trades at or below "
            f"`{format_number(args.target_premium)}` points"
        ),
        "- Stop fill rule: use stop price when touched intrabar; use candle open when it opens above the stop",
        "- Target fill rule: use target price when touched intrabar; use candle open when it opens below the target",
        "- Same-candle stop/target rule: stop-first fill",
        "- Re-entry rule: none",
        "- Pricing rule: exact timestamp matching; no nearest-candle fallback",
        f"- Contract multiplier: {args.lot_size} x {args.lots} = {args.lot_size * args.lots} rupees per option point",
        f"- Execution slippage: {format_number(args.slippage_points_per_order)} point per order",
        (
            f"- Brokerage rule: Rs {format_number(args.brokerage_per_order)} per order, "
            f"Rs {format_number(args.brokerage_per_order * 4)} per completed strangle"
        ),
        "",
        "## Results Summary",
        "",
        f"- Total traded days: `{len(traded_results)}`",
        f"- Total skipped days: `{len(skipped_results)}`",
        f"- Total leg trades: `{len(trade_rows)}`",
        f"- Target leg exits: `{target_count}`",
        f"- Gap target leg exits: `{gap_target_count}`",
        f"- Stop-loss leg exits: `{stop_loss_count}`",
        f"- Gap stop-loss leg exits: `{gap_stop_loss_count}`",
        f"- Day-close leg exits: `{day_close_count}`",
        f"- Winning days: `{winning_days}`",
        f"- Losing days: `{losing_days}`",
        f"- Total Profit/Loss: `{format_number(net_total)}`",
        f"- Total Brokerage: `{format_number(brokerage_total)}`",
        f"- Profit/Loss without Brokerage: `{format_number(gross_total)}`",
        (
            f"- Max profit day: `{max_profit_day.entry_date}` with net P/L `{max_profit_day.net_pnl}`"
            if max_profit_day
            else "- Max profit day: `N/A`"
        ),
        (
            f"- Max loss day: `{max_loss_day.entry_date}` with net P/L `{max_loss_day.net_pnl}`"
            if max_loss_day
            else "- Max loss day: `N/A`"
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
            "- The NIFTY spot file is the source of truth for the trading calendar and intraday monitoring timestamps.",
            "- Raw 1-minute option candles from `Options_2025` are used directly.",
            "- A day is skipped if either strangle leg lacks the needed entry, monitoring, or scheduled exit candle.",
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
