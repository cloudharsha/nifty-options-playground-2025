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
DAYWISE_FILENAME = "intraday_adjusted_straddle_2025_daywise.csv"
EVENTS_FILENAME = "intraday_adjusted_straddle_2025_events.csv"
EXCEPTION_DAYWISE_FILENAME = "intraday_adjusted_straddle_2025_exception_daywise.csv"
EXCEPTION_EVENTS_FILENAME = "intraday_adjusted_straddle_2025_exception_events.csv"
SUMMARY_FILENAME = "intraday_adjusted_straddle_2025_summary.md"
LOG_FILENAME = "intraday_adjusted_straddle_2025.log"


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
class ActiveLeg:
    leg_id: int
    side: str
    strike: int
    contract_data: ContractData
    entry_timestamp: str
    entry_price: float
    entry_price_text: str
    entry_reason: str


@dataclass
class ClosedLeg:
    side: str
    strike: int
    entry_timestamp: str
    entry_price: float
    exit_timestamp: str
    exit_price: float
    entry_reason: str
    exit_reason: str


@dataclass
class ShortCandidate:
    strike: int
    contract_data: ContractData
    price_row: PriceRow
    gap: float
    strike_distance: int


@dataclass
class EventRow:
    entry_date: str
    event_timestamp: str
    event_sequence: str
    event_group: str
    order_action: str
    side: str
    strike: str
    price: str
    higher_side_before: str
    higher_value_before: str
    lower_side_before: str
    lower_value_before: str
    target_low: str
    target_high: str
    target_value: str
    active_ce_value_after: str
    active_pe_value_after: str
    remarks: str


@dataclass
class TradeResult:
    entry_date: str
    status: str
    skip_reason: str
    expiry_date: str
    spot_entry_timestamp: str
    spot_entry_open: str
    atm_strike: str
    initial_ce_entry_open: str
    initial_pe_entry_open: str
    entry_credit_points: str
    entry_credit_rupees: str
    adjustments: str
    first_add_count: str
    rebalance_count: str
    reversal_exit_count: str
    orders_executed: str
    exit_timestamp: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Backtest the 2025 intraday adjusted weekly short straddle strategy.",
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
    parser.add_argument("--exit-time", default="15:20")
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--lot-size", type=int, default=65)
    parser.add_argument("--lots", type=int, default=2)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
    parser.add_argument("--half-trigger-ratio", type=float, default=0.50)
    parser.add_argument("--first-add-min-ratio", type=float, default=0.20)
    parser.add_argument("--first-add-max-ratio", type=float, default=0.30)
    parser.add_argument("--first-add-target-ratio", type=float, default=0.25)
    parser.add_argument("--rebalance-min-ratio", type=float, default=0.65)
    parser.add_argument("--rebalance-max-ratio", type=float, default=0.85)
    parser.add_argument("--rebalance-target-ratio", type=float, default=0.75)
    parser.add_argument("--reversal-parity-ratio", type=float, default=1.00)
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
    logger = logging.getLogger("intraday_adjusted_straddle_2025")
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


def next_expiry_on_or_after(expiries: List[str], entry_date: str) -> Optional[str]:
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
    spot_entry_timestamp: str,
    spot_entry_open: str,
    atm_strike: str,
    skip_reason: str,
    remarks: str,
    exit_timestamp: str,
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date,
        status="SKIPPED",
        skip_reason=skip_reason,
        expiry_date=expiry_date,
        spot_entry_timestamp=spot_entry_timestamp,
        spot_entry_open=spot_entry_open,
        atm_strike=atm_strike,
        initial_ce_entry_open="",
        initial_pe_entry_open="",
        entry_credit_points="0.00",
        entry_credit_rupees="0.00",
        adjustments="0",
        first_add_count="0",
        rebalance_count="0",
        reversal_exit_count="0",
        orders_executed="0",
        exit_timestamp=exit_timestamp,
        gross_pnl="0.00",
        brokerage="0.00",
        net_pnl="0.00",
        remarks=remarks,
    )


def calculate_gross_pnl(
    closed_legs: List[ClosedLeg],
    slippage_points_per_order: float,
    contract_multiplier: int,
) -> float:
    gross_pnl = 0.0
    for closed_leg in closed_legs:
        gross_pnl += leg_pnl_after_slippage(
            closed_leg.entry_price - closed_leg.exit_price,
            slippage_points_per_order,
        ) * contract_multiplier
    return gross_pnl


def make_trade_result(
    entry_date: str,
    status: str,
    skip_reason: str,
    expiry_date: str,
    spot_entry_timestamp: str,
    spot_entry_open: str,
    atm_strike: str,
    ce_entry_row: PriceRow,
    pe_entry_row: PriceRow,
    contract_multiplier: int,
    first_add_count: int,
    rebalance_count: int,
    reversal_exit_count: int,
    orders_executed: int,
    exit_timestamp: str,
    closed_legs: List[ClosedLeg],
    brokerage_per_order: float,
    slippage_points_per_order: float,
    remarks: str,
) -> TradeResult:
    gross_pnl = calculate_gross_pnl(
        closed_legs=closed_legs,
        slippage_points_per_order=slippage_points_per_order,
        contract_multiplier=contract_multiplier,
    )
    brokerage = orders_executed * brokerage_per_order
    net_pnl = gross_pnl - brokerage
    entry_credit_points = ce_entry_row.open_value + pe_entry_row.open_value
    adjustments = first_add_count + rebalance_count + reversal_exit_count
    return TradeResult(
        entry_date=entry_date,
        status=status,
        skip_reason=skip_reason,
        expiry_date=expiry_date,
        spot_entry_timestamp=spot_entry_timestamp,
        spot_entry_open=spot_entry_open,
        atm_strike=atm_strike,
        initial_ce_entry_open=ce_entry_row.open_text,
        initial_pe_entry_open=pe_entry_row.open_text,
        entry_credit_points=format_money(entry_credit_points),
        entry_credit_rupees=format_money(entry_credit_points * contract_multiplier),
        adjustments=str(adjustments),
        first_add_count=str(first_add_count),
        rebalance_count=str(rebalance_count),
        reversal_exit_count=str(reversal_exit_count),
        orders_executed=str(orders_executed),
        exit_timestamp=exit_timestamp,
        gross_pnl=format_money(gross_pnl),
        brokerage=format_money(brokerage),
        net_pnl=format_money(net_pnl),
        remarks=remarks,
    )


