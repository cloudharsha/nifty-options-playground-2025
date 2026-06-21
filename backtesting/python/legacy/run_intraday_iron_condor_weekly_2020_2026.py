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
BASE_FILENAME = "intraday_iron_condor_weekly_2020_2026"
DAYWISE_FILENAME = f"{BASE_FILENAME}_daywise.csv"
SUMMARY_FILENAME = f"{BASE_FILENAME}_summary.md"
LOG_FILENAME = f"{BASE_FILENAME}.log"


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
    status: str
    skip_reason: str
    active_expiry: str
    spot_atm_timestamp: str
    spot_atm_open: str
    atm_strike: str
    sell_ce_strike: str
    sell_ce_entry_timestamp: str
    sell_ce_entry_open: str
    sell_ce_exit_timestamp: str
    sell_ce_exit_open: str
    sell_pe_strike: str
    sell_pe_entry_timestamp: str
    sell_pe_entry_open: str
    sell_pe_exit_timestamp: str
    sell_pe_exit_open: str
    buy_ce_strike: str
    buy_ce_entry_timestamp: str
    buy_ce_entry_open: str
    buy_ce_exit_timestamp: str
    buy_ce_exit_open: str
    buy_pe_strike: str
    buy_pe_entry_timestamp: str
    buy_pe_entry_open: str
    buy_pe_exit_timestamp: str
    buy_pe_exit_open: str
    lot_size: str
    num_lots: str
    total_qty: str
    net_entry_credit_points: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Backtest a daily intraday Nifty short iron condor on weekly expiry options. "
            "Enters at 09:20 every trading day using the current active weekly expiry, "
            "exits at 15:20 the same day. Uses ~300 units per side (nearest lot multiple)."
        ),
    )
    parser.add_argument(
        "--spot-file",
        type=Path,
        default=repo_root / "nifty" / "NIFTY50_INDEX_15m_last_4y.csv",
        help="15-minute NIFTY spot CSV. Used only for 9:15 open to determine ATM.",
    )
    parser.add_argument(
        "--options-dir",
        type=Path,
        default=repo_root / "NiftyOptions_2020_2026" / "Options",
        help="Directory containing expiry-date sub-folders with 1-minute option CSVs.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=repo_root / "backtesting" / "results",
    )
    parser.add_argument(
        "--atm-time",
        default="09:15",
        help="Spot candle time used to determine ATM (default: 09:15, first 15m bar).",
    )
    parser.add_argument(
        "--entry-time",
        default="09:20",
        help="Options entry candle time (default: 09:20).",
    )
    parser.add_argument(
        "--exit-time",
        default="15:20",
        help="Options exit candle time (default: 15:20).",
    )
    parser.add_argument(
        "--sell-offset",
        type=int,
        default=250,
        help="Points from ATM for the short CE and PE legs (default: 250).",
    )
    parser.add_argument(
        "--buy-offset",
        type=int,
        default=450,
        help="Points from ATM for the long CE and PE hedge legs (default: 450).",
    )
    parser.add_argument(
        "--target-qty",
        type=int,
        default=300,
        help="Target number of units per side; nearest lot multiple is chosen (default: 300).",
    )
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
    return parser.parse_args()


def build_timestamp(day: str, time_text: str) -> str:
    hour, minute = time_text.split(":")
    return f"{day}T{hour}:{minute}:00{IST_SUFFIX}"


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


def lot_size_for_expiry(expiry_date: str) -> int:
    if expiry_date < "2021-10-07":
        return 75
    if expiry_date <= "2024-04-25":
        return 50
    if expiry_date <= "2024-11-21":
        return 25
    if expiry_date <= "2025-12-30":
        return 75
    return 65


def compute_lots(lot_size: int, target_qty: int) -> int:
    lo = target_qty // lot_size
    hi = lo + 1
    if lo == 0:
        return 1
    diff_lo = abs(lo * lot_size - target_qty)
    diff_hi = abs(hi * lot_size - target_qty)
    return lo if diff_lo <= diff_hi else hi


def expiry_suffix(expiry_date: str) -> str:
    dt = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
    return dt.strftime("%d_%b_%y").upper()


