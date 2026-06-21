#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

IST_SUFFIX = "+05:30"
BASE_FILENAME = "overnight_strangle_by_day_2025"
DAYWISE_FILENAME = f"{BASE_FILENAME}_daywise.csv"
TRADES_FILENAME = f"{BASE_FILENAME}_trades.csv"
SUMMARY_FILENAME = f"{BASE_FILENAME}_summary.md"
LOG_FILENAME = f"{BASE_FILENAME}.log"

# Monday=0 ... Sunday=6; primary band, fallback band (upper +5)
PREMIUM_BAND_BY_WEEKDAY: Dict[int, Tuple[float, float, float]] = {
    0: (5.0, 10.0, 15.0),   # Monday
    1: (20.0, 25.0, 30.0),  # Tuesday
    2: (20.0, 25.0, 30.0),  # Wednesday
    3: (15.0, 20.0, 25.0),  # Thursday
    4: (10.0, 15.0, 20.0),  # Friday
}
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@dataclass
class PriceRow:
    timestamp: str
    open_value: float
    open_text: str


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
    next_trading_day: str
    spot_entry_timestamp: str
    spot_entry_open: str
    atm_strike: str
    premium_band: str
    ce_strike: str
    ce_contract_file: str
    ce_entry_timestamp: str
    ce_entry_open: str
    ce_exit_timestamp: str
    ce_exit_open: str
    ce_points_pnl: str
    ce_gross_pnl: str
    ce_brokerage: str
    ce_net_pnl: str
    pe_strike: str
    pe_contract_file: str
    pe_entry_timestamp: str
    pe_entry_open: str
    pe_exit_timestamp: str
    pe_exit_open: str
    pe_points_pnl: str
    pe_gross_pnl: str
    pe_brokerage: str
    pe_net_pnl: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Backtest overnight short strangle: sell at 15:20, buy back next day 09:20.",
    )
    parser.add_argument("--spot-file", type=Path,
                        default=repo_root / "nifty" / "NIFTY50_INDEX_1m_2025.csv")
    parser.add_argument("--options-dir", type=Path, default=repo_root / "Options_2025")
    parser.add_argument("--results-dir", type=Path,
                        default=repo_root / "backtesting" / "results")
    parser.add_argument("--entry-time", default="15:20")
    parser.add_argument("--exit-time", default="09:20")
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--lot-size", type=int, default=75)
    parser.add_argument("--lots", type=int, default=1)
    parser.add_argument("--slippage-points-per-order", type=float, default=0.5)
    return parser.parse_args()


def build_timestamp(day: str, time_text: str) -> str:
    h, m = time_text.split(":")
    return f"{day}T{h}:{m}:00{IST_SUFFIX}"


def round_to_nearest_50(price: float) -> int:
    remainder = price % 50
    rounded_down = int(price - remainder)
    return rounded_down if remainder < 25 else rounded_down + 50


def fmt(value: float) -> str:
    return f"{value:.2f}"


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger(BASE_FILENAME)
    for h in logger.handlers:
        h.close()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def close_logger(logger: logging.Logger) -> None:
    for h in logger.handlers:
        h.close()
    logger.handlers.clear()


def load_spot_data(spot_file: Path) -> Tuple[List[str], Dict[str, Dict[str, PriceRow]]]:
    trading_days: List[str] = []
    rows_by_day: Dict[str, Dict[str, PriceRow]] = {}

    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            if not ts.startswith("2025-"):
                continue
            day = ts[:10]
            if day not in rows_by_day:
                rows_by_day[day] = {}
                trading_days.append(day)
            rows_by_day[day][ts] = PriceRow(
                timestamp=ts,
                open_value=float(row["open"]),
                open_text=row["open"],
            )

    return trading_days, rows_by_day


def load_expiry_folders(options_dir: Path) -> Tuple[List[str], Set[str]]:
    expiries = sorted(p.name for p in options_dir.iterdir() if p.is_dir())
    return expiries, set(expiries)


def next_expiry_strictly_after(expiries: List[str], date: str) -> Optional[str]:
    for e in expiries:
        if e > date:
            return e
    return None


