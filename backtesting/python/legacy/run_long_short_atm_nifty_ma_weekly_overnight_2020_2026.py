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
DAYWISE_FILENAME = "long_short_atm_nifty_ma_weekly_overnight_2020_2026_daywise.csv"
SUMMARY_FILENAME = "long_short_atm_nifty_ma_weekly_overnight_2020_2026_summary.md"
LOG_FILENAME = "long_short_atm_nifty_ma_weekly_overnight_2020_2026.log"


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
    lot_size: str
    lots: str
    spot_signal_timestamp: str
    spot_signal_close: str
    spot_sma_25: str
    spot_signal_relation: str
    atm_strike: str
    bought_side: str
    sold_side: str
    bought_contract_name: str
    bought_option_entry_timestamp: str
    bought_option_entry_open: str
    bought_option_exit_timestamp: str
    bought_option_exit_open: str
    sold_contract_name: str
    sold_option_entry_timestamp: str
    sold_option_entry_open: str
    sold_option_exit_timestamp: str
    sold_option_exit_open: str
    bought_gross_pnl: str
    sold_gross_pnl: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Backtest the overnight weekly Long+Short ATM NIFTY 25-SMA strategy "
            "over 2020-2026 with capital-based dynamic lot sizing."
        ),
    )
    parser.add_argument(
        "--spot-file",
        type=Path,
        default=repo_root / "nifty" / "NIFTY50_INDEX_15m_last_4y.csv",
        help="15-minute NIFTY spot CSV. Available range: ~May 2022 – May 2026.",
    )
    parser.add_argument(
        "--options-dir",
        type=Path,
        default=repo_root / "NiftyOptions_2020_2026" / "Options",
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
    parser.add_argument(
        "--capital",
        type=float,
        default=10_00_000.0,
        help="Capital in rupees used to compute lot count per trade (default: 10,00,000).",
    )
    parser.add_argument(
        "--margin-fraction",
        type=float,
        default=0.10,
        help=(
            "Fraction of contract value (lot_size × spot_close) used as margin per lot. "
            "Approximates NIFTY futures initial margin (~10%%). Default: 0.10."
        ),
    )
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
    return parser.parse_args()


def lot_size_for_expiry(expiry_date: str) -> int:
    # Source: details.md — Nifty lot size history (by expiry date)
    #   pre-2021-10-07   → 75
    #   2021-10-07 through 2024-04-25 → 50
    #   2024-05-02 through 2024-11-21 → 25  (SEBI ₹15L mandate, new contracts from Nov 20 2024)
    #   2024-11-28 through 2025-12-30 → 75
    #   2026-01-01 onwards → 65
    if expiry_date < "2021-10-07":
        return 75
    if expiry_date <= "2024-04-25":
        return 50
    if expiry_date <= "2024-11-21":
        return 25
    if expiry_date <= "2025-12-30":
        return 75
    return 65


def compute_lots(capital: float, lot_size: int, spot_close: float, margin_fraction: float = 0.10) -> int:
    # Margin per lot for a synthetic directional position ≈ 10% of contract value
    # (similar to NIFTY futures initial margin; source: details.md margin table)
    margin_per_lot = lot_size * spot_close * margin_fraction
    if margin_per_lot <= 0:
        return 1
    return max(1, int(capital / margin_per_lot))


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
    logger = logging.getLogger("long_short_atm_nifty_ma_weekly_overnight_2020_2026")
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

    if not rows_by_timestamp:
        cache[contract_path] = None  # type: ignore[assignment]
        return None

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
    lot_size: int = 0,
    lots: int = 0,
    spot_signal_timestamp: str = "",
    spot_signal_close: str = "",
    spot_sma_25: str = "",
    spot_signal_relation: str = "",
    atm_strike: str = "",
    bought_side: str = "",
    sold_side: str = "",
    bought_contract_name: str = "",
    bought_option_entry_timestamp: str = "",
    bought_option_entry_open: str = "",
    bought_option_exit_timestamp: str = "",
    bought_option_exit_open: str = "",
    sold_contract_name: str = "",
    sold_option_entry_timestamp: str = "",
    sold_option_entry_open: str = "",
    sold_option_exit_timestamp: str = "",
    sold_option_exit_open: str = "",
    bought_gross_pnl: float = 0.0,
    sold_gross_pnl: float = 0.0,
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
        lot_size=str(lot_size),
        lots=str(lots),
        spot_signal_timestamp=spot_signal_timestamp,
        spot_signal_close=spot_signal_close,
        spot_sma_25=spot_sma_25,
        spot_signal_relation=spot_signal_relation,
        atm_strike=atm_strike,
        bought_side=bought_side,
        sold_side=sold_side,
        bought_contract_name=bought_contract_name,
        bought_option_entry_timestamp=bought_option_entry_timestamp,
        bought_option_entry_open=bought_option_entry_open,
        bought_option_exit_timestamp=bought_option_exit_timestamp,
        bought_option_exit_open=bought_option_exit_open,
        sold_contract_name=sold_contract_name,
        sold_option_entry_timestamp=sold_option_entry_timestamp,
        sold_option_entry_open=sold_option_entry_open,
        sold_option_exit_timestamp=sold_option_exit_timestamp,
        sold_option_exit_open=sold_option_exit_open,
        bought_gross_pnl=format_money(bought_gross_pnl),
        sold_gross_pnl=format_money(sold_gross_pnl),
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
                sold_side = "PE"
            elif spot_signal_row.close_value < spot_sma_25:
                spot_signal_relation = "BELOW_SMA"
                bought_side = "PE"
                sold_side = "CE"
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
                    sold_side=sold_side,
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
                    sold_side=sold_side,
                    remarks="No weekly expiry folder exists strictly after the trade date.",
                )
                results.append(result)
                logger.info("SKIPPED date=%s reason=%s", entry_date, result.skip_reason)
                continue

            trade_lot_size = lot_size_for_expiry(expiry_date)
            option_exit_timestamp = build_timestamp(next_trading_day, args.exit_time)
            option_suffix = expiry_suffix(expiry_date)
            bought_contract_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_{bought_side}_{option_suffix}.csv"
            sold_contract_path = args.options_dir / expiry_date / f"NIFTY_{atm_strike}_{sold_side}_{option_suffix}.csv"
            bought_contract = load_contract(bought_contract_path, contract_cache)
            sold_contract = load_contract(sold_contract_path, contract_cache)

            if bought_contract is None or sold_contract is None:
                missing_names: List[str] = []
                if bought_contract is None:
                    missing_names.append(bought_contract_path.name)
                if sold_contract is None:
                    missing_names.append(sold_contract_path.name)
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="missing_option_file",
                    expiry_date=expiry_date,
                    next_trading_day=next_trading_day,
                    lot_size=trade_lot_size,
                    spot_signal_timestamp=spot_signal_timestamp,
                    spot_signal_close=spot_signal_close,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation=spot_signal_relation,
                    atm_strike=strike_text,
                    bought_side=bought_side,
                    sold_side=sold_side,
                    bought_contract_name=bought_contract_path.name,
                    sold_contract_name=sold_contract_path.name,
                    remarks=f"Missing option file(s): {', '.join(missing_names)}",
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s buy=%s sell=%s strike=%s reason=%s",
                    entry_date, expiry_date, bought_side, sold_side, strike_text, result.skip_reason,
                )
                continue

            bought_entry_row = bought_contract.rows_by_timestamp.get(option_entry_timestamp)
            bought_exit_row = bought_contract.rows_by_timestamp.get(option_exit_timestamp)
            sold_entry_row = sold_contract.rows_by_timestamp.get(option_entry_timestamp)
            sold_exit_row = sold_contract.rows_by_timestamp.get(option_exit_timestamp)

            missing_points: List[str] = []
            if bought_entry_row is None:
                missing_points.append(f"{bought_contract_path.name} missing entry timestamp {option_entry_timestamp}")
            if bought_exit_row is None:
                missing_points.append(f"{bought_contract_path.name} missing exit timestamp {option_exit_timestamp}")
            if sold_entry_row is None:
                missing_points.append(f"{sold_contract_path.name} missing entry timestamp {option_entry_timestamp}")
            if sold_exit_row is None:
                missing_points.append(f"{sold_contract_path.name} missing exit timestamp {option_exit_timestamp}")

            if missing_points:
                result = make_result(
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="missing_entry_or_exit_timestamp",
                    expiry_date=expiry_date,
                    next_trading_day=next_trading_day,
                    lot_size=trade_lot_size,
                    spot_signal_timestamp=spot_signal_timestamp,
                    spot_signal_close=spot_signal_close,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation=spot_signal_relation,
                    atm_strike=strike_text,
                    bought_side=bought_side,
                    sold_side=sold_side,
                    bought_contract_name=bought_contract_path.name,
                    bought_option_entry_timestamp=option_entry_timestamp,
                    bought_option_exit_timestamp=option_exit_timestamp,
                    sold_contract_name=sold_contract_path.name,
                    sold_option_entry_timestamp=option_entry_timestamp,
                    sold_option_exit_timestamp=option_exit_timestamp,
                    remarks="; ".join(missing_points),
                )
                results.append(result)
                logger.info(
                    "SKIPPED date=%s expiry=%s buy=%s sell=%s strike=%s reason=%s",
                    entry_date, expiry_date, bought_side, sold_side, strike_text, result.skip_reason,
                )
                continue

            # Determine lot count from capital and spot-based margin estimate
            lots = compute_lots(args.capital, trade_lot_size, spot_signal_row.close_value, args.margin_fraction)
            multiplier = trade_lot_size * lots

            bought_gross_pnl = (
                leg_pnl_after_slippage(
                    bought_exit_row.open_value - bought_entry_row.open_value,
                    args.slippage_points_per_order,
                )
                * multiplier
            )
            sold_gross_pnl = (
                leg_pnl_after_slippage(
                    sold_entry_row.open_value - sold_exit_row.open_value,
                    args.slippage_points_per_order,
                )
                * multiplier
            )
            gross_pnl = bought_gross_pnl + sold_gross_pnl
            # 4 orders: buy entry, buy exit, sell entry, sell exit
            brokerage = args.brokerage_per_order * 4
            net_pnl = gross_pnl - brokerage

            result = make_result(
                entry_date=entry_date,
                status="TRADED",
                skip_reason="",
                expiry_date=expiry_date,
                next_trading_day=next_trading_day,
                lot_size=trade_lot_size,
                lots=lots,
                spot_signal_timestamp=spot_signal_timestamp,
                spot_signal_close=spot_signal_close,
                spot_sma_25=spot_sma_text,
                spot_signal_relation=spot_signal_relation,
                atm_strike=strike_text,
                bought_side=bought_side,
                sold_side=sold_side,
                bought_contract_name=bought_contract_path.name,
                bought_option_entry_timestamp=option_entry_timestamp,
                bought_option_entry_open=bought_entry_row.open_text,
                bought_option_exit_timestamp=option_exit_timestamp,
                bought_option_exit_open=bought_exit_row.open_text,
                sold_contract_name=sold_contract_path.name,
                sold_option_entry_timestamp=option_entry_timestamp,
                sold_option_entry_open=sold_entry_row.open_text,
                sold_option_exit_timestamp=option_exit_timestamp,
                sold_option_exit_open=sold_exit_row.open_text,
                bought_gross_pnl=bought_gross_pnl,
                sold_gross_pnl=sold_gross_pnl,
                gross_pnl=gross_pnl,
                brokerage=brokerage,
                net_pnl=net_pnl,
            )
            results.append(result)
            logger.info(
                "TRADED date=%s expiry=%s lot_size=%s lots=%s buy=%s sell=%s strike=%s "
                "bought_gross=%s sold_gross=%s net=%s",
                entry_date, expiry_date, trade_lot_size, lots,
                bought_side, sold_side, strike_text,
                result.bought_gross_pnl, result.sold_gross_pnl, result.net_pnl,
            )
    except Exception:
        logger.exception("ERROR unexpected failure while running the backtest")
        raise

    traded_count = sum(1 for r in results if r.status == "TRADED")
    skipped_count = sum(1 for r in results if r.status == "SKIPPED")
    logger.info("COMPLETED traded=%s skipped=%s total=%s", traded_count, skipped_count, len(results))
    return results


