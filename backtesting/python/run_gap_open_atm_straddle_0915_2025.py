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
BASE_FILENAME = "gap_open_atm_straddle_0915_2025"
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
class LegResult:
    side: str
    contract_file: str
    direction: str
    entry_timestamp: str
    entry_open: str
    exit_timestamp: str
    exit_close: str
    raw_points_pnl: str
    raw_gross_pnl: str
    slippage_points: str
    slippage_loss: str
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
    previous_trading_day: str
    previous_close_timestamp: str
    previous_close: str
    spot_entry_timestamp: str
    spot_entry_open: str
    gap_points: str
    gap_percent: str
    strategy_direction: str
    atm_strike: str
    ce_contract_file: str
    ce_direction: str
    ce_entry_open: str
    ce_exit_close: str
    ce_raw_points_pnl: str
    ce_raw_gross_pnl: str
    ce_slippage_points: str
    ce_slippage_loss: str
    ce_brokerage: str
    ce_net_pnl: str
    pe_contract_file: str
    pe_direction: str
    pe_entry_open: str
    pe_exit_close: str
    pe_raw_points_pnl: str
    pe_raw_gross_pnl: str
    pe_slippage_points: str
    pe_slippage_loss: str
    pe_brokerage: str
    pe_net_pnl: str
    orders_executed: str
    raw_gross_pnl: str
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
    spot_entry_timestamp: str
    spot_entry_open: str
    gap_points: str
    strategy_direction: str
    atm_strike: str
    side: str
    contract_file: str
    direction: str
    entry_timestamp: str
    entry_open: str
    exit_timestamp: str
    exit_close: str
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
        description="Backtest a 2025 09:15 gap-open ATM straddle scalp.",
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
    parser.add_argument("--entry-time", default="09:15")
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--lot-size", type=int, default=65)
    parser.add_argument("--lots", type=int, default=4)
    parser.add_argument("--slippage-points-per-order", type=float, default=2.0)
    args = parser.parse_args()

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


def strategy_direction_from_gap(gap_points: float) -> str:
    if gap_points < 0:
        return "LONG_STRADDLE"
    if gap_points > 0:
        return "SHORT_STRADDLE"
    return "FLAT_OPEN"


def empty_leg(side: str, contract_file: str = "", direction: str = "", remarks: str = "") -> LegResult:
    return LegResult(
        side=side,
        contract_file=contract_file,
        direction=direction,
        entry_timestamp="",
        entry_open="",
        exit_timestamp="",
        exit_close="",
        raw_points_pnl="0.00",
        raw_gross_pnl="0.00",
        slippage_points="0.00",
        slippage_loss="0.00",
        brokerage="0.00",
        net_pnl="0.00",
        failure_reason="",
        remarks=remarks,
    )


def resolve_leg(
    side: str,
    contract: ContractData,
    timestamp: str,
    strategy_direction: str,
    contract_multiplier: int,
    slippage_points_per_order: float,
    brokerage_per_order: float,
) -> LegResult:
    row = contract.rows_by_timestamp.get(timestamp)
    leg_direction = "LONG" if strategy_direction == "LONG_STRADDLE" else "SHORT"

    if row is None:
        remarks = (
            f"{contract.path.name} is header-only"
            if not contract.rows_by_timestamp
            else f"{contract.path.name} missing 09:15 timestamp {timestamp}"
        )
        return LegResult(
            side=side,
            contract_file=contract.path.name,
            direction=leg_direction,
            entry_timestamp="",
            entry_open="",
            exit_timestamp="",
            exit_close="",
            raw_points_pnl="0.00",
            raw_gross_pnl="0.00",
            slippage_points="0.00",
            slippage_loss="0.00",
            brokerage="0.00",
            net_pnl="0.00",
            failure_reason="missing_option_timestamp",
            remarks=remarks,
        )

    if strategy_direction == "LONG_STRADDLE":
        raw_points_pnl = row.close_value - row.open_value
    else:
        raw_points_pnl = row.open_value - row.close_value

    raw_gross_pnl = raw_points_pnl * contract_multiplier
    slippage_points = 2 * slippage_points_per_order
    slippage_loss = slippage_points * contract_multiplier
    brokerage = 2 * brokerage_per_order
    net_pnl = raw_gross_pnl - slippage_loss - brokerage

    return LegResult(
        side=side,
        contract_file=contract.path.name,
        direction=leg_direction,
        entry_timestamp=row.timestamp,
        entry_open=row.open_text,
        exit_timestamp=row.timestamp,
        exit_close=row.close_text,
        raw_points_pnl=format_number(raw_points_pnl),
        raw_gross_pnl=format_number(raw_gross_pnl),
        slippage_points=format_number(slippage_points),
        slippage_loss=format_number(slippage_loss),
        brokerage=format_number(brokerage),
        net_pnl=format_number(net_pnl),
        failure_reason="",
        remarks="",
    )


