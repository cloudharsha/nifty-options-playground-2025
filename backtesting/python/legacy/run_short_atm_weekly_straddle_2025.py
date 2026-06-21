#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


IST_SUFFIX = "+05:30"
DAYWISE_FILENAME = "short_atm_weekly_straddle_2025_daywise.csv"
SUMMARY_FILENAME = "short_atm_weekly_straddle_2025_summary.md"
LOG_FILENAME = "short_atm_weekly_straddle_2025.log"


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
    expiry_date: str
    next_trading_day: str
    spot_entry_timestamp: str
    spot_entry_open: str
    atm_strike: str
    ce_entry_timestamp: str
    ce_entry_open: str
    ce_exit_timestamp: str
    ce_exit_open: str
    pe_entry_timestamp: str
    pe_entry_open: str
    pe_exit_timestamp: str
    pe_exit_open: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    adjustments: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Backtest the 2025 overnight weekly short ATM straddle strategy.",
    )
    parser.add_argument(
        "--spot-file",
        type=Path,
        default=repo_root / "nifty" / "NIFTY50_INDEX_1m_2025.csv",
    )
    parser.add_argument(
        "--options-dir",
        type=Path,
        default=repo_root / "Options_2025",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=repo_root / "backtesting" / "results",
    )
    parser.add_argument("--entry-time", default="15:20")
    parser.add_argument("--exit-time", default="09:16")
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--lot-size", type=int, default=65)
    parser.add_argument("--lots", type=int, default=4)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
    return parser.parse_args()


def build_timestamp(day: str, time_text: str) -> str:
    parts = time_text.split(":")
    if len(parts) != 2:
        raise ValueError(f"Time must be HH:MM, got {time_text!r}")
    hour, minute = parts
    return f"{day}T{hour}:{minute}:00{IST_SUFFIX}"


def round_to_nearest_50(price: float) -> int:
    remainder = price % 50
    rounded_down = int(price - remainder)
    return rounded_down if remainder < 25 else rounded_down + 50


def format_money(value: float) -> str:
    return f"{value:.2f}"


def leg_pnl_after_slippage(raw_points_pnl: float, slippage_points_per_order: float) -> float:
    return raw_points_pnl - (2 * slippage_points_per_order)


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("short_atm_weekly_straddle_2025")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def load_spot_data(spot_file: Path) -> tuple[List[str], Dict[str, Dict[str, PriceRow]], Dict[str, PriceRow]]:
    trading_days: List[str] = []
    rows_by_day: Dict[str, Dict[str, PriceRow]] = {}
    rows_by_timestamp: Dict[str, PriceRow] = {}

    with spot_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = row["timestamp"]
            day = timestamp[:10]
            if day not in rows_by_day:
                rows_by_day[day] = {}
                trading_days.append(day)
            price_row = PriceRow(
                timestamp=timestamp,
                open_value=float(row["open"]),
                open_text=row["open"],
            )
            rows_by_day[day][timestamp] = price_row
            rows_by_timestamp[timestamp] = price_row

    return trading_days, rows_by_day, rows_by_timestamp


def load_expiry_folders(options_dir: Path) -> List[str]:
    return sorted(path.name for path in options_dir.iterdir() if path.is_dir())


def next_expiry_after(expiries: List[str], entry_date: str) -> Optional[str]:
    for expiry in expiries:
        if expiry > entry_date:
            return expiry
    return None


def expiry_suffix(expiry_date: str) -> str:
    expiry_dt = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
    return expiry_dt.strftime("%d_%b_%y").upper()


def load_contract(contract_path: Path, cache: Dict[Path, ContractData]) -> Optional[ContractData]:
    if contract_path in cache:
        return cache[contract_path]
    if not contract_path.exists():
        return None

    rows_by_timestamp: Dict[str, PriceRow] = {}
    with contract_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = row["timestamp"]
            rows_by_timestamp[timestamp] = PriceRow(
                timestamp=timestamp,
                open_value=float(row["open"]),
                open_text=row["open"],
            )

    contract_data = ContractData(path=contract_path, rows_by_timestamp=rows_by_timestamp)
    cache[contract_path] = contract_data
    return contract_data


