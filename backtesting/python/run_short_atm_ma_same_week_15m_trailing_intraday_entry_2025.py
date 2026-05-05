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
DAYWISE_FILENAME = "short_atm_ma_same_week_15m_trailing_intraday_entry_2025_daywise.csv"
SUMMARY_FILENAME = "short_atm_ma_same_week_15m_trailing_intraday_entry_2025_summary.md"
LOG_FILENAME = "short_atm_ma_same_week_15m_trailing_intraday_entry_2025.log"
UNAVAILABLE_STATUSES = {"MISSING_FILE", "MISSING_TIMESTAMP"}
LEG_STATE_PENDING = "PENDING"
LEG_STATE_ACTIVE = "ACTIVE"
LEG_STATE_CLOSED = "CLOSED"
LEG_STATE_UNAVAILABLE = "UNAVAILABLE"


@dataclass
class PriceRow:
    timestamp: str
    open_value: float
    open_text: str
    close_value: float
    close_text: str


@dataclass
class ContractData:
    path: Path
    rows_by_timestamp: Dict[str, PriceRow]
    ordered_rows: List[PriceRow]
    index_by_timestamp: Dict[str, int]


@dataclass
class SideExitOutcome:
    exit_row: Optional[PriceRow]
    exit_reason: str
    failure_reason: str
    failure_remarks: str


@dataclass
class LegState:
    side: str
    contract_path: Path
    contract_data: Optional[ContractData]
    signal_status: str
    remarks: str
    entry_row: Optional[PriceRow]
    entry_sma: Optional[float]
    exit_outcome: Optional[SideExitOutcome]
    state: str
    saw_valid_sma: bool
    last_prior_count: int


