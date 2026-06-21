#!/usr/bin/env python3
"""
Combined Intraday Short Strangle — NIFTY Mon/Tue/Fri + SENSEX Wed/Thu
Sep 1 2025 → latest available data. Tests SL from 20% to 100%.

Strike selection (per day):
  - Friday   NIFTY  : OTM CE + PE in price range [10, 20]
  - Monday   NIFTY  : OTM CE + PE in price range [7,  15]
  - Tuesday  NIFTY  : OTM CE + PE in price range [5,  10]
  - Wednesday SENSEX : OTM CE + PE in price range [30, 50]
  - Thursday  SENSEX : OTM CE + PE in price range [15, 40]

Pair selection: among all OTM CE (above ATM) and OTM PE (below ATM) whose
entry price falls in the day's range, pick the pair with:
  1. Minimum |CE_price - PE_price|  (most balanced)
  2. Minimum total CE_price + PE_price  (cheapest when tied)

SL levels: 20%, 30%, 40%, 50%, 60%, 70%, 80%, 90%, 100%
"""
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

IST_SUFFIX    = "+05:30"
BASE_FILENAME = "combined_strangle_2025"
DAYWISE_CSV   = f"{BASE_FILENAME}_daywise.csv"
SUMMARY_MD    = f"{BASE_FILENAME}_summary.md"
LOG_FILE      = f"{BASE_FILENAME}.log"
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
START_DATE    = "2025-09-01"
SL_LEVELS     = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
MAX_SEARCH    = 25   # max strikes to scan OTM in each direction

# Day → (index, min_price, max_price, strike_interval)
DAY_CONFIG: Dict[str, Tuple[str, float, float, int]] = {
    "Monday":    ("NIFTY",   7,  15, 50),
    "Tuesday":   ("NIFTY",   5,  10, 50),
    "Wednesday": ("SENSEX", 30,  50, 100),
    "Thursday":  ("SENSEX", 15,  40, 100),
    "Friday":    ("NIFTY",  10,  20, 50),
}


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class PriceRow:
    timestamp: str
    open_value: float
    high_value: float


@dataclass
class ContractData:
    path: Path
    rows_by_timestamp: Dict[str, PriceRow]


@dataclass
class RawTrade:
    """Entry data captured once; used to compute P&L at any SL level."""
    index: str
    entry_date: str
    day_of_week: str
    expiry_date: str
    spot_open_text: str
    atm: int
    ce_strike: int
    pe_strike: int
    lot_size: int
    num_lots: int
    qty: int
    ce_open: float
    pe_open: float
    ce_path_name: str
    pe_path_name: str
    entry_ts: str
    exit_ts: str
    slippage: float
    brokerage_per_straddle: float
    ce_contract: ContractData = field(repr=False)
    pe_contract: ContractData = field(repr=False)


@dataclass
class SkippedDay:
    index: str
    entry_date: str
    day_of_week: str
    skip_reason: str
    remarks: str


@dataclass
class TradeResult:
    """Computed result for one trade at one SL level."""
    index: str
    entry_date: str
    day_of_week: str
    expiry_date: str
    atm: int
    ce_strike: int
    pe_strike: int
    qty: int
    ce_open: float
    pe_open: float
    sl_pct: float
    ce_exit_ts: str
    ce_exit_price: str
    ce_exit_reason: str
    ce_points_pnl: float
    ce_gross_pnl: float
    pe_exit_ts: str
    pe_exit_price: str
    pe_exit_reason: str
    pe_points_pnl: float
    pe_gross_pnl: float
    gross_pnl: float
    net_pnl: float