def make_skipped_result(
    entry_date: str,
    expiry_date: str,
    next_trading_day: str,
    spot_entry_timestamp: str,
    spot_entry_open: str,
    atm_strike: str,
    skip_reason: str,
    remarks: str,
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date,
        status="SKIPPED",
        skip_reason=skip_reason,
        expiry_date=expiry_date,
        next_trading_day=next_trading_day,
        spot_entry_timestamp=spot_entry_timestamp,
        spot_entry_open=spot_entry_open,
        atm_strike=atm_strike,
        ce_entry_timestamp="",
        ce_entry_open="",
        ce_exit_timestamp="",
        ce_exit_open="",
        pe_entry_timestamp="",
        pe_entry_open="",
        pe_exit_timestamp="",
        pe_exit_open="",
        gross_pnl="0.00",
        brokerage="0.00",
        net_pnl="0.00",
        adjustments="0",
        remarks=remarks,
    )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, spot_rows_by_day, _ = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    contract_cache: Dict[Path, ContractData] = {}
    results: List[TradeResult] = []
    next_day_by_day = {
        trading_days[index]: trading_days[index + 1] if index + 1 < len(trading_days) else ""
        for index in range(len(trading_days))
    }
    entry_time_text = args.entry_time
    exit_time_text = args.exit_time
    round_trip_brokerage = args.brokerage_per_order * 4
    contract_multiplier = args.lot_size * args.lots

    try:
        for entry_date in trading_days:
            spot_entry_timestamp = build_timestamp(entry_date, entry_time_text)
            spot_entry_row = spot_rows_by_day[entry_date].get(spot_entry_timestamp)
            if spot_entry_row is None:
                continue

            next_trading_day = next_day_by_day[entry_date]
            if not next_trading_day:
                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date="",
                    next_trading_day="",
                    spot_entry_timestamp=spot_entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    atm_strike="",
                    skip_reason="no_next_trading_day",
                    remarks="No next trading day exists in the dataset.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            expiry_date = next_expiry_after(expiries, entry_date)
            if expiry_date is None:
                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date="",
                    next_trading_day=next_trading_day,
                    spot_entry_timestamp=spot_entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    atm_strike="",
                    skip_reason="no_next_weekly_expiry",
                    remarks="No later weekly expiry folder exists in the dataset.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            strike = round_to_nearest_50(spot_entry_row.open_value)
            strike_text = str(strike)
            option_suffix = expiry_suffix(expiry_date)
            ce_path = args.options_dir / expiry_date / f"NIFTY_{strike}_CE_{option_suffix}.csv"
            pe_path = args.options_dir / expiry_date / f"NIFTY_{strike}_PE_{option_suffix}.csv"
            exit_timestamp = build_timestamp(next_trading_day, exit_time_text)

            ce_contract = load_contract(ce_path, contract_cache)
            pe_contract = load_contract(pe_path, contract_cache)
            if ce_contract is None or pe_contract is None:
                missing_names = []
                if ce_contract is None:
                    missing_names.append(ce_path.name)
                if pe_contract is None:
                    missing_names.append(pe_path.name)
                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date=expiry_date,
                    next_trading_day=next_trading_day,
                    spot_entry_timestamp=spot_entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    atm_strike=strike_text,
                    skip_reason="missing_option_file",
                    remarks=f"Missing option file(s): {', '.join(missing_names)}",
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s strike=%s reason=%s",
                    entry_date,
                    expiry_date,
                    strike_text,
                    result.remarks,
                )
                continue

            ce_entry_row = ce_contract.rows_by_timestamp.get(spot_entry_timestamp)
            ce_exit_row = ce_contract.rows_by_timestamp.get(exit_timestamp)
            pe_entry_row = pe_contract.rows_by_timestamp.get(spot_entry_timestamp)
            pe_exit_row = pe_contract.rows_by_timestamp.get(exit_timestamp)

            missing_points: List[str] = []
            if ce_entry_row is None:
                missing_points.append(f"{ce_path.name} missing entry timestamp {spot_entry_timestamp}")
            if ce_exit_row is None:
                missing_points.append(f"{ce_path.name} missing exit timestamp {exit_timestamp}")
            if pe_entry_row is None:
                missing_points.append(f"{pe_path.name} missing entry timestamp {spot_entry_timestamp}")
            if pe_exit_row is None:
                missing_points.append(f"{pe_path.name} missing exit timestamp {exit_timestamp}")

            if missing_points:
                remarks = "; ".join(missing_points)
                if entry_date == "2025-10-20":
                    remarks = (
                        f"{remarks}; Next trading day is a special session that starts at 13:45, "
                        "so the exact 09:16 exit candle is unavailable."
                    )
                result = make_skipped_result(
                    entry_date=entry_date,
                    expiry_date=expiry_date,
                    next_trading_day=next_trading_day,
                    spot_entry_timestamp=spot_entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    atm_strike=strike_text,
                    skip_reason="missing_entry_or_exit_timestamp",
                    remarks=remarks,
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s strike=%s reason=%s",
                    entry_date,
                    expiry_date,
                    strike_text,
                    result.remarks,
                )
                continue

            ce_points_pnl = leg_pnl_after_slippage(
                ce_entry_row.open_value - ce_exit_row.open_value,
                args.slippage_points_per_order,
            )
            pe_points_pnl = leg_pnl_after_slippage(
                pe_entry_row.open_value - pe_exit_row.open_value,
                args.slippage_points_per_order,
            )
            gross_pnl = (ce_points_pnl + pe_points_pnl) * contract_multiplier
            brokerage = round_trip_brokerage
            net_pnl = gross_pnl - brokerage

            result = TradeResult(
                entry_date=entry_date,
                status="TRADED",
                skip_reason="",
                expiry_date=expiry_date,
                next_trading_day=next_trading_day,
                spot_entry_timestamp=spot_entry_timestamp,
                spot_entry_open=spot_entry_row.open_text,
                atm_strike=strike_text,
                ce_entry_timestamp=spot_entry_timestamp,
                ce_entry_open=ce_entry_row.open_text,
                ce_exit_timestamp=exit_timestamp,
                ce_exit_open=ce_exit_row.open_text,
                pe_entry_timestamp=spot_entry_timestamp,
                pe_entry_open=pe_entry_row.open_text,
                pe_exit_timestamp=exit_timestamp,
                pe_exit_open=pe_exit_row.open_text,
                gross_pnl=format_money(gross_pnl),
                brokerage=format_money(brokerage),
                net_pnl=format_money(net_pnl),
                adjustments="0",
                remarks="",
            )
            results.append(result)
            logger.info(
                "TRADED date=%s expiry=%s strike=%s gross=%s brokerage=%s net=%s",
                entry_date,
                expiry_date,
                strike_text,
                result.gross_pnl,
                result.brokerage,
                result.net_pnl,
            )
    except Exception:
        logger.exception("ERROR unexpected failure while running the backtest")
        raise

    traded_count = sum(1 for result in results if result.status == "TRADED")
    skipped_count = sum(1 for result in results if result.status == "SKIPPED")
    logger.info("COMPLETED traded=%s skipped=%s total=%s", traded_count, skipped_count, len(results))
    return results


