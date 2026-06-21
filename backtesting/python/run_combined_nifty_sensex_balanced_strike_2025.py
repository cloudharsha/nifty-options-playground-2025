#!/usr/bin/env python3
"""
Combined Intraday ATM Straddle — NIFTY Mon/Tue/Fri + SENSEX Wed/Thu
Sep 1 2025 → latest available data.

Same strategy as run_combined_nifty_sensex_expiry_incl_2025.py but with
balanced-strike search: if the exact ATM strike gives CE/PE price ratio
below 70%, search adjacent strikes (ATM±1, ATM±2, …) until a balanced
pair is found. This compensates for spot vs futures divergence.

Strike search order: ATM → ATM+N → ATM-N → ATM+2N → ATM-2N → ...
First strike where min(CE,PE)/max(CE,PE) >= balance_min_ratio is used.
If no balanced strike is found within max_search_strikes, the day is skipped.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
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
class TradeResult:
    index: str            # "NIFTY" | "SENSEX"
    entry_date: str
    day_of_week: str
    status: str           # "TRADED" | "SKIPPED"
    skip_reason: str
    expiry_date: str
    spot_entry_timestamp: str
    spot_entry_open: str
    atm_strike: str       # pure ATM based on spot rounding
    chosen_strike: str    # actual strike traded (may differ from atm_strike)
    strike_offset: str    # how many intervals away from ATM (0 = ATM itself)
    lot_size: str
    lots: str
    quantity: str
    ce_contract_file: str
    ce_entry_open: str
    ce_stop_price: str
    ce_exit_timestamp: str
    ce_exit_price: str
    ce_exit_reason: str
    ce_points_pnl: str
    ce_gross_pnl: str
    pe_contract_file: str
    pe_entry_open: str
    pe_stop_price: str
    pe_exit_timestamp: str
    pe_exit_price: str
    pe_exit_reason: str
    pe_points_pnl: str
    pe_gross_pnl: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


# ---------------------------------------------------------------------------
# CLI ARGS
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    p = argparse.ArgumentParser(
        description="Combined NIFTY+SENSEX intraday straddle with balanced-strike search."
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
    p.add_argument("--sl-pct", type=float, default=0.20)
    p.add_argument("--brokerage-per-order", type=float, default=25.0)
    p.add_argument("--slippage-per-order", type=float, default=0.5)
    p.add_argument("--balance-min-ratio", type=float, default=0.70,
                   help="Min allowed min(CE,PE)/max(CE,PE). Default 0.70 = 70%%.")
    p.add_argument("--max-search-strikes", type=int, default=5,
                   help="Max strikes to search away from ATM in each direction.")
    p.add_argument("--capital", type=float, default=500_000.0,
                   help="Notional capital (₹) for CAGR calculation.")
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
    """Return (lot_size, num_lots) targeting ~300 qty, expiry-date aware."""
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
    Search strikes outward from ATM for a balanced CE/PE pair.

    Search order: ATM, ATM+N, ATM-N, ATM+2N, ATM-2N, ...
    Returns (chosen_strike, offset_count, ce_data, pe_data, ce_row, pe_row)
    or None if no balanced strike found within max_search.
    """
    suffix = expiry_suffix(expiry_date)

    candidates: List[Tuple[int, int]] = [(atm, 0)]   # (strike, offset_count)
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
        ratio = min(ce_open, pe_open) / max(ce_open, pe_open)
        if ratio >= balance_min_ratio:
            return strike, offset, ce, pe, ce_row, pe_row

    return None


# ---------------------------------------------------------------------------
# TRADE LOGIC
# ---------------------------------------------------------------------------

def _leg_result(
    entry_open: float, exit_price: float, exit_reason: str,
    exit_ts: str, slippage: float, qty: int,
) -> Tuple[str, str, str, str, str]:
    points = entry_open - exit_price - 2 * slippage
    return exit_ts, fmt(exit_price), exit_reason, fmt(points), fmt(points * qty)