def make_day_result(
    entry_date: str,
    status: str,
    skip_reason: str,
    expiry_date: str,
    previous_trading_day: str,
    previous_close_timestamp: str,
    previous_close: str,
    spot_entry_timestamp: str,
    spot_entry_open: str,
    gap_points: str,
    gap_percent: str,
    strategy_direction: str,
    atm_strike: str,
    ce_leg: LegResult,
    pe_leg: LegResult,
    remarks: str,
) -> DayResult:
    traded_legs = [leg for leg in (ce_leg, pe_leg) if leg.entry_timestamp and leg.exit_timestamp]
    orders_executed = 2 * len(traded_legs) if status == "TRADED" else 0
    raw_gross_pnl = sum(float(leg.raw_gross_pnl) for leg in traded_legs) if status == "TRADED" else 0.0
    slippage_loss = sum(float(leg.slippage_loss) for leg in traded_legs) if status == "TRADED" else 0.0
    brokerage = sum(float(leg.brokerage) for leg in traded_legs) if status == "TRADED" else 0.0
    net_pnl = raw_gross_pnl - slippage_loss - brokerage

    return DayResult(
        entry_date=entry_date,
        status=status,
        skip_reason=skip_reason,
        expiry_date=expiry_date,
        previous_trading_day=previous_trading_day,
        previous_close_timestamp=previous_close_timestamp,
        previous_close=previous_close,
        spot_entry_timestamp=spot_entry_timestamp,
        spot_entry_open=spot_entry_open,
        gap_points=gap_points,
        gap_percent=gap_percent,
        strategy_direction=strategy_direction,
        atm_strike=atm_strike,
        ce_contract_file=ce_leg.contract_file,
        ce_direction=ce_leg.direction,
        ce_entry_open=ce_leg.entry_open,
        ce_exit_close=ce_leg.exit_close,
        ce_raw_points_pnl=ce_leg.raw_points_pnl if status == "TRADED" else "0.00",
        ce_raw_gross_pnl=ce_leg.raw_gross_pnl if status == "TRADED" else "0.00",
        ce_slippage_points=ce_leg.slippage_points if status == "TRADED" else "0.00",
        ce_slippage_loss=ce_leg.slippage_loss if status == "TRADED" else "0.00",
        ce_brokerage=ce_leg.brokerage if status == "TRADED" else "0.00",
        ce_net_pnl=ce_leg.net_pnl if status == "TRADED" else "0.00",
        pe_contract_file=pe_leg.contract_file,
        pe_direction=pe_leg.direction,
        pe_entry_open=pe_leg.entry_open,
        pe_exit_close=pe_leg.exit_close,
        pe_raw_points_pnl=pe_leg.raw_points_pnl if status == "TRADED" else "0.00",
        pe_raw_gross_pnl=pe_leg.raw_gross_pnl if status == "TRADED" else "0.00",
        pe_slippage_points=pe_leg.slippage_points if status == "TRADED" else "0.00",
        pe_slippage_loss=pe_leg.slippage_loss if status == "TRADED" else "0.00",
        pe_brokerage=pe_leg.brokerage if status == "TRADED" else "0.00",
        pe_net_pnl=pe_leg.net_pnl if status == "TRADED" else "0.00",
        orders_executed=str(orders_executed),
        raw_gross_pnl=format_number(raw_gross_pnl),
        slippage_loss=format_number(slippage_loss),
        brokerage=format_number(brokerage),
        net_pnl=format_number(net_pnl),
        remarks=remarks,
    )


