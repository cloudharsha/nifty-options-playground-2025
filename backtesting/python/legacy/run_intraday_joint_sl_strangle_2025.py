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
BASE_FILENAME = "intraday_joint_sl_strangle_2025"
DAYWISE_FILENAME = f"{BASE_FILENAME}_daywise.csv"
SUMMARY_FILENAME = f"{BASE_FILENAME}_summary.md"
LOG_FILENAME = f"{BASE_FILENAME}.log"

# Monday=0 ... Sunday=6; (min_premium, max_premium, fallback_max_premium)
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
    high_value: float
    low_value: float


@dataclass
class ContractData:
    path: Path
    rows_by_timestamp: Dict[str, PriceRow]


@dataclass
class LegResult:
    strike: str
    contract_file: str
    entry_timestamp: str
    entry_price: str
    stop_price: str
    exit_timestamp: str
    exit_price: str
    exit_reason: str
    points_pnl: str
    gross_pnl: str
    brokerage: str
    net_pnl: str


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
    premium_band: str
    sl_trigger: str
    ce_strike: str
    ce_contract_file: str
    ce_entry_timestamp: str
    ce_entry_open: str
    ce_stop_price: str
    ce_exit_timestamp: str
    ce_exit_price: str
    ce_exit_reason: str
    ce_points_pnl: str
    ce_gross_pnl: str
    ce_brokerage: str
    ce_net_pnl: str
    pe_strike: str
    pe_contract_file: str
    pe_entry_timestamp: str
    pe_entry_open: str
    pe_stop_price: str
    pe_exit_timestamp: str
    pe_exit_price: str
    pe_exit_reason: str
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
        description="Backtest intraday joint-SL short strangle: enter 09:20, exit 15:20 or 2x SL.",
    )
    parser.add_argument("--spot-file", type=Path,
                        default=repo_root / "nifty" / "NIFTY50_INDEX_1m_2025.csv")
    parser.add_argument("--options-dir", type=Path, default=repo_root / "Options_2025")
    parser.add_argument("--results-dir", type=Path,
                        default=repo_root / "backtesting" / "results")
    parser.add_argument("--entry-time", default="09:20")
    parser.add_argument("--exit-time", default="15:20")
    parser.add_argument("--sl-multiple", type=float, default=2.0,
                        help="Stop loss as a multiple of entry premium (default 2x)")
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


def load_spot_data(spot_file: Path) -> Tuple[List[str], Dict[str, List[str]]]:
    trading_days: List[str] = []
    timestamps_by_day: Dict[str, List[str]] = {}

    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            if not ts.startswith("2025-"):
                continue
            day = ts[:10]
            if day not in timestamps_by_day:
                timestamps_by_day[day] = []
                trading_days.append(day)
            timestamps_by_day[day].append(ts)

    return trading_days, timestamps_by_day


def load_spot_entry(spot_file: Path, trading_days: List[str]) -> Dict[str, float]:
    # reuse the spot file to get open prices at entry time
    result: Dict[str, float] = {}
    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            day = ts[:10]
            if day in result:
                continue
            if "T09:20:00" in ts:
                result[day] = float(row["open"])
    return result


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


def load_contract(contract_path: Path, cache: Dict[Path, Optional[ContractData]]) -> Optional[ContractData]:
    if contract_path in cache:
        return cache[contract_path]
    if not contract_path.exists():
        cache[contract_path] = None
        return None
    rows: Dict[str, PriceRow] = {}
    with contract_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            rows[ts] = PriceRow(
                timestamp=ts,
                open_value=float(row["open"]),
                open_text=row["open"],
                high_value=float(row["high"]),
                low_value=float(row["low"]),
            )
    data = ContractData(path=contract_path, rows_by_timestamp=rows)
    cache[contract_path] = data
    return data