# ---------------------------------------------------------------------------
# CLI ARGS
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    p = argparse.ArgumentParser(description="Combined NIFTY+SENSEX strangle with multi-SL testing.")
    p.add_argument("--nifty-spot-file", type=Path,
                   default=repo_root / "nifty" / "NIFTY50_INDEX_5m_last_7y.csv")
    p.add_argument("--sensex-spot-file", type=Path,
                   default=repo_root / "nifty" / "SENSEX_INDEX_5m_last_7y.csv")
    p.add_argument("--nifty-options-dir", type=Path,
                   default=repo_root / "NiftyOptions_2020_2026" / "Options")
    p.add_argument("--sensex-options-dir", type=Path,
                   default=repo_root / "SensexOptions_2024_2026" / "Options")
    p.add_argument("--results-dir", type=Path,
                   default=repo_root / "backtesting" / "results")
    p.add_argument("--entry-time", default="09:20")
    p.add_argument("--exit-time", default="15:20")
    p.add_argument("--brokerage-per-order", type=float, default=25.0)
    p.add_argument("--slippage-per-order", type=float, default=0.5)
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


def round_to_n(price: float, n: int) -> int:
    rem = price % n
    base = int(price - rem)
    return base if rem < n / 2 else base + n


def get_nifty_lot_config(expiry_date: str) -> Tuple[int, int]:
    d = datetime.date.fromisoformat(expiry_date)
    if d <= datetime.date(2021, 10, 6):  return 75, 4
    if d <= datetime.date(2024, 4, 25):  return 50, 6
    if d <= datetime.date(2024, 11, 21): return 25, 12
    if d <= datetime.date(2025, 12, 30): return 75, 4
    return 65, 5


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger(BASE_FILENAME)
    for h in logger.handlers:
        h.close()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    h = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(h)
    logger.propagate = False
    return logger


def close_logger(logger: logging.Logger) -> None:
    for h in logger.handlers:
        h.close()
    logger.handlers.clear()


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------

def load_spot_opens(
    spot_file: Path, entry_time: str
) -> Tuple[List[str], Dict[str, Tuple[float, str]]]:
    trading_days: List[str] = []
    seen: Dict[str, bool] = {}
    spot_open: Dict[str, Tuple[float, str]] = {}
    marker = f"T{entry_time}:00"
    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
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
                high_value=float(row["high"]),
            )
    cache[path] = ContractData(path=path, rows_by_timestamp=rows)
    return cache[path]


# ---------------------------------------------------------------------------
# STRANGLE PAIR SELECTION
# ---------------------------------------------------------------------------

def find_strangle_pair(
    options_dir: Path,
    prefix: str,
    expiry_date: str,
    entry_ts: str,
    atm: int,
    strike_interval: int,
    min_price: float,
    max_price: float,
    cache: Dict[Path, Optional[ContractData]],
) -> Optional[Tuple[int, float, ContractData, int, float, ContractData]]:
    """
    Search OTM CE (above ATM) and OTM PE (below ATM) for a balanced pair
    whose entry price falls in [min_price, max_price].

    Returns (ce_strike, ce_price, ce_contract, pe_strike, pe_price, pe_contract)
    for the pair with minimum |CE_price - PE_price|, ties broken by lowest total.
    Returns None if no valid pair found.
    """
    suffix = expiry_suffix(expiry_date)

    ce_candidates: List[Tuple[int, float, ContractData]] = []
    for i in range(1, MAX_SEARCH + 1):
        strike = atm + i * strike_interval
        path = options_dir / expiry_date / f"{prefix}_{strike}_CE_{suffix}.csv"
        contract = load_contract(path, cache)
        if contract is None:
            continue
        row = contract.rows_by_timestamp.get(entry_ts)
        if row is None or row.open_value <= 0:
            continue
        price = row.open_value
        if price < min_price:
            break    # going further OTM only makes it cheaper; stop scanning
        if price <= max_price:
            ce_candidates.append((strike, price, contract))

    pe_candidates: List[Tuple[int, float, ContractData]] = []
    for i in range(1, MAX_SEARCH + 1):
        strike = atm - i * strike_interval
        if strike <= 0:
            break
        path = options_dir / expiry_date / f"{prefix}_{strike}_PE_{suffix}.csv"
        contract = load_contract(path, cache)
        if contract is None:
            continue
        row = contract.rows_by_timestamp.get(entry_ts)
        if row is None or row.open_value <= 0:
            continue
        price = row.open_value
        if price < min_price:
            break
        if price <= max_price:
            pe_candidates.append((strike, price, contract))

    if not ce_candidates or not pe_candidates:
        return None

    best = None
    best_diff  = float("inf")
    best_total = float("inf")
    for ce_strike, ce_price, ce_contract in ce_candidates:
        for pe_strike, pe_price, pe_contract in pe_candidates:
            diff  = abs(ce_price - pe_price)
            total = ce_price + pe_price
            if diff < best_diff or (diff == best_diff and total < best_total):
                best_diff  = diff
                best_total = total
                best = (ce_strike, ce_price, ce_contract, pe_strike, pe_price, pe_contract)
    return best