def load_spot_data(
    spot_file: Path, atm_time: str
) -> Tuple[List[str], Dict[str, Optional[PriceRow]]]:
    trading_days: List[str] = []
    atm_row_by_day: Dict[str, Optional[PriceRow]] = {}
    atm_marker = f"T{atm_time}:00"

    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            ts = row["timestamp"]
            day = ts[:10]
            if day not in atm_row_by_day:
                atm_row_by_day[day] = None
                trading_days.append(day)
            if atm_marker in ts and atm_row_by_day[day] is None:
                atm_row_by_day[day] = PriceRow(
                    timestamp=ts,
                    open_value=float(row["open"]),
                    open_text=row["open"],
                )

    return trading_days, atm_row_by_day


def load_expiry_folders(options_dir: Path) -> Tuple[List[str], Set[str]]:
    expiries = sorted(p.name for p in options_dir.iterdir() if p.is_dir())
    return expiries, set(expiries)


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
            )
    data = ContractData(path=contract_path, rows_by_timestamp=rows)
    cache[contract_path] = data
    return data


def make_skipped_result(
    entry_date: str,
    active_expiry: str,
    spot_atm_timestamp: str,
    spot_atm_open: str,
    atm_strike: str,
    skip_reason: str,
    remarks: str,
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date,
        status="SKIPPED",
        skip_reason=skip_reason,
        active_expiry=active_expiry,
        spot_atm_timestamp=spot_atm_timestamp,
        spot_atm_open=spot_atm_open,
        atm_strike=atm_strike,
        sell_ce_strike="",
        sell_ce_entry_timestamp="",
        sell_ce_entry_open="",
        sell_ce_exit_timestamp="",
        sell_ce_exit_open="",
        sell_pe_strike="",
        sell_pe_entry_timestamp="",
        sell_pe_entry_open="",
        sell_pe_exit_timestamp="",
        sell_pe_exit_open="",
        buy_ce_strike="",
        buy_ce_entry_timestamp="",
        buy_ce_entry_open="",
        buy_ce_exit_timestamp="",
        buy_ce_exit_open="",
        buy_pe_strike="",
        buy_pe_entry_timestamp="",
        buy_pe_entry_open="",
        buy_pe_exit_timestamp="",
        buy_pe_exit_open="",
        lot_size="",
        num_lots="",
        total_qty="",
        net_entry_credit_points="0.00",
        gross_pnl="0.00",
        brokerage="0.00",
        net_pnl="0.00",
        remarks=remarks,
    )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, atm_row_by_day = load_spot_data(args.spot_file, args.atm_time)
    expiries, _ = load_expiry_folders(args.options_dir)
    contract_cache: Dict[Path, Optional[ContractData]] = {}
    cached_expiry = ""
    results: List[TradeResult] = []
    round_trip_brokerage = args.brokerage_per_order * 8

    try:
        for day in trading_days:
            active_expiry = first_expiry_on_or_after(expiries, day)
            if active_expiry is None:
                result = make_skipped_result(
                    entry_date=day,
                    active_expiry="",
                    spot_atm_timestamp="",
                    spot_atm_open="",
                    atm_strike="",
                    skip_reason="no_active_expiry",
                    remarks=f"No expiry on or after {day} in options dataset.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", day, result.skip_reason)
                continue

            atm_row = atm_row_by_day.get(day)
            if atm_row is None:
                result = make_skipped_result(
                    entry_date=day,
                    active_expiry=active_expiry,
                    spot_atm_timestamp=build_timestamp(day, args.atm_time),
                    spot_atm_open="",
                    atm_strike="",
                    skip_reason="missing_spot_entry_timestamp",
                    remarks=f"No {args.atm_time} candle in spot file for {day}.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", day, result.skip_reason)
                continue

            atm_strike = round_to_nearest_50(atm_row.open_value)
            sell_ce_strike = round_to_nearest_50(float(atm_strike + args.sell_offset))
            sell_pe_strike = round_to_nearest_50(float(atm_strike - args.sell_offset))
            buy_ce_strike = round_to_nearest_50(float(atm_strike + args.buy_offset))
            buy_pe_strike = round_to_nearest_50(float(atm_strike - args.buy_offset))

            if active_expiry != cached_expiry:
                contract_cache.clear()
                cached_expiry = active_expiry

            suffix = expiry_suffix(active_expiry)
            sell_ce_path = args.options_dir / active_expiry / f"NIFTY_{sell_ce_strike}_CE_{suffix}.csv"
            sell_pe_path = args.options_dir / active_expiry / f"NIFTY_{sell_pe_strike}_PE_{suffix}.csv"
            buy_ce_path = args.options_dir / active_expiry / f"NIFTY_{buy_ce_strike}_CE_{suffix}.csv"
            buy_pe_path = args.options_dir / active_expiry / f"NIFTY_{buy_pe_strike}_PE_{suffix}.csv"

            sell_ce_data = load_contract(sell_ce_path, contract_cache)
            sell_pe_data = load_contract(sell_pe_path, contract_cache)
            buy_ce_data = load_contract(buy_ce_path, contract_cache)
            buy_pe_data = load_contract(buy_pe_path, contract_cache)

            missing_files = [
                p.name
                for p, d in [
                    (sell_ce_path, sell_ce_data),
                    (sell_pe_path, sell_pe_data),
                    (buy_ce_path, buy_ce_data),
                    (buy_pe_path, buy_pe_data),
                ]
                if d is None
            ]
            if missing_files:
                result = make_skipped_result(
                    entry_date=day,
                    active_expiry=active_expiry,
                    spot_atm_timestamp=atm_row.timestamp,
                    spot_atm_open=atm_row.open_text,
                    atm_strike=str(atm_strike),
                    skip_reason="missing_contract_file",
                    remarks=f"Missing: {', '.join(missing_files)}",
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s atm=%s reason=%s",
                    day, active_expiry, atm_strike, result.remarks,
                )
                continue

            entry_timestamp = build_timestamp(day, args.entry_time)
            exit_timestamp = build_timestamp(day, args.exit_time)

            sell_ce_entry = sell_ce_data.rows_by_timestamp.get(entry_timestamp)  # type: ignore[union-attr]
            sell_ce_exit = sell_ce_data.rows_by_timestamp.get(exit_timestamp)  # type: ignore[union-attr]
            sell_pe_entry = sell_pe_data.rows_by_timestamp.get(entry_timestamp)  # type: ignore[union-attr]
            sell_pe_exit = sell_pe_data.rows_by_timestamp.get(exit_timestamp)  # type: ignore[union-attr]
            buy_ce_entry = buy_ce_data.rows_by_timestamp.get(entry_timestamp)  # type: ignore[union-attr]
            buy_ce_exit = buy_ce_data.rows_by_timestamp.get(exit_timestamp)  # type: ignore[union-attr]
            buy_pe_entry = buy_pe_data.rows_by_timestamp.get(entry_timestamp)  # type: ignore[union-attr]
            buy_pe_exit = buy_pe_data.rows_by_timestamp.get(exit_timestamp)  # type: ignore[union-attr]

            missing_candles: List[str] = []
            for label, row in [
                (f"{sell_ce_path.name}@entry", sell_ce_entry),
                (f"{sell_ce_path.name}@exit", sell_ce_exit),
                (f"{sell_pe_path.name}@entry", sell_pe_entry),
                (f"{sell_pe_path.name}@exit", sell_pe_exit),
                (f"{buy_ce_path.name}@entry", buy_ce_entry),
                (f"{buy_ce_path.name}@exit", buy_ce_exit),
                (f"{buy_pe_path.name}@entry", buy_pe_entry),
                (f"{buy_pe_path.name}@exit", buy_pe_exit),
            ]:
                if row is None:
                    missing_candles.append(label)

            if missing_candles:
                result = make_skipped_result(
                    entry_date=day,
                    active_expiry=active_expiry,
                    spot_atm_timestamp=atm_row.timestamp,
                    spot_atm_open=atm_row.open_text,
                    atm_strike=str(atm_strike),
                    skip_reason="missing_candle_at_timestamp",
                    remarks="; ".join(missing_candles),
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s atm=%s reason=%s",
                    day, active_expiry, atm_strike, result.remarks,
                )
                continue

            lot_size = lot_size_for_expiry(active_expiry)
            num_lots = compute_lots(lot_size, args.target_qty)
            total_qty = lot_size * num_lots

            sell_ce_pnl = (sell_ce_entry.open_value - sell_ce_exit.open_value) - 2 * args.slippage_points_per_order  # type: ignore[union-attr]
            sell_pe_pnl = (sell_pe_entry.open_value - sell_pe_exit.open_value) - 2 * args.slippage_points_per_order  # type: ignore[union-attr]
            buy_ce_pnl = (buy_ce_exit.open_value - buy_ce_entry.open_value) - 2 * args.slippage_points_per_order  # type: ignore[union-attr]
            buy_pe_pnl = (buy_pe_exit.open_value - buy_pe_entry.open_value) - 2 * args.slippage_points_per_order  # type: ignore[union-attr]
            gross_pnl = (sell_ce_pnl + sell_pe_pnl + buy_ce_pnl + buy_pe_pnl) * total_qty
            net_pnl = gross_pnl - round_trip_brokerage

            net_entry_credit = (
                sell_ce_entry.open_value + sell_pe_entry.open_value  # type: ignore[union-attr]
                - buy_ce_entry.open_value - buy_pe_entry.open_value  # type: ignore[union-attr]
            )

            result = TradeResult(
                entry_date=day,
                status="TRADED",
                skip_reason="",
                active_expiry=active_expiry,
                spot_atm_timestamp=atm_row.timestamp,
                spot_atm_open=atm_row.open_text,
                atm_strike=str(atm_strike),
                sell_ce_strike=str(sell_ce_strike),
                sell_ce_entry_timestamp=entry_timestamp,
                sell_ce_entry_open=sell_ce_entry.open_text,  # type: ignore[union-attr]
                sell_ce_exit_timestamp=exit_timestamp,
                sell_ce_exit_open=sell_ce_exit.open_text,  # type: ignore[union-attr]
                sell_pe_strike=str(sell_pe_strike),
                sell_pe_entry_timestamp=entry_timestamp,
                sell_pe_entry_open=sell_pe_entry.open_text,  # type: ignore[union-attr]
                sell_pe_exit_timestamp=exit_timestamp,
                sell_pe_exit_open=sell_pe_exit.open_text,  # type: ignore[union-attr]
                buy_ce_strike=str(buy_ce_strike),
                buy_ce_entry_timestamp=entry_timestamp,
                buy_ce_entry_open=buy_ce_entry.open_text,  # type: ignore[union-attr]
                buy_ce_exit_timestamp=exit_timestamp,
                buy_ce_exit_open=buy_ce_exit.open_text,  # type: ignore[union-attr]
                buy_pe_strike=str(buy_pe_strike),
                buy_pe_entry_timestamp=entry_timestamp,
                buy_pe_entry_open=buy_pe_entry.open_text,  # type: ignore[union-attr]
                buy_pe_exit_timestamp=exit_timestamp,
                buy_pe_exit_open=buy_pe_exit.open_text,  # type: ignore[union-attr]
                lot_size=str(lot_size),
                num_lots=str(num_lots),
                total_qty=str(total_qty),
                net_entry_credit_points=fmt(net_entry_credit),
                gross_pnl=fmt(gross_pnl),
                brokerage=fmt(round_trip_brokerage),
                net_pnl=fmt(net_pnl),
                remarks="",
            )
            results.append(result)
            logger.info(
                "TRADED date=%s expiry=%s atm=%s lot_size=%s lots=%s qty=%s "
                "sell_ce=%s sell_pe=%s buy_ce=%s buy_pe=%s credit=%.2f gross=%s net=%s",
                day, active_expiry, atm_strike, lot_size, num_lots, total_qty,
                sell_ce_strike, sell_pe_strike, buy_ce_strike, buy_pe_strike,
                net_entry_credit, result.gross_pnl, result.net_pnl,
            )

    except Exception:
        logger.exception("ERROR unexpected failure during backtest")
        raise

    traded = sum(1 for r in results if r.status == "TRADED")
    skipped = sum(1 for r in results if r.status == "SKIPPED")
    logger.info("COMPLETED traded=%s skipped=%s total=%s", traded, skipped, len(results))
    return results


