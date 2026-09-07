#!/usr/bin/env python3
"""Intraday ATM Straddle — 20% independent SL per leg — NIFTY Monthly Options 2020–2026."""
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

IST_SUFFIX = "+05:30"
BASE_FILENAME = "intraday_atm_straddle_20pct_sl_nifty_monthly_2020_2026"
DAYWISE_FILENAME = f"{BASE_FILENAME}_daywise.csv"
SUMMARY_FILENAME = f"{BASE_FILENAME}_summary.md"
LOG_FILENAME = f"{BASE_FILENAME}.log"
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


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
    entry_date: str
    day_of_week: str
    status: str
    skip_reason: str
    expiry_date: str
    expiry_type: str
    spot_entry_timestamp: str
    spot_entry_open: str
    atm_strike: str
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


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    p = argparse.ArgumentParser(
        description="Backtest intraday ATM straddle with 20% independent SL on monthly options — NIFTY 2020–2026."
    )
    p.add_argument("--spot-file", type=Path,
                   default=repo_root / "nifty" / "NIFTY50_INDEX_5m_last_7y.csv")
    p.add_argument("--options-dir", type=Path,
                   default=repo_root / "NiftyOptions_2020_2026" / "Options")
    p.add_argument("--results-dir", type=Path,
                   default=repo_root / "backtesting" / "results")
    p.add_argument("--entry-time", default="09:20")
    p.add_argument("--exit-time", default="15:20")
    p.add_argument("--sl-pct", type=float, default=0.20)
    p.add_argument("--balance-max-diff", type=float, default=0.20)
    p.add_argument("--brokerage-per-order", type=float, default=25.0)
    p.add_argument("--slippage-per-order", type=float, default=0.5)
    return p.parse_args()


def fmt(v: float) -> str:
    return f"{v:.2f}"


def build_ts(day: str, time_text: str) -> str:
    h, m = time_text.split(":")
    return f"{day}T{h}:{m}:00{IST_SUFFIX}"


def round_to_50(price: float) -> int:
    rem = price % 50
    base = int(price - rem)
    return base if rem < 25 else base + 50


def expiry_suffix(expiry_date: str) -> str:
    return datetime.datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%d_%b_%y").upper()


def get_lot_config(expiry_date: str) -> Tuple[int, int]:
    """(lot_size, num_lots) targeting ~300 quantity, expiry-aware."""
    d = datetime.date.fromisoformat(expiry_date)
    if d <= datetime.date(2021, 10, 6):
        return 75, 4
    if d <= datetime.date(2024, 4, 25):
        return 50, 6
    if d <= datetime.date(2024, 11, 21):
        return 25, 12
    if d <= datetime.date(2025, 12, 30):
        return 75, 4
    return 65, 5


def get_monthly_expiries(all_expiries: List[str]) -> List[str]:
    """Returns the last expiry of each calendar month (= monthly contract)."""
    by_month: Dict[str, List[str]] = {}
    for e in all_expiries:
        by_month.setdefault(e[:7], []).append(e)
    return [max(dates) for dates in sorted(by_month.values())]


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