# ---------------------------------------------------------------------------
# SL RESOLUTION
# ---------------------------------------------------------------------------

def resolve_leg(
    contract: ContractData,
    entry_open: float,
    entry_ts: str,
    exit_ts: str,
    sl_pct: float,
    slippage: float,
    qty: int,
) -> Tuple[str, str, str, float, float]:
    """Walk 1-minute candles. Returns (exit_ts, exit_price_str, reason, points, gross)."""
    stop   = entry_open * (1.0 + sl_pct)
    window = sorted(ts for ts in contract.rows_by_timestamp if entry_ts <= ts <= exit_ts)
    for ts in window:
        row = contract.rows_by_timestamp[ts]
        if row.open_value >= stop:
            pts = entry_open - row.open_value - 2 * slippage
            return ts, fmt(row.open_value), "gap_sl", pts, pts * qty
        if row.high_value >= stop:
            pts = entry_open - stop - 2 * slippage
            return ts, fmt(stop), "sl", pts, pts * qty
    exit_row = contract.rows_by_timestamp.get(exit_ts)
    if exit_row:
        pts = entry_open - exit_row.open_value - 2 * slippage
        return exit_ts, fmt(exit_row.open_value), "day_close", pts, pts * qty
    candidates = [ts for ts in contract.rows_by_timestamp if ts <= exit_ts]
    if candidates:
        last_ts  = max(candidates)
        last_row = contract.rows_by_timestamp[last_ts]
        pts = entry_open - last_row.open_value - 2 * slippage
        return last_ts, fmt(last_row.open_value), "last_candle_before_exit", pts, pts * qty
    return exit_ts, fmt(entry_open), "missing_exit_candle", 0.0, 0.0


# ---------------------------------------------------------------------------
# MAIN BACKTEST ENTRY COLLECTION
# ---------------------------------------------------------------------------

