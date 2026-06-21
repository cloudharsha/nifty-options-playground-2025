#!/usr/bin/env python3
"""
Heads & Tails — Random Single-Leg ATM Short Option, NIFTY Weekly (all data)

09:30  Randomly sell ATM CE or PE (coin flip).
       SL   = 20% rise  above entry → loss
       Target = 50% decay below entry → profit

       If SL hit BEFORE 12:00 → sell OPPOSITE leg at 12:00, same SL/target.
       If SL hit AT/AFTER 12:00 → no more trades.
       Target hit any time → done for day (no second trade).
       No hit → exit both at 15:20.

Qty: ~300 (NIFTY lot-size schedule; same as other scripts).
Tested 5 independent runs with fixed seeds to measure variance from random pick.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

IST_SUFFIX    = "+05:30"
BASE_FILENAME = "heads_tails_nifty"
DAYWISE_CSV   = f"{BASE_FILENAME}_daywise.csv"
SUMMARY_MD    = f"{BASE_FILENAME}_summary.md"
LOG_FILE      = f"{BASE_FILENAME}.log"
WEEKDAY_NAMES = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

ENTRY_TIME  = "09:30"
MIDDAY_TIME = "12:00"
EXIT_TIME   = "15:20"
SL_PCT      = 0.20
TARGET_PCT  = 0.50
NUM_RUNS    = 5
SEEDS       = [42, 137, 2025, 777, 1984]
BROK_PER_ORDER = 25.0    # ₹ per order
SLIP_PER_ORDER = 0.5     # points per order side
BROK_PER_TRADE = BROK_PER_ORDER * 2   # 2 orders (sell + buyback) per trade


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class PriceRow:
    timestamp: str
    open_value: float
    open_text: str
    high_value: float
    low_value: float


@dataclass
class ContractData:
    path: Path
    rows_by_timestamp: Dict[str, PriceRow]


@dataclass
class DayData:
    """Deterministic per-day data loaded once, reused across all 5 runs."""
    entry_date: str
    day_of_week: str
    expiry_date: str
    lot_size: int
    num_lots: int
    qty: int
    atm_strike: int
    entry_ts: str
    midday_ts: str
    exit_ts: str
    ce_contract: ContractData = field(repr=False)
    pe_contract: ContractData = field(repr=False)
    ce_morning_open: float     # CE open at 09:30
    pe_morning_open: float     # PE open at 09:30
    ce_noon_open: float        # CE open at 12:00 (0.0 if missing)
    pe_noon_open: float        # PE open at 12:00 (0.0 if missing)


@dataclass
class SkippedDay:
    entry_date: str
    day_of_week: str
    skip_reason: str
    details: str = ""


@dataclass
class TradeResult:
    entry_date: str
    day_of_week: str
    run_number: int
    seed: int
    expiry_date: str
    atm_strike: int
    qty: int
    # morning
    morning_choice: str
    morning_open: float
    morning_sl_price: float
    morning_target_price: float
    morning_exit_ts: str
    morning_exit_price: float
    morning_exit_reason: str
    morning_points_pnl: float
    morning_gross_pnl: float
    morning_net_pnl: float
    # noon (second trade)
    second_trade: bool
    second_choice: str
    second_open: float
    second_exit_ts: str
    second_exit_price: float
    second_exit_reason: str
    second_points_pnl: float
    second_gross_pnl: float
    second_net_pnl: float
    # combined
    total_net_pnl: float


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    p = argparse.ArgumentParser(description="Heads & Tails NIFTY single-leg random strategy.")
    p.add_argument("--spot-file", type=Path,
                   default=repo_root / "nifty" / "NIFTY50_INDEX_5m_last_7y.csv")
    p.add_argument("--options-dir", type=Path,
                   default=repo_root / "NiftyOptions_2020_2026" / "Options")
    p.add_argument("--results-dir", type=Path,
                   default=repo_root / "backtesting" / "results")
    p.add_argument("--capital", type=float, default=500_000.0)
    return p.parse_args()


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def fmt(v: float) -> str:
    return f"{v:.2f}"


def build_ts(day: str, time_text: str) -> str:
    h, m = time_text.split(":")
    return f"{day}T{h}:{m}:00{IST_SUFFIX}"


def expiry_suffix(expiry_date: str) -> str:
    return datetime.datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%d_%b_%y").upper()


def round_to_50(price: float) -> int:
    rem = price % 50
    base = int(price - rem)
    return base if rem < 25 else base + 50


def get_lot_config(expiry_date: str) -> Tuple[int, int]:
    d = datetime.date.fromisoformat(expiry_date)
    if d <= datetime.date(2021, 10, 6):  return 75, 4
    if d <= datetime.date(2024, 4, 25):  return 50, 6
    if d <= datetime.date(2024, 11, 21): return 25, 12
    if d <= datetime.date(2025, 12, 30): return 75, 4
    return 65, 5


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger(BASE_FILENAME)
    for h in logger.handlers:
        h.close()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(fh)
    logger.propagate = False
    return logger


def close_logger(logger: logging.Logger) -> None:
    for h in logger.handlers:
        h.close()
    logger.handlers.clear()


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------

def load_spot_opens(spot_file: Path) -> Tuple[List[str], Dict[str, Tuple[float, str]]]:
    trading_days: List[str] = []
    seen: Dict[str, bool] = {}
    spot_open: Dict[str, Tuple[float, str]] = {}
    marker = f"T{ENTRY_TIME}:00"
    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts  = row["timestamp"]
            day = ts[:10]
            if day not in seen:
                seen[day] = True
                trading_days.append(day)
            if marker in ts and day not in spot_open:
                spot_open[day] = (float(row["open"]), row["open"])
    return trading_days, spot_open


def load_expiry_folders(options_dir: Path) -> List[str]:
    return sorted(p.name for p in options_dir.iterdir() if p.is_dir())


def first_expiry_on_or_after(expiries: List[str], date: str) -> Optional[str]:
    for e in expiries:
        if e >= date:
            return e
    return None


def load_contract(path: Path, cache: Dict[Path, Optional[ContractData]]) -> Optional[ContractData]:
    if path in cache:
        return cache[path]
    if not path.exists():
        cache[path] = None
        return None
    rows: Dict[str, PriceRow] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            rows[ts] = PriceRow(
                timestamp=ts,
                open_value=float(row["open"]),
                open_text=row["open"],
                high_value=float(row["high"]),
                low_value=float(row["low"]),
            )
    cache[path] = ContractData(path=path, rows_by_timestamp=rows)
    return cache[path]


# ---------------------------------------------------------------------------
# SL + TARGET RESOLUTION (short option position)
# ---------------------------------------------------------------------------

def resolve_sell_leg(
    contract: ContractData,
    entry_open: float,
    entry_ts: str,
    exit_ts: str,
) -> Tuple[str, float, str, float, float]:
    """
    Walk 1-minute candles from entry_ts to exit_ts for a short option.
      gap_sl     : opens at/above SL  → fill at open
      gap_target : opens at/below target → fill at open
      sl         : high reaches SL    → fill at SL price
      target     : low reaches target → fill at target price
      day_close  : no trigger, exits at exit_ts open
    Returns (exit_ts, exit_price, reason, points_pnl, gross_pnl).
    NOTE: gross_pnl does NOT include slippage or brokerage.
    """
    sl_price     = entry_open * (1.0 + SL_PCT)
    target_price = entry_open * (1.0 - TARGET_PCT)
    window = sorted(ts for ts in contract.rows_by_timestamp if entry_ts <= ts <= exit_ts)

    for ts in window:
        row = contract.rows_by_timestamp[ts]
        if row.open_value >= sl_price:
            pts = entry_open - row.open_value
            return ts, row.open_value, "gap_sl", pts, pts
        if row.open_value <= target_price:
            pts = entry_open - row.open_value
            return ts, row.open_value, "gap_target", pts, pts
        if row.high_value >= sl_price:
            pts = entry_open - sl_price
            return ts, sl_price, "sl", pts, pts
        if row.low_value <= target_price:
            pts = entry_open - target_price
            return ts, target_price, "target", pts, pts

    exit_row = contract.rows_by_timestamp.get(exit_ts)
    if exit_row:
        pts = entry_open - exit_row.open_value
        return exit_ts, exit_row.open_value, "day_close", pts, pts

    candidates = [ts for ts in contract.rows_by_timestamp if ts <= exit_ts]
    if candidates:
        last_ts  = max(candidates)
        last_row = contract.rows_by_timestamp[last_ts]
        pts = entry_open - last_row.open_value
        return last_ts, last_row.open_value, "last_candle", pts, pts

    return exit_ts, entry_open, "missing_exit", 0.0, 0.0


def apply_costs(points_pnl: float, qty: int) -> Tuple[float, float, float]:
    """Returns (gross_pnl, brokerage, net_pnl) for one trade leg."""
    net_pts  = points_pnl - 2 * SLIP_PER_ORDER   # entry + exit slippage
    gross    = net_pts * qty
    net      = gross - BROK_PER_TRADE
    return gross, BROK_PER_TRADE, net


# ---------------------------------------------------------------------------
# PASS 1 — COLLECT DAY DATA (deterministic)
# ---------------------------------------------------------------------------

def collect_day_data(args: argparse.Namespace) -> Tuple[List[DayData], List[SkippedDay]]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILE)

    trading_days, spot_opens = load_spot_opens(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    cache: Dict[Path, Optional[ContractData]] = {}
    days: List[DayData]       = []
    skipped: List[SkippedDay] = []

    try:
        for entry_date in trading_days:
            wd = datetime.date.fromisoformat(entry_date).weekday()
            if wd >= 5:
                continue
            day_name  = WEEKDAY_NAMES[wd]
            entry_ts  = build_ts(entry_date, ENTRY_TIME)
            midday_ts = build_ts(entry_date, MIDDAY_TIME)
            exit_ts   = build_ts(entry_date, EXIT_TIME)

            spot = spot_opens.get(entry_date)
            if not spot:
                skipped.append(SkippedDay(entry_date, day_name,
                                          "missing_spot", f"No candle at {entry_ts}"))
                continue

            spot_val, _ = spot
            expiry_date = first_expiry_on_or_after(expiries, entry_date)
            if expiry_date is None:
                skipped.append(SkippedDay(entry_date, day_name, "no_expiry", ""))
                continue

            lot_size, num_lots = get_lot_config(expiry_date)
            qty    = lot_size * num_lots
            atm    = round_to_50(spot_val)
            suffix = expiry_suffix(expiry_date)

            ce_path = args.options_dir / expiry_date / f"NIFTY_{atm}_CE_{suffix}.csv"
            pe_path = args.options_dir / expiry_date / f"NIFTY_{atm}_PE_{suffix}.csv"
            ce = load_contract(ce_path, cache)
            pe = load_contract(pe_path, cache)

            if ce is None or pe is None:
                miss = ("CE " if ce is None else "") + ("PE" if pe is None else "")
                skipped.append(SkippedDay(entry_date, day_name, "missing_contract",
                                          f"Missing {miss.strip()} atm={atm}"))
                logger.info("SKIP %s missing_contract atm=%s", entry_date, atm)
                continue

            ce_m = ce.rows_by_timestamp.get(entry_ts)
            pe_m = pe.rows_by_timestamp.get(entry_ts)
            if ce_m is None or pe_m is None:
                miss = ("CE " if ce_m is None else "") + ("PE" if pe_m is None else "")
                skipped.append(SkippedDay(entry_date, day_name, "missing_entry_candle",
                                          f"Missing {miss.strip()} at {entry_ts}"))
                logger.info("SKIP %s missing_entry_candle atm=%s", entry_date, atm)
                continue

            ce_noon = ce.rows_by_timestamp.get(midday_ts)
            pe_noon = pe.rows_by_timestamp.get(midday_ts)

            days.append(DayData(
                entry_date=entry_date, day_of_week=day_name,
                expiry_date=expiry_date, lot_size=lot_size, num_lots=num_lots, qty=qty,
                atm_strike=atm, entry_ts=entry_ts, midday_ts=midday_ts, exit_ts=exit_ts,
                ce_contract=ce, pe_contract=pe,
                ce_morning_open=ce_m.open_value, pe_morning_open=pe_m.open_value,
                ce_noon_open=ce_noon.open_value if ce_noon else 0.0,
                pe_noon_open=pe_noon.open_value if pe_noon else 0.0,
            ))
            logger.info("LOADED %s day=%s expiry=%s atm=%s ce=%.2f pe=%.2f",
                        entry_date, day_name, expiry_date, atm,
                        ce_m.open_value, pe_m.open_value)

    except Exception:
        logger.exception("ERROR")
        raise
    finally:
        logger.info("Loaded=%s Skipped=%s", len(days), len(skipped))
        close_logger(logger)

    return days, skipped


# ---------------------------------------------------------------------------
# PASS 2 — SIMULATE ONE RUN
# ---------------------------------------------------------------------------

def simulate_run(days: List[DayData], run_number: int, seed: int) -> List[TradeResult]:
    rng     = random.Random(seed)
    results: List[TradeResult] = []

    for dd in days:
        morning_choice  = rng.choice(["CE", "PE"])
        opposite_choice = "PE" if morning_choice == "CE" else "CE"

        if morning_choice == "CE":
            m_contract, m_open = dd.ce_contract, dd.ce_morning_open
            opp_noon_open      = dd.pe_noon_open
            opp_contract       = dd.pe_contract
        else:
            m_contract, m_open = dd.pe_contract, dd.pe_morning_open
            opp_noon_open      = dd.ce_noon_open
            opp_contract       = dd.ce_contract

        m_exit_ts, m_exit_px, m_reason, m_pts, _ = resolve_sell_leg(
            m_contract, m_open, dd.entry_ts, dd.exit_ts,
        )
        m_gross, _, m_net = apply_costs(m_pts, dd.qty)

        # Second trade: only if morning SL hit BEFORE noon
        is_morning_sl   = "sl" in m_reason
        is_before_noon  = m_exit_ts < dd.midday_ts
        do_second_trade = is_morning_sl and is_before_noon and opp_noon_open > 0

        s_choice = s_exit_ts = s_exit_reason = ""
        s_open = s_exit_px = s_pts = s_gross = s_net = 0.0

        if do_second_trade:
            s_exit_ts, s_exit_px, s_exit_reason, s_pts, _ = resolve_sell_leg(
                opp_contract, opp_noon_open, dd.midday_ts, dd.exit_ts,
            )
            s_gross, _, s_net = apply_costs(s_pts, dd.qty)
            s_choice = opposite_choice
            s_open   = opp_noon_open

        results.append(TradeResult(
            entry_date=dd.entry_date, day_of_week=dd.day_of_week,
            run_number=run_number, seed=seed,
            expiry_date=dd.expiry_date, atm_strike=dd.atm_strike, qty=dd.qty,
            morning_choice=morning_choice,
            morning_open=round(m_open, 2),
            morning_sl_price=round(m_open * (1 + SL_PCT), 2),
            morning_target_price=round(m_open * (1 - TARGET_PCT), 2),
            morning_exit_ts=m_exit_ts,
            morning_exit_price=round(m_exit_px, 4),
            morning_exit_reason=m_reason,
            morning_points_pnl=round(m_pts, 4),
            morning_gross_pnl=round(m_gross, 2),
            morning_net_pnl=round(m_net, 2),
            second_trade=do_second_trade,
            second_choice=s_choice,
            second_open=round(s_open, 2),
            second_exit_ts=s_exit_ts,
            second_exit_price=round(s_exit_px, 4),
            second_exit_reason=s_exit_reason,
            second_points_pnl=round(s_pts, 4),
            second_gross_pnl=round(s_gross, 2),
            second_net_pnl=round(s_net, 2),
            total_net_pnl=round(m_net + s_net, 2),
        ))

    return results


# ---------------------------------------------------------------------------
# ANALYTICS
# ---------------------------------------------------------------------------

def compute_equity_curve(net_pnls: List[float]) -> Tuple[float, float]:
    """Returns (max_drawdown, max_cumulative_profit)."""
    cumulative = peak = max_dd = max_cum = 0.0
    for pnl in net_pnls:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
        if cumulative > max_cum:
            max_cum = cumulative
    return max_dd, max_cum


def compute_cagr(net_total: float, capital: float, first_date: str, last_date: str) -> float:
    if capital <= 0:
        return 0.0
    days = (datetime.date.fromisoformat(last_date) - datetime.date.fromisoformat(first_date)).days
    if days <= 0:
        return 0.0
    base = 1.0 + net_total / capital
    if base <= 0:
        return -1.0
    return base ** (365.25 / days) - 1.0


# ---------------------------------------------------------------------------
# OUTPUT — CSV
# ---------------------------------------------------------------------------

def write_daywise_csv(all_results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "run_number", "seed", "entry_date", "day_of_week", "expiry_date",
        "atm_strike", "qty",
        "morning_choice", "morning_open", "morning_sl_price", "morning_target_price",
        "morning_exit_ts", "morning_exit_price", "morning_exit_reason",
        "morning_points_pnl", "morning_gross_pnl", "morning_net_pnl",
        "second_trade", "second_choice", "second_open",
        "second_exit_ts", "second_exit_price", "second_exit_reason",
        "second_points_pnl", "second_gross_pnl", "second_net_pnl",
        "total_net_pnl",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in all_results:
            w.writerow({
                "run_number": r.run_number, "seed": r.seed,
                "entry_date": r.entry_date, "day_of_week": r.day_of_week,
                "expiry_date": r.expiry_date, "atm_strike": r.atm_strike, "qty": r.qty,
                "morning_choice": r.morning_choice,
                "morning_open": fmt(r.morning_open),
                "morning_sl_price": fmt(r.morning_sl_price),
                "morning_target_price": fmt(r.morning_target_price),
                "morning_exit_ts": r.morning_exit_ts,
                "morning_exit_price": fmt(r.morning_exit_price),
                "morning_exit_reason": r.morning_exit_reason,
                "morning_points_pnl": fmt(r.morning_points_pnl),
                "morning_gross_pnl": fmt(r.morning_gross_pnl),
                "morning_net_pnl": fmt(r.morning_net_pnl),
                "second_trade": r.second_trade,
                "second_choice": r.second_choice,
                "second_open": fmt(r.second_open) if r.second_open else "",
                "second_exit_ts": r.second_exit_ts,
                "second_exit_price": fmt(r.second_exit_price) if r.second_exit_price else "",
                "second_exit_reason": r.second_exit_reason,
                "second_points_pnl": fmt(r.second_points_pnl) if r.second_trade else "",
                "second_gross_pnl": fmt(r.second_gross_pnl) if r.second_trade else "",
                "second_net_pnl": fmt(r.second_net_pnl) if r.second_trade else "",
                "total_net_pnl": fmt(r.total_net_pnl),
            })


# ---------------------------------------------------------------------------
# OUTPUT — SUMMARY MARKDOWN
# ---------------------------------------------------------------------------

def write_summary(
    runs: Dict[int, List[TradeResult]],
    skipped: List[SkippedDay],
    output_path: Path,
    args: argparse.Namespace,
) -> None:
    run_ids  = sorted(runs)
    sample   = runs[run_ids[0]]
    first_d  = sample[0].entry_date  if sample else "N/A"
    last_d   = sample[-1].entry_date if sample else "N/A"
    num_days = len(sample)

    lines: List[str] = [
        "# Heads & Tails — Random Single-Leg ATM Short, NIFTY Weekly (all data)",
        "",
        "## Strategy Rules",
        "",
        f"- **Entry**: `{ENTRY_TIME}` — sell ATM CE or PE at random (50/50 coin flip)",
        f"- **Stop Loss**: `{SL_PCT*100:.0f}%` rise above entry premium",
        f"- **Target**: `{TARGET_PCT*100:.0f}%` decay (option halves in price)",
        "- If morning SL hit **before 12:00** → sell OPPOSITE at 12:00 (same SL/target)",
        "- If morning SL hit **at/after 12:00** → done for day, no second trade",
        "- Target hit any time → done for day",
        f"- **Day exit**: `{EXIT_TIME}` if neither SL nor target hit",
        f"- Options: NIFTY weekly, current-week (expiry-inclusive), ~300 qty",
        f"- Brokerage: ₹{BROK_PER_ORDER:.0f}/order → ₹{BROK_PER_TRADE:.0f}/trade (2 orders: sell+buyback)",
        f"- Slippage: {SLIP_PER_ORDER} pt/order (2× per trade)",
        f"- Seeds used: {SEEDS}",
        f"- Period: `{first_d}` → `{last_d}` | Trading days loaded: `{num_days}` "
        f"| Skipped: `{len(skipped)}`",
        f"- Capital (for CAGR): ₹{args.capital:,.0f}",
        "",
        "---",
        "",
        "## Run Comparison Table",
        "",
        "| Run | Seed | Days | Targets | SLs(morn) | 2nd Trades | Win% | Net P/L | Max Profit | Max DD | CAGR |",
        "|-----|------|------|---------|-----------|------------|------|---------|------------|--------|------|",
    ]

    best_net = float("-inf")
    best_run = run_ids[0]
    for run_id in run_ids:
        rr = runs[run_id]
        seed = SEEDS[run_id - 1]
        net_total = sum(r.total_net_pnl for r in rr)
        if net_total > best_net:
            best_net = net_total
            best_run = run_id
        wins      = sum(1 for r in rr if r.total_net_pnl > 0)
        targets   = sum(1 for r in rr if "target" in r.morning_exit_reason)
        morn_sl   = sum(1 for r in rr if "sl" in r.morning_exit_reason)
        second_n  = sum(1 for r in rr if r.second_trade)
        dd, max_c = compute_equity_curve([r.total_net_pnl for r in rr])
        cagr      = compute_cagr(net_total, args.capital, first_d, last_d) * 100
        label     = f"**{run_id}**" if run_id == best_run else str(run_id)
        lines.append(
            f"| {label} | `{seed}` | `{num_days}` | `{targets}` | `{morn_sl}` "
            f"| `{second_n}` | `{wins/num_days*100:.1f}%` | `₹{fmt(net_total)}` "
            f"| `₹{fmt(max_c)}` | `₹{fmt(dd)}` | `{cagr:.2f}%` |"
        )

    lines += ["", f"_Bold = best combined Net P/L (Run {best_run})_", "", "---", ""]

    # ── MONTHLY P/L COMPARISON (all 5 runs side by side) ──────────────────
    all_months = sorted({r.entry_date[:7] for r in runs[run_ids[0]]})
    run_hdrs   = " | ".join(f"Run {r}" for r in run_ids)
    run_sep    = " | ".join("--------" for _ in run_ids)
    lines += [
        "## Monthly Net P/L by Run",
        "",
        f"| Month | {run_hdrs} |",
        f"|-------|{run_sep}|",
    ]
    for month in all_months:
        cells = []
        for run_id in run_ids:
            m_net = sum(r.total_net_pnl for r in runs[run_id] if r.entry_date[:7] == month)
            cells.append(f"₹{fmt(m_net)}")
        lines.append("| " + month + " | " + " | ".join(f"`{c}`" for c in cells) + " |")
    lines += ["", "---", ""]

    # ── YEARLY SUMMARY ────────────────────────────────────────────────────
    all_years = sorted({r.entry_date[:4] for r in runs[run_ids[0]]})
    run_hdrs2 = " | ".join(f"Run {r}" for r in run_ids)
    run_sep2  = " | ".join("---------" for _ in run_ids)
    lines += [
        "## Yearly Net P/L by Run",
        "",
        f"| Year | {run_hdrs2} |",
        f"|------|{run_sep2}|",
    ]
    for year in all_years:
        cells = []
        for run_id in run_ids:
            y_net = sum(r.total_net_pnl for r in runs[run_id] if r.entry_date[:4] == year)
            cells.append(f"₹{fmt(y_net)}")
        lines.append("| " + year + " | " + " | ".join(f"`{c}`" for c in cells) + " |")
    lines += ["", "---", ""]

    # ── DAY-OF-WEEK BREAKDOWN (best run) ──────────────────────────────────
    best_results = runs[best_run]
    lines += [
        f"## Day-of-Week Breakdown (Best Run #{best_run}, Seed {SEEDS[best_run-1]})",
        "",
        "| Day | Trades | Wins | Losses | 2nd Trades | Net P/L | Avg/Day |",
        "|-----|--------|------|--------|------------|---------|---------|",
    ]
    by_day: Dict[str, List[TradeResult]] = {}
    for r in best_results:
        by_day.setdefault(r.day_of_week, []).append(r)
    for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        dr = by_day.get(d, [])
        if not dr:
            lines.append(f"| {d} | 0 | — | — | — | — | — |")
            continue
        d_net   = sum(r.total_net_pnl for r in dr)
        d_wins  = sum(1 for r in dr if r.total_net_pnl > 0)
        d_sec   = sum(1 for r in dr if r.second_trade)
        lines.append(
            f"| {d} | {len(dr)} | {d_wins} | {len(dr)-d_wins} | {d_sec} "
            f"| `₹{fmt(d_net)}` | `₹{fmt(d_net/len(dr))}` |"
        )
    lines += ["", "---", ""]

    # ── EXIT REASON ANALYSIS (best run) ───────────────────────────────────
    lines += [
        f"## Exit Reason Analysis (Best Run #{best_run})",
        "",
        "### Morning Trade",
        "",
        "| Reason | Count | % of days |",
        "|--------|-------|-----------|",
    ]
    reason_counts: Dict[str, int] = {}
    for r in best_results:
        reason_counts[r.morning_exit_reason] = reason_counts.get(r.morning_exit_reason, 0) + 1
    n = len(best_results)
    for reason, cnt in sorted(reason_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| `{reason}` | {cnt} | {cnt/n*100:.1f}% |")

    second_traded = [r for r in best_results if r.second_trade]
    if second_traded:
        lines += ["", "### Afternoon Trade (12:00 re-entries)", "", "| Reason | Count |", "|--------|-------|"]
        reason2: Dict[str, int] = {}
        for r in second_traded:
            reason2[r.second_exit_reason] = reason2.get(r.second_exit_reason, 0) + 1
        for reason, cnt in sorted(reason2.items(), key=lambda x: -x[1]):
            lines.append(f"| `{reason}` | {cnt} |")

    lines += ["", "---", ""]

    # ── DETAILED STATS PER RUN ────────────────────────────────────────────
    lines += ["## Detailed Stats Per Run", ""]
    for run_id in run_ids:
        rr    = runs[run_id]
        seed  = SEEDS[run_id - 1]
        n_tot = sum(r.total_net_pnl for r in rr)
        wins  = sum(1 for r in rr if r.total_net_pnl > 0)
        tgts  = sum(1 for r in rr if "target" in r.morning_exit_reason)
        m_sl  = sum(1 for r in rr if "sl" in r.morning_exit_reason)
        m_cl  = sum(1 for r in rr if "close" in r.morning_exit_reason or "candle" in r.morning_exit_reason)
        s_n   = sum(1 for r in rr if r.second_trade)
        s_win = sum(1 for r in rr if r.second_trade and r.second_net_pnl > 0)
        dd, mx = compute_equity_curve([r.total_net_pnl for r in rr])
        cagr   = compute_cagr(n_tot, args.capital, first_d, last_d) * 100
        best_r  = max(rr, key=lambda r: r.total_net_pnl)
        worst_r = min(rr, key=lambda r: r.total_net_pnl)
        ce_picks = sum(1 for r in rr if r.morning_choice == "CE")
        pe_picks = sum(1 for r in rr if r.morning_choice == "PE")

        lines += [
            f"### Run {run_id}  (seed={seed})",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Trading days | `{len(rr)}` |",
            f"| CE picks / PE picks | `{ce_picks}` / `{pe_picks}` |",
            f"| Morning targets hit | `{tgts}` ({tgts/len(rr)*100:.1f}%) |",
            f"| Morning SL hit | `{m_sl}` ({m_sl/len(rr)*100:.1f}%) |",
            f"| Morning day-close | `{m_cl}` ({m_cl/len(rr)*100:.1f}%) |",
            f"| 2nd trades triggered | `{s_n}` (win rate: `{s_win/s_n*100:.1f}%`) |" if s_n else "| 2nd trades triggered | `0` |",
            f"| Win days | `{wins}` / `{len(rr)}` ({wins/len(rr)*100:.1f}%) |",
            f"| **Net P/L** | **`₹{fmt(n_tot)}`** |",
            f"| Max cumulative profit | `₹{fmt(mx)}` |",
            f"| Max drawdown | `₹{fmt(dd)}` |",
            f"| **CAGR** (on ₹{args.capital:,.0f}) | **`{cagr:.2f}%`** |",
            f"| Best day | `{best_r.entry_date}` ({best_r.day_of_week}) `₹{fmt(best_r.total_net_pnl)}` |",
            f"| Worst day | `{worst_r.entry_date}` ({worst_r.day_of_week}) `₹{fmt(worst_r.total_net_pnl)}` |",
            "",
        ]

    # ── ENTRY PRICE DISTRIBUTION ──────────────────────────────────────────
    all_opens = (
        [r.morning_open for r in runs[run_ids[0]]]
    )
    buckets = [(0, 50), (50, 100), (100, 150), (150, 200), (200, 300), (300, 99999)]
    lines += ["## Morning Entry Price Distribution (all days, run-independent)", ""]
    lines += ["| Price Range | Days | % |", "|-------------|------|---|"]
    total_d = len(all_opens)
    for lo, hi in buckets:
        cnt = sum(1 for v in all_opens if lo <= v < hi)
        label = f"{lo}–{hi}" if hi < 99999 else f"{lo}+"
        lines.append(f"| `{label}` | {cnt} | {cnt/total_d*100:.1f}% |")
    lines += ["", "---", ""]

    # ── SKIP SUMMARY ──────────────────────────────────────────────────────
    skip_by: Dict[str, int] = {}
    for s in skipped:
        skip_by[s.skip_reason] = skip_by.get(s.skip_reason, 0) + 1
    lines += ["## Skip Reason Summary", ""]
    for reason, cnt in sorted(skip_by.items(), key=lambda x: -x[1]):
        lines.append(f"- `{reason}`: {cnt}")

    lines += [
        "",
        "## Remarks",
        "",
        "- Only ONE option leg is sold each morning (not a straddle).",
        "- Second trade at 12:00 uses SAME expiry contract, OPPOSITE type (CE↔PE).",
        "- `gap_sl` / `gap_target` : option opens through the trigger price.",
        "- `sl` / `target` : triggered within a 1-minute candle (high/low).",
        "- SL checked before target within each candle (conservative).",
        "- Slippage 0.5 pt/order applied on entry and exit (2 × per trade).",
        "- Five runs use identical price data; only the daily CE/PE coin flip differs.",
        "- Fixed seeds ensure reproducibility across re-runs of the script.",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)

    print("Pass 1: loading all day data …")
    days, skipped = collect_day_data(args)
    print(f"  Loaded {len(days)} days, {len(skipped)} skipped.")

    all_results: List[TradeResult] = []
    runs: Dict[int, List[TradeResult]] = {}

    for i, seed in enumerate(SEEDS, start=1):
        print(f"Pass 2 run {i}/{NUM_RUNS} (seed={seed}) …")
        run_results = simulate_run(days, i, seed)
        runs[i]      = run_results
        all_results += run_results
        net = sum(r.total_net_pnl for r in run_results)
        print(f"  Net P/L: Rs.{fmt(net)}")

    write_daywise_csv(all_results, args.results_dir / DAYWISE_CSV)
    write_summary(runs, skipped, args.results_dir / SUMMARY_MD, args)

    print(f"\nDaywise CSV : {args.results_dir / DAYWISE_CSV}")
    print(f"Summary     : {args.results_dir / SUMMARY_MD}")


if __name__ == "__main__":
    main()