def resolve_leg(
    contract: ContractData,
    entry_open: float, entry_ts: str, exit_ts: str,
    sl_pct: float, slippage: float, qty: int,
) -> Tuple[str, str, str, str, str]:
    stop   = entry_open * (1.0 + sl_pct)
    window = sorted(ts for ts in contract.rows_by_timestamp if entry_ts <= ts <= exit_ts)
    for ts in window:
        row = contract.rows_by_timestamp[ts]
        if row.open_value >= stop:
            return _leg_result(entry_open, row.open_value, "gap_sl", ts, slippage, qty)
        if row.high_value >= stop:
            return _leg_result(entry_open, stop, "sl", ts, slippage, qty)
    exit_row = contract.rows_by_timestamp.get(exit_ts)
    if exit_row:
        return _leg_result(entry_open, exit_row.open_value, "day_close", exit_ts, slippage, qty)
    candidates = [ts for ts in contract.rows_by_timestamp if ts <= exit_ts]
    if candidates:
        last_ts = max(candidates)
        return _leg_result(entry_open, contract.rows_by_timestamp[last_ts].open_value,
                           "last_candle_before_exit", last_ts, slippage, qty)
    return _leg_result(entry_open, entry_open, "missing_exit_candle", exit_ts, slippage, qty)


def make_skip(
    index: str, entry_date: str, day_name: str, skip_reason: str, remarks: str = "",
    expiry_date: str = "", spot_ts: str = "", spot_open: str = "",
    atm: str = "", lot_size: str = "", lots: str = "", qty: str = "",
) -> TradeResult:
    return TradeResult(
        index=index, entry_date=entry_date, day_of_week=day_name,
        status="SKIPPED", skip_reason=skip_reason,
        expiry_date=expiry_date,
        spot_entry_timestamp=spot_ts, spot_entry_open=spot_open,
        atm_strike=atm, chosen_strike="", strike_offset="",
        lot_size=lot_size, lots=lots, quantity=qty,
        ce_contract_file="", ce_entry_open="", ce_stop_price="",
        ce_exit_timestamp="", ce_exit_price="", ce_exit_reason="",
        ce_points_pnl="0.00", ce_gross_pnl="0.00",
        pe_contract_file="", pe_entry_open="", pe_stop_price="",
        pe_exit_timestamp="", pe_exit_price="", pe_exit_reason="",
        pe_points_pnl="0.00", pe_gross_pnl="0.00",
        gross_pnl="0.00", brokerage="0.00", net_pnl="0.00", remarks=remarks,
    )


# ---------------------------------------------------------------------------
# MAIN BACKTEST LOOP
# ---------------------------------------------------------------------------

