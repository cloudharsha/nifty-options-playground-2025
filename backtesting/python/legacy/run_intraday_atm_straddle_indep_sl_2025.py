#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

IST_SUFFIX = "+05:30"
BASE_FILENAME = "intraday_atm_straddle_indep_sl_2025"
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
    low_value: float


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
        description="Backtest intraday ATM straddle with independent 2x SL per leg.",
    )
    parser.add_argument("--spot-file", type=Path,
                        default=repo_root / "nifty" / "NIFTY50_INDEX_1m_2025.csv")
    parser.add_argument("--options-dir", type=Path, default=repo_root / "Options_2025")
    parser.add_argument("--results-dir", type=Path,
                        default=repo_root / "backtesting" / "results")
    parser.add_argument("--entry-time", default="09:20")
    parser.add_argument("--exit-time", default="15:20")
    parser.add_argument("--sl-multiple", type=float, default=2.0)
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


def resolve_leg(
    contract: ContractData,
    entry_row: PriceRow,
    day_timestamps: List[str],
    entry_timestamp: str,
    exit_timestamp: str,
    sl_multiple: float,
    slippage: float,
    contract_multiplier: int,
    brokerage_per_order: float,
) -> Tuple[str, str, str, str, str, str, str]:
    """Returns: exit_ts, exit_price, exit_reason, points_pnl, gross_pnl, brokerage, net_pnl"""
    stop_price = entry_row.open_value * sl_multiple

    try:
        entry_idx = day_timestamps.index(entry_timestamp)
        exit_idx = day_timestamps.index(exit_timestamp)
    except ValueError:
        entry_idx = 0
        exit_idx = len(day_timestamps) - 1

    for ts in day_timestamps[entry_idx:exit_idx + 1]:
        row = contract.rows_by_timestamp.get(ts)
        if row is None:
            continue

        # Gap SL: open already at or above stop
        if row.open_value >= stop_price:
            exit_price = row.open_value
            exit_reason = "gap_sl"
            return _leg_result(entry_row, exit_price, exit_reason, ts,
                               slippage, contract_multiplier, brokerage_per_order)

        # Intrabar SL
        if row.high_value >= stop_price:
            exit_price = stop_price
            exit_reason = "sl"
            return _leg_result(entry_row, exit_price, exit_reason, ts,
                               slippage, contract_multiplier, brokerage_per_order)

    # Day close
    exit_row = contract.rows_by_timestamp.get(exit_timestamp)
    if exit_row:
        return _leg_result(entry_row, exit_row.open_value, "day_close", exit_timestamp,
                           slippage, contract_multiplier, brokerage_per_order)

    # Fallback: use entry price (missing exit candle)
    return _leg_result(entry_row, entry_row.open_value, "missing_exit_candle", exit_timestamp,
                       slippage, contract_multiplier, brokerage_per_order)


