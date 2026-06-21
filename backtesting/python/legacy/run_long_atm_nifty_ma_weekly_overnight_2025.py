#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


IST_SUFFIX = "+05:30"
DAYWISE_FILENAME = "long_atm_nifty_ma_weekly_overnight_2025_daywise.csv"
SUMMARY_FILENAME = "long_atm_nifty_ma_weekly_overnight_2025_summary.md"
LOG_FILENAME = "long_atm_nifty_ma_weekly_overnight_2025.log"


@dataclass
class SpotRow:
    timestamp: str
    open_value: float
    open_text: str
    close_value: float
    close_text: str


@dataclass
class SpotData:
    rows_by_timestamp: Dict[str, SpotRow]
    ordered_rows: List[SpotRow]
    index_by_timestamp: Dict[str, int]


@dataclass
class OptionRow:
    timestamp: str
    open_value: float
    open_text: str


@dataclass
class ContractData:
    path: Path
    rows_by_timestamp: Dict[str, OptionRow]


@dataclass
class TradeResult:
    entry_date: str
    status: str
    skip_reason: str
    expiry_date: str
    next_trading_day: str
    spot_signal_timestamp: str
    spot_signal_close: str
    spot_sma_25: str
    spot_signal_relation: str
    atm_strike: str
    bought_side: str
    contract_name: str
    option_entry_timestamp: str
    option_entry_open: str
    option_exit_timestamp: str
    option_exit_open: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Backtest the 2025 overnight weekly directional ATM long option strategy using a NIFTY 25-SMA signal.",
    )
    parser.add_argument(
        "--spot-file",
        type=Path,
        default=repo_root / "nifty" / "NIFTY50_INDEX_15m_last_4y.csv",
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
    parser.add_argument("--signal-time", default="15:15")
    parser.add_argument("--entry-time", default="15:29")
    parser.add_argument("--exit-time", default="09:16")
    parser.add_argument("--ma-period", type=int, default=25)
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
    logger = logging.getLogger("long_atm_nifty_ma_weekly_overnight_2025")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def load_spot_data(spot_file: Path) -> Tuple[SpotData, List[str]]:
    rows_by_timestamp: Dict[str, SpotRow] = {}
    ordered_rows: List[SpotRow] = []
    index_by_timestamp: Dict[str, int] = {}
    trading_days: List[str] = []
    seen_days: set[str] = set()

    with spot_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = row["timestamp"]
            spot_row = SpotRow(
                timestamp=timestamp,
                open_value=float(row["open"]),
                open_text=row["open"],
                close_value=float(row["close"]),
                close_text=row["close"],
            )
            index_by_timestamp[timestamp] = len(ordered_rows)
            ordered_rows.append(spot_row)
            rows_by_timestamp[timestamp] = spot_row

            if timestamp.startswith("2025-"):
                day = timestamp[:10]
                if day not in seen_days:
                    trading_days.append(day)
                    seen_days.add(day)

    return SpotData(rows_by_timestamp, ordered_rows, index_by_timestamp), trading_days


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

    rows_by_timestamp: Dict[str, OptionRow] = {}
    with contract_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = row["timestamp"]
            rows_by_timestamp[timestamp] = OptionRow(
                timestamp=timestamp,
                open_value=float(row["open"]),
                open_text=row["open"],
            )

    contract_data = ContractData(path=contract_path, rows_by_timestamp=rows_by_timestamp)
    cache[contract_path] = contract_data
    return contract_data


def compute_spot_sma_including_current(
    spot_data: SpotData,
    timestamp: str,
    ma_period: int,
) -> Tuple[Optional[float], int]:
    index = spot_data.index_by_timestamp.get(timestamp)
    if index is None:
        return None, 0
    observed_count = index + 1
    if observed_count < ma_period:
        return None, observed_count
    window = spot_data.ordered_rows[index - ma_period + 1 : index + 1]
    sma = sum(row.close_value for row in window) / ma_period
    return sma, observed_count


def make_result(
    entry_date: str,
    status: str,
    skip_reason: str,
    expiry_date: str = "",
    next_trading_day: str = "",
    spot_signal_timestamp: str = "",
    spot_signal_close: str = "",
    spot_sma_25: str = "",
    spot_signal_relation: str = "",
    atm_strike: str = "",
    bought_side: str = "",
    contract_name: str = "",
    option_entry_timestamp: str = "",
    option_entry_open: str = "",
    option_exit_timestamp: str = "",
    option_exit_open: str = "",
    gross_pnl: float = 0.0,
    brokerage: float = 0.0,
    net_pnl: float = 0.0,
    remarks: str = "",
) -> TradeResult:
    return TradeResult(
        entry_date=entry_date,
        status=status,
        skip_reason=skip_reason,
        expiry_date=expiry_date,
        next_trading_day=next_trading_day,
        spot_signal_timestamp=spot_signal_timestamp,
        spot_signal_close=spot_signal_close,
        spot_sma_25=spot_sma_25,
        spot_signal_relation=spot_signal_relation,
        atm_strike=atm_strike,
        bought_side=bought_side,
        contract_name=contract_name,
        option_entry_timestamp=option_entry_timestamp,
        option_entry_open=option_entry_open,
        option_exit_timestamp=option_exit_timestamp,
        option_exit_open=option_exit_open,
        gross_pnl=format_money(gross_pnl),
        brokerage=format_money(brokerage),
        net_pnl=format_money(net_pnl),
        remarks=remarks,
    )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    spot_data, trading_days = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    contract_cache: Dict[Path, ContractData] = {}
    results: List[TradeResult] = []
    next_day_by_day = {
        trading_days[index]: trading_days[index + 1] if index + 1 < len(trading_days) else ""
        for index in range(len(trading_days))
    }
    round_trip_brokerage = args.brokerage_per_order * 2
    contract_multiplier = args.lot_size * args.lots

    try:
        for entry_date in trading_days:
            spot_signal_timestamp = build_timestamp(entry_date, args.signal_time)
            option_entry_timestamp = build_timestamp(entry_date, args.entry_time)
            spot_signal_row = spot_data.rows_by_timestamp.get(spot_signal_timestamp)
            if spot_signal_row is None:
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="missing_spot_signal_timestamp",
                    spot_signal_timestamp=spot_signal_timestamp,
                    remarks=f"Missing spot signal timestamp {spot_signal_timestamp}",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            spot_sma_25, observed_count = compute_spot_sma_including_current(
                spot_data,
                spot_signal_timestamp,
                args.ma_period,
            )
            if spot_sma_25 is None:
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="insufficient_spot_history",
                    spot_signal_timestamp=spot_signal_timestamp,
                    spot_signal_close=spot_signal_row.close_text,
                    remarks=(
                        f"{spot_signal_timestamp} has {observed_count} spot bars including the signal bar; "
                        f"needs {args.ma_period}"
                    ),
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            spot_signal_close = spot_signal_row.close_text
            spot_sma_text = format_money(spot_sma_25)
            atm_strike = round_to_nearest_50(spot_signal_row.close_value)
            strike_text = str(atm_strike)

            if spot_signal_row.close_value > spot_sma_25:
                spot_signal_relation = "ABOVE_SMA"
                bought_side = "CE"
            elif spot_signal_row.close_value < spot_sma_25:
                spot_signal_relation = "BELOW_SMA"
                bought_side = "PE"
            else:
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="equal_close_and_sma",
                    spot_signal_timestamp=spot_signal_timestamp,
                    spot_signal_close=spot_signal_close,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation="EQUAL_SMA",
                    atm_strike=strike_text,
                    remarks=(
                        f"NIFTY close {spot_signal_close} equals {args.ma_period}-SMA {spot_sma_text} "
                        f"at {spot_signal_timestamp}"
                    ),
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            next_trading_day = next_day_by_day[entry_date]
            if not next_trading_day:
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="no_next_trading_day",
                    spot_signal_timestamp=spot_signal_timestamp,
                    spot_signal_close=spot_signal_close,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation=spot_signal_relation,
                    atm_strike=strike_text,
                    bought_side=bought_side,
                    remarks="No next trading day exists in the dataset.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            expiry_date = next_expiry_after(expiries, entry_date)
            if expiry_date is None:
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="no_next_weekly_expiry",
                    next_trading_day=next_trading_day,
                    spot_signal_timestamp=spot_signal_timestamp,
                    spot_signal_close=spot_signal_close,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation=spot_signal_relation,
                    atm_strike=strike_text,
                    bought_side=bought_side,
                    remarks="No weekly expiry folder exists strictly after the trade date.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            option_exit_timestamp = build_timestamp(next_trading_day, args.exit_time)
            option_suffix = expiry_suffix(expiry_date)
            contract_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_{bought_side}_{option_suffix}.csv"
            contract_data = load_contract(contract_path, contract_cache)
            if contract_data is None:
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="missing_option_file",
                    expiry_date=expiry_date,
                    next_trading_day=next_trading_day,
                    spot_signal_timestamp=spot_signal_timestamp,
                    spot_signal_close=spot_signal_close,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation=spot_signal_relation,
                    atm_strike=strike_text,
                    bought_side=bought_side,
                    contract_name=contract_path.name,
                    remarks=f"Missing option file: {contract_path.name}",
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s side=%s strike=%s reason=%s",
                    entry_date,
                    expiry_date,
                    bought_side,
                    strike_text,
                    result.skip_reason,
                )
                continue

            entry_row = contract_data.rows_by_timestamp.get(option_entry_timestamp)
            exit_row = contract_data.rows_by_timestamp.get(option_exit_timestamp)
            missing_points: List[str] = []
            if entry_row is None:
                missing_points.append(f"{contract_path.name} missing entry timestamp {option_entry_timestamp}")
            if exit_row is None:
                missing_points.append(f"{contract_path.name} missing exit timestamp {option_exit_timestamp}")

            if missing_points:
                remarks = "; ".join(missing_points)
                if next_trading_day == "2025-10-21":
                    remarks = (
                        f"{remarks}; Next trading day is a special session that starts at 13:45, "
                        "so the exact 09:16 exit candle is unavailable."
                    )
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="missing_entry_or_exit_timestamp",
                    expiry_date=expiry_date,
                    next_trading_day=next_trading_day,
                    spot_signal_timestamp=spot_signal_timestamp,
                    spot_signal_close=spot_signal_close,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation=spot_signal_relation,
                    atm_strike=strike_text,
                    bought_side=bought_side,
                    contract_name=contract_path.name,
                    option_entry_timestamp=option_entry_timestamp,
                    option_exit_timestamp=option_exit_timestamp,
                    remarks=remarks,
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s side=%s strike=%s reason=%s",
                    entry_date,
                    expiry_date,
                    bought_side,
                    strike_text,
                    result.skip_reason,
                )
                continue

            gross_pnl = (
                leg_pnl_after_slippage(
                    exit_row.open_value - entry_row.open_value,
                    args.slippage_points_per_order,
                )
                * contract_multiplier
            )
            brokerage = round_trip_brokerage
            net_pnl = gross_pnl - brokerage
            result = make_result(
                entry_date=entry_date,
                status="TRADED",
                skip_reason="",
                expiry_date=expiry_date,
                next_trading_day=next_trading_day,
                spot_signal_timestamp=spot_signal_timestamp,
                spot_signal_close=spot_signal_close,
                spot_sma_25=spot_sma_text,
                spot_signal_relation=spot_signal_relation,
                atm_strike=strike_text,
                bought_side=bought_side,
                contract_name=contract_path.name,
                option_entry_timestamp=option_entry_timestamp,
                option_entry_open=entry_row.open_text,
                option_exit_timestamp=option_exit_timestamp,
                option_exit_open=exit_row.open_text,
                gross_pnl=gross_pnl,
                brokerage=brokerage,
                net_pnl=net_pnl,
            )
            results.append(result)
            logger.info(
                "TRADED date=%s expiry=%s side=%s strike=%s gross=%s brokerage=%s net=%s",
                entry_date,
                expiry_date,
                bought_side,
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
        "spot_signal_timestamp",
        "spot_signal_close",
        "spot_sma_25",
        "spot_signal_relation",
        "atm_strike",
        "bought_side",
        "contract_name",
        "option_entry_timestamp",
        "option_entry_open",
        "option_exit_timestamp",
        "option_exit_open",
        "gross_pnl",
        "brokerage",
        "net_pnl",
        "remarks",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)