def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILE)

    nifty_days, nifty_spot  = load_spot_opens(args.nifty_spot_file, args.entry_time)
    _,          sensex_spot = load_spot_opens(args.sensex_spot_file, args.entry_time)

    nifty_expiries  = load_expiry_folders(args.nifty_options_dir)
    sensex_expiries = load_expiry_folders(args.sensex_options_dir)

    contract_cache: Dict[Path, Optional[ContractData]] = {}
    brokerage_per_straddle = args.brokerage_per_order * 4
    results: List[TradeResult] = []

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
                results.append(make_skip(index, entry_date, day_name, "missing_spot_entry",
                                         f"No {index} spot candle at {entry_ts}."))
                continue
            spot_val, spot_text = spot

            expiry_date = first_expiry_on_or_after(expiries, entry_date)
            if expiry_date is None:
                results.append(make_skip(index, entry_date, day_name, "no_expiry_found",
                                         "No suitable expiry found.",
                                         spot_ts=entry_ts, spot_open=spot_text))
                continue

            if index == "NIFTY":
                lot_size, num_lots = get_nifty_lot_config(expiry_date)
            else:
                lot_size, num_lots = 10, 10
            qty = lot_size * num_lots

            atm = round_to_n(spot_val, strike_interval)

            found = find_balanced_strike(
                options_dir, prefix, expiry_date, entry_ts,
                atm, strike_interval,
                args.max_search_strikes, args.balance_min_ratio,
                contract_cache,
            )

            if found is None:
                suffix = expiry_suffix(expiry_date)
                results.append(make_skip(
                    index, entry_date, day_name, "no_balanced_strike",
                    f"No strike within {args.max_search_strikes} of ATM={atm} passes "
                    f"{args.balance_min_ratio*100:.0f}% balance rule.",
                    expiry_date, entry_ts, spot_text,
                    str(atm), str(lot_size), str(num_lots), str(qty),
                ))
                logger.info("SKIPPED %s date=%s no_balanced_strike atm=%s", index, entry_date, atm)
                continue

            chosen_strike, offset, ce, pe, ce_row, pe_row = found
            suffix = expiry_suffix(expiry_date)
            ce_path = options_dir / expiry_date / f"{prefix}_{chosen_strike}_CE_{suffix}.csv"
            pe_path = options_dir / expiry_date / f"{prefix}_{chosen_strike}_PE_{suffix}.csv"

            ce_open = ce_row.open_value
            pe_open = pe_row.open_value

            ce_res = resolve_leg(ce, ce_open, entry_ts, exit_ts, args.sl_pct, args.slippage_per_order, qty)
            pe_res = resolve_leg(pe, pe_open, entry_ts, exit_ts, args.sl_pct, args.slippage_per_order, qty)
            ce_exit_ts, ce_exit_px, ce_exit_reason, ce_pts, ce_gross = ce_res
            pe_exit_ts, pe_exit_px, pe_exit_reason, pe_pts, pe_gross = pe_res

            gross_pnl = float(ce_gross) + float(pe_gross)
            net_pnl   = gross_pnl - brokerage_per_straddle

            offset_tag = f"+{offset}" if offset > 0 else str(offset)
            remarks = "" if offset == 0 else f"ATM={atm} shifted {offset_tag} strikes to {chosen_strike}"

            results.append(TradeResult(
                index=index, entry_date=entry_date, day_of_week=day_name,
                status="TRADED", skip_reason="",
                expiry_date=expiry_date,
                spot_entry_timestamp=entry_ts, spot_entry_open=spot_text,
                atm_strike=str(atm), chosen_strike=str(chosen_strike), strike_offset=offset_tag,
                lot_size=str(lot_size), lots=str(num_lots), quantity=str(qty),
                ce_contract_file=ce_path.name,
                ce_entry_open=fmt(ce_open), ce_stop_price=fmt(ce_open * (1 + args.sl_pct)),
                ce_exit_timestamp=ce_exit_ts, ce_exit_price=ce_exit_px, ce_exit_reason=ce_exit_reason,
                ce_points_pnl=ce_pts, ce_gross_pnl=ce_gross,
                pe_contract_file=pe_path.name,
                pe_entry_open=fmt(pe_open), pe_stop_price=fmt(pe_open * (1 + args.sl_pct)),
                pe_exit_timestamp=pe_exit_ts, pe_exit_price=pe_exit_px, pe_exit_reason=pe_exit_reason,
                pe_points_pnl=pe_pts, pe_gross_pnl=pe_gross,
                gross_pnl=fmt(gross_pnl), brokerage=fmt(brokerage_per_straddle), net_pnl=fmt(net_pnl),
                remarks=remarks,
            ))

            sl_hits = []
            if "sl" in ce_exit_reason: sl_hits.append("CE_SL")
            if "sl" in pe_exit_reason: sl_hits.append("PE_SL")
            logger.info(
                "TRADED %s date=%s day=%s expiry=%s atm=%s chosen=%s offset=%s qty=%s "
                "ce=%.2f pe=%.2f ratio=%.2f sl=[%s] net=%.2f",
                index, entry_date, day_name, expiry_date, atm, chosen_strike, offset_tag, qty,
                ce_open, pe_open, min(ce_open, pe_open) / max(ce_open, pe_open),
                ",".join(sl_hits) if sl_hits else "none", net_pnl,
            )

    except Exception:
        logger.exception("ERROR unexpected failure")
        raise
    finally:
        traded_n  = sum(1 for r in results if r.status == "TRADED")
        skipped_n = sum(1 for r in results if r.status == "SKIPPED")
        logger.info("COMPLETED traded=%s skipped=%s total=%s", traded_n, skipped_n, len(results))
        close_logger(logger)

    return results


