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
DAYWISE_FILENAME = "short_iron_condor_next_week_2025_daywise.csv"
SUMMARY_FILENAME = "short_iron_condor_next_week_2025_summary.md"
LOG_FILENAME = "short_iron_condor_next_week_2025.log"


@dataclass
class PriceRow:
    timestamp: str
    open_value: float
    open_text: str


@dataclass
class ContractData:
    path: Path
    rows_by_timestamp: Dict[str, PriceRow]


@dataclass
class OptionCandidate:
    strike: int
    entry_row: PriceRow
    exit_row: PriceRow
    premium_gap: float
    strike_distance: int


@dataclass
class TradeResult:
    entry_date: str
    status: str
    skip_reason: str
    expiry_date: str
    exit_date: str
    spot_entry_timestamp: str
    spot_entry_open: str
    spot_exit_timestamp: str
    spot_exit_open: str
    atm_strike: str
    sell_ce_strike: str
    sell_ce_entry_timestamp: str
    sell_ce_entry_open: str
    sell_ce_exit_timestamp: str
    sell_ce_exit_open: str
    sell_pe_strike: str
    sell_pe_entry_timestamp: str
    sell_pe_entry_open: str
    sell_pe_exit_timestamp: str
    sell_pe_exit_open: str
    buy_ce_strike: str
    buy_ce_entry_timestamp: str
    buy_ce_entry_open: str
    buy_ce_exit_timestamp: str
    buy_ce_exit_open: str
    buy_pe_strike: str
    buy_pe_entry_timestamp: str
    buy_pe_entry_open: str
    buy_pe_exit_timestamp: str
    buy_pe_exit_open: str
    entry_credit_points: str
    entry_debit_points: str
    net_entry_credit_points: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    adjustments: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Backtest the 2025 next-week Monday short iron condor strategy.",
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
    parser.add_argument("--entry-time", default="09:30")
    parser.add_argument("--exit-time", default="09:25")
    parser.add_argument("--sell-min-premium", type=float, default=25.0)
    parser.add_argument("--sell-max-premium", type=float, default=35.0)
    parser.add_argument("--sell-target-premium", type=float, default=30.0)
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--lot-size", type=int, default=65)
    parser.add_argument("--lots", type=int, default=4)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
    parser.add_argument("--wing-min-ratio", type=float, default=0.25)
    parser.add_argument("--wing-max-ratio", type=float, default=0.35)
    parser.add_argument("--wing-target-ratio", type=float, default=1.0 / 3.0)
    return parser.parse_args()


def build_timestamp(day: str, time_text: str) -> str:
    hour, minute = time_text.split(":")
    return f"{day}T{hour}:{minute}:00{IST_SUFFIX}"


def round_to_nearest_50(price: float) -> int:
    remainder = price % 50
    rounded_down = int(price - remainder)
    return rounded_down if remainder < 25 else rounded_down + 50


def format_money(value: float) -> str:
    return f"{value:.2f}"


def leg_pnl_after_slippage(raw_points_pnl: float, slippage_points_per_order: float) -> float:
    return raw_points_pnl - (2 * slippage_points_per_order)


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("short_iron_condor_next_week_2025")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def load_spot_data(spot_file: Path) -> Tuple[List[str], Dict[str, Dict[str, PriceRow]]]:
    trading_days: List[str] = []
    rows_by_day: Dict[str, Dict[str, PriceRow]] = {}
    with spot_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = row["timestamp"]
            day = timestamp[:10]
            if day not in rows_by_day:
                rows_by_day[day] = {}
                trading_days.append(day)
            rows_by_day[day][timestamp] = PriceRow(
                timestamp=timestamp,
                open_value=float(row["open"]),
                open_text=row["open"],
            )
    return trading_days, rows_by_day


def load_expiry_folders(options_dir: Path) -> List[str]:
    return sorted(path.name for path in options_dir.iterdir() if path.is_dir())


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


