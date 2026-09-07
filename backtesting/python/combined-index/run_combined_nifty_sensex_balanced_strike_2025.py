#!/usr/bin/env python3
"""
Combined Intraday ATM Straddle — NIFTY Mon/Tue/Fri + SENSEX Wed/Thu
Sep 1 2025 → latest available data. Tests SL from 20% to 100%.

Balanced-strike search: start at ATM; if min(CE,PE)/max(CE,PE) < 70%,
try ATM±1, ATM±2, … up to max_search_strikes. First passing strike is used.

SL levels tested: 20%, 30%, 40%, 50%, 60%, 70%, 80%, 90%, 100%
Pass 1 — collect entries (strike search, no SL logic).
Pass 2 — compute P&L for every entry × every SL level.
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
BASE_FILENAME = "combined_nifty_sensex_balanced_strike_2025"
DAYWISE_CSV   = f"{BASE_FILENAME}_daywise.csv"
SUMMARY_MD    = f"{BASE_FILENAME}_summary.md"
LOG_FILE      = f"{BASE_FILENAME}.log"
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

NIFTY_DAYS  = {0, 1, 4}   # Mon=0, Tue=1, Fri=4
SENSEX_DAYS = {2, 3}       # Wed=2, Thu=3
START_DATE  = "2025-09-01"
SL_LEVELS   = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class PriceRow:
    timestamp: str
    open_value: float
    open_text: str
    high_value: float


@dataclass
class ContractData:
    path: Path
    rows_by_timestamp: Dict[str, PriceRow]


@dataclass
class RawTrade:
    """Entry data captured once; reused for every SL level."""
    index: str
    entry_date: str
    day_of_week: str
    expiry_date: str
    spot_entry_timestamp: str
    spot_entry_open: str
    atm_strike: int
    chosen_strike: int
    strike_offset: int
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
    """Result for one trade at one SL level."""
    index: str
    entry_date: str
    day_of_week: str
    expiry_date: str
    atm_strike: int
    chosen_strike: int
    strike_offset: int
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
    p = argparse.ArgumentParser(
        description="Combined NIFTY+SENSEX balanced-strike straddle, multi-SL testing."
    )
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
    p.add_argument("--balance-min-ratio", type=float, default=0.70)
    p.add_argument("--max-search-strikes", type=int, default=5)
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
                open_text=row["open"],
                high_value=float(row["high"]),
            )
    cache[path] = ContractData(path=path, rows_by_timestamp=rows)
    return cache[path]


# ---------------------------------------------------------------------------
# BALANCED STRIKE SEARCH
# ---------------------------------------------------------------------------

def find_balanced_strike(
    options_dir: Path,
    prefix: str,
    expiry_date: str,
    entry_ts: str,
    atm: int,
    strike_interval: int,
    max_search: int,
    balance_min_ratio: float,
    cache: Dict[Path, Optional[ContractData]],
) -> Optional[Tuple[int, int, ContractData, ContractData, PriceRow, PriceRow]]:
    """
    Search ATM, then ATM±1, ATM±2, … for a strike where
    min(CE,PE)/max(CE,PE) >= balance_min_ratio.
    Returns (chosen_strike, offset, ce_data, pe_data, ce_row, pe_row) or None.
    """
    suffix = expiry_suffix(expiry_date)
    candidates: List[Tuple[int, int]] = [(atm, 0)]
    for i in range(1, max_search + 1):
        candidates.append((atm + i * strike_interval, i))
        candidates.append((atm - i * strike_interval, i))

    for strike, offset in candidates:
        if strike <= 0:
            continue
        ce_path = options_dir / expiry_date / f"{prefix}_{strike}_CE_{suffix}.csv"
        pe_path = options_dir / expiry_date / f"{prefix}_{strike}_PE_{suffix}.csv"
        ce = load_contract(ce_path, cache)
        pe = load_contract(pe_path, cache)
        if ce is None or pe is None:
            continue
        ce_row = ce.rows_by_timestamp.get(entry_ts)
        pe_row = pe.rows_by_timestamp.get(entry_ts)
        if ce_row is None or pe_row is None:
            continue
        ce_open = ce_row.open_value
        pe_open = pe_row.open_value
        if ce_open <= 0 or pe_open <= 0:
            continue
        if min(ce_open, pe_open) / max(ce_open, pe_open) >= balance_min_ratio:
            return strike, offset, ce, pe, ce_row, pe_row
    return None


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
    """Returns (exit_ts, exit_price_str, reason, points_pnl, gross_pnl)."""
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
        last_ts = max(candidates)
        last_row = contract.rows_by_timestamp[last_ts]
        pts = entry_open - last_row.open_value - 2 * slippage
        return last_ts, fmt(last_row.open_value), "last_candle_before_exit", pts, pts * qty
    return exit_ts, fmt(entry_open), "missing_exit_candle", 0.0, 0.0


# ---------------------------------------------------------------------------
# PASS 1 — COLLECT ENTRIES
# ---------------------------------------------------------------------------

def collect_entries(args: argparse.Namespace) -> Tuple[List[RawTrade], List[SkippedDay]]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILE)

    nifty_days, nifty_spot  = load_spot_opens(args.nifty_spot_file,  args.entry_time)
    _,          sensex_spot = load_spot_opens(args.sensex_spot_file, args.entry_time)
    nifty_expiries  = load_expiry_folders(args.nifty_options_dir)
    sensex_expiries = load_expiry_folders(args.sensex_options_dir)

    contract_cache: Dict[Path, Optional[ContractData]] = {}
    brokerage = args.brokerage_per_order * 4
    raw_trades: List[RawTrade]   = []
    skipped:    List[SkippedDay] = []

    try:
        for entry_date in nifty_days:
            if entry_date < START_DATE:
                continue
            wd = datetime.date.fromisoformat(entry_date).weekday()
            if wd >= 5:
                continue
            day_name = WEEKDAY_NAMES[wd]
            entry_ts = build_ts(entry_date, args.entry_time)
            exit_ts  = build_ts(entry_date, args.exit_time)

            if wd in NIFTY_DAYS:
                index           = "NIFTY"
                spot_opens      = nifty_spot
                expiries        = nifty_expiries
                options_dir     = args.nifty_options_dir
                prefix          = "NIFTY"
                strike_interval = 50
            else:
                index           = "SENSEX"
                spot_opens      = sensex_spot
                expiries        = sensex_expiries
                options_dir     = args.sensex_options_dir
                prefix          = "SENSEX"
                strike_interval = 100

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

            lot_size, num_lots = get_nifty_lot_config(expiry_date) if index == "NIFTY" else (10, 10)
            qty = lot_size * num_lots
            atm = round_to_n(spot_val, strike_interval)

            found = find_balanced_strike(
                options_dir, prefix, expiry_date, entry_ts,
                atm, strike_interval,
                args.max_search_strikes, args.balance_min_ratio,
                contract_cache,
            )

            if found is None:
                skipped.append(SkippedDay(
                    index, entry_date, day_name, "no_balanced_strike",
                    f"No strike within {args.max_search_strikes} of ATM={atm} passes "
                    f"{args.balance_min_ratio*100:.0f}% balance rule.",
                ))
                logger.info("SKIPPED %s %s no_balanced_strike atm=%s", index, entry_date, atm)
                continue

            chosen_strike, offset, ce, pe, ce_row, pe_row = found
            suffix = expiry_suffix(expiry_date)
            ce_name = f"{prefix}_{chosen_strike}_CE_{suffix}.csv"
            pe_name = f"{prefix}_{chosen_strike}_PE_{suffix}.csv"
            offset_tag = f"+{offset}" if offset > 0 else str(offset)

            raw_trades.append(RawTrade(
                index=index, entry_date=entry_date, day_of_week=day_name,
                expiry_date=expiry_date,
                spot_entry_timestamp=entry_ts, spot_entry_open=spot_text,
                atm_strike=atm, chosen_strike=chosen_strike, strike_offset=offset,
                lot_size=lot_size, num_lots=num_lots, qty=qty,
                ce_open=ce_row.open_value, pe_open=pe_row.open_value,
                ce_path_name=ce_name, pe_path_name=pe_name,
                entry_ts=entry_ts, exit_ts=exit_ts,
                slippage=args.slippage_per_order,
                brokerage_per_straddle=brokerage,
                ce_contract=ce, pe_contract=pe,
            ))
            logger.info(
                "ENTRY %s %s day=%s expiry=%s atm=%s chosen=%s offset=%s "
                "ce=%.2f pe=%.2f ratio=%.2f qty=%s",
                index, entry_date, day_name, expiry_date, atm,
                chosen_strike, offset_tag,
                ce_row.open_value, pe_row.open_value,
                min(ce_row.open_value, pe_row.open_value) / max(ce_row.open_value, pe_row.open_value),
                qty,
            )

    except Exception:
        logger.exception("ERROR")
        raise
    finally:
        logger.info("ENTRIES found=%s skipped=%s", len(raw_trades), len(skipped))
        close_logger(logger)

    return raw_trades, skipped


# ---------------------------------------------------------------------------
# PASS 2 — COMPUTE P&L FOR EVERY ENTRY × EVERY SL LEVEL
# ---------------------------------------------------------------------------

def compute_results(raw_trades: List[RawTrade]) -> List[TradeResult]:
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
                expiry_date=rt.expiry_date,
                atm_strike=rt.atm_strike, chosen_strike=rt.chosen_strike,
                strike_offset=rt.strike_offset, qty=rt.qty,
                ce_open=rt.ce_open, pe_open=rt.pe_open, sl_pct=sl_pct,
                ce_exit_ts=ce_exit_ts, ce_exit_price=ce_exit_px, ce_exit_reason=ce_reason,
                ce_points_pnl=round(ce_pts, 4), ce_gross_pnl=round(ce_gross, 2),
                pe_exit_ts=pe_exit_ts, pe_exit_price=pe_exit_px, pe_exit_reason=pe_reason,
                pe_points_pnl=round(pe_pts, 4), pe_gross_pnl=round(pe_gross, 2),
                gross_pnl=round(gross, 2), net_pnl=round(net, 2),
            ))
    return results


# ---------------------------------------------------------------------------
# OUTPUT — DAYWISE CSV
# ---------------------------------------------------------------------------

def write_daywise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "index", "entry_date", "day_of_week", "expiry_date",
        "atm_strike", "chosen_strike", "strike_offset", "qty",
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
                "atm_strike": r.atm_strike, "chosen_strike": r.chosen_strike,
                "strike_offset": r.strike_offset, "qty": r.qty,
                "ce_entry_open": fmt(r.ce_open), "pe_entry_open": fmt(r.pe_open),
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


# ---------------------------------------------------------------------------
# OUTPUT — SUMMARY MARKDOWN
# ---------------------------------------------------------------------------

def write_summary(
    results: List[TradeResult],
    raw_trades: List[RawTrade],
    skipped: List[SkippedDay],
    output_path: Path,
    args: argparse.Namespace,
) -> None:
    by_sl = group_by_sl(results)
    sample = by_sl.get(0.20, [])
    first_date = sample[0].entry_date  if sample else START_DATE
    last_date  = sample[-1].entry_date if sample else START_DATE

    skip_by_reason: Dict[str, int] = {}
    for s in skipped:
        key = f"{s.index}:{s.skip_reason}"
        skip_by_reason[key] = skip_by_reason.get(key, 0) + 1

    at_atm  = sum(1 for rt in raw_trades if rt.strike_offset == 0)
    off_atm = sum(1 for rt in raw_trades if rt.strike_offset != 0)

    lines = [
        "# Combined NIFTY + SENSEX — Balanced-Strike ATM Straddle, Multi-SL (Sep 2025+)",
        "",
        "## Strategy Details",
        "",
        f"- Period: `{START_DATE}` → latest available data",
        f"- Entry: `{args.entry_time}` | Exit: `{args.exit_time}`",
        f"- Stop loss: tested from 20% to 100% in 10% steps (independent per leg)",
        "- Expiry: current-week, **traded even on expiry day itself** (no roll)",
        f"- Balanced-strike search: ATM → ATM±1 … ±{args.max_search_strikes}",
        f"  until `min(CE,PE)/max(CE,PE) ≥ {args.balance_min_ratio*100:.0f}%`.",
        "  If none found → day skipped.",
        "- **Monday / Tuesday / Friday** → NIFTY weekly options (~300 qty)",
        "- **Wednesday / Thursday**       → SENSEX weekly options (100 qty)",
        f"- Slippage: {fmt(args.slippage_per_order)} pt/order (2× per leg)",
        f"- Brokerage: ₹{fmt(args.brokerage_per_order)}/order → "
        f"₹{fmt(args.brokerage_per_order * 4)}/straddle",
        f"- Notional capital for CAGR: ₹{args.capital:,.0f}",
        f"- Traded days: `{len(raw_trades)}` "
        f"(at ATM: `{at_atm}` | adjusted strike: `{off_atm}`) | Skipped: `{len(skipped)}`",
        "",
        "---",
        "",
    ]

    # ── MAIN COMPARISON TABLE ─────────────────────────────────────────────
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

    best_sl = 0.20
    best_net = float("-inf")

    for sl in SL_LEVELS:
        sl_res = by_sl.get(sl, [])
        nifty_r  = [r for r in sl_res if r.index == "NIFTY"]
        sensex_r = [r for r in sl_res if r.index == "SENSEX"]

        def _col(grp: List[TradeResult]) -> Tuple[str, str, str]:
            if not grp:
                return "—", "—", "—"
            net  = sum(r.net_pnl for r in grp)
            wins = sum(1 for r in grp if r.net_pnl > 0)
            dd, _ = compute_equity_curve([r.net_pnl for r in grp])
            return f"₹{fmt(net)}", f"{wins/len(grp)*100:.1f}%", f"₹{fmt(dd)}"

        n_net, n_win, n_dd = _col(nifty_r)
        s_net, s_win, s_dd = _col(sensex_r)
        c_net_s, c_win, c_dd = _col(sl_res)

        comb_net = sum(r.net_pnl for r in sl_res) if sl_res else 0.0
        cagr_pct = compute_cagr(comb_net, args.capital, first_date, last_date) * 100
        if comb_net > best_net:
            best_net = comb_net
            best_sl  = sl

        label = f"**{sl*100:.0f}%**" if sl == best_sl else f"{sl*100:.0f}%"
        lines.append(
            f"| {label} | `{n_net}` | `{n_win}` | `{n_dd}` "
            f"| `{s_net}` | `{s_win}` | `{s_dd}` "
            f"| `{c_net_s}` | `{c_win}` | `{cagr_pct:.1f}%` |"
        )

    lines += ["", f"_Bold = best combined Net P/L (SL {best_sl*100:.0f}%)_", "", "---", ""]

    # ── DAY-OF-WEEK × SL TABLE ────────────────────────────────────────────
    lines += [
        "## Day-of-Week Avg Net P/L by SL Level",
        "",
        "| SL % | Monday (N) | Tuesday (N) | Wednesday (S) | Thursday (S) | Friday (N) |",
        "|------|------------|-------------|---------------|--------------|------------|",
    ]
    for sl in SL_LEVELS:
        sl_res = by_sl.get(sl, [])
        by_day: Dict[str, List[TradeResult]] = {}
        for r in sl_res:
            by_day.setdefault(r.day_of_week, []).append(r)
        cells = []
        for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            dr = by_day.get(d, [])
            cells.append(f"₹{fmt(sum(r.net_pnl for r in dr)/len(dr))}" if dr else "—")
        lines.append(
            f"| {sl*100:.0f}% | `{cells[0]}` | `{cells[1]}` "
            f"| `{cells[2]}` | `{cells[3]}` | `{cells[4]}` |"
        )
    lines += ["", "_(N)=NIFTY  (S)=SENSEX  avg net P/L per traded day_", "", "---", ""]

    # ── MONTHLY P&L × SL TABLE ────────────────────────────────────────────
    all_months = sorted({r.entry_date[:7] for r in results})
    sl_headers = " | ".join(f"SL {int(sl*100)}%" for sl in SL_LEVELS)
    sl_sep     = " | ".join("-------" for _ in SL_LEVELS)
    lines += ["## Monthly Net P/L by SL Level (Combined)", "", f"| Month | {sl_headers} |", f"|-------|{sl_sep}|"]
    for month in all_months:
        cells = []
        for sl in SL_LEVELS:
            sl_res = by_sl.get(sl, [])
            mr = [r for r in sl_res if r.entry_date[:7] == month]
            cells.append(f"₹{fmt(sum(r.net_pnl for r in mr))}" if mr else "—")
        lines.append(f"| {month} | " + " | ".join(f"`{c}`" for c in cells) + " |")
    lines += ["", "---", ""]

    # ── DETAILED BREAKDOWN AT BEST SL ────────────────────────────────────
    best_sl_res = by_sl.get(best_sl, [])
    lines += [f"## Detailed Breakdown — Best SL ({best_sl*100:.0f}%)", ""]

    for grp_label, grp in [
        ("Combined (NIFTY + SENSEX)", best_sl_res),
        ("NIFTY only (Mon/Tue/Fri)",  [r for r in best_sl_res if r.index == "NIFTY"]),
        ("SENSEX only (Wed/Thu)",     [r for r in best_sl_res if r.index == "SENSEX"]),
    ]:
        if not grp:
            continue
        net_total = sum(r.net_pnl for r in grp)
        wins      = sum(1 for r in grp if r.net_pnl > 0)
        losses    = len(grp) - wins
        max_dd, max_cum = compute_equity_curve([r.net_pnl for r in grp])
        ce_sl   = sum(1 for r in grp if "sl" in r.ce_exit_reason)
        pe_sl   = sum(1 for r in grp if "sl" in r.pe_exit_reason)
        both_sl = sum(1 for r in grp if "sl" in r.ce_exit_reason and "sl" in r.pe_exit_reason)
        cagr = compute_cagr(net_total, args.capital, grp[0].entry_date, grp[-1].entry_date) * 100
        best_r  = max(grp, key=lambda r: r.net_pnl)
        worst_r = min(grp, key=lambda r: r.net_pnl)

        lines += [
            f"### {grp_label}",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Traded days | `{len(grp)}` |",
            f"| Win / Loss | `{wins}` / `{losses}` |",
            f"| Win rate | `{wins/len(grp)*100:.1f}%` |",
            f"| CE SL hit | `{ce_sl}` | PE SL hit | `{pe_sl}` | Both | `{both_sl}` |",
            f"| **Net P/L** | **`₹{fmt(net_total)}`** |",
            f"| Max cumulative profit | `₹{fmt(max_cum)}` |",
            f"| Max drawdown | `₹{fmt(max_dd)}` |",
            f"| **CAGR** (on ₹{args.capital:,.0f}) | **`{cagr:.2f}%`** |",
            f"| Best day  | `{best_r.entry_date}` ({best_r.day_of_week}) `₹{fmt(best_r.net_pnl)}` |",
            f"| Worst day | `{worst_r.entry_date}` ({worst_r.day_of_week}) `₹{fmt(worst_r.net_pnl)}` |",
            "",
        ]

        # monthly table
        by_month: Dict[str, List[TradeResult]] = {}
        for r in grp:
            by_month.setdefault(r.entry_date[:7], []).append(r)
        lines += [
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

    # ── STRIKE OFFSET ANALYSIS ────────────────────────────────────────────
    lines += ["## Strike Offset Analysis (entry data — SL-independent)", ""]
    by_offset: Dict[int, List[RawTrade]] = {}
    for rt in raw_trades:
        by_offset.setdefault(rt.strike_offset, []).append(rt)
    lines += [
        "| Offset | Trades | Index breakdown |",
        "|--------|--------|-----------------|",
    ]
    for off in sorted(by_offset):
        grp   = by_offset[off]
        label = "ATM (0)" if off == 0 else f"±{off}"
        n_cnt = sum(1 for rt in grp if rt.index == "NIFTY")
        s_cnt = sum(1 for rt in grp if rt.index == "SENSEX")
        lines.append(f"| {label} | {len(grp)} | NIFTY: {n_cnt}  SENSEX: {s_cnt} |")
    lines += ["", "---", ""]

    # ── SKIP REASONS ──────────────────────────────────────────────────────
    lines += ["## Skip Reason Summary", ""]
    for reason, count in sorted(skip_by_reason.items(), key=lambda x: -x[1]):
        lines.append(f"- `{reason}`: {count}")
    lines += ["", "## First 30 Skipped Days", ""]
    for s in skipped[:30]:
        lines.append(
            f"- `{s.entry_date}` ({s.day_of_week}) [{s.index}]: "
            f"`{s.skip_reason}` — {s.remarks}"
        )

    lines += [
        "",
        "## Remarks",
        "",
        "- Strike search: ATM first, then ATM±1, ±2… until balance ratio ≥ threshold.",
        "- Both legs managed independently; one SL hit does not exit the other.",
        "- gap_sl  : option opens at/above SL → filled at candle open.",
        "- sl      : option high touches SL → filled at SL price.",
        "- SL monitoring uses 1-minute option candles.",
        "- All 9 SL scenarios share the same entry; only the exit logic differs.",
        "- CSV column sl_pct identifies the scenario for each row.",
        "- CAGR computed on notional capital via --capital arg.",
        "- Max drawdown = largest peak-to-trough drop in running cumulative equity.",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)

    print("Pass 1: collecting entries (balanced-strike search) …")
    raw_trades, skipped = collect_entries(args)
    print(f"  Found {len(raw_trades)} entries, {len(skipped)} skipped.")

    print(f"Pass 2: computing P&L for {len(SL_LEVELS)} SL levels …")
    results = compute_results(raw_trades)
    print(f"  Computed {len(results)} result rows ({len(raw_trades)} × {len(SL_LEVELS)} SLs).")

    write_daywise_csv(results, args.results_dir / DAYWISE_CSV)
    write_summary(results, raw_trades, skipped, args.results_dir / SUMMARY_MD, args)

    print(f"Daywise CSV : {args.results_dir / DAYWISE_CSV}")
    print(f"Summary     : {args.results_dir / SUMMARY_MD}")


if __name__ == "__main__":
    main()