def write_daywise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "skip_reason",
        "expiry_date",
        "next_trading_day",
        "spot_entry_timestamp",
        "spot_entry_open",
        "atm_strike",
        "ce_entry_timestamp",
        "ce_entry_open",
        "ce_exit_timestamp",
        "ce_exit_open",
        "pe_entry_timestamp",
        "pe_entry_open",
        "pe_exit_timestamp",
        "pe_exit_open",
        "gross_pnl",
        "brokerage",
        "net_pnl",
        "adjustments",
        "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)


def write_summary(results: List[TradeResult], output_path: Path, args: argparse.Namespace) -> None:
    traded_results = [result for result in results if result.status == "TRADED"]
    skipped_results = [result for result in results if result.status == "SKIPPED"]
    gross_total = sum(float(result.gross_pnl) for result in traded_results)
    brokerage_total = sum(float(result.brokerage) for result in traded_results)
    net_total = sum(float(result.net_pnl) for result in traded_results)

    lines: List[str] = [
        "# 2025 Overnight Weekly Short ATM Straddle Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Entry time: `{args.entry_time}`",
        f"- Exit time: `{args.exit_time}`",
        "- ATM rule: nearest 50 using spot 15:20 open",
        "- Expiry rule: first weekly expiry strictly after entry date",
        "- Pricing rule: option open price at exact timestamps",
        f"- Contract multiplier: {args.lot_size} x {args.lots} = {args.lot_size * args.lots} rupees per option point",
        f"- Execution slippage: {format_money(args.slippage_points_per_order)} point per order, applied against every entry and exit",
        (
            f"- Brokerage rule: Rs {int(args.brokerage_per_order)} per order per leg, "
            f"Rs {int(args.brokerage_per_order * 4)} per completed straddle"
        ),
        "- Adjustments: none",
        "",
        "## Results Summary",
        "",
        f"- No of trades: `{len(traded_results)}`",
        "- No of adjustments: `0`",
        f"- Total Profit/Loss: `{format_money(net_total)}`",
        f"- Total Brokerage: `{format_money(brokerage_total)}`",
        f"- Profit/Loss without Brokerage: `{format_money(gross_total)}`",
        "",
        "## Exceptions",
        "",
    ]

    if skipped_results:
        for result in skipped_results:
            lines.append(
                f"- `{result.entry_date}`: `{result.skip_reason}`. {result.remarks}"
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Remarks",
            "",
            "- The backtest uses exact timestamp matching for both entry and exit; no nearest-candle fallback is allowed.",
            "- Profit/Loss without Brokerage includes the configured execution slippage but excludes brokerage.",
            "- The NIFTY spot file is the source of truth for the trading calendar.",
            "- `2025-10-21` is a special session that starts at `13:45`, which is why the `2025-10-20` trade is skipped.",
            "- `2025-12-30` is skipped because there is no later weekly expiry folder in the dataset.",
            "- `2025-12-31` is skipped because there is no next trading day available in the dataset.",
        ]
    )

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    results = run_backtest(args)
    write_daywise_csv(results, args.results_dir / DAYWISE_FILENAME)
    write_summary(results, args.results_dir / SUMMARY_FILENAME, args)


if __name__ == "__main__":
    main()
