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
TRADEWISE_FILENAME = "short_atm_nifty_ma_weekly_intraday_trailing_2020_2026_trades.csv"
DAYWISE_FILENAME = "short_atm_nifty_ma_weekly_intraday_trailing_2020_2026_daywise.csv"
SUMMARY_FILENAME = "short_atm_nifty_ma_weekly_intraday_trailing_2020_2026_summary.md"
LOG_FILENAME = "short_atm_nifty_ma_weekly_intraday_trailing_2020_2026.log"
CAPITAL_FOR_CAGR = 10_00_000.0  # Rs 10L reference base


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
class Spot5mData:
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
    lot_size: str
    lots: str
    qty: str
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
            "Backtest 2020-2026 intraday weekly directional ATM short option strategy "
            "using a NIFTY 25-SMA signal with 5-minute trailing stop."
        ),
    )
    parser.add_argument("--spot-15m-file", type=Path,
                        default=repo_root / "nifty" / "NIFTY50_INDEX_15m_last_7y.csv")
    parser.add_argument("--spot-5m-file", type=Path,
                        default=repo_root / "nifty" / "NIFTY50_INDEX_5m_last_7y.csv")
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

    if not (args.entry_start_time <= args.last_entry_time < args.exit_time):
        parser.error("entry-start-time must be <= last-entry-time and last-entry-time must be < exit-time")

    return args


def build_timestamp(day: str, time_text: str) -> str:
    h, m = time_text.split(":")
    return f"{day}T{h}:{m}:00{IST_SUFFIX}"


def timestamp_to_datetime(ts: str) -> datetime.datetime:
    return datetime.datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")