def append_event(
    events: List[EventRow],
    entry_date: str,
    event_timestamp: str,
    event_sequence: int,
    event_group: str,
    order_action: str,
    side: str,
    strike: int,
    price: str,
    higher_side_before: str,
    higher_value_before: Optional[float],
    lower_side_before: str,
    lower_value_before: Optional[float],
    target_low: Optional[float],
    target_high: Optional[float],
    target_value: Optional[float],
    active_ce_value_after: float,
    active_pe_value_after: float,
    remarks: str,
) -> None:
    events.append(
        EventRow(
            entry_date=entry_date,
            event_timestamp=event_timestamp,
            event_sequence=str(event_sequence),
            event_group=event_group,
            order_action=order_action,
            side=side,
            strike=str(strike),
            price=price,
            higher_side_before=higher_side_before,
            higher_value_before="" if higher_value_before is None else format_money(higher_value_before),
            lower_side_before=lower_side_before,
            lower_value_before="" if lower_value_before is None else format_money(lower_value_before),
            target_low="" if target_low is None else format_money(target_low),
            target_high="" if target_high is None else format_money(target_high),
            target_value="" if target_value is None else format_money(target_value),
            active_ce_value_after=format_money(active_ce_value_after),
            active_pe_value_after=format_money(active_pe_value_after),
            remarks=remarks,
        )
    )


def current_higher_lower(ce_value: float, pe_value: float) -> Tuple[str, float, str, float]:
    if ce_value >= pe_value:
        return "CE", ce_value, "PE", pe_value
    return "PE", pe_value, "CE", ce_value


def build_current_rows(
    active_legs: List[ActiveLeg],
    timestamp: str,
    phase_label: str,
) -> Tuple[Optional[Dict[int, PriceRow]], str]:
    rows: Dict[int, PriceRow] = {}
    missing: List[str] = []
    for leg in active_legs:
        row = leg.contract_data.rows_by_timestamp.get(timestamp)
        if row is None:
            missing.append(
                f"{leg.contract_data.path.name} missing {phase_label} timestamp {timestamp}"
            )
        else:
            rows[leg.leg_id] = row
    if missing:
        return None, "; ".join(missing)
    return rows, ""


def compute_active_side_values(
    active_legs: List[ActiveLeg],
    current_rows: Dict[int, PriceRow],
) -> Tuple[float, float]:
    ce_value = 0.0
    pe_value = 0.0
    for leg in active_legs:
        row = current_rows[leg.leg_id]
        if leg.side == "CE":
            ce_value += row.open_value
        else:
            pe_value += row.open_value
    return ce_value, pe_value


def select_short_candidate(
    expiry_date: str,
    side: str,
    atm_strike: int,
    eval_timestamp: str,
    final_exit_timestamp: str,
    options_dir: Path,
    strike_index: Dict[Tuple[str, str], List[int]],
    contract_cache: Dict[Path, ContractData],
    min_value: float,
    max_value: float,
    target_value: float,
    base_value: float,
) -> Tuple[Optional[ShortCandidate], str]:
    suffix = expiry_suffix(expiry_date)
    strikes = strike_index.get((expiry_date, side), [])
    if side == "CE":
        eligible_strikes = [strike for strike in strikes if strike > atm_strike]
    else:
        eligible_strikes = [strike for strike in strikes if strike < atm_strike]

    if not eligible_strikes:
        return None, f"No OTM {side} strikes are available beyond ATM {atm_strike} for expiry {expiry_date}."

    best_candidate: Optional[ShortCandidate] = None
    best_key: Optional[Tuple[float, int, int]] = None
    for strike in eligible_strikes:
        contract_path = options_dir / expiry_date / f"NIFTY_{strike}_{side}_{suffix}.csv"
        contract_data = load_contract(contract_path, contract_cache)
        if contract_data is None:
            continue

        eval_row = contract_data.rows_by_timestamp.get(eval_timestamp)
        exit_row = contract_data.rows_by_timestamp.get(final_exit_timestamp)
        if eval_row is None or exit_row is None:
            continue

        combined_value = base_value + eval_row.open_value
        if not (min_value <= combined_value <= max_value):
            continue

        tie_break = strike if side == "CE" else -strike
        candidate_key = (
            abs(combined_value - target_value),
            abs(strike - atm_strike),
            tie_break,
        )
        if best_key is None or candidate_key < best_key:
            best_candidate = ShortCandidate(
                strike=strike,
                contract_data=contract_data,
                price_row=eval_row,
                gap=abs(combined_value - target_value),
                strike_distance=abs(strike - atm_strike),
            )
            best_key = candidate_key

    if best_candidate is not None:
        return best_candidate, ""
    return (
        None,
        (
            f"No OTM {side} contract satisfied the value band {format_money(min_value)}-"
            f"{format_money(max_value)} at {eval_timestamp} while also having exact final exit "
            f"timestamp {final_exit_timestamp}."
        ),
    )