def find_candidate(
    expiry_date: str,
    side: str,
    atm_strike: int,
    entry_timestamp: str,
    options_dir: Path,
    strike_index: Dict[Tuple[str, str], List[int]],
    contract_cache: Dict[Path, Optional[ContractData]],
    min_premium: float,
    max_premium: float,
) -> Optional[Tuple[int, ContractData, PriceRow]]:
    suffix = expiry_suffix(expiry_date)
    strikes = strike_index.get((expiry_date, side), [])
    ordered = [s for s in strikes if s > atm_strike] if side == "CE" else [s for s in reversed(strikes) if s < atm_strike]

    best: Optional[Tuple[int, int, ContractData, PriceRow]] = None
    for strike in ordered:
        path = options_dir / expiry_date / f"NIFTY_{strike}_{side}_{suffix}.csv"
        contract = load_contract(path, contract_cache)
        if contract is None:
            continue
        entry_row = contract.rows_by_timestamp.get(entry_timestamp)
        if entry_row is None:
            continue
        if not (min_premium <= entry_row.open_value <= max_premium):
            continue
        dist = abs(strike - atm_strike)
        if best is None or dist < best[0]:
            best = (dist, strike, contract, entry_row)

    if best is None:
        return None
    _, strike, contract, entry_row = best
    return strike, contract, entry_row


def select_candidate(
    expiry_date: str,
    side: str,
    atm_strike: int,
    entry_timestamp: str,
    options_dir: Path,
    strike_index: Dict[Tuple[str, str], List[int]],
    contract_cache: Dict[Path, Optional[ContractData]],
    min_premium: float,
    max_premium: float,
    fallback_max_premium: float,
) -> Tuple[Optional[Tuple[int, ContractData, PriceRow]], str, str]:
    result = find_candidate(
        expiry_date, side, atm_strike, entry_timestamp,
        options_dir, strike_index, contract_cache, min_premium, max_premium,
    )
    if result is not None:
        return result, f"{fmt(min_premium)}-{fmt(max_premium)}", ""

    result = find_candidate(
        expiry_date, side, atm_strike, entry_timestamp,
        options_dir, strike_index, contract_cache, min_premium, fallback_max_premium,
    )
    if result is not None:
        return result, f"{fmt(min_premium)}-{fmt(fallback_max_premium)}(fb)", ""

    return (
        None,
        "",
        f"No OTM {side} in [{fmt(min_premium)}, {fmt(fallback_max_premium)}] at {entry_timestamp}.",
    )


def short_points_pnl(entry: float, exit_price: float, slippage: float) -> float:
    return entry - exit_price - 2 * slippage


