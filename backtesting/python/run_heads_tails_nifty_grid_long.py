#!/usr/bin/env python3
"""
Heads & Tails LONG — Parameter Grid Test, NIFTY Weekly (all data 2020–2026)

Same coin-flip strategy as the short grid but now BUYING the ATM option.

  SL levels    : 20%, 30%, 40%, 50%   (option price FALLS by this %)
  Target levels: open, 50%, 60%, 70%, 80%, 90%, 100%  (price RISES by this %)
  = 28 combos × 5 random runs = 140 total series

"open" target = hold until SL triggers or day exit at 15:20.

Morning (09:30): randomly BUY ATM CE or PE.
  - SL hit BEFORE 12:00 → BUY OPPOSITE at 12:00, same SL/target
  - SL hit AT/AFTER 12:00 → done for day
  - Target hit → done for day
  - No trigger → exit at 15:20
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
BASE_FILENAME = "heads_tails_nifty_grid_long"
DAYWISE_CSV   = f"{BASE_FILENAME}_daywise.csv"
SUMMARY_MD    = f"{BASE_FILENAME}_summary.md"
LOG_FILE      = f"{BASE_FILENAME}.log"
WEEKDAY_NAMES = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

ENTRY_TIME  = "09:30"
MIDDAY_TIME = "12:00"
EXIT_TIME   = "15:20"

SL_LEVELS: List[float]            = [0.20, 0.30, 0.40, 0.50]
TARGET_LEVELS: List[Optional[float]] = [None, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
SEEDS          = [42, 137, 2025, 777, 1984]
NUM_RUNS       = 5
BROK_PER_ORDER = 25.0
SLIP_PER_ORDER = 0.5
BROK_PER_TRADE = BROK_PER_ORDER * 2   # buy + sell-back


def target_label(t: Optional[float]) -> str:
    return "open" if t is None else f"{t*100:.0f}%"


def combo_key(sl: float, tgt: Optional[float]) -> str:
    return f"SL{sl*100:.0f}%_T{target_label(tgt)}"


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
    ce_morning_open: float
    pe_morning_open: float
    ce_noon_open: float
    pe_noon_open: float


@dataclass
class SkippedDay:
    entry_date: str
    day_of_week: str
    skip_reason: str
    details: str = ""


@dataclass
class TradeResult:
    sl_pct: float
    target_pct: float          # -1.0 = "open"
    combo: str
    run_number: int
    seed: int
    entry_date: str
    day_of_week: str
    expiry_date: str
    atm_strike: int
    qty: int
    morning_choice: str
    morning_open: float
    morning_exit_ts: str
    morning_exit_price: float
    morning_exit_reason: str
    morning_points_pnl: float
    morning_gross_pnl: float
    morning_net_pnl: float
    second_trade: bool
    second_choice: str
    second_open: float
    second_exit_ts: str
    second_exit_price: float
    second_exit_reason: str
    second_points_pnl: float
    second_gross_pnl: float
    second_net_pnl: float
    total_net_pnl: float


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    p = argparse.ArgumentParser(description="Heads & Tails LONG NIFTY parameter grid.")
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
# RESOLUTION — LONG option position
# ---------------------------------------------------------------------------

def resolve_buy_leg(
    contract: ContractData,
    entry_open: float,
    entry_ts: str,
    exit_ts: str,
    sl_pct: float,
    target_pct: Optional[float],
) -> Tuple[str, float, str, float]:
    """
    Walk 1-min candles for a LONG option position.
    SL    : option price FALLS to entry * (1 - sl_pct)
    Target: option price RISES to entry * (1 + target_pct)
    target_pct=None → no profit target.

    Returns (exit_ts, exit_price, reason, raw_points_pnl).
    raw_points_pnl = exit_price - entry_open  (positive = profit).
    Slippage applied separately in apply_costs().

    Within each candle: gap checks first (open), then intra-candle
    SL (low) checked before target (high) — conservative ordering.
    """
    sl_price  = entry_open * (1.0 - sl_pct)
    tgt_price = entry_open * (1.0 + target_pct) if target_pct is not None else None
    window    = sorted(ts for ts in contract.rows_by_timestamp if entry_ts <= ts <= exit_ts)

    for ts in window:
        row = contract.rows_by_timestamp[ts]
        # gap SL: opens at or below SL
        if row.open_value <= sl_price:
            return ts, row.open_value, "gap_sl", row.open_value - entry_open
        # gap target: opens at or above target
        if tgt_price is not None and row.open_value >= tgt_price:
            return ts, row.open_value, "gap_target", row.open_value - entry_open
        # intra-candle SL (low hits SL) — checked before target
        if row.low_value <= sl_price:
            return ts, sl_price, "sl", sl_price - entry_open
        # intra-candle target (high hits target)
        if tgt_price is not None and row.high_value >= tgt_price:
            return ts, tgt_price, "target", tgt_price - entry_open

    exit_row = contract.rows_by_timestamp.get(exit_ts)
    if exit_row:
        return exit_ts, exit_row.open_value, "day_close", exit_row.open_value - entry_open

    candidates = [ts for ts in contract.rows_by_timestamp if ts <= exit_ts]
    if candidates:
        last_ts  = max(candidates)
        last_row = contract.rows_by_timestamp[last_ts]
        return last_ts, last_row.open_value, "last_candle", last_row.open_value - entry_open

    return exit_ts, entry_open, "missing_exit", 0.0


def apply_costs(raw_pts: float, qty: int) -> Tuple[float, float]:
    """
    Returns (gross_pnl, net_pnl).
    For long: buy at open+slip, sell at exit-slip → effective pts = raw_pts - 2*slip.
    """
    net_pts = raw_pts - 2 * SLIP_PER_ORDER
    gross   = net_pts * qty
    net     = gross - BROK_PER_TRADE
    return gross, net


# ---------------------------------------------------------------------------
# PASS 1 — COLLECT DAY DATA
# ---------------------------------------------------------------------------

def collect_day_data(args: argparse.Namespace) -> Tuple[List[DayData], List[SkippedDay]]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILE)

    trading_days, spot_opens = load_spot_opens(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    cache: Dict[Path, Optional[ContractData]] = {}
    days:    List[DayData]    = []
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
                skipped.append(SkippedDay(entry_date, day_name, "missing_spot",
                                          f"No spot candle at {entry_ts}"))
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
                continue

            ce_m = ce.rows_by_timestamp.get(entry_ts)
            pe_m = pe.rows_by_timestamp.get(entry_ts)
            if ce_m is None or pe_m is None:
                miss = ("CE " if ce_m is None else "") + ("PE" if pe_m is None else "")
                skipped.append(SkippedDay(entry_date, day_name, "missing_entry_candle",
                                          f"Missing {miss.strip()} at {entry_ts}"))
                continue

            ce_noon = ce.rows_by_timestamp.get(midday_ts)
            pe_noon = pe.rows_by_timestamp.get(midday_ts)

            days.append(DayData(
                entry_date=entry_date, day_of_week=day_name,
                expiry_date=expiry_date, lot_size=lot_size, num_lots=num_lots, qty=qty,
                atm_strike=atm, entry_ts=entry_ts, midday_ts=midday_ts, exit_ts=exit_ts,
                ce_contract=ce, pe_contract=pe,
                ce_morning_open=ce_m.open_value,
                pe_morning_open=pe_m.open_value,
                ce_noon_open=ce_noon.open_value if ce_noon else 0.0,
                pe_noon_open=pe_noon.open_value if pe_noon else 0.0,
            ))
            logger.debug("LOADED %s atm=%s ce=%.2f pe=%.2f",
                         entry_date, atm, ce_m.open_value, pe_m.open_value)

    except Exception:
        logger.exception("ERROR")
        raise
    finally:
        logger.info("Loaded=%s Skipped=%s", len(days), len(skipped))
        close_logger(logger)

    return days, skipped


# ---------------------------------------------------------------------------
# PASS 2 — SIMULATE ONE (combo × run)
# ---------------------------------------------------------------------------

def simulate_one(
    days: List[DayData],
    sl_pct: float,
    target_pct: Optional[float],
    run_number: int,
    seed: int,
) -> List[TradeResult]:
    rng    = random.Random(seed)
    ck     = combo_key(sl_pct, target_pct)
    tgt_f  = -1.0 if target_pct is None else target_pct
    results: List[TradeResult] = []

    for dd in days:
        morning_choice  = rng.choice(["CE", "PE"])
        opposite_choice = "PE" if morning_choice == "CE" else "CE"

        if morning_choice == "CE":
            m_contract, m_open = dd.ce_contract, dd.ce_morning_open
            opp_contract       = dd.pe_contract
            opp_noon_open      = dd.pe_noon_open
        else:
            m_contract, m_open = dd.pe_contract, dd.pe_morning_open
            opp_contract       = dd.ce_contract
            opp_noon_open      = dd.ce_noon_open

        m_exit_ts, m_exit_px, m_reason, m_raw_pts = resolve_buy_leg(
            m_contract, m_open, dd.entry_ts, dd.exit_ts, sl_pct, target_pct,
        )
        m_gross, m_net = apply_costs(m_raw_pts, dd.qty)

        is_morning_sl = "sl" in m_reason
        before_noon   = m_exit_ts < dd.midday_ts
        do_second     = is_morning_sl and before_noon and opp_noon_open > 0

        s_choice = s_exit_ts = s_exit_reason = ""
        s_open = s_exit_px = s_raw_pts = s_gross = s_net = 0.0

        if do_second:
            s_exit_ts, s_exit_px, s_exit_reason, s_raw_pts = resolve_buy_leg(
                opp_contract, opp_noon_open, dd.midday_ts, dd.exit_ts, sl_pct, target_pct,
            )
            s_gross, s_net = apply_costs(s_raw_pts, dd.qty)
            s_choice = opposite_choice
            s_open   = opp_noon_open

        results.append(TradeResult(
            sl_pct=sl_pct, target_pct=tgt_f, combo=ck,
            run_number=run_number, seed=seed,
            entry_date=dd.entry_date, day_of_week=dd.day_of_week,
            expiry_date=dd.expiry_date, atm_strike=dd.atm_strike, qty=dd.qty,
            morning_choice=morning_choice,
            morning_open=round(m_open, 2),
            morning_exit_ts=m_exit_ts,
            morning_exit_price=round(m_exit_px, 4),
            morning_exit_reason=m_reason,
            morning_points_pnl=round(m_raw_pts - 2 * SLIP_PER_ORDER, 4),
            morning_gross_pnl=round(m_gross, 2),
            morning_net_pnl=round(m_net, 2),
            second_trade=do_second,
            second_choice=s_choice,
            second_open=round(s_open, 2),
            second_exit_ts=s_exit_ts,
            second_exit_price=round(s_exit_px, 4),
            second_exit_reason=s_exit_reason,
            second_points_pnl=round(s_raw_pts - 2 * SLIP_PER_ORDER, 4) if do_second else 0.0,
            second_gross_pnl=round(s_gross, 2),
            second_net_pnl=round(s_net, 2),
            total_net_pnl=round(m_net + s_net, 2),
        ))

    return results


# ---------------------------------------------------------------------------
# ANALYTICS
# ---------------------------------------------------------------------------

def compute_equity_curve(net_pnls: List[float]) -> Tuple[float, float]:
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
        "combo", "sl_pct", "target_pct", "run_number", "seed",
        "entry_date", "day_of_week", "expiry_date", "atm_strike", "qty",
        "morning_choice", "morning_open",
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
            tgt_str = "open" if r.target_pct < 0 else f"{r.target_pct*100:.0f}%"
            w.writerow({
                "combo": r.combo, "sl_pct": f"{r.sl_pct*100:.0f}%",
                "target_pct": tgt_str, "run_number": r.run_number, "seed": r.seed,
                "entry_date": r.entry_date, "day_of_week": r.day_of_week,
                "expiry_date": r.expiry_date, "atm_strike": r.atm_strike, "qty": r.qty,
                "morning_choice": r.morning_choice, "morning_open": fmt(r.morning_open),
                "morning_exit_ts": r.morning_exit_ts,
                "morning_exit_price": fmt(r.morning_exit_price),
                "morning_exit_reason": r.morning_exit_reason,
                "morning_points_pnl": fmt(r.morning_points_pnl),
                "morning_gross_pnl": fmt(r.morning_gross_pnl),
                "morning_net_pnl": fmt(r.morning_net_pnl),
                "second_trade": r.second_trade, "second_choice": r.second_choice,
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

ResultsMap = Dict[Tuple[float, Optional[float]], Dict[int, List[TradeResult]]]


def _avg_net(rm: ResultsMap, sl: float, tgt: Optional[float]) -> float:
    runs = rm.get((sl, tgt), {})
    if not runs: return 0.0
    return sum(sum(r.total_net_pnl for r in v) for v in runs.values()) / len(runs)


def _avg_cagr(rm: ResultsMap, sl: float, tgt: Optional[float], capital: float) -> float:
    runs = rm.get((sl, tgt), {})
    if not runs: return 0.0
    cagrs = []
    for rr in runs.values():
        if not rr: continue
        net  = sum(r.total_net_pnl for r in rr)
        cagrs.append(compute_cagr(net, capital, rr[0].entry_date, rr[-1].entry_date) * 100)
    return sum(cagrs) / len(cagrs) if cagrs else 0.0


def _avg_dd(rm: ResultsMap, sl: float, tgt: Optional[float]) -> float:
    runs = rm.get((sl, tgt), {})
    if not runs: return 0.0
    dds = [compute_equity_curve([r.total_net_pnl for r in rr])[0] for rr in runs.values()]
    return sum(dds) / len(dds) if dds else 0.0


def _avg_winpct(rm: ResultsMap, sl: float, tgt: Optional[float]) -> float:
    runs = rm.get((sl, tgt), {})
    if not runs: return 0.0
    wps = [sum(1 for r in rr if r.total_net_pnl > 0) / len(rr) * 100 for rr in runs.values() if rr]
    return sum(wps) / len(wps) if wps else 0.0


def _pos_runs(rm: ResultsMap, sl: float, tgt: Optional[float]) -> int:
    runs = rm.get((sl, tgt), {})
    return sum(1 for rr in runs.values() if sum(r.total_net_pnl for r in rr) > 0)


def write_summary(
    results_map: ResultsMap,
    skipped: List[SkippedDay],
    output_path: Path,
    args: argparse.Namespace,
) -> None:
    sample_run = next(iter(next(iter(results_map.values())).values()))
    first_d    = sample_run[0].entry_date
    last_d     = sample_run[-1].entry_date
    num_days   = len(sample_run)

    tgt_labels = [target_label(t) for t in TARGET_LEVELS]
    sl_labels  = [f"{int(sl*100)}%" for sl in SL_LEVELS]

    # find best combo by avg net P/L
    best_sl  = SL_LEVELS[0]
    best_tgt: Optional[float] = TARGET_LEVELS[0]
    best_avg = float("-inf")
    for sl in SL_LEVELS:
        for tgt in TARGET_LEVELS:
            avg = _avg_net(results_map, sl, tgt)
            if avg > best_avg:
                best_avg = avg
                best_sl  = sl
                best_tgt = tgt

    lines: List[str] = [
        "# Heads & Tails LONG — Parameter Grid (NIFTY Weekly, all data 2020–2026)",
        "",
        "## Strategy",
        "",
        f"- Entry `{ENTRY_TIME}` — **BUY** ATM CE or PE at random (50/50)",
        "- If morning SL hit **before 12:00** → BUY OPPOSITE at 12:00, same SL/target",
        "- If morning SL hit **at/after 12:00** → done for day",
        "- Target hit → done for day",
        f"- Day exit: `{EXIT_TIME}`",
        "- **SL**: option price FALLS by SL%",
        "- **Target**: option price RISES by Target%",
        f"- Brokerage ₹{BROK_PER_ORDER:.0f}/order → ₹{BROK_PER_TRADE:.0f}/trade | "
        f"Slippage {SLIP_PER_ORDER} pt/order",
        f"- Period: `{first_d}` → `{last_d}` | Days loaded: `{num_days}` | Skipped: `{len(skipped)}`",
        f"- Seeds: {SEEDS} | Capital: ₹{args.capital:,.0f}",
        "",
        "---",
        "",
    ]

    col_hdr = " | ".join(f"T={lbl}" for lbl in tgt_labels)
    col_sep = " | ".join("----------" for _ in tgt_labels)

    # Grid 1: Avg Net P/L
    lines += [
        "## Grid 1 — Average Net P/L across 5 Runs  (₹)",
        "",
        f"| SL \\ Target | {col_hdr} |",
        f"|-------------|{col_sep}|",
    ]
    for sl, sl_lbl in zip(SL_LEVELS, sl_labels):
        cells = []
        for tgt in TARGET_LEVELS:
            avg  = _avg_net(results_map, sl, tgt)
            mark = " ★" if sl == best_sl and tgt == best_tgt else ""
            cells.append(f"₹{fmt(avg)}{mark}")
        lines.append(f"| SL={sl_lbl} | " + " | ".join(f"`{c}`" for c in cells) + " |")
    lines += ["", f"_★ = best combo (SL={best_sl*100:.0f}%, T={target_label(best_tgt)})_", "", ""]

    # Grid 2: Avg CAGR
    lines += [
        "## Grid 2 — Average CAGR across 5 Runs  (%)",
        "",
        f"| SL \\ Target | {col_hdr} |",
        f"|-------------|{col_sep}|",
    ]
    for sl, sl_lbl in zip(SL_LEVELS, sl_labels):
        cells = []
        for tgt in TARGET_LEVELS:
            cagr = _avg_cagr(results_map, sl, tgt, args.capital)
            mark = " ★" if sl == best_sl and tgt == best_tgt else ""
            cells.append(f"{cagr:.2f}%{mark}")
        lines.append(f"| SL={sl_lbl} | " + " | ".join(f"`{c}`" for c in cells) + " |")
    lines += ["", ""]

    # Grid 3: Avg Win%
    lines += [
        "## Grid 3 — Average Win% across 5 Runs",
        "",
        f"| SL \\ Target | {col_hdr} |",
        f"|-------------|{col_sep}|",
    ]
    for sl, sl_lbl in zip(SL_LEVELS, sl_labels):
        cells = [f"{_avg_winpct(results_map, sl, tgt):.1f}%" for tgt in TARGET_LEVELS]
        lines.append(f"| SL={sl_lbl} | " + " | ".join(f"`{c}`" for c in cells) + " |")
    lines += ["", ""]

    # Grid 4: Avg Max Drawdown
    lines += [
        "## Grid 4 — Average Max Drawdown across 5 Runs  (₹)",
        "",
        f"| SL \\ Target | {col_hdr} |",
        f"|-------------|{col_sep}|",
    ]
    for sl, sl_lbl in zip(SL_LEVELS, sl_labels):
        cells = [f"₹{fmt(_avg_dd(results_map, sl, tgt))}" for tgt in TARGET_LEVELS]
        lines.append(f"| SL={sl_lbl} | " + " | ".join(f"`{c}`" for c in cells) + " |")
    lines += ["", ""]

    # Grid 5: Profitable runs count
    lines += [
        "## Grid 5 — # of Profitable Runs (out of 5)",
        "",
        f"| SL \\ Target | {col_hdr} |",
        f"|-------------|{col_sep}|",
    ]
    for sl, sl_lbl in zip(SL_LEVELS, sl_labels):
        cells = [str(_pos_runs(results_map, sl, tgt)) + "/5" for tgt in TARGET_LEVELS]
        lines.append(f"| SL={sl_lbl} | " + " | ".join(f"`{c}`" for c in cells) + " |")
    lines += ["", "---", ""]

    # All combos ranked
    ranked: List[Tuple[float, float, Optional[float]]] = []
    for sl in SL_LEVELS:
        for tgt in TARGET_LEVELS:
            ranked.append((_avg_net(results_map, sl, tgt), sl, tgt))
    ranked.sort(reverse=True)

    lines += [
        "## All Combos Ranked by Avg Net P/L",
        "",
        "| Rank | Combo | Avg Net P/L | Avg CAGR | Avg Win% | Avg DD | Profitable Runs |",
        "|------|-------|-------------|----------|----------|--------|-----------------|",
    ]
    for rank, (avg_net, sl, tgt) in enumerate(ranked, 1):
        cagr = _avg_cagr(results_map, sl, tgt, args.capital)
        win  = _avg_winpct(results_map, sl, tgt)
        dd   = _avg_dd(results_map, sl, tgt)
        pos  = _pos_runs(results_map, sl, tgt)
        lbl  = f"SL={sl*100:.0f}% T={target_label(tgt)}"
        mark = " ★" if rank == 1 else ""
        lines.append(
            f"| {rank} | `{lbl}{mark}` | `₹{fmt(avg_net)}` | `{cagr:.2f}%` "
            f"| `{win:.1f}%` | `₹{fmt(dd)}` | `{pos}/5` |"
        )
    lines += ["", "---", ""]

    # Best combo per-run detail
    best_runs = results_map[(best_sl, best_tgt)]
    lines += [
        f"## Best Combo Detail — SL={best_sl*100:.0f}%, Target={target_label(best_tgt)}",
        "",
        "| Run | Seed | Net P/L | CAGR | Win% | Max Profit | Max DD |",
        "|-----|------|---------|------|------|------------|--------|",
    ]
    for run_id in sorted(best_runs):
        rr   = best_runs[run_id]
        seed = SEEDS[run_id - 1]
        net  = sum(r.total_net_pnl for r in rr)
        cagr = compute_cagr(net, args.capital, rr[0].entry_date, rr[-1].entry_date) * 100
        wins = sum(1 for r in rr if r.total_net_pnl > 0)
        dd, mx = compute_equity_curve([r.total_net_pnl for r in rr])
        lines.append(
            f"| {run_id} | `{seed}` | `₹{fmt(net)}` | `{cagr:.2f}%` "
            f"| `{wins/len(rr)*100:.1f}%` | `₹{fmt(mx)}` | `₹{fmt(dd)}` |"
        )
    lines += [""]

    # Monthly + yearly for best combo
    sample_rr  = best_runs[sorted(best_runs)[0]]
    all_months = sorted({r.entry_date[:7] for r in sample_rr})
    all_years  = sorted({r.entry_date[:4] for r in sample_rr})

    lines += [
        "### Monthly P/L — Best Combo (each run + avg)",
        "",
        "| Month | Run1 | Run2 | Run3 | Run4 | Run5 | Avg |",
        "|-------|------|------|------|------|------|-----|",
    ]
    for month in all_months:
        cells = []
        for run_id in sorted(best_runs):
            m_net = sum(r.total_net_pnl for r in best_runs[run_id] if r.entry_date[:7] == month)
            cells.append(f"₹{fmt(m_net)}")
        avg_m = sum(
            sum(r.total_net_pnl for r in best_runs[rid] if r.entry_date[:7] == month)
            for rid in best_runs
        ) / len(best_runs)
        lines.append("| " + month + " | " + " | ".join(f"`{c}`" for c in cells)
                     + f" | `₹{fmt(avg_m)}` |")
    lines += [""]

    lines += [
        "### Yearly P/L — Best Combo (each run + avg)",
        "",
        "| Year | Run1 | Run2 | Run3 | Run4 | Run5 | Avg |",
        "|------|------|------|------|------|------|-----|",
    ]
    for year in all_years:
        cells = []
        for run_id in sorted(best_runs):
            y_net = sum(r.total_net_pnl for r in best_runs[run_id] if r.entry_date[:4] == year)
            cells.append(f"₹{fmt(y_net)}")
        avg_y = sum(
            sum(r.total_net_pnl for r in best_runs[rid] if r.entry_date[:4] == year)
            for rid in best_runs
        ) / len(best_runs)
        lines.append("| " + year + " | " + " | ".join(f"`{c}`" for c in cells)
                     + f" | `₹{fmt(avg_y)}` |")
    lines += ["", "---", ""]

    # Yearly table across all combos
    all_combos_ordered = [(sl, tgt) for sl in SL_LEVELS for tgt in TARGET_LEVELS]
    combo_labels_short = [
        f"SL{int(sl*100)}T{target_label(tgt)}" for sl, tgt in all_combos_ordered
    ]
    year_hdr = " | ".join(f"`{lbl}`" for lbl in combo_labels_short)
    year_sep = " | ".join("--------" for _ in all_combos_ordered)
    lines += [
        "## Yearly Avg Net P/L by Combo (across 5 runs)",
        "",
        f"| Year | {year_hdr} |",
        f"|------|{year_sep}|",
    ]
    for year in all_years:
        cells = []
        for sl, tgt in all_combos_ordered:
            rc = results_map.get((sl, tgt), {})
            if not rc:
                cells.append("—")
                continue
            avg_y = sum(
                sum(r.total_net_pnl for r in rc[rid] if r.entry_date[:4] == year)
                for rid in rc
            ) / len(rc)
            cells.append(f"₹{fmt(avg_y)}")
        lines.append("| " + year + " | " + " | ".join(f"`{c}`" for c in cells) + " |")
    lines += ["", "---", ""]

    # Skip summary
    skip_by: Dict[str, int] = {}
    for s in skipped:
        skip_by[s.skip_reason] = skip_by.get(s.skip_reason, 0) + 1
    lines += ["## Skip Summary", ""]
    for reason, cnt in sorted(skip_by.items(), key=lambda x: -x[1]):
        lines.append(f"- `{reason}`: {cnt}")

    lines += [
        "",
        "## Remarks",
        "",
        "- 28 parameter combos × 5 runs = 140 simulation series.",
        "- LONG position: buy ATM option, exit when price moves up (target) or down (SL).",
        "- All 140 series share identical price data; only CE/PE coin flip differs.",
        "- Fixed seeds ensure reproducibility.",
        "- `open` target = hold until SL or 15:20, no profit booking.",
        "- Second trade at 12:00 only if morning SL hits BEFORE 12:00.",
        "- Second trade: BUY opposite option with same SL/target.",
        "- SL (low candle) checked before target (high candle) within each candle.",
        "- Slippage 0.5 pt/order × 2 per trade; brokerage ₹50/trade.",
        "- Max drawdown = largest peak-to-trough drop in cumulative equity.",
        "- CAGR computed on notional capital ₹5,00,000.",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)

    print("Pass 1: loading day data ...")
    days, skipped = collect_day_data(args)
    print(f"  Loaded {len(days)} days, {len(skipped)} skipped.")

    results_map: ResultsMap = {}
    all_results: List[TradeResult] = []
    total_combos = len(SL_LEVELS) * len(TARGET_LEVELS)

    combo_num = 0
    for sl in SL_LEVELS:
        for tgt in TARGET_LEVELS:
            combo_num += 1
            ck = combo_key(sl, tgt)
            print(f"Combo {combo_num:2d}/{total_combos}  {ck}")
            results_map[(sl, tgt)] = {}
            for i, seed in enumerate(SEEDS, start=1):
                run_results = simulate_one(days, sl, tgt, i, seed)
                results_map[(sl, tgt)][i] = run_results
                all_results.extend(run_results)
                net = sum(r.total_net_pnl for r in run_results)
                print(f"  Run {i} seed={seed}: Rs.{fmt(net)}")

    print(f"\nTotal result rows: {len(all_results)}")
    print("Writing CSV ...")
    write_daywise_csv(all_results, args.results_dir / DAYWISE_CSV)
    print("Writing summary ...")
    write_summary(results_map, skipped, args.results_dir / SUMMARY_MD, args)

    print(f"\nDaywise CSV : {args.results_dir / DAYWISE_CSV}")
    print(f"Summary     : {args.results_dir / SUMMARY_MD}")


if __name__ == "__main__":
    main()