def collect_entries(args: argparse.Namespace) -> Tuple[List[RawTrade], List[SkippedDay]]:
    """Pass 1: find strangle pairs. No SL computation yet."""
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILE)

    nifty_days, nifty_spot  = load_spot_opens(args.nifty_spot_file,  args.entry_time)
    _,          sensex_spot = load_spot_opens(args.sensex_spot_file, args.entry_time)

    nifty_expiries  = load_expiry_folders(args.nifty_options_dir)
    sensex_expiries = load_expiry_folders(args.sensex_options_dir)

    contract_cache: Dict[Path, Optional[ContractData]] = {}
    raw_trades: List[RawTrade]   = []
    skipped:    List[SkippedDay] = []

    brokerage_per_straddle = args.brokerage_per_order * 4

    try:
        for entry_date in nifty_days:
            if entry_date < START_DATE:
                continue
            wd = datetime.date.fromisoformat(entry_date).weekday()
            if wd >= 5:
                continue
            day_name = WEEKDAY_NAMES[wd]

            if day_name not in DAY_CONFIG:
                continue
            index, min_price, max_price, strike_interval = DAY_CONFIG[day_name]

            spot_opens  = nifty_spot  if index == "NIFTY"  else sensex_spot
            expiries    = nifty_expiries  if index == "NIFTY"  else sensex_expiries
            options_dir = args.nifty_options_dir if index == "NIFTY" else args.sensex_options_dir
            prefix      = index

            entry_ts = build_ts(entry_date, args.entry_time)
            exit_ts  = build_ts(entry_date, args.exit_time)

            spot = spot_opens.get(entry_date)
            if not spot:
                skipped.append(SkippedDay(index, entry_date, day_name,
                                          "missing_spot_entry",
                                          f"No {index} spot at {entry_ts}."))
                continue

            spot_val, spot_text = spot
            expiry_date = first_expiry_on_or_after(expiries, entry_date)
            if expiry_date is None:
                skipped.append(SkippedDay(index, entry_date, day_name,
                                          "no_expiry_found", ""))
                continue

            if index == "NIFTY":
                lot_size, num_lots = get_nifty_lot_config(expiry_date)
            else:
                lot_size, num_lots = 10, 10
            qty = lot_size * num_lots
            atm = round_to_n(spot_val, strike_interval)

            pair = find_strangle_pair(
                options_dir, prefix, expiry_date, entry_ts,
                atm, strike_interval, min_price, max_price,
                contract_cache,
            )

            if pair is None:
                skipped.append(SkippedDay(
                    index, entry_date, day_name, "no_strangle_pair",
                    f"No balanced OTM pair found in [{min_price},{max_price}] "
                    f"within {MAX_SEARCH} strikes of ATM={atm}.",
                ))
                logger.info("SKIPPED %s %s no_strangle_pair atm=%s range=[%s,%s]",
                            index, entry_date, atm, min_price, max_price)
                continue

            ce_strike, ce_open, ce_contract, pe_strike, pe_open, pe_contract = pair
            suffix = expiry_suffix(expiry_date)
            ce_name = f"{prefix}_{ce_strike}_CE_{suffix}.csv"
            pe_name = f"{prefix}_{pe_strike}_PE_{suffix}.csv"

            raw_trades.append(RawTrade(
                index=index, entry_date=entry_date, day_of_week=day_name,
                expiry_date=expiry_date, spot_open_text=spot_text,
                atm=atm, ce_strike=ce_strike, pe_strike=pe_strike,
                lot_size=lot_size, num_lots=num_lots, qty=qty,
                ce_open=ce_open, pe_open=pe_open,
                ce_path_name=ce_name, pe_path_name=pe_name,
                entry_ts=entry_ts, exit_ts=exit_ts,
                slippage=args.slippage_per_order,
                brokerage_per_straddle=brokerage_per_straddle,
                ce_contract=ce_contract, pe_contract=pe_contract,
            ))
            logger.info(
                "ENTRY %s %s day=%s expiry=%s atm=%s CE=%s(%.2f) PE=%s(%.2f) qty=%s",
                index, entry_date, day_name, expiry_date, atm,
                ce_strike, ce_open, pe_strike, pe_open, qty,
            )

    except Exception:
        logger.exception("ERROR unexpected failure")
        raise
    finally:
        logger.info("ENTRIES found=%s skipped=%s", len(raw_trades), len(skipped))
        close_logger(logger)

    return raw_trades, skipped


# ---------------------------------------------------------------------------
# PASS 2: COMPUTE P&L FOR EACH SL LEVEL
# ---------------------------------------------------------------------------

