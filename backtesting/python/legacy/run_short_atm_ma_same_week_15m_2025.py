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
DAYWISE_FILENAME = "short_atm_ma_same_week_15m_2025_daywise.csv"
SUMMARY_FILENAME = "short_atm_ma_same_week_15m_2025_summary.md"
LOG_FILENAME = "short_atm_ma_same_week_15m_2025.log"
UNAVAILABLE_STATUSES = {"MISSING_FILE", "MISSING_TIMESTAMP", "INSUFFICIENT_HISTORY"}


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
class SideEvaluation:
    side: str
    signal_status: str
    remarks: str
    contract_path: Path
    contract_data: Optional[ContractData]
    entry_row: Optional[PriceRow]
    entry_sma: Optional[float]


@dataclass
class SideExitOutcome:
    exit_row: Optional[PriceRow]
    exit_reason: str
    failure_reason: str
    failure_remarks: str


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
        description="Backtest the 2025 same-week ATM short option strategy using 15-minute SMA signals.",
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
    parser.add_argument("--entry-time", default="09:30")
    parser.add_argument("--exit-time", default="15:15")
    parser.add_argument("--ma-period", type=int, default=25)
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--lot-size", type=int, default=65)
    parser.add_argument("--lots", type=int, default=4)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
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


def format_optional_money(value: Optional[float]) -> str:
    return "" if value is None else format_money(value)


def leg_pnl_after_slippage(raw_points_pnl: float, slippage_points_per_order: float) -> float:
    return raw_points_pnl - (2 * slippage_points_per_order)


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("short_atm_ma_same_week_15m_2025")
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


def evaluate_side_entry(
    side: str,
    contract_path: Path,
    entry_timestamp: str,
    ma_period: int,
    contract_cache: Dict[Path, ContractData],
) -> SideEvaluation:
    contract_data = load_contract(contract_path, contract_cache)
    if contract_data is None:
        return SideEvaluation(
            side=side,
            signal_status="MISSING_FILE",
            remarks=f"Missing option file: {contract_path.name}",
            contract_path=contract_path,
            contract_data=None,
            entry_row=None,
            entry_sma=None,
        )

    entry_row = contract_data.rows_by_timestamp.get(entry_timestamp)
    if entry_row is None:
        remarks = (
            f"{contract_path.name} is header-only"
            if not contract_data.ordered_rows
            else f"{contract_path.name} missing entry timestamp {entry_timestamp}"
        )
        return SideEvaluation(
            side=side,
            signal_status="MISSING_TIMESTAMP",
            remarks=remarks,
            contract_path=contract_path,
            contract_data=contract_data,
            entry_row=None,
            entry_sma=None,
        )

    entry_sma, prior_count = compute_prior_sma(contract_data, entry_timestamp, ma_period)
    if entry_sma is None:
        return SideEvaluation(
            side=side,
            signal_status="INSUFFICIENT_HISTORY",
            remarks=(
                f"{contract_path.name} has {prior_count} prior bars at {entry_timestamp}; "
                f"needs {ma_period}"
            ),
            contract_path=contract_path,
            contract_data=contract_data,
            entry_row=entry_row,
            entry_sma=None,
        )

    if entry_row.open_value < entry_sma:
        return SideEvaluation(
            side=side,
            signal_status="TRADED",
            remarks="",
            contract_path=contract_path,
            contract_data=contract_data,
            entry_row=entry_row,
            entry_sma=entry_sma,
        )

    return SideEvaluation(
        side=side,
        signal_status="NO_SIGNAL",
        remarks=(
            f"{contract_path.name} open {entry_row.open_text} is not below SMA "
            f"{format_money(entry_sma)} at {entry_timestamp}"
        ),
        contract_path=contract_path,
        contract_data=contract_data,
        entry_row=entry_row,
        entry_sma=entry_sma,
    )


