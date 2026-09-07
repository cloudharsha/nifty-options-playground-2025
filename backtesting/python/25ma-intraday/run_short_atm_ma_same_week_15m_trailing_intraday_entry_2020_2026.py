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
DAYWISE_FILENAME = "short_atm_ma_same_week_15m_trailing_intraday_entry_2020_2026_daywise.csv"
SUMMARY_FILENAME = "short_atm_ma_same_week_15m_trailing_intraday_entry_2020_2026_summary.md"
LOG_FILENAME = "short_atm_ma_same_week_15m_trailing_intraday_entry_2020_2026.log"
UNAVAILABLE_STATUSES = {"MISSING_FILE", "MISSING_TIMESTAMP"}
LEG_STATE_PENDING = "PENDING"
LEG_STATE_ACTIVE = "ACTIVE"
LEG_STATE_CLOSED = "CLOSED"
LEG_STATE_UNAVAILABLE = "UNAVAILABLE"
CAPITAL_FOR_CAGR = 10_00_000.0  # Rs 10L reference base


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
    lot_size: str
    lots: str
    qty: str
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


def qty_for_expiry(expiry_date: str) -> Tuple[int, int]:
    """Return (lot_size, lots) targeting ~300 quantity, per NIFTY lot size history."""
    if expiry_date < "2021-10-07":
        return 75, 4   # 300
    if expiry_date <= "2024-04-25":
        return 50, 6   # 300
    if expiry_date <= "2024-11-21":
        return 25, 12  # 300
    if expiry_date <= "2025-12-30":
        return 75, 4   # 300
    return 65, 5       # 325


def compute_cagr(net_total: float, capital: float, first_day: str, last_day: str) -> float:
    start = datetime.date.fromisoformat(first_day)
    end = datetime.date.fromisoformat(last_day)
    days = (end - start).days
    if days <= 0 or capital <= 0:
        return 0.0
    return ((1.0 + net_total / capital) ** (365.25 / days) - 1.0) * 100.0


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Backtest 2020-2026 same-week ATM short option strategy using a 15-minute "
            "trailing option SMA stop with intraday first-entry monitoring."
        ),
    )
    parser.add_argument("--spot-file", type=Path,
                        default=repo_root / "nifty" / "NIFTY50_INDEX_15m_last_7y.csv")
    parser.add_argument("--options-dir", type=Path,
                        default=repo_root / "NiftyOptions_2020_2026" / "Options")
    parser.add_argument("--results-dir", type=Path,
                        default=repo_root / "backtesting" / "results")
    parser.add_argument("--entry-start-time", default="09:30")
    parser.add_argument("--last-entry-time", default="15:00")
    parser.add_argument("--exit-time", default="15:15")
    parser.add_argument("--ma-period", type=int, default=25)
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
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
    cur = start_dt
    while cur <= end_dt:
        timestamps.append(cur.strftime("%Y-%m-%dT%H:%M:00") + IST_SUFFIX)
        cur += datetime.timedelta(minutes=15)
    return timestamps


def round_to_nearest_50(price: float) -> int:
    remainder = price % 50
    rounded_down = int(price - remainder)
    return rounded_down if remainder < 25 else rounded_down + 50


def format_money(value: float) -> str:
    return f"{value:.2f}"


def format_optional_money(value: Optional[float]) -> str:
    return "" if value is None else format_money(value)


def leg_pnl_after_slippage(raw_pts: float, slip: float) -> float:
    return raw_pts - (2 * slip)


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("short_atm_ma_same_week_15m_trailing_intraday_entry_2020_2026")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def join_remarks(parts: List[str]) -> str:
    return "; ".join(p for p in parts if p)


def load_spot_data(spot_file: Path) -> Tuple[List[str], Dict[str, Dict[str, PriceRow]]]:
    trading_days: List[str] = []
    rows_by_day: Dict[str, Dict[str, PriceRow]] = {}

    with spot_file.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            ts = row["timestamp"]
            day = ts[:10]
            if day not in rows_by_day:
                rows_by_day[day] = {}
                trading_days.append(day)
            rows_by_day[day][ts] = PriceRow(
                timestamp=ts,
                open_value=float(row["open"]), open_text=row["open"],
                close_value=float(row["close"]), close_text=row["close"],
            )

    return trading_days, rows_by_day