def compute_results(raw_trades: List[RawTrade]) -> List[TradeResult]:
    """For every raw trade × every SL level, compute P&L."""
    results: List[TradeResult] = []
    for rt in raw_trades:
        for sl_pct in SL_LEVELS:
            ce_exit_ts, ce_exit_px, ce_reason, ce_pts, ce_gross = resolve_leg(
                rt.ce_contract, rt.ce_open, rt.entry_ts, rt.exit_ts,
                sl_pct, rt.slippage, rt.qty,
            )
            pe_exit_ts, pe_exit_px, pe_reason, pe_pts, pe_gross = resolve_leg(
                rt.pe_contract, rt.pe_open, rt.entry_ts, rt.exit_ts,
                sl_pct, rt.slippage, rt.qty,
            )
            gross = ce_gross + pe_gross
            net   = gross - rt.brokerage_per_straddle
            results.append(TradeResult(
                index=rt.index, entry_date=rt.entry_date, day_of_week=rt.day_of_week,
                expiry_date=rt.expiry_date, atm=rt.atm,
                ce_strike=rt.ce_strike, pe_strike=rt.pe_strike, qty=rt.qty,
                ce_open=rt.ce_open, pe_open=rt.pe_open, sl_pct=sl_pct,
                ce_exit_ts=ce_exit_ts, ce_exit_price=ce_exit_px, ce_exit_reason=ce_reason,
                ce_points_pnl=round(ce_pts, 4), ce_gross_pnl=round(ce_gross, 2),
                pe_exit_ts=pe_exit_ts, pe_exit_price=pe_exit_px, pe_exit_reason=pe_reason,
                pe_points_pnl=round(pe_pts, 4), pe_gross_pnl=round(pe_gross, 2),
                gross_pnl=round(gross, 2), net_pnl=round(net, 2),
            ))
    return results


# ---------------------------------------------------------------------------
# OUTPUT: DAYWISE CSV
# ---------------------------------------------------------------------------

def write_daywise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "index", "entry_date", "day_of_week", "expiry_date",
        "atm_strike", "ce_strike", "pe_strike", "qty",
        "ce_entry_open", "pe_entry_open", "sl_pct",
        "ce_exit_ts", "ce_exit_price", "ce_exit_reason", "ce_points_pnl", "ce_gross_pnl",
        "pe_exit_ts", "pe_exit_price", "pe_exit_reason", "pe_points_pnl", "pe_gross_pnl",
        "gross_pnl", "net_pnl",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in results:
            w.writerow({
                "index": r.index, "entry_date": r.entry_date,
                "day_of_week": r.day_of_week, "expiry_date": r.expiry_date,
                "atm_strike": r.atm, "ce_strike": r.ce_strike, "pe_strike": r.pe_strike,
                "qty": r.qty, "ce_entry_open": fmt(r.ce_open), "pe_entry_open": fmt(r.pe_open),
                "sl_pct": f"{r.sl_pct*100:.0f}%",
                "ce_exit_ts": r.ce_exit_ts, "ce_exit_price": r.ce_exit_price,
                "ce_exit_reason": r.ce_exit_reason,
                "ce_points_pnl": fmt(r.ce_points_pnl), "ce_gross_pnl": fmt(r.ce_gross_pnl),
                "pe_exit_ts": r.pe_exit_ts, "pe_exit_price": r.pe_exit_price,
                "pe_exit_reason": r.pe_exit_reason,
                "pe_points_pnl": fmt(r.pe_points_pnl), "pe_gross_pnl": fmt(r.pe_gross_pnl),
                "gross_pnl": fmt(r.gross_pnl), "net_pnl": fmt(r.net_pnl),
            })


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
    d0 = datetime.date.fromisoformat(first_date)
    d1 = datetime.date.fromisoformat(last_date)
    days = (d1 - d0).days
    if days <= 0:
        return 0.0
    base = 1.0 + net_total / capital
    if base <= 0:
        return -1.0
    return base ** (365.25 / days) - 1.0


def group_by_sl(results: List[TradeResult]) -> Dict[float, List[TradeResult]]:
    by_sl: Dict[float, List[TradeResult]] = {}
    for r in results:
        by_sl.setdefault(r.sl_pct, []).append(r)
    return by_sl


def metrics(trades: List[TradeResult], capital: float) -> Dict:
    if not trades:
        return {}
    net_total = sum(r.net_pnl for r in trades)
    wins      = sum(1 for r in trades if r.net_pnl > 0)
    max_dd, max_cum = compute_equity_curve([r.net_pnl for r in trades])
    cagr = compute_cagr(net_total, capital, trades[0].entry_date, trades[-1].entry_date)
    return {
        "n": len(trades), "wins": wins, "losses": len(trades) - wins,
        "win_pct": wins / len(trades) * 100,
        "net": net_total, "max_dd": max_dd, "max_cum": max_cum,
        "cagr_pct": cagr * 100,
    }