def first_expiry_on_or_after(expiries: List[str], date: str) -> Optional[str]:
    for e in expiries:
        if e >= date:
            return e
    return None


def expiry_suffix(expiry_date: str) -> str:
    dt = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
    return dt.strftime("%d_%b_%y").upper()


def index_option_strikes(options_dir: Path, expiries: List[str]) -> Dict[Tuple[str, str], List[int]]:
    indexed: Dict[Tuple[str, str], List[int]] = {}
    pattern = re.compile(r"^NIFTY_(\d+)_(CE|PE)_[A-Z0-9_]+\.csv$")
    for expiry in expiries:
        ce_strikes: List[int] = []
        pe_strikes: List[int] = []
        for p in (options_dir / expiry).iterdir():
            if not p.is_file():
                continue
            m = pattern.match(p.name)
            if not m:
                continue
            strike = int(m.group(1))
            if m.group(2) == "CE":
                ce_strikes.append(strike)
            else:
                pe_strikes.append(strike)
        indexed[(expiry, "CE")] = sorted(ce_strikes)
        indexed[(expiry, "PE")] = sorted(pe_strikes)
    return indexed


def load_option_row(contract_path: Path, timestamp: str,
                    row_cache: Dict[Tuple[Path, str], Optional[PriceRow]]) -> Optional[PriceRow]:
    key = (contract_path, timestamp)
    if key in row_cache:
        return row_cache[key]
    if not contract_path.exists():
        row_cache[key] = None
        return None
    with contract_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            if ts == timestamp:
                result = PriceRow(timestamp=ts, open_value=float(row["open"]), open_text=row["open"])
                row_cache[key] = result
                return result
            if ts > timestamp:
                break
    row_cache[key] = None
    return None


def _scan_candidates(
    expiry_date: str,
    side: str,
    atm_strike: int,
    entry_timestamp: str,
    next_day_timestamp: str,
    options_dir: Path,
    strike_index: Dict[Tuple[str, str], List[int]],
    entry_row_cache: Dict[Tuple[Path, str], Optional[PriceRow]],
    exit_row_cache: Dict[Tuple[Path, str], Optional[PriceRow]],
    min_premium: float,
    max_premium: float,
) -> Optional[Tuple[int, Path, PriceRow, PriceRow]]:
    suffix = expiry_suffix(expiry_date)
    strikes = strike_index.get((expiry_date, side), [])
    ordered = [s for s in strikes if s > atm_strike] if side == "CE" else [s for s in reversed(strikes) if s < atm_strike]

    best: Optional[Tuple[int, int, Path, PriceRow, PriceRow]] = None
    for strike in ordered:
        path = options_dir / expiry_date / f"NIFTY_{strike}_{side}_{suffix}.csv"
        entry_row = load_option_row(path, entry_timestamp, entry_row_cache)
        if entry_row is None:
            continue
        if not (min_premium <= entry_row.open_value <= max_premium):
            continue
        exit_row = load_option_row(path, next_day_timestamp, exit_row_cache)
        if exit_row is None:
            continue
        dist = abs(strike - atm_strike)
        if best is None or dist < best[0]:
            best = (dist, strike, path, entry_row, exit_row)

    if best is None:
        return None
    _, strike, path, entry_row, exit_row = best
    return (strike, path, entry_row, exit_row)