def monitor_and_exit(
    ce_contract: ContractData,
    pe_contract: ContractData,
    ce_entry: PriceRow,
    pe_entry: PriceRow,
    day_timestamps: List[str],
    entry_timestamp: str,
    exit_timestamp: str,
    sl_multiple: float,
    slippage: float,
    contract_multiplier: int,
    brokerage_per_order: float,
) -> Tuple[str, str, str, str, str, str, str, str, str, str, str, str, str, str]:
    """
    Returns:
        sl_trigger,
        ce_exit_ts, ce_exit_price, ce_exit_reason,
        pe_exit_ts, pe_exit_price, pe_exit_reason,
        ce_points, ce_gross, ce_brok, ce_net,
        pe_points, pe_gross, pe_brok, pe_net
    """
    ce_stop = ce_entry.open_value * sl_multiple
    pe_stop = pe_entry.open_value * sl_multiple

    try:
        entry_idx = day_timestamps.index(entry_timestamp)
        exit_idx = day_timestamps.index(exit_timestamp)
    except ValueError:
        # If timestamps not found, fall through to scheduled exit
        entry_idx = 0
        exit_idx = len(day_timestamps) - 1

    monitoring_ts = day_timestamps[entry_idx:exit_idx + 1]

    for ts in monitoring_ts:
        ce_row = ce_contract.rows_by_timestamp.get(ts)
        pe_row = pe_contract.rows_by_timestamp.get(ts)

        if ce_row is None or pe_row is None:
            continue

        # Check gap SL (open already above stop)
        ce_gap_sl = ce_row.open_value >= ce_stop
        pe_gap_sl = pe_row.open_value >= pe_stop

        if ce_gap_sl or pe_gap_sl:
            # Determine which triggered first (if both gap simultaneously, CE takes priority)
            if ce_gap_sl and pe_gap_sl:
                sl_trigger = "BOTH"
            elif ce_gap_sl:
                sl_trigger = "CE"
            else:
                sl_trigger = "PE"

            ce_exit_price = ce_row.open_value
            pe_exit_price = pe_row.open_value
            ce_exit_reason = "gap_sl" if ce_gap_sl else "partner_gap_sl"
            pe_exit_reason = "gap_sl" if pe_gap_sl else "partner_gap_sl"

            ce_pts = short_points_pnl(ce_entry.open_value, ce_exit_price, slippage)
            pe_pts = short_points_pnl(pe_entry.open_value, pe_exit_price, slippage)
            ce_gross = ce_pts * contract_multiplier
            pe_gross = pe_pts * contract_multiplier
            ce_brok = brokerage_per_order * 2
            pe_brok = brokerage_per_order * 2
            return (
                sl_trigger,
                ts, fmt(ce_exit_price), ce_exit_reason,
                ts, fmt(pe_exit_price), pe_exit_reason,
                fmt(ce_pts), fmt(ce_gross), fmt(ce_brok), fmt(ce_gross - ce_brok),
                fmt(pe_pts), fmt(pe_gross), fmt(pe_brok), fmt(pe_gross - pe_brok),
            )

        # Check intrabar SL
        ce_sl_hit = ce_row.high_value >= ce_stop
        pe_sl_hit = pe_row.high_value >= pe_stop

        if ce_sl_hit or pe_sl_hit:
            sl_trigger = "BOTH" if (ce_sl_hit and pe_sl_hit) else ("CE" if ce_sl_hit else "PE")

            # SL leg exits at stop price; partner leg exits at current candle open
            if ce_sl_hit:
                ce_exit_price = ce_stop
                ce_exit_reason = "sl"
                pe_exit_price = pe_row.open_value
                pe_exit_reason = "partner_sl"
            else:
                pe_exit_price = pe_stop
                pe_exit_reason = "sl"
                ce_exit_price = ce_row.open_value
                ce_exit_reason = "partner_sl"

            if ce_sl_hit and pe_sl_hit:
                ce_exit_price = ce_stop
                ce_exit_reason = "sl"
                pe_exit_price = pe_stop
                pe_exit_reason = "sl"

            ce_pts = short_points_pnl(ce_entry.open_value, ce_exit_price, slippage)
            pe_pts = short_points_pnl(pe_entry.open_value, pe_exit_price, slippage)
            ce_gross = ce_pts * contract_multiplier
            pe_gross = pe_pts * contract_multiplier
            ce_brok = brokerage_per_order * 2
            pe_brok = brokerage_per_order * 2
            return (
                sl_trigger,
                ts, fmt(ce_exit_price), ce_exit_reason,
                ts, fmt(pe_exit_price), pe_exit_reason,
                fmt(ce_pts), fmt(ce_gross), fmt(ce_brok), fmt(ce_gross - ce_brok),
                fmt(pe_pts), fmt(pe_gross), fmt(pe_brok), fmt(pe_gross - pe_brok),
            )

    # No SL hit — exit at scheduled close
    ce_exit_row = ce_contract.rows_by_timestamp.get(exit_timestamp)
    pe_exit_row = pe_contract.rows_by_timestamp.get(exit_timestamp)

    ce_exit_price = ce_exit_row.open_value if ce_exit_row else ce_entry.open_value
    pe_exit_price = pe_exit_row.open_value if pe_exit_row else pe_entry.open_value
    ce_exit_reason = "day_close" if ce_exit_row else "missing_exit_candle"
    pe_exit_reason = "day_close" if pe_exit_row else "missing_exit_candle"

    ce_pts = short_points_pnl(ce_entry.open_value, ce_exit_price, slippage)
    pe_pts = short_points_pnl(pe_entry.open_value, pe_exit_price, slippage)
    ce_gross = ce_pts * contract_multiplier
    pe_gross = pe_pts * contract_multiplier
    ce_brok = brokerage_per_order * 2
    pe_brok = brokerage_per_order * 2
    return (
        "none",
        exit_timestamp, fmt(ce_exit_price), ce_exit_reason,
        exit_timestamp, fmt(pe_exit_price), pe_exit_reason,
        fmt(ce_pts), fmt(ce_gross), fmt(ce_brok), fmt(ce_gross - ce_brok),
        fmt(pe_pts), fmt(pe_gross), fmt(pe_brok), fmt(pe_gross - pe_brok),
    )