def load_spot_data(
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
            rows[ts] = PriceRow(ts, float(row["open"]), row["open"], float(row["high"]))
    result = ContractData(path=path, rows_by_timestamp=rows)
    cache[path] = result
    return result


def next_expiry_after(expiries: List[str], date: str) -> Optional[str]:
    for e in expiries:
        if e > date:
            return e
    return None


def first_expiry_on_or_after(expiries: List[str], date: str) -> Optional[str]:
    for e in expiries:
        if e >= date:
            return e
    return None


def _leg_result(
    entry_open: float, exit_price: float, exit_reason: str, exit_ts: str,
    slippage: float, qty: int,
) -> Tuple[str, str, str, str, str]:
    points = entry_open - exit_price - 2 * slippage
    return exit_ts, fmt(exit_price), exit_reason, fmt(points), fmt(points * qty)


def resolve_leg(
    contract: ContractData, entry_open: float,
    entry_ts: str, exit_ts: str, sl_pct: float, slippage: float, qty: int,
) -> Tuple[str, str, str, str, str]:
    stop = entry_open * (1.0 + sl_pct)
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
    entry_date: str, day_name: str, skip_reason: str, remarks: str = "",
    expiry_date: str = "", expiry_type: str = "",
    spot_ts: str = "", spot_open: str = "",
    atm: str = "", lot_size: str = "", lots: str = "", qty: str = "",
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date, day_of_week=day_name,
        status="SKIPPED", skip_reason=skip_reason,
        expiry_date=expiry_date, expiry_type=expiry_type,
        spot_entry_timestamp=spot_ts, spot_entry_open=spot_open,
        atm_strike=atm, lot_size=lot_size, lots=lots, quantity=qty,
        ce_contract_file="", ce_entry_open="", ce_stop_price="",
        ce_exit_timestamp="", ce_exit_price="", ce_exit_reason="",
        ce_points_pnl="0.00", ce_gross_pnl="0.00",
        pe_contract_file="", pe_entry_open="", pe_stop_price="",
        pe_exit_timestamp="", pe_exit_price="", pe_exit_reason="",
        pe_points_pnl="0.00", pe_gross_pnl="0.00",
        gross_pnl="0.00", brokerage="0.00", net_pnl="0.00", remarks=remarks,
    )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, spot_open_by_day = load_spot_data(args.spot_file, args.entry_time)

    all_expiries = sorted(p.name for p in args.options_dir.iterdir() if p.is_dir())
    monthly_expiries = get_monthly_expiries(all_expiries)
    monthly_expiry_set = set(monthly_expiries)

    contract_cache: Dict[Path, Optional[ContractData]] = {}
    brokerage_per_straddle = args.brokerage_per_order * 4
    results: List[TradeResult] = []

    try:
        for entry_date in trading_days:
            wd = datetime.date.fromisoformat(entry_date).weekday()
            if wd >= 5:
                continue
            day_name = WEEKDAY_NAMES[wd]
            entry_ts = build_ts(entry_date, args.entry_time)
            exit_ts = build_ts(entry_date, args.exit_time)

            spot = spot_open_by_day.get(entry_date)
            if not spot:
                results.append(make_skip(entry_date, day_name, "missing_spot_entry",
                                         f"No spot candle at {entry_ts}."))
                continue

            spot_val, spot_text = spot

            # Monthly expiry selection: if today is a monthly expiry day, use next month
            if entry_date in monthly_expiry_set:
                expiry_date = next_expiry_after(monthly_expiries, entry_date)
                expiry_type = "next_month"
            else:
                expiry_date = first_expiry_on_or_after(monthly_expiries, entry_date)
                expiry_type = "current_month"

            if expiry_date is None:
                results.append(make_skip(entry_date, day_name, "no_expiry_found",
                                         "No monthly expiry found.",
                                         expiry_type=expiry_type,
                                         spot_ts=entry_ts, spot_open=spot_text))
                continue

            lot_size, num_lots = get_lot_config(expiry_date)
            qty = lot_size * num_lots
            atm = round_to_50(spot_val)
            suffix = expiry_suffix(expiry_date)
            ce_path = args.options_dir / expiry_date / f"NIFTY_{atm}_CE_{suffix}.csv"
            pe_path = args.options_dir / expiry_date / f"NIFTY_{atm}_PE_{suffix}.csv"

            ce = load_contract(ce_path, contract_cache)
            pe = load_contract(pe_path, contract_cache)

            missing = [p.name for p, c in [(ce_path, ce), (pe_path, pe)] if c is None]
            if missing:
                results.append(make_skip(entry_date, day_name, "missing_contract_file",
                                         f"Missing: {', '.join(missing)}",
                                         expiry_date, expiry_type, entry_ts, spot_text,
                                         str(atm), str(lot_size), str(num_lots), str(qty)))
                logger.info("SKIPPED date=%s missing_contract atm=%s expiry=%s", entry_date, atm, expiry_date)
                continue

            ce_row = ce.rows_by_timestamp.get(entry_ts)
            pe_row = pe.rows_by_timestamp.get(entry_ts)
            missing_ts = []
            if ce_row is None:
                missing_ts.append(ce_path.name)
            if pe_row is None:
                missing_ts.append(pe_path.name)
            if missing_ts:
                results.append(make_skip(entry_date, day_name, "missing_entry_candle",
                                         f"No {entry_ts} candle in: {', '.join(missing_ts)}",
                                         expiry_date, expiry_type, entry_ts, spot_text,
                                         str(atm), str(lot_size), str(num_lots), str(qty)))
                logger.info("SKIPPED date=%s missing_entry_candle atm=%s expiry=%s", entry_date, atm, expiry_date)
                continue

            ce_open = ce_row.open_value
            pe_open = pe_row.open_value

            if ce_open <= 0 or pe_open <= 0 or \
               min(ce_open, pe_open) / max(ce_open, pe_open) < (1.0 - args.balance_max_diff):
                results.append(make_skip(entry_date, day_name, "balance_check_failed",
                                         f"CE={fmt(ce_open)} PE={fmt(pe_open)} diff>{args.balance_max_diff*100:.0f}%",
                                         expiry_date, expiry_type, entry_ts, spot_text,
                                         str(atm), str(lot_size), str(num_lots), str(qty)))
                logger.info("SKIPPED date=%s balance_failed ce=%.2f pe=%.2f", entry_date, ce_open, pe_open)
                continue

            ce_exit_ts, ce_exit_px, ce_exit_reason, ce_pts, ce_gross = resolve_leg(
                ce, ce_open, entry_ts, exit_ts, args.sl_pct, args.slippage_per_order, qty)
            pe_exit_ts, pe_exit_px, pe_exit_reason, pe_pts, pe_gross = resolve_leg(
                pe, pe_open, entry_ts, exit_ts, args.sl_pct, args.slippage_per_order, qty)

            gross_pnl = float(ce_gross) + float(pe_gross)
            net_pnl = gross_pnl - brokerage_per_straddle

            results.append(TradeResult(
                entry_date=entry_date, day_of_week=day_name,
                status="TRADED", skip_reason="",
                expiry_date=expiry_date, expiry_type=expiry_type,
                spot_entry_timestamp=entry_ts, spot_entry_open=spot_text,
                atm_strike=str(atm), lot_size=str(lot_size), lots=str(num_lots), quantity=str(qty),
                ce_contract_file=ce_path.name,
                ce_entry_open=fmt(ce_open), ce_stop_price=fmt(ce_open * (1 + args.sl_pct)),
                ce_exit_timestamp=ce_exit_ts, ce_exit_price=ce_exit_px, ce_exit_reason=ce_exit_reason,
                ce_points_pnl=ce_pts, ce_gross_pnl=ce_gross,
                pe_contract_file=pe_path.name,
                pe_entry_open=fmt(pe_open), pe_stop_price=fmt(pe_open * (1 + args.sl_pct)),
                pe_exit_timestamp=pe_exit_ts, pe_exit_price=pe_exit_px, pe_exit_reason=pe_exit_reason,
                pe_points_pnl=pe_pts, pe_gross_pnl=pe_gross,
                gross_pnl=fmt(gross_pnl), brokerage=fmt(brokerage_per_straddle), net_pnl=fmt(net_pnl),
                remarks="",
            ))

            sl_hits = []
            if "sl" in ce_exit_reason:
                sl_hits.append("CE_SL")
            if "sl" in pe_exit_reason:
                sl_hits.append("PE_SL")
            logger.info(
                "TRADED date=%s day=%s expiry=%s atm=%s qty=%s ce=%.2f pe=%.2f sl=[%s] net=%.2f",
                entry_date, day_name, expiry_date, atm, qty,
                ce_open, pe_open, ",".join(sl_hits) if sl_hits else "none", net_pnl,
            )

    except Exception:
        logger.exception("ERROR unexpected failure")
        raise
    finally:
        traded_n = sum(1 for r in results if r.status == "TRADED")
        skipped_n = sum(1 for r in results if r.status == "SKIPPED")
        logger.info("COMPLETED traded=%s skipped=%s total=%s", traded_n, skipped_n, len(results))
        close_logger(logger)

    return results


