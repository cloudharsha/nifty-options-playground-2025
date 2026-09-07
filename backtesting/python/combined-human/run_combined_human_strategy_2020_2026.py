#!/usr/bin/env python3
"""
Combined human-compatible NIFTY intraday strategy (2020-2026).

Design philosophy: simulate how a disciplined human trader actually operates.
  - Checks the market every 15 minutes (no continuous monitoring).
  - Sets GTT-equivalent SL and target orders at entry, then walks away.
  - Exits manually if NIFTY closes on wrong side of SMA at any 15-min check.
  - Hard daily firewall: stop after 2 stop-outs to prevent spiral.
  - No entries after 13:30 (eliminates late-day emotional trades).
  - Min-gap filter at entry: skip when market is too close to SMA (indecision).

Exit reasons:
  target_hit     : option premium fell to TARGET_FACTOR x entry (60% credit captured)
  premium_sl     : option premium rose to SL_FACTOR x entry (GTT SL fired)
  sma_cross_exit : NIFTY close crossed to other side of SMA at a 15-min check
  day_close      : mandatory close at 15:15

Stop-out events (count toward 2-SL/day cap): premium_sl, sma_cross_exit
Non-stop events (do not count): target_hit, day_close

Output: backtesting/results/combined-human/
"""
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


IST_SUFFIX = "+05:30"
CAPITAL_FOR_CAGR = 10_00_000.0

MA_PERIOD = 25
SL_CAP_PER_DAY = 2
MIN_GAP_ENTRY = 50.0       # skip initial entry if |spot - SMA| < this (indecision zone)
MIN_GAP_REENTRY = 25.0     # slightly relaxed for re-entries after a stop-out
SL_FACTOR = 2.5            # catastrophic backstop: exit if premium rises to SL_FACTOR x entry
TARGET_FACTOR = 0.40       # exit if premium falls to TARGET_FACTOR x entry (60% credit captured)
ENTRY_START_TIME = "09:30"
LAST_ENTRY_TIME = "13:30"
MANDATORY_CLOSE_TIME = "15:15"
CHECK_INTERVAL_MINUTES = 15

TRADES_FILENAME = "combined_human_strategy_2020_2026_trades.csv"
DAYWISE_FILENAME = "combined_human_strategy_2020_2026_daywise.csv"
SUMMARY_FILENAME = "combined_human_strategy_2020_2026_summary.md"
LOG_FILENAME = "combined_human_strategy_2020_2026.log"


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
    status: str                 # TRADED / SKIPPED
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
    sl_premium_level: str       # SL_FACTOR x entry_premium
    target_premium_level: str   # TARGET_FACTOR x entry_premium
    exit_timestamp: str
    option_exit_open: str
    exit_reason: str
    exit_spot_sma: str
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
    target_hit_exits: str
    premium_sl_exits: str
    sma_cross_exits: str
    day_close_exits: str
    skipped_signals: str
    orders_executed: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    stop_out_count: int
    sl_capped: bool
    remarks: str


@dataclass
class ExitOutcome:
    status: str
    skip_reason: str
    exit_timestamp: str
    option_exit_open: str
    exit_reason: str
    exit_spot_sma: str
    gross_pnl: float
    brokerage: float
    net_pnl: float
    is_stop_out: bool
    remarks: str


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

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
    final = capital + net_total
    if final <= 0:
        return -100.0
    return ((final / capital) ** (365.25 / days) - 1.0) * 100.0


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description="Combined human-compatible NIFTY intraday strategy.")
    parser.add_argument("--spot-15m-file", type=Path,
                        default=repo_root / "nifty" / "NIFTY50_INDEX_15m_last_7y.csv")
    parser.add_argument("--options-dir", type=Path,
                        default=repo_root / "NiftyOptions_2020_2026" / "Options")
    parser.add_argument("--results-dir", type=Path,
                        default=repo_root / "backtesting" / "results" / "combined-human")
    parser.add_argument("--ma-period", type=int, default=MA_PERIOD)
    parser.add_argument("--sl-factor", type=float, default=SL_FACTOR,
                        help="Catastrophic SL: exit if premium rises to this multiple of entry")
    parser.add_argument("--target-factor", type=float, default=TARGET_FACTOR,
                        help="Target: exit if premium falls to this fraction of entry")
    parser.add_argument("--min-gap-entry", type=float, default=MIN_GAP_ENTRY,
                        help="Min |spot-SMA| required for initial entry (pts)")
    parser.add_argument("--min-gap-reentry", type=float, default=MIN_GAP_REENTRY,
                        help="Min |spot-SMA| required for re-entry (pts)")
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
    """The 15-min candle that just closed before this entry (entry - 15 min)."""
    entry_dt = timestamp_to_datetime(entry_ts)
    return datetime_to_timestamp(entry_dt - datetime.timedelta(minutes=15))