@dataclass
class TradeResult:
    entry_date: str
    status: str
    skip_reason: str
    expiry_date: str
    spot_entry_timestamp: str
    spot_entry_open: str
    atm_strike: str
    ce_signal_status: str
    ce_entry_sma: str
    ce_entry_timestamp: str
    ce_entry_open: str
    ce_exit_timestamp: str
    ce_exit_open: str
    ce_exit_reason: str
    pe_signal_status: str
    pe_entry_sma: str
    pe_entry_timestamp: str
    pe_entry_open: str
    pe_exit_timestamp: str
    pe_exit_open: str
    pe_exit_reason: str
    legs_traded: str
    orders_executed: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Backtest the 2025 same-week ATM short option strategy using a 15-minute "
            "trailing SMA stop with intraday first-entry monitoring."
        ),
    )
    parser.add_argument(
        "--spot-file",
        type=Path,
        default=repo_root / "nifty" / "NIFTY50_INDEX_15m_last_4y.csv",
    )
    parser.add_argument(
        "--options-dir",
        type=Path,
        default=repo_root / "Options_2025_15m",
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

    if not (args.entry_start_time <= args.last_entry_time <= args.exit_time):
        parser.error("--entry-start-time must be <= --last-entry-time <= --exit-time")

    return args


def build_timestamp(day: str, time_text: str) -> str:
    hour, minute = time_text.split(":")
    return f"{day}T{hour}:{minute}:00{IST_SUFFIX}"


def build_intraday_timestamps(day: str, start_time: str, end_time: str) -> List[str]:
    start_dt = datetime.datetime.strptime(f"{day} {start_time}", "%Y-%m-%d %H:%M")
    end_dt = datetime.datetime.strptime(f"{day} {end_time}", "%Y-%m-%d %H:%M")
    timestamps: List[str] = []
    current_dt = start_dt
    while current_dt <= end_dt:
        timestamps.append(current_dt.strftime("%Y-%m-%dT%H:%M:00") + IST_SUFFIX)
        current_dt += datetime.timedelta(minutes=15)
    return timestamps


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
    logger = logging.getLogger("short_atm_ma_same_week_15m_trailing_intraday_entry_2025")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def join_remarks(parts: List[str]) -> str:
    return "; ".join(part for part in parts if part)


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
            price_row = PriceRow(
                timestamp=timestamp,
                open_value=float(row["open"]),
                open_text=row["open"],
                close_value=float(row["close"]),
                close_text=row["close"],
            )
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
    ordered_rows: List[PriceRow] = []
    index_by_timestamp: Dict[str, int] = {}

    with contract_path.open("r", encoding="utf-8", newline="") as handle:
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

    contract_data = ContractData(
        path=contract_path,
        rows_by_timestamp=rows_by_timestamp,
        ordered_rows=ordered_rows,
        index_by_timestamp=index_by_timestamp,
    )
    cache[contract_path] = contract_data
    return contract_data


def compute_prior_sma(contract_data: ContractData, timestamp: str, ma_period: int) -> Tuple[Optional[float], int]:
    index = contract_data.index_by_timestamp.get(timestamp)
    if index is None:
        return None, 0
    if index < ma_period:
        return None, index
    window = contract_data.ordered_rows[index - ma_period : index]
    sma = sum(row.close_value for row in window) / ma_period
    return sma, index


def first_missing_timestamp(
    rows_by_timestamp: Dict[str, PriceRow],
    required_timestamps: List[str],
) -> Optional[str]:
    for timestamp in required_timestamps:
        if timestamp not in rows_by_timestamp:
            return timestamp
    return None


def placeholder_leg_state(side: str, signal_status: str, remarks: str = "") -> LegState:
    return LegState(
        side=side,
        contract_path=Path(""),
        contract_data=None,
        signal_status=signal_status,
        remarks=remarks,
        entry_row=None,
        entry_sma=None,
        exit_outcome=None,
        state=LEG_STATE_UNAVAILABLE,
        saw_valid_sma=False,
        last_prior_count=0,
    )


def initialize_leg_state(
    side: str,
    contract_path: Path,
    required_timestamps: List[str],
    contract_cache: Dict[Path, ContractData],
) -> LegState:
    contract_data = load_contract(contract_path, contract_cache)
    if contract_data is None:
        return LegState(
            side=side,
            contract_path=contract_path,
            contract_data=None,
            signal_status="MISSING_FILE",
            remarks=f"Missing option file: {contract_path.name}",
            entry_row=None,
            entry_sma=None,
            exit_outcome=None,
            state=LEG_STATE_UNAVAILABLE,
            saw_valid_sma=False,
            last_prior_count=0,
        )

    missing_timestamp = first_missing_timestamp(contract_data.rows_by_timestamp, required_timestamps)
    if missing_timestamp is not None:
        remarks = (
            f"{contract_path.name} is header-only"
            if not contract_data.ordered_rows
            else f"{contract_path.name} missing monitoring timestamp {missing_timestamp}"
        )
        return LegState(
            side=side,
            contract_path=contract_path,
            contract_data=contract_data,
            signal_status="MISSING_TIMESTAMP",
            remarks=remarks,
            entry_row=None,
            entry_sma=None,
            exit_outcome=None,
            state=LEG_STATE_UNAVAILABLE,
            saw_valid_sma=False,
            last_prior_count=0,
        )

    return LegState(
        side=side,
        contract_path=contract_path,
        contract_data=contract_data,
        signal_status="",
        remarks="",
        entry_row=None,
        entry_sma=None,
        exit_outcome=None,
        state=LEG_STATE_PENDING,
        saw_valid_sma=False,
        last_prior_count=0,
    )


def evaluate_pending_leg_entry(leg_state: LegState, timestamp: str, ma_period: int) -> None:
    if leg_state.state != LEG_STATE_PENDING or leg_state.contract_data is None:
        return

    current_row = leg_state.contract_data.rows_by_timestamp[timestamp]
    current_sma, prior_count = compute_prior_sma(leg_state.contract_data, timestamp, ma_period)
    leg_state.last_prior_count = prior_count
    if current_sma is None:
        return

    leg_state.saw_valid_sma = True
    if current_row.open_value < current_sma:
        leg_state.signal_status = "TRADED"
        leg_state.entry_row = current_row
        leg_state.entry_sma = current_sma
        leg_state.state = LEG_STATE_ACTIVE


def evaluate_active_leg_exit(leg_state: LegState, timestamp: str, ma_period: int) -> None:
    if leg_state.state != LEG_STATE_ACTIVE or leg_state.contract_data is None or leg_state.entry_row is None:
        return

    current_row = leg_state.contract_data.rows_by_timestamp.get(timestamp)
    if current_row is None:
        leg_state.exit_outcome = SideExitOutcome(
            exit_row=None,
            exit_reason="",
            failure_reason="entered_side_missing_timestamp",
            failure_remarks=(
                f"{leg_state.contract_path.name} missing monitoring timestamp {timestamp} "
                f"after {leg_state.entry_row.timestamp}"
            ),
        )
        leg_state.state = LEG_STATE_CLOSED
        return

    current_sma, _ = compute_prior_sma(leg_state.contract_data, timestamp, ma_period)
    if current_sma is None:
        leg_state.exit_outcome = SideExitOutcome(
            exit_row=None,
            exit_reason="",
            failure_reason="entered_side_insufficient_history",
            failure_remarks=(
                f"{leg_state.contract_path.name} does not have {ma_period} prior bars at {timestamp}"
            ),
        )
        leg_state.state = LEG_STATE_CLOSED
        return

    if current_row.open_value > current_sma:
        leg_state.exit_outcome = SideExitOutcome(
            exit_row=current_row,
            exit_reason="stop_loss_ma_cross",
            failure_reason="",
            failure_remarks="",
        )
        leg_state.state = LEG_STATE_CLOSED


def force_day_close_exit(leg_state: LegState, exit_timestamp: str) -> None:
    if leg_state.state != LEG_STATE_ACTIVE or leg_state.contract_data is None:
        return

    exit_row = leg_state.contract_data.rows_by_timestamp.get(exit_timestamp)
    if exit_row is None:
        leg_state.exit_outcome = SideExitOutcome(
            exit_row=None,
            exit_reason="",
            failure_reason="entered_side_missing_timestamp",
            failure_remarks=f"{leg_state.contract_path.name} missing scheduled exit timestamp {exit_timestamp}",
        )
        leg_state.state = LEG_STATE_CLOSED
        return

    leg_state.exit_outcome = SideExitOutcome(
        exit_row=exit_row,
        exit_reason="day_close",
        failure_reason="",
        failure_remarks="",
    )
    leg_state.state = LEG_STATE_CLOSED


def finalize_pending_leg(
    leg_state: LegState,
    entry_start_time: str,
    last_entry_time: str,
    ma_period: int,
) -> None:
    if leg_state.state != LEG_STATE_PENDING:
        return

    if leg_state.saw_valid_sma:
        leg_state.signal_status = "NO_SIGNAL"
        leg_state.remarks = (
            f"{leg_state.contract_path.name} had no qualifying bar with open below prior "
            f"{ma_period}-close SMA between {entry_start_time} and {last_entry_time}"
        )
    else:
        leg_state.signal_status = "INSUFFICIENT_HISTORY"
        leg_state.remarks = (
            f"{leg_state.contract_path.name} never had {ma_period} prior bars by {last_entry_time}; "
            f"max prior bars observed was {leg_state.last_prior_count}"
        )

    leg_state.state = LEG_STATE_CLOSED


def make_result(
    entry_date: str,
    status: str,
    skip_reason: str,
    expiry_date: str,
    spot_entry_timestamp: str,
    spot_entry_open: str,
    atm_strike: str,
    ce_leg: LegState,
    pe_leg: LegState,
    legs_traded: int,
    orders_executed: int,
    gross_pnl: float,
    brokerage: float,
    net_pnl: float,
    remarks: str,
) -> TradeResult:
    ce_entered = ce_leg.signal_status == "TRADED" and ce_leg.entry_row is not None
    pe_entered = pe_leg.signal_status == "TRADED" and pe_leg.entry_row is not None

    return TradeResult(
        entry_date=entry_date,
        status=status,
        skip_reason=skip_reason,
        expiry_date=expiry_date,
        spot_entry_timestamp=spot_entry_timestamp,
        spot_entry_open=spot_entry_open,
        atm_strike=atm_strike,
        ce_signal_status=ce_leg.signal_status,
        ce_entry_sma=format_optional_money(ce_leg.entry_sma if ce_entered else None),
        ce_entry_timestamp=ce_leg.entry_row.timestamp if ce_entered else "",
        ce_entry_open=ce_leg.entry_row.open_text if ce_entered else "",
        ce_exit_timestamp=ce_leg.exit_outcome.exit_row.timestamp if ce_leg.exit_outcome and ce_leg.exit_outcome.exit_row else "",
        ce_exit_open=ce_leg.exit_outcome.exit_row.open_text if ce_leg.exit_outcome and ce_leg.exit_outcome.exit_row else "",
        ce_exit_reason=ce_leg.exit_outcome.exit_reason if ce_leg.exit_outcome else "",
        pe_signal_status=pe_leg.signal_status,
        pe_entry_sma=format_optional_money(pe_leg.entry_sma if pe_entered else None),
        pe_entry_timestamp=pe_leg.entry_row.timestamp if pe_entered else "",
        pe_entry_open=pe_leg.entry_row.open_text if pe_entered else "",
        pe_exit_timestamp=pe_leg.exit_outcome.exit_row.timestamp if pe_leg.exit_outcome and pe_leg.exit_outcome.exit_row else "",
        pe_exit_open=pe_leg.exit_outcome.exit_row.open_text if pe_leg.exit_outcome and pe_leg.exit_outcome.exit_row else "",
        pe_exit_reason=pe_leg.exit_outcome.exit_reason if pe_leg.exit_outcome else "",
        legs_traded=str(legs_traded),
        orders_executed=str(orders_executed),
        gross_pnl=format_money(gross_pnl),
        brokerage=format_money(brokerage),
        net_pnl=format_money(net_pnl),
        remarks=remarks,
    )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, spot_rows_by_day, _ = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    contract_cache: Dict[Path, ContractData] = {}
    results: List[TradeResult] = []
    contract_multiplier = args.lot_size * args.lots

    try:
        for entry_date in trading_days:
            reference_timestamp = build_timestamp(entry_date, args.entry_start_time)
            exit_timestamp = build_timestamp(entry_date, args.exit_time)
            spot_rows = spot_rows_by_day[entry_date]
            monitoring_timestamps = build_intraday_timestamps(entry_date, args.entry_start_time, args.exit_time)
            entry_timestamps = build_intraday_timestamps(entry_date, args.entry_start_time, args.last_entry_time)
            entry_timestamp_set = set(entry_timestamps)

            missing_spot_timestamps = [
                timestamp for timestamp in monitoring_timestamps if timestamp not in spot_rows
            ]
            if missing_spot_timestamps:
                remarks = (
                    "Missing spot monitoring timestamps: " + ", ".join(missing_spot_timestamps)
                )
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="missing_spot_timestamp",
                    expiry_date="",
                    spot_entry_timestamp=reference_timestamp,
                    spot_entry_open=spot_rows[reference_timestamp].open_text if reference_timestamp in spot_rows else "",
                    atm_strike="",
                    ce_leg=placeholder_leg_state("CE", "MISSING_TIMESTAMP"),
                    pe_leg=placeholder_leg_state("PE", "MISSING_TIMESTAMP"),
                    legs_traded=0,
                    orders_executed=0,
                    gross_pnl=0.0,
                    brokerage=0.0,
                    net_pnl=0.0,
                    remarks=remarks,
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, remarks)
                continue

            expiry_date = first_expiry_on_or_after(expiries, entry_date)
            if expiry_date is None:
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="no_same_week_expiry",
                    expiry_date="",
                    spot_entry_timestamp=reference_timestamp,
                    spot_entry_open=spot_rows[reference_timestamp].open_text,
                    atm_strike="",
                    ce_leg=placeholder_leg_state("CE", "MISSING_FILE"),
                    pe_leg=placeholder_leg_state("PE", "MISSING_FILE"),
                    legs_traded=0,
                    orders_executed=0,
                    gross_pnl=0.0,
                    brokerage=0.0,
                    net_pnl=0.0,
                    remarks="No expiry folder exists on or after this trade date.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=no_same_week_expiry", entry_date)
                continue

            spot_reference_row = spot_rows[reference_timestamp]
            atm_strike = round_to_nearest_50(spot_reference_row.open_value)
            strike_text = str(atm_strike)
            option_suffix = expiry_suffix(expiry_date)
            ce_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_CE_{option_suffix}.csv"
            pe_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_PE_{option_suffix}.csv"

            ce_leg = initialize_leg_state(
                side="CE",
                contract_path=ce_path,
                required_timestamps=monitoring_timestamps,
                contract_cache=contract_cache,
            )
            pe_leg = initialize_leg_state(
                side="PE",
                contract_path=pe_path,
                required_timestamps=monitoring_timestamps,
                contract_cache=contract_cache,
            )

            for timestamp in monitoring_timestamps:
                if timestamp != exit_timestamp:
                    for leg_state in (ce_leg, pe_leg):
                        if (
                            leg_state.state == LEG_STATE_ACTIVE
                            and leg_state.entry_row is not None
                            and timestamp != leg_state.entry_row.timestamp
                        ):
                            evaluate_active_leg_exit(leg_state, timestamp, args.ma_period)

                if timestamp in entry_timestamp_set:
                    for leg_state in (ce_leg, pe_leg):
                        if leg_state.state == LEG_STATE_PENDING:
                            evaluate_pending_leg_entry(leg_state, timestamp, args.ma_period)

            for leg_state in (ce_leg, pe_leg):
                if leg_state.state == LEG_STATE_ACTIVE:
                    force_day_close_exit(leg_state, exit_timestamp)
                if leg_state.state == LEG_STATE_PENDING:
                    finalize_pending_leg(
                        leg_state,
                        entry_start_time=args.entry_start_time,
                        last_entry_time=args.last_entry_time,
                        ma_period=args.ma_period,
                    )

            exit_failures = [
                leg_state.exit_outcome.failure_remarks
                for leg_state in (ce_leg, pe_leg)
                if leg_state.exit_outcome and leg_state.exit_outcome.failure_reason
            ]
            entered_legs = [
                leg_state for leg_state in (ce_leg, pe_leg) if leg_state.signal_status == "TRADED"
            ]

            if exit_failures:
                failure_reasons = [
                    leg_state.exit_outcome.failure_reason
                    for leg_state in (ce_leg, pe_leg)
                    if leg_state.exit_outcome and leg_state.exit_outcome.failure_reason
                ]
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason=failure_reasons[0] if failure_reasons else "entered_side_missing_timestamp",
                    expiry_date=expiry_date,
                    spot_entry_timestamp=reference_timestamp,
                    spot_entry_open=spot_reference_row.open_text,
                    atm_strike=strike_text,
                    ce_leg=ce_leg,
                    pe_leg=pe_leg,
                    legs_traded=len(entered_legs),
                    orders_executed=0,
                    gross_pnl=0.0,
                    brokerage=0.0,
                    net_pnl=0.0,
                    remarks=join_remarks([ce_leg.remarks, pe_leg.remarks] + exit_failures),
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s strike=%s reason=%s",
                    entry_date,
                    expiry_date,
                    strike_text,
                    result.skip_reason,
                )
                continue

            if not entered_legs:
                both_sides_unavailable = (
                    ce_leg.signal_status in UNAVAILABLE_STATUSES and pe_leg.signal_status in UNAVAILABLE_STATUSES
                )
                skip_reason = "both_sides_unavailable" if both_sides_unavailable else "no_entry_signal"
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason=skip_reason,
                    expiry_date=expiry_date,
                    spot_entry_timestamp=reference_timestamp,
                    spot_entry_open=spot_reference_row.open_text,
                    atm_strike=strike_text,
                    ce_leg=ce_leg,
                    pe_leg=pe_leg,
                    legs_traded=0,
                    orders_executed=0,
                    gross_pnl=0.0,
                    brokerage=0.0,
                    net_pnl=0.0,
                    remarks=join_remarks([ce_leg.remarks, pe_leg.remarks]),
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s strike=%s reason=%s",
                    entry_date,
                    expiry_date,
                    strike_text,
                    skip_reason,
                )
                continue

            gross_pnl = 0.0
            for leg_state in entered_legs:
                if leg_state.entry_row is None or leg_state.exit_outcome is None or leg_state.exit_outcome.exit_row is None:
                    continue
                gross_pnl += (
                    leg_pnl_after_slippage(
                        leg_state.entry_row.open_value - leg_state.exit_outcome.exit_row.open_value,
                        args.slippage_points_per_order,
                    )
                    * contract_multiplier
                )

            orders_executed = 2 * len(entered_legs)
            brokerage = orders_executed * args.brokerage_per_order
            net_pnl = gross_pnl - brokerage
            result = make_result(
                entry_date=entry_date,
                status="TRADED",
                skip_reason="",
                expiry_date=expiry_date,
                spot_entry_timestamp=reference_timestamp,
                spot_entry_open=spot_reference_row.open_text,
                atm_strike=strike_text,
                ce_leg=ce_leg,
                pe_leg=pe_leg,
                legs_traded=len(entered_legs),
                orders_executed=orders_executed,
                gross_pnl=gross_pnl,
                brokerage=brokerage,
                net_pnl=net_pnl,
                remarks=join_remarks([ce_leg.remarks, pe_leg.remarks]),
            )
            results.append(result)
            logger.info(
                "TRADED date=%s expiry=%s strike=%s legs=%s gross=%s brokerage=%s net=%s",
                entry_date,
                expiry_date,
                strike_text,
                result.legs_traded,
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
        "spot_entry_timestamp",
        "spot_entry_open",
        "atm_strike",
        "ce_signal_status",
        "ce_entry_sma",
        "ce_entry_timestamp",
        "ce_entry_open",
        "ce_exit_timestamp",
        "ce_exit_open",
        "ce_exit_reason",
        "pe_signal_status",
        "pe_entry_sma",
        "pe_entry_timestamp",
        "pe_entry_open",
        "pe_exit_timestamp",
        "pe_exit_open",
        "pe_exit_reason",
        "legs_traded",
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


def write_summary(results: List[TradeResult], output_path: Path, args: argparse.Namespace) -> None:
    traded_results = [result for result in results if result.status == "TRADED"]
    skipped_results = [result for result in results if result.status == "SKIPPED"]
    gross_total = sum(float(result.gross_pnl) for result in traded_results)
    brokerage_total = sum(float(result.brokerage) for result in traded_results)
    net_total = sum(float(result.net_pnl) for result in traded_results)
    ce_only_count = sum(
        1
        for result in traded_results
        if result.ce_signal_status == "TRADED" and result.pe_signal_status != "TRADED"
    )
    pe_only_count = sum(
        1
        for result in traded_results
        if result.pe_signal_status == "TRADED" and result.ce_signal_status != "TRADED"
    )
    both_legs_count = sum(1 for result in traded_results if result.legs_traded == "2")

    lines: List[str] = [
        "# 2025 15-Minute Same-Week ATM MA Short Options Backtest With Intraday First Entry",
        "",
        "## Strategy Details",
        "",
        f"- ATM reference time: `{args.entry_start_time}`",
        f"- Last fresh-entry time: `{args.last_entry_time}`",
        f"- Exit time: `{args.exit_time}`",
        f"- Spot ATM rule: fixed nearest 50 using the NIFTY {args.entry_start_time} open",
        "- Expiry rule: first expiry folder on or after the trade date",
        (
            f"- Entry rule: monitor the fixed {args.entry_start_time} ATM CE and PE independently from "
            f"{args.entry_start_time} through {args.last_entry_time}; sell the first bar whose open is below the prior "
            f"{args.ma_period}-close SMA"
        ),
        (
            f"- Trailing stop rule: every later 15-minute bar recalculates the prior "
            f"{args.ma_period}-close SMA; exit when that bar open is above the updated SMA"
        ),
        "- MA source: option close",
        "- Re-entry rule: each leg may trade at most once per day",
        "- Pricing rule: exact option open price at exact timestamps",
        f"- Contract multiplier: {args.lot_size} x {args.lots} = {args.lot_size * args.lots} rupees per option point",
        f"- Execution slippage: {format_money(args.slippage_points_per_order)} point per order, applied against every entry and exit",
        (
            f"- Brokerage rule: Rs {int(args.brokerage_per_order)} per order, "
            f"so one-leg trades pay Rs {int(args.brokerage_per_order * 2)} and "
            f"two-leg trades pay Rs {int(args.brokerage_per_order * 4)} at the current settings"
        ),
        "",
        "## Results Summary",
        "",
        f"- Total traded days: `{len(traded_results)}`",
        f"- Total skipped days: `{len(skipped_results)}`",
        f"- CE-only trade count: `{ce_only_count}`",
        f"- PE-only trade count: `{pe_only_count}`",
        f"- Both-legs trade count: `{both_legs_count}`",
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
            "- Exact timestamp matching is required; no nearest-candle fallback is allowed.",
            f"- ATM is fixed once from the {args.entry_start_time} spot open and does not roll intraday.",
            "- CE and PE are monitored independently for first entry through the last-entry bar.",
            "- `15:15` is exit-only in this strategy variant.",
            "- Expiry folder dates are used as truth, which naturally handles Tuesday special expiries.",
            "- No intraday re-entry is allowed after a leg exits.",
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
