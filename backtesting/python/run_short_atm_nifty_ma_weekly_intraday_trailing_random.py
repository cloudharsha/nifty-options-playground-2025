#!/usr/bin/env python3
"""
Random-participation variant of the Short ATM NIFTY MA Weekly Intraday Trailing strategy.

Simulates a human trader who:
  - Randomly skips entire trading days (tested at 30%, 40%, 50% skip rates)
  - On days they do trade, starts at a random 15-minute entry boundary (09:30 to 15:00)
  - Once in a trade, exits only at the trailing MA stop-loss or EOD (15:15) -- unchanged

Runs 5 independent simulations per skip rate (15 total) with fixed random seeds.
Seeds: 42, 137, 999, 2024, 31415
"""
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import random as _random_mod


IST_SUFFIX = "+05:30"
SUMMARY_FILENAME = "short_atm_nifty_ma_weekly_intraday_trailing_random_summary.md"
LOG_FILENAME = "short_atm_nifty_ma_weekly_intraday_trailing_random.log"
CAPITAL_FOR_CAGR = 10_00_000.0

SKIP_RATES = [0.30, 0.40, 0.50]
NUM_RUNS = 5
RUN_SEEDS = [42, 137, 999, 2024, 31415]


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


@dataclass
class SimResult:
    skip_rate: float
    run_index: int
    seed: int
    traded_days: int
    random_skipped_days: int
    strategy_skipped_days: int
    total_days: int
    net_pnl: float
    gross_pnl: float
    brokerage: float
    cagr: float
    max_drawdown: float
    wins: int
    losses: int
    win_pct: float
    max_consec_wins: int
    max_consec_losses: int
    ce_trades: int
    pe_trades: int
    stop_exits: int
    day_close_exits: int
    first_day: str
    last_day: str
    avg_start_slot: float


def qty_for_expiry(expiry_date: str) -> Tuple[int, int]:
    if expiry_date < "2021-10-07":
        return 75, 4
    if expiry_date <= "2024-04-25":
        return 50, 6
    if expiry_date <= "2024-11-21":
        return 25, 12
    if expiry_date <= "2025-12-30":
        return 75, 4
    return 65, 5


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
        description="Random-participation backtest of Short ATM NIFTY MA Weekly Intraday Trailing strategy.",
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
    return parser.parse_args()


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
    logger = logging.getLogger("short_atm_nifty_ma_weekly_intraday_trailing_random")
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


def run_single_simulation(
    spot_15m: Spot15Data,
    spot_5m: Spot5mData,
    expiries: List[str],
    contract_cache: Dict[Path, ContractData],
    args: argparse.Namespace,
    skip_rate: float,
    rng: _random_mod.Random,
    logger: logging.Logger,
) -> Tuple[List[DayResult], int, int, float]:
    """
    Returns (day_results, random_skipped_count, strategy_skipped_count, avg_start_slot_index).
    avg_start_slot_index is the mean index of the randomly chosen entry start slot (0 = 09:30).
    """
    day_results: List[DayResult] = []
    random_skipped = 0
    start_slot_indices: List[int] = []

    for entry_date in spot_15m.trading_days:
        # Random day skip
        if rng.random() < skip_rate:
            random_skipped += 1
            expiry_date = first_expiry_on_or_after(expiries, entry_date) or ""
            result = make_skipped_trade(
                entry_date=entry_date, skip_reason="random_skip",
                expiry_date=expiry_date,
                entry_timestamp=build_timestamp(entry_date, args.entry_start_time),
                remarks="Day randomly skipped (human participation model).",
            )
            day_results.append(aggregate_day_result(entry_date, expiry_date, [result]))
            continue

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
            day_results.append(aggregate_day_result(entry_date, expiry_date, day_trades))
            continue

        if not expiry_date:
            result = make_skipped_trade(
                entry_date=entry_date, skip_reason="no_same_week_expiry",
                entry_timestamp=build_timestamp(entry_date, args.entry_start_time),
                remarks="No expiry folder exists on or after this trade date.",
            )
            day_trades.append(result)
            day_results.append(aggregate_day_result(entry_date, "", day_trades))
            continue

        # Random start: pick any 15m slot from the full entry window
        start_slot_idx = rng.randint(0, len(entry_timestamps) - 1)
        start_slot_indices.append(start_slot_idx)
        next_allowed_entry_dt = timestamp_to_datetime(entry_timestamps[start_slot_idx])

        option_suffix = expiry_suffix(expiry_date)
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
                day_trades.append(result)
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
                day_trades.append(result)
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
                day_trades.append(result)
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
                day_trades.append(result)
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
                day_trades.append(result)
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
                day_trades.append(result)
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
            day_trades.append(result)
            logger.debug("TRADED date=%s entry=%s exit=%s side=%s net=%s",
                         entry_date, entry_ts, outcome.exit_timestamp, sold_side, result.net_pnl)

            if outcome.exit_reason == "day_close":
                stop_day = True
                break
            next_allowed_entry_dt = next_15m_boundary_after(outcome.exit_timestamp)

        if stop_day:
            pass

        if not day_trades:
            result = make_skipped_trade(
                entry_date=entry_date, skip_reason="no_entry_signal",
                expiry_date=expiry_date,
                entry_timestamp=build_timestamp(entry_date, args.entry_start_time),
                remarks="No completed trades or material skipped signals produced for this date.",
            )
            day_trades.append(result)

        day_results.append(aggregate_day_result(entry_date, expiry_date, day_trades))

    strategy_skipped = sum(1 for r in day_results
                           if int(r.trades) == 0 and r.skip_reason != "random_skip")
    avg_slot = sum(start_slot_indices) / len(start_slot_indices) if start_slot_indices else 0.0
    return day_results, random_skipped, strategy_skipped, avg_slot


