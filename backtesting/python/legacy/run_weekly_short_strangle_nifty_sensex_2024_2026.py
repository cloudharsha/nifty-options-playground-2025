#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

IST_SUFFIX = "+05:30"
BASE_FILENAME = "weekly_strangle_nifty_sensex_2024_2026"
DAYWISE_FILENAME = f"{BASE_FILENAME}_daywise.csv"
SUMMARY_FILENAME = f"{BASE_FILENAME}_summary.md"
LOG_FILENAME = f"{BASE_FILENAME}.log"

SENSEX_LOT_SIZE = 10
SENSEX_STRIKE_INTERVAL = 100
NIFTY_STRIKE_INTERVAL = 50


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
    side: str
    strike: int
    entry_price: str
    stop_price: str
    exit_price: str
    exit_timestamp: str
    exit_reason: str
    points_pnl: str
    gross_pnl: str
    net_pnl: str
    failure_reason: str
    remarks: str


@dataclass
class DayResult:
    entry_date: str
    status: str
    skip_reason: str
    index: str
    active_expiry: str
    spot: str
    atm_strike: str
    ce_strike: str
    ce_entry_price: str
    ce_stop_price: str
    ce_exit_price: str
    ce_exit_timestamp: str
    ce_exit_reason: str
    ce_points_pnl: str
    ce_gross_pnl: str
    ce_net_pnl: str
    ce_failure_reason: str
    pe_strike: str
    pe_entry_price: str
    pe_stop_price: str
    pe_exit_price: str
    pe_exit_timestamp: str
    pe_exit_reason: str
    pe_points_pnl: str
    pe_gross_pnl: str
    pe_net_pnl: str
    pe_failure_reason: str
    lot_size: str
    lots: str
    total_qty: str
    combined_entry_credit: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Backtest a daily intraday short strangle alternating between Nifty and Sensex "
            "weekly expiry options. Enters at 09:30, exits at 15:20 or on 2× stop-loss per leg. "
            "Nifty uses a 15m spot file for ATM; Sensex spot is inferred from option prices."
        ),
    )
    parser.add_argument(
        "--nifty-spot-file",
        type=Path,
        default=repo_root / "nifty" / "NIFTY50_INDEX_15m_last_4y.csv",
        help="15-minute NIFTY spot CSV. Provides trading calendar and Nifty ATM price.",
    )
    parser.add_argument(
        "--nifty-options-dir",
        type=Path,
        default=repo_root / "NiftyOptions_2020_2026" / "Options",
        help="Directory containing NIFTY expiry-date sub-folders with 1-minute option CSVs.",
    )
    parser.add_argument(
        "--sensex-options-dir",
        type=Path,
        default=repo_root / "SensexOptions_2024_2026" / "Options",
        help="Directory containing SENSEX expiry-date sub-folders with 1-minute option CSVs.",
    )
    parser.add_argument(
        "--start-date",
        default="2024-10-01",
        help="First trading day to include (YYYY-MM-DD). Defaults to 2024-10-01.",
    )
    parser.add_argument(
        "--end-date",
        default="",
        help="Last trading day to include (YYYY-MM-DD). Defaults to last available day.",
    )
    parser.add_argument(
        "--atm-time",
        default="09:15",
        help="Spot candle time used to determine Nifty ATM (default: 09:15, first 15m bar open).",
    )
    parser.add_argument(
        "--entry-time",
        default="09:30",
        help="Options entry candle time (default: 09:30).",
    )
    parser.add_argument(
        "--exit-time",
        default="15:20",
        help="Scheduled end-of-day exit candle time (default: 15:20).",
    )
    parser.add_argument(
        "--nifty-offset",
        type=int,
        default=200,
        help="Points from spot for Nifty CE and PE strikes (default: 200).",
    )
    parser.add_argument(
        "--sensex-offset",
        type=int,
        default=600,
        help="Points from spot for Sensex CE and PE strikes (default: 600).",
    )
    parser.add_argument(
        "--stop-loss-multiple",
        type=float,
        default=2.0,
        help="Exit leg when option price reaches entry × this multiple (default: 2.0).",
    )
    parser.add_argument(
        "--lots",
        type=int,
        default=1,
        help="Number of lots per side (default: 1).",
    )
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=repo_root / "backtesting" / "results",
    )
    return parser.parse_args()