def load_expiry_folders(options_dir: Path) -> List[str]:
    return sorted(p.name for p in options_dir.iterdir() if p.is_dir())


def first_expiry_on_or_after(expiries: List[str], entry_date: str) -> Optional[str]:
    for expiry in expiries:
        if expiry >= entry_date:
            return expiry
    return None


def expiry_suffix(expiry_date: str) -> str:
    return datetime.datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%d_%b_%y").upper()


def load_contract(contract_path: Path, cache: Dict[Path, ContractData]) -> Optional[ContractData]:
    """Load option contract, sampling 1m data at 15m boundaries (minute % 15 == 0)."""
    if contract_path in cache:
        return cache[contract_path]
    if not contract_path.exists():
        return None

    rows_by_ts: Dict[str, PriceRow] = {}
    ordered: List[PriceRow] = []
    idx_by_ts: Dict[str, int] = {}

    with contract_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            ts = row["timestamp"]
            # Sample only at 15-minute boundaries (09:15, 09:30, 09:45 ...)
            minute = int(ts[14:16])
            if minute % 15 != 0:
                continue
            pr = PriceRow(
                timestamp=ts,
                open_value=float(row["open"]), open_text=row["open"],
                close_value=float(row["close"]), close_text=row["close"],
            )
            idx_by_ts[ts] = len(ordered)
            ordered.append(pr)
            rows_by_ts[ts] = pr

    cd = ContractData(path=contract_path, rows_by_timestamp=rows_by_ts,
                      ordered_rows=ordered, index_by_timestamp=idx_by_ts)
    cache[contract_path] = cd
    return cd


def compute_prior_sma(contract_data: ContractData, timestamp: str, ma_period: int) -> Tuple[Optional[float], int]:
    idx = contract_data.index_by_timestamp.get(timestamp)
    if idx is None:
        return None, 0
    if idx < ma_period:
        return None, idx
    window = contract_data.ordered_rows[idx - ma_period: idx]
    sma = sum(r.close_value for r in window) / ma_period
    return sma, idx


def first_missing_timestamp(rows_by_ts: Dict[str, PriceRow], required: List[str]) -> Optional[str]:
    for ts in required:
        if ts not in rows_by_ts:
            return ts
    return None


def placeholder_leg_state(side: str, signal_status: str, remarks: str = "") -> LegState:
    return LegState(side=side, contract_path=Path(""), contract_data=None,
                    signal_status=signal_status, remarks=remarks,
                    entry_row=None, entry_sma=None, exit_outcome=None,
                    state=LEG_STATE_UNAVAILABLE, saw_valid_sma=False, last_prior_count=0)


def initialize_leg_state(side: str, contract_path: Path, required_timestamps: List[str],
                          contract_cache: Dict[Path, ContractData]) -> LegState:
    cd = load_contract(contract_path, contract_cache)
    if cd is None:
        return LegState(side=side, contract_path=contract_path, contract_data=None,
                        signal_status="MISSING_FILE",
                        remarks=f"Missing option file: {contract_path.name}",
                        entry_row=None, entry_sma=None, exit_outcome=None,
                        state=LEG_STATE_UNAVAILABLE, saw_valid_sma=False, last_prior_count=0)

    missing = first_missing_timestamp(cd.rows_by_timestamp, required_timestamps)
    if missing is not None:
        remarks = (f"{contract_path.name} is header-only" if not cd.ordered_rows
                   else f"{contract_path.name} missing monitoring timestamp {missing}")
        return LegState(side=side, contract_path=contract_path, contract_data=cd,
                        signal_status="MISSING_TIMESTAMP", remarks=remarks,
                        entry_row=None, entry_sma=None, exit_outcome=None,
                        state=LEG_STATE_UNAVAILABLE, saw_valid_sma=False, last_prior_count=0)

    return LegState(side=side, contract_path=contract_path, contract_data=cd,
                    signal_status="", remarks="", entry_row=None, entry_sma=None,
                    exit_outcome=None, state=LEG_STATE_PENDING, saw_valid_sma=False,
                    last_prior_count=0)