def datetime_to_timestamp(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:00") + IST_SUFFIX


def build_intraday_timestamps(day: str, start_time: str, end_time: str, step_minutes: int) -> List[str]:
    start_dt = datetime.datetime.strptime(f"{day} {start_time}", "%Y-%m-%d %H:%M")
    end_dt = datetime.datetime.strptime(f"{day} {end_time}", "%Y-%m-%d %H:%M")
    timestamps: List[str] = []
    cur = start_dt
    while cur <= end_dt:
        timestamps.append(datetime_to_timestamp(cur))
        cur += datetime.timedelta(minutes=step_minutes)
    return timestamps


def signal_timestamp_for_entry(entry_ts: str) -> str:
    entry_dt = timestamp_to_datetime(entry_ts)
    return datetime_to_timestamp(entry_dt - datetime.timedelta(minutes=15))


def latest_completed_signal_timestamp(monitor_ts: str) -> str:
    dt = timestamp_to_datetime(monitor_ts)
    floored = (dt.minute // 15) * 15
    boundary = dt.replace(minute=floored, second=0)
    return datetime_to_timestamp(boundary - datetime.timedelta(minutes=15))


def next_15m_boundary_after(ts: str) -> datetime.datetime:
    cur = timestamp_to_datetime(ts).replace(second=0, microsecond=0)
    mins = cur.hour * 60 + cur.minute
    next_mins = ((mins // 15) + 1) * 15
    return cur.replace(hour=0, minute=0) + datetime.timedelta(minutes=next_mins)


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
    logger = logging.getLogger("short_atm_nifty_ma_weekly_intraday_trailing_2020_2026")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def join_remarks(parts: List[str]) -> str:
    return "; ".join(p for p in parts if p)


def summarize_timestamps(label: str, timestamps: List[str], edge: int = 5) -> str:
    if len(timestamps) <= edge * 2:
        return f"{label}: " + ", ".join(timestamps)
    first = ", ".join(timestamps[:edge])
    last = ", ".join(timestamps[-edge:])
    return (f"{label}: {len(timestamps)} missing from {timestamps[0]} through {timestamps[-1]}; "
            f"first {edge}: {first}; last {edge}: {last}")


def load_spot_15m_data(spot_file: Path) -> Spot15Data:
    rows_by_ts: Dict[str, PriceRow] = {}
    ordered: List[PriceRow] = []
    idx_by_ts: Dict[str, int] = {}
    trading_days: List[str] = []
    seen: set[str] = set()

    with spot_file.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            ts = row["timestamp"]
            pr = PriceRow(
                timestamp=ts,
                open_value=float(row["open"]), open_text=row["open"],
                high_value=float(row["high"]), high_text=row["high"],
                low_value=float(row["low"]), low_text=row["low"],
                close_value=float(row["close"]), close_text=row["close"],
            )
            idx_by_ts[ts] = len(ordered)
            ordered.append(pr)
            rows_by_ts[ts] = pr
            day = ts[:10]
            if day not in seen:
                trading_days.append(day)
                seen.add(day)

    return Spot15Data(rows_by_timestamp=rows_by_ts, ordered_rows=ordered,
                      index_by_timestamp=idx_by_ts, trading_days=trading_days)


def load_spot_5m_data(spot_file: Path) -> Spot5mData:
    rows_by_day: Dict[str, Dict[str, PriceRow]] = {}

    with spot_file.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            ts = row["timestamp"]
            day = ts[:10]
            if day not in rows_by_day:
                rows_by_day[day] = {}
            rows_by_day[day][ts] = PriceRow(
                timestamp=ts,
                open_value=float(row["open"]), open_text=row["open"],
                high_value=float(row["high"]), high_text=row["high"],
                low_value=float(row["low"]), low_text=row["low"],
                close_value=float(row["close"]), close_text=row["close"],
            )

    return Spot5mData(rows_by_day=rows_by_day)


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
    if contract_path in cache:
        return cache[contract_path]
    if not contract_path.exists():
        return None
    rows: Dict[str, OptionRow] = {}
    with contract_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            ts = row["timestamp"]
            rows[ts] = OptionRow(timestamp=ts, open_value=float(row["open"]), open_text=row["open"])
    cd = ContractData(path=contract_path, rows_by_timestamp=rows)
    cache[contract_path] = cd
    return cd


def compute_spot_sma(spot_data: Spot15Data, timestamp: str, ma_period: int) -> Tuple[Optional[float], int]:
    idx = spot_data.index_by_timestamp.get(timestamp)
    if idx is None:
        return None, 0
    n = idx + 1
    if n < ma_period:
        return None, n
    sma = sum(r.close_value for r in spot_data.ordered_rows[idx - ma_period + 1: idx + 1]) / ma_period
    return sma, n


def make_skipped_trade(
    entry_date: str, skip_reason: str, lot_size: int = 0, lots: int = 0,
    expiry_date: str = "", signal_timestamp: str = "", signal_close: str = "",
    spot_sma_25: str = "", spot_signal_relation: str = "", entry_timestamp: str = "",
    atm_strike: str = "", sold_side: str = "", contract_name: str = "",
    option_entry_open: str = "", exit_timestamp: str = "", option_exit_open: str = "",
    exit_reason: str = "", exit_spot_ma: str = "", remarks: str = "",
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date, status="SKIPPED", skip_reason=skip_reason,
        expiry_date=expiry_date, lot_size=str(lot_size), lots=str(lots), qty=str(lot_size * lots),
        signal_timestamp=signal_timestamp, signal_close=signal_close,
        spot_sma_25=spot_sma_25, spot_signal_relation=spot_signal_relation,
        entry_timestamp=entry_timestamp, atm_strike=atm_strike, sold_side=sold_side,
        contract_name=contract_name, option_entry_open=option_entry_open,
        exit_timestamp=exit_timestamp, option_exit_open=option_exit_open,
        exit_reason=exit_reason, exit_spot_ma=exit_spot_ma,
        gross_pnl="0.00", brokerage="0.00", net_pnl="0.00", remarks=remarks,
    )


def make_traded_result(
    entry_date: str, expiry_date: str, lot_size: int, lots: int,
    signal_timestamp: str, signal_close: str, spot_sma_25: str, spot_signal_relation: str,
    entry_timestamp: str, atm_strike: str, sold_side: str, contract_name: str,
    option_entry_open: str, exit_timestamp: str, option_exit_open: str,
    exit_reason: str, exit_spot_ma: str,
    gross_pnl: float, brokerage: float, net_pnl: float, remarks: str = "",
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date, status="TRADED", skip_reason="",
        expiry_date=expiry_date, lot_size=str(lot_size), lots=str(lots), qty=str(lot_size * lots),
        signal_timestamp=signal_timestamp, signal_close=signal_close,
        spot_sma_25=spot_sma_25, spot_signal_relation=spot_signal_relation,
        entry_timestamp=entry_timestamp, atm_strike=atm_strike, sold_side=sold_side,
        contract_name=contract_name, option_entry_open=option_entry_open,
        exit_timestamp=exit_timestamp, option_exit_open=option_exit_open,
        exit_reason=exit_reason, exit_spot_ma=exit_spot_ma,
        gross_pnl=format_money(gross_pnl), brokerage=format_money(brokerage),
        net_pnl=format_money(net_pnl), remarks=remarks,
    )


def resolve_trade_exit(
    entry_row: OptionRow, contract_data: ContractData,
    spot_5m_rows: Dict[str, PriceRow], spot_15m_data: Spot15Data,
    day: str, entry_timestamp: str, exit_time: str, sold_side: str,
    ma_period: int, slippage_points_per_order: float,
    brokerage_per_order: float, contract_multiplier: int,
) -> ExitOutcome:
    entry_dt = timestamp_to_datetime(entry_timestamp)
    final_exit_ts = build_timestamp(day, exit_time)
    final_exit_dt = timestamp_to_datetime(final_exit_ts)
    current_dt = entry_dt + datetime.timedelta(minutes=5)

    while current_dt < final_exit_dt:
        spot_ts = datetime_to_timestamp(current_dt)
        spot_row = spot_5m_rows.get(spot_ts)
        if spot_row is None:
            return ExitOutcome(
                status="SKIPPED", skip_reason="missing_spot_5m_timestamp",
                exit_timestamp=spot_ts, option_exit_open="",
                exit_reason="", exit_spot_ma="",
                gross_pnl=0.0, brokerage=0.0, net_pnl=0.0,
                remarks=f"Missing 5-minute NIFTY monitoring timestamp {spot_ts}",
            )

        stop_sig_ts = latest_completed_signal_timestamp(spot_ts)
        stop_sma, n = compute_spot_sma(spot_15m_data, stop_sig_ts, ma_period)
        if stop_sma is None:
            return ExitOutcome(
                status="SKIPPED", skip_reason="missing_or_insufficient_stop_sma",
                exit_timestamp=spot_ts, option_exit_open="",
                exit_reason="", exit_spot_ma="",
                gross_pnl=0.0, brokerage=0.0, net_pnl=0.0,
                remarks=f"{stop_sig_ts} has {n} bars; needs {ma_period}",
            )

        stop_hit = (spot_row.low_value <= stop_sma if sold_side == "PE"
                    else spot_row.high_value >= stop_sma)
        if stop_hit:
            exit_row = contract_data.rows_by_timestamp.get(spot_ts)
            if exit_row is None:
                return ExitOutcome(
                    status="SKIPPED", skip_reason="missing_option_exit_timestamp",
                    exit_timestamp=spot_ts, option_exit_open="",
                    exit_reason="stop_loss_ma_touch", exit_spot_ma=format_money(stop_sma),
                    gross_pnl=0.0, brokerage=0.0, net_pnl=0.0,
                    remarks=f"{contract_data.path.name} missing stop exit timestamp {spot_ts}",
                )
            gross = leg_pnl_after_slippage(entry_row.open_value - exit_row.open_value,
                                           slippage_points_per_order) * contract_multiplier
            brok = brokerage_per_order * 2
            return ExitOutcome(
                status="TRADED", skip_reason="",
                exit_timestamp=spot_ts, option_exit_open=exit_row.open_text,
                exit_reason="stop_loss_ma_touch", exit_spot_ma=format_money(stop_sma),
                gross_pnl=gross, brokerage=brok, net_pnl=gross - brok, remarks="",
            )

        current_dt += datetime.timedelta(minutes=5)

    exit_row = contract_data.rows_by_timestamp.get(final_exit_ts)
    if exit_row is None:
        return ExitOutcome(
            status="SKIPPED", skip_reason="missing_option_exit_timestamp",
            exit_timestamp=final_exit_ts, option_exit_open="",
            exit_reason="day_close", exit_spot_ma="",
            gross_pnl=0.0, brokerage=0.0, net_pnl=0.0,
            remarks=f"{contract_data.path.name} missing scheduled exit {final_exit_ts}",
        )

    final_stop_sig_ts = signal_timestamp_for_entry(final_exit_ts)
    final_sma, _ = compute_spot_sma(spot_15m_data, final_stop_sig_ts, ma_period)
    gross = leg_pnl_after_slippage(entry_row.open_value - exit_row.open_value,
                                   slippage_points_per_order) * contract_multiplier
    brok = brokerage_per_order * 2
    return ExitOutcome(
        status="TRADED", skip_reason="",
        exit_timestamp=final_exit_ts, option_exit_open=exit_row.open_text,
        exit_reason="day_close", exit_spot_ma=format_optional_money(final_sma),
        gross_pnl=gross, brokerage=brok, net_pnl=gross - brok, remarks="",
    )


def aggregate_day_result(entry_date: str, expiry_date: str, trade_results: List[TradeResult]) -> DayResult:
    traded = [r for r in trade_results if r.status == "TRADED"]
    skipped = [r for r in trade_results if r.status == "SKIPPED"]
    net_total = sum(float(r.net_pnl) for r in traded)
    gross_total = sum(float(r.gross_pnl) for r in traded)
    brok_total = sum(float(r.brokerage) for r in traded)
    ce = sum(1 for r in traded if r.sold_side == "CE")
    pe = sum(1 for r in traded if r.sold_side == "PE")
    stopped = sum(1 for r in traded if r.exit_reason == "stop_loss_ma_touch")
    day_close = sum(1 for r in traded if r.exit_reason == "day_close")
    skip_reasons = [r.skip_reason for r in skipped if r.skip_reason]
    skip_remarks = [r.remarks for r in skipped if r.remarks]

    if traded:
        status = "TRADED"
        skip_reason = ";".join(sorted(set(skip_reasons)))
    else:
        status = "SKIPPED"
        skip_reason = ";".join(sorted(set(skip_reasons))) if skip_reasons else "no_completed_trade"

    return DayResult(
        entry_date=entry_date, status=status, skip_reason=skip_reason, expiry_date=expiry_date,
        trades=str(len(traded)), ce_trades=str(ce), pe_trades=str(pe),
        stopped_trades=str(stopped), day_close_trades=str(day_close),
        skipped_signals=str(len(skipped)), orders_executed=str(2 * len(traded)),
        gross_pnl=format_money(gross_total), brokerage=format_money(brok_total),
        net_pnl=format_money(net_total), remarks=join_remarks(skip_remarks),
    )


def run_backtest(args: argparse.Namespace) -> Tuple[List[TradeResult], List[DayResult]]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    spot_15m = load_spot_15m_data(args.spot_15m_file)
    spot_5m = load_spot_5m_data(args.spot_5m_file)
    expiries = load_expiry_folders(args.options_dir)
    contract_cache: Dict[Path, ContractData] = {}
    trade_results: List[TradeResult] = []
    day_results: List[DayResult] = []

    try:
        for entry_date in spot_15m.trading_days:
            day_trades: List[TradeResult] = []
            expiry_date = first_expiry_on_or_after(expiries, entry_date) or ""
            lot_size, lots = qty_for_expiry(expiry_date) if expiry_date else (0, 0)
            contract_multiplier = lot_size * lots

            monitor_timestamps = build_intraday_timestamps(
                entry_date, args.entry_start_time, args.exit_time, step_minutes=5)
            entry_timestamps = build_intraday_timestamps(
                entry_date, args.entry_start_time, args.last_entry_time, step_minutes=15)
            spot_5m_rows = spot_5m.rows_by_day.get(entry_date, {})
            missing_5m = [ts for ts in monitor_timestamps if ts not in spot_5m_rows]

            if missing_5m:
                remarks = summarize_timestamps("Missing 5-minute NIFTY monitoring timestamps", missing_5m)
                result = make_skipped_trade(
                    entry_date=entry_date, skip_reason="missing_spot_5m_timestamp",
                    lot_size=lot_size, lots=lots,
                    expiry_date=expiry_date,
                    entry_timestamp=build_timestamp(entry_date, args.entry_start_time),
                    remarks=remarks,
                )
                day_trades.append(result)
                trade_results.append(result)
                day_results.append(aggregate_day_result(entry_date, expiry_date, day_trades))
                logger.info("SKIPPED date=%s reason=missing_spot_5m_timestamp", entry_date)
                continue

            if not expiry_date:
                result = make_skipped_trade(
                    entry_date=entry_date, skip_reason="no_same_week_expiry",
                    entry_timestamp=build_timestamp(entry_date, args.entry_start_time),
                    remarks="No expiry folder exists on or after this trade date.",
                )
                day_trades.append(result)
                trade_results.append(result)
                day_results.append(aggregate_day_result(entry_date, "", day_trades))
                logger.info("SKIPPED date=%s reason=no_same_week_expiry", entry_date)
                continue

            option_suffix = expiry_suffix(expiry_date)
            next_allowed_entry_dt = timestamp_to_datetime(entry_timestamps[0])
            stop_day = False

            for entry_ts in entry_timestamps:
                if timestamp_to_datetime(entry_ts) < next_allowed_entry_dt:
                    continue

                sig_ts = signal_timestamp_for_entry(entry_ts)
                sig_row = spot_15m.rows_by_timestamp.get(sig_ts)
                if sig_row is None:
                    result = make_skipped_trade(
                        entry_date=entry_date, skip_reason="missing_spot_signal_timestamp",
                        lot_size=lot_size, lots=lots,
                        expiry_date=expiry_date, signal_timestamp=sig_ts, entry_timestamp=entry_ts,
                        remarks=f"Missing 15-minute NIFTY signal timestamp {sig_ts}",
                    )
                    day_trades.append(result); trade_results.append(result)
                    continue

                sma, n = compute_spot_sma(spot_15m, sig_ts, args.ma_period)
                if sma is None:
                    result = make_skipped_trade(
                        entry_date=entry_date, skip_reason="insufficient_spot_history",
                        lot_size=lot_size, lots=lots,
                        expiry_date=expiry_date, signal_timestamp=sig_ts,
                        signal_close=sig_row.close_text, entry_timestamp=entry_ts,
                        remarks=f"{sig_ts} has {n} bars; needs {args.ma_period}",
                    )
                    day_trades.append(result); trade_results.append(result)
                    continue

                sma_text = format_money(sma)
                atm = round_to_nearest_50(sig_row.close_value)
                strike_text = str(atm)

                if sig_row.close_value > sma:
                    relation, sold_side = "ABOVE_SMA", "PE"
                elif sig_row.close_value < sma:
                    relation, sold_side = "BELOW_SMA", "CE"
                else:
                    result = make_skipped_trade(
                        entry_date=entry_date, skip_reason="equal_close_and_sma",
                        lot_size=lot_size, lots=lots,
                        expiry_date=expiry_date, signal_timestamp=sig_ts,
                        signal_close=sig_row.close_text, spot_sma_25=sma_text,
                        spot_signal_relation="EQUAL_SMA", entry_timestamp=entry_ts,
                        atm_strike=strike_text,
                        remarks=f"Close {sig_row.close_text} equals SMA {sma_text}",
                    )
                    day_trades.append(result); trade_results.append(result)
                    continue

                contract_path = args.options_dir / expiry_date / f"NIFTY_{atm}_{sold_side}_{option_suffix}.csv"
                cd = load_contract(contract_path, contract_cache)
                if cd is None:
                    result = make_skipped_trade(
                        entry_date=entry_date, skip_reason="missing_option_file",
                        lot_size=lot_size, lots=lots,
                        expiry_date=expiry_date, signal_timestamp=sig_ts,
                        signal_close=sig_row.close_text, spot_sma_25=sma_text,
                        spot_signal_relation=relation, entry_timestamp=entry_ts,
                        atm_strike=strike_text, sold_side=sold_side,
                        contract_name=contract_path.name,
                        remarks=f"Missing option file: {contract_path.name}",
                    )
                    day_trades.append(result); trade_results.append(result)
                    continue

                entry_row = cd.rows_by_timestamp.get(entry_ts)
                if entry_row is None:
                    remarks = (f"{contract_path.name} is header-only"
                               if not cd.rows_by_timestamp
                               else f"{contract_path.name} missing entry {entry_ts}")
                    result = make_skipped_trade(
                        entry_date=entry_date, skip_reason="missing_option_entry_timestamp",
                        lot_size=lot_size, lots=lots,
                        expiry_date=expiry_date, signal_timestamp=sig_ts,
                        signal_close=sig_row.close_text, spot_sma_25=sma_text,
                        spot_signal_relation=relation, entry_timestamp=entry_ts,
                        atm_strike=strike_text, sold_side=sold_side,
                        contract_name=contract_path.name, remarks=remarks,
                    )
                    day_trades.append(result); trade_results.append(result)
                    continue

                outcome = resolve_trade_exit(
                    entry_row=entry_row, contract_data=cd,
                    spot_5m_rows=spot_5m_rows, spot_15m_data=spot_15m,
                    day=entry_date, entry_timestamp=entry_ts,
                    exit_time=args.exit_time, sold_side=sold_side,
                    ma_period=args.ma_period,
                    slippage_points_per_order=args.slippage_points_per_order,
                    brokerage_per_order=args.brokerage_per_order,
                    contract_multiplier=contract_multiplier,
                )

                if outcome.status == "SKIPPED":
                    result = make_skipped_trade(
                        entry_date=entry_date, skip_reason=outcome.skip_reason,
                        lot_size=lot_size, lots=lots,
                        expiry_date=expiry_date, signal_timestamp=sig_ts,
                        signal_close=sig_row.close_text, spot_sma_25=sma_text,
                        spot_signal_relation=relation, entry_timestamp=entry_ts,
                        atm_strike=strike_text, sold_side=sold_side,
                        contract_name=contract_path.name,
                        option_entry_open=entry_row.open_text,
                        exit_timestamp=outcome.exit_timestamp,
                        option_exit_open=outcome.option_exit_open,
                        exit_reason=outcome.exit_reason, exit_spot_ma=outcome.exit_spot_ma,
                        remarks=outcome.remarks,
                    )
                    day_trades.append(result); trade_results.append(result)
                    stop_day = True
                    break

                result = make_traded_result(
                    entry_date=entry_date, expiry_date=expiry_date,
                    lot_size=lot_size, lots=lots,
                    signal_timestamp=sig_ts, signal_close=sig_row.close_text,
                    spot_sma_25=sma_text, spot_signal_relation=relation,
                    entry_timestamp=entry_ts, atm_strike=strike_text,
                    sold_side=sold_side, contract_name=contract_path.name,
                    option_entry_open=entry_row.open_text,
                    exit_timestamp=outcome.exit_timestamp,
                    option_exit_open=outcome.option_exit_open,
                    exit_reason=outcome.exit_reason, exit_spot_ma=outcome.exit_spot_ma,
                    gross_pnl=outcome.gross_pnl, brokerage=outcome.brokerage,
                    net_pnl=outcome.net_pnl,
                )
                day_trades.append(result); trade_results.append(result)
                logger.info("TRADED date=%s entry=%s exit=%s expiry=%s side=%s strike=%s lot=%sx%s net=%s reason=%s",
                            entry_date, entry_ts, outcome.exit_timestamp, expiry_date, sold_side, atm,
                            lot_size, lots, result.net_pnl, outcome.exit_reason)

                if outcome.exit_reason == "day_close":
                    stop_day = True
                    break
                next_allowed_entry_dt = next_15m_boundary_after(outcome.exit_timestamp)

            if stop_day:
                logger.info("DAY_STOPPED date=%s", entry_date)

            if not day_trades:
                result = make_skipped_trade(
                    entry_date=entry_date, skip_reason="no_entry_signal",
                    expiry_date=expiry_date,
                    entry_timestamp=build_timestamp(entry_date, args.entry_start_time),
                    remarks="No completed trades or material skipped signals produced for this date.",
                )
                day_trades.append(result); trade_results.append(result)

            day_results.append(aggregate_day_result(entry_date, expiry_date, day_trades))

    except Exception:
        logger.exception("ERROR unexpected failure")
        raise

    return trade_results, day_results


def write_tradewise_csv(results: List[TradeResult], path: Path) -> None:
    fields = [f.name for f in TradeResult.__dataclass_fields__.values()]
    with path.open("w", encoding="utf-8", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow(r.__dict__)


def write_daywise_csv(results: List[DayResult], path: Path) -> None:
    fields = [f.name for f in DayResult.__dataclass_fields__.values()]
    with path.open("w", encoding="utf-8", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow(r.__dict__)


def compute_max_consecutive_streaks(vals: List[float]) -> Tuple[int, int]:
    max_w = max_l = cur_w = cur_l = 0
    for v in vals:
        if v > 0:
            cur_w += 1; cur_l = 0; max_w = max(max_w, cur_w)
        elif v < 0:
            cur_l += 1; cur_w = 0; max_l = max(max_l, cur_l)
        else:
            cur_w = cur_l = 0
    return max_w, max_l


def compute_max_drawdown(vals: List[float]) -> float:
    peak = dd = cum = 0.0
    for v in vals:
        cum += v; peak = max(peak, cum); dd = max(dd, peak - cum)
    return dd


def write_summary(
    trade_results: List[TradeResult], day_results: List[DayResult],
    path: Path, args: argparse.Namespace,
) -> None:
    traded_tr = [r for r in trade_results if r.status == "TRADED"]
    traded_dr = [r for r in day_results if int(r.trades) > 0]
    skipped_dr = [r for r in day_results if int(r.trades) == 0]
    gross = sum(float(r.gross_pnl) for r in traded_dr)
    brok = sum(float(r.brokerage) for r in traded_dr)
    net = sum(float(r.net_pnl) for r in traded_dr)
    ce = sum(1 for r in traded_tr if r.sold_side == "CE")
    pe = sum(1 for r in traded_tr if r.sold_side == "PE")
    stopped = sum(1 for r in traded_tr if r.exit_reason == "stop_loss_ma_touch")
    day_close = sum(1 for r in traded_tr if r.exit_reason == "day_close")
    vals = [float(r.net_pnl) for r in traded_dr]
    wins = sum(1 for v in vals if v > 0)
    losses = sum(1 for v in vals if v < 0)
    be = sum(1 for v in vals if v == 0)
    max_w, max_l = compute_max_consecutive_streaks(vals)
    dd = compute_max_drawdown(vals)
    best = max(traded_dr, key=lambda r: float(r.net_pnl), default=None)
    worst = min(traded_dr, key=lambda r: float(r.net_pnl), default=None)
    first_day = spot_15m_first_day = day_results[0].entry_date if day_results else ""
    last_day = day_results[-1].entry_date if day_results else ""
    cagr = compute_cagr(net, CAPITAL_FOR_CAGR, first_day, last_day) if first_day and last_day else 0.0

    lines: List[str] = [
        "# Intraday Weekly Short ATM NIFTY 25-SMA Trailing Backtest (2020-2026)",
        "",
        "## Strategy Details",
        "",
        "- Signal source: NIFTY 15-minute close",
        f"- Entry window: `{args.entry_start_time}` through `{args.last_entry_time}`",
        f"- Exit time: `{args.exit_time}`",
        f"- MA rule: {args.ma_period}-SMA of 15-minute NIFTY closes including the signal candle",
        "- Direction rule: above SMA -> short ATM PE; below SMA -> short ATM CE; equal -> no trade",
        "- Stop source: NIFTY 5-minute candles (proxy for 1-minute for multi-year data)",
        "- Stop rule: short PE exits when 5-minute NIFTY low touches the trailing MA; short CE when high touches it",
        "- Trailing MA rule: latest completed 15-minute SMA stays fixed until the next 15-minute close",
        "- Re-entry rule: one active trade at a time; next entry only after next 15-minute boundary post-stop",
        "- Expiry rule: first weekly expiry on or after the trade date",
        "- ATM rule: nearest 50 using the signal candle close",
        "- Quantity: ~300 per trade (dynamic lot sizing by expiry era)",
        "  - pre-2021-10-07: 75x4=300 | 2021-10-07-2024-04-25: 50x6=300",
        "  - 2024-04-26-2024-11-21: 25x12=300 | 2024-11-22-2025-12-30: 75x4=300",
        "  - 2026+: 65x5=325",
        f"- Slippage: {format_money(args.slippage_points_per_order)} pt/order",
        f"- Brokerage: Rs {int(args.brokerage_per_order)}/order -> Rs {int(args.brokerage_per_order * 2)}/trade",
        f"- Capital reference (CAGR): Rs {int(CAPITAL_FOR_CAGR):,}",
        f"- Data range: `{first_day}` to `{last_day}`" if first_day else "",
        "",
        "## Results Summary",
        "",
        f"- Traded days: `{len(traded_dr)}`",
        f"- Skipped days: `{len(skipped_dr)}`",
        f"- Completed trades: `{len(traded_tr)}`",
        f"- CE-sell count: `{ce}`",
        f"- PE-sell count: `{pe}`",
        f"- Stop-loss exits: `{stopped}`",
        f"- Day-close exits: `{day_close}`",
        f"- Winning days: `{wins}`",
        f"- Losing days: `{losses}`",
        f"- Break-even days: `{be}`",
        f"- Max profit day: `{best.entry_date}` net `{best.net_pnl}`" if best else "- Max profit day: `N/A`",
        f"- Max loss day: `{worst.entry_date}` net `{worst.net_pnl}`" if worst else "- Max loss day: `N/A`",
        f"- Max consecutive wins: `{max_w}`",
        f"- Max consecutive losses: `{max_l}`",
        f"- Max drawdown: `{format_money(dd)}`",
        f"- Total Profit/Loss: `{format_money(net)}`",
        f"- Total Brokerage: `{format_money(brok)}`",
        f"- Gross P/L: `{format_money(gross)}`",
        f"- CAGR (on Rs {int(CAPITAL_FOR_CAGR):,}): `{cagr:.2f}%`",
        "",
        "## Yearly Summary",
        "",
        "| Year | Traded Days | Wins | Losses | Win% | Net P/L |",
        "|------|------------|------|--------|------|---------|",
    ]

    years: Dict[str, List[float]] = {}
    for r in traded_dr:
        y = r.entry_date[:4]
        years.setdefault(y, []).append(float(r.net_pnl))
    for y in sorted(years):
        yv = years[y]
        yw = sum(1 for v in yv if v > 0)
        yl = sum(1 for v in yv if v < 0)
        pct = yw / len(yv) * 100 if yv else 0.0
        lines.append(f"| {y} | {len(yv)} | {yw} | {yl} | {pct:.1f}% | {format_money(sum(yv))} |")

    lines.extend(["", "## Exceptions", ""])
    exc_rows = [r for r in day_results if r.skip_reason or r.remarks]
    if exc_rows:
        for r in exc_rows:
            lines.append(f"- `{r.entry_date}`: `{r.skip_reason}`. {r.remarks}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Remarks",
        "",
        "- Exact timestamp matching; no nearest-candle fallback.",
        "- Stop checks use 5-minute bars as proxy for intraday momentum (1-minute data not available pre-2025).",
        "- The 15-minute spot file determines the trading calendar.",
        "- Expiry folder dates are used as truth for expiry selection.",
        "- Lot sizes are dynamic per expiry era to maintain ~300 quantity throughout the period.",
    ])

    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    trade_results, day_results = run_backtest(args)
    write_tradewise_csv(trade_results, args.results_dir / TRADEWISE_FILENAME)
    write_daywise_csv(day_results, args.results_dir / DAYWISE_FILENAME)
    write_summary(trade_results, day_results, args.results_dir / SUMMARY_FILENAME, args)
    traded = sum(1 for r in day_results if int(r.trades) > 0)
    net = sum(float(r.net_pnl) for r in day_results)
    print(f"Done. Traded days={traded} Net={format_money(net)}")
    print(f"Summary: {args.results_dir / SUMMARY_FILENAME}")


if __name__ == "__main__":
    main()