def write_daywise_csv(results: List[TradeResult], output_path: Path) -> None:
    fieldnames = [
        "entry_date",
        "status",
        "skip_reason",
        "expiry_date",
        "next_trading_day",
        "lot_size",
        "lots",
        "spot_signal_timestamp",
        "spot_signal_close",
        "spot_sma_25",
        "spot_signal_relation",
        "atm_strike",
        "bought_side",
        "sold_side",
        "bought_contract_name",
        "bought_option_entry_timestamp",
        "bought_option_entry_open",
        "bought_option_exit_timestamp",
        "bought_option_exit_open",
        "sold_contract_name",
        "sold_option_entry_timestamp",
        "sold_option_entry_open",
        "sold_option_exit_timestamp",
        "sold_option_exit_open",
        "bought_gross_pnl",
        "sold_gross_pnl",
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
    max_wins = 0
    max_losses = 0
    cur_wins = 0
    cur_losses = 0
    for net_pnl in net_pnl_values:
        if net_pnl > 0:
            cur_wins += 1
            cur_losses = 0
            max_wins = max(max_wins, cur_wins)
        elif net_pnl < 0:
            cur_losses += 1
            cur_wins = 0
            max_losses = max(max_losses, cur_losses)
        else:
            cur_wins = 0
            cur_losses = 0
    return max_wins, max_losses


def compute_max_drawdown(net_pnl_values: List[float]) -> float:
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for net_pnl in net_pnl_values:
        cumulative += net_pnl
        peak = max(peak, cumulative)
        max_dd = max(max_dd, peak - cumulative)
    return max_dd


def compute_cagr(net_total: float, capital: float, start_date: str, end_date: str) -> Optional[float]:
    try:
        d0 = datetime.date.fromisoformat(start_date)
        d1 = datetime.date.fromisoformat(end_date)
        years = (d1 - d0).days / 365.25
        if years <= 0 or capital <= 0:
            return None
        final_value = capital + net_total
        if final_value <= 0:
            return None
        return ((final_value / capital) ** (1 / years) - 1) * 100
    except Exception:
        return None


def write_summary(results: List[TradeResult], output_path: Path, args: argparse.Namespace) -> None:
    traded_results = [r for r in results if r.status == "TRADED"]
    skipped_results = [r for r in results if r.status == "SKIPPED"]
    bought_gross_total = sum(float(r.bought_gross_pnl) for r in traded_results)
    sold_gross_total = sum(float(r.sold_gross_pnl) for r in traded_results)
    gross_total = sum(float(r.gross_pnl) for r in traded_results)
    brokerage_total = sum(float(r.brokerage) for r in traded_results)
    net_total = sum(float(r.net_pnl) for r in traded_results)
    ce_buy_count = sum(1 for r in traded_results if r.bought_side == "CE")
    pe_buy_count = sum(1 for r in traded_results if r.bought_side == "PE")
    above_sma_count = sum(1 for r in traded_results if r.spot_signal_relation == "ABOVE_SMA")
    below_sma_count = sum(1 for r in traded_results if r.spot_signal_relation == "BELOW_SMA")
    net_pnl_values = [float(r.net_pnl) for r in traded_results]
    winning_days = sum(1 for v in net_pnl_values if v > 0)
    losing_days = sum(1 for v in net_pnl_values if v < 0)
    break_even_days = sum(1 for v in net_pnl_values if v == 0)
    max_consecutive_wins, max_consecutive_losses = compute_max_consecutive_streaks(net_pnl_values)
    max_drawdown = compute_max_drawdown(net_pnl_values)
    max_profit_day = max(traded_results, key=lambda r: float(r.net_pnl), default=None)
    max_loss_day = min(traded_results, key=lambda r: float(r.net_pnl), default=None)

    # Lot size period breakdown
    period_counts: Dict[int, int] = {}
    for r in traded_results:
        ls = int(r.lot_size) if r.lot_size else 0
        period_counts[ls] = period_counts.get(ls, 0) + 1

    first_trade_date = traded_results[0].entry_date if traded_results else ""
    last_trade_date = traded_results[-1].entry_date if traded_results else ""
    cagr = compute_cagr(net_total, args.capital, first_trade_date, last_trade_date) if first_trade_date else None

    lines: List[str] = [
        "# Overnight Weekly Long+Short ATM NIFTY 25-SMA Backtest — 2020-2026",
        "",
        "## Strategy Details",
        "",
        "- Signal source: NIFTY 15-minute close",
        f"- Signal bar time: `{args.signal_time}` row as `15:30` close proxy",
        f"- MA rule: {args.ma_period}-SMA of spot closes including the signal bar",
        "- Direction rule: above SMA → buy ATM CE + sell ATM PE; below SMA → buy ATM PE + sell ATM CE; equal → no trade",
        f"- Entry execution time: `{args.entry_time}` option open",
        f"- Exit execution time: next trading day `{args.exit_time}` option open",
        "- Expiry rule: first weekly expiry strictly after entry date",
        "- ATM rule: nearest 50 using the spot signal close",
        f"- Capital base: Rs {int(args.capital):,}",
        (
            f"- Lot sizing: dynamic — `floor(capital / (lot_size × spot_close × {args.margin_fraction}))`, "
            f"minimum 1 lot (margin fraction ≈ NIFTY futures initial margin ~10% of contract value)"
        ),
        "- Lot size by expiry period (source: details.md + NSE circulars):",
        "  - Pre 2021-10-07 expiry: **75**",
        "  - 2021-10-07 to 2024-04-25 expiry: **50**",
        "  - 2024-05-02 to 2024-11-21 expiry: **25**",
        "  - 2024-11-28 to 2025-12-30 expiry: **75** (SEBI ₹15L minimum contract mandate)",
        "  - 2026-01-01 onwards: **65**",
        f"- Execution slippage: {format_money(args.slippage_points_per_order)} point per order",
        f"- Brokerage: Rs {int(args.brokerage_per_order)} per order × 4 orders = Rs {int(args.brokerage_per_order * 4)} per trade",
        "- Spot data coverage: ~May 2022 – May 2026 (pre-May 2022 dates skipped due to missing spot data)",
        "",
        "## Results Summary",
        "",
        f"- First traded date: `{first_trade_date}`",
        f"- Last traded date: `{last_trade_date}`",
        f"- Traded days: `{len(traded_results)}`",
        f"- Skipped days: `{len(skipped_results)}`",
        f"- Above-SMA trade count: `{above_sma_count}`",
        f"- Below-SMA trade count: `{below_sma_count}`",
        f"- CE-buy count (bullish days): `{ce_buy_count}`",
        f"- PE-buy count (bearish days): `{pe_buy_count}`",
        f"- Winning days: `{winning_days}`",
        f"- Losing days: `{losing_days}`",
        f"- Break-even days: `{break_even_days}`",
        (
            f"- Max profit day: `{max_profit_day.entry_date}` with net P/L `{max_profit_day.net_pnl}`"
            if max_profit_day else "- Max profit day: `N/A`"
        ),
        (
            f"- Max loss day: `{max_loss_day.entry_date}` with net P/L `{max_loss_day.net_pnl}`"
            if max_loss_day else "- Max loss day: `N/A`"
        ),
        f"- Max consecutive wins: `{max_consecutive_wins}`",
        f"- Max consecutive losses: `{max_consecutive_losses}`",
        f"- Max drawdown: `{format_money(max_drawdown)}`",
        f"- Total Net P/L: `{format_money(net_total)}`",
        f"- Total Brokerage: `{format_money(brokerage_total)}`",
        f"- Gross P/L (before brokerage): `{format_money(gross_total)}`",
        f"- Buy-leg gross P/L: `{format_money(bought_gross_total)}`",
        f"- Sell-leg gross P/L: `{format_money(sold_gross_total)}`",
        (
            f"- CAGR: `{cagr:.2f}%` (on Rs {int(args.capital):,} capital)"
            if cagr is not None else "- CAGR: `N/A`"
        ),
        "",
        "## Lot Size Period Breakdown (Traded Days)",
        "",
    ]
    for ls in sorted(period_counts.keys()):
        lines.append(f"- Lot size {ls}: `{period_counts[ls]}` traded days")

    lines += [
        "",
        "## Exceptions",
        "",
    ]

    if skipped_results:
        for result in skipped_results:
            lines.append(f"- `{result.entry_date}`: `{result.skip_reason}`. {result.remarks}")
    else:
        lines.append("- None")

    lines += [
        "",
        "## Remarks",
        "",
        "- Exact timestamp matching is required; no nearest-candle fallback is allowed.",
        "- The `15:15` spot row is used as the `15:30` close proxy because the spot dataset has no exact `15:30` timestamp.",
        "- The `15:29` option row is used as the entry proxy because the options dataset has no exact `15:30` timestamp.",
        "- The NIFTY spot file is the source of truth for the trading calendar.",
        "- Expiry folder dates from NiftyOptions_2020_2026 are used as truth, handling Thursday/Tuesday expiry changes and holiday shifts.",
        f"- Lot count is computed fresh each trade: floor(capital / (lot_size × spot_close × {args.margin_fraction})), minimum 1 lot.",
        "- Margin fraction approximates NIFTY futures SPAN margin (~10% of contract value); see details.md for per-period estimates.",
        "- Both buy and sell legs use the same lot count for the trade.",
        "- Empty option CSVs (header-only) are treated as missing and cause the day to be skipped.",
        "- Equality between spot close and the SMA produces no trade for that day.",
        "- Both buy and sell option legs must have exact entry and exit timestamps for the trade to count.",
    ]

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