def compute_sim_result(
    day_results: List[DayResult],
    random_skipped: int,
    strategy_skipped: int,
    avg_slot: float,
    skip_rate: float,
    run_index: int,
    seed: int,
) -> SimResult:
    traded_dr = [r for r in day_results if int(r.trades) > 0]
    net = sum(float(r.net_pnl) for r in traded_dr)
    gross = sum(float(r.gross_pnl) for r in traded_dr)
    brok = sum(float(r.brokerage) for r in traded_dr)
    vals = [float(r.net_pnl) for r in traded_dr]
    wins = sum(1 for v in vals if v > 0)
    losses = sum(1 for v in vals if v < 0)
    win_pct = wins / len(vals) * 100 if vals else 0.0
    max_w, max_l = compute_max_consecutive_streaks(vals)
    dd = compute_max_drawdown(vals)
    ce = sum(int(r.ce_trades) for r in traded_dr)
    pe = sum(int(r.pe_trades) for r in traded_dr)
    stopped = sum(int(r.stopped_trades) for r in traded_dr)
    day_close = sum(int(r.day_close_trades) for r in traded_dr)
    first_day = day_results[0].entry_date if day_results else ""
    last_day = day_results[-1].entry_date if day_results else ""
    cagr = compute_cagr(net, CAPITAL_FOR_CAGR, first_day, last_day) if first_day and last_day else 0.0

    return SimResult(
        skip_rate=skip_rate, run_index=run_index, seed=seed,
        traded_days=len(traded_dr),
        random_skipped_days=random_skipped,
        strategy_skipped_days=strategy_skipped,
        total_days=len(day_results),
        net_pnl=net, gross_pnl=gross, brokerage=brok,
        cagr=cagr, max_drawdown=dd,
        wins=wins, losses=losses, win_pct=win_pct,
        max_consec_wins=max_w, max_consec_losses=max_l,
        ce_trades=ce, pe_trades=pe,
        stop_exits=stopped, day_close_exits=day_close,
        first_day=first_day, last_day=last_day,
        avg_start_slot=avg_slot,
    )


def fmt_inr(v: float) -> str:
    """Format as Indian rupee with sign."""
    sign = "-" if v < 0 else ""
    s = f"{abs(v):,.0f}"
    return f"{sign}Rs {s}"


def slot_to_time(slot: float) -> str:
    """Convert average slot index (0=09:30, 1=09:45 ...) to approximate HH:MM."""
    total_minutes = 9 * 60 + 30 + int(round(slot)) * 15
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h:02d}:{m:02d}"


