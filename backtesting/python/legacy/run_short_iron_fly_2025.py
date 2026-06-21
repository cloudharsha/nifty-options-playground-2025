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
DAYWISE_FILENAME = "short_iron_fly_2025_daywise.csv"
SUMMARY_FILENAME = "short_iron_fly_2025_summary.md"
LOG_FILENAME = "short_iron_fly_2025.log"


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
class WingCandidate:
    strike: int
    entry_row: PriceRow
    exit_row: PriceRow
    premium_gap: float
    strike_distance: int


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
    sold_ce_entry_timestamp: str
    sold_ce_entry_open: str
    sold_ce_exit_timestamp: str
    sold_ce_exit_open: str
    sold_pe_entry_timestamp: str
    sold_pe_entry_open: str
    sold_pe_exit_timestamp: str
    sold_pe_exit_open: str
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
    gross_pnl: str
    brokerage: str
    net_pnl: str
    adjustments: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Backtest the 2025 overnight weekly short iron fly strategy.",
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
    parser.add_argument("--wing-min-ratio", type=float, default=0.25)
    parser.add_argument("--wing-max-ratio", type=float, default=0.35)
    parser.add_argument("--wing-target-ratio", type=float, default=1.0 / 3.0)
    return parser.parse_args()


def build_timestamp(day: str, time_text: str) -> str:
    hour, minute = time_text.split(":")
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
    logger = logging.getLogger("short_iron_fly_2025")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def load_spot_data(spot_file: Path) -> tuple[List[str], Dict[str, Dict[str, PriceRow]]]:
    trading_days: List[str] = []
    rows_by_day: Dict[str, Dict[str, PriceRow]] = {}
    with spot_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = row["timestamp"]
            day = timestamp[:10]
            if day not in rows_by_day:
                rows_by_day[day] = {}
                trading_days.append(day)
            rows_by_day[day][timestamp] = PriceRow(
                timestamp=timestamp,
                open_value=float(row["open"]),
                open_text=row["open"],
            )
    return trading_days, rows_by_day


def load_expiry_folders(options_dir: Path) -> List[str]:
    return sorted(path.name for path in options_dir.iterdir() if path.is_dir())


def index_option_strikes(options_dir: Path, expiries: List[str]) -> Dict[Tuple[str, str], List[int]]:
    indexed: Dict[Tuple[str, str], List[int]] = {}
    pattern = re.compile(r"^NIFTY_(\d+)_(CE|PE)_[A-Z0-9_]+\.csv$")
    for expiry in expiries:
        ce_strikes: List[int] = []
        pe_strikes: List[int] = []
        for contract_path in (options_dir / expiry).iterdir():
            if not contract_path.is_file():
                continue
            match = pattern.match(contract_path.name)
            if not match:
                continue
            strike = int(match.group(1))
            side = match.group(2)
            if side == "CE":
                ce_strikes.append(strike)
            else:
                pe_strikes.append(strike)
        indexed[(expiry, "CE")] = sorted(ce_strikes)
        indexed[(expiry, "PE")] = sorted(pe_strikes)
    return indexed


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
        sold_ce_entry_timestamp="",
        sold_ce_entry_open="",
        sold_ce_exit_timestamp="",
        sold_ce_exit_open="",
        sold_pe_entry_timestamp="",
        sold_pe_entry_open="",
        sold_pe_exit_timestamp="",
        sold_pe_exit_open="",
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
        gross_pnl="0.00",
        brokerage="0.00",
        net_pnl="0.00",
        adjustments="0",
        remarks=remarks,
    )