def select_candidate(
    expiry_date: str,
    side: str,
    atm_strike: int,
    entry_timestamp: str,
    next_day_timestamp: str,
    options_dir: Path,
    strike_index: Dict[Tuple[str, str], List[int]],
    entry_row_cache: Dict[Tuple[Path, str], Optional[PriceRow]],
    exit_row_cache: Dict[Tuple[Path, str], Optional[PriceRow]],
    min_premium: float,
    max_premium: float,
    fallback_max_premium: float,
) -> Tuple[Optional[Tuple[int, Path, PriceRow, PriceRow]], str, str]:
    strikes = strike_index.get((expiry_date, side), [])
    if not strikes:
        return None, "", f"No OTM {side} strikes found beyond {atm_strike} for expiry {expiry_date}."

    result = _scan_candidates(
        expiry_date, side, atm_strike, entry_timestamp, next_day_timestamp,
        options_dir, strike_index, entry_row_cache, exit_row_cache,
        min_premium, max_premium,
    )
    if result is not None:
        return result, f"{fmt(min_premium)}-{fmt(max_premium)}", ""

    # fallback: widen upper bound
    result = _scan_candidates(
        expiry_date, side, atm_strike, entry_timestamp, next_day_timestamp,
        options_dir, strike_index, entry_row_cache, exit_row_cache,
        min_premium, fallback_max_premium,
    )
    if result is not None:
        return result, f"{fmt(min_premium)}-{fmt(fallback_max_premium)}(fallback)", ""

    return (
        None,
        "",
        f"No OTM {side} contract with premium in [{fmt(min_premium)}, {fmt(fallback_max_premium)}] "
        f"having both entry {entry_timestamp} and exit {next_day_timestamp}.",
    )