def close_leg(
    active_legs: List[ActiveLeg],
    closed_legs: List[ClosedLeg],
    leg_to_close: ActiveLeg,
    exit_timestamp: str,
    exit_price: float,
    exit_reason: str,
) -> None:
    active_legs[:] = [leg for leg in active_legs if leg.leg_id != leg_to_close.leg_id]
    closed_legs.append(
        ClosedLeg(
            side=leg_to_close.side,
            strike=leg_to_close.strike,
            entry_timestamp=leg_to_close.entry_timestamp,
            entry_price=leg_to_close.entry_price,
            exit_timestamp=exit_timestamp,
            exit_price=exit_price,
            entry_reason=leg_to_close.entry_reason,
            exit_reason=exit_reason,
        )
    )


def exit_all_active_legs(
    active_legs: List[ActiveLeg],
    closed_legs: List[ClosedLeg],
    events: List[EventRow],
    entry_date: str,
    exit_timestamp: str,
    exit_rows: Dict[int, PriceRow],
    event_sequence: int,
    event_group: str,
    exit_reason: str,
    remarks: str,
) -> int:
    ce_before, pe_before = compute_active_side_values(active_legs, exit_rows)
    higher_side_before, higher_value_before, lower_side_before, lower_value_before = (
        current_higher_lower(ce_before, pe_before)
    )
    orders_executed = 0
    while active_legs:
        leg_to_close = active_legs[0]
        exit_row = exit_rows[leg_to_close.leg_id]
        close_leg(
            active_legs=active_legs,
            closed_legs=closed_legs,
            leg_to_close=leg_to_close,
            exit_timestamp=exit_timestamp,
            exit_price=exit_row.open_value,
            exit_reason=exit_reason,
        )
        orders_executed += 1
        ce_after_value, pe_after_value = compute_active_side_values(active_legs, exit_rows)
        append_event(
            events=events,
            entry_date=entry_date,
            event_timestamp=exit_timestamp,
            event_sequence=event_sequence,
            event_group=event_group,
            order_action="BUY",
            side=leg_to_close.side,
            strike=leg_to_close.strike,
            price=exit_row.open_text,
            higher_side_before=higher_side_before,
            higher_value_before=higher_value_before,
            lower_side_before=lower_side_before,
            lower_value_before=lower_value_before,
            target_low=None,
            target_high=None,
            target_value=None,
            active_ce_value_after=ce_after_value,
            active_pe_value_after=pe_after_value,
            remarks=remarks,
        )
    return orders_executed