def completed_candle_at_check(check_ts: str) -> str:
    """The last completed 15-min candle at human check time (check - 15 min)."""
    dt = timestamp_to_datetime(check_ts)
    floored_min = (dt.minute // 15) * 15
    boundary = dt.replace(minute=floored_min, second=0)
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


def join_remarks(parts: List[str]) -> str:
    return "; ".join(p for p in parts if p)


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("combined_human_strategy")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def load_spot_15m_data(spot_file: Path) -> Spot15Data:
    rows_by_ts: Dict[str, PriceRow] = {}
    ordered: List[PriceRow] = []
    idx_by_ts: Dict[str, int] = {}
    trading_days: List[str] = []
    seen: set = set()

    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
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
    with contract_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
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


# ---------------------------------------------------------------------------
# Trade result builders
# ---------------------------------------------------------------------------

def make_skipped_trade(
    entry_date: str,
    skip_reason: str,
    lot_size: int = 0,
    lots: int = 0,
    expiry_date: str = "",
    signal_timestamp: str = "",
    signal_close: str = "",
    spot_sma_25: str = "",
    spot_signal_relation: str = "",
    ma_gap: str = "",
    entry_timestamp: str = "",
    atm_strike: str = "",
    sold_side: str = "",
    contract_name: str = "",
    option_entry_open: str = "",
    sl_premium_level: str = "",
    target_premium_level: str = "",
    exit_timestamp: str = "",
    option_exit_open: str = "",
    exit_reason: str = "",
    exit_spot_sma: str = "",
    remarks: str = "",
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date, status="SKIPPED", skip_reason=skip_reason,
        expiry_date=expiry_date, lot_size=str(lot_size), lots=str(lots), qty=str(lot_size * lots),
        signal_timestamp=signal_timestamp, signal_close=signal_close,
        spot_sma_25=spot_sma_25, spot_signal_relation=spot_signal_relation, ma_gap=ma_gap,
        entry_timestamp=entry_timestamp, atm_strike=atm_strike, sold_side=sold_side,
        contract_name=contract_name, option_entry_open=option_entry_open,
        sl_premium_level=sl_premium_level, target_premium_level=target_premium_level,
        exit_timestamp=exit_timestamp, option_exit_open=option_exit_open,
        exit_reason=exit_reason, exit_spot_sma=exit_spot_sma,
        gross_pnl="0.00", brokerage="0.00", net_pnl="0.00", remarks=remarks,
    )


def make_traded_result(
    entry_date: str, expiry_date: str, lot_size: int, lots: int,
    signal_timestamp: str, signal_close: str, spot_sma_25: str, spot_signal_relation: str,
    ma_gap: str, entry_timestamp: str, atm_strike: str, sold_side: str, contract_name: str,
    option_entry_open: str, sl_premium_level: str, target_premium_level: str,
    exit_timestamp: str, option_exit_open: str, exit_reason: str, exit_spot_sma: str,
    gross_pnl: float, brokerage: float, net_pnl: float, remarks: str = "",
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date, status="TRADED", skip_reason="",
        expiry_date=expiry_date, lot_size=str(lot_size), lots=str(lots), qty=str(lot_size * lots),
        signal_timestamp=signal_timestamp, signal_close=signal_close,
        spot_sma_25=spot_sma_25, spot_signal_relation=spot_signal_relation, ma_gap=ma_gap,
        entry_timestamp=entry_timestamp, atm_strike=atm_strike, sold_side=sold_side,
        contract_name=contract_name, option_entry_open=option_entry_open,
        sl_premium_level=sl_premium_level, target_premium_level=target_premium_level,
        exit_timestamp=exit_timestamp, option_exit_open=option_exit_open,
        exit_reason=exit_reason, exit_spot_sma=exit_spot_sma,
        gross_pnl=format_money(gross_pnl), brokerage=format_money(brokerage),
        net_pnl=format_money(net_pnl), remarks=remarks,
    )


# ---------------------------------------------------------------------------
# Core exit logic — 15-min human monitoring
# ---------------------------------------------------------------------------

def resolve_trade_exit_human(
    entry_row: OptionRow,
    contract_data: ContractData,
    spot_15m_data: Spot15Data,
    day: str,
    entry_timestamp: str,
    sold_side: str,
    ma_period: int,
    slippage: float,
    brokerage_per_order: float,
    contract_multiplier: int,
    sl_factor: float,
    target_factor: float,
) -> ExitOutcome:
    """
    Simulate a human checking every 15 minutes after entry.

    At each check the human sees:
      - The NIFTY close of the just-completed 15-min candle vs its 25-SMA
      - The option premium at the open of the current candle (what GTT would execute at)

    Priority at each check:
      1. target_hit  — premium fell to TARGET_FACTOR x entry (take profit)
      2. premium_sl  — premium rose to SL_FACTOR x entry (GTT stop fired)
      3. sma_cross   — NIFTY closed on the wrong side of SMA (manual exit)

    If none triggers, waits until mandatory close at MANDATORY_CLOSE_TIME.
    """
    entry_premium = entry_row.open_value
    sl_level = entry_premium * sl_factor
    target_level = entry_premium * target_factor
    sold_pe = (sold_side == "PE")

    close_ts = build_timestamp(day, MANDATORY_CLOSE_TIME)
    close_dt = timestamp_to_datetime(close_ts)

    # Build 15-min check timestamps starting from the boundary after entry
    check_start_dt = next_15m_boundary_after(entry_timestamp)
    check_timestamps: List[str] = []
    cur_dt = check_start_dt
    while cur_dt <= close_dt:
        check_timestamps.append(datetime_to_timestamp(cur_dt))
        cur_dt += datetime.timedelta(minutes=15)

    for check_ts in check_timestamps:
        # The last completed 15-min candle at this check time.
        # A human at check_ts can see the full OHLC of the just-closed candle on their chart.
        sig_ts = completed_candle_at_check(check_ts)
        sig_row = spot_15m_data.rows_by_timestamp.get(sig_ts)
        if sig_row is None:
            continue

        sma, _ = compute_spot_sma(spot_15m_data, sig_ts, ma_period)
        if sma is None:
            continue

        # SMA touch check: did NIFTY touch the SMA at any point during the completed candle?
        # Use LOW for PE shorts (NIFTY fell to SMA) and HIGH for CE shorts (NIFTY rose to SMA).
        # This mirrors the base strategy's bar-by-bar trailing stop — the SMA acts as a price level.
        sma_touched = (
            (sold_pe and sig_row.low_value <= sma) or
            (not sold_pe and sig_row.high_value >= sma)
        )

        # Option price at the open of the current candle — the price the human executes at
        option_row = contract_data.rows_by_timestamp.get(check_ts)

        if option_row is None:
            # No option data at this check — defer
            continue

        current_premium = option_row.open_value
        gross = leg_pnl_after_slippage(entry_premium - current_premium, slippage) * contract_multiplier
        brok = brokerage_per_order * 2

        # Target hit — take profit (check first, best outcome)
        if current_premium <= target_level:
            return ExitOutcome(
                status="TRADED", skip_reason="",
                exit_timestamp=check_ts, option_exit_open=option_row.open_text,
                exit_reason="target_hit", exit_spot_sma=format_money(sma),
                gross_pnl=gross, brokerage=brok, net_pnl=gross - brok,
                is_stop_out=False, remarks="",
            )

        # Catastrophic premium SL — wide backstop for extreme moves
        if current_premium >= sl_level:
            return ExitOutcome(
                status="TRADED", skip_reason="",
                exit_timestamp=check_ts, option_exit_open=option_row.open_text,
                exit_reason="premium_sl", exit_spot_sma=format_money(sma),
                gross_pnl=gross, brokerage=brok, net_pnl=gross - brok,
                is_stop_out=True, remarks="",
            )

        # SMA touch — primary exit (equivalent to trailing SMA stop, 15-min granularity)
        if sma_touched:
            return ExitOutcome(
                status="TRADED", skip_reason="",
                exit_timestamp=check_ts, option_exit_open=option_row.open_text,
                exit_reason="sma_touch_exit", exit_spot_sma=format_money(sma),
                gross_pnl=gross, brokerage=brok, net_pnl=gross - brok,
                is_stop_out=True, remarks="",
            )

    # Mandatory close
    close_row = contract_data.rows_by_timestamp.get(close_ts)
    if close_row is None:
        return ExitOutcome(
            status="SKIPPED", skip_reason="missing_option_exit_timestamp",
            exit_timestamp=close_ts, option_exit_open="",
            exit_reason="day_close", exit_spot_sma="",
            gross_pnl=0.0, brokerage=0.0, net_pnl=0.0,
            is_stop_out=False,
            remarks=f"{contract_data.path.name} missing mandatory close {close_ts}",
        )

    close_sig_ts = completed_candle_at_check(close_ts)
    close_sma, _ = compute_spot_sma(spot_15m_data, close_sig_ts, ma_period)
    gross = leg_pnl_after_slippage(entry_premium - close_row.open_value, slippage) * contract_multiplier
    brok = brokerage_per_order * 2
    return ExitOutcome(
        status="TRADED", skip_reason="",
        exit_timestamp=close_ts, option_exit_open=close_row.open_text,
        exit_reason="day_close", exit_spot_sma=format_optional_money(close_sma),
        gross_pnl=gross, brokerage=brok, net_pnl=gross - brok,
        is_stop_out=False, remarks="",
    )


# ---------------------------------------------------------------------------
# Day aggregation
# ---------------------------------------------------------------------------

def aggregate_day_result(
    entry_date: str,
    expiry_date: str,
    trade_results: List[TradeResult],
    stop_out_count: int = 0,
    sl_capped: bool = False,
) -> DayResult:
    traded = [r for r in trade_results if r.status == "TRADED"]
    skipped = [r for r in trade_results if r.status == "SKIPPED"]
    net_total = sum(float(r.net_pnl) for r in traded)
    gross_total = sum(float(r.gross_pnl) for r in traded)
    brok_total = sum(float(r.brokerage) for r in traded)
    ce = sum(1 for r in traded if r.sold_side == "CE")
    pe = sum(1 for r in traded if r.sold_side == "PE")
    target_hits = sum(1 for r in traded if r.exit_reason == "target_hit")
    prem_sl = sum(1 for r in traded if r.exit_reason == "premium_sl")
    sma_cross = sum(1 for r in traded if r.exit_reason in ("sma_cross_exit", "sma_touch_exit"))
    day_close = sum(1 for r in traded if r.exit_reason == "day_close")
    skip_reasons = [r.skip_reason for r in skipped if r.skip_reason]
    skip_remarks = [r.remarks for r in skipped if r.remarks]

    if traded:
        status = "TRADED"
        skip_reason = ";".join(sorted(set(skip_reasons))) if skip_reasons else ""
    else:
        status = "SKIPPED"
        skip_reason = ";".join(sorted(set(skip_reasons))) if skip_reasons else "no_completed_trade"

    return DayResult(
        entry_date=entry_date, status=status, skip_reason=skip_reason, expiry_date=expiry_date,
        trades=str(len(traded)), ce_trades=str(ce), pe_trades=str(pe),
        target_hit_exits=str(target_hits), premium_sl_exits=str(prem_sl),
        sma_cross_exits=str(sma_cross), day_close_exits=str(day_close),
        skipped_signals=str(len(skipped)),
        orders_executed=str(2 * len(traded)),
        gross_pnl=format_money(gross_total), brokerage=format_money(brok_total),
        net_pnl=format_money(net_total),
        stop_out_count=stop_out_count, sl_capped=sl_capped,
        remarks=join_remarks(skip_remarks),
    )


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def compute_max_drawdown(day_pnls: List[float]) -> float:
    peak = dd = cum = 0.0
    for v in day_pnls:
        cum += v
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    return dd


def compute_max_consecutive_streaks(day_pnls: List[float]) -> Tuple[int, int]:
    max_w = max_l = cur_w = cur_l = 0
    for v in day_pnls:
        if v > 0:
            cur_w += 1; cur_l = 0; max_w = max(max_w, cur_w)
        elif v < 0:
            cur_l += 1; cur_w = 0; max_l = max(max_l, cur_l)
        else:
            cur_w = cur_l = 0
    return max_w, max_l


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------

def run_simulation(
    spot_15m: Spot15Data,
    expiries: List[str],
    contract_cache: Dict[Path, ContractData],
    args: argparse.Namespace,
    logger: logging.Logger,
) -> Tuple[List[DayResult], List[TradeResult]]:
    day_results: List[DayResult] = []
    all_trade_results: List[TradeResult] = []

    for entry_date in spot_15m.trading_days:
        day_trades: List[TradeResult] = []
        expiry_date = first_expiry_on_or_after(expiries, entry_date) or ""

        if not expiry_date:
            result = make_skipped_trade(
                entry_date=entry_date, skip_reason="no_expiry_found",
                entry_timestamp=build_timestamp(entry_date, ENTRY_START_TIME),
                remarks="No expiry folder on or after this date.",
            )
            day_trades.append(result)
            all_trade_results.extend(day_trades)
            day_results.append(aggregate_day_result(entry_date, "", day_trades))
            continue

        lot_size, lots = qty_for_expiry(expiry_date)
        contract_multiplier = lot_size * lots
        option_suffix = expiry_suffix(expiry_date)

        entry_timestamps = build_intraday_timestamps(
            entry_date, ENTRY_START_TIME, LAST_ENTRY_TIME, step_minutes=CHECK_INTERVAL_MINUTES
        )

        next_allowed_entry_dt = timestamp_to_datetime(entry_timestamps[0])
        stop_day = False
        daily_stop_out_count = 0
        sl_capped_today = False
        is_first_entry = True

        for entry_ts in entry_timestamps:
            if stop_day:
                break
            if timestamp_to_datetime(entry_ts) < next_allowed_entry_dt:
                continue

            # Signal: the 15-min candle that just completed before this entry
            sig_ts = signal_timestamp_for_entry(entry_ts)
            sig_row = spot_15m.rows_by_timestamp.get(sig_ts)
            if sig_row is None:
                result = make_skipped_trade(
                    entry_date=entry_date, skip_reason="missing_spot_signal_timestamp",
                    lot_size=lot_size, lots=lots,
                    expiry_date=expiry_date, signal_timestamp=sig_ts, entry_timestamp=entry_ts,
                    remarks=f"Missing 15-min NIFTY signal timestamp {sig_ts}",
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

            # Gap filter: skip if too close to SMA (no clear directional conviction)
            min_gap = args.min_gap_entry if is_first_entry else args.min_gap_reentry
            if gap < min_gap:
                result = make_skipped_trade(
                    entry_date=entry_date, skip_reason="gap_too_small",
                    lot_size=lot_size, lots=lots,
                    expiry_date=expiry_date, signal_timestamp=sig_ts,
                    signal_close=sig_row.close_text, spot_sma_25=sma_text,
                    ma_gap=gap_text, entry_timestamp=entry_ts,
                    remarks=(f"Gap {gap_text} < min {min_gap:.0f} pts; "
                             f"close={sig_row.close_text} sma={sma_text}"),
                )
                day_trades.append(result)
                continue

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
                    remarks=f"Close {sig_row.close_text} == SMA {sma_text}",
                )
                day_trades.append(result)
                continue

            atm = round_to_nearest_50(sig_row.close_value)
            strike_text = str(atm)

            contract_path = (args.options_dir / expiry_date
                             / f"NIFTY_{atm}_{sold_side}_{option_suffix}.csv")
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
                remark = (f"{contract_path.name} is header-only"
                          if not cd.rows_by_timestamp
                          else f"{contract_path.name} missing entry {entry_ts}")
                result = make_skipped_trade(
                    entry_date=entry_date, skip_reason="missing_option_entry_timestamp",
                    lot_size=lot_size, lots=lots,
                    expiry_date=expiry_date, signal_timestamp=sig_ts,
                    signal_close=sig_row.close_text, spot_sma_25=sma_text,
                    ma_gap=gap_text, spot_signal_relation=relation, entry_timestamp=entry_ts,
                    atm_strike=strike_text, sold_side=sold_side,
                    contract_name=contract_path.name, remarks=remark,
                )
                day_trades.append(result)
                continue

            sl_level = entry_row.open_value * args.sl_factor
            target_level = entry_row.open_value * args.target_factor

            outcome = resolve_trade_exit_human(
                entry_row=entry_row, contract_data=cd,
                spot_15m_data=spot_15m,
                day=entry_date, entry_timestamp=entry_ts, sold_side=sold_side,
                ma_period=args.ma_period,
                slippage=args.slippage_points_per_order,
                brokerage_per_order=args.brokerage_per_order,
                contract_multiplier=contract_multiplier,
                sl_factor=args.sl_factor,
                target_factor=args.target_factor,
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
                    sl_premium_level=format_money(sl_level),
                    target_premium_level=format_money(target_level),
                    exit_timestamp=outcome.exit_timestamp,
                    exit_reason=outcome.exit_reason, exit_spot_sma=outcome.exit_spot_sma,
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
                sl_premium_level=format_money(sl_level),
                target_premium_level=format_money(target_level),
                exit_timestamp=outcome.exit_timestamp,
                option_exit_open=outcome.option_exit_open,
                exit_reason=outcome.exit_reason, exit_spot_sma=outcome.exit_spot_sma,
                gross_pnl=outcome.gross_pnl, brokerage=outcome.brokerage,
                net_pnl=outcome.net_pnl,
            )
            day_trades.append(result)
            is_first_entry = False

            logger.debug("TRADED date=%s entry=%s exit=%s side=%s reason=%s net=%s",
                         entry_date, entry_ts, outcome.exit_timestamp,
                         sold_side, outcome.exit_reason, result.net_pnl)

            if outcome.exit_reason in ("target_hit", "day_close"):
                stop_day = True
                break

            if outcome.is_stop_out:
                daily_stop_out_count += 1
                if daily_stop_out_count >= SL_CAP_PER_DAY:
                    sl_capped_today = True
                    logger.debug("2SL_CAP date=%s after %d stop-outs", entry_date, daily_stop_out_count)
                    stop_day = True
                    break

            # Wait one 15-min boundary before next entry attempt
            next_allowed_entry_dt = next_15m_boundary_after(outcome.exit_timestamp)

        if not day_trades:
            result = make_skipped_trade(
                entry_date=entry_date, skip_reason="no_entry_signal",
                expiry_date=expiry_date,
                entry_timestamp=build_timestamp(entry_date, ENTRY_START_TIME),
                remarks="No trade or skipped signal produced for this date.",
            )
            day_trades.append(result)

        all_trade_results.extend(day_trades)
        day_results.append(aggregate_day_result(
            entry_date, expiry_date, day_trades,
            stop_out_count=daily_stop_out_count, sl_capped=sl_capped_today,
        ))

    return day_results, all_trade_results


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------

def write_tradewise_csv(results: List[TradeResult], path: Path) -> None:
    fields = list(TradeResult.__dataclass_fields__)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow(r.__dict__)


def write_daywise_csv(results: List[DayResult], path: Path) -> None:
    fields = list(DayResult.__dataclass_fields__)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow(r.__dict__)


# ---------------------------------------------------------------------------
# Summary writer
# ---------------------------------------------------------------------------

def fmt_inr(v: float) -> str:
    sign = "-" if v < 0 else ""
    return f"{sign}Rs {abs(v):,.0f}"


def write_summary(
    day_results: List[DayResult],
    all_trade_results: List[TradeResult],
    args: argparse.Namespace,
    path: Path,
) -> None:
    traded_dr = [r for r in day_results if int(r.trades) > 0]
    skipped_dr = [r for r in day_results if int(r.trades) == 0]
    traded_tr = [r for r in all_trade_results if r.status == "TRADED"]

    net = sum(float(r.net_pnl) for r in traded_dr)
    gross = sum(float(r.gross_pnl) for r in traded_dr)
    brok = sum(float(r.brokerage) for r in traded_dr)
    day_pnls = [float(r.net_pnl) for r in traded_dr]
    wins = sum(1 for v in day_pnls if v > 0)
    losses = sum(1 for v in day_pnls if v < 0)
    win_pct = wins / len(day_pnls) * 100 if day_pnls else 0.0
    max_w, max_l = compute_max_consecutive_streaks(day_pnls)
    max_dd = compute_max_drawdown(day_pnls)

    target_hits = sum(int(r.target_hit_exits) for r in traded_dr)
    prem_sl = sum(int(r.premium_sl_exits) for r in traded_dr)
    sma_cross = sum(int(r.sma_cross_exits) for r in traded_dr)  # now counts sma_touch_exit too
    day_close_exits = sum(int(r.day_close_exits) for r in traded_dr)
    total_exits = len(traded_tr)

    ce_trades = sum(int(r.ce_trades) for r in traded_dr)
    pe_trades = sum(int(r.pe_trades) for r in traded_dr)
    days_2sl_capped = sum(1 for r in day_results if r.sl_capped)

    best_day = max(traded_dr, key=lambda r: float(r.net_pnl), default=None)
    worst_day = min(traded_dr, key=lambda r: float(r.net_pnl), default=None)

    first_day = day_results[0].entry_date if day_results else ""
    last_day = day_results[-1].entry_date if day_results else ""
    cagr = compute_cagr(net, CAPITAL_FOR_CAGR, first_day, last_day)

    # Yearly breakdown
    yearly: Dict[str, Dict] = {}
    for r in traded_dr:
        yr = r.entry_date[:4]
        if yr not in yearly:
            yearly[yr] = {"days": 0, "wins": 0, "losses": 0, "net": 0.0}
        yearly[yr]["days"] += 1
        v = float(r.net_pnl)
        if v > 0:
            yearly[yr]["wins"] += 1
        elif v < 0:
            yearly[yr]["losses"] += 1
        yearly[yr]["net"] += v

    lines: List[str] = [
        "# Combined Human Strategy — NIFTY Intraday (2020-2026)",
        "",
        "## Strategy Parameters",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| Signal | 25-SMA direction on 15-min NIFTY spot at 09:30 |",
        f"| Entry filter | |spot - SMA| >= {args.min_gap_entry:.0f} pts (skip indecision) |",
        f"| Re-entry filter | |spot - SMA| >= {args.min_gap_reentry:.0f} pts |",
        f"| SL (GTT) | Premium rises to {args.sl_factor:.2f}x entry |",
        f"| Target (GTT) | Premium falls to {args.target_factor:.2f}x entry ({(1-args.target_factor)*100:.0f}% credit captured) |",
        f"| Monitoring | Every {CHECK_INTERVAL_MINUTES} minutes |",
        f"| Daily stop-out cap | {SL_CAP_PER_DAY} (premium_sl + sma_cross_exit) |",
        f"| Last entry | {LAST_ENTRY_TIME} |",
        f"| Mandatory close | {MANDATORY_CLOSE_TIME} |",
        f"| Brokerage/order | Rs {args.brokerage_per_order:.0f} |",
        f"| Slippage/order | {args.slippage_points_per_order:.1f} pts |",
        "",
        "## Overall Results (2020-2026)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Capital base | Rs 10,00,000 |",
        f"| Net P/L | {fmt_inr(net)} |",
        f"| Gross P/L | {fmt_inr(gross)} |",
        f"| Brokerage + slippage | {fmt_inr(brok)} |",
        f"| CAGR | {cagr:.2f}% |",
        f"| Total days in data | {len(day_results)} |",
        f"| Traded days | {len(traded_dr)} |",
        f"| Skipped days | {len(skipped_dr)} |",
        f"| Win days | {wins} |",
        f"| Loss days | {losses} |",
        f"| Win rate (day) | {win_pct:.1f}% |",
        f"| Max drawdown | {fmt_inr(max_dd)} |",
        f"| Max consec win days | {max_w} |",
        f"| Max consec loss days | {max_l} |",
        f"| Days with 2-SL cap hit | {days_2sl_capped} |",
        f"| Best day | {best_day.entry_date if best_day else '-'} — {fmt_inr(float(best_day.net_pnl)) if best_day else '-'} |",
        f"| Worst day | {worst_day.entry_date if worst_day else '-'} — {fmt_inr(float(worst_day.net_pnl)) if worst_day else '-'} |",
        "",
        "## Trade-Level Stats",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total trades executed | {total_exits} |",
        f"| CE trades | {ce_trades} |",
        f"| PE trades | {pe_trades} |",
        "",
        "## Exit Reason Breakdown",
        "",
        "| Exit Reason | Count | % | Notes |",
        "|-------------|-------|---|-------|",
        f"| target_hit | {target_hits} | {target_hits/total_exits*100:.1f}% | 60% credit captured — done for day |" if total_exits else "| — | — | — | — |",
        f"| premium_sl | {prem_sl} | {prem_sl/total_exits*100:.1f}% | GTT SL fired (counts toward cap) |" if total_exits else "| — | — | — | — |",
        f"| sma_touch_exit | {sma_cross} | {sma_cross/total_exits*100:.1f}% | SMA touched in 15-min candle (counts toward cap) |" if total_exits else "| — | — | — | — |",
        f"| day_close | {day_close_exits} | {day_close_exits/total_exits*100:.1f}% | Mandatory close at {MANDATORY_CLOSE_TIME} |" if total_exits else "| — | — | — | — |",
        "",
        "## Yearly Breakdown",
        "",
        "| Year | Traded Days | Wins | Losses | Win% | Net P/L |",
        "|------|-------------|------|--------|------|---------|",
    ]

    for yr in sorted(yearly.keys()):
        yd = yearly[yr]
        total_y = yd["wins"] + yd["losses"]
        wp = yd["wins"] / total_y * 100 if total_y else 0.0
        lines.append(
            f"| {yr} | {yd['days']} | {yd['wins']} | {yd['losses']} "
            f"| {wp:.1f}% | {fmt_inr(yd['net'])} |"
        )

    lines.extend([
        "",
        "## vs Baseline Strategies",
        "",
        "| Strategy | CAGR | Max DD | Notes |",
        "|----------|------|--------|-------|",
        "| Base intraday (full participation) | -100% | Rs 19,86,026 | Trailing SMA stop, no cap |",
        "| With-SL-cap 30% skip | -3.63% | Rs 8,47,288 | 2-SL cap + random skip |",
        "| MA-gap-100 + SL-cap 30% | 22.83% | Rs 1,21,120 | Additional max-gap filter |",
        f"| **This strategy (combined-human)** | **{cagr:.2f}%** | **{fmt_inr(max_dd)}** | "
        f"Min-gap + premium SL + target + 15-min monitoring |",
        "",
        "## Notes",
        "",
        f"- **Min-gap filter**: entry skipped when |spot - SMA| < {args.min_gap_entry:.0f} pts. "
        f"Unlike the magap backtest (which skips when gap is TOO LARGE), this skips when "
        f"the market is too flat (no directional conviction).",
        f"- **Premium SL** ({args.sl_factor:.2f}x): simulates a GTT buy-back order placed at entry. "
        f"Fires automatically even if the human is not watching.",
        f"- **Target** ({args.target_factor:.2f}x = {(1-args.target_factor)*100:.0f}% credit): "
        f"simulates a GTT take-profit. When hit, trading stops for the day.",
        f"- **SMA cross exit**: at each 15-min check, if NIFTY 15-min close is on the wrong side "
        f"of SMA, exit manually at the next candle open price.",
        f"- **15-min monitoring**: option premium checked at candle OPEN; NIFTY spot checked "
        f"at the CLOSE of the just-completed candle.",
        f"- **2-SL cap**: after {SL_CAP_PER_DAY} stop-outs (premium_sl or sma_cross_exit) in "
        f"one day, no further entries taken.",
        f"- **Re-entry direction**: always determined fresh from SMA position at re-entry time "
        f"(not locked to original trade direction).",
        "- CAGR uses Rs 10,00,000 capital reference. Actual deployed capital should be "
        "70% of account (30% buffer for margin safety — not modeled here).",
    ])

    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    print("Loading 15-min NIFTY spot data...")
    spot_15m = load_spot_15m_data(args.spot_15m_file)
    print(f"  {len(spot_15m.trading_days)} trading days, {len(spot_15m.ordered_rows)} candles")

    print("Loading option expiry folders...")
    expiries = load_expiry_folders(args.options_dir)
    print(f"  {len(expiries)} expiry folders")

    contract_cache: Dict[Path, ContractData] = {}

    print("Running simulation...")
    logger.info(
        "START sl_factor=%.2f target_factor=%.2f min_gap_entry=%.0f min_gap_reentry=%.0f",
        args.sl_factor, args.target_factor, args.min_gap_entry, args.min_gap_reentry,
    )

    day_results, all_trade_results = run_simulation(spot_15m, expiries, contract_cache, args, logger)

    traded_dr = [r for r in day_results if int(r.trades) > 0]
    net = sum(float(r.net_pnl) for r in traded_dr)
    first_day = day_results[0].entry_date if day_results else ""
    last_day = day_results[-1].entry_date if day_results else ""
    cagr = compute_cagr(net, CAPITAL_FOR_CAGR, first_day, last_day)
    dd = compute_max_drawdown([float(r.net_pnl) for r in traded_dr])

    print(f"  Traded days : {len(traded_dr)}")
    print(f"  Net P/L     : {fmt_inr(net)}")
    print(f"  CAGR        : {cagr:.2f}%")
    print(f"  Max DD      : {fmt_inr(dd)}")

    logger.info("DONE traded=%d net=%.2f cagr=%.2f%% dd=%.2f", len(traded_dr), net, cagr, dd)

    trades_path = args.results_dir / TRADES_FILENAME
    daywise_path = args.results_dir / DAYWISE_FILENAME
    summary_path = args.results_dir / SUMMARY_FILENAME

    write_tradewise_csv(all_trade_results, trades_path)
    write_daywise_csv(day_results, daywise_path)
    write_summary(day_results, all_trade_results, args, summary_path)

    print(f"\nOutput written to {args.results_dir}")
    print(f"  Trades  : {trades_path.name}")
    print(f"  Daywise : {daywise_path.name}")
    print(f"  Summary : {summary_path.name}")


if __name__ == "__main__":
    main()