# ---------------------------------------------------------------------------
# OUTPUT: DAYWISE CSV
# ---------------------------------------------------------------------------

def write_daywise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "index", "entry_date", "day_of_week", "status", "skip_reason",
        "expiry_date", "spot_entry_timestamp", "spot_entry_open",
        "atm_strike", "chosen_strike", "strike_offset",
        "lot_size", "lots", "quantity",
        "ce_contract_file", "ce_entry_open", "ce_stop_price",
        "ce_exit_timestamp", "ce_exit_price", "ce_exit_reason",
        "ce_points_pnl", "ce_gross_pnl",
        "pe_contract_file", "pe_entry_open", "pe_stop_price",
        "pe_exit_timestamp", "pe_exit_price", "pe_exit_reason",
        "pe_points_pnl", "pe_gross_pnl",
        "gross_pnl", "brokerage", "net_pnl", "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r.__dict__)


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


# ---------------------------------------------------------------------------
# SUMMARY HELPERS
# ---------------------------------------------------------------------------

def _overall_block(label: str, traded: List[TradeResult], capital: float) -> List[str]:
    if not traded:
        return [f"### {label}", "", "_No trades._", ""]
    net_total   = sum(float(r.net_pnl)   for r in traded)
    gross_total = sum(float(r.gross_pnl) for r in traded)
    brok_total  = sum(float(r.brokerage) for r in traded)
    max_dd, max_cum = compute_equity_curve([float(r.net_pnl) for r in traded])
    wins    = sum(1 for r in traded if float(r.net_pnl) > 0)
    losses  = sum(1 for r in traded if float(r.net_pnl) < 0)
    ce_sl   = sum(1 for r in traded if "sl" in r.ce_exit_reason)
    pe_sl   = sum(1 for r in traded if "sl" in r.pe_exit_reason)
    both_sl = sum(1 for r in traded if "sl" in r.ce_exit_reason and "sl" in r.pe_exit_reason)
    no_sl   = sum(1 for r in traded if "sl" not in r.ce_exit_reason and "sl" not in r.pe_exit_reason)
    best    = max(traded, key=lambda r: float(r.net_pnl))
    worst   = min(traded, key=lambda r: float(r.net_pnl))
    cagr    = compute_cagr(net_total, capital, traded[0].entry_date, traded[-1].entry_date) * 100.0

    # Strike offset stats
    at_atm    = sum(1 for r in traded if r.strike_offset == "0")
    off_atm   = sum(1 for r in traded if r.strike_offset != "0")

    return [
        f"### {label}",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Traded days | `{len(traded)}` |",
        f"| Winning days | `{wins}` |",
        f"| Losing days | `{losses}` |",
        f"| Win rate | `{wins / len(traded) * 100:.1f}%` |",
        f"| Days CE SL hit | `{ce_sl}` |",
        f"| Days PE SL hit | `{pe_sl}` |",
        f"| Days both SL hit | `{both_sl}` |",
        f"| Days neither SL hit | `{no_sl}` |",
        f"| Traded at ATM | `{at_atm}` |",
        f"| Traded at adjusted strike | `{off_atm}` |",
        f"| Gross P/L | `₹{fmt(gross_total)}` |",
        f"| Total Brokerage | `₹{fmt(brok_total)}` |",
        f"| **Net P/L** | **`₹{fmt(net_total)}`** |",
        f"| Max cumulative profit | `₹{fmt(max_cum)}` |",
        f"| Max drawdown | `₹{fmt(max_dd)}` |",
        f"| **CAGR** (on ₹{capital:,.0f} capital) | **`{cagr:.2f}%`** |",
        f"| Best day | `{best.entry_date}` ({best.day_of_week}) `₹{best.net_pnl}` |",
        f"| Worst day | `{worst.entry_date}` ({worst.day_of_week}) `₹{worst.net_pnl}` |",
        "",
    ]