def evaluate_pending_leg_entry(leg: LegState, timestamp: str, ma_period: int) -> None:
    if leg.state != LEG_STATE_PENDING or leg.contract_data is None:
        return
    row = leg.contract_data.rows_by_timestamp[timestamp]
    sma, prior_count = compute_prior_sma(leg.contract_data, timestamp, ma_period)
    leg.last_prior_count = prior_count
    if sma is None:
        return
    leg.saw_valid_sma = True
    if row.open_value < sma:
        leg.signal_status = "TRADED"
        leg.entry_row = row
        leg.entry_sma = sma
        leg.state = LEG_STATE_ACTIVE


def evaluate_active_leg_exit(leg: LegState, timestamp: str, ma_period: int) -> None:
    if leg.state != LEG_STATE_ACTIVE or leg.contract_data is None or leg.entry_row is None:
        return
    row = leg.contract_data.rows_by_timestamp.get(timestamp)
    if row is None:
        leg.exit_outcome = SideExitOutcome(
            exit_row=None, exit_reason="",
            failure_reason="entered_side_missing_timestamp",
            failure_remarks=(f"{leg.contract_path.name} missing monitoring timestamp {timestamp} "
                             f"after {leg.entry_row.timestamp}"))
        leg.state = LEG_STATE_CLOSED
        return
    sma, _ = compute_prior_sma(leg.contract_data, timestamp, ma_period)
    if sma is None:
        leg.exit_outcome = SideExitOutcome(
            exit_row=None, exit_reason="",
            failure_reason="entered_side_insufficient_history",
            failure_remarks=f"{leg.contract_path.name} does not have {ma_period} prior bars at {timestamp}")
        leg.state = LEG_STATE_CLOSED
        return
    if row.open_value > sma:
        leg.exit_outcome = SideExitOutcome(exit_row=row, exit_reason="stop_loss_ma_cross",
                                            failure_reason="", failure_remarks="")
        leg.state = LEG_STATE_CLOSED


def force_day_close_exit(leg: LegState, exit_timestamp: str) -> None:
    if leg.state != LEG_STATE_ACTIVE or leg.contract_data is None:
        return
    row = leg.contract_data.rows_by_timestamp.get(exit_timestamp)
    if row is None:
        leg.exit_outcome = SideExitOutcome(
            exit_row=None, exit_reason="",
            failure_reason="entered_side_missing_timestamp",
            failure_remarks=f"{leg.contract_path.name} missing scheduled exit timestamp {exit_timestamp}")
        leg.state = LEG_STATE_CLOSED
        return
    leg.exit_outcome = SideExitOutcome(exit_row=row, exit_reason="day_close",
                                        failure_reason="", failure_remarks="")
    leg.state = LEG_STATE_CLOSED


def finalize_pending_leg(leg: LegState, entry_start_time: str, last_entry_time: str,
                          ma_period: int) -> None:
    if leg.state != LEG_STATE_PENDING:
        return
    if leg.saw_valid_sma:
        leg.signal_status = "NO_SIGNAL"
        leg.remarks = (f"{leg.contract_path.name} had no qualifying bar with open below prior "
                       f"{ma_period}-close SMA between {entry_start_time} and {last_entry_time}")
    else:
        leg.signal_status = "INSUFFICIENT_HISTORY"
        leg.remarks = (f"{leg.contract_path.name} never had {ma_period} prior bars by {last_entry_time}; "
                       f"max prior bars observed was {leg.last_prior_count}")
    leg.state = LEG_STATE_CLOSED