def fmt(value: float) -> str:
    return f"{value:.2f}"


def build_timestamp(day: str, time_text: str) -> str:
    hour, minute = time_text.split(":")
    return f"{day}T{hour}:{minute}:00{IST_SUFFIX}"


def round_to_nearest_n(price: float, n: int) -> int:
    return int(round(price / n) * n)


def expiry_suffix(expiry_date: str) -> str:
    dt = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
    return dt.strftime("%d_%b_%y").upper()


def build_day_timestamps(day: str) -> List[str]:
    result: List[str] = []
    start_dt = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 9, 15)
    for minute in range(375):
        dt = start_dt + datetime.timedelta(minutes=minute)
        result.append(f"{day}T{dt.strftime('%H:%M')}:00{IST_SUFFIX}")
    return result


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


def lot_size_for_nifty_expiry(expiry_date: str) -> int:
    if expiry_date < "2021-10-07":
        return 75
    if expiry_date <= "2024-04-25":
        return 50
    if expiry_date <= "2024-11-21":
        return 25
    if expiry_date <= "2025-12-30":
        return 75
    return 65


def load_spot_data(
    spot_file: Path, atm_time: str, start_date: str, end_date: str
) -> Tuple[List[str], Dict[str, Optional[PriceRow]]]:
    trading_days: List[str] = []
    atm_row_by_day: Dict[str, Optional[PriceRow]] = {}
    atm_marker = f"T{atm_time}:00"

    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            ts = row["timestamp"]
            day = ts[:10]
            if day < start_date:
                continue
            if end_date and day > end_date:
                break
            if day not in atm_row_by_day:
                atm_row_by_day[day] = None
                trading_days.append(day)
            if atm_marker in ts and atm_row_by_day[day] is None:
                atm_row_by_day[day] = PriceRow(
                    timestamp=ts,
                    open_value=float(row["open"]),
                    open_text=row["open"],
                    high_value=float(row.get("high", row["open"])),
                    low_value=float(row.get("low", row["open"])),
                )

    return trading_days, atm_row_by_day


def load_expiry_folders(options_dir: Path) -> List[str]:
    return sorted(p.name for p in options_dir.iterdir() if p.is_dir())


def first_expiry_on_or_after(expiries: List[str], date: str) -> Optional[str]:
    for e in expiries:
        if e >= date:
            return e
    return None


def load_contract(
    contract_path: Path, cache: Dict[Path, Optional[ContractData]]
) -> Optional[ContractData]:
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


def load_option_open(
    contract_path: Path,
    timestamp: str,
    scan_cache: Dict[Tuple[Path, str], Optional[float]],
) -> Optional[float]:
    """Read only the open price at a single timestamp, with lightweight caching."""
    key = (contract_path, timestamp)
    if key in scan_cache:
        return scan_cache[key]
    if not contract_path.exists():
        scan_cache[key] = None
        return None
    val: Optional[float] = None
    with contract_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row["timestamp"] == timestamp:
                val = float(row["open"])
                break
            if row["timestamp"] > timestamp:
                break
    scan_cache[key] = val
    return val


def find_sensex_spot(
    sensex_options_dir: Path,
    expiry: str,
    entry_timestamp: str,
    scan_cache: Dict[Tuple[Path, str], Optional[float]],
    min_ratio: float = 0.80,
) -> Optional[int]:
    """Find the Sensex synthetic spot by scanning options for the strike where CE ≈ PE."""
    expiry_folder = sensex_options_dir / expiry
    if not expiry_folder.exists():
        return None

    suffix = expiry_suffix(expiry)
    ce_pattern = re.compile(r"^SENSEX_(\d+)_CE_.*\.csv$")

    best_strike: Optional[int] = None
    best_diff: float = float("inf")
    fallback_strike: Optional[int] = None
    fallback_diff: float = float("inf")

    for ce_file in expiry_folder.glob("SENSEX_*_CE_*.csv"):
        m = ce_pattern.match(ce_file.name)
        if not m:
            continue
        strike = int(m.group(1))
        pe_file = expiry_folder / f"SENSEX_{strike}_PE_{suffix}.csv"

        ce_price = load_option_open(ce_file, entry_timestamp, scan_cache)
        pe_price = load_option_open(pe_file, entry_timestamp, scan_cache)

        if ce_price is None or pe_price is None or ce_price <= 0 or pe_price <= 0:
            continue

        diff = abs(ce_price - pe_price)

        if diff < fallback_diff:
            fallback_diff = diff
            fallback_strike = strike

        ratio = min(ce_price, pe_price) / max(ce_price, pe_price)
        if ratio >= min_ratio and diff < best_diff:
            best_diff = diff
            best_strike = strike

    return best_strike if best_strike is not None else fallback_strike


