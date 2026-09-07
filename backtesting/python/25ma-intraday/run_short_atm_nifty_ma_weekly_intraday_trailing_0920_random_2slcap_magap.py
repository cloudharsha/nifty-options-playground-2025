#!/usr/bin/env python3
"""
09:20-start random-skip variant with 2-SL/day cap AND an MA-gap entry filter.

Builds on run_short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap.py.

Additional filter (new in this script):
  - At each entry slot, if abs(spot_close - 25-SMA) > ma_gap_threshold, skip that entry.
  - Tested with thresholds: 75, 100, 125, 150 points.

Everything else is identical to the 2slcap baseline:
  - Entry at 09:20, falls through to 09:30 if option data unavailable.
  - Random day-skipping at 30%, 40%, 50%.
  - 2-SL/day cap: halt trading after 2 stop-loss exits in one day.
  - Seeds: 42, 137, 999, 2024, 31415 (5 runs per skip rate).

Total runs: 4 thresholds × 3 skip rates × 5 seeds = 60 runs.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import logging
import random as _random_mod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


IST_SUFFIX = "+05:30"
SUMMARY_FILENAME = "short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_magap_summary.md"
LOG_FILENAME = "short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_magap.log"
CAPITAL_FOR_CAGR = 10_00_000.0

SKIP_RATES = [0.30, 0.40, 0.50]
NUM_RUNS = 5
RUN_SEEDS = [42, 137, 999, 2024, 31415]
MA_GAP_THRESHOLDS = [75, 100, 125, 150]   # points; entry skipped if abs(close - SMA) > threshold

EARLY_ENTRY_TIME = "09:20"
STANDARD_ENTRY_START = "09:30"
EARLY_ENTRY_SIGNAL_TIME = "09:15"
SL_CAP_PER_DAY = 2


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
    ma_gap: str
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
    max_consec_sl_in_day: int
    sl_capped: bool
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
    ma_gap_threshold: int
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
    max_consec_sl_in_day: int
    max_consec_sl_overall: int
    days_2sl_capped: int
    gap_filtered_entries: int   # individual entry slots blocked by the gap filter
    first_day: str
    last_day: str


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
        description="09:20-start random-skip + 2-SL cap + MA-gap filter backtest.",
    )
    parser.add_argument("--spot-15m-file", type=Path,
                        default=repo_root / "nifty" / "NIFTY50_INDEX_15m_last_7y.csv")
    parser.add_argument("--spot-5m-file", type=Path,
                        default=repo_root / "nifty" / "NIFTY50_INDEX_5m_last_7y.csv")
    parser.add_argument("--options-dir", type=Path,
                        default=repo_root / "NiftyOptions_2020_2026" / "Options")
    parser.add_argument("--results-dir", type=Path,
                        default=repo_root / "backtesting" / "results")
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


def signal_timestamp_for_entry(entry_ts: str, day: str) -> str:
    entry_dt = timestamp_to_datetime(entry_ts)
    if entry_dt.hour == 9 and entry_dt.minute < 30:
        return build_timestamp(day, EARLY_ENTRY_SIGNAL_TIME)
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
    logger = logging.getLogger("short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_magap")
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
    spot_sma_25: str = "", spot_signal_relation: str = "", ma_gap: str = "",
    entry_timestamp: str = "", atm_strike: str = "", sold_side: str = "",
    contract_name: str = "", option_entry_open: str = "", exit_timestamp: str = "",
    option_exit_open: str = "", exit_reason: str = "", exit_spot_ma: str = "",
    remarks: str = "",
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date, status="SKIPPED", skip_reason=skip_reason,
        expiry_date=expiry_date, lot_size=str(lot_size), lots=str(lots), qty=str(lot_size * lots),
        signal_timestamp=signal_timestamp, signal_close=signal_close,
        spot_sma_25=spot_sma_25, spot_signal_relation=spot_signal_relation, ma_gap=ma_gap,
        entry_timestamp=entry_timestamp, atm_strike=atm_strike, sold_side=sold_side,
        contract_name=contract_name, option_entry_open=option_entry_open,
        exit_timestamp=exit_timestamp, option_exit_open=option_exit_open,
        exit_reason=exit_reason, exit_spot_ma=exit_spot_ma,
        gross_pnl="0.00", brokerage="0.00", net_pnl="0.00", remarks=remarks,
    )


def make_traded_result(
    entry_date: str, expiry_date: str, lot_size: int, lots: int,
    signal_timestamp: str, signal_close: str, spot_sma_25: str, spot_signal_relation: str,
    ma_gap: str, entry_timestamp: str, atm_strike: str, sold_side: str, contract_name: str,
    option_entry_open: str, exit_timestamp: str, option_exit_open: str,
    exit_reason: str, exit_spot_ma: str,
    gross_pnl: float, brokerage: float, net_pnl: float, remarks: str = "",
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date, status="TRADED", skip_reason="",
        expiry_date=expiry_date, lot_size=str(lot_size), lots=str(lots), qty=str(lot_size * lots),
        signal_timestamp=signal_timestamp, signal_close=signal_close,
        spot_sma_25=spot_sma_25, spot_signal_relation=spot_signal_relation, ma_gap=ma_gap,
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
            if spot_15m_data.index_by_timestamp.get(stop_sig_ts) is None:
                current_dt += datetime.timedelta(minutes=5)
                continue
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

    final_stop_sig_ts = signal_timestamp_for_entry(final_exit_ts, day)
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


def max_consecutive_sl(exit_reasons: List[str]) -> int:
    best = cur = 0
    for r in exit_reasons:
        if r == "stop_loss_ma_touch":
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def aggregate_day_result(
    entry_date: str, expiry_date: str, trade_results: List[TradeResult], sl_capped: bool = False,
) -> DayResult:
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
    sl_streak = max_consecutive_sl([r.exit_reason for r in traded])

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
        net_pnl=format_money(net_total), max_consec_sl_in_day=sl_streak,
        sl_capped=sl_capped,
        remarks=join_remarks(skip_remarks),
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
    ma_gap_threshold: int,
    rng: _random_mod.Random,
    logger: logging.Logger,
) -> Tuple[List[DayResult], List[TradeResult], List[TradeResult], int, int, int]:
    """
    Returns (day_results, all_trade_results, all_traded_trades,
             random_skipped_count, strategy_skipped_count, gap_filtered_entries).
    """
    day_results: List[DayResult] = []
    all_trade_results: List[TradeResult] = []
    all_traded_trades: List[TradeResult] = []
    random_skipped = 0
    gap_filtered_entries = 0

    for entry_date in spot_15m.trading_days:
        if rng.random() < skip_rate:
            random_skipped += 1
            expiry_date = first_expiry_on_or_after(expiries, entry_date) or ""
            result = make_skipped_trade(
                entry_date=entry_date, skip_reason="random_skip",
                expiry_date=expiry_date,
                entry_timestamp=build_timestamp(entry_date, EARLY_ENTRY_TIME),
                remarks="Day randomly skipped (human participation model).",
            )
            all_trade_results.append(result)
            day_results.append(aggregate_day_result(entry_date, expiry_date, [result]))
            continue

        day_trades: List[TradeResult] = []
        expiry_date = first_expiry_on_or_after(expiries, entry_date) or ""
        lot_size, lots = qty_for_expiry(expiry_date) if expiry_date else (0, 0)
        contract_multiplier = lot_size * lots

        monitor_timestamps = build_intraday_timestamps(entry_date, "09:25", args.exit_time, step_minutes=5)
        spot_5m_rows = spot_5m.rows_by_day.get(entry_date, {})
        missing_5m = [ts for ts in monitor_timestamps if ts not in spot_5m_rows]

        if missing_5m:
            remarks = summarize_timestamps("Missing 5-minute NIFTY monitoring timestamps", missing_5m)
            result = make_skipped_trade(
                entry_date=entry_date, skip_reason="missing_spot_5m_timestamp",
                lot_size=lot_size, lots=lots, expiry_date=expiry_date,
                entry_timestamp=build_timestamp(entry_date, EARLY_ENTRY_TIME),
                remarks=remarks,
            )
            day_trades.append(result)
            day_results.append(aggregate_day_result(entry_date, expiry_date, day_trades))
            continue

        if not expiry_date:
            result = make_skipped_trade(
                entry_date=entry_date, skip_reason="no_same_week_expiry",
                entry_timestamp=build_timestamp(entry_date, EARLY_ENTRY_TIME),
                remarks="No expiry folder exists on or after this trade date.",
            )
            day_trades.append(result)
            day_results.append(aggregate_day_result(entry_date, "", day_trades))
            continue

        entry_timestamps = (
            [build_timestamp(entry_date, EARLY_ENTRY_TIME)]
            + build_intraday_timestamps(entry_date, STANDARD_ENTRY_START, args.last_entry_time, step_minutes=15)
        )

        option_suffix = expiry_suffix(expiry_date)
        next_allowed_entry_dt = timestamp_to_datetime(entry_timestamps[0])
        stop_day = False
        daily_sl_count = 0
        sl_capped_today = False

        for entry_ts in entry_timestamps:
            if timestamp_to_datetime(entry_ts) < next_allowed_entry_dt:
                continue

            sig_ts = signal_timestamp_for_entry(entry_ts, entry_date)
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
            gap = abs(sig_row.close_value - sma)
            gap_text = format_money(gap)

            # MA-gap filter: skip entry if price is too far from MA
            if gap > ma_gap_threshold:
                gap_filtered_entries += 1
                result = make_skipped_trade(
                    entry_date=entry_date, skip_reason="ma_gap_exceeded",
                    lot_size=lot_size, lots=lots,
                    expiry_date=expiry_date, signal_timestamp=sig_ts,
                    signal_close=sig_row.close_text, spot_sma_25=sma_text,
                    ma_gap=gap_text, entry_timestamp=entry_ts,
                    remarks=(f"Gap {gap_text} > threshold {ma_gap_threshold}; "
                             f"close={sig_row.close_text} sma={sma_text}"),
                )
                day_trades.append(result)
                continue

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
                    ma_gap=gap_text, spot_signal_relation="EQUAL_SMA", entry_timestamp=entry_ts,
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
                    ma_gap=gap_text, spot_signal_relation=relation, entry_timestamp=entry_ts,
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
                    ma_gap=gap_text, spot_signal_relation=relation, entry_timestamp=entry_ts,
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
                    ma_gap=gap_text, spot_signal_relation=relation, entry_timestamp=entry_ts,
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
                ma_gap=gap_text, entry_timestamp=entry_ts, atm_strike=strike_text,
                sold_side=sold_side, contract_name=contract_path.name,
                option_entry_open=entry_row.open_text,
                exit_timestamp=outcome.exit_timestamp,
                option_exit_open=outcome.option_exit_open,
                exit_reason=outcome.exit_reason, exit_spot_ma=outcome.exit_spot_ma,
                gross_pnl=outcome.gross_pnl, brokerage=outcome.brokerage,
                net_pnl=outcome.net_pnl,
            )
            day_trades.append(result)
            all_traded_trades.append(result)
            logger.debug("TRADED date=%s entry=%s exit=%s side=%s net=%s",
                         entry_date, entry_ts, outcome.exit_timestamp, sold_side, result.net_pnl)

            if outcome.exit_reason == "day_close":
                stop_day = True
                break

            if outcome.exit_reason == "stop_loss_ma_touch":
                daily_sl_count += 1
                if daily_sl_count >= SL_CAP_PER_DAY:
                    sl_capped_today = True
                    logger.debug("2SL_CAP date=%s after %d SL exits", entry_date, daily_sl_count)
                    stop_day = True
                    break

            next_allowed_entry_dt = next_15m_boundary_after(outcome.exit_timestamp)

        if not day_trades:
            result = make_skipped_trade(
                entry_date=entry_date, skip_reason="no_entry_signal",
                expiry_date=expiry_date,
                entry_timestamp=build_timestamp(entry_date, EARLY_ENTRY_TIME),
                remarks="No completed trades or material skipped signals produced for this date.",
            )
            day_trades.append(result)

        all_trade_results.extend(day_trades)
        day_results.append(aggregate_day_result(entry_date, expiry_date, day_trades, sl_capped=sl_capped_today))

    strategy_skipped = sum(1 for r in day_results
                           if int(r.trades) == 0 and r.skip_reason != "random_skip")
    return day_results, all_trade_results, all_traded_trades, random_skipped, strategy_skipped, gap_filtered_entries


def compute_sim_result(
    day_results: List[DayResult],
    all_traded_trades: List[TradeResult],
    random_skipped: int,
    strategy_skipped: int,
    gap_filtered_entries: int,
    ma_gap_threshold: int,
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

    max_sl_day = max((r.max_consec_sl_in_day for r in traded_dr), default=0)
    all_exit_reasons = [r.exit_reason for r in all_traded_trades]
    max_sl_overall = max_consecutive_sl(all_exit_reasons)
    days_2sl_capped = sum(1 for r in day_results if r.sl_capped)

    first_day = day_results[0].entry_date if day_results else ""
    last_day = day_results[-1].entry_date if day_results else ""
    cagr = compute_cagr(net, CAPITAL_FOR_CAGR, first_day, last_day) if first_day and last_day else 0.0

    return SimResult(
        ma_gap_threshold=ma_gap_threshold,
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
        max_consec_sl_in_day=max_sl_day,
        max_consec_sl_overall=max_sl_overall,
        days_2sl_capped=days_2sl_capped,
        gap_filtered_entries=gap_filtered_entries,
        first_day=first_day, last_day=last_day,
    )


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


def fmt_inr(v: float) -> str:
    sign = "-" if v < 0 else ""
    s = f"{abs(v):,.0f}"
    return f"{sign}Rs {s}"


def write_summary(sim_results: List[SimResult], path: Path) -> None:
    baseline_cagr = 31.48

    lines: List[str] = [
        "# 09:20-Start Random-Skip + 2-SL/Day Cap + MA-Gap Filter — Short ATM NIFTY MA Weekly Intraday Trailing",
        "",
        "## Strategy filters (stacked)",
        "",
        "1. **Entry at 09:20** — falls through to 09:30 if option data unavailable",
        "2. **Random day skip** — 30% / 40% / 50%",
        f"3. **2-SL/day cap** — halt trading after {SL_CAP_PER_DAY} stop-loss exits in one day",
        f"4. **MA-gap filter** — skip entry if abs(spot_close − 25-SMA) > threshold",
        f"   Thresholds tested: {MA_GAP_THRESHOLDS} points",
        "",
        "## Baseline (full participation, 09:30, no SL cap, no gap filter)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        "| Net P/L | Rs 67,11,939 |",
        "| CAGR | 31.48% |",
        "| Max Drawdown | Rs 1,36,705 |",
        "| Capital base | Rs 10,00,000 |",
        "",
    ]

    # Per-threshold sections
    for threshold in MA_GAP_THRESHOLDS:
        group = [r for r in sim_results if r.ma_gap_threshold == threshold]
        lines.extend([
            f"## MA Gap ≤ {threshold} pts  (skip if gap > {threshold})",
            "",
            "| Skip | Run | Seed | Traded Days | Gap Filtered | 2SL-Cap Days"
            " | Net P/L | CAGR | vs Base | Max DD | Win% | Max SL Overall |",
            "|------|-----|------|-------------|--------------|-------------|"
            "---------|------|---------|--------|------|----------------|",
        ])
        for r in group:
            vs = f"{r.cagr / baseline_cagr * 100:.1f}%"
            lines.append(
                f"| {int(r.skip_rate * 100)}% | {r.run_index} | {r.seed} "
                f"| {r.traded_days} | {r.gap_filtered_entries} | {r.days_2sl_capped} "
                f"| {fmt_inr(r.net_pnl)} | {r.cagr:.2f}% | {vs} "
                f"| {fmt_inr(r.max_drawdown)} | {r.win_pct:.1f}% "
                f"| {r.max_consec_sl_overall} |"
            )
        lines.append("")

        # Aggregate by skip rate within this threshold
        lines.extend([
            f"### Aggregated — gap ≤ {threshold} pts",
            "",
            "| Skip Rate | Avg Net P/L | Avg CAGR | Min CAGR | Max CAGR"
            " | Avg Max DD | Avg Win% | Avg Traded Days | Avg Gap Filtered | Avg 2SL-Cap Days |",
            "|-----------|-------------|----------|----------|----------"
            "|------------|----------|-----------------|------------------|-----------------|",
        ])
        for rate in SKIP_RATES:
            sub = [r for r in group if r.skip_rate == rate]
            avg_net = sum(r.net_pnl for r in sub) / len(sub)
            avg_cagr = sum(r.cagr for r in sub) / len(sub)
            min_cagr = min(r.cagr for r in sub)
            max_cagr = max(r.cagr for r in sub)
            avg_dd = sum(r.max_drawdown for r in sub) / len(sub)
            avg_win = sum(r.win_pct for r in sub) / len(sub)
            avg_td = sum(r.traded_days for r in sub) / len(sub)
            avg_gap = sum(r.gap_filtered_entries for r in sub) / len(sub)
            avg_capped = sum(r.days_2sl_capped for r in sub) / len(sub)
            lines.append(
                f"| {int(rate * 100)}% | {fmt_inr(avg_net)} | {avg_cagr:.2f}% "
                f"| {min_cagr:.2f}% | {max_cagr:.2f}% | {fmt_inr(avg_dd)} "
                f"| {avg_win:.1f}% | {avg_td:.0f} | {avg_gap:.0f} | {avg_capped:.0f} |"
            )
        lines.append("")

    # Cross-threshold comparison (30% skip, averaged over 5 runs)
    lines.extend([
        "## Cross-Threshold Comparison (30% skip, avg of 5 runs)",
        "",
        "| Gap Threshold | Avg Net P/L | Avg CAGR | vs 2SL-cap baseline* | Avg Max DD | Avg Win% | Avg Gap Filtered |",
        "|---------------|-------------|----------|----------------------|------------|----------|-----------------|",
    ])
    # 2SL-cap baseline at 30%: from the 2slcap run results (hardcoded from previous run)
    ref_cagr_30 = 27.43
    for threshold in MA_GAP_THRESHOLDS:
        sub = [r for r in sim_results if r.ma_gap_threshold == threshold and r.skip_rate == 0.30]
        avg_net = sum(r.net_pnl for r in sub) / len(sub)
        avg_cagr = sum(r.cagr for r in sub) / len(sub)
        avg_dd = sum(r.max_drawdown for r in sub) / len(sub)
        avg_win = sum(r.win_pct for r in sub) / len(sub)
        avg_gap = sum(r.gap_filtered_entries for r in sub) / len(sub)
        vs_ref = f"{avg_cagr / ref_cagr_30 * 100:.1f}%"
        lines.append(
            f"| ≤ {threshold} pts | {fmt_inr(avg_net)} | {avg_cagr:.2f}% | {vs_ref} "
            f"| {fmt_inr(avg_dd)} | {avg_win:.1f}% | {avg_gap:.0f} |"
        )
    lines.extend([
        "",
        "_* 2SL-cap baseline at 30% skip = 27.43% avg CAGR (from prior run)_",
        "",
    ])

    lines.extend([
        "## Notes",
        "",
        "- **MA-gap filter**: entry slot is skipped if `abs(spot_close_at_signal − 25-SMA) > threshold`.",
        "  The gap is rechecked at every re-entry slot within the day, not just the first.",
        "- **2-SL/day cap**: if stop-loss fires twice in one day, no further entries taken that day.",
        "- **Gap Filtered**: count of individual entry attempts blocked by the gap filter across the full backtest.",
        "- **2SL-Cap Days**: days where the SL cap was triggered.",
        "- CAGR computed on Rs 10,00,000 capital over the full data range.",
        "- 'vs Base' is relative to the original 09:30 full-participation baseline (31.48% CAGR).",
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

    total_runs = len(MA_GAP_THRESHOLDS) * len(SKIP_RATES) * NUM_RUNS
    sim_results: List[SimResult] = []
    run_num = 0

    for threshold in MA_GAP_THRESHOLDS:
        print(f"\n=== MA Gap threshold: {threshold} pts ===")
        for skip_rate in SKIP_RATES:
            for run_idx in range(1, NUM_RUNS + 1):
                run_num += 1
                seed = RUN_SEEDS[run_idx - 1]
                rng = _random_mod.Random(seed)
                print(f"  [{run_num}/{total_runs}] gap={threshold}  skip={int(skip_rate*100)}%  run={run_idx}  seed={seed}")
                logger.info("START gap=%d skip_rate=%.0f%% run=%d seed=%d",
                            threshold, skip_rate * 100, run_idx, seed)

                day_results, all_trade_results, all_traded_trades, random_skipped, strategy_skipped, gap_filtered = (
                    run_single_simulation(
                        spot_15m, spot_5m, expiries, contract_cache, args,
                        skip_rate, threshold, rng, logger,
                    )
                )
                sr = compute_sim_result(
                    day_results, all_traded_trades, random_skipped, strategy_skipped,
                    gap_filtered, threshold, skip_rate, run_idx, seed,
                )
                sim_results.append(sr)

                tag = f"gap{threshold}_skip{int(skip_rate * 100)}_run{run_idx}"
                write_tradewise_csv(
                    all_trade_results,
                    args.results_dir / f"short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_magap_{tag}_trades.csv",
                )
                write_daywise_csv(
                    day_results,
                    args.results_dir / f"short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_magap_{tag}_daywise.csv",
                )

                logger.info(
                    "DONE gap=%d skip=%.0f%% run=%d traded=%d net=%.2f cagr=%.2f%% dd=%.2f gap_filtered=%d 2sl_capped=%d",
                    threshold, skip_rate * 100, run_idx,
                    sr.traded_days, sr.net_pnl, sr.cagr, sr.max_drawdown,
                    sr.gap_filtered_entries, sr.days_2sl_capped,
                )
                print(
                    f"         traded={sr.traded_days}  net={fmt_inr(sr.net_pnl)}"
                    f"  CAGR={sr.cagr:.2f}%  DD={fmt_inr(sr.max_drawdown)}"
                    f"  gap_filtered={sr.gap_filtered_entries}  2SL_capped={sr.days_2sl_capped}"
                )

    summary_path = args.results_dir / SUMMARY_FILENAME
    write_summary(sim_results, summary_path)
    print(f"\nAll done. Summary: {summary_path}")


if __name__ == "__main__":
    main()