def compute_max_consecutive_streaks(net_pnl_values: List[float]) -> Tuple[int, int]:
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    current_wins = 0
    current_losses = 0

    for net_pnl in net_pnl_values:
        if net_pnl > 0:
            current_wins += 1
            current_losses = 0
            max_consecutive_wins = max(max_consecutive_wins, current_wins)
        elif net_pnl < 0:
            current_losses += 1
            current_wins = 0
            max_consecutive_losses = max(max_consecutive_losses, current_losses)
        else:
            current_wins = 0
            current_losses = 0

    return max_consecutive_wins, max_consecutive_losses


def compute_max_drawdown(net_pnl_values: List[float]) -> float:
    cumulative_net = 0.0
    equity_peak = 0.0
    max_drawdown = 0.0

    for net_pnl in net_pnl_values:
        cumulative_net += net_pnl
        equity_peak = max(equity_peak, cumulative_net)
        max_drawdown = max(max_drawdown, equity_peak - cumulative_net)

    return max_drawdown


def write_summary(results: List[TradeResult], output_path: Path, args: argparse.Namespace) -> None:
    traded_results = [result for result in results if result.status == "TRADED"]
    skipped_results = [result for result in results if result.status == "SKIPPED"]
    gross_total = sum(float(result.gross_pnl) for result in traded_results)
    brokerage_total = sum(float(result.brokerage) for result in traded_results)
    net_total = sum(float(result.net_pnl) for result in traded_results)
    ce_buy_count = sum(1 for result in traded_results if result.bought_side == "CE")
    pe_buy_count = sum(1 for result in traded_results if result.bought_side == "PE")
    net_pnl_values = [float(result.net_pnl) for result in traded_results]
    winning_days = sum(1 for net_pnl in net_pnl_values if net_pnl > 0)
    losing_days = sum(1 for net_pnl in net_pnl_values if net_pnl < 0)
    break_even_days = sum(1 for net_pnl in net_pnl_values if net_pnl == 0)
    max_consecutive_wins, max_consecutive_losses = compute_max_consecutive_streaks(net_pnl_values)
    max_drawdown = compute_max_drawdown(net_pnl_values)
    max_profit_day = max(traded_results, key=lambda result: float(result.net_pnl), default=None)
    max_loss_day = min(traded_results, key=lambda result: float(result.net_pnl), default=None)

    lines: List[str] = [
        "# 2025 Overnight Weekly Long ATM NIFTY 25-SMA Backtest",
        "",
        "## Strategy Details",
        "",
        "- Signal source: NIFTY 15-minute close",
        f"- Signal bar time: `{args.signal_time}` row as `15:30` close proxy",
        f"- MA rule: {args.ma_period}-SMA of spot closes including the signal bar",
        "- Direction rule: above SMA -> buy ATM CE; below SMA -> buy ATM PE; equal -> no trade",
        f"- Entry execution time: `{args.entry_time}` option open",
        f"- Exit execution time: next trading day `{args.exit_time}` option open",
        "- Expiry rule: first weekly expiry strictly after entry date",
        "- ATM rule: nearest 50 using the spot signal close",
        f"- Contract multiplier: {args.lot_size} x {args.lots} = {args.lot_size * args.lots} rupees per option point",
        f"- Execution slippage: {format_money(args.slippage_points_per_order)} point per order, applied against every entry and exit",
        (
            f"- Brokerage rule: Rs {int(args.brokerage_per_order)} per order, "
            f"so one completed long leg pays Rs {int(args.brokerage_per_order * 2)}"
        ),
        "",
        "## Results Summary",
        "",
        f"- Traded days: `{len(traded_results)}`",
        f"- Skipped days: `{len(skipped_results)}`",
        f"- CE-buy count: `{ce_buy_count}`",
        f"- PE-buy count: `{pe_buy_count}`",
        f"- Winning days: `{winning_days}`",
        f"- Losing days: `{losing_days}`",
        f"- Break-even days: `{break_even_days}`",
        (
            f"- Max profit day: `{max_profit_day.entry_date}` with net P/L "
            f"`{max_profit_day.net_pnl}`"
            if max_profit_day
            else "- Max profit day: `N/A`"
        ),
        (
            f"- Max loss day: `{max_loss_day.entry_date}` with net P/L "
            f"`{max_loss_day.net_pnl}`"
            if max_loss_day
            else "- Max loss day: `N/A`"
        ),
        f"- Max consecutive wins: `{max_consecutive_wins}`",
        f"- Max consecutive losses: `{max_consecutive_losses}`",
        f"- Max drawdown: `{format_money(max_drawdown)}`",
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
            "- Exact timestamp matching is required; no nearest-candle fallback is allowed.",
            "- The `15:15` spot row is used as the `15:30` close proxy because the spot dataset has no exact `15:30` timestamp.",
            "- The `15:29` option row is used as the buy proxy because the options dataset has no exact `15:30` timestamp.",
            "- The NIFTY spot file is the source of truth for the trading calendar.",
            "- Expiry folder dates are used as truth, which naturally handles Tuesday special expiries and holiday shifts.",
            "- Equality between the spot close and the SMA produces no trade for that day.",
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