def run_backtest(
    args: argparse.Namespace,
) -> Tuple[List[TradeResult], List[EventRow], List[TradeResult], List[EventRow]]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, spot_rows_by_day = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    strike_index = index_option_strikes(args.options_dir, expiries)
    contract_cache: Dict[Path, ContractData] = {}
    cached_expiry = ""

    results: List[TradeResult] = []
    events: List[EventRow] = []
    exception_results: List[TradeResult] = []
    exception_events: List[EventRow] = []
    candidate_days = 0
    total_adjustments = 0
    contract_multiplier = args.lot_size * args.lots

    try:
        for entry_date in trading_days:
            entry_timestamp = build_timestamp(entry_date, args.entry_time)
            exit_timestamp = build_timestamp(entry_date, args.exit_time)
            day_rows = spot_rows_by_day[entry_date]
            spot_entry_row = day_rows.get(entry_timestamp)
            spot_exit_row = day_rows.get(exit_timestamp)
            if spot_entry_row is None or spot_exit_row is None:
                continue

            candidate_days += 1
            expiry_date = next_expiry_on_or_after(expiries, entry_date)
            if expiry_date is None:
                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date="",
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    atm_strike="",
                    skip_reason="no_same_or_next_weekly_expiry",
                    remarks="No weekly expiry folder exists on or after this entry date.",
                    exit_timestamp=exit_timestamp,
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            if expiry_date != cached_expiry:
                contract_cache.clear()
                cached_expiry = expiry_date

            atm_strike = round_to_nearest_50(spot_entry_row.open_value)
            atm_strike_text = str(atm_strike)
            suffix = expiry_suffix(expiry_date)

            ce_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_CE_{suffix}.csv"
            pe_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_PE_{suffix}.csv"
            ce_contract = load_contract(ce_path, contract_cache)
            pe_contract = load_contract(pe_path, contract_cache)
            if ce_contract is None or pe_contract is None:
                missing_names: List[str] = []
                if ce_contract is None:
                    missing_names.append(ce_path.name)
                if pe_contract is None:
                    missing_names.append(pe_path.name)
                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date=expiry_date,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    atm_strike=atm_strike_text,
                    skip_reason="missing_atm_option_file",
                    remarks=f"Missing ATM option file(s): {', '.join(missing_names)}",
                    exit_timestamp=exit_timestamp,
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s strike=%s reason=%s",
                    entry_date,
                    expiry_date,
                    atm_strike_text,
                    result.remarks,
                )
                continue

            ce_entry_row = ce_contract.rows_by_timestamp.get(entry_timestamp)
            ce_exit_row = ce_contract.rows_by_timestamp.get(exit_timestamp)
            pe_entry_row = pe_contract.rows_by_timestamp.get(entry_timestamp)
            pe_exit_row = pe_contract.rows_by_timestamp.get(exit_timestamp)
            missing_points: List[str] = []
            if ce_entry_row is None:
                missing_points.append(f"{ce_path.name} missing entry timestamp {entry_timestamp}")
            if ce_exit_row is None:
                missing_points.append(f"{ce_path.name} missing final exit timestamp {exit_timestamp}")
            if pe_entry_row is None:
                missing_points.append(f"{pe_path.name} missing entry timestamp {entry_timestamp}")
            if pe_exit_row is None:
                missing_points.append(f"{pe_path.name} missing final exit timestamp {exit_timestamp}")

            if missing_points:
                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date=expiry_date,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    atm_strike=atm_strike_text,
                    skip_reason="missing_atm_entry_or_exit_timestamp",
                    remarks="; ".join(missing_points),
                    exit_timestamp=exit_timestamp,
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s strike=%s reason=%s",
                    entry_date,
                    expiry_date,
                    atm_strike_text,
                    result.remarks,
                )
                continue

            temp_events: List[EventRow] = []
            closed_legs: List[ClosedLeg] = []
            pending_cycle_logs: List[str] = []
            active_legs: List[ActiveLeg] = []
            leg_id_counter = 1
            next_event_sequence = 1
            orders_executed = 0
            first_add_count = 0
            rebalance_count = 0
            reversal_exit_count = 0
            skip_reason = ""
            skip_remarks = ""
            exception_exit_timestamp = ""
            exception_exit_rows: Optional[Dict[int, PriceRow]] = None

            ce_leg = ActiveLeg(
                leg_id=leg_id_counter,
                side="CE",
                strike=atm_strike,
                contract_data=ce_contract,
                entry_timestamp=entry_timestamp,
                entry_price=ce_entry_row.open_value,
                entry_price_text=ce_entry_row.open_text,
                entry_reason="INITIAL_ENTRY",
            )
            leg_id_counter += 1
            pe_leg = ActiveLeg(
                leg_id=leg_id_counter,
                side="PE",
                strike=atm_strike,
                contract_data=pe_contract,
                entry_timestamp=entry_timestamp,
                entry_price=pe_entry_row.open_value,
                entry_price_text=pe_entry_row.open_text,
                entry_reason="INITIAL_ENTRY",
            )
            leg_id_counter += 1

            initial_rows = {
                ce_leg.leg_id: ce_entry_row,
                pe_leg.leg_id: pe_entry_row,
            }
            initial_sequence = next_event_sequence
            next_event_sequence += 1
            active_legs.append(ce_leg)
            orders_executed += 1
            ce_after_value, pe_after_value = compute_active_side_values(active_legs, initial_rows)
            append_event(
                events=temp_events,
                entry_date=entry_date,
                event_timestamp=entry_timestamp,
                event_sequence=initial_sequence,
                event_group="INITIAL_ENTRY",
                order_action="SELL",
                side="CE",
                strike=atm_strike,
                price=ce_entry_row.open_text,
                higher_side_before="",
                higher_value_before=None,
                lower_side_before="",
                lower_value_before=None,
                target_low=None,
                target_high=None,
                target_value=None,
                active_ce_value_after=ce_after_value,
                active_pe_value_after=pe_after_value,
                remarks="Initial ATM CE short entry.",
            )
            active_legs.append(pe_leg)
            orders_executed += 1
            ce_after_value, pe_after_value = compute_active_side_values(active_legs, initial_rows)
            append_event(
                events=temp_events,
                entry_date=entry_date,
                event_timestamp=entry_timestamp,
                event_sequence=initial_sequence,
                event_group="INITIAL_ENTRY",
                order_action="SELL",
                side="PE",
                strike=atm_strike,
                price=pe_entry_row.open_text,
                higher_side_before="",
                higher_value_before=None,
                lower_side_before="",
                lower_value_before=None,
                target_low=None,
                target_high=None,
                target_value=None,
                active_ce_value_after=ce_after_value,
                active_pe_value_after=pe_after_value,
                remarks="Initial ATM PE short entry.",
            )

            evaluation_timestamps = [
                timestamp
                for timestamp in sorted(day_rows)
                if entry_timestamp < timestamp < exit_timestamp
            ]

            for eval_timestamp in evaluation_timestamps:
                current_rows, missing_rows_error = build_current_rows(
                    active_legs,
                    eval_timestamp,
                    "evaluation",
                )
                if current_rows is None:
                    skip_reason = "missing_active_leg_timestamp"
                    skip_remarks = missing_rows_error
                    break

                ce_legs = [leg for leg in active_legs if leg.side == "CE"]
                pe_legs = [leg for leg in active_legs if leg.side == "PE"]
                ce_value, pe_value = compute_active_side_values(active_legs, current_rows)
                higher_side_before, higher_value_before, lower_side_before, lower_value_before = (
                    current_higher_lower(ce_value, pe_value)
                )

                if (len(ce_legs), len(pe_legs)) in {(2, 1), (1, 2)}:
                    double_side = "CE" if len(ce_legs) == 2 else "PE"
                    single_side = "PE" if double_side == "CE" else "CE"
                    double_legs = ce_legs if double_side == "CE" else pe_legs
                    double_value = ce_value if double_side == "CE" else pe_value
                    single_value = ce_value if single_side == "CE" else pe_value
                    if single_value <= double_value * args.reversal_parity_ratio:
                        smaller_leg = min(
                            double_legs,
                            key=lambda leg: (current_rows[leg.leg_id].open_value, leg.leg_id),
                        )
                        smaller_row = current_rows[smaller_leg.leg_id]
                        event_sequence = next_event_sequence
                        next_event_sequence += 1
                        close_leg(
                            active_legs=active_legs,
                            closed_legs=closed_legs,
                            leg_to_close=smaller_leg,
                            exit_timestamp=eval_timestamp,
                            exit_price=smaller_row.open_value,
                            exit_reason="REVERSAL_EXIT",
                        )
                        orders_executed += 1
                        reversal_exit_count += 1
                        ce_after_value, pe_after_value = compute_active_side_values(active_legs, current_rows)
                        append_event(
                            events=temp_events,
                            entry_date=entry_date,
                            event_timestamp=eval_timestamp,
                            event_sequence=event_sequence,
                            event_group="REVERSAL_EXIT",
                            order_action="BUY",
                            side=smaller_leg.side,
                            strike=smaller_leg.strike,
                            price=smaller_row.open_text,
                            higher_side_before=higher_side_before,
                            higher_value_before=higher_value_before,
                            lower_side_before=lower_side_before,
                            lower_value_before=lower_value_before,
                            target_low=None,
                            target_high=None,
                            target_value=double_value * args.reversal_parity_ratio,
                            active_ce_value_after=ce_after_value,
                            active_pe_value_after=pe_after_value,
                            remarks=(
                                f"Exited smaller {double_side} short after parity reversal against "
                                f"the single {single_side} side."
                            ),
                        )
                        pending_cycle_logs.append(
                            "ADJUSTMENT date=%s timestamp=%s group=REVERSAL_EXIT exited_side=%s "
                            "exited_strike=%s single_value=%s double_value=%s"
                            % (
                                entry_date,
                                eval_timestamp,
                                smaller_leg.side,
                                smaller_leg.strike,
                                format_money(single_value),
                                format_money(double_value),
                            )
                        )
                        continue

                if lower_value_before <= higher_value_before * args.half_trigger_ratio:
                    weak_side = lower_side_before
                    weak_legs = ce_legs if weak_side == "CE" else pe_legs
                    target_low: float
                    target_high: float
                    target_value: float
                    if len(weak_legs) == 1:
                        target_low = higher_value_before * args.first_add_min_ratio
                        target_high = higher_value_before * args.first_add_max_ratio
                        target_value = higher_value_before * args.first_add_target_ratio
                        candidate, error_message = select_short_candidate(
                            expiry_date=expiry_date,
                            side=weak_side,
                            atm_strike=atm_strike,
                            eval_timestamp=eval_timestamp,
                            final_exit_timestamp=exit_timestamp,
                            options_dir=args.options_dir,
                            strike_index=strike_index,
                            contract_cache=contract_cache,
                            min_value=target_low,
                            max_value=target_high,
                            target_value=target_value,
                            base_value=0.0,
                        )
                        if candidate is None:
                            skip_reason = "no_valid_first_add_candidate"
                            skip_remarks = error_message
                            exception_exit_timestamp = eval_timestamp
                            exception_exit_rows = current_rows
                            break

                        event_sequence = next_event_sequence
                        next_event_sequence += 1
                        new_leg = ActiveLeg(
                            leg_id=leg_id_counter,
                            side=weak_side,
                            strike=candidate.strike,
                            contract_data=candidate.contract_data,
                            entry_timestamp=eval_timestamp,
                            entry_price=candidate.price_row.open_value,
                            entry_price_text=candidate.price_row.open_text,
                            entry_reason="FIRST_ADD",
                        )
                        leg_id_counter += 1
                        active_legs.append(new_leg)
                        current_rows[new_leg.leg_id] = candidate.price_row
                        orders_executed += 1
                        first_add_count += 1
                        ce_after_value, pe_after_value = compute_active_side_values(active_legs, current_rows)
                        append_event(
                            events=temp_events,
                            entry_date=entry_date,
                            event_timestamp=eval_timestamp,
                            event_sequence=event_sequence,
                            event_group="FIRST_ADD",
                            order_action="SELL",
                            side=new_leg.side,
                            strike=new_leg.strike,
                            price=new_leg.entry_price_text,
                            higher_side_before=higher_side_before,
                            higher_value_before=higher_value_before,
                            lower_side_before=lower_side_before,
                            lower_value_before=lower_value_before,
                            target_low=target_low,
                            target_high=target_high,
                            target_value=target_value,
                            active_ce_value_after=ce_after_value,
                            active_pe_value_after=pe_after_value,
                            remarks=f"Added OTM {weak_side} short closest to the first-add target.",
                        )
                        pending_cycle_logs.append(
                            "ADJUSTMENT date=%s timestamp=%s group=FIRST_ADD side=%s strike=%s "
                            "higher_value=%s target_band=%s-%s"
                            % (
                                entry_date,
                                eval_timestamp,
                                new_leg.side,
                                new_leg.strike,
                                format_money(higher_value_before),
                                format_money(target_low),
                                format_money(target_high),
                            )
                        )
                        continue

                    if len(weak_legs) == 2:
                        smaller_leg = min(
                            weak_legs,
                            key=lambda leg: (current_rows[leg.leg_id].open_value, leg.leg_id),
                        )
                        retained_leg = next(
                            leg for leg in weak_legs if leg.leg_id != smaller_leg.leg_id
                        )
                        retained_value = current_rows[retained_leg.leg_id].open_value
                        target_low = higher_value_before * args.rebalance_min_ratio
                        target_high = higher_value_before * args.rebalance_max_ratio
                        target_value = higher_value_before * args.rebalance_target_ratio
                        candidate, error_message = select_short_candidate(
                            expiry_date=expiry_date,
                            side=weak_side,
                            atm_strike=atm_strike,
                            eval_timestamp=eval_timestamp,
                            final_exit_timestamp=exit_timestamp,
                            options_dir=args.options_dir,
                            strike_index=strike_index,
                            contract_cache=contract_cache,
                            min_value=target_low,
                            max_value=target_high,
                            target_value=target_value,
                            base_value=retained_value,
                        )
                        if candidate is None:
                            skip_reason = "no_valid_rebalance_candidate"
                            skip_remarks = error_message
                            exception_exit_timestamp = eval_timestamp
                            exception_exit_rows = current_rows
                            break

                        event_sequence = next_event_sequence
                        next_event_sequence += 1
                        smaller_row = current_rows[smaller_leg.leg_id]
                        close_leg(
                            active_legs=active_legs,
                            closed_legs=closed_legs,
                            leg_to_close=smaller_leg,
                            exit_timestamp=eval_timestamp,
                            exit_price=smaller_row.open_value,
                            exit_reason="REBALANCE_EXIT",
                        )
                        orders_executed += 1
                        ce_after_exit, pe_after_exit = compute_active_side_values(active_legs, current_rows)
                        append_event(
                            events=temp_events,
                            entry_date=entry_date,
                            event_timestamp=eval_timestamp,
                            event_sequence=event_sequence,
                            event_group="REBALANCE",
                            order_action="BUY",
                            side=smaller_leg.side,
                            strike=smaller_leg.strike,
                            price=smaller_row.open_text,
                            higher_side_before=higher_side_before,
                            higher_value_before=higher_value_before,
                            lower_side_before=lower_side_before,
                            lower_value_before=lower_value_before,
                            target_low=target_low,
                            target_high=target_high,
                            target_value=target_value,
                            active_ce_value_after=ce_after_exit,
                            active_pe_value_after=pe_after_exit,
                            remarks="Exited the smaller weak-side short before replacement.",
                        )

                        new_leg = ActiveLeg(
                            leg_id=leg_id_counter,
                            side=weak_side,
                            strike=candidate.strike,
                            contract_data=candidate.contract_data,
                            entry_timestamp=eval_timestamp,
                            entry_price=candidate.price_row.open_value,
                            entry_price_text=candidate.price_row.open_text,
                            entry_reason="REBALANCE_ADD",
                        )
                        leg_id_counter += 1
                        active_legs.append(new_leg)
                        current_rows[new_leg.leg_id] = candidate.price_row
                        orders_executed += 1
                        rebalance_count += 1
                        ce_after_add, pe_after_add = compute_active_side_values(active_legs, current_rows)
                        append_event(
                            events=temp_events,
                            entry_date=entry_date,
                            event_timestamp=eval_timestamp,
                            event_sequence=event_sequence,
                            event_group="REBALANCE",
                            order_action="SELL",
                            side=new_leg.side,
                            strike=new_leg.strike,
                            price=new_leg.entry_price_text,
                            higher_side_before=higher_side_before,
                            higher_value_before=higher_value_before,
                            lower_side_before=lower_side_before,
                            lower_value_before=lower_value_before,
                            target_low=target_low,
                            target_high=target_high,
                            target_value=target_value,
                            active_ce_value_after=ce_after_add,
                            active_pe_value_after=pe_after_add,
                            remarks=(
                                f"Added replacement {weak_side} short with retained {weak_side} "
                                f"strike {retained_leg.strike}."
                            ),
                        )
                        pending_cycle_logs.append(
                            "ADJUSTMENT date=%s timestamp=%s group=REBALANCE side=%s exited_strike=%s "
                            "new_strike=%s higher_value=%s target_band=%s-%s"
                            % (
                                entry_date,
                                eval_timestamp,
                                weak_side,
                                smaller_leg.strike,
                                new_leg.strike,
                                format_money(higher_value_before),
                                format_money(target_low),
                                format_money(target_high),
                            )
                        )
                        continue

            if skip_reason:
                if exception_exit_rows is not None:
                    forced_exit_sequence = next_event_sequence
                    next_event_sequence += 1
                    forced_exit_remarks = f"Forced exit after {skip_reason}: {skip_remarks}"
                    orders_executed += exit_all_active_legs(
                        active_legs=active_legs,
                        closed_legs=closed_legs,
                        events=temp_events,
                        entry_date=entry_date,
                        exit_timestamp=exception_exit_timestamp,
                        exit_rows=exception_exit_rows,
                        event_sequence=forced_exit_sequence,
                        event_group="EXCEPTION_EXIT",
                        exit_reason="EXCEPTION_EXIT",
                        remarks=forced_exit_remarks,
                    )
                    result = make_trade_result(
                        entry_date=entry_date,
                        status="EXCEPTION_EXIT",
                        skip_reason=skip_reason,
                        expiry_date=expiry_date,
                        spot_entry_timestamp=entry_timestamp,
                        spot_entry_open=spot_entry_row.open_text,
                        atm_strike=atm_strike_text,
                        ce_entry_row=ce_entry_row,
                        pe_entry_row=pe_entry_row,
                        contract_multiplier=contract_multiplier,
                        first_add_count=first_add_count,
                        rebalance_count=rebalance_count,
                        reversal_exit_count=reversal_exit_count,
                        orders_executed=orders_executed,
                        exit_timestamp=exception_exit_timestamp,
                        closed_legs=closed_legs,
                        brokerage_per_order=args.brokerage_per_order,
                        slippage_points_per_order=args.slippage_points_per_order,
                        remarks=skip_remarks,
                    )
                    exception_results.append(result)
                    exception_events.extend(temp_events)
                    for log_line in pending_cycle_logs:
                        logger.info(log_line)
                    logger.info(
                        "EXCEPTION_EXIT date=%s expiry=%s atm=%s reason=%s exit=%s orders=%s gross=%s brokerage=%s net=%s",
                        entry_date,
                        expiry_date,
                        atm_strike_text,
                        skip_reason,
                        result.exit_timestamp,
                        result.orders_executed,
                        result.gross_pnl,
                        result.brokerage,
                        result.net_pnl,
                    )
                    continue

                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date=expiry_date,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    atm_strike=atm_strike_text,
                    skip_reason=skip_reason,
                    remarks=skip_remarks,
                    exit_timestamp=exit_timestamp,
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s strike=%s reason=%s",
                    entry_date,
                    expiry_date,
                    atm_strike_text,
                    result.remarks,
                )
                continue

            final_rows, final_rows_error = build_current_rows(
                active_legs,
                exit_timestamp,
                "final exit",
            )
            if final_rows is None:
                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date=expiry_date,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    atm_strike=atm_strike_text,
                    skip_reason="missing_active_leg_timestamp",
                    remarks=final_rows_error,
                    exit_timestamp=exit_timestamp,
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s strike=%s reason=%s",
                    entry_date,
                    expiry_date,
                    atm_strike_text,
                    result.remarks,
                )
                continue

            final_sequence = next_event_sequence
            next_event_sequence += 1
            final_ce_before, final_pe_before = compute_active_side_values(active_legs, final_rows)
            higher_side_before, higher_value_before, lower_side_before, lower_value_before = (
                current_higher_lower(final_ce_before, final_pe_before)
            )
            while active_legs:
                leg_to_close = active_legs[0]
                exit_row = final_rows[leg_to_close.leg_id]
                close_leg(
                    active_legs=active_legs,
                    closed_legs=closed_legs,
                    leg_to_close=leg_to_close,
                    exit_timestamp=exit_timestamp,
                    exit_price=exit_row.open_value,
                    exit_reason="FINAL_EXIT",
                )
                orders_executed += 1
                ce_after_value, pe_after_value = compute_active_side_values(active_legs, final_rows)
                append_event(
                    events=temp_events,
                    entry_date=entry_date,
                    event_timestamp=exit_timestamp,
                    event_sequence=final_sequence,
                    event_group="FINAL_EXIT",
                    order_action="BUY",
                    side=leg_to_close.side,
                    strike=leg_to_close.strike,
                    price=exit_row.open_text,
                    higher_side_before=higher_side_before,
                    higher_value_before=higher_value_before,
                    lower_side_before=lower_side_before,
                    lower_value_before=lower_value_before,
                    target_low=None,
                    target_high=None,
                    target_value=None,
                    active_ce_value_after=ce_after_value,
                    active_pe_value_after=pe_after_value,
                    remarks="End-of-day exit for active short leg.",
                )

            adjustments = first_add_count + rebalance_count + reversal_exit_count
            total_adjustments += adjustments
            result = make_trade_result(
                entry_date=entry_date,
                status="TRADED",
                skip_reason="",
                expiry_date=expiry_date,
                spot_entry_timestamp=entry_timestamp,
                spot_entry_open=spot_entry_row.open_text,
                atm_strike=atm_strike_text,
                ce_entry_row=ce_entry_row,
                pe_entry_row=pe_entry_row,
                contract_multiplier=contract_multiplier,
                first_add_count=first_add_count,
                rebalance_count=rebalance_count,
                reversal_exit_count=reversal_exit_count,
                orders_executed=orders_executed,
                exit_timestamp=exit_timestamp,
                closed_legs=closed_legs,
                brokerage_per_order=args.brokerage_per_order,
                slippage_points_per_order=args.slippage_points_per_order,
                remarks="",
            )
            results.append(result)
            events.extend(temp_events)
            for log_line in pending_cycle_logs:
                logger.info(log_line)
            logger.info(
                "TRADED date=%s expiry=%s atm=%s adjustments=%s orders=%s gross=%s brokerage=%s net=%s",
                entry_date,
                expiry_date,
                atm_strike_text,
                result.adjustments,
                result.orders_executed,
                result.gross_pnl,
                result.brokerage,
                result.net_pnl,
            )
    except Exception:
        logger.exception("ERROR unexpected failure while running the backtest")
        raise

    traded_count = sum(1 for result in results if result.status == "TRADED")
    skipped_count = sum(1 for result in results if result.status == "SKIPPED")
    logger.info(
        "COMPLETED candidate_days=%s traded=%s skipped=%s exception_exits=%s total_adjustments=%s",
        candidate_days,
        traded_count,
        skipped_count,
        len(exception_results),
        total_adjustments,
    )
    return results, events, exception_results, exception_events