def run_backtest(args: argparse.Namespace) -> List[DayResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, spot_rows_by_day, timestamps_by_day = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    contract_cache: Dict[Path, ContractData] = {}
    results: List[DayResult] = []
    contract_multiplier = args.lot_size * args.lots

    try:
        try:
            for day_index, entry_date in enumerate(trading_days):
                entry_timestamp = build_timestamp(entry_date, args.entry_time)
                previous_close = previous_close_for_day(
                    trading_days=trading_days,
                    spot_rows_by_day=spot_rows_by_day,
                    timestamps_by_day=timestamps_by_day,
                    day_index=day_index,
                )

                if previous_close is None:
                    result = make_day_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="no_previous_close",
                        expiry_date="",
                        previous_trading_day="",
                        previous_close_timestamp="",
                        previous_close="",
                        spot_entry_timestamp=entry_timestamp,
                        spot_entry_open="",
                        gap_points="",
                        gap_percent="",
                        strategy_direction="",
                        atm_strike="",
                        ce_leg=empty_leg("CE"),
                        pe_leg=empty_leg("PE"),
                        remarks="No previous trading day close exists in the dataset.",
                    )
                    results.append(result)
                    logger.info("SKIPPED date=%s reason=no_previous_close", entry_date)
                    continue

                previous_day, previous_close_row = previous_close
                spot_entry_row = spot_rows_by_day[entry_date].get(entry_timestamp)
                if spot_entry_row is None:
                    result = make_day_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="missing_spot_timestamp",
                        expiry_date="",
                        previous_trading_day=previous_day,
                        previous_close_timestamp=previous_close_row.timestamp,
                        previous_close=previous_close_row.close_text,
                        spot_entry_timestamp=entry_timestamp,
                        spot_entry_open="",
                        gap_points="",
                        gap_percent="",
                        strategy_direction="",
                        atm_strike="",
                        ce_leg=empty_leg("CE"),
                        pe_leg=empty_leg("PE"),
                        remarks=f"Missing spot entry timestamp {entry_timestamp}",
                    )
                    results.append(result)
                    logger.info("SKIPPED date=%s reason=missing_spot_timestamp", entry_date)
                    continue

                gap_points_value = spot_entry_row.open_value - previous_close_row.close_value
                gap_percent_value = (
                    (gap_points_value / previous_close_row.close_value) * 100
                    if previous_close_row.close_value
                    else 0.0
                )
                strategy_direction = strategy_direction_from_gap(gap_points_value)
                gap_points = format_number(gap_points_value)
                gap_percent = format_number(gap_percent_value)

                if strategy_direction == "FLAT_OPEN":
                    result = make_day_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="flat_open",
                        expiry_date="",
                        previous_trading_day=previous_day,
                        previous_close_timestamp=previous_close_row.timestamp,
                        previous_close=previous_close_row.close_text,
                        spot_entry_timestamp=entry_timestamp,
                        spot_entry_open=spot_entry_row.open_text,
                        gap_points=gap_points,
                        gap_percent=gap_percent,
                        strategy_direction=strategy_direction,
                        atm_strike="",
                        ce_leg=empty_leg("CE"),
                        pe_leg=empty_leg("PE"),
                        remarks="Open matched previous close exactly.",
                    )
                    results.append(result)
                    logger.info("SKIPPED date=%s reason=flat_open", entry_date)
                    continue

                expiry_date = first_expiry_on_or_after(expiries, entry_date)
                if expiry_date is None:
                    result = make_day_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="no_same_week_expiry",
                        expiry_date="",
                        previous_trading_day=previous_day,
                        previous_close_timestamp=previous_close_row.timestamp,
                        previous_close=previous_close_row.close_text,
                        spot_entry_timestamp=entry_timestamp,
                        spot_entry_open=spot_entry_row.open_text,
                        gap_points=gap_points,
                        gap_percent=gap_percent,
                        strategy_direction=strategy_direction,
                        atm_strike="",
                        ce_leg=empty_leg("CE"),
                        pe_leg=empty_leg("PE"),
                        remarks="No expiry folder exists on or after this trade date.",
                    )
                    results.append(result)
                    logger.info("SKIPPED date=%s reason=no_same_week_expiry", entry_date)
                    continue

                atm_strike = round_to_nearest_50(spot_entry_row.open_value)
                strike_text = str(atm_strike)
                option_suffix = expiry_suffix(expiry_date)
                ce_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_CE_{option_suffix}.csv"
                pe_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_PE_{option_suffix}.csv"
                leg_direction = "LONG" if strategy_direction == "LONG_STRADDLE" else "SHORT"

                ce_contract = load_contract(ce_path, contract_cache)
                pe_contract = load_contract(pe_path, contract_cache)
                if ce_contract is None or pe_contract is None:
                    missing_names: List[str] = []
                    if ce_contract is None:
                        missing_names.append(ce_path.name)
                    if pe_contract is None:
                        missing_names.append(pe_path.name)
                    result = make_day_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="missing_option_file",
                        expiry_date=expiry_date,
                        previous_trading_day=previous_day,
                        previous_close_timestamp=previous_close_row.timestamp,
                        previous_close=previous_close_row.close_text,
                        spot_entry_timestamp=entry_timestamp,
                        spot_entry_open=spot_entry_row.open_text,
                        gap_points=gap_points,
                        gap_percent=gap_percent,
                        strategy_direction=strategy_direction,
                        atm_strike=strike_text,
                        ce_leg=empty_leg("CE", ce_path.name if ce_contract is None else ce_contract.path.name, leg_direction),
                        pe_leg=empty_leg("PE", pe_path.name if pe_contract is None else pe_contract.path.name, leg_direction),
                        remarks=f"Missing option file(s): {', '.join(missing_names)}",
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
                    side="CE",
                    contract=ce_contract,
                    timestamp=entry_timestamp,
                    strategy_direction=strategy_direction,
                    contract_multiplier=contract_multiplier,
                    slippage_points_per_order=args.slippage_points_per_order,
                    brokerage_per_order=args.brokerage_per_order,
                )
                pe_leg = resolve_leg(
                    side="PE",
                    contract=pe_contract,
                    timestamp=entry_timestamp,
                    strategy_direction=strategy_direction,
                    contract_multiplier=contract_multiplier,
                    slippage_points_per_order=args.slippage_points_per_order,
                    brokerage_per_order=args.brokerage_per_order,
                )

                failures = [leg for leg in (ce_leg, pe_leg) if leg.failure_reason]
                if failures:
                    result = make_day_result(
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason=failures[0].failure_reason,
                        expiry_date=expiry_date,
                        previous_trading_day=previous_day,
                        previous_close_timestamp=previous_close_row.timestamp,
                        previous_close=previous_close_row.close_text,
                        spot_entry_timestamp=entry_timestamp,
                        spot_entry_open=spot_entry_row.open_text,
                        gap_points=gap_points,
                        gap_percent=gap_percent,
                        strategy_direction=strategy_direction,
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
                    previous_trading_day=previous_day,
                    previous_close_timestamp=previous_close_row.timestamp,
                    previous_close=previous_close_row.close_text,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    gap_points=gap_points,
                    gap_percent=gap_percent,
                    strategy_direction=strategy_direction,
                    atm_strike=strike_text,
                    ce_leg=ce_leg,
                    pe_leg=pe_leg,
                    remarks="",
                )
                results.append(result)
                logger.info(
                    "TRADED date=%s direction=%s expiry=%s strike=%s raw=%s slippage=%s brokerage=%s net=%s",
                    entry_date,
                    strategy_direction,
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
                previous_trading_day=result.previous_trading_day,
                previous_close=result.previous_close,
                spot_entry_timestamp=result.spot_entry_timestamp,
                spot_entry_open=result.spot_entry_open,
                gap_points=result.gap_points,
                strategy_direction=result.strategy_direction,
                atm_strike=result.atm_strike,
                side="CE",
                contract_file=result.ce_contract_file,
                direction=result.ce_direction,
                entry_timestamp=result.spot_entry_timestamp,
                entry_open=result.ce_entry_open,
                exit_timestamp=result.spot_entry_timestamp,
                exit_close=result.ce_exit_close,
                raw_points_pnl=result.ce_raw_points_pnl,
                raw_gross_pnl=result.ce_raw_gross_pnl,
                slippage_points=result.ce_slippage_points,
                slippage_loss=result.ce_slippage_loss,
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
                previous_trading_day=result.previous_trading_day,
                previous_close=result.previous_close,
                spot_entry_timestamp=result.spot_entry_timestamp,
                spot_entry_open=result.spot_entry_open,
                gap_points=result.gap_points,
                strategy_direction=result.strategy_direction,
                atm_strike=result.atm_strike,
                side="PE",
                contract_file=result.pe_contract_file,
                direction=result.pe_direction,
                entry_timestamp=result.spot_entry_timestamp,
                entry_open=result.pe_entry_open,
                exit_timestamp=result.spot_entry_timestamp,
                exit_close=result.pe_exit_close,
                raw_points_pnl=result.pe_raw_points_pnl,
                raw_gross_pnl=result.pe_raw_gross_pnl,
                slippage_points=result.pe_slippage_points,
                slippage_loss=result.pe_slippage_loss,
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
        "previous_trading_day",
        "previous_close_timestamp",
        "previous_close",
        "spot_entry_timestamp",
        "spot_entry_open",
        "gap_points",
        "gap_percent",
        "strategy_direction",
        "atm_strike",
        "ce_contract_file",
        "ce_direction",
        "ce_entry_open",
        "ce_exit_close",
        "ce_raw_points_pnl",
        "ce_raw_gross_pnl",
        "ce_slippage_points",
        "ce_slippage_loss",
        "ce_brokerage",
        "ce_net_pnl",
        "pe_contract_file",
        "pe_direction",
        "pe_entry_open",
        "pe_exit_close",
        "pe_raw_points_pnl",
        "pe_raw_gross_pnl",
        "pe_slippage_points",
        "pe_slippage_loss",
        "pe_brokerage",
        "pe_net_pnl",
        "orders_executed",
        "raw_gross_pnl",
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
        "spot_entry_timestamp",
        "spot_entry_open",
        "gap_points",
        "strategy_direction",
        "atm_strike",
        "side",
        "contract_file",
        "direction",
        "entry_timestamp",
        "entry_open",
        "exit_timestamp",
        "exit_close",
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


def write_summary(results: List[DayResult], output_path: Path, args: argparse.Namespace) -> None:
    traded_results = [result for result in results if result.status == "TRADED"]
    skipped_results = [result for result in results if result.status == "SKIPPED"]
    trade_rows = trade_rows_from_results(results)
    long_count = sum(1 for result in traded_results if result.strategy_direction == "LONG_STRADDLE")
    short_count = sum(1 for result in traded_results if result.strategy_direction == "SHORT_STRADDLE")
    winning_days = sum(1 for result in traded_results if float(result.net_pnl) > 0)
    losing_days = sum(1 for result in traded_results if float(result.net_pnl) < 0)
    raw_total = sum(float(result.raw_gross_pnl) for result in traded_results)
    slippage_total = sum(float(result.slippage_loss) for result in traded_results)
    brokerage_total = sum(float(result.brokerage) for result in traded_results)
    net_total = sum(float(result.net_pnl) for result in traded_results)
    max_profit_day = max(traded_results, key=lambda result: float(result.net_pnl), default=None)
    max_loss_day = min(traded_results, key=lambda result: float(result.net_pnl), default=None)

    lines: List[str] = [
        "# 2025 09:15 Gap-Open ATM Straddle Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Entry and exit candle: `{args.entry_time}`",
        "- Gap rule: compare NIFTY 09:15 open with the previous trading day's last close",
        "- Negative open: buy ATM CE and ATM PE at option open, exit both at option close",
        "- Positive open: short ATM CE and ATM PE at option open, cover both at option close",
        "- Flat open: skip",
        "- ATM rule: nearest 50 using NIFTY 09:15 open",
        "- Expiry rule: first expiry folder on or after the trade date",
        "- Pricing rule: option open to option close of the same 09:15 candle",
        f"- Contract multiplier: {args.lot_size} x {args.lots} = {args.lot_size * args.lots} rupees per option point",
        (
            f"- Slippage: {format_number(args.slippage_points_per_order)} points per order, "
            f"{format_number(args.slippage_points_per_order * 2)} points per leg round trip"
        ),
        (
            f"- Brokerage: Rs {format_number(args.brokerage_per_order)} per order, "
            f"Rs {format_number(args.brokerage_per_order * 4)} per completed straddle"
        ),
        "",
        "## Results Summary",
        "",
        f"- Total traded days: `{len(traded_results)}`",
        f"- Total skipped days: `{len(skipped_results)}`",
        f"- Total leg trades: `{len(trade_rows)}`",
        f"- Long straddle days: `{long_count}`",
        f"- Short straddle days: `{short_count}`",
        f"- Winning days: `{winning_days}`",
        f"- Losing days: `{losing_days}`",
        f"- Raw Profit/Loss before costs: `{format_number(raw_total)}`",
        f"- Slippage loss: `{format_number(slippage_total)}`",
        f"- Brokerage: `{format_number(brokerage_total)}`",
        f"- Net Profit/Loss: `{format_number(net_total)}`",
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
            "- The NIFTY spot file is the source of truth for trading days and previous-close detection.",
            "- Raw 1-minute option candles from `Options_2025` are used directly.",
            "- Slippage loss is reported separately and deducted from net P/L.",
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