def make_result(entry_date: str, status: str, skip_reason: str, expiry_date: str,
                lot_size: int, lots: int,
                spot_entry_timestamp: str, spot_entry_open: str, atm_strike: str,
                ce_leg: LegState, pe_leg: LegState,
                legs_traded: int, orders_executed: int,
                gross_pnl: float, brokerage: float, net_pnl: float,
                remarks: str) -> TradeResult:
    ce_entered = ce_leg.signal_status == "TRADED" and ce_leg.entry_row is not None
    pe_entered = pe_leg.signal_status == "TRADED" and pe_leg.entry_row is not None
    return TradeResult(
        entry_date=entry_date, status=status, skip_reason=skip_reason, expiry_date=expiry_date,
        lot_size=str(lot_size), lots=str(lots), qty=str(lot_size * lots),
        spot_entry_timestamp=spot_entry_timestamp, spot_entry_open=spot_entry_open,
        atm_strike=atm_strike,
        ce_signal_status=ce_leg.signal_status,
        ce_entry_sma=format_optional_money(ce_leg.entry_sma if ce_entered else None),
        ce_entry_timestamp=ce_leg.entry_row.timestamp if ce_entered else "",
        ce_entry_open=ce_leg.entry_row.open_text if ce_entered else "",
        ce_exit_timestamp=(ce_leg.exit_outcome.exit_row.timestamp
                           if ce_leg.exit_outcome and ce_leg.exit_outcome.exit_row else ""),
        ce_exit_open=(ce_leg.exit_outcome.exit_row.open_text
                      if ce_leg.exit_outcome and ce_leg.exit_outcome.exit_row else ""),
        ce_exit_reason=ce_leg.exit_outcome.exit_reason if ce_leg.exit_outcome else "",
        pe_signal_status=pe_leg.signal_status,
        pe_entry_sma=format_optional_money(pe_leg.entry_sma if pe_entered else None),
        pe_entry_timestamp=pe_leg.entry_row.timestamp if pe_entered else "",
        pe_entry_open=pe_leg.entry_row.open_text if pe_entered else "",
        pe_exit_timestamp=(pe_leg.exit_outcome.exit_row.timestamp
                           if pe_leg.exit_outcome and pe_leg.exit_outcome.exit_row else ""),
        pe_exit_open=(pe_leg.exit_outcome.exit_row.open_text
                      if pe_leg.exit_outcome and pe_leg.exit_outcome.exit_row else ""),
        pe_exit_reason=pe_leg.exit_outcome.exit_reason if pe_leg.exit_outcome else "",
        legs_traded=str(legs_traded), orders_executed=str(orders_executed),
        gross_pnl=format_money(gross_pnl), brokerage=format_money(brokerage),
        net_pnl=format_money(net_pnl), remarks=remarks,
    )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, spot_rows_by_day = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    contract_cache: Dict[Path, ContractData] = {}
    results: List[TradeResult] = []

    try:
        for entry_date in trading_days:
            reference_ts = build_timestamp(entry_date, args.entry_start_time)
            exit_ts = build_timestamp(entry_date, args.exit_time)
            spot_rows = spot_rows_by_day[entry_date]
            monitoring_timestamps = build_intraday_timestamps(entry_date, args.entry_start_time, args.exit_time)
            entry_timestamps = build_intraday_timestamps(entry_date, args.entry_start_time, args.last_entry_time)
            entry_ts_set = set(entry_timestamps)

            missing_spot = [ts for ts in monitoring_timestamps if ts not in spot_rows]
            if missing_spot:
                result = make_result(
                    entry_date=entry_date, status="SKIPPED", skip_reason="missing_spot_timestamp",
                    expiry_date="", lot_size=0, lots=0,
                    spot_entry_timestamp=reference_ts,
                    spot_entry_open=spot_rows[reference_ts].open_text if reference_ts in spot_rows else "",
                    atm_strike="",
                    ce_leg=placeholder_leg_state("CE", "MISSING_TIMESTAMP"),
                    pe_leg=placeholder_leg_state("PE", "MISSING_TIMESTAMP"),
                    legs_traded=0, orders_executed=0, gross_pnl=0.0, brokerage=0.0, net_pnl=0.0,
                    remarks="Missing spot monitoring timestamps: " + ", ".join(missing_spot[:5]),
                )
                results.append(result)
                continue

            expiry_date = first_expiry_on_or_after(expiries, entry_date)
            if expiry_date is None:
                result = make_result(
                    entry_date=entry_date, status="SKIPPED", skip_reason="no_same_week_expiry",
                    expiry_date="", lot_size=0, lots=0,
                    spot_entry_timestamp=reference_ts,
                    spot_entry_open=spot_rows[reference_ts].open_text,
                    atm_strike="",
                    ce_leg=placeholder_leg_state("CE", "MISSING_FILE"),
                    pe_leg=placeholder_leg_state("PE", "MISSING_FILE"),
                    legs_traded=0, orders_executed=0, gross_pnl=0.0, brokerage=0.0, net_pnl=0.0,
                    remarks="No expiry folder exists on or after this trade date.",
                )
                results.append(result)
                continue

            lot_size, lots = qty_for_expiry(expiry_date)
            contract_multiplier = lot_size * lots
            spot_ref_row = spot_rows[reference_ts]
            atm = round_to_nearest_50(spot_ref_row.open_value)
            strike_text = str(atm)
            suffix = expiry_suffix(expiry_date)
            ce_path = args.options_dir / expiry_date / f"NIFTY_{atm}_CE_{suffix}.csv"
            pe_path = args.options_dir / expiry_date / f"NIFTY_{atm}_PE_{suffix}.csv"

            ce_leg = initialize_leg_state("CE", ce_path, monitoring_timestamps, contract_cache)
            pe_leg = initialize_leg_state("PE", pe_path, monitoring_timestamps, contract_cache)

            for ts in monitoring_timestamps:
                if ts != exit_ts:
                    for leg in (ce_leg, pe_leg):
                        if (leg.state == LEG_STATE_ACTIVE and leg.entry_row is not None
                                and ts != leg.entry_row.timestamp):
                            evaluate_active_leg_exit(leg, ts, args.ma_period)
                if ts in entry_ts_set:
                    for leg in (ce_leg, pe_leg):
                        if leg.state == LEG_STATE_PENDING:
                            evaluate_pending_leg_entry(leg, ts, args.ma_period)

            for leg in (ce_leg, pe_leg):
                if leg.state == LEG_STATE_ACTIVE:
                    force_day_close_exit(leg, exit_ts)
                if leg.state == LEG_STATE_PENDING:
                    finalize_pending_leg(leg, args.entry_start_time, args.last_entry_time, args.ma_period)

            exit_failures = [
                leg.exit_outcome.failure_remarks
                for leg in (ce_leg, pe_leg)
                if leg.exit_outcome and leg.exit_outcome.failure_reason
            ]
            entered_legs = [leg for leg in (ce_leg, pe_leg) if leg.signal_status == "TRADED"]

            if exit_failures:
                failure_reasons = [leg.exit_outcome.failure_reason for leg in (ce_leg, pe_leg)
                                   if leg.exit_outcome and leg.exit_outcome.failure_reason]
                result = make_result(
                    entry_date=entry_date, status="SKIPPED",
                    skip_reason=failure_reasons[0] if failure_reasons else "entered_side_missing_timestamp",
                    expiry_date=expiry_date, lot_size=lot_size, lots=lots,
                    spot_entry_timestamp=reference_ts, spot_entry_open=spot_ref_row.open_text,
                    atm_strike=strike_text, ce_leg=ce_leg, pe_leg=pe_leg,
                    legs_traded=len(entered_legs), orders_executed=0,
                    gross_pnl=0.0, brokerage=0.0, net_pnl=0.0,
                    remarks=join_remarks([ce_leg.remarks, pe_leg.remarks] + exit_failures),
                )
                results.append(result)
                logger.info("SKIPPED date=%s expiry=%s strike=%s reason=%s lot=%sx%s",
                            entry_date, expiry_date, strike_text, result.skip_reason, lot_size, lots)
                continue

            if not entered_legs:
                both_unavail = (ce_leg.signal_status in UNAVAILABLE_STATUSES
                                and pe_leg.signal_status in UNAVAILABLE_STATUSES)
                skip_reason = "both_sides_unavailable" if both_unavail else "no_entry_signal"
                result = make_result(
                    entry_date=entry_date, status="SKIPPED", skip_reason=skip_reason,
                    expiry_date=expiry_date, lot_size=lot_size, lots=lots,
                    spot_entry_timestamp=reference_ts, spot_entry_open=spot_ref_row.open_text,
                    atm_strike=strike_text, ce_leg=ce_leg, pe_leg=pe_leg,
                    legs_traded=0, orders_executed=0, gross_pnl=0.0, brokerage=0.0, net_pnl=0.0,
                    remarks=join_remarks([ce_leg.remarks, pe_leg.remarks]),
                )
                results.append(result)
                logger.info("SKIPPED date=%s expiry=%s strike=%s reason=%s",
                            entry_date, expiry_date, strike_text, skip_reason)
                continue

            gross_pnl = 0.0
            for leg in entered_legs:
                if leg.entry_row is None or leg.exit_outcome is None or leg.exit_outcome.exit_row is None:
                    continue
                gross_pnl += (leg_pnl_after_slippage(
                    leg.entry_row.open_value - leg.exit_outcome.exit_row.open_value,
                    args.slippage_points_per_order) * contract_multiplier)

            orders_executed = 2 * len(entered_legs)
            brokerage = orders_executed * args.brokerage_per_order
            net_pnl = gross_pnl - brokerage
            result = make_result(
                entry_date=entry_date, status="TRADED", skip_reason="",
                expiry_date=expiry_date, lot_size=lot_size, lots=lots,
                spot_entry_timestamp=reference_ts, spot_entry_open=spot_ref_row.open_text,
                atm_strike=strike_text, ce_leg=ce_leg, pe_leg=pe_leg,
                legs_traded=len(entered_legs), orders_executed=orders_executed,
                gross_pnl=gross_pnl, brokerage=brokerage, net_pnl=net_pnl,
                remarks=join_remarks([ce_leg.remarks, pe_leg.remarks]),
            )
            results.append(result)
            logger.info("TRADED date=%s expiry=%s strike=%s legs=%s lot=%sx%s gross=%s net=%s",
                        entry_date, expiry_date, strike_text, result.legs_traded,
                        lot_size, lots, result.gross_pnl, result.net_pnl)

    except Exception:
        logger.exception("ERROR unexpected failure")
        raise

    traded = sum(1 for r in results if r.status == "TRADED")
    skipped = sum(1 for r in results if r.status == "SKIPPED")
    logger.info("COMPLETED traded=%s skipped=%s total=%s", traded, skipped, len(results))
    return results