def write_daywise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "skip_reason",
        "expiry_date",
        "spot_entry_timestamp",
        "spot_entry_open",
        "atm_strike",
        "initial_ce_entry_open",
        "initial_pe_entry_open",
        "entry_credit_points",
        "entry_credit_rupees",
        "adjustments",
        "first_add_count",
        "rebalance_count",
        "reversal_exit_count",
        "orders_executed",
        "exit_timestamp",
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


def write_events_csv(events: List[EventRow], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "event_timestamp",
        "event_sequence",
        "event_group",
        "order_action",
        "side",
        "strike",
        "price",
        "higher_side_before",
        "higher_value_before",
        "lower_side_before",
        "lower_value_before",
        "target_low",
        "target_high",
        "target_value",
        "active_ce_value_after",
        "active_pe_value_after",
        "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for event in events:
            writer.writerow(event.__dict__)


def write_summary(
    results: List[TradeResult],
    exception_results: List[TradeResult],
    output_path: Path,
    args: argparse.Namespace,
) -> None:
    traded_results = [result for result in results if result.status == "TRADED"]
    skipped_results = [result for result in results if result.status == "SKIPPED"]
    gross_total = sum(float(result.gross_pnl) for result in traded_results)
    brokerage_total = sum(float(result.brokerage) for result in traded_results)
    net_total = sum(float(result.net_pnl) for result in traded_results)
    total_adjustments = sum(int(result.adjustments) for result in traded_results)
    exception_gross_total = sum(float(result.gross_pnl) for result in exception_results)
    exception_brokerage_total = sum(float(result.brokerage) for result in exception_results)
    exception_net_total = sum(float(result.net_pnl) for result in exception_results)
    exception_adjustments = sum(int(result.adjustments) for result in exception_results)

    lines: List[str] = [
        "# 2025 Intraday Adjusted Weekly Straddle Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Entry time: `{args.entry_time}`",
        f"- Exit time: `{args.exit_time}`",
        "- Expiry rule: first weekly expiry on or after the entry date",
        "- ATM rule: nearest 50 using spot 09:30 open",
        f"- Lot size and lots: `{args.lot_size}` x `{args.lots}`",
        f"- Contract multiplier: `{args.lot_size * args.lots}` rupees per option point",
        (
            f"- Slippage: `{format_money(args.slippage_points_per_order)}` point per order, "
            "applied against every executed entry and exit"
        ),
        f"- Brokerage: `Rs {int(args.brokerage_per_order)}` per order per leg",
        (
            f"- First-add band and target: `{int(args.first_add_min_ratio * 100)}%-"
            f"{int(args.first_add_max_ratio * 100)}%`, target `{args.first_add_target_ratio * 100:.2f}%` "
            "of the stronger-side value"
        ),
        (
            f"- Rebalance band and target: `{int(args.rebalance_min_ratio * 100)}%-"
            f"{int(args.rebalance_max_ratio * 100)}%`, target `{args.rebalance_target_ratio * 100:.2f}%` "
            "combined with the retained weak-side short"
        ),
        (
            f"- Reversal rule: exit the smaller leg on the two-short side when the single-side value is "
            f"`<= {args.reversal_parity_ratio * 100:.2f}%` of the combined two-short side"
        ),
        "- Adjustments are symmetric for upside and downside moves",
        "- Final exit happens at the exact 15:20 open",
        "",
        "## Results Summary",
        "",
        f"- No of trades: `{len(traded_results)}`",
        f"- No of adjustments: `{total_adjustments}`",
        f"- Total Profit/Loss: `{format_money(net_total)}`",
        f"- Total Brokerage: `{format_money(brokerage_total)}`",
        f"- Profit/Loss without Brokerage: `{format_money(gross_total)}`",
        "",
        "## Exception Trade Results",
        "",
        f"- No of exception trades: `{len(exception_results)}`",
        f"- No of exception adjustments before forced exit: `{exception_adjustments}`",
        f"- Total Exception Profit/Loss: `{format_money(exception_net_total)}`",
        f"- Total Exception Brokerage: `{format_money(exception_brokerage_total)}`",
        f"- Exception Profit/Loss without Brokerage: `{format_money(exception_gross_total)}`",
        f"- Daywise file: `{EXCEPTION_DAYWISE_FILENAME}`",
        f"- Events file: `{EXCEPTION_EVENTS_FILENAME}`",
        "- These rows are not included in the main Results Summary totals.",
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
            "- Candidate days are limited to sessions with exact spot candles at `09:30` and `15:20`.",
            "- The engine evaluates at most one adjustment cycle per minute, with `REVERSAL_EXIT` taking priority over trend adds and rebalances.",
            "- Profit/Loss without Brokerage includes the configured execution slippage but excludes brokerage.",
            "- Candidate-selection failures after entry are force-closed immediately and reported only in the exception trade result files.",
            "- Other validation failures remain skipped when the engine cannot price every active leg.",
            "- Same-day expiry trades are allowed because the expiry rule is `expiry >= entry_date`.",
            "- `2025-10-21` is excluded as a candidate day because the spot dataset does not contain an exact `09:30` candle for that special session.",
        ]
    )

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    results, events, exception_results, exception_events = run_backtest(args)
    write_daywise_csv(results, args.results_dir / DAYWISE_FILENAME)
    write_events_csv(events, args.results_dir / EVENTS_FILENAME)
    write_daywise_csv(exception_results, args.results_dir / EXCEPTION_DAYWISE_FILENAME)
    write_events_csv(exception_events, args.results_dir / EXCEPTION_EVENTS_FILENAME)
    write_summary(results, exception_results, args.results_dir / SUMMARY_FILENAME, args)


if __name__ == "__main__":
    main()