def _dow_table(traded: List[TradeResult]) -> List[str]:
    by_day: Dict[str, List[TradeResult]] = {}
    for r in traded:
        by_day.setdefault(r.day_of_week, []).append(r)
    lines = [
        "| Day | Index | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |",
        "|-----|-------|--------|-----|------|-------|-------|---------------|-------------|",
    ]
    for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        dr = by_day.get(d, [])
        if not dr:
            idx = "NIFTY" if d in ("Monday", "Tuesday", "Friday") else "SENSEX"
            lines.append(f"| {d} | {idx} | 0 | — | — | — | — | — | — |")
            continue
        idx     = dr[0].index
        d_net   = sum(float(r.net_pnl) for r in dr)
        d_win   = sum(1 for r in dr if float(r.net_pnl) > 0)
        d_loss  = sum(1 for r in dr if float(r.net_pnl) < 0)
        d_ce_sl = sum(1 for r in dr if "sl" in r.ce_exit_reason)
        d_pe_sl = sum(1 for r in dr if "sl" in r.pe_exit_reason)
        lines.append(
            f"| {d} | {idx} | {len(dr)} | {d_win} | {d_loss} | {d_ce_sl} | {d_pe_sl} "
            f"| `₹{fmt(d_net)}` | `₹{fmt(d_net / len(dr))}` |"
        )
    return lines


def _dow_detail(traded: List[TradeResult]) -> List[str]:
    by_day: Dict[str, List[TradeResult]] = {}
    for r in traded:
        by_day.setdefault(r.day_of_week, []).append(r)
    lines: List[str] = []
    for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        dr = by_day.get(d, [])
        if not dr:
            lines += [f"#### {d}: no trades", ""]
            continue
        d_net   = sum(float(r.net_pnl)   for r in dr)
        d_gross = sum(float(r.gross_pnl) for r in dr)
        d_brok  = sum(float(r.brokerage) for r in dr)
        d_win   = sum(1 for r in dr if float(r.net_pnl) > 0)
        d_loss  = sum(1 for r in dr if float(r.net_pnl) < 0)
        d_ce_sl = sum(1 for r in dr if "sl" in r.ce_exit_reason)
        d_pe_sl = sum(1 for r in dr if "sl" in r.pe_exit_reason)
        best    = max(dr, key=lambda r: float(r.net_pnl))
        worst   = min(dr, key=lambda r: float(r.net_pnl))
        at_atm  = sum(1 for r in dr if r.strike_offset == "0")
        lines += [
            f"#### {d} ({dr[0].index})",
            f"- Trades: `{len(dr)}`  Win: `{d_win}`  Loss: `{d_loss}`  "
            f"CE-SL: `{d_ce_sl}`  PE-SL: `{d_pe_sl}`  At-ATM: `{at_atm}`",
            f"- Total Net P/L: `₹{fmt(d_net)}`  **Avg Net/Day: `₹{fmt(d_net / len(dr))}`**",
            f"- Gross: `₹{fmt(d_gross)}`  Brokerage: `₹{fmt(d_brok)}`",
            f"- Best: `{best.entry_date}` `₹{best.net_pnl}`  "
            f"Worst: `{worst.entry_date}` `₹{worst.net_pnl}`",
            "",
        ]
    return lines


def _monthly_table(traded: List[TradeResult]) -> List[str]:
    by_month: Dict[str, List[TradeResult]] = {}
    for r in traded:
        by_month.setdefault(r.entry_date[:7], []).append(r)
    lines = [
        "| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day | Cumulative P/L |",
        "|-------|--------|-----|------|---------------|-------------|----------------|",
    ]
    running = 0.0
    for month in sorted(by_month):
        mr    = by_month[month]
        m_net = sum(float(r.net_pnl) for r in mr)
        m_win = sum(1 for r in mr if float(r.net_pnl) > 0)
        m_los = sum(1 for r in mr if float(r.net_pnl) < 0)
        running += m_net
        lines.append(
            f"| {month} | {len(mr)} | {m_win} | {m_los} "
            f"| `₹{fmt(m_net)}` | `₹{fmt(m_net / len(mr))}` | `₹{fmt(running)}` |"
        )
    return lines