def make_empty_result(
    entry_date: str,
    day_of_week: str,
    status: str,
    skip_reason: str,
    expiry_date: str,
    expiry_type: str,
    next_trading_day: str,
    spot_entry_timestamp: str,
    spot_entry_open: str,
    atm_strike: str,
    premium_band: str,
    remarks: str,
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date,
        day_of_week=day_of_week,
        status=status,
        skip_reason=skip_reason,
        expiry_date=expiry_date,
        expiry_type=expiry_type,
        next_trading_day=next_trading_day,
        spot_entry_timestamp=spot_entry_timestamp,
        spot_entry_open=spot_entry_open,
        atm_strike=atm_strike,
        premium_band=premium_band,
        ce_strike="", ce_contract_file="",
        ce_entry_timestamp="", ce_entry_open="",
        ce_exit_timestamp="", ce_exit_open="",
        ce_points_pnl="0.00", ce_gross_pnl="0.00",
        ce_brokerage="0.00", ce_net_pnl="0.00",
        pe_strike="", pe_contract_file="",
        pe_entry_timestamp="", pe_entry_open="",
        pe_exit_timestamp="", pe_exit_open="",
        pe_points_pnl="0.00", pe_gross_pnl="0.00",
        pe_brokerage="0.00", pe_net_pnl="0.00",
        gross_pnl="0.00", brokerage="0.00", net_pnl="0.00",
        remarks=remarks,
    )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, spot_rows_by_day = load_spot_data(args.spot_file)
    expiries, expiry_set = load_expiry_folders(args.options_dir)
    strike_index = index_option_strikes(args.options_dir, expiries)
    entry_row_cache: Dict[Tuple[Path, str], Optional[PriceRow]] = {}
    exit_row_cache: Dict[Tuple[Path, str], Optional[PriceRow]] = {}
    contract_multiplier = args.lot_size * args.lots
    round_trip_brokerage = args.brokerage_per_order * 4
    next_day_map = {
        trading_days[i]: trading_days[i + 1] if i + 1 < len(trading_days) else ""
        for i in range(len(trading_days))
    }
    results: List[TradeResult] = []

    try:
        for entry_date in trading_days:
            weekday = datetime.date.fromisoformat(entry_date).weekday()
            day_name = WEEKDAY_NAMES[weekday]

            if weekday not in PREMIUM_BAND_BY_WEEKDAY:
                logger.info("SKIP date=%s day=%s reason=weekend", entry_date, day_name)
                continue

            min_prem, max_prem, fallback_max_prem = PREMIUM_BAND_BY_WEEKDAY[weekday]
            band_text = f"{fmt(min_prem)}-{fmt(max_prem)}"

            entry_timestamp = build_timestamp(entry_date, args.entry_time)
            spot_day = spot_rows_by_day.get(entry_date, {})
            spot_row = spot_day.get(entry_timestamp)

            if spot_row is None:
                result = make_empty_result(
                    entry_date=entry_date, day_of_week=day_name,
                    status="SKIPPED", skip_reason="missing_spot_entry",
                    expiry_date="", expiry_type="", next_trading_day="",
                    spot_entry_timestamp=entry_timestamp, spot_entry_open="",
                    atm_strike="", premium_band=band_text,
                    remarks=f"No spot candle at {entry_timestamp}.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=missing_spot_entry", entry_date)
                continue

            next_trading_day = next_day_map[entry_date]
            if not next_trading_day:
                result = make_empty_result(
                    entry_date=entry_date, day_of_week=day_name,
                    status="SKIPPED", skip_reason="no_next_trading_day",
                    expiry_date="", expiry_type="", next_trading_day="",
                    spot_entry_timestamp=entry_timestamp, spot_entry_open=spot_row.open_text,
                    atm_strike="", premium_band=band_text,
                    remarks="No next trading day in dataset.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=no_next_trading_day", entry_date)
                continue

            is_expiry_day = entry_date in expiry_set
            if is_expiry_day:
                expiry_date = next_expiry_strictly_after(expiries, entry_date)
                expiry_type = "next_week"
            else:
                expiry_date = first_expiry_on_or_after(expiries, entry_date)
                expiry_type = "current_week"

            if expiry_date is None:
                result = make_empty_result(
                    entry_date=entry_date, day_of_week=day_name,
                    status="SKIPPED", skip_reason="no_expiry_found",
                    expiry_date="", expiry_type=expiry_type, next_trading_day=next_trading_day,
                    spot_entry_timestamp=entry_timestamp, spot_entry_open=spot_row.open_text,
                    atm_strike="", premium_band=band_text,
                    remarks="No suitable expiry folder found.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=no_expiry_found", entry_date)
                continue

            atm_strike = round_to_nearest_50(spot_row.open_value)
            exit_timestamp = build_timestamp(next_trading_day, args.exit_time)

            ce_result, ce_band_used, ce_error = select_candidate(
                expiry_date=expiry_date, side="CE", atm_strike=atm_strike,
                entry_timestamp=entry_timestamp, next_day_timestamp=exit_timestamp,
                options_dir=args.options_dir, strike_index=strike_index,
                entry_row_cache=entry_row_cache, exit_row_cache=exit_row_cache,
                min_premium=min_prem, max_premium=max_prem,
                fallback_max_premium=fallback_max_prem,
            )
            pe_result, pe_band_used, pe_error = select_candidate(
                expiry_date=expiry_date, side="PE", atm_strike=atm_strike,
                entry_timestamp=entry_timestamp, next_day_timestamp=exit_timestamp,
                options_dir=args.options_dir, strike_index=strike_index,
                entry_row_cache=entry_row_cache, exit_row_cache=exit_row_cache,
                min_premium=min_prem, max_premium=max_prem,
                fallback_max_premium=fallback_max_prem,
            )

            if ce_result is None or pe_result is None:
                errors = "; ".join(e for e in [ce_error, pe_error] if e)
                result = make_empty_result(
                    entry_date=entry_date, day_of_week=day_name,
                    status="SKIPPED", skip_reason="no_valid_strangle",
                    expiry_date=expiry_date, expiry_type=expiry_type,
                    next_trading_day=next_trading_day,
                    spot_entry_timestamp=entry_timestamp, spot_entry_open=spot_row.open_text,
                    atm_strike=str(atm_strike), premium_band=band_text,
                    remarks=errors,
                )
                results.append(result)
                logger.info("SKIPPED date=%s expiry=%s atm=%s reason=%s",
                            entry_date, expiry_date, atm_strike, errors)
                continue

            ce_strike, ce_path, ce_entry_row, ce_exit_row = ce_result
            pe_strike, pe_path, pe_entry_row, pe_exit_row = pe_result

            ce_points = ce_entry_row.open_value - ce_exit_row.open_value - 2 * args.slippage_points_per_order
            pe_points = pe_entry_row.open_value - pe_exit_row.open_value - 2 * args.slippage_points_per_order
            ce_gross = ce_points * contract_multiplier
            pe_gross = pe_points * contract_multiplier
            gross_pnl = ce_gross + pe_gross
            brokerage = round_trip_brokerage
            net_pnl = gross_pnl - brokerage
            actual_band = f"CE:{ce_band_used} PE:{pe_band_used}"

            result = TradeResult(
                entry_date=entry_date,
                day_of_week=day_name,
                status="TRADED",
                skip_reason="",
                expiry_date=expiry_date,
                expiry_type=expiry_type,
                next_trading_day=next_trading_day,
                spot_entry_timestamp=entry_timestamp,
                spot_entry_open=spot_row.open_text,
                atm_strike=str(atm_strike),
                premium_band=actual_band,
                ce_strike=str(ce_strike),
                ce_contract_file=ce_path.name,
                ce_entry_timestamp=entry_timestamp,
                ce_entry_open=ce_entry_row.open_text,
                ce_exit_timestamp=exit_timestamp,
                ce_exit_open=ce_exit_row.open_text,
                ce_points_pnl=fmt(ce_points),
                ce_gross_pnl=fmt(ce_gross),
                ce_brokerage=fmt(args.brokerage_per_order * 2),
                ce_net_pnl=fmt(ce_gross - args.brokerage_per_order * 2),
                pe_strike=str(pe_strike),
                pe_contract_file=pe_path.name,
                pe_entry_timestamp=entry_timestamp,
                pe_entry_open=pe_entry_row.open_text,
                pe_exit_timestamp=exit_timestamp,
                pe_exit_open=pe_exit_row.open_text,
                pe_points_pnl=fmt(pe_points),
                pe_gross_pnl=fmt(pe_gross),
                pe_brokerage=fmt(args.brokerage_per_order * 2),
                pe_net_pnl=fmt(pe_gross - args.brokerage_per_order * 2),
                gross_pnl=fmt(gross_pnl),
                brokerage=fmt(brokerage),
                net_pnl=fmt(net_pnl),
                remarks="",
            )
            results.append(result)
            logger.info(
                "TRADED date=%s day=%s expiry=%s(%s) atm=%s ce=%s@%s[%s] pe=%s@%s[%s] net=%s",
                entry_date, day_name, expiry_date, expiry_type,
                atm_strike, ce_strike, ce_entry_row.open_text, ce_band_used,
                pe_strike, pe_entry_row.open_text, pe_band_used, fmt(net_pnl),
            )
    except Exception:
        logger.exception("ERROR unexpected failure")
        raise
    finally:
        traded = sum(1 for r in results if r.status == "TRADED")
        skipped = sum(1 for r in results if r.status == "SKIPPED")
        logger.info("COMPLETED traded=%s skipped=%s total=%s", traded, skipped, len(results))
        close_logger(logger)

    return results