def write_summary(sim_results: List[SimResult], path: Path, args: argparse.Namespace) -> None:
    baseline_cagr = 31.48
    baseline_net = 67_11_939.0

    lines: List[str] = [
        "# Random-Participation Backtest — Short ATM NIFTY MA Weekly Intraday Trailing",
        "",
        "## Strategy (unchanged from baseline)",
        "",
        "- Signal: NIFTY 25-SMA on 15-minute closes",
        f"- Entry window (when present): `{args.entry_start_time}` through `{args.last_entry_time}`",
        f"- Exit: `{args.exit_time}` or trailing MA stop on 5-minute candles",
        "- Direction: above SMA → short ATM PE; below SMA → short ATM CE",
        "- Re-entry after stop: next 15-minute boundary",
        "",
        "## Randomness Model",
        "",
        "- **Day skip**: each trading day independently skipped with probability = skip_rate",
        "- **Random start time**: on days the trader participates, the first entry attempt",
        "  is at a uniformly random 15-minute boundary from 09:30 to 15:00",
        "- Once a position is open, exit logic is **identical to baseline** (SL or EOD only)",
        f"- Seeds: {RUN_SEEDS}",
        "",
        f"## Baseline (full participation, always 09:30 start)",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Net P/L | Rs 67,11,939 |",
        f"| CAGR | 31.48% |",
        f"| Max Drawdown | Rs 1,36,705 |",
        f"| Capital base | Rs 10,00,000 |",
        "",
        "## Simulation Results",
        "",
        "| Skip Rate | Run | Seed | Traded Days | Rnd Skipped | Strat Skipped |"
        " Net P/L | CAGR | vs Baseline | Max DD | Win% | Avg Start |",
        "|-----------|-----|------|-------------|-------------|---------------|"
        "---------|------|-------------|--------|------|-----------|",
    ]

    for r in sim_results:
        vs = f"{r.cagr / baseline_cagr * 100:.1f}%" if baseline_cagr else "N/A"
        lines.append(
            f"| {int(r.skip_rate * 100)}% | {r.run_index} | {r.seed} "
            f"| {r.traded_days} | {r.random_skipped_days} | {r.strategy_skipped_days} "
            f"| {fmt_inr(r.net_pnl)} | {r.cagr:.2f}% | {vs} "
            f"| {fmt_inr(r.max_drawdown)} | {r.win_pct:.1f}% | {slot_to_time(r.avg_start_slot)} |"
        )

    # Per-skip-rate aggregates
    lines.extend(["", "## Aggregated by Skip Rate (across 5 runs)", ""])
    lines.append("| Skip Rate | Avg Net P/L | Avg CAGR | Min CAGR | Max CAGR | Avg Max DD | Avg Win% | Avg Traded Days |")
    lines.append("|-----------|-------------|----------|----------|----------|------------|----------|-----------------|")

    for rate in SKIP_RATES:
        group = [r for r in sim_results if r.skip_rate == rate]
        avg_net = sum(r.net_pnl for r in group) / len(group)
        avg_cagr = sum(r.cagr for r in group) / len(group)
        min_cagr = min(r.cagr for r in group)
        max_cagr = max(r.cagr for r in group)
        avg_dd = sum(r.max_drawdown for r in group) / len(group)
        avg_win = sum(r.win_pct for r in group) / len(group)
        avg_td = sum(r.traded_days for r in group) / len(group)
        lines.append(
            f"| {int(rate * 100)}% | {fmt_inr(avg_net)} | {avg_cagr:.2f}% "
            f"| {min_cagr:.2f}% | {max_cagr:.2f}% | {fmt_inr(avg_dd)} "
            f"| {avg_win:.1f}% | {avg_td:.0f} |"
        )

    lines.extend(["", "## Notes", ""])
    lines.extend([
        "- CAGR is computed on Rs 10,00,000 capital over the full data range (same as baseline).",
        "- 'Rnd Skipped' = days the random model chose not to participate.",
        "- 'Strat Skipped' = days participated but no trade completed (data gaps, no signal, etc.).",
        "- 'Avg Start' ≈ average time of day the trader began looking for entries on active days.",
        "- All trade mechanics (MA filter, trailing stop, re-entry, slippage, brokerage) are unchanged.",
    ])

    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    print("Loading data...")
    spot_15m = load_spot_15m_data(args.spot_15m_file)
    spot_5m = load_spot_5m_data(args.spot_5m_file)
    expiries = load_expiry_folders(args.options_dir)
    contract_cache: Dict[Path, ContractData] = {}

    total_runs = len(SKIP_RATES) * NUM_RUNS
    sim_results: List[SimResult] = []
    run_num = 0

    for skip_rate in SKIP_RATES:
        for run_idx in range(1, NUM_RUNS + 1):
            run_num += 1
            seed = RUN_SEEDS[run_idx - 1]
            rng = _random_mod.Random(seed)
            print(f"  [{run_num}/{total_runs}] skip={int(skip_rate*100)}%  run={run_idx}  seed={seed}")
            logger.info("START skip_rate=%.0f%% run=%d seed=%d", skip_rate * 100, run_idx, seed)

            day_results, random_skipped, strategy_skipped, avg_slot = run_single_simulation(
                spot_15m, spot_5m, expiries, contract_cache, args, skip_rate, rng, logger
            )
            sr = compute_sim_result(
                day_results, random_skipped, strategy_skipped, avg_slot,
                skip_rate, run_idx, seed
            )
            sim_results.append(sr)
            logger.info("DONE skip=%.0f%% run=%d seed=%d traded=%d net=%.2f cagr=%.2f%%",
                        skip_rate * 100, run_idx, seed, sr.traded_days, sr.net_pnl, sr.cagr)
            print(f"         traded={sr.traded_days}  net={fmt_inr(sr.net_pnl)}  CAGR={sr.cagr:.2f}%")

    summary_path = args.results_dir / SUMMARY_FILENAME
    write_summary(sim_results, summary_path, args)
    print(f"\nAll done. Summary: {summary_path}")


if __name__ == "__main__":
    main()