def write_daywise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date", "day_of_week", "status", "skip_reason",
        "expiry_date", "expiry_type",
        "spot_entry_timestamp", "spot_entry_open", "atm_strike",
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


def compute_equity_stats(net_pnls: List[float]) -> Tuple[float, float]:
    cumulative = peak = max_dd = peak_profit = 0.0
    for pnl in net_pnls:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
        if cumulative > peak_profit:
            peak_profit = cumulative
    return max_dd, peak_profit


def write_summary(results: List[TradeResult], output_path: Path, args: argparse.Namespace) -> None:
    traded = [r for r in results if r.status == "TRADED"]
    skipped = [r for r in results if r.status == "SKIPPED"]
    net_total = sum(float(r.net_pnl) for r in traded)
    gross_total = sum(float(r.gross_pnl) for r in traded)
    brok_total = sum(float(r.brokerage) for r in traded)
    max_dd, peak_profit = compute_equity_stats([float(r.net_pnl) for r in traded])
    wins = sum(1 for r in traded if float(r.net_pnl) > 0)
    losses = sum(1 for r in traded if float(r.net_pnl) < 0)
    ce_sl = sum(1 for r in traded if "sl" in r.ce_exit_reason)
    pe_sl = sum(1 for r in traded if "sl" in r.pe_exit_reason)
    both_sl = sum(1 for r in traded if "sl" in r.ce_exit_reason and "sl" in r.pe_exit_reason)
    neither_sl = sum(1 for r in traded if "sl" not in r.ce_exit_reason and "sl" not in r.pe_exit_reason)
    balance_fails = sum(1 for r in skipped if r.skip_reason == "balance_check_failed")
    max_profit_r = max(traded, key=lambda r: float(r.net_pnl), default=None)
    max_loss_r = min(traded, key=lambda r: float(r.net_pnl), default=None)

    by_day: Dict[str, List[TradeResult]] = {}
    for r in traded:
        by_day.setdefault(r.day_of_week, []).append(r)

    skip_by_reason: Dict[str, int] = {}
    for r in skipped:
        skip_by_reason[r.skip_reason] = skip_by_reason.get(r.skip_reason, 0) + 1

    lines = [
        "# NIFTY Intraday ATM Straddle — 20% Independent SL — Monthly Options (2020–2026)",
        "",
        "## Strategy Details",
        "",
        f"- Entry: `{args.entry_time}` — sell ATM CE + PE (nearest 50 to spot open)",
        f"- Exit: `{args.exit_time}` — day close if SL not hit",
        f"- Stop loss: `{args.sl_pct * 100:.0f}%` above entry price, **independent per leg**",
        f"- Balance rule: skip if |CE − PE| / max(CE, PE) > {args.balance_max_diff * 100:.0f}%",
        "- Contract: **monthly expiry** (last expiry of each calendar month)",
        "- Expiry selection: on monthly expiry day → next month; otherwise current month",
        "- Lot sizing (expiry-aware, targeting ~300 quantity):",
        "  - Until 2021-10-06 expiry  : 75 × 4 = **300**",
        "  - 2021-10-07 – 2024-04-25  : 50 × 6 = **300**",
        "  - 2024-04-26 – 2024-11-21  : 25 × 12 = **300**",
        "  - 2024-11-22 – 2025-12-30  : 75 × 4 = **300**",
        "  - 2026+ expiry              : 65 × 5 = **325**",
        f"- Slippage: {fmt(args.slippage_per_order)} pt/order",
        f"- Brokerage: ₹{fmt(args.brokerage_per_order)}/order → ₹{fmt(args.brokerage_per_order * 4)}/straddle",
        f"- Spot data: `NIFTY50_INDEX_5m_last_7y.csv`",
        f"- Options data: `NiftyOptions_2020_2026/Options`",
        "",
        "## Overall Results",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Traded days | `{len(traded)}` |",
        f"| Skipped days | `{len(skipped)}` |",
        f"| Winning days | `{wins}` |",
        f"| Losing days | `{losses}` |",
        (f"| Win rate | `{wins / len(traded) * 100:.1f}%` |" if traded else "| Win rate | N/A |"),
        f"| Days CE SL hit | `{ce_sl}` |",
        f"| Days PE SL hit | `{pe_sl}` |",
        f"| Days both SL hit | `{both_sl}` |",
        f"| Days neither SL hit | `{neither_sl}` |",
        f"| Gross P/L | `₹{fmt(gross_total)}` |",
        f"| Total Brokerage | `₹{fmt(brok_total)}` |",
        f"| **Net P/L** | **`₹{fmt(net_total)}`** |",
        f"| Peak cumulative profit | `₹{fmt(peak_profit)}` |",
        f"| Max drawdown | `₹{fmt(max_dd)}` |",
        (f"| Best day | `{max_profit_r.entry_date}` ({max_profit_r.day_of_week}) `₹{max_profit_r.net_pnl}` qty={max_profit_r.quantity} |"
         if max_profit_r else "| Best day | N/A |"),
        (f"| Worst day | `{max_loss_r.entry_date}` ({max_loss_r.day_of_week}) `₹{max_loss_r.net_pnl}` qty={max_loss_r.quantity} |"
         if max_loss_r else "| Worst day | N/A |"),
        "",
        "## Results by Day of Week",
        "",
        "| Day | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |",
        "|-----|--------|-----|------|-------|-------|---------------|-------------|",
    ]

    for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        dr = by_day.get(d, [])
        if not dr:
            lines.append(f"| {d} | 0 | — | — | — | — | — | — |")
            continue
        d_net = sum(float(r.net_pnl) for r in dr)
        d_win = sum(1 for r in dr if float(r.net_pnl) > 0)
        d_loss = sum(1 for r in dr if float(r.net_pnl) < 0)
        d_ce_sl = sum(1 for r in dr if "sl" in r.ce_exit_reason)
        d_pe_sl = sum(1 for r in dr if "sl" in r.pe_exit_reason)
        lines.append(
            f"| {d} | {len(dr)} | {d_win} | {d_loss} | {d_ce_sl} | {d_pe_sl} "
            f"| `₹{fmt(d_net)}` | `₹{fmt(d_net / len(dr))}` |"
        )

    lines += ["", "### Day-of-Week Detail", ""]
    for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        dr = by_day.get(d, [])
        if not dr:
            lines += [f"#### {d}: no trades", ""]
            continue
        d_net = sum(float(r.net_pnl) for r in dr)
        d_gross = sum(float(r.gross_pnl) for r in dr)
        d_brok = sum(float(r.brokerage) for r in dr)
        d_win = sum(1 for r in dr if float(r.net_pnl) > 0)
        d_loss = sum(1 for r in dr if float(r.net_pnl) < 0)
        d_ce_sl = sum(1 for r in dr if "sl" in r.ce_exit_reason)
        d_pe_sl = sum(1 for r in dr if "sl" in r.pe_exit_reason)
        best = max(dr, key=lambda r: float(r.net_pnl))
        worst = min(dr, key=lambda r: float(r.net_pnl))
        lines += [
            f"#### {d}",
            f"- Trades: `{len(dr)}`  Win: `{d_win}`  Loss: `{d_loss}`  CE-SL: `{d_ce_sl}`  PE-SL: `{d_pe_sl}`",
            f"- Total Net P/L: `₹{fmt(d_net)}`  **Avg Net/Day: `₹{fmt(d_net / len(dr))}`**",
            f"- Gross: `₹{fmt(d_gross)}`  Brokerage: `₹{fmt(d_brok)}`",
            f"- Best: `{best.entry_date}` `₹{best.net_pnl}`  Worst: `{worst.entry_date}` `₹{worst.net_pnl}`",
            "",
        ]

    by_year: Dict[str, List[TradeResult]] = {}
    for r in traded:
        by_year.setdefault(r.entry_date[:4], []).append(r)

    lines += [
        "## Yearly Summary",
        "",
        "| Year | Trades | Win | Loss | Total Net P/L | Avg Net/Day |",
        "|------|--------|-----|------|---------------|-------------|",
    ]
    for year in sorted(by_year):
        yr = by_year[year]
        y_net = sum(float(r.net_pnl) for r in yr)
        y_win = sum(1 for r in yr if float(r.net_pnl) > 0)
        y_loss = sum(1 for r in yr if float(r.net_pnl) < 0)
        lines.append(f"| {year} | {len(yr)} | {y_win} | {y_loss} | `₹{fmt(y_net)}` | `₹{fmt(y_net / len(yr))}` |")

    by_month_key: Dict[str, List[TradeResult]] = {}
    for r in traded:
        by_month_key.setdefault(r.entry_date[:7], []).append(r)

    lines += [
        "",
        "## Monthly Summary",
        "",
        "| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day |",
        "|-------|--------|-----|------|---------------|-------------|",
    ]
    for month in sorted(by_month_key):
        mr = by_month_key[month]
        m_net = sum(float(r.net_pnl) for r in mr)
        m_win = sum(1 for r in mr if float(r.net_pnl) > 0)
        m_loss = sum(1 for r in mr if float(r.net_pnl) < 0)
        lines.append(f"| {month} | {len(mr)} | {m_win} | {m_loss} | `₹{fmt(m_net)}` | `₹{fmt(m_net / len(mr))}` |")

    lines += ["", "## Skip Reason Summary", ""]
    for reason, count in sorted(skip_by_reason.items(), key=lambda x: -x[1]):
        lines.append(f"- `{reason}`: {count}")
    if balance_fails:
        lines.append(f"  _(balance check failures: {balance_fails})_")

    lines += ["", "## Exceptions (first 30)", ""]
    for r in skipped[:30]:
        lines.append(f"- `{r.entry_date}` ({r.day_of_week}): `{r.skip_reason}` — {r.remarks}")

    lines += [
        "", "## Remarks", "",
        "- Uses monthly contracts (last expiry of each calendar month).",
        "- Monthly options carry significantly higher premium than weekly options.",
        "- SL is 20% above entry price per leg; each leg exits independently.",
        "- SL monitoring uses the option contract's 1-minute candles.",
        "- Balance check: skip if min(CE,PE)/max(CE,PE) < 0.80 at entry.",
        "- Lot sizing is expiry-aware to maintain ~300 quantity.",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    results = run_backtest(args)
    write_daywise_csv(results, args.results_dir / DAYWISE_FILENAME)
    write_summary(results, args.results_dir / SUMMARY_FILENAME, args)
    traded = sum(1 for r in results if r.status == "TRADED")
    skipped = sum(1 for r in results if r.status == "SKIPPED")
    print(f"Done. Traded={traded} Skipped={skipped} Total={len(results)}")
    print(f"Daywise CSV : {args.results_dir / DAYWISE_FILENAME}")
    print(f"Summary     : {args.results_dir / SUMMARY_FILENAME}")


if __name__ == "__main__":
    main()