def determine_trade_index(
    day: str,
    current_index: str,
    nifty_expiries: List[str],
    sensex_expiries: List[str],
) -> Tuple[str, Optional[str], Optional[str], str]:
    """Return (index_to_trade, nifty_expiry, sensex_expiry, next_current_index).

    Scheduling rule:
      - Trade whichever index has the closer upcoming expiry.
      - Tie: continue with current_index (Nifty wins at the start).
      - After trading on the expiry day, the caller switches current_index.
    """
    nifty_exp = first_expiry_on_or_after(nifty_expiries, day)
    sensex_exp = first_expiry_on_or_after(sensex_expiries, day)

    if nifty_exp is None and sensex_exp is None:
        return current_index, None, None, current_index

    if nifty_exp is None:
        return "SENSEX", None, sensex_exp, current_index
    if sensex_exp is None:
        return "NIFTY", nifty_exp, None, current_index

    if nifty_exp < sensex_exp:
        next_idx = "SENSEX" if day == nifty_exp else current_index
        return "NIFTY", nifty_exp, sensex_exp, next_idx
    elif sensex_exp < nifty_exp:
        next_idx = "NIFTY" if day == sensex_exp else current_index
        return "SENSEX", nifty_exp, sensex_exp, next_idx
    else:
        # Tie: both expire same day
        next_idx = ("SENSEX" if current_index == "NIFTY" else "NIFTY") if day == nifty_exp else current_index
        return current_index, nifty_exp, sensex_exp, next_idx


def resolve_leg(
    contract: ContractData,
    side: str,
    strike: int,
    entry_timestamp: str,
    exit_timestamp: str,
    day_timestamps: List[str],
    stop_loss_multiple: float,
    slippage: float,
    lot_size: int,
    lots: int,
    brokerage_per_order: float,
) -> LegResult:
    total_qty = lot_size * lots

    entry_row = contract.rows_by_timestamp.get(entry_timestamp)
    if entry_row is None:
        return LegResult(
            side=side, strike=strike,
            entry_price="", stop_price="", exit_price="",
            exit_timestamp="", exit_reason="",
            points_pnl="0.00", gross_pnl="0.00", net_pnl="0.00",
            failure_reason="missing_entry_candle",
            remarks=f"{contract.path.name} has no candle at {entry_timestamp}",
        )

    stop_price = entry_row.open_value * stop_loss_multiple

    try:
        entry_index = day_timestamps.index(entry_timestamp)
        exit_index = day_timestamps.index(exit_timestamp)
    except ValueError as exc:
        return LegResult(
            side=side, strike=strike,
            entry_price=entry_row.open_text, stop_price=fmt(stop_price),
            exit_price="", exit_timestamp="", exit_reason="",
            points_pnl="0.00", gross_pnl="0.00", net_pnl="0.00",
            failure_reason="timestamp_not_in_day",
            remarks=str(exc),
        )

    exit_price: Optional[float] = None
    exit_ts: str = ""
    exit_reason: str = ""

    for ts in day_timestamps[entry_index:exit_index]:
        row = contract.rows_by_timestamp.get(ts)
        if row is None:
            continue

        if row.open_value >= stop_price:
            exit_price = row.open_value
            exit_ts = row.timestamp
            exit_reason = "gap_stop_loss"
            break

        if row.high_value >= stop_price:
            exit_price = stop_price
            exit_ts = row.timestamp
            exit_reason = "stop_loss"
            break

    if exit_price is None:
        exit_row = contract.rows_by_timestamp.get(exit_timestamp)
        if exit_row is None:
            return LegResult(
                side=side, strike=strike,
                entry_price=entry_row.open_text, stop_price=fmt(stop_price),
                exit_price="", exit_timestamp="", exit_reason="",
                points_pnl="0.00", gross_pnl="0.00", net_pnl="0.00",
                failure_reason="missing_exit_candle",
                remarks=f"{contract.path.name} has no candle at {exit_timestamp}",
            )
        exit_price = exit_row.open_value
        exit_ts = exit_row.timestamp
        exit_reason = "day_close"

    points_pnl = entry_row.open_value - exit_price - 2 * slippage
    gross_pnl = points_pnl * total_qty
    brokerage = 2 * brokerage_per_order
    net_pnl = gross_pnl - brokerage

    return LegResult(
        side=side, strike=strike,
        entry_price=entry_row.open_text,
        stop_price=fmt(stop_price),
        exit_price=fmt(exit_price),
        exit_timestamp=exit_ts,
        exit_reason=exit_reason,
        points_pnl=fmt(points_pnl),
        gross_pnl=fmt(gross_pnl),
        net_pnl=fmt(net_pnl),
        failure_reason="",
        remarks="",
    )


