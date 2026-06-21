#!/usr/bin/env python3
"""
Intraday ATM Straddle with 25-period 15m MA filter.

Entry at 09:40: sell ATM CE/PE only if price < 25-period 15m MA (checked at 09:15 candle).
If only one leg qualifies, sell only that leg (partial straddle).
SL: exit a leg when its price crosses above the rolling 25-period 15m MA during the day.
Exit all open legs at 15:20 (1m data) if SL not triggered.
No re-entry after SL or day close.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

IST_SUFFIX = "+05:30"
BASE_FILENAME = "intraday_atm_straddle_ma25_2025"
DAYWISE_FILENAME = f"{BASE_FILENAME}_daywise.csv"
SUMMARY_FILENAME = f"{BASE_FILENAME}_summary.md"
LOG_FILENAME = f"{BASE_FILENAME}.log"

MA_PERIOD = 25
MA_CHECK_CANDLE_TIME = "09:15"  # last complete 15m candle before 09:40 entry
MONITOR_START_TIME = "09:45"    # first 15m candle to check after 09:40 entry
MONITOR_END_TIME = "15:15"      # last 15m candle before 15:20 exit

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@dataclass
class PriceRow1m:
    timestamp: str
    open_value: float
    open_text: str
    high_value: float
    low_value: float


@dataclass
class PriceRow15m:
    timestamp: str
    open_value: float
    high_value: float
    close_value: float


@dataclass
class Contract1mData:
    path: Path
    rows_by_timestamp: Dict[str, PriceRow1m]


@dataclass
class Contract15mData:
    path: Path
    sorted_rows: List[PriceRow15m]
    rows_by_timestamp: Dict[str, PriceRow15m]


@dataclass
class TradeResult:
    entry_date: str
    day_of_week: str
    status: str          # TRADED, PARTIAL, SKIPPED
    skip_reason: str
    expiry_date: str
    expiry_type: str
    spot_entry_timestamp: str
    spot_entry_open: str
    atm_strike: str
    ce_entered: str
    ce_contract_file: str
    ce_entry_timestamp: str
    ce_entry_open: str
    ce_ma_at_entry: str
    ce_exit_timestamp: str
    ce_exit_price: str
    ce_exit_reason: str
    ce_points_pnl: str
    ce_gross_pnl: str
    ce_brokerage: str
    ce_net_pnl: str
    pe_entered: str
    pe_contract_file: str
    pe_entry_timestamp: str
    pe_entry_open: str
    pe_ma_at_entry: str
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
        description="Backtest intraday ATM straddle with 25-period 15m MA filter.",
    )
    parser.add_argument("--spot-file", type=Path,
                        default=repo_root / "nifty" / "NIFTY50_INDEX_1m_2025.csv")
    parser.add_argument("--options-dir", type=Path, default=repo_root / "Options_2025")
    parser.add_argument("--options-15m-dir", type=Path, default=repo_root / "Options_2025_15m")
    parser.add_argument("--results-dir", type=Path,
                        default=repo_root / "backtesting" / "results")
    parser.add_argument("--entry-time", default="09:40")
    parser.add_argument("--exit-time", default="15:20")
    parser.add_argument("--ma-period", type=int, default=MA_PERIOD)
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


def expiry_suffix(expiry_date: str) -> str:
    dt = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
    return dt.strftime("%d_%b_%y").upper()


def load_spot_data(
    spot_file: Path,
    entry_time: str,
) -> Tuple[List[str], Dict[str, List[str]], Dict[str, Tuple[float, str]]]:
    trading_days: List[str] = []
    timestamps_by_day: Dict[str, List[str]] = {}
    spot_open_by_day: Dict[str, Tuple[float, str]] = {}
    entry_marker = f"T{entry_time}:00"

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
            if day not in spot_open_by_day and entry_marker in ts:
                spot_open_by_day[day] = (float(row["open"]), row["open"])

    return trading_days, timestamps_by_day, spot_open_by_day


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


def load_contract_1m(
    path: Path,
    cache: Dict[Path, Optional[Contract1mData]],
) -> Optional[Contract1mData]:
    if path in cache:
        return cache[path]
    if not path.exists():
        cache[path] = None
        return None
    rows: Dict[str, PriceRow1m] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if not row.get("open"):
                continue
            ts = row["timestamp"]
            rows[ts] = PriceRow1m(
                timestamp=ts,
                open_value=float(row["open"]),
                open_text=row["open"],
                high_value=float(row["high"]),
                low_value=float(row["low"]),
            )
    data = Contract1mData(path=path, rows_by_timestamp=rows)
    cache[path] = data
    return data


def load_contract_15m(
    path: Path,
    cache: Dict[Path, Optional[Contract15mData]],
) -> Optional[Contract15mData]:
    if path in cache:
        return cache[path]
    if not path.exists():
        cache[path] = None
        return None
    sorted_rows: List[PriceRow15m] = []
    rows_by_ts: Dict[str, PriceRow15m] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if not row.get("open"):
                continue
            ts = row["timestamp"]
            pr = PriceRow15m(
                timestamp=ts,
                open_value=float(row["open"]),
                high_value=float(row["high"]),
                close_value=float(row["close"]),
            )
            sorted_rows.append(pr)
            rows_by_ts[ts] = pr
    sorted_rows.sort(key=lambda r: r.timestamp)
    data = Contract15mData(path=path, sorted_rows=sorted_rows, rows_by_timestamp=rows_by_ts)
    cache[path] = data
    return data


def compute_ma(sorted_rows: List[PriceRow15m], up_to_ts: str, period: int) -> Optional[float]:
    """Simple MA of closes for the most recent `period` rows ending at up_to_ts (inclusive)."""
    idx = None
    for i, row in enumerate(sorted_rows):
        if row.timestamp == up_to_ts:
            idx = i
            break
    if idx is None:
        return None
    start = max(0, idx - period + 1)
    window = sorted_rows[start:idx + 1]
    if len(window) < period:
        return None
    return sum(r.close_value for r in window) / period


def generate_monitoring_timestamps(date: str, from_time: str, to_time: str) -> List[str]:
    """Generate 15m IST timestamps on date from from_time to to_time inclusive."""
    fh, fm = map(int, from_time.split(":"))
    th, tm = map(int, to_time.split(":"))
    result = []
    h, m = fh, fm
    while (h * 60 + m) <= (th * 60 + tm):
        result.append(f"{date}T{h:02d}:{m:02d}:00{IST_SUFFIX}")
        m += 15
        if m >= 60:
            m -= 60
            h += 1
    return result


def _leg_result(
    entry_price: float,
    exit_price: float,
    exit_reason: str,
    exit_ts: str,
    slippage: float,
    contract_multiplier: int,
    brokerage_per_order: float,
) -> Tuple[str, str, str, str, str, str, str]:
    """Returns: exit_ts, exit_price, exit_reason, points_pnl, gross_pnl, brokerage, net_pnl"""
    points = entry_price - exit_price - 2 * slippage
    gross = points * contract_multiplier
    brok = brokerage_per_order * 2
    return exit_ts, fmt(exit_price), exit_reason, fmt(points), fmt(gross), fmt(brok), fmt(gross - brok)


def not_entered_leg() -> Tuple[str, str, str, str, str, str, str]:
    return "", "", "not_entered", "0.00", "0.00", "0.00", "0.00"


def resolve_leg_ma(
    contract_1m: Contract1mData,
    contract_15m: Contract15mData,
    entry_price: float,
    exit_timestamp_1m: str,
    monitoring_timestamps: List[str],
    slippage: float,
    contract_multiplier: int,
    brokerage_per_order: float,
    ma_period: int,
) -> Tuple[str, str, str, str, str, str, str]:
    """Resolve a single leg: SL when price crosses above rolling MA, else exit at day close."""
    for ts in monitoring_timestamps:
        row_15m = contract_15m.rows_by_timestamp.get(ts)
        if row_15m is None:
            continue
        ma = compute_ma(contract_15m.sorted_rows, ts, ma_period)
        if ma is None:
            continue

        # Gap open at or above MA
        if row_15m.open_value >= ma:
            return _leg_result(entry_price, row_15m.open_value, "ma_gap_sl", ts,
                               slippage, contract_multiplier, brokerage_per_order)

        # Intrabar cross above MA
        if row_15m.high_value >= ma:
            return _leg_result(entry_price, ma, "ma_sl", ts,
                               slippage, contract_multiplier, brokerage_per_order)

    # No SL triggered — exit at 15:20 using 1m data
    row_1m = contract_1m.rows_by_timestamp.get(exit_timestamp_1m)
    if row_1m:
        return _leg_result(entry_price, row_1m.open_value, "day_close", exit_timestamp_1m,
                           slippage, contract_multiplier, brokerage_per_order)

    # Fallback: last available 15m close
    for ts in reversed(monitoring_timestamps):
        row_15m = contract_15m.rows_by_timestamp.get(ts)
        if row_15m:
            return _leg_result(entry_price, row_15m.close_value, "missing_exit_candle", ts,
                               slippage, contract_multiplier, brokerage_per_order)

    return _leg_result(entry_price, entry_price, "missing_exit_candle", exit_timestamp_1m,
                       slippage, contract_multiplier, brokerage_per_order)


def empty_result(
    entry_date: str, day_of_week: str, skip_reason: str,
    expiry_date: str, expiry_type: str,
    spot_entry_timestamp: str, spot_entry_open: str,
    atm_strike: str, remarks: str,
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date, day_of_week=day_of_week,
        status="SKIPPED", skip_reason=skip_reason,
        expiry_date=expiry_date, expiry_type=expiry_type,
        spot_entry_timestamp=spot_entry_timestamp, spot_entry_open=spot_entry_open,
        atm_strike=atm_strike,
        ce_entered="no", ce_contract_file="", ce_entry_timestamp="", ce_entry_open="",
        ce_ma_at_entry="", ce_exit_timestamp="", ce_exit_price="", ce_exit_reason="",
        ce_points_pnl="0.00", ce_gross_pnl="0.00", ce_brokerage="0.00", ce_net_pnl="0.00",
        pe_entered="no", pe_contract_file="", pe_entry_timestamp="", pe_entry_open="",
        pe_ma_at_entry="", pe_exit_timestamp="", pe_exit_price="", pe_exit_reason="",
        pe_points_pnl="0.00", pe_gross_pnl="0.00", pe_brokerage="0.00", pe_net_pnl="0.00",
        gross_pnl="0.00", brokerage="0.00", net_pnl="0.00", remarks=remarks,
    )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, timestamps_by_day, spot_open_by_day = load_spot_data(
        args.spot_file, args.entry_time
    )
    expiries, expiry_set = load_expiry_folders(args.options_dir)
    cache_1m: Dict[Path, Optional[Contract1mData]] = {}
    cache_15m: Dict[Path, Optional[Contract15mData]] = {}
    contract_multiplier = args.lot_size * args.lots
    results: List[TradeResult] = []

    try:
        for entry_date in trading_days:
            weekday = datetime.date.fromisoformat(entry_date).weekday()
            if weekday >= 5:
                continue
            day_name = WEEKDAY_NAMES[weekday]
            entry_timestamp = build_timestamp(entry_date, args.entry_time)
            exit_timestamp = build_timestamp(entry_date, args.exit_time)
            ma_check_timestamp = build_timestamp(entry_date, MA_CHECK_CANDLE_TIME)
            monitoring_timestamps = generate_monitoring_timestamps(
                entry_date, MONITOR_START_TIME, MONITOR_END_TIME,
            )

            day_timestamps = timestamps_by_day.get(entry_date, [])
            if entry_timestamp not in day_timestamps:
                results.append(empty_result(
                    entry_date, day_name, "missing_spot_entry", "", "",
                    entry_timestamp, "", "", f"No spot candle at {entry_timestamp}.",
                ))
                continue

            spot_open = spot_open_by_day.get(entry_date)
            if not spot_open:
                results.append(empty_result(
                    entry_date, day_name, "missing_spot_open", "", "",
                    entry_timestamp, "", "", "Spot open price unavailable.",
                ))
                continue

            spot_open_val, spot_open_text = spot_open

            is_expiry_day = entry_date in expiry_set
            if is_expiry_day:
                expiry_date = next_expiry_strictly_after(expiries, entry_date)
                expiry_type = "next_week"
            else:
                expiry_date = first_expiry_on_or_after(expiries, entry_date)
                expiry_type = "current_week"

            if expiry_date is None:
                results.append(empty_result(
                    entry_date, day_name, "no_expiry_found", "", expiry_type,
                    entry_timestamp, spot_open_text, "", "No suitable expiry found.",
                ))
                continue

            atm_strike = round_to_nearest_50(spot_open_val)
            suffix = expiry_suffix(expiry_date)
            ce_fname = f"NIFTY_{atm_strike}_CE_{suffix}.csv"
            pe_fname = f"NIFTY_{atm_strike}_PE_{suffix}.csv"

            ce_path_1m = args.options_dir / expiry_date / ce_fname
            pe_path_1m = args.options_dir / expiry_date / pe_fname
            ce_path_15m = args.options_15m_dir / expiry_date / ce_fname
            pe_path_15m = args.options_15m_dir / expiry_date / pe_fname

            ce_1m = load_contract_1m(ce_path_1m, cache_1m)
            pe_1m = load_contract_1m(pe_path_1m, cache_1m)
            ce_15m = load_contract_15m(ce_path_15m, cache_15m)
            pe_15m = load_contract_15m(pe_path_15m, cache_15m)

            missing = []
            if ce_1m is None:
                missing.append(ce_fname)
            if pe_1m is None:
                missing.append(pe_fname)
            if ce_15m is None:
                missing.append(f"15m/{ce_fname}")
            if pe_15m is None:
                missing.append(f"15m/{pe_fname}")
            if missing:
                results.append(empty_result(
                    entry_date, day_name, "missing_contract_file",
                    expiry_date, expiry_type, entry_timestamp, spot_open_text,
                    str(atm_strike), f"Missing: {', '.join(missing)}",
                ))
                logger.info("SKIPPED date=%s reason=missing_contract atm=%s", entry_date, atm_strike)
                continue

            # MA check at 09:15 candle (last complete 15m bar before 09:40 entry)
            ce_ma = compute_ma(ce_15m.sorted_rows, ma_check_timestamp, args.ma_period)
            pe_ma = compute_ma(pe_15m.sorted_rows, ma_check_timestamp, args.ma_period)

            if ce_ma is None and pe_ma is None:
                results.append(empty_result(
                    entry_date, day_name, "insufficient_ma_data",
                    expiry_date, expiry_type, entry_timestamp, spot_open_text,
                    str(atm_strike), f"Fewer than {args.ma_period} 15m candles available for both legs.",
                ))
                logger.info("SKIPPED date=%s reason=insufficient_ma_data atm=%s", entry_date, atm_strike)
                continue

            # Entry prices from 1m data at 09:40
            ce_entry_row = ce_1m.rows_by_timestamp.get(entry_timestamp)
            pe_entry_row = pe_1m.rows_by_timestamp.get(entry_timestamp)

            ce_qualifies = (
                ce_ma is not None
                and ce_entry_row is not None
                and ce_entry_row.open_value < ce_ma
            )
            pe_qualifies = (
                pe_ma is not None
                and pe_entry_row is not None
                and pe_entry_row.open_value < pe_ma
            )

            if not ce_qualifies and not pe_qualifies:
                ce_price_str = fmt(ce_entry_row.open_value) if ce_entry_row else "N/A"
                pe_price_str = fmt(pe_entry_row.open_value) if pe_entry_row else "N/A"
                ce_ma_str = fmt(ce_ma) if ce_ma is not None else "N/A"
                pe_ma_str = fmt(pe_ma) if pe_ma is not None else "N/A"
                results.append(empty_result(
                    entry_date, day_name, "no_ma_signal",
                    expiry_date, expiry_type, entry_timestamp, spot_open_text,
                    str(atm_strike),
                    f"CE price {ce_price_str} >= MA {ce_ma_str}; PE price {pe_price_str} >= MA {pe_ma_str}",
                ))
                logger.info(
                    "SKIPPED date=%s reason=no_ma_signal atm=%s ce=%s/ma=%s pe=%s/ma=%s",
                    entry_date, atm_strike, ce_price_str, ce_ma_str, pe_price_str, pe_ma_str,
                )
                continue

            # Resolve CE leg
            if ce_qualifies:
                (ce_exit_ts, ce_exit_price, ce_exit_reason,
                 ce_pts, ce_gross, ce_brok, ce_net) = resolve_leg_ma(
                    ce_1m, ce_15m, ce_entry_row.open_value, exit_timestamp,
                    monitoring_timestamps, args.slippage_points_per_order,
                    contract_multiplier, args.brokerage_per_order, args.ma_period,
                )
                ce_entered = "yes"
                ce_entry_open = ce_entry_row.open_text
                ce_ma_at_entry = fmt(ce_ma)
            else:
                (ce_exit_ts, ce_exit_price, ce_exit_reason,
                 ce_pts, ce_gross, ce_brok, ce_net) = not_entered_leg()
                ce_entered = "no"
                ce_entry_open = ""
                ce_ma_at_entry = fmt(ce_ma) if ce_ma is not None else ""

            # Resolve PE leg
            if pe_qualifies:
                (pe_exit_ts, pe_exit_price, pe_exit_reason,
                 pe_pts, pe_gross, pe_brok, pe_net) = resolve_leg_ma(
                    pe_1m, pe_15m, pe_entry_row.open_value, exit_timestamp,
                    monitoring_timestamps, args.slippage_points_per_order,
                    contract_multiplier, args.brokerage_per_order, args.ma_period,
                )
                pe_entered = "yes"
                pe_entry_open = pe_entry_row.open_text
                pe_ma_at_entry = fmt(pe_ma)
            else:
                (pe_exit_ts, pe_exit_price, pe_exit_reason,
                 pe_pts, pe_gross, pe_brok, pe_net) = not_entered_leg()
                pe_entered = "no"
                pe_entry_open = ""
                pe_ma_at_entry = fmt(pe_ma) if pe_ma is not None else ""

            gross_pnl = float(ce_gross) + float(pe_gross)
            total_brok = float(ce_brok) + float(pe_brok)
            net_pnl = gross_pnl - total_brok

            status = "TRADED" if (ce_qualifies and pe_qualifies) else "PARTIAL"

            result = TradeResult(
                entry_date=entry_date,
                day_of_week=day_name,
                status=status,
                skip_reason="",
                expiry_date=expiry_date,
                expiry_type=expiry_type,
                spot_entry_timestamp=entry_timestamp,
                spot_entry_open=spot_open_text,
                atm_strike=str(atm_strike),
                ce_entered=ce_entered,
                ce_contract_file=ce_fname,
                ce_entry_timestamp=entry_timestamp if ce_qualifies else "",
                ce_entry_open=ce_entry_open,
                ce_ma_at_entry=ce_ma_at_entry,
                ce_exit_timestamp=ce_exit_ts,
                ce_exit_price=ce_exit_price,
                ce_exit_reason=ce_exit_reason,
                ce_points_pnl=ce_pts,
                ce_gross_pnl=ce_gross,
                ce_brokerage=ce_brok,
                ce_net_pnl=ce_net,
                pe_entered=pe_entered,
                pe_contract_file=pe_fname,
                pe_entry_timestamp=entry_timestamp if pe_qualifies else "",
                pe_entry_open=pe_entry_open,
                pe_ma_at_entry=pe_ma_at_entry,
                pe_exit_timestamp=pe_exit_ts,
                pe_exit_price=pe_exit_price,
                pe_exit_reason=pe_exit_reason,
                pe_points_pnl=pe_pts,
                pe_gross_pnl=pe_gross,
                pe_brokerage=pe_brok,
                pe_net_pnl=pe_net,
                gross_pnl=fmt(gross_pnl),
                brokerage=fmt(total_brok),
                net_pnl=fmt(net_pnl),
                remarks="",
            )
            results.append(result)

            sl_tags = []
            if "sl" in ce_exit_reason:
                sl_tags.append(f"CE_SL@{ce_exit_ts[11:16]}")
            if "sl" in pe_exit_reason:
                sl_tags.append(f"PE_SL@{pe_exit_ts[11:16]}")
            logger.info(
                "%s date=%s day=%s expiry=%s atm=%s ce=%s pe=%s sl=[%s] net=%s",
                status, entry_date, day_name, expiry_date, atm_strike,
                ce_entry_open or "skip", pe_entry_open or "skip",
                ",".join(sl_tags) if sl_tags else "none", fmt(net_pnl),
            )

    except Exception:
        logger.exception("ERROR unexpected failure")
        raise
    finally:
        active = sum(1 for r in results if r.status in ("TRADED", "PARTIAL"))
        skipped = sum(1 for r in results if r.status == "SKIPPED")
        logger.info("COMPLETED traded=%s skipped=%s total=%s", active, skipped, len(results))
        close_logger(logger)

    return results


def write_daywise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date", "day_of_week", "status", "skip_reason",
        "expiry_date", "expiry_type",
        "spot_entry_timestamp", "spot_entry_open", "atm_strike",
        "ce_entered", "ce_contract_file", "ce_entry_timestamp", "ce_entry_open", "ce_ma_at_entry",
        "ce_exit_timestamp", "ce_exit_price", "ce_exit_reason",
        "ce_points_pnl", "ce_gross_pnl", "ce_brokerage", "ce_net_pnl",
        "pe_entered", "pe_contract_file", "pe_entry_timestamp", "pe_entry_open", "pe_ma_at_entry",
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
    active = [r for r in results if r.status in ("TRADED", "PARTIAL")]
    skipped = [r for r in results if r.status == "SKIPPED"]
    traded_full = [r for r in active if r.status == "TRADED"]
    traded_partial = [r for r in active if r.status == "PARTIAL"]
    gross_total = sum(float(r.gross_pnl) for r in active)
    brokerage_total = sum(float(r.brokerage) for r in active)
    net_total = sum(float(r.net_pnl) for r in active)
    max_dd, peak_profit = compute_equity_stats([float(r.net_pnl) for r in active])
    winning_days = sum(1 for r in active if float(r.net_pnl) > 0)
    losing_days = sum(1 for r in active if float(r.net_pnl) < 0)

    ce_sl = sum(1 for r in active if "sl" in r.ce_exit_reason)
    pe_sl = sum(1 for r in active if "sl" in r.pe_exit_reason)

    max_profit_day = max(active, key=lambda r: float(r.net_pnl), default=None)
    max_loss_day = min(active, key=lambda r: float(r.net_pnl), default=None)

    by_day: Dict[str, List[TradeResult]] = {}
    for r in active:
        by_day.setdefault(r.day_of_week, []).append(r)

    skip_by_reason: Dict[str, int] = {}
    for r in skipped:
        skip_by_reason[r.skip_reason] = skip_by_reason.get(r.skip_reason, 0) + 1

    lines = [
        "# 2025 Intraday ATM Straddle — 25-period 15m MA Filter",
        "",
        "## Strategy Details",
        "",
        f"- Entry time: `{args.entry_time}` — sell ATM CE/PE only if price < {args.ma_period}-period 15m MA",
        f"- Exit time: `{args.exit_time}` if SL not triggered (1m candle open)",
        f"- MA period: `{args.ma_period}` candles on 15-minute chart",
        f"- MA check candle: `{MA_CHECK_CANDLE_TIME}` (last complete 15m bar before entry)",
        "- Entry condition: option open at 09:40 < 25-period MA → sell; else skip that leg",
        "- SL rule: exit when price crosses above rolling 25-period 15m MA (dynamic level)",
        "- SL fill: gap open ≥ MA → fill at candle open; intrabar high ≥ MA → fill at MA",
        "- Partial straddle: only qualifying legs are sold",
        "- ATM rule: nearest 50 to spot open at 09:40",
        "- Expiry rule: expiry day → next week; otherwise current week",
        f"- Contract multiplier: {args.lot_size} × {args.lots} = {args.lot_size * args.lots} per point",
        f"- Slippage: {fmt(args.slippage_points_per_order)} pts per order (entry + exit = 2× per leg)",
        f"- Brokerage: Rs {fmt(args.brokerage_per_order)} per order; partial = Rs {fmt(args.brokerage_per_order * 2)}, full = Rs {fmt(args.brokerage_per_order * 4)}",
        "- Data: 1m from `Options_2025/` (entry/exit prices); 15m from `Options_2025_15m/` (MA + SL)",
        "",
        "## Results Summary",
        "",
        f"- Total active days: `{len(active)}` (full straddle: `{len(traded_full)}`, partial: `{len(traded_partial)}`)",
        f"- Total skipped days: `{len(skipped)}`",
        f"- Winning days: `{winning_days}`",
        f"- Losing days: `{losing_days}`",
        f"- Days CE SL hit: `{ce_sl}`",
        f"- Days PE SL hit: `{pe_sl}`",
        f"- Total Gross P/L: `{fmt(gross_total)}`",
        f"- Total Brokerage: `{fmt(brokerage_total)}`",
        f"- Total Net P/L: `{fmt(net_total)}`",
        (f"- Max profit day: `{max_profit_day.entry_date}` ({max_profit_day.day_of_week})"
         f" net `{max_profit_day.net_pnl}`" if max_profit_day else "- Max profit day: N/A"),
        (f"- Max loss day: `{max_loss_day.entry_date}` ({max_loss_day.day_of_week})"
         f" net `{max_loss_day.net_pnl}`" if max_loss_day else "- Max loss day: N/A"),
        f"- Peak cumulative profit: `{fmt(peak_profit)}`",
        f"- Max drawdown: `{fmt(max_dd)}`",
        "",
        "## Results by Day of Week",
        "",
    ]

    for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        day_results = by_day.get(d, [])
        if not day_results:
            lines += [f"### {d}: no trades", ""]
            continue
        d_gross = sum(float(r.gross_pnl) for r in day_results)
        d_net = sum(float(r.net_pnl) for r in day_results)
        d_brok = sum(float(r.brokerage) for r in day_results)
        d_win = sum(1 for r in day_results if float(r.net_pnl) > 0)
        d_loss = sum(1 for r in day_results if float(r.net_pnl) < 0)
        d_ce_sl = sum(1 for r in day_results if "sl" in r.ce_exit_reason)
        d_pe_sl = sum(1 for r in day_results if "sl" in r.pe_exit_reason)
        d_partial = sum(1 for r in day_results if r.status == "PARTIAL")
        lines += [
            f"### {d}",
            (f"- Trades: `{len(day_results)}`  Full: `{len(day_results) - d_partial}`  "
             f"Partial: `{d_partial}`  Win: `{d_win}`  Loss: `{d_loss}`  "
             f"CE-SL: `{d_ce_sl}`  PE-SL: `{d_pe_sl}`"),
            f"- Net P/L: `{fmt(d_net)}`  Gross: `{fmt(d_gross)}`  Brokerage: `{fmt(d_brok)}`",
            "",
        ]

    lines += [
        "## Skipped Summary",
        "",
    ]
    for reason, count in sorted(skip_by_reason.items(), key=lambda x: -x[1]):
        lines.append(f"- `{reason}`: {count} days")

    lines += [
        "",
        "## Exceptions",
        "",
    ]
    if skipped:
        for r in skipped:
            lines.append(f"- `{r.entry_date}` ({r.day_of_week}): `{r.skip_reason}`. {r.remarks}")
    else:
        lines.append("- None")

    lines += [
        "",
        "## Remarks",
        "",
        "- 25-period MA is computed from `Options_2025_15m/` (15-minute bars).",
        f"- MA at entry uses the `{MA_CHECK_CANDLE_TIME}` candle — last complete 15m bar before 09:40.",
        f"- SL monitoring starts from `{MONITOR_START_TIME}` candle; the 09:40–09:44 window is unmonitored.",
        "- MA is re-computed at every 15m candle intraday (rolling window — dynamic SL level).",
        "- If MA unavailable at a monitoring candle, that candle is skipped for SL purposes.",
        "- Partial straddle: if only one leg is below MA, only that leg is sold.",
        "- NIFTY spot file is source of truth for the trading-day calendar.",
    ]

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