def empty_result(
    entry_date: str, day_of_week: str, skip_reason: str,
    expiry_date: str, expiry_type: str,
    spot_entry_timestamp: str, spot_entry_open: str,
    atm_strike: str, premium_band: str, remarks: str,
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date, day_of_week=day_of_week,
        status="SKIPPED", skip_reason=skip_reason,
        expiry_date=expiry_date, expiry_type=expiry_type,
        spot_entry_timestamp=spot_entry_timestamp, spot_entry_open=spot_entry_open,
        atm_strike=atm_strike, premium_band=premium_band, sl_trigger="",
        ce_strike="", ce_contract_file="",
        ce_entry_timestamp="", ce_entry_open="", ce_stop_price="",
        ce_exit_timestamp="", ce_exit_price="", ce_exit_reason="",
        ce_points_pnl="0.00", ce_gross_pnl="0.00", ce_brokerage="0.00", ce_net_pnl="0.00",
        pe_strike="", pe_contract_file="",
        pe_entry_timestamp="", pe_entry_open="", pe_stop_price="",
        pe_exit_timestamp="", pe_exit_price="", pe_exit_reason="",
        pe_points_pnl="0.00", pe_gross_pnl="0.00", pe_brokerage="0.00", pe_net_pnl="0.00",
        gross_pnl="0.00", brokerage="0.00", net_pnl="0.00", remarks=remarks,
    )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, timestamps_by_day = load_spot_data(args.spot_file)
    expiries, expiry_set = load_expiry_folders(args.options_dir)
    strike_index = index_option_strikes(args.options_dir, expiries)
    contract_cache: Dict[Path, Optional[ContractData]] = {}
    contract_multiplier = args.lot_size * args.lots
    round_trip_brokerage = args.brokerage_per_order * 4

    # Load spot open prices at entry time
    spot_open_by_day: Dict[str, Tuple[float, str]] = {}
    with args.spot_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            if not ts.startswith("2025-"):
                continue
            day = ts[:10]
            if day not in spot_open_by_day and f"T{args.entry_time}:00" in ts:
                spot_open_by_day[day] = (float(row["open"]), row["open"])

    results: List[TradeResult] = []

    try:
        for entry_date in trading_days:
            weekday = datetime.date.fromisoformat(entry_date).weekday()
            day_name = WEEKDAY_NAMES[weekday]

            if weekday not in PREMIUM_BAND_BY_WEEKDAY:
                continue

            min_prem, max_prem, fallback_max_prem = PREMIUM_BAND_BY_WEEKDAY[weekday]
            band_label = f"{fmt(min_prem)}-{fmt(max_prem)}"
            entry_timestamp = build_timestamp(entry_date, args.entry_time)
            exit_timestamp = build_timestamp(entry_date, args.exit_time)
            day_timestamps = timestamps_by_day.get(entry_date, [])

            if entry_timestamp not in day_timestamps:
                results.append(empty_result(
                    entry_date, day_name, "missing_spot_entry",
                    "", "", entry_timestamp, "", "", band_label,
                    f"No spot candle at {entry_timestamp}.",
                ))
                logger.info("SKIPPED date=%s reason=missing_spot_entry", entry_date)
                continue

            if exit_timestamp not in day_timestamps:
                results.append(empty_result(
                    entry_date, day_name, "missing_spot_exit",
                    "", "", entry_timestamp, "", "", band_label,
                    f"No spot candle at {exit_timestamp}.",
                ))
                logger.info("SKIPPED date=%s reason=missing_spot_exit", entry_date)
                continue

            spot_open_val, spot_open_text = spot_open_by_day.get(entry_date, (0.0, ""))
            if not spot_open_text:
                results.append(empty_result(
                    entry_date, day_name, "missing_spot_open",
                    "", "", entry_timestamp, "", "", band_label,
                    "Spot open price unavailable.",
                ))
                continue

            is_expiry_day = entry_date in expiry_set
            if is_expiry_day:
                expiry_date = next_expiry_strictly_after(expiries, entry_date)
                expiry_type = "next_week"
            else:
                expiry_date = first_expiry_on_or_after(expiries, entry_date)
                expiry_type = "current_week"

            if expiry_date is None:
                results.append(empty_result(
                    entry_date, day_name, "no_expiry_found",
                    "", expiry_type if is_expiry_day else "current_week",
                    entry_timestamp, spot_open_text, "", band_label,
                    "No suitable expiry found.",
                ))
                continue

            atm_strike = round_to_nearest_50(spot_open_val)

            ce_result, ce_band, ce_error = select_candidate(
                expiry_date, "CE", atm_strike, entry_timestamp,
                args.options_dir, strike_index, contract_cache,
                min_prem, max_prem, fallback_max_prem,
            )
            pe_result, pe_band, pe_error = select_candidate(
                expiry_date, "PE", atm_strike, entry_timestamp,
                args.options_dir, strike_index, contract_cache,
                min_prem, max_prem, fallback_max_prem,
            )

            if ce_result is None or pe_result is None:
                errors = "; ".join(e for e in [ce_error, pe_error] if e)
                results.append(empty_result(
                    entry_date, day_name, "no_valid_strangle",
                    expiry_date, expiry_type, entry_timestamp, spot_open_text,
                    str(atm_strike), band_label, errors,
                ))
                logger.info("SKIPPED date=%s expiry=%s atm=%s reason=%s",
                            entry_date, expiry_date, atm_strike, errors)
                continue

            ce_strike, ce_contract, ce_entry_row = ce_result
            pe_strike, pe_contract, pe_entry_row = pe_result
            actual_band = f"CE:{ce_band} PE:{pe_band}"

            (
                sl_trigger,
                ce_exit_ts, ce_exit_price, ce_exit_reason,
                pe_exit_ts, pe_exit_price, pe_exit_reason,
                ce_pts, ce_gross, ce_brok, ce_net,
                pe_pts, pe_gross, pe_brok, pe_net,
            ) = monitor_and_exit(
                ce_contract=ce_contract,
                pe_contract=pe_contract,
                ce_entry=ce_entry_row,
                pe_entry=pe_entry_row,
                day_timestamps=day_timestamps,
                entry_timestamp=entry_timestamp,
                exit_timestamp=exit_timestamp,
                sl_multiple=args.sl_multiple,
                slippage=args.slippage_points_per_order,
                contract_multiplier=contract_multiplier,
                brokerage_per_order=args.brokerage_per_order,
            )

            gross_pnl = float(ce_gross) + float(pe_gross)
            net_pnl = gross_pnl - round_trip_brokerage

            result = TradeResult(
                entry_date=entry_date,
                day_of_week=day_name,
                status="TRADED",
                skip_reason="",
                expiry_date=expiry_date,
                expiry_type=expiry_type,
                spot_entry_timestamp=entry_timestamp,
                spot_entry_open=spot_open_text,
                atm_strike=str(atm_strike),
                premium_band=actual_band,
                sl_trigger=sl_trigger,
                ce_strike=str(ce_strike),
                ce_contract_file=ce_contract.path.name,
                ce_entry_timestamp=entry_timestamp,
                ce_entry_open=ce_entry_row.open_text,
                ce_stop_price=fmt(ce_entry_row.open_value * args.sl_multiple),
                ce_exit_timestamp=ce_exit_ts,
                ce_exit_price=ce_exit_price,
                ce_exit_reason=ce_exit_reason,
                ce_points_pnl=ce_pts,
                ce_gross_pnl=ce_gross,
                ce_brokerage=ce_brok,
                ce_net_pnl=ce_net,
                pe_strike=str(pe_strike),
                pe_contract_file=pe_contract.path.name,
                pe_entry_timestamp=entry_timestamp,
                pe_entry_open=pe_entry_row.open_text,
                pe_stop_price=fmt(pe_entry_row.open_value * args.sl_multiple),
                pe_exit_timestamp=pe_exit_ts,
                pe_exit_price=pe_exit_price,
                pe_exit_reason=pe_exit_reason,
                pe_points_pnl=pe_pts,
                pe_gross_pnl=pe_gross,
                pe_brokerage=pe_brok,
                pe_net_pnl=pe_net,
                gross_pnl=fmt(gross_pnl),
                brokerage=fmt(round_trip_brokerage),
                net_pnl=fmt(net_pnl),
                remarks="",
            )
            results.append(result)
            logger.info(
                "TRADED date=%s day=%s expiry=%s atm=%s ce=%s@%s pe=%s@%s sl=%s net=%s",
                entry_date, day_name, expiry_date, atm_strike,
                ce_strike, ce_entry_row.open_text,
                pe_strike, pe_entry_row.open_text,
                sl_trigger, fmt(net_pnl),
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
        "expiry_date", "expiry_type",
        "spot_entry_timestamp", "spot_entry_open", "atm_strike", "premium_band", "sl_trigger",
        "ce_strike", "ce_contract_file", "ce_entry_timestamp", "ce_entry_open", "ce_stop_price",
        "ce_exit_timestamp", "ce_exit_price", "ce_exit_reason",
        "ce_points_pnl", "ce_gross_pnl", "ce_brokerage", "ce_net_pnl",
        "pe_strike", "pe_contract_file", "pe_entry_timestamp", "pe_entry_open", "pe_stop_price",
        "pe_exit_timestamp", "pe_exit_price", "pe_exit_reason",
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
    sl_days = sum(1 for r in traded if r.sl_trigger != "none")
    no_sl_days = sum(1 for r in traded if r.sl_trigger == "none")
    max_profit = max(traded, key=lambda r: float(r.net_pnl), default=None)
    max_loss = min(traded, key=lambda r: float(r.net_pnl), default=None)

    by_day: Dict[str, List[TradeResult]] = {}
    for r in traded:
        by_day.setdefault(r.day_of_week, []).append(r)

    lines = [
        "# 2025 Intraday Joint-SL Short Strangle Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Entry time: `{args.entry_time}` (sell OTM CE + PE)",
        f"- Exit time: `{args.exit_time}` if no SL hit (day close)",
        f"- Stop loss: `{args.sl_multiple}x` entry premium per leg",
        "- Joint SL rule: if either leg hits SL, exit BOTH immediately at same candle",
        "  - SL leg: exits at stop price (or candle open if gap)",
        "  - Partner leg: exits at current candle open",
        "- Expiry rule: expiry day → next week; otherwise current week",
        "- Premium bands (primary → fallback):",
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
        f"- Days SL triggered: `{sl_days}`",
        f"- Days closed at {args.exit_time}: `{no_sl_days}`",
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
        d_net = sum(float(r.net_pnl) for r in day_results)
        d_brok = sum(float(r.brokerage) for r in day_results)
        d_win = sum(1 for r in day_results if float(r.net_pnl) > 0)
        d_loss = sum(1 for r in day_results if float(r.net_pnl) < 0)
        d_sl = sum(1 for r in day_results if r.sl_trigger != "none")
        lines.extend([
            f"### {d}",
            f"- Trades: `{len(day_results)}`  Win: `{d_win}`  Loss: `{d_loss}`  SL hits: `{d_sl}`",
            f"- Net P/L: `{fmt(d_net)}`  Gross: `{fmt(d_gross)}`  Brokerage: `{fmt(d_brok)}`",
            "",
        ])

    lines.extend(["## Exceptions", ""])
    if skipped:
        for r in skipped:
            lines.append(f"- `{r.entry_date}` ({r.day_of_week}): `{r.skip_reason}`. {r.remarks}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Remarks",
        "",
        "- SL fill rule: gap open above SL → fill at candle open; intrabar high crosses SL → fill at SL price.",
        "- Partner leg fill: exits at the same candle's open when SL fires on the other leg.",
        "- Exact timestamp matching; no nearest-candle fallback.",
        "- NIFTY spot file is the source of truth for the trading calendar.",
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