def make_skipped_day(
    day: str,
    index: str,
    expiry: str,
    skip_reason: str,
    remarks: str,
) -> DayResult:
    return DayResult(
        entry_date=day, status="SKIPPED", skip_reason=skip_reason,
        index=index, active_expiry=expiry, spot="",
        atm_strike="", ce_strike="", ce_entry_price="", ce_stop_price="",
        ce_exit_price="", ce_exit_timestamp="", ce_exit_reason="",
        ce_points_pnl="0.00", ce_gross_pnl="0.00", ce_net_pnl="0.00",
        ce_failure_reason="",
        pe_strike="", pe_entry_price="", pe_stop_price="",
        pe_exit_price="", pe_exit_timestamp="", pe_exit_reason="",
        pe_points_pnl="0.00", pe_gross_pnl="0.00", pe_net_pnl="0.00",
        pe_failure_reason="",
        lot_size="", lots="", total_qty="", combined_entry_credit="0.00",
        gross_pnl="0.00", brokerage="0.00", net_pnl="0.00",
        remarks=remarks,
    )


def run_backtest(args: argparse.Namespace) -> List[DayResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, atm_row_by_day = load_spot_data(
        args.nifty_spot_file, args.atm_time, args.start_date, args.end_date
    )
    nifty_expiries = load_expiry_folders(args.nifty_options_dir)
    sensex_expiries = load_expiry_folders(args.sensex_options_dir)

    contract_cache: Dict[Path, Optional[ContractData]] = {}
    spot_scan_cache: Dict[Tuple[Path, str], Optional[float]] = {}
    current_index = "NIFTY"
    results: List[DayResult] = []

    try:
        for day in trading_days:
            index_to_trade, nifty_exp, sensex_exp, next_index = determine_trade_index(
                day, current_index, nifty_expiries, sensex_expiries
            )
            active_expiry = nifty_exp if index_to_trade == "NIFTY" else sensex_exp

            if active_expiry is None:
                result = make_skipped_day(day, index_to_trade, "", "no_active_expiry", "")
                results.append(result)
                logger.info("SKIPPED date=%s reason=no_active_expiry", day)
                current_index = next_index
                continue

            entry_timestamp = build_timestamp(day, args.entry_time)
            exit_timestamp = build_timestamp(day, args.exit_time)
            day_timestamps = build_day_timestamps(day)

            if index_to_trade == "NIFTY":
                atm_row = atm_row_by_day.get(day)
                if atm_row is None:
                    result = make_skipped_day(
                        day, "NIFTY", active_expiry,
                        "missing_nifty_spot",
                        f"No {args.atm_time} candle in spot file for {day}.",
                    )
                    results.append(result)
                    logger.info("SKIPPED date=%s index=NIFTY reason=missing_nifty_spot", day)
                    current_index = next_index
                    continue

                spot_price = atm_row.open_value
                spot_text = atm_row.open_text
                lot_size = lot_size_for_nifty_expiry(active_expiry)
                offset = args.nifty_offset
                interval = NIFTY_STRIKE_INTERVAL
                index_prefix = "NIFTY"
                options_dir = args.nifty_options_dir

            else:  # SENSEX
                sensex_spot = find_sensex_spot(
                    args.sensex_options_dir, active_expiry, entry_timestamp, spot_scan_cache
                )
                if sensex_spot is None:
                    result = make_skipped_day(
                        day, "SENSEX", active_expiry,
                        "sensex_spot_not_found",
                        f"No CE≈PE pair found at {entry_timestamp} for expiry {active_expiry}.",
                    )
                    results.append(result)
                    logger.info(
                        "SKIPPED date=%s index=SENSEX expiry=%s reason=sensex_spot_not_found",
                        day, active_expiry,
                    )
                    current_index = next_index
                    continue

                spot_price = float(sensex_spot)
                spot_text = str(sensex_spot)
                lot_size = SENSEX_LOT_SIZE
                offset = args.sensex_offset
                interval = SENSEX_STRIKE_INTERVAL
                index_prefix = "SENSEX"
                options_dir = args.sensex_options_dir

            atm_strike = round_to_nearest_n(spot_price, interval)
            ce_strike = round_to_nearest_n(spot_price + offset, interval)
            pe_strike = round_to_nearest_n(spot_price - offset, interval)
            suffix = expiry_suffix(active_expiry)

            ce_path = options_dir / active_expiry / f"{index_prefix}_{ce_strike}_CE_{suffix}.csv"
            pe_path = options_dir / active_expiry / f"{index_prefix}_{pe_strike}_PE_{suffix}.csv"

            ce_data = load_contract(ce_path, contract_cache)
            pe_data = load_contract(pe_path, contract_cache)

            missing: List[str] = []
            if ce_data is None:
                missing.append(ce_path.name)
            if pe_data is None:
                missing.append(pe_path.name)
            if missing:
                result = make_skipped_day(
                    day, index_to_trade, active_expiry,
                    "missing_contract_file",
                    f"Missing: {', '.join(missing)}",
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s index=%s expiry=%s reason=missing_contract_file files=%s",
                    day, index_to_trade, active_expiry, missing,
                )
                current_index = next_index
                continue

            total_qty = lot_size * args.lots

            ce_leg = resolve_leg(
                contract=ce_data,  # type: ignore[arg-type]
                side="CE",
                strike=ce_strike,
                entry_timestamp=entry_timestamp,
                exit_timestamp=exit_timestamp,
                day_timestamps=day_timestamps,
                stop_loss_multiple=args.stop_loss_multiple,
                slippage=args.slippage_points_per_order,
                lot_size=lot_size,
                lots=args.lots,
                brokerage_per_order=args.brokerage_per_order,
            )
            pe_leg = resolve_leg(
                contract=pe_data,  # type: ignore[arg-type]
                side="PE",
                strike=pe_strike,
                entry_timestamp=entry_timestamp,
                exit_timestamp=exit_timestamp,
                day_timestamps=day_timestamps,
                stop_loss_multiple=args.stop_loss_multiple,
                slippage=args.slippage_points_per_order,
                lot_size=lot_size,
                lots=args.lots,
                brokerage_per_order=args.brokerage_per_order,
            )

            if ce_leg.failure_reason or pe_leg.failure_reason:
                failures = []
                if ce_leg.failure_reason:
                    failures.append(f"CE:{ce_leg.failure_reason}({ce_leg.remarks})")
                if pe_leg.failure_reason:
                    failures.append(f"PE:{pe_leg.failure_reason}({pe_leg.remarks})")
                result = make_skipped_day(
                    day, index_to_trade, active_expiry,
                    "leg_failure",
                    "; ".join(failures),
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s index=%s expiry=%s reason=leg_failure details=%s",
                    day, index_to_trade, active_expiry, failures,
                )
                current_index = next_index
                continue

            ce_entry = float(ce_leg.entry_price)
            pe_entry = float(pe_leg.entry_price)
            combined_credit = ce_entry + pe_entry
            gross_pnl = float(ce_leg.gross_pnl) + float(pe_leg.gross_pnl)
            brokerage = args.brokerage_per_order * 4
            net_pnl = gross_pnl - brokerage

            result = DayResult(
                entry_date=day, status="TRADED", skip_reason="",
                index=index_to_trade, active_expiry=active_expiry,
                spot=spot_text, atm_strike=str(atm_strike),
                ce_strike=str(ce_strike),
                ce_entry_price=ce_leg.entry_price,
                ce_stop_price=ce_leg.stop_price,
                ce_exit_price=ce_leg.exit_price,
                ce_exit_timestamp=ce_leg.exit_timestamp,
                ce_exit_reason=ce_leg.exit_reason,
                ce_points_pnl=ce_leg.points_pnl,
                ce_gross_pnl=ce_leg.gross_pnl,
                ce_net_pnl=ce_leg.net_pnl,
                ce_failure_reason="",
                pe_strike=str(pe_strike),
                pe_entry_price=pe_leg.entry_price,
                pe_stop_price=pe_leg.stop_price,
                pe_exit_price=pe_leg.exit_price,
                pe_exit_timestamp=pe_leg.exit_timestamp,
                pe_exit_reason=pe_leg.exit_reason,
                pe_points_pnl=pe_leg.points_pnl,
                pe_gross_pnl=pe_leg.gross_pnl,
                pe_net_pnl=pe_leg.net_pnl,
                pe_failure_reason="",
                lot_size=str(lot_size),
                lots=str(args.lots),
                total_qty=str(total_qty),
                combined_entry_credit=fmt(combined_credit),
                gross_pnl=fmt(gross_pnl),
                brokerage=fmt(brokerage),
                net_pnl=fmt(net_pnl),
                remarks="",
            )
            results.append(result)
            logger.info(
                "TRADED date=%s index=%s expiry=%s spot=%s atm=%s "
                "ce=%s(entry=%.2f,exit=%.2f,reason=%s) "
                "pe=%s(entry=%.2f,exit=%.2f,reason=%s) "
                "lot_size=%s lots=%s net_pnl=%.2f",
                day, index_to_trade, active_expiry, spot_text, atm_strike,
                ce_strike, ce_entry, float(ce_leg.exit_price), ce_leg.exit_reason,
                pe_strike, pe_entry, float(pe_leg.exit_price), pe_leg.exit_reason,
                lot_size, args.lots, net_pnl,
            )

            current_index = next_index

    except Exception:
        logger.exception("ERROR unexpected failure during backtest")
        raise

    traded = sum(1 for r in results if r.status == "TRADED")
    skipped = sum(1 for r in results if r.status == "SKIPPED")
    logger.info("COMPLETED traded=%s skipped=%s total=%s", traded, skipped, len(results))
    return results


DAYWISE_FIELDS = [
    "entry_date", "status", "skip_reason", "index", "active_expiry",
    "spot", "atm_strike",
    "ce_strike", "ce_entry_price", "ce_stop_price",
    "ce_exit_price", "ce_exit_timestamp", "ce_exit_reason",
    "ce_points_pnl", "ce_gross_pnl", "ce_net_pnl", "ce_failure_reason",
    "pe_strike", "pe_entry_price", "pe_stop_price",
    "pe_exit_price", "pe_exit_timestamp", "pe_exit_reason",
    "pe_points_pnl", "pe_gross_pnl", "pe_net_pnl", "pe_failure_reason",
    "lot_size", "lots", "total_qty", "combined_entry_credit",
    "gross_pnl", "brokerage", "net_pnl", "remarks",
]


def write_daywise_csv(results: List[DayResult], output_path: Path) -> None:
    cumulative = 0.0
    rows = []
    for r in results:
        row = r.__dict__.copy()
        if r.status == "TRADED":
            cumulative += float(r.net_pnl)
        row["cumulative_pnl"] = fmt(cumulative)
        rows.append(row)

    fields = DAYWISE_FIELDS + ["cumulative_pnl"]
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_summary(results: List[DayResult], output_path: Path, args: argparse.Namespace) -> None:
    traded = [r for r in results if r.status == "TRADED"]
    skipped = [r for r in results if r.status == "SKIPPED"]

    nifty_traded = [r for r in traded if r.index == "NIFTY"]
    sensex_traded = [r for r in traded if r.index == "SENSEX"]

    gross_total = sum(float(r.gross_pnl) for r in traded)
    brokerage_total = sum(float(r.brokerage) for r in traded)
    net_total = sum(float(r.net_pnl) for r in traded)
    nifty_net = sum(float(r.net_pnl) for r in nifty_traded)
    sensex_net = sum(float(r.net_pnl) for r in sensex_traded)

    winning_days = sum(1 for r in traded if float(r.net_pnl) > 0)
    losing_days = sum(1 for r in traded if float(r.net_pnl) < 0)

    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in traded:
        cumulative += float(r.net_pnl)
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    stop_loss_days = sum(
        1 for r in traded
        if r.ce_exit_reason in ("stop_loss", "gap_stop_loss")
        or r.pe_exit_reason in ("stop_loss", "gap_stop_loss")
    )

    skip_reasons: Dict[str, int] = {}
    for r in skipped:
        skip_reasons[r.skip_reason] = skip_reasons.get(r.skip_reason, 0) + 1

    lines = [
        f"# Weekly Short Strangle — Nifty + Sensex (2024–2026) Backtest",
        "",
        "## Strategy Details",
        "",
        "- **Structure**: Short strangle — sell CE and PE independently each day",
        f"- **Nifty offset**: {args.nifty_offset} points from spot (rounded to nearest 50)",
        f"- **Sensex offset**: {args.sensex_offset} points from spot (rounded to nearest 100)",
        f"- **Entry**: {args.entry_time} open candle",
        f"- **Exit**: {args.exit_time} open candle, or 2× stop-loss per leg (whichever first)",
        f"- **Stop-loss multiple**: {args.stop_loss_multiple}×",
        f"- **Lots**: {args.lots} per side",
        f"- **Slippage**: {fmt(args.slippage_points_per_order)} pt per order "
        f"({fmt(2 * args.slippage_points_per_order)} pts round-trip per leg)",
        f"- **Brokerage**: Rs {fmt(args.brokerage_per_order)} per order, "
        f"Rs {fmt(args.brokerage_per_order * 4)} per day (4 orders: 2 entries + 2 exits)",
        "- **Scheduling**: Closest upcoming expiry wins; tie → continue current index; "
        "switch index after each expiry day",
        "- **Nifty spot**: 15m file, 09:15 bar open (rounded to nearest 50)",
        "- **Sensex spot**: Synthetic — strike where CE ≈ PE at entry time "
        "(≥80% ratio preferred; min |CE−PE| fallback)",
        f"- **Start date**: {args.start_date}",
        f"- **Nifty options**: `{args.nifty_options_dir.name}`",
        f"- **Sensex options**: `{args.sensex_options_dir.name}`",
        "",
        "## Results Summary",
        "",
        f"- Days processed         : `{len(results)}`",
        f"- Trades executed        : `{len(traded)}`",
        f"  - Nifty trades         : `{len(nifty_traded)}`",
        f"  - Sensex trades        : `{len(sensex_traded)}`",
        f"- Days skipped           : `{len(skipped)}`",
        f"- Winning days           : `{winning_days}`",
        f"- Losing days            : `{losing_days}`",
        f"- Days with SL hit       : `{stop_loss_days}`",
        f"- Gross P&L              : `Rs {fmt(gross_total)}`",
        f"- Total Brokerage        : `Rs {fmt(brokerage_total)}`",
        f"- **Net P&L**            : **`Rs {fmt(net_total)}`**",
        f"  - Nifty net P&L        : `Rs {fmt(nifty_net)}`",
        f"  - Sensex net P&L       : `Rs {fmt(sensex_net)}`",
        f"- Max Drawdown           : `Rs {fmt(max_dd)}`",
        "",
        "## Skip Reason Summary",
        "",
    ]

    if skip_reasons:
        for reason, count in sorted(skip_reasons.items(), key=lambda x: -x[1]):
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- None")

    lines += [
        "",
        "## Notes",
        "",
        "- The Sensex synthetic spot is the strike with the smallest |CE−PE| price difference "
        "at the entry candle, subject to both prices being within 80% of each other. "
        "If no strike meets the ratio threshold, the closest pair is used as fallback.",
        "- Missing monitoring candles (common for illiquid Sensex strikes) are skipped; "
        "the stop-loss check resumes on the next available candle.",
        "- Nifty lot sizes are expiry-aware: 25 (May–Nov 2024), 75 (Nov 2024–Dec 2025), "
        "65 (Jan 2026+). Sensex lot size is fixed at 10.",
        "- Days where the entry or exit candle is missing from the option file are skipped.",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    results = run_backtest(args)

    daywise_path = args.results_dir / DAYWISE_FILENAME
    summary_path = args.results_dir / SUMMARY_FILENAME

    write_daywise_csv(results, daywise_path)
    write_summary(results, summary_path, args)

    traded = sum(1 for r in results if r.status == "TRADED")
    net_total = sum(float(r.net_pnl) for r in results if r.status == "TRADED")
    print(f"Done. {traded}/{len(results)} days traded. Net P&L: Rs {net_total:.2f}")
    print(f"  Daywise : {daywise_path}")
    print(f"  Summary : {summary_path}")
    print(f"  Log     : {args.results_dir / LOG_FILENAME}")


if __name__ == "__main__":
    main()