def _leg_result(
    entry_row: PriceRow,
    exit_price: float,
    exit_reason: str,
    exit_ts: str,
    slippage: float,
    contract_multiplier: int,
    brokerage_per_order: float,
) -> Tuple[str, str, str, str, str, str, str]:
    points = entry_row.open_value - exit_price - 2 * slippage
    gross = points * contract_multiplier
    brok = brokerage_per_order * 2
    return exit_ts, fmt(exit_price), exit_reason, fmt(points), fmt(gross), fmt(brok), fmt(gross - brok)


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
        ce_contract_file="", ce_entry_timestamp="", ce_entry_open="", ce_stop_price="",
        ce_exit_timestamp="", ce_exit_price="", ce_exit_reason="",
        ce_points_pnl="0.00", ce_gross_pnl="0.00", ce_brokerage="0.00", ce_net_pnl="0.00",
        pe_contract_file="", pe_entry_timestamp="", pe_entry_open="", pe_stop_price="",
        pe_exit_timestamp="", pe_exit_price="", pe_exit_reason="",
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
    contract_cache: Dict[Path, Optional[ContractData]] = {}
    contract_multiplier = args.lot_size * args.lots
    round_trip_brokerage = args.brokerage_per_order * 4
    results: List[TradeResult] = []

    try:
        for entry_date in trading_days:
            weekday = datetime.date.fromisoformat(entry_date).weekday()
            if weekday >= 5:
                continue
            day_name = WEEKDAY_NAMES[weekday]
            entry_timestamp = build_timestamp(entry_date, args.entry_time)
            exit_timestamp = build_timestamp(entry_date, args.exit_time)
            day_timestamps = timestamps_by_day.get(entry_date, [])

            if entry_timestamp not in day_timestamps:
                results.append(empty_result(
                    entry_date, day_name, "missing_spot_entry", "", "",
                    entry_timestamp, "", "", f"No spot candle at {entry_timestamp}.",
                ))
                continue

            if exit_timestamp not in day_timestamps:
                results.append(empty_result(
                    entry_date, day_name, "missing_spot_exit", "", "",
                    entry_timestamp, "", "", f"No spot candle at {exit_timestamp}.",
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
            ce_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_CE_{suffix}.csv"
            pe_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_PE_{suffix}.csv"

            ce_contract = load_contract(ce_path, contract_cache)
            pe_contract = load_contract(pe_path, contract_cache)

            missing = [p.name for p in [ce_path, pe_path]
                       if (ce_contract if p == ce_path else pe_contract) is None]
            if missing:
                results.append(empty_result(
                    entry_date, day_name, "missing_contract_file",
                    expiry_date, expiry_type, entry_timestamp, spot_open_text,
                    str(atm_strike), f"Missing: {', '.join(missing)}",
                ))
                logger.info("SKIPPED date=%s reason=missing_contract atm=%s", entry_date, atm_strike)
                continue

            ce_entry_row = ce_contract.rows_by_timestamp.get(entry_timestamp)
            pe_entry_row = pe_contract.rows_by_timestamp.get(entry_timestamp)

            missing_ts = []
            if ce_entry_row is None:
                missing_ts.append(f"{ce_path.name} missing {entry_timestamp}")
            if pe_entry_row is None:
                missing_ts.append(f"{pe_path.name} missing {entry_timestamp}")
            if missing_ts:
                results.append(empty_result(
                    entry_date, day_name, "missing_entry_candle",
                    expiry_date, expiry_type, entry_timestamp, spot_open_text,
                    str(atm_strike), "; ".join(missing_ts),
                ))
                logger.info("SKIPPED date=%s reason=missing_entry_candle atm=%s", entry_date, atm_strike)
                continue

            # Resolve each leg independently
            ce_exit_ts, ce_exit_price, ce_exit_reason, ce_pts, ce_gross, ce_brok, ce_net = resolve_leg(
                ce_contract, ce_entry_row, day_timestamps,
                entry_timestamp, exit_timestamp,
                args.sl_multiple, args.slippage_points_per_order,
                contract_multiplier, args.brokerage_per_order,
            )
            pe_exit_ts, pe_exit_price, pe_exit_reason, pe_pts, pe_gross, pe_brok, pe_net = resolve_leg(
                pe_contract, pe_entry_row, day_timestamps,
                entry_timestamp, exit_timestamp,
                args.sl_multiple, args.slippage_points_per_order,
                contract_multiplier, args.brokerage_per_order,
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

            sl_summary = []
            if "sl" in ce_exit_reason:
                sl_summary.append(f"CE_SL@{ce_exit_ts[-14:-9]}")
            if "sl" in pe_exit_reason:
                sl_summary.append(f"PE_SL@{pe_exit_ts[-14:-9]}")
            logger.info(
                "TRADED date=%s day=%s expiry=%s atm=%s ce@%s pe@%s sl=[%s] net=%s",
                entry_date, day_name, expiry_date, atm_strike,
                ce_entry_row.open_text, pe_entry_row.open_text,
                ",".join(sl_summary) if sl_summary else "none", fmt(net_pnl),
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
        "spot_entry_timestamp", "spot_entry_open", "atm_strike",
        "ce_contract_file", "ce_entry_timestamp", "ce_entry_open", "ce_stop_price",
        "ce_exit_timestamp", "ce_exit_price", "ce_exit_reason",
        "ce_points_pnl", "ce_gross_pnl", "ce_brokerage", "ce_net_pnl",
        "pe_contract_file", "pe_entry_timestamp", "pe_entry_open", "pe_stop_price",
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

    ce_sl = sum(1 for r in traded if "sl" in r.ce_exit_reason)
    pe_sl = sum(1 for r in traded if "sl" in r.pe_exit_reason)
    both_sl = sum(1 for r in traded if "sl" in r.ce_exit_reason and "sl" in r.pe_exit_reason)
    neither_sl = sum(1 for r in traded if "sl" not in r.ce_exit_reason and "sl" not in r.pe_exit_reason)

    max_profit = max(traded, key=lambda r: float(r.net_pnl), default=None)
    max_loss = min(traded, key=lambda r: float(r.net_pnl), default=None)

    by_day: Dict[str, List[TradeResult]] = {}
    for r in traded:
        by_day.setdefault(r.day_of_week, []).append(r)

    lines = [
        "# 2025 Intraday ATM Straddle — Independent SL per Leg",
        "",
        "## Strategy Details",
        "",
        f"- Entry time: `{args.entry_time}` (sell ATM CE + PE)",
        f"- Exit time: `{args.exit_time}` if SL not hit (day close)",
        f"- Stop loss: `{args.sl_multiple}x` entry premium, independent per leg",
        "- SL rule: each leg exits only itself when its own SL is hit; partner continues",
        "- ATM rule: nearest 50 to spot open at entry time",
        "- Expiry rule: expiry day → next week; otherwise current week",
        f"- Contract multiplier: {args.lot_size} × {args.lots} = {args.lot_size * args.lots} per point",
        f"- Slippage: {fmt(args.slippage_points_per_order)} point per order",
        f"- Brokerage: Rs {fmt(args.brokerage_per_order)} per order, Rs {fmt(args.brokerage_per_order * 4)} per straddle",
        "",
        "## Results Summary",
        "",
        f"- Total traded days: `{len(traded)}`",
        f"- Total skipped days: `{len(skipped)}`",
        f"- Winning days: `{winning_days}`",
        f"- Losing days: `{losing_days}`",
        f"- Days CE SL hit: `{ce_sl}`",
        f"- Days PE SL hit: `{pe_sl}`",
        f"- Days both SL hit: `{both_sl}`",
        f"- Days neither SL hit: `{neither_sl}`",
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
        lines += [
            f"### {d}",
            f"- Trades: `{len(day_results)}`  Win: `{d_win}`  Loss: `{d_loss}`  CE-SL: `{d_ce_sl}`  PE-SL: `{d_pe_sl}`",
            f"- Net P/L: `{fmt(d_net)}`  Gross: `{fmt(d_gross)}`  Brokerage: `{fmt(d_brok)}`",
            "",
        ]

    lines += ["## Exceptions", ""]
    if skipped:
        for r in skipped:
            lines.append(f"- `{r.entry_date}` ({r.day_of_week}): `{r.skip_reason}`. {r.remarks}")
    else:
        lines.append("- None")

    lines += [
        "",
        "## Remarks",
        "",
        "- Each leg is managed independently — SL on one side does NOT affect the other.",
        "- SL fill: gap open ≥ SL → fill at candle open; intrabar high ≥ SL → fill at SL price.",
        "- Exact timestamp matching; no nearest-candle fallback.",
        "- NIFTY spot file is source of truth for the trading calendar.",
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