def write_daywise_csv(results: List[TradeResult], path: Path) -> None:
    fields = [f.name for f in TradeResult.__dataclass_fields__.values()]
    with path.open("w", encoding="utf-8", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow(r.__dict__)


def compute_max_drawdown(vals: List[float]) -> float:
    peak = dd = cum = 0.0
    for v in vals:
        cum += v; peak = max(peak, cum); dd = max(dd, peak - cum)
    return dd


def write_summary(results: List[TradeResult], path: Path, args: argparse.Namespace) -> None:
    traded = [r for r in results if r.status == "TRADED"]
    skipped = [r for r in results if r.status == "SKIPPED"]
    gross = sum(float(r.gross_pnl) for r in traded)
    brok = sum(float(r.brokerage) for r in traded)
    net = sum(float(r.net_pnl) for r in traded)
    vals = [float(r.net_pnl) for r in traded]
    wins = sum(1 for v in vals if v > 0)
    losses = sum(1 for v in vals if v < 0)
    dd = compute_max_drawdown(vals)
    best = max(traded, key=lambda r: float(r.net_pnl), default=None)
    worst = min(traded, key=lambda r: float(r.net_pnl), default=None)
    ce_only = sum(1 for r in traded if r.ce_signal_status == "TRADED" and r.pe_signal_status != "TRADED")
    pe_only = sum(1 for r in traded if r.pe_signal_status == "TRADED" and r.ce_signal_status != "TRADED")
    both_legs = sum(1 for r in traded if r.legs_traded == "2")
    first_day = results[0].entry_date if results else ""
    last_day = results[-1].entry_date if results else ""
    cagr = compute_cagr(net, CAPITAL_FOR_CAGR, first_day, last_day) if first_day and last_day else 0.0

    lines: List[str] = [
        "# 15-Minute Same-Week ATM MA Short Options Backtest With Intraday First Entry (2020-2026)",
        "",
        "## Strategy Details",
        "",
        f"- ATM reference time: `{args.entry_start_time}`",
        f"- Last fresh-entry time: `{args.last_entry_time}`",
        f"- Exit time: `{args.exit_time}`",
        f"- Spot ATM rule: fixed nearest 50 using the NIFTY {args.entry_start_time} open",
        "- Expiry rule: first expiry folder on or after the trade date",
        (f"- Entry rule: monitor fixed {args.entry_start_time} ATM CE and PE independently from "
         f"{args.entry_start_time} through {args.last_entry_time}; "
         f"sell the first bar whose open is below the prior {args.ma_period}-close SMA"),
        (f"- Trailing stop rule: every later 15-minute bar recalculates the prior "
         f"{args.ma_period}-close SMA; exit when that bar open is above the updated SMA"),
        "- MA source: option close (15-minute sampled from 1-minute data for 2020-2026)",
        "- Re-entry rule: each leg may trade at most once per day",
        "- Pricing rule: exact option open price at exact 15-minute boundary timestamps",
        "- Quantity: ~300 per trade (dynamic lot sizing by expiry era)",
        "  - pre-2021-10-07: 75x4=300 | 2021-10-07-2024-04-25: 50x6=300",
        "  - 2024-04-26-2024-11-21: 25x12=300 | 2024-11-22-2025-12-30: 75x4=300",
        "  - 2026+: 65x5=325",
        f"- Slippage: {format_money(args.slippage_points_per_order)} pt/order",
        f"- Brokerage: Rs {int(args.brokerage_per_order)}/order",
        f"- Capital reference (CAGR): Rs {int(CAPITAL_FOR_CAGR):,}",
        f"- Data range: `{first_day}` to `{last_day}`" if first_day else "",
        "",
        "## Results Summary",
        "",
        f"- Traded days: `{len(traded)}`",
        f"- Skipped days: `{len(skipped)}`",
        f"- CE-only trade count: `{ce_only}`",
        f"- PE-only trade count: `{pe_only}`",
        f"- Both-legs trade count: `{both_legs}`",
        f"- Winning days: `{wins}`",
        f"- Losing days: `{losses}`",
        f"- Max drawdown: `{format_money(dd)}`",
        f"- Best day: `{best.entry_date}` net `{best.net_pnl}`" if best else "- Best day: N/A",
        f"- Worst day: `{worst.entry_date}` net `{worst.net_pnl}`" if worst else "- Worst day: N/A",
        f"- Total Profit/Loss: `{format_money(net)}`",
        f"- Total Brokerage: `{format_money(brok)}`",
        f"- Gross P/L: `{format_money(gross)}`",
        f"- CAGR (on Rs {int(CAPITAL_FOR_CAGR):,}): `{cagr:.2f}%`",
        "",
        "## Yearly Summary",
        "",
        "| Year | Traded | CE-only | PE-only | Both | Wins | Losses | Win% | Net P/L |",
        "|------|--------|---------|---------|------|------|--------|------|---------|",
    ]

    years: Dict[str, List] = {}
    for r in traded:
        y = r.entry_date[:4]
        years.setdefault(y, []).append(r)
    for y in sorted(years):
        yr = years[y]
        yv = [float(r.net_pnl) for r in yr]
        yw = sum(1 for v in yv if v > 0)
        yl = sum(1 for v in yv if v < 0)
        pct = yw / len(yv) * 100 if yv else 0.0
        yco = sum(1 for r in yr if r.ce_signal_status == "TRADED" and r.pe_signal_status != "TRADED")
        ypo = sum(1 for r in yr if r.pe_signal_status == "TRADED" and r.ce_signal_status != "TRADED")
        ybo = sum(1 for r in yr if r.legs_traded == "2")
        lines.append(f"| {y} | {len(yr)} | {yco} | {ypo} | {ybo} | {yw} | {yl} | {pct:.1f}% | {format_money(sum(yv))} |")

    lines.extend(["", "## Exceptions", ""])
    if skipped:
        for r in skipped:
            lines.append(f"- `{r.entry_date}`: `{r.skip_reason}`. {r.remarks}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Remarks",
        "",
        "- Exact timestamp matching; no nearest-candle fallback.",
        f"- ATM is fixed from the {args.entry_start_time} spot open and does not roll intraday.",
        "- CE and PE are monitored independently; both can trade on the same day.",
        "- Option data is 1-minute CSVs sampled at 15-minute boundaries (minute % 15 == 0).",
        "- The close at each 15-minute boundary row is used as the SMA input.",
        "- Expiry folder dates are used as truth for expiry selection.",
        "- Lot sizes are dynamic per expiry era to maintain ~300 quantity throughout the period.",
    ])

    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    results = run_backtest(args)
    write_daywise_csv(results, args.results_dir / DAYWISE_FILENAME)
    write_summary(results, args.results_dir / SUMMARY_FILENAME, args)
    traded = sum(1 for r in results if r.status == "TRADED")
    net = sum(float(r.net_pnl) for r in results if r.status == "TRADED")
    print(f"Done. Traded={traded} Net={format_money(net)}")
    print(f"Summary: {args.results_dir / SUMMARY_FILENAME}")


if __name__ == "__main__":
    main()