def next_expiry_after_date(expiries: List[str], date_text: str) -> Optional[str]:
    for expiry in expiries:
        if expiry > date_text:
            return expiry
    return None


def expiry_suffix(expiry_date: str) -> str:
    expiry_dt = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
    return expiry_dt.strftime("%d_%b_%y").upper()


def is_monday(date_text: str) -> bool:
    return datetime.datetime.strptime(date_text, "%Y-%m-%d").weekday() == 0


def planned_exit_date(entry_date: str) -> str:
    entry_dt = datetime.datetime.strptime(entry_date, "%Y-%m-%d")
    return (entry_dt + datetime.timedelta(days=7)).strftime("%Y-%m-%d")


def load_contract(contract_path: Path, cache: Dict[Path, ContractData]) -> Optional[ContractData]:
    if contract_path in cache:
        return cache[contract_path]
    if not contract_path.exists():
        return None

    rows_by_timestamp: Dict[str, PriceRow] = {}
    with contract_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = row["timestamp"]
            rows_by_timestamp[timestamp] = PriceRow(
                timestamp=timestamp,
                open_value=float(row["open"]),
                open_text=row["open"],
            )

    contract_data = ContractData(path=contract_path, rows_by_timestamp=rows_by_timestamp)
    cache[contract_path] = contract_data
    return contract_data


def make_skipped_result(
    entry_date: str,
    expiry_date: str,
    exit_date: str,
    spot_entry_timestamp: str,
    spot_entry_open: str,
    spot_exit_timestamp: str,
    spot_exit_open: str,
    atm_strike: str,
    skip_reason: str,
    remarks: str,
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date,
        status="SKIPPED",
        skip_reason=skip_reason,
        expiry_date=expiry_date,
        exit_date=exit_date,
        spot_entry_timestamp=spot_entry_timestamp,
        spot_entry_open=spot_entry_open,
        spot_exit_timestamp=spot_exit_timestamp,
        spot_exit_open=spot_exit_open,
        atm_strike=atm_strike,
        sell_ce_strike="",
        sell_ce_entry_timestamp="",
        sell_ce_entry_open="",
        sell_ce_exit_timestamp="",
        sell_ce_exit_open="",
        sell_pe_strike="",
        sell_pe_entry_timestamp="",
        sell_pe_entry_open="",
        sell_pe_exit_timestamp="",
        sell_pe_exit_open="",
        buy_ce_strike="",
        buy_ce_entry_timestamp="",
        buy_ce_entry_open="",
        buy_ce_exit_timestamp="",
        buy_ce_exit_open="",
        buy_pe_strike="",
        buy_pe_entry_timestamp="",
        buy_pe_entry_open="",
        buy_pe_exit_timestamp="",
        buy_pe_exit_open="",
        entry_credit_points="0.00",
        entry_debit_points="0.00",
        net_entry_credit_points="0.00",
        gross_pnl="0.00",
        brokerage="0.00",
        net_pnl="0.00",
        adjustments="0",
        remarks=remarks,
    )


def candidate_strikes_for_side(strikes: List[int], side: str, reference_strike: int) -> List[int]:
    if side == "CE":
        return [strike for strike in strikes if strike > reference_strike]
    return [strike for strike in reversed(strikes) if strike < reference_strike]