def resolve_side_exit(
    evaluation: SideEvaluation,
    day_timestamps: List[str],
    entry_timestamp: str,
    exit_timestamp: str,
    ma_period: int,
) -> SideExitOutcome:
    if evaluation.contract_data is None or evaluation.entry_row is None:
        return SideExitOutcome(
            exit_row=None,
            exit_reason="",
            failure_reason="entered_side_missing_timestamp",
            failure_remarks=f"{evaluation.side} side did not have valid contract data after entry.",
        )

    entry_index = day_timestamps.index(entry_timestamp)
    exit_index = day_timestamps.index(exit_timestamp)

    for timestamp in day_timestamps[entry_index + 1 : exit_index]:
        current_row = evaluation.contract_data.rows_by_timestamp.get(timestamp)
        if current_row is None:
            return SideExitOutcome(
                exit_row=None,
                exit_reason="",
                failure_reason="entered_side_missing_timestamp",
                failure_remarks=(
                    f"{evaluation.contract_path.name} missing monitoring timestamp {timestamp} "
                    f"after {entry_timestamp}"
                ),
            )

        current_sma, _ = compute_prior_sma(evaluation.contract_data, timestamp, ma_period)
        if current_sma is None:
            return SideExitOutcome(
                exit_row=None,
                exit_reason="",
                failure_reason="entered_side_insufficient_history",
                failure_remarks=(
                    f"{evaluation.contract_path.name} does not have {ma_period} prior bars at {timestamp}"
                ),
            )

        if current_row.open_value > current_sma:
            return SideExitOutcome(
                exit_row=current_row,
                exit_reason="stop_loss_ma_cross",
                failure_reason="",
                failure_remarks="",
            )

    exit_row = evaluation.contract_data.rows_by_timestamp.get(exit_timestamp)
    if exit_row is None:
        return SideExitOutcome(
            exit_row=None,
            exit_reason="",
            failure_reason="entered_side_missing_timestamp",
            failure_remarks=f"{evaluation.contract_path.name} missing scheduled exit timestamp {exit_timestamp}",
        )

    return SideExitOutcome(
        exit_row=exit_row,
        exit_reason="day_close",
        failure_reason="",
        failure_remarks="",
    )