def _yearly_table(traded: List[TradeResult], capital: float) -> List[str]:
    by_year: Dict[str, List[TradeResult]] = {}
    for r in traded:
        by_year.setdefault(r.entry_date[:4], []).append(r)
    lines = [
        "| Year | Trades | Win | Loss | Total Net P/L | Avg Net/Day | CAGR |",
        "|------|--------|-----|------|---------------|-------------|------|",
    ]
    for year in sorted(by_year):
        yr    = by_year[year]
        y_net = sum(float(r.net_pnl) for r in yr)
        y_win = sum(1 for r in yr if float(r.net_pnl) > 0)
        y_los = sum(1 for r in yr if float(r.net_pnl) < 0)
        y_cagr = compute_cagr(y_net, capital, yr[0].entry_date, yr[-1].entry_date) * 100.0
        lines.append(
            f"| {year} | {len(yr)} | {y_win} | {y_los} "
            f"| `₹{fmt(y_net)}` | `₹{fmt(y_net / len(yr))}` | `{y_cagr:.1f}%` |"
        )
    return lines


def _strike_offset_table(traded: List[TradeResult]) -> List[str]:
    """Show how often we had to move away from ATM, and P&L per offset level."""
    by_offset: Dict[int, List[TradeResult]] = {}
    for r in traded:
        off = int(r.strike_offset.replace("+", ""))
        by_offset.setdefault(off, []).append(r)
    lines = [
        "| Offset (strikes from ATM) | Trades | Win | Loss | Total Net P/L | Avg Net/Day |",
        "|--------------------------|--------|-----|------|---------------|-------------|",
    ]
    for off in sorted(by_offset):
        gr    = by_offset[off]
        g_net = sum(float(r.net_pnl) for r in gr)
        g_win = sum(1 for r in gr if float(r.net_pnl) > 0)
        g_los = sum(1 for r in gr if float(r.net_pnl) < 0)
        label = f"ATM (0)" if off == 0 else f"±{off}"
        lines.append(
            f"| {label} | {len(gr)} | {g_win} | {g_los} "
            f"| `₹{fmt(g_net)}` | `₹{fmt(g_net / len(gr))}` |"
        )
    return lines


# ---------------------------------------------------------------------------
# OUTPUT: SUMMARY MARKDOWN
# ---------------------------------------------------------------------------