def select_wing_candidate(
    expiry_date: str,
    side: str,
    atm_strike: int,
    entry_timestamp: str,
    exit_timestamp: str,
    sold_entry_price: float,
    options_dir: Path,
    cache: Dict[Path, ContractData],
    strike_index: Dict[Tuple[str, str], List[int]],
    min_ratio: float,
    max_ratio: float,
    target_ratio: float,
) -> tuple[Optional[WingCandidate], str]:
    suffix = expiry_suffix(expiry_date)
    target_premium = sold_entry_price * target_ratio
    min_premium = sold_entry_price * min_ratio
    max_premium = sold_entry_price * max_ratio
    best_candidate: Optional[WingCandidate] = None
    strikes = strike_index.get((expiry_date, side), [])
    if side == "CE":
        candidate_strikes = [strike for strike in strikes if strike > atm_strike]
    else:
        candidate_strikes = [strike for strike in strikes if strike < atm_strike]
        candidate_strikes.reverse()

    if not candidate_strikes:
        return None, f"No {side} wing contracts were found beyond ATM strike {atm_strike}."

    for strike in candidate_strikes:
        contract_path = options_dir / expiry_date / f"NIFTY_{strike}_{side}_{suffix}.csv"
        contract_data = load_contract(contract_path, cache)
        if contract_data is not None:
            entry_row = contract_data.rows_by_timestamp.get(entry_timestamp)
            exit_row = contract_data.rows_by_timestamp.get(exit_timestamp)
            if entry_row is not None and exit_row is not None:
                if min_premium <= entry_row.open_value <= max_premium:
                    candidate = WingCandidate(
                        strike=strike,
                        entry_row=entry_row,
                        exit_row=exit_row,
                        premium_gap=abs(entry_row.open_value - target_premium),
                        strike_distance=abs(strike - atm_strike),
                    )
                    if best_candidate is None:
                        best_candidate = candidate
                    else:
                        current_key = (candidate.premium_gap, candidate.strike_distance, candidate.strike)
                        best_key = (
                            best_candidate.premium_gap,
                            best_candidate.strike_distance,
                            best_candidate.strike,
                        )
                        if current_key < best_key:
                            best_candidate = candidate

    if best_candidate is not None:
        return best_candidate, ""
    return (
        None,
        (
            f"No {side} wing contract satisfied the {min_ratio:.0%}-{max_ratio:.0%} premium band "
            f"with exact entry/exit timestamps."
        ),
    )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, spot_rows_by_day = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    strike_index = index_option_strikes(args.options_dir, expiries)
    contract_cache: Dict[Path, ContractData] = {}
    cached_expiry = ""
    results: List[TradeResult] = []
    next_day_by_day = {
        trading_days[index]: trading_days[index + 1] if index + 1 < len(trading_days) else ""
        for index in range(len(trading_days))
    }
    round_trip_brokerage = args.brokerage_per_order * 8
    contract_multiplier = args.lot_size * args.lots

    try:
        for entry_date in trading_days:
            entry_timestamp = build_timestamp(entry_date, args.entry_time)
            spot_entry_row = spot_rows_by_day[entry_date].get(entry_timestamp)
            if spot_entry_row is None:
                continue

            next_trading_day = next_day_by_day[entry_date]
            if not next_trading_day:
                result = make_skipped_result(
                    entry_date,
                    "",
                    "",
                    entry_timestamp,
                    spot_entry_row.open_text,
                    "",
                    "no_next_trading_day",
                    "No next trading day exists in the dataset.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            expiry_date = next_expiry_after(expiries, entry_date)
            if expiry_date is None:
                result = make_skipped_result(
                    entry_date,
                    "",
                    next_trading_day,
                    entry_timestamp,
                    spot_entry_row.open_text,
                    "",
                    "no_next_weekly_expiry",
                    "No later weekly expiry folder exists in the dataset.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            if expiry_date != cached_expiry:
                contract_cache.clear()
                cached_expiry = expiry_date

            atm_strike = round_to_nearest_50(spot_entry_row.open_value)
            atm_strike_text = str(atm_strike)
            suffix = expiry_suffix(expiry_date)
            exit_timestamp = build_timestamp(next_trading_day, args.exit_time)

            sold_ce_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_CE_{suffix}.csv"
            sold_pe_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_PE_{suffix}.csv"
            sold_ce = load_contract(sold_ce_path, contract_cache)
            sold_pe = load_contract(sold_pe_path, contract_cache)

            if sold_ce is None or sold_pe is None:
                missing_names = []
                if sold_ce is None:
                    missing_names.append(sold_ce_path.name)
                if sold_pe is None:
                    missing_names.append(sold_pe_path.name)
                result = make_skipped_result(
                    entry_date,
                    expiry_date,
                    next_trading_day,
                    entry_timestamp,
                    spot_entry_row.open_text,
                    atm_strike_text,
                    "missing_atm_option_file",
                    f"Missing ATM option file(s): {', '.join(missing_names)}",
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s strike=%s reason=%s",
                    entry_date,
                    expiry_date,
                    atm_strike_text,
                    result.remarks,
                )
                continue

            sold_ce_entry = sold_ce.rows_by_timestamp.get(entry_timestamp)
            sold_ce_exit = sold_ce.rows_by_timestamp.get(exit_timestamp)
            sold_pe_entry = sold_pe.rows_by_timestamp.get(entry_timestamp)
            sold_pe_exit = sold_pe.rows_by_timestamp.get(exit_timestamp)
            missing_points: List[str] = []
            if sold_ce_entry is None:
                missing_points.append(f"{sold_ce_path.name} missing entry timestamp {entry_timestamp}")
            if sold_ce_exit is None:
                missing_points.append(f"{sold_ce_path.name} missing exit timestamp {exit_timestamp}")
            if sold_pe_entry is None:
                missing_points.append(f"{sold_pe_path.name} missing entry timestamp {entry_timestamp}")
            if sold_pe_exit is None:
                missing_points.append(f"{sold_pe_path.name} missing exit timestamp {exit_timestamp}")

            if missing_points:
                remarks = "; ".join(missing_points)
                if entry_date == "2025-10-20":
                    remarks = (
                        f"{remarks}; Next trading day is a special session that starts at 13:45, "
                        "so the exact 09:16 exit candle is unavailable."
                    )
                result = make_skipped_result(
                    entry_date,
                    expiry_date,
                    next_trading_day,
                    entry_timestamp,
                    spot_entry_row.open_text,
                    atm_strike_text,
                    "missing_atm_entry_or_exit_timestamp",
                    remarks,
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s strike=%s reason=%s",
                    entry_date,
                    expiry_date,
                    atm_strike_text,
                    result.remarks,
                )
                continue

            buy_ce_candidate, ce_wing_error = select_wing_candidate(
                expiry_date=expiry_date,
                side="CE",
                atm_strike=atm_strike,
                entry_timestamp=entry_timestamp,
                exit_timestamp=exit_timestamp,
                sold_entry_price=sold_ce_entry.open_value,
                options_dir=args.options_dir,
                cache=contract_cache,
                strike_index=strike_index,
                min_ratio=args.wing_min_ratio,
                max_ratio=args.wing_max_ratio,
                target_ratio=args.wing_target_ratio,
            )
            buy_pe_candidate, pe_wing_error = select_wing_candidate(
                expiry_date=expiry_date,
                side="PE",
                atm_strike=atm_strike,
                entry_timestamp=entry_timestamp,
                exit_timestamp=exit_timestamp,
                sold_entry_price=sold_pe_entry.open_value,
                options_dir=args.options_dir,
                cache=contract_cache,
                strike_index=strike_index,
                min_ratio=args.wing_min_ratio,
                max_ratio=args.wing_max_ratio,
                target_ratio=args.wing_target_ratio,
            )

            if buy_ce_candidate is None or buy_pe_candidate is None:
                remarks_list: List[str] = []
                if ce_wing_error:
                    remarks_list.append(ce_wing_error)
                if pe_wing_error:
                    remarks_list.append(pe_wing_error)
                result = make_skipped_result(
                    entry_date,
                    expiry_date,
                    next_trading_day,
                    entry_timestamp,
                    spot_entry_row.open_text,
                    atm_strike_text,
                    "no_valid_wing_in_premium_band",
                    "; ".join(remarks_list),
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s strike=%s reason=%s",
                    entry_date,
                    expiry_date,
                    atm_strike_text,
                    result.remarks,
                )
                continue

            sold_ce_points_pnl = leg_pnl_after_slippage(
                sold_ce_entry.open_value - sold_ce_exit.open_value,
                args.slippage_points_per_order,
            )
            sold_pe_points_pnl = leg_pnl_after_slippage(
                sold_pe_entry.open_value - sold_pe_exit.open_value,
                args.slippage_points_per_order,
            )
            buy_ce_points_pnl = leg_pnl_after_slippage(
                buy_ce_candidate.exit_row.open_value - buy_ce_candidate.entry_row.open_value,
                args.slippage_points_per_order,
            )
            buy_pe_points_pnl = leg_pnl_after_slippage(
                buy_pe_candidate.exit_row.open_value - buy_pe_candidate.entry_row.open_value,
                args.slippage_points_per_order,
            )
            gross_pnl = (
                sold_ce_points_pnl
                + sold_pe_points_pnl
                + buy_ce_points_pnl
                + buy_pe_points_pnl
            ) * contract_multiplier
            brokerage = round_trip_brokerage
            net_pnl = gross_pnl - brokerage

            result = TradeResult(
                entry_date=entry_date,
                status="TRADED",
                skip_reason="",
                expiry_date=expiry_date,
                next_trading_day=next_trading_day,
                spot_entry_timestamp=entry_timestamp,
                spot_entry_open=spot_entry_row.open_text,
                atm_strike=atm_strike_text,
                sold_ce_entry_timestamp=entry_timestamp,
                sold_ce_entry_open=sold_ce_entry.open_text,
                sold_ce_exit_timestamp=exit_timestamp,
                sold_ce_exit_open=sold_ce_exit.open_text,
                sold_pe_entry_timestamp=entry_timestamp,
                sold_pe_entry_open=sold_pe_entry.open_text,
                sold_pe_exit_timestamp=exit_timestamp,
                sold_pe_exit_open=sold_pe_exit.open_text,
                buy_ce_strike=str(buy_ce_candidate.strike),
                buy_ce_entry_timestamp=entry_timestamp,
                buy_ce_entry_open=buy_ce_candidate.entry_row.open_text,
                buy_ce_exit_timestamp=exit_timestamp,
                buy_ce_exit_open=buy_ce_candidate.exit_row.open_text,
                buy_pe_strike=str(buy_pe_candidate.strike),
                buy_pe_entry_timestamp=entry_timestamp,
                buy_pe_entry_open=buy_pe_candidate.entry_row.open_text,
                buy_pe_exit_timestamp=exit_timestamp,
                buy_pe_exit_open=buy_pe_candidate.exit_row.open_text,
                gross_pnl=format_money(gross_pnl),
                brokerage=format_money(brokerage),
                net_pnl=format_money(net_pnl),
                adjustments="0",
                remarks="",
            )
            results.append(result)
            logger.info(
                "TRADED date=%s expiry=%s atm=%s buy_ce=%s buy_pe=%s gross=%s brokerage=%s net=%s",
                entry_date,
                expiry_date,
                atm_strike_text,
                result.buy_ce_strike,
                result.buy_pe_strike,
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
        "sold_ce_entry_timestamp",
        "sold_ce_entry_open",
        "sold_ce_exit_timestamp",
        "sold_ce_exit_open",
        "sold_pe_entry_timestamp",
        "sold_pe_entry_open",
        "sold_pe_exit_timestamp",
        "sold_pe_exit_open",
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
        "# 2025 Overnight Short Iron Fly Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Entry time: `{args.entry_time}`",
        f"- Exit time: `{args.exit_time}`",
        "- ATM rule: nearest 50 using spot 15:20 open",
        "- Expiry rule: first weekly expiry strictly after entry date",
        "- Sold legs: ATM CE and ATM PE at exact entry timestamp open price",
        (
            f"- Wing selection rule: buy OTM CE and OTM PE with entry premiums in the "
            f"{int(args.wing_min_ratio * 100)}% to {int(args.wing_max_ratio * 100)}% band of their "
            f"respective sold ATM leg, choosing the candidate closest to {args.wing_target_ratio * 100:.2f}%"
        ),
        "- Pricing rule: option open price at exact timestamps",
        f"- Contract multiplier: {args.lot_size} x {args.lots} = {args.lot_size * args.lots} rupees per option point",
        f"- Execution slippage: {format_money(args.slippage_points_per_order)} point per order, applied against every entry and exit",
        (
            f"- Brokerage rule: Rs {int(args.brokerage_per_order)} per order per leg, "
            f"Rs {int(args.brokerage_per_order * 8)} per completed iron fly"
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
            lines.append(f"- `{result.entry_date}`: `{result.skip_reason}`. {result.remarks}")
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
            "- The OTM call wing is selected from strikes above ATM, and the OTM put wing is selected from strikes below ATM.",
            "- If no valid wing exists in the requested premium band on either side, the full trade is skipped.",
            "- Special-session and end-of-dataset skips are recorded in the exceptions section rather than stopping the run.",
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