def write_daywise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date", "day_of_week", "status", "skip_reason",
        "expiry_date", "expiry_type", "next_trading_day",
        "spot_entry_timestamp", "spot_entry_open", "atm_strike", "premium_band",
        "ce_strike", "ce_contract_file", "ce_entry_timestamp", "ce_entry_open",
        "ce_exit_timestamp", "ce_exit_open",
        "ce_points_pnl", "ce_gross_pnl", "ce_brokerage", "ce_net_pnl",
        "pe_strike", "pe_contract_file", "pe_entry_timestamp", "pe_entry_open",
        "pe_exit_timestamp", "pe_exit_open",
        "pe_points_pnl", "pe_gross_pnl", "pe_brokerage", "pe_net_pnl",
        "gross_pnl", "brokerage", "net_pnl", "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r.__dict__)


def compute_equity_stats(net_pnls: List[float]) -> tuple:
    """Returns (max_drawdown, peak_cumulative_profit)."""
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    peak_profit = 0.0
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
    gross_total = sum(float(r.gross_pnl) for r in traded)
    brokerage_total = sum(float(r.brokerage) for r in traded)
    net_total = sum(float(r.net_pnl) for r in traded)
    max_dd, peak_profit = compute_equity_stats([float(r.net_pnl) for r in traded])
    winning_days = sum(1 for r in traded if float(r.net_pnl) > 0)
    losing_days = sum(1 for r in traded if float(r.net_pnl) < 0)

    by_day: Dict[str, List[TradeResult]] = {}
    for r in traded:
        by_day.setdefault(r.day_of_week, []).append(r)

    max_profit = max(traded, key=lambda r: float(r.net_pnl), default=None)
    max_loss = min(traded, key=lambda r: float(r.net_pnl), default=None)

    lines = [
        "# 2025 Overnight Short Strangle by Day Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Entry time: `{args.entry_time}` (sell)",
        f"- Exit time: `{args.exit_time}` next trading day (buy back)",
        "- ATM rule: nearest 50 using spot open at entry time",
        "- Expiry rule: if entry day is expiry day → next week expiry; otherwise → current week expiry",
        "- CE selection: OTM CE closest to ATM with price in band",
        "- PE selection: OTM PE closest to ATM with price in band",
        "- Premium bands by day (primary → fallback if not found):",
        "  - Monday: 5-10 → 5-15",
        "  - Tuesday (expiry, next week): 20-25 → 20-30",
        "  - Wednesday: 20-25 → 20-30",
        "  - Thursday: 15-20 → 15-25",
        "  - Friday: 10-15 → 10-20",
        f"- Contract multiplier: {args.lot_size} × {args.lots} = {args.lot_size * args.lots} per point",
        f"- Slippage: {fmt(args.slippage_points_per_order)} point per order",
        f"- Brokerage: Rs {fmt(args.brokerage_per_order)} per order, Rs {fmt(args.brokerage_per_order * 4)} per strangle",
        "",
        "## Results Summary",
        "",
        f"- Total traded days: `{len(traded)}`",
        f"- Total skipped days: `{len(skipped)}`",
        f"- Winning days: `{winning_days}`",
        f"- Losing days: `{losing_days}`",
        f"- Total Gross P/L: `{fmt(gross_total)}`",
        f"- Total Brokerage: `{fmt(brokerage_total)}`",
        f"- Total Net P/L: `{fmt(net_total)}`",
        (f"- Max profit day: `{max_profit.entry_date}` ({max_profit.day_of_week}) net `{max_profit.net_pnl}`"
         if max_profit else "- Max profit day: N/A"),
        (f"- Max loss day: `{max_loss.entry_date}` ({max_loss.day_of_week}) net `{max_loss.net_pnl}`"
         if max_loss else "- Max loss day: N/A"),
        f"- Peak cumulative profit: `{fmt(peak_profit)}`",
        f"- Max drawdown: `{fmt(max_dd)}`",
        "",
        "## Results by Day of Week",
        "",
    ]

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for d in day_order:
        day_results = by_day.get(d, [])
        if not day_results:
            lines.append(f"### {d}: no trades")
            lines.append("")
            continue
        d_gross = sum(float(r.gross_pnl) for r in day_results)
        d_brok = sum(float(r.brokerage) for r in day_results)
        d_net = sum(float(r.net_pnl) for r in day_results)
        d_win = sum(1 for r in day_results if float(r.net_pnl) > 0)
        d_loss = sum(1 for r in day_results if float(r.net_pnl) < 0)
        lines.extend([
            f"### {d}",
            f"- Trades: `{len(day_results)}`  Win: `{d_win}`  Loss: `{d_loss}`",
            f"- Net P/L: `{fmt(d_net)}`  Gross: `{fmt(d_gross)}`  Brokerage: `{fmt(d_brok)}`",
            "",
        ])

    lines.extend([
        "## Exceptions",
        "",
    ])
    if skipped:
        for r in skipped:
            lines.append(f"- `{r.entry_date}` ({r.day_of_week}): `{r.skip_reason}`. {r.remarks}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Remarks",
        "",
        "- Exact timestamp matching only; no nearest-candle fallback.",
        "- A day is skipped if no OTM CE or PE satisfies the band with both entry and exit candles.",
        "- NIFTY spot file is the source of truth for the trading calendar.",
        "- Tuesday is treated as expiry day when that date has an expiry folder.",
    ])

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    results = run_backtest(args)
    write_daywise_csv(results, args.results_dir / DAYWISE_FILENAME)
    write_summary(results, args.results_dir / SUMMARY_FILENAME, args)


if __name__ == "__main__":
    main()