def make_result(
    entry_date: str,
    status: str,
    skip_reason: str,
    expiry_date: str,
    spot_entry_timestamp: str,
    spot_entry_open: str,
    atm_strike: str,
    ce_evaluation: SideEvaluation,
    pe_evaluation: SideEvaluation,
    ce_exit: Optional[SideExitOutcome],
    pe_exit: Optional[SideExitOutcome],
    legs_traded: int,
    orders_executed: int,
    gross_pnl: float,
    brokerage: float,
    net_pnl: float,
    remarks: str,
) -> TradeResult:
    ce_entry_timestamp = ce_evaluation.entry_row.timestamp if ce_evaluation.signal_status == "TRADED" and ce_evaluation.entry_row else ""
    ce_entry_open = ce_evaluation.entry_row.open_text if ce_evaluation.signal_status == "TRADED" and ce_evaluation.entry_row else ""
    pe_entry_timestamp = pe_evaluation.entry_row.timestamp if pe_evaluation.signal_status == "TRADED" and pe_evaluation.entry_row else ""
    pe_entry_open = pe_evaluation.entry_row.open_text if pe_evaluation.signal_status == "TRADED" and pe_evaluation.entry_row else ""

    return TradeResult(
        entry_date=entry_date,
        status=status,
        skip_reason=skip_reason,
        expiry_date=expiry_date,
        spot_entry_timestamp=spot_entry_timestamp,
        spot_entry_open=spot_entry_open,
        atm_strike=atm_strike,
        ce_signal_status=ce_evaluation.signal_status,
        ce_entry_sma=format_optional_money(ce_evaluation.entry_sma),
        ce_entry_timestamp=ce_entry_timestamp,
        ce_entry_open=ce_entry_open,
        ce_exit_timestamp=ce_exit.exit_row.timestamp if ce_exit and ce_exit.exit_row else "",
        ce_exit_open=ce_exit.exit_row.open_text if ce_exit and ce_exit.exit_row else "",
        ce_exit_reason=ce_exit.exit_reason if ce_exit else "",
        pe_signal_status=pe_evaluation.signal_status,
        pe_entry_sma=format_optional_money(pe_evaluation.entry_sma),
        pe_entry_timestamp=pe_entry_timestamp,
        pe_entry_open=pe_entry_open,
        pe_exit_timestamp=pe_exit.exit_row.timestamp if pe_exit and pe_exit.exit_row else "",
        pe_exit_open=pe_exit.exit_row.open_text if pe_exit and pe_exit.exit_row else "",
        pe_exit_reason=pe_exit.exit_reason if pe_exit else "",
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

    trading_days, spot_rows_by_day, timestamps_by_day = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    contract_cache: Dict[Path, ContractData] = {}
    results: List[TradeResult] = []
    contract_multiplier = args.lot_size * args.lots

    try:
        for entry_date in trading_days:
            entry_timestamp = build_timestamp(entry_date, args.entry_time)
            exit_timestamp = build_timestamp(entry_date, args.exit_time)
            spot_rows = spot_rows_by_day[entry_date]
            day_timestamps = timestamps_by_day[entry_date]

            if entry_timestamp not in spot_rows or exit_timestamp not in spot_rows:
                remarks = join_remarks(
                    [
                        f"Missing spot entry timestamp {entry_timestamp}"
                        if entry_timestamp not in spot_rows
                        else "",
                        f"Missing spot exit timestamp {exit_timestamp}"
                        if exit_timestamp not in spot_rows
                        else "",
                    ]
                )
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="missing_spot_timestamp",
                    expiry_date="",
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open="",
                    atm_strike="",
                    ce_evaluation=SideEvaluation("CE", "MISSING_TIMESTAMP", "", Path(""), None, None, None),
                    pe_evaluation=SideEvaluation("PE", "MISSING_TIMESTAMP", "", Path(""), None, None, None),
                    ce_exit=None,
                    pe_exit=None,
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
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_rows[entry_timestamp].open_text,
                    atm_strike="",
                    ce_evaluation=SideEvaluation("CE", "MISSING_FILE", "", Path(""), None, None, None),
                    pe_evaluation=SideEvaluation("PE", "MISSING_FILE", "", Path(""), None, None, None),
                    ce_exit=None,
                    pe_exit=None,
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

            spot_entry_row = spot_rows[entry_timestamp]
            atm_strike = round_to_nearest_50(spot_entry_row.open_value)
            strike_text = str(atm_strike)
            option_suffix = expiry_suffix(expiry_date)
            ce_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_CE_{option_suffix}.csv"
            pe_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_PE_{option_suffix}.csv"

            ce_evaluation = evaluate_side_entry(
                side="CE",
                contract_path=ce_path,
                entry_timestamp=entry_timestamp,
                ma_period=args.ma_period,
                contract_cache=contract_cache,
            )
            pe_evaluation = evaluate_side_entry(
                side="PE",
                contract_path=pe_path,
                entry_timestamp=entry_timestamp,
                ma_period=args.ma_period,
                contract_cache=contract_cache,
            )

            ce_unavailable = ce_evaluation.signal_status in UNAVAILABLE_STATUSES
            pe_unavailable = pe_evaluation.signal_status in UNAVAILABLE_STATUSES
            entered_evaluations = [
                evaluation
                for evaluation in (ce_evaluation, pe_evaluation)
                if evaluation.signal_status == "TRADED"
            ]

            if not entered_evaluations:
                skip_reason = "both_sides_unavailable" if ce_unavailable and pe_unavailable else "no_entry_signal"
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason=skip_reason,
                    expiry_date=expiry_date,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    atm_strike=strike_text,
                    ce_evaluation=ce_evaluation,
                    pe_evaluation=pe_evaluation,
                    ce_exit=None,
                    pe_exit=None,
                    legs_traded=0,
                    orders_executed=0,
                    gross_pnl=0.0,
                    brokerage=0.0,
                    net_pnl=0.0,
                    remarks=join_remarks([ce_evaluation.remarks, pe_evaluation.remarks]),
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

            ce_exit: Optional[SideExitOutcome] = None
            pe_exit: Optional[SideExitOutcome] = None
            exit_failures: List[str] = []

            if ce_evaluation.signal_status == "TRADED":
                ce_exit = resolve_side_exit(
                    evaluation=ce_evaluation,
                    day_timestamps=day_timestamps,
                    entry_timestamp=entry_timestamp,
                    exit_timestamp=exit_timestamp,
                    ma_period=args.ma_period,
                )
                if ce_exit.failure_reason:
                    exit_failures.append(ce_exit.failure_remarks)

            if pe_evaluation.signal_status == "TRADED":
                pe_exit = resolve_side_exit(
                    evaluation=pe_evaluation,
                    day_timestamps=day_timestamps,
                    entry_timestamp=entry_timestamp,
                    exit_timestamp=exit_timestamp,
                    ma_period=args.ma_period,
                )
                if pe_exit.failure_reason:
                    exit_failures.append(pe_exit.failure_remarks)

            if exit_failures:
                failure_reasons = [
                    outcome.failure_reason
                    for outcome in (ce_exit, pe_exit)
                    if outcome and outcome.failure_reason
                ]
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason=failure_reasons[0] if failure_reasons else "entered_side_missing_timestamp",
                    expiry_date=expiry_date,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    atm_strike=strike_text,
                    ce_evaluation=ce_evaluation,
                    pe_evaluation=pe_evaluation,
                    ce_exit=ce_exit,
                    pe_exit=pe_exit,
                    legs_traded=len(entered_evaluations),
                    orders_executed=0,
                    gross_pnl=0.0,
                    brokerage=0.0,
                    net_pnl=0.0,
                    remarks=join_remarks([ce_evaluation.remarks, pe_evaluation.remarks] + exit_failures),
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

            gross_pnl = 0.0
            if ce_evaluation.signal_status == "TRADED" and ce_exit and ce_evaluation.entry_row and ce_exit.exit_row:
                gross_pnl += (
                    leg_pnl_after_slippage(
                        ce_evaluation.entry_row.open_value - ce_exit.exit_row.open_value,
                        args.slippage_points_per_order,
                    )
                    * contract_multiplier
                )
            if pe_evaluation.signal_status == "TRADED" and pe_exit and pe_evaluation.entry_row and pe_exit.exit_row:
                gross_pnl += (
                    leg_pnl_after_slippage(
                        pe_evaluation.entry_row.open_value - pe_exit.exit_row.open_value,
                        args.slippage_points_per_order,
                    )
                    * contract_multiplier
                )

            orders_executed = 2 * len(entered_evaluations)
            brokerage = orders_executed * args.brokerage_per_order
            net_pnl = gross_pnl - brokerage
            result = make_result(
                entry_date=entry_date,
                status="TRADED",
                skip_reason="",
                expiry_date=expiry_date,
                spot_entry_timestamp=entry_timestamp,
                spot_entry_open=spot_entry_row.open_text,
                atm_strike=strike_text,
                ce_evaluation=ce_evaluation,
                pe_evaluation=pe_evaluation,
                ce_exit=ce_exit,
                pe_exit=pe_exit,
                legs_traded=len(entered_evaluations),
                orders_executed=orders_executed,
                gross_pnl=gross_pnl,
                brokerage=brokerage,
                net_pnl=net_pnl,
                remarks=join_remarks([ce_evaluation.remarks, pe_evaluation.remarks]),
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
        "# 2025 15-Minute Same-Week ATM MA Short Options Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Entry time: `{args.entry_time}`",
        f"- Exit time: `{args.exit_time}`",
        "- Spot ATM rule: nearest 50 using the NIFTY 09:30 open",
        "- Expiry rule: first expiry folder on or after the trade date",
        f"- Signal rule: option 09:30 open below prior {args.ma_period}-close SMA",
        f"- Stop rule: later bar open above prior {args.ma_period}-close SMA",
        "- MA source: option close",
        "- Re-entry rule: none",
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
            "- This strategy uses the 15-minute NIFTY spot file and the derived 15-minute options dataset.",
            "- `15:15` is the end-of-day execution proxy because the dataset does not contain an exact `15:20` timestamp.",
            "- Expiry folder dates are used as truth, which naturally handles Tuesday special expiries.",
            "- One side may trade even if the other side is unavailable or has no signal.",
            "- No intraday re-entry is allowed after a side exits.",
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