def write_daywise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "skip_reason",
        "active_expiry",
        "spot_atm_timestamp",
        "spot_atm_open",
        "atm_strike",
        "sell_ce_strike",
        "sell_ce_entry_timestamp",
        "sell_ce_entry_open",
        "sell_ce_exit_timestamp",
        "sell_ce_exit_open",
        "sell_pe_strike",
        "sell_pe_entry_timestamp",
        "sell_pe_entry_open",
        "sell_pe_exit_timestamp",
        "sell_pe_exit_open",
        "buy_ce_strike",
        "buy_ce_entry_timestamp",
        "buy_ce_entry_open",
        "buy_ce_exit_timestamp",
        "buy_ce_exit_open",
        "buy_pe_strike",
        "buy_pe_entry_timestamp",
        "buy_pe_entry_open",
        "buy_pe_exit_timestamp",
        "buy_pe_exit_open",
        "lot_size",
        "num_lots",
        "total_qty",
        "net_entry_credit_points",
        "gross_pnl",
        "brokerage",
        "net_pnl",
        "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)


def write_summary(results: List[TradeResult], output_path: Path, args: argparse.Namespace) -> None:
    traded = [r for r in results if r.status == "TRADED"]
    skipped = [r for r in results if r.status == "SKIPPED"]
    gross_total = sum(float(r.gross_pnl) for r in traded)
    brokerage_total = sum(float(r.brokerage) for r in traded)
    net_total = sum(float(r.net_pnl) for r in traded)

    skip_reasons: Dict[str, int] = {}
    for r in skipped:
        skip_reasons[r.skip_reason] = skip_reasons.get(r.skip_reason, 0) + 1

    lines: List[str] = [
        "# Intraday Iron Condor — Weekly Expiry (2020–2026) Backtest",
        "",
        "## Strategy Details",
        "",
        "- **Structure**: Short iron condor — sell CE/PE at `ATM ± sell_offset`, "
        "buy CE/PE at `ATM ± buy_offset` as hedge",
        f"- **Sell offset**: {args.sell_offset} points from ATM",
        f"- **Buy offset (hedge)**: {args.buy_offset} points from ATM",
        f"- **Entry**: {args.entry_time} open candle (options), every trading day",
        f"- **Exit**: {args.exit_time} open candle (options), same day",
        f"- **ATM source**: {args.atm_time} spot open (15-minute bar), rounded to nearest 50",
        "- **Expiry**: current active weekly expiry (first expiry ≥ trading day)",
        f"- **Target quantity**: {args.target_qty} per side (nearest lot multiple per era)",
        "- **Lot size**: dynamic per expiry — 75 (pre-Oct 2021), 50 (Oct 2021–Apr 2024), "
        "25 (May 2024–Nov 2024), 75 (Nov 2024–Dec 2025), 65 (Jan 2026+)",
        f"- **Slippage**: {fmt(args.slippage_points_per_order)} pt per order "
        f"({fmt(2 * args.slippage_points_per_order)} pts round-trip per leg)",
        f"- **Brokerage**: Rs {int(args.brokerage_per_order)} per order, "
        f"Rs {int(args.brokerage_per_order * 8)} per completed condor (4 legs × 2 sides)",
        f"- **Spot file**: `{args.spot_file.name}` (~May 2022–2026; earlier dates skipped)",
        f"- **Options data**: `{args.options_dir.name}`",
        "- **No stop-loss, no intraday adjustments**",
        "",
        "## Results Summary",
        "",
        f"- Trading days processed : `{len(results)}`",
        f"- Trades executed        : `{len(traded)}`",
        f"- Trades skipped         : `{len(skipped)}`",
        f"- Gross P&L              : `{fmt(gross_total)}`",
        f"- Total Brokerage        : `{fmt(brokerage_total)}`",
        f"- Net P&L                : `{fmt(net_total)}`",
        "",
        "## Skip Reason Summary",
        "",
    ]

    if skip_reasons:
        for reason, count in sorted(skip_reasons.items(), key=lambda x: -x[1]):
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Notes",
        "",
        "- ATM is determined from the 09:15 spot candle open (first 15-minute bar). "
        "The strategy enters at 09:20 using the open of the first 1-minute candle in the options data.",
        "- The active expiry for each trading day is the earliest available weekly expiry "
        "folder on or after that date, including expiry day itself.",
        "- Trading days before ~May 2022 are skipped because the spot file does not cover that range.",
        "- Lot sizes are applied per the target expiry date. From Jan 2026 (lot size 65), "
        f"5 lots (325 units) are used as the nearest multiple to {args.target_qty}.",
        "- Deeply OTM or illiquid contracts may lack candles at 09:20 or 15:20, causing skips.",
        "- Gross P&L includes slippage deduction but excludes brokerage.",
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