def write_summary(results: List[TradeResult], output_path: Path, args: argparse.Namespace) -> None:
    traded  = [r for r in results if r.status == "TRADED"]
    skipped = [r for r in results if r.status == "SKIPPED"]

    nifty_traded  = [r for r in traded  if r.index == "NIFTY"]
    sensex_traded = [r for r in traded  if r.index == "SENSEX"]

    skip_by_reason: Dict[str, int] = {}
    for r in skipped:
        key = f"{r.index}:{r.skip_reason}"
        skip_by_reason[key] = skip_by_reason.get(key, 0) + 1

    lines = [
        "# Combined NIFTY + SENSEX — Balanced Strike Search (Sep 2025+)",
        "",
        "## Strategy Details",
        "",
        f"- Period: `{START_DATE}` → latest available data",
        f"- Entry: `{args.entry_time}` | Exit: `{args.exit_time}`",
        f"- Stop loss: `{args.sl_pct * 100:.0f}%` above entry price, **independent per leg**",
        "- Expiry: current-week expiry, **traded even on expiry day itself** (no roll)",
        "- Balance filter: **disabled** (replaced by strike search)",
        f"- **Strike search**: start at ATM, try ±1, ±2 … ±{args.max_search_strikes} strikes",
        f"  until `min(CE,PE)/max(CE,PE) >= {args.balance_min_ratio*100:.0f}%`.",
        "  If no balanced strike found → day skipped.",
        "- **Monday / Tuesday / Friday** → NIFTY weekly options (~300 qty, strike rounding 50)",
        "- **Wednesday / Thursday**       → SENSEX weekly options (~100 qty, strike rounding 100)",
        "- NIFTY lot sizing (expiry-aware):",
        "  - Until 2025-12-30 : 75 × 4 = **300**",
        "  - 2026+ expiry      : 65 × 5 = **325**",
        "- SENSEX lot sizing: 10 × 10 = **100** (fixed)",
        f"- Slippage: {fmt(args.slippage_per_order)} pt/order (2× per leg)",
        f"- Brokerage: ₹{fmt(args.brokerage_per_order)}/order → ₹{fmt(args.brokerage_per_order * 4)}/straddle",
        f"- Notional capital for CAGR: ₹{args.capital:,.0f}",
        "",
        "---",
        "",
        "## Overall Combined Results",
        "",
    ]
    lines += _overall_block("Combined (NIFTY + SENSEX)", traded, args.capital)

    lines += ["## Per-Index Results", ""]
    lines += _overall_block("NIFTY (Mon / Tue / Fri)", nifty_traded, args.capital)
    lines += _overall_block("SENSEX (Wed / Thu)", sensex_traded, args.capital)

    lines += [
        "---",
        "",
        "## Strike Offset Analysis",
        "",
        "How often the strategy moved away from ATM to find a balanced pair:",
        "",
    ]
    lines += _strike_offset_table(traded)

    lines += [
        "",
        "---",
        "",
        "## Results by Day of Week",
        "",
    ]
    lines += _dow_table(traded)
    lines += ["", "### Day-of-Week Detail", ""]
    lines += _dow_detail(traded)

    lines += ["---", "", "## Monthly Summary (Combined)", ""]
    lines += _monthly_table(traded)

    lines += ["", "## Yearly Summary (Combined)", ""]
    lines += _yearly_table(traded, args.capital)

    if nifty_traded:
        lines += ["", "## Monthly Summary — NIFTY only", ""]
        lines += _monthly_table(nifty_traded)

    if sensex_traded:
        lines += ["", "## Monthly Summary — SENSEX only", ""]
        lines += _monthly_table(sensex_traded)

    lines += ["", "---", "", "## Skip Reason Summary", ""]
    for reason, count in sorted(skip_by_reason.items(), key=lambda x: -x[1]):
        lines.append(f"- `{reason}`: {count}")

    lines += ["", "## First 30 Skipped Days", ""]
    nifty_skipped  = [r for r in skipped if r.index == "NIFTY"]
    sensex_skipped = [r for r in skipped if r.index == "SENSEX"]
    for r in (nifty_skipped + sensex_skipped)[:30]:
        lines.append(f"- `{r.entry_date}` ({r.day_of_week}) [{r.index}]: `{r.skip_reason}` — {r.remarks}")

    lines += [
        "",
        "## Remarks",
        "",
        "- Strike search: ATM first, then ATM±1, ATM±2, … until balance ratio ≥ threshold.",
        "- Both legs managed independently; one SL hit does not exit the other.",
        "- gap_sl  : option opens at/above SL → filled at candle open.",
        "- sl      : option high touches SL price → filled at SL.",
        "- SL monitoring uses 1-minute option candles.",
        "- chosen_strike and strike_offset columns in the CSV show how far from ATM we went.",
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
    results = run_backtest(args)
    write_daywise_csv(results, args.results_dir / DAYWISE_CSV)
    write_summary(results, args.results_dir / SUMMARY_MD, args)
    traded  = sum(1 for r in results if r.status == "TRADED")
    skipped = sum(1 for r in results if r.status == "SKIPPED")
    print(f"Done. Traded={traded} Skipped={skipped} Total={len(results)}")
    print(f"Daywise CSV : {args.results_dir / DAYWISE_CSV}")
    print(f"Summary     : {args.results_dir / SUMMARY_MD}")


if __name__ == "__main__":
    main()