def select_option_candidate(
    expiry_date: str,
    side: str,
    reference_strike: int,
    entry_timestamp: str,
    exit_timestamp: str,
    options_dir: Path,
    cache: Dict[Path, ContractData],
    strike_index: Dict[Tuple[str, str], List[int]],
    min_premium: float,
    max_premium: float,
    target_premium: float,
    label: str,
) -> Tuple[Optional[OptionCandidate], str]:
    suffix = expiry_suffix(expiry_date)
    strikes = strike_index.get((expiry_date, side), [])
    candidate_strikes = candidate_strikes_for_side(strikes, side, reference_strike)
    if not candidate_strikes:
        return None, f"No OTM {side} {label} contracts were found beyond strike {reference_strike}."

    best_candidate: Optional[OptionCandidate] = None
    best_key: Optional[Tuple[float, int, int]] = None
    for strike in candidate_strikes:
        contract_path = options_dir / expiry_date / f"NIFTY_{strike}_{side}_{suffix}.csv"
        contract_data = load_contract(contract_path, cache)
        if contract_data is None:
            continue

        entry_row = contract_data.rows_by_timestamp.get(entry_timestamp)
        exit_row = contract_data.rows_by_timestamp.get(exit_timestamp)
        if entry_row is None or exit_row is None:
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
            best_candidate = OptionCandidate(
                strike=strike,
                entry_row=entry_row,
                exit_row=exit_row,
                premium_gap=candidate_key[0],
                strike_distance=candidate_key[1],
            )
            best_key = candidate_key

    if best_candidate is not None:
        return best_candidate, ""
    return (
        None,
        (
            f"No OTM {side} {label} contract satisfied the premium band "
            f"{format_money(min_premium)}-{format_money(max_premium)} at {entry_timestamp} "
            f"while also having exact exit timestamp {exit_timestamp}."
        ),
    )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, spot_rows_by_day = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    strike_index = index_option_strikes(args.options_dir, expiries)
    contract_cache: Dict[Path, ContractData] = {}
    cached_expiry = ""
    results: List[TradeResult] = []
    round_trip_brokerage = args.brokerage_per_order * 8
    contract_multiplier = args.lot_size * args.lots

    try:
        for entry_date in trading_days:
            if not is_monday(entry_date):
                continue

            entry_timestamp = build_timestamp(entry_date, args.entry_time)
            exit_date = planned_exit_date(entry_date)
            exit_timestamp = build_timestamp(exit_date, args.exit_time)
            spot_entry_row = spot_rows_by_day[entry_date].get(entry_timestamp)
            if spot_entry_row is None:
                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date="",
                    exit_date=exit_date,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open="",
                    spot_exit_timestamp=exit_timestamp,
                    spot_exit_open="",
                    atm_strike="",
                    skip_reason="missing_spot_entry_timestamp",
                    remarks=f"Spot file is missing exact entry timestamp {entry_timestamp}.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            spot_exit_row = spot_rows_by_day.get(exit_date, {}).get(exit_timestamp)
            if spot_exit_row is None:
                skip_reason = (
                    "no_planned_exit_trading_day"
                    if exit_date not in spot_rows_by_day
                    else "missing_spot_exit_timestamp"
                )
                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date="",
                    exit_date=exit_date,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    spot_exit_timestamp=exit_timestamp,
                    spot_exit_open="",
                    atm_strike="",
                    skip_reason=skip_reason,
                    remarks=f"Spot file is missing exact planned exit timestamp {exit_timestamp}.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            expiry_date = next_expiry_after_date(expiries, exit_date)
            if expiry_date is None:
                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date="",
                    exit_date=exit_date,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    spot_exit_timestamp=exit_timestamp,
                    spot_exit_open=spot_exit_row.open_text,
                    atm_strike="",
                    skip_reason="no_next_week_expiry_after_exit",
                    remarks="No weekly expiry folder exists strictly after the planned exit date.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            if expiry_date != cached_expiry:
                contract_cache.clear()
                cached_expiry = expiry_date

            atm_strike = round_to_nearest_50(spot_entry_row.open_value)
            atm_strike_text = str(atm_strike)

            sell_ce_candidate, sell_ce_error = select_option_candidate(
                expiry_date=expiry_date,
                side="CE",
                reference_strike=atm_strike,
                entry_timestamp=entry_timestamp,
                exit_timestamp=exit_timestamp,
                options_dir=args.options_dir,
                cache=contract_cache,
                strike_index=strike_index,
                min_premium=args.sell_min_premium,
                max_premium=args.sell_max_premium,
                target_premium=args.sell_target_premium,
                label="sell",
            )
            sell_pe_candidate, sell_pe_error = select_option_candidate(
                expiry_date=expiry_date,
                side="PE",
                reference_strike=atm_strike,
                entry_timestamp=entry_timestamp,
                exit_timestamp=exit_timestamp,
                options_dir=args.options_dir,
                cache=contract_cache,
                strike_index=strike_index,
                min_premium=args.sell_min_premium,
                max_premium=args.sell_max_premium,
                target_premium=args.sell_target_premium,
                label="sell",
            )

            if sell_ce_candidate is None or sell_pe_candidate is None:
                remarks_list: List[str] = []
                if sell_ce_error:
                    remarks_list.append(sell_ce_error)
                if sell_pe_error:
                    remarks_list.append(sell_pe_error)
                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date=expiry_date,
                    exit_date=exit_date,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    spot_exit_timestamp=exit_timestamp,
                    spot_exit_open=spot_exit_row.open_text,
                    atm_strike=atm_strike_text,
                    skip_reason="no_valid_sell_candidate",
                    remarks="; ".join(remarks_list),
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s atm=%s reason=%s",
                    entry_date,
                    expiry_date,
                    atm_strike_text,
                    result.remarks,
                )
                continue

            buy_ce_candidate, buy_ce_error = select_option_candidate(
                expiry_date=expiry_date,
                side="CE",
                reference_strike=sell_ce_candidate.strike,
                entry_timestamp=entry_timestamp,
                exit_timestamp=exit_timestamp,
                options_dir=args.options_dir,
                cache=contract_cache,
                strike_index=strike_index,
                min_premium=sell_ce_candidate.entry_row.open_value * args.wing_min_ratio,
                max_premium=sell_ce_candidate.entry_row.open_value * args.wing_max_ratio,
                target_premium=sell_ce_candidate.entry_row.open_value * args.wing_target_ratio,
                label="buy wing",
            )
            buy_pe_candidate, buy_pe_error = select_option_candidate(
                expiry_date=expiry_date,
                side="PE",
                reference_strike=sell_pe_candidate.strike,
                entry_timestamp=entry_timestamp,
                exit_timestamp=exit_timestamp,
                options_dir=args.options_dir,
                cache=contract_cache,
                strike_index=strike_index,
                min_premium=sell_pe_candidate.entry_row.open_value * args.wing_min_ratio,
                max_premium=sell_pe_candidate.entry_row.open_value * args.wing_max_ratio,
                target_premium=sell_pe_candidate.entry_row.open_value * args.wing_target_ratio,
                label="buy wing",
            )

            if buy_ce_candidate is None or buy_pe_candidate is None:
                remarks_list = []
                if buy_ce_error:
                    remarks_list.append(buy_ce_error)
                if buy_pe_error:
                    remarks_list.append(buy_pe_error)
                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date=expiry_date,
                    exit_date=exit_date,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    spot_exit_timestamp=exit_timestamp,
                    spot_exit_open=spot_exit_row.open_text,
                    atm_strike=atm_strike_text,
                    skip_reason="no_valid_wing_candidate",
                    remarks="; ".join(remarks_list),
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s atm=%s reason=%s",
                    entry_date,
                    expiry_date,
                    atm_strike_text,
                    result.remarks,
                )
                continue

            sell_ce_points_pnl = leg_pnl_after_slippage(
                sell_ce_candidate.entry_row.open_value - sell_ce_candidate.exit_row.open_value,
                args.slippage_points_per_order,
            )
            sell_pe_points_pnl = leg_pnl_after_slippage(
                sell_pe_candidate.entry_row.open_value - sell_pe_candidate.exit_row.open_value,
                args.slippage_points_per_order,
            )
            buy_ce_points_pnl = leg_pnl_after_slippage(
                buy_ce_candidate.exit_row.open_value - buy_ce_candidate.entry_row.open_value,
                args.slippage_points_per_order,
            )
            buy_pe_points_pnl = leg_pnl_after_slippage(
                buy_pe_candidate.exit_row.open_value - buy_pe_candidate.entry_row.open_value,
                args.slippage_points_per_order,
            )
            gross_pnl = (
                sell_ce_points_pnl
                + sell_pe_points_pnl
                + buy_ce_points_pnl
                + buy_pe_points_pnl
            ) * contract_multiplier
            brokerage = round_trip_brokerage
            net_pnl = gross_pnl - brokerage
            entry_credit_points = (
                sell_ce_candidate.entry_row.open_value + sell_pe_candidate.entry_row.open_value
            )
            entry_debit_points = (
                buy_ce_candidate.entry_row.open_value + buy_pe_candidate.entry_row.open_value
            )

            result = TradeResult(
                entry_date=entry_date,
                status="TRADED",
                skip_reason="",
                expiry_date=expiry_date,
                exit_date=exit_date,
                spot_entry_timestamp=entry_timestamp,
                spot_entry_open=spot_entry_row.open_text,
                spot_exit_timestamp=exit_timestamp,
                spot_exit_open=spot_exit_row.open_text,
                atm_strike=atm_strike_text,
                sell_ce_strike=str(sell_ce_candidate.strike),
                sell_ce_entry_timestamp=entry_timestamp,
                sell_ce_entry_open=sell_ce_candidate.entry_row.open_text,
                sell_ce_exit_timestamp=exit_timestamp,
                sell_ce_exit_open=sell_ce_candidate.exit_row.open_text,
                sell_pe_strike=str(sell_pe_candidate.strike),
                sell_pe_entry_timestamp=entry_timestamp,
                sell_pe_entry_open=sell_pe_candidate.entry_row.open_text,
                sell_pe_exit_timestamp=exit_timestamp,
                sell_pe_exit_open=sell_pe_candidate.exit_row.open_text,
                buy_ce_strike=str(buy_ce_candidate.strike),
                buy_ce_entry_timestamp=entry_timestamp,
                buy_ce_entry_open=buy_ce_candidate.entry_row.open_text,
                buy_ce_exit_timestamp=exit_timestamp,
                buy_ce_exit_open=buy_ce_candidate.exit_row.open_text,
                buy_pe_strike=str(buy_pe_candidate.strike),
                buy_pe_entry_timestamp=entry_timestamp,
                buy_pe_entry_open=buy_pe_candidate.entry_row.open_text,
                buy_pe_exit_timestamp=exit_timestamp,
                buy_pe_exit_open=buy_pe_candidate.exit_row.open_text,
                entry_credit_points=format_money(entry_credit_points),
                entry_debit_points=format_money(entry_debit_points),
                net_entry_credit_points=format_money(entry_credit_points - entry_debit_points),
                gross_pnl=format_money(gross_pnl),
                brokerage=format_money(brokerage),
                net_pnl=format_money(net_pnl),
                adjustments="0",
                remarks="",
            )
            results.append(result)
            logger.info(
                "TRADED date=%s expiry=%s exit=%s atm=%s sell_ce=%s sell_pe=%s buy_ce=%s buy_pe=%s gross=%s brokerage=%s net=%s",
                entry_date,
                expiry_date,
                exit_date,
                atm_strike_text,
                result.sell_ce_strike,
                result.sell_pe_strike,
                result.buy_ce_strike,
                result.buy_pe_strike,
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


def write_daywise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "skip_reason",
        "expiry_date",
        "exit_date",
        "spot_entry_timestamp",
        "spot_entry_open",
        "spot_exit_timestamp",
        "spot_exit_open",
        "atm_strike",
        "sell_ce_strike",
        "sell_ce_entry_timestamp",
        "sell_ce_entry_open",
        "sell_ce_exit_timestamp",
        "sell_ce_exit_open",
        "sell_pe_strike",
        "sell_pe_entry_timestamp",
        "sell_pe_entry_open",
        "sell_pe_exit_timestamp",
        "sell_pe_exit_open",
        "buy_ce_strike",
        "buy_ce_entry_timestamp",
        "buy_ce_entry_open",
        "buy_ce_exit_timestamp",
        "buy_ce_exit_open",
        "buy_pe_strike",
        "buy_pe_entry_timestamp",
        "buy_pe_entry_open",
        "buy_pe_exit_timestamp",
        "buy_pe_exit_open",
        "entry_credit_points",
        "entry_debit_points",
        "net_entry_credit_points",
        "gross_pnl",
        "brokerage",
        "net_pnl",
        "adjustments",
        "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)


def write_summary(results: List[TradeResult], output_path: Path, args: argparse.Namespace) -> None:
    traded_results = [result for result in results if result.status == "TRADED"]
    skipped_results = [result for result in results if result.status == "SKIPPED"]
    gross_total = sum(float(result.gross_pnl) for result in traded_results)
    brokerage_total = sum(float(result.brokerage) for result in traded_results)
    net_total = sum(float(result.net_pnl) for result in traded_results)

    lines: List[str] = [
        "# 2025 Next-Week Short Iron Condor Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Entry rule: trading Mondays at exact `{args.entry_time}` open",
        f"- Exit rule: next calendar Monday at exact `{args.exit_time}` open",
        "- Expiry rule: first available expiry folder strictly after the planned next-Monday exit date",
        "- ATM rule: nearest 50 using spot entry open",
        (
            f"- Short selection rule: sell OTM CE and OTM PE with entry premiums in the "
            f"{format_money(args.sell_min_premium)}-{format_money(args.sell_max_premium)} band, "
            f"choosing closest to {format_money(args.sell_target_premium)}"
        ),
        (
            f"- Wing selection rule: buy further OTM CE and PE with entry premiums in the "
            f"{int(args.wing_min_ratio * 100)}%-{int(args.wing_max_ratio * 100)}% band of each "
            f"sold leg, choosing closest to {args.wing_target_ratio * 100:.2f}%"
        ),
        "- Pricing rule: option open price at exact timestamps",
        f"- Contract multiplier: {args.lot_size} x {args.lots} = {args.lot_size * args.lots} rupees per option point",
        f"- Execution slippage: {format_money(args.slippage_points_per_order)} point per order, applied against every entry and exit",
        (
            f"- Brokerage rule: Rs {int(args.brokerage_per_order)} per order per leg, "
            f"Rs {int(args.brokerage_per_order * 8)} per completed iron condor"
        ),
        "- Adjustments: none",
        "",
        "## Results Summary",
        "",
        f"- No of Monday candidates: `{len(results)}`",
        f"- No of trades: `{len(traded_results)}`",
        "- No of adjustments: `0`",
        f"- Total Profit/Loss: `{format_money(net_total)}`",
        f"- Total Brokerage: `{format_money(brokerage_total)}`",
        f"- Profit/Loss without Brokerage: `{format_money(gross_total)}`",
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
            "- The backtest uses exact timestamp matching for both entry and exit; no nearest-candle fallback is allowed.",
            "- Profit/Loss without Brokerage includes the configured execution slippage but excludes brokerage.",
            "- The NIFTY spot file is the source of truth for Monday entries and planned exit-session availability.",
            "- The OTM call side is selected from strikes above the reference strike, and the OTM put side is selected from strikes below it.",
            "- If no valid sell or wing candidate exists in the requested premium band on either side, the full trade is skipped.",
            "- Missing next-Monday sessions, special sessions, and end-of-dataset gaps are recorded in the exceptions section.",
        ]
    )

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    results = run_backtest(args)
    write_daywise_csv(results, args.results_dir / DAYWISE_FILENAME)
    write_summary(results, args.results_dir / SUMMARY_FILENAME, args)


if __name__ == "__main__":
    main()