# ---------------------------------------------------------------------------
# OUTPUT: SUMMARY MARKDOWN
# ---------------------------------------------------------------------------

def write_summary(
    results: List[TradeResult],
    raw_trades: List[RawTrade],
    skipped: List[SkippedDay],
    output_path: Path,
    args: argparse.Namespace,
) -> None:
    by_sl = group_by_sl(results)

    # All unique traded dates (from 20% SL results as representative)
    sample = by_sl.get(0.20, [])
    first_date = sample[0].entry_date  if sample else START_DATE
    last_date  = sample[-1].entry_date if sample else START_DATE

    skip_by_reason: Dict[str, int] = {}
    for s in skipped:
        key = f"{s.index}:{s.skip_reason}"
        skip_by_reason[key] = skip_by_reason.get(key, 0) + 1

    # ---------- header
    lines = [
        "# Combined Short Strangle — NIFTY Mon/Tue/Fri + SENSEX Wed/Thu (Sep 2025+)",
        "",
        "## Strategy Details",
        "",
        f"- Period: `{START_DATE}` → latest available data",
        f"- Entry: `{args.entry_time}` — sell OTM CE + OTM PE",
        f"- Exit: `{args.exit_time}` — day close if SL not hit",
        "- Expiry: current-week, traded even on expiry day (no roll)",
        "- No balance filter — pair selected by minimum price difference",
        "",
        "| Day | Index | OTM Price Range | Qty |",
        "|-----|-------|-----------------|-----|",
        "| Monday    | NIFTY  | ₹7 – ₹15  | ~300 |",
        "| Tuesday   | NIFTY  | ₹5 – ₹10  | ~300 |",
        "| Wednesday | SENSEX | ₹30 – ₹50 | 100  |",
        "| Thursday  | SENSEX | ₹15 – ₹40 | 100  |",
        "| Friday    | NIFTY  | ₹10 – ₹20 | ~300 |",
        "",
        "**Pair selection:** among all OTM CE (above ATM) and OTM PE (below ATM) "
        "with entry price in the day's range, choose the pair with minimum "
        "|CE_price − PE_price|. On ties, prefer lowest total premium.",
        "",
        f"- Slippage: {fmt(args.slippage_per_order)} pt/order (2× per leg)",
        f"- Brokerage: ₹{fmt(args.brokerage_per_order)}/order → "
        f"₹{fmt(args.brokerage_per_order * 4)}/straddle",
        f"- Notional capital for CAGR: ₹{args.capital:,.0f}",
        f"- Traded days found: `{len(raw_trades)}`  Skipped: `{len(skipped)}`",
        "",
        "---",
        "",
    ]

    # ---------- MAIN COMPARISON TABLE (SL vs NIFTY / SENSEX / Combined)
    lines += [
        "## SL Level Comparison",
        "",
        "| SL % | NIFTY Net P/L | NIFTY Win% | NIFTY Drawdown "
        "| SENSEX Net P/L | SENSEX Win% | SENSEX Drawdown "
        "| Combined Net P/L | Combined Win% | Combined CAGR |",
        "|------|---------------|------------|----------------|"
        "----------------|-------------|----------------|"
        "------------------|---------------|---------------|",
    ]

    best_combined_sl = None
    best_combined_net = float("-inf")

    for sl in SL_LEVELS:
        sl_results = by_sl.get(sl, [])
        nifty_r   = [r for r in sl_results if r.index == "NIFTY"]
        sensex_r  = [r for r in sl_results if r.index == "SENSEX"]

        def _row(grp: List[TradeResult]) -> Tuple[str, str, str]:
            if not grp:
                return "—", "—", "—"
            net  = sum(r.net_pnl for r in grp)
            wins = sum(1 for r in grp if r.net_pnl > 0)
            dd, _ = compute_equity_curve([r.net_pnl for r in grp])
            return f"₹{fmt(net)}", f"{wins/len(grp)*100:.1f}%", f"₹{fmt(dd)}"

        n_net, n_win, n_dd = _row(nifty_r)
        s_net, s_win, s_dd = _row(sensex_r)
        c_net_v, c_win, c_dd = _row(sl_results)

        comb_net_float = sum(r.net_pnl for r in sl_results) if sl_results else 0.0
        comb_cagr = compute_cagr(comb_net_float, args.capital, first_date, last_date) * 100
        if comb_net_float > best_combined_net:
            best_combined_net = comb_net_float
            best_combined_sl  = sl

        sl_label = f"**{sl*100:.0f}%**" if sl == best_combined_sl else f"{sl*100:.0f}%"
        lines.append(
            f"| {sl_label} | `{n_net}` | `{n_win}` | `{n_dd}` "
            f"| `{s_net}` | `{s_win}` | `{s_dd}` "
            f"| `{c_net_v}` | `{c_win}` | `{comb_cagr:.1f}%` |"
        )

    lines += ["", f"_Bold row = best combined Net P/L (SL {best_combined_sl*100:.0f}%)_", "", "---", ""]

    # ---------- DAY-OF-WEEK TABLE (per SL)
    lines += [
        "## Day-of-Week P&L by SL Level",
        "",
        "| SL % | Monday (N) | Tuesday (N) | Wednesday (S) | Thursday (S) | Friday (N) |",
        "|------|------------|-------------|---------------|--------------|------------|",
    ]
    for sl in SL_LEVELS:
        sl_results = by_sl.get(sl, [])
        by_day: Dict[str, List[TradeResult]] = {}
        for r in sl_results:
            by_day.setdefault(r.day_of_week, []).append(r)
        row_parts = []
        for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            dr = by_day.get(d, [])
            if not dr:
                row_parts.append("—")
            else:
                avg = sum(r.net_pnl for r in dr) / len(dr)
                row_parts.append(f"₹{fmt(avg)}")
        lines.append(
            f"| {sl*100:.0f}% | `{row_parts[0]}` | `{row_parts[1]}` "
            f"| `{row_parts[2]}` | `{row_parts[3]}` | `{row_parts[4]}` |"
        )

    lines += ["", "_(N) = NIFTY  (S) = SENSEX  Values are avg net P/L per traded day_", "", "---", ""]

    # ---------- MONTHLY BREAKDOWN PER SL (combined)
    lines += ["## Monthly P&L by SL Level (Combined)", ""]

    # Build month list
    all_months = sorted({r.entry_date[:7] for r in results})

    # Header
    sl_headers   = " | ".join(f"SL {int(sl*100)}%" for sl in SL_LEVELS)
    sl_separator = " | ".join("-------" for _ in SL_LEVELS)
    lines.append(f"| Month | {sl_headers} |")
    lines.append(f"|-------|{sl_separator}|")

    for month in all_months:
        cells = []
        for sl in SL_LEVELS:
            sl_results = by_sl.get(sl, [])
            month_r = [r for r in sl_results if r.entry_date[:7] == month]
            if not month_r:
                cells.append("—")
            else:
                net = sum(r.net_pnl for r in month_r)
                cells.append(f"₹{fmt(net)}")
        lines.append(f"| {month} | " + " | ".join(f"`{c}`" for c in cells) + " |")

    lines += ["", "---", ""]

    # ---------- DETAILED MONTHLY TABLES (best SL level)
    if best_combined_sl is not None:
        best_sl_results = by_sl.get(best_combined_sl, [])
        lines += [
            f"## Detailed Monthly Breakdown — Best SL ({best_combined_sl*100:.0f}%)",
            "",
        ]
        for grp_label, grp_results in [
            ("Combined (All 5 days)", best_sl_results),
            ("NIFTY only (Mon/Tue/Fri)", [r for r in best_sl_results if r.index == "NIFTY"]),
            ("SENSEX only (Wed/Thu)",    [r for r in best_sl_results if r.index == "SENSEX"]),
        ]:
            if not grp_results:
                continue
            by_month: Dict[str, List[TradeResult]] = {}
            for r in grp_results:
                by_month.setdefault(r.entry_date[:7], []).append(r)
            lines += [
                f"### {grp_label}",
                "",
                "| Month | Trades | Win | Loss | Net P/L | Avg/Day | Cumulative |",
                "|-------|--------|-----|------|---------|---------|------------|",
            ]
            running = 0.0
            for month in sorted(by_month):
                mr    = by_month[month]
                m_net = sum(r.net_pnl for r in mr)
                m_win = sum(1 for r in mr if r.net_pnl > 0)
                m_los = sum(1 for r in mr if r.net_pnl < 0)
                running += m_net
                lines.append(
                    f"| {month} | {len(mr)} | {m_win} | {m_los} "
                    f"| `₹{fmt(m_net)}` | `₹{fmt(m_net/len(mr))}` | `₹{fmt(running)}` |"
                )
            lines.append("")

    lines += ["---", ""]

    # ---------- ENTRY PRICE OVERVIEW (show what prices were found)
    lines += [
        "## Entry Price Overview (Sample — first 20 trades)",
        "",
        "| Date | Day | Index | ATM | CE Strike | CE Price | PE Strike | PE Price | Diff |",
        "|------|-----|-------|-----|-----------|----------|-----------|----------|------|",
    ]
    for rt in raw_trades[:20]:
        diff = abs(rt.ce_open - rt.pe_open)
        lines.append(
            f"| {rt.entry_date} | {rt.day_of_week[:3]} | {rt.index} "
            f"| {rt.atm} | {rt.ce_strike} | `{fmt(rt.ce_open)}` "
            f"| {rt.pe_strike} | `{fmt(rt.pe_open)}` | `{fmt(diff)}` |"
        )
    lines += ["", "---", ""]

    # ---------- SKIP REASONS
    lines += ["## Skip Reason Summary", ""]
    for reason, count in sorted(skip_by_reason.items(), key=lambda x: -x[1]):
        lines.append(f"- `{reason}`: {count}")
    lines += ["", "## First 20 Skipped Days", ""]
    for s in skipped[:20]:
        lines.append(f"- `{s.entry_date}` ({s.day_of_week}) [{s.index}]: "
                     f"`{s.skip_reason}` — {s.remarks}")

    lines += [
        "",
        "## Remarks",
        "",
        "- Strangle: sell OTM CE (above ATM) + OTM PE (below ATM), independent SL per leg.",
        "- Pair chosen to minimise |CE_price − PE_price|; cheapest total on ties.",
        "- Early stop in OTM scan: if price drops below range floor, scan stops (cheaper strikes skipped).",
        "- gap_sl  : option opens at/above SL → filled at candle open.",
        "- sl      : option high touches SL → filled at SL price.",
        "- SL monitoring uses 1-minute option candles.",
        "- All 9 SL scenarios share the same entry; only exit differs.",
        "- CAGR computed on notional capital via --capital arg.",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)

    print("Pass 1: collecting strangle entries …")
    raw_trades, skipped = collect_entries(args)
    print(f"  Found {len(raw_trades)} entries, {len(skipped)} skipped.")

    print(f"Pass 2: computing P&L for {len(SL_LEVELS)} SL levels …")
    results = compute_results(raw_trades)
    print(f"  Computed {len(results)} result rows ({len(raw_trades)} trades × {len(SL_LEVELS)} SLs).")

    csv_path = args.results_dir / DAYWISE_CSV
    md_path  = args.results_dir / SUMMARY_MD

    write_daywise_csv(results, csv_path)
    write_summary(results, raw_trades, skipped, md_path, args)

    print(f"Daywise CSV : {csv_path}")
    print(f"Summary     : {md_path}")


if __name__ == "__main__":
    main()
