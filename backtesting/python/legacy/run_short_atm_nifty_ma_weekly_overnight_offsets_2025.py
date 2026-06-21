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
DAYWISE_FILENAME = "short_atm_nifty_ma_weekly_overnight_offsets_2025_daywise.csv"
SUMMARY_FILENAME = "short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md"
LOG_FILENAME = "short_atm_nifty_ma_weekly_overnight_offsets_2025.log"
MONEYNESS_OTM = "OTM"
MONEYNESS_ITM = "ITM"


@dataclass(frozen=True)
class OffsetSpec:
    range_label: str
    moneyness: str
    offset_points: int


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
    range_label: str
    moneyness: str
    offset_points: str
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
    target_strike: str
    sold_side: str
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
        description=(
            "Backtest the 2025 overnight weekly directional short option strategy using "
            "NIFTY 25-SMA signals across OTM and ITM strike offsets."
        ),
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
    parser.add_argument("--otm-offsets", type=int, nargs="+", default=[100, 200, 300, 400, 500])
    parser.add_argument("--itm-offsets", type=int, nargs="+", default=[100, 200, 300])
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--lot-size", type=int, default=65)
    parser.add_argument("--lots", type=int, default=4)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
    args = parser.parse_args()

    if any(offset <= 0 for offset in args.otm_offsets + args.itm_offsets):
        parser.error("--otm-offsets and --itm-offsets must contain positive point offsets")

    return args


def build_offset_specs(args: argparse.Namespace) -> List[OffsetSpec]:
    specs = [
        OffsetSpec(
            range_label=f"{MONEYNESS_OTM}_{offset}",
            moneyness=MONEYNESS_OTM,
            offset_points=offset,
        )
        for offset in args.otm_offsets
    ]
    specs.extend(
        OffsetSpec(
            range_label=f"{MONEYNESS_ITM}_{offset}",
            moneyness=MONEYNESS_ITM,
            offset_points=offset,
        )
        for offset in args.itm_offsets
    )
    return specs


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


def target_strike_for_offset(atm_strike: int, sold_side: str, spec: OffsetSpec) -> int:
    if sold_side == "PE":
        return atm_strike - spec.offset_points if spec.moneyness == MONEYNESS_OTM else atm_strike + spec.offset_points
    return atm_strike + spec.offset_points if spec.moneyness == MONEYNESS_OTM else atm_strike - spec.offset_points


def format_money(value: float) -> str:
    return f"{value:.2f}"


def leg_pnl_after_slippage(raw_points_pnl: float, slippage_points_per_order: float) -> float:
    return raw_points_pnl - (2 * slippage_points_per_order)


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("short_atm_nifty_ma_weekly_overnight_offsets_2025")
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
    spec: OffsetSpec,
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
    target_strike: str = "",
    sold_side: str = "",
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
        range_label=spec.range_label,
        moneyness=spec.moneyness,
        offset_points=str(spec.offset_points),
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
        target_strike=target_strike,
        sold_side=sold_side,
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


def add_common_skip_results(
    results: List[TradeResult],
    offset_specs: List[OffsetSpec],
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
    sold_side: str = "",
    remarks: str = "",
) -> None:
    for spec in offset_specs:
        target_strike = ""
        if atm_strike and sold_side:
            target_strike = str(target_strike_for_offset(int(atm_strike), sold_side, spec))
        results.append(
            make_result(
                spec=spec,
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
                target_strike=target_strike,
                sold_side=sold_side,
                remarks=remarks,
            )
        )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    offset_specs = build_offset_specs(args)
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
                add_common_skip_results(
                    results=results,
                    offset_specs=offset_specs,
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="missing_spot_signal_timestamp",
                    spot_signal_timestamp=spot_signal_timestamp,
                    remarks=f"Missing spot signal timestamp {spot_signal_timestamp}",
                )
                logger.info("SKIPPED date=%s reason=missing_spot_signal_timestamp all_ranges=1", entry_date)
                continue

            spot_sma_25, observed_count = compute_spot_sma_including_current(
                spot_data,
                spot_signal_timestamp,
                args.ma_period,
            )
            if spot_sma_25 is None:
                add_common_skip_results(
                    results=results,
                    offset_specs=offset_specs,
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
                logger.info("SKIPPED date=%s reason=insufficient_spot_history all_ranges=1", entry_date)
                continue

            spot_signal_close = spot_signal_row.close_text
            spot_sma_text = format_money(spot_sma_25)
            atm_strike = round_to_nearest_50(spot_signal_row.close_value)
            strike_text = str(atm_strike)

            if spot_signal_row.close_value > spot_sma_25:
                spot_signal_relation = "ABOVE_SMA"
                sold_side = "PE"
            elif spot_signal_row.close_value < spot_sma_25:
                spot_signal_relation = "BELOW_SMA"
                sold_side = "CE"
            else:
                add_common_skip_results(
                    results=results,
                    offset_specs=offset_specs,
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
                logger.info("SKIPPED date=%s reason=equal_close_and_sma all_ranges=1", entry_date)
                continue

            next_trading_day = next_day_by_day[entry_date]
            if not next_trading_day:
                add_common_skip_results(
                    results=results,
                    offset_specs=offset_specs,
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="no_next_trading_day",
                    spot_signal_timestamp=spot_signal_timestamp,
                    spot_signal_close=spot_signal_close,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation=spot_signal_relation,
                    atm_strike=strike_text,
                    sold_side=sold_side,
                    remarks="No next trading day exists in the dataset.",
                )
                logger.info("SKIPPED date=%s reason=no_next_trading_day all_ranges=1", entry_date)
                continue

            expiry_date = next_expiry_after(expiries, entry_date)
            if expiry_date is None:
                add_common_skip_results(
                    results=results,
                    offset_specs=offset_specs,
                    entry_date=entry_date,
                    status="SKIPPED",
                    skip_reason="no_next_weekly_expiry",
                    next_trading_day=next_trading_day,
                    spot_signal_timestamp=spot_signal_timestamp,
                    spot_signal_close=spot_signal_close,
                    spot_sma_25=spot_sma_text,
                    spot_signal_relation=spot_signal_relation,
                    atm_strike=strike_text,
                    sold_side=sold_side,
                    remarks="No weekly expiry folder exists strictly after the trade date.",
                )
                logger.info("SKIPPED date=%s reason=no_next_weekly_expiry all_ranges=1", entry_date)
                continue

            option_exit_timestamp = build_timestamp(next_trading_day, args.exit_time)
            option_suffix = expiry_suffix(expiry_date)

            for spec in offset_specs:
                target_strike = target_strike_for_offset(atm_strike, sold_side, spec)
                target_strike_text = str(target_strike)
                if target_strike <= 0:
                    result = make_result(
                        spec=spec,
                        entry_date=entry_date,
                        status="SKIPPED",
                        skip_reason="invalid_target_strike",
                        expiry_date=expiry_date,
                        next_trading_day=next_trading_day,
                        spot_signal_timestamp=spot_signal_timestamp,
                        spot_signal_close=spot_signal_close,
                        spot_sma_25=spot_sma_text,
                        spot_signal_relation=spot_signal_relation,
                        atm_strike=strike_text,
                        target_strike=target_strike_text,
                        sold_side=sold_side,
                        remarks=f"Computed target strike {target_strike_text} is not valid.",
                    )
                    results.append(result)
                    logger.info(
                        "SKIPPED date=%s range=%s reason=invalid_target_strike target=%s",
                        entry_date,
                        spec.range_label,
                        target_strike_text,
                    )
                    continue

                contract_path = args.options_dir / expiry_date / f"NIFTY_{target_strike}_{sold_side}_{option_suffix}.csv"
                contract_data = load_contract(contract_path, contract_cache)
                if contract_data is None:
                    result = make_result(
                        spec=spec,
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
                        target_strike=target_strike_text,
                        sold_side=sold_side,
                        contract_name=contract_path.name,
                        option_entry_timestamp=option_entry_timestamp,
                        option_exit_timestamp=option_exit_timestamp,
                        remarks=f"Missing option file: {contract_path.name}",
                    )
                    results.append(result)
                    logger.info(
                        "SKIPPED date=%s range=%s expiry=%s side=%s atm=%s target=%s reason=missing_option_file",
                        entry_date,
                        spec.range_label,
                        expiry_date,
                        sold_side,
                        strike_text,
                        target_strike_text,
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
                        spec=spec,
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
                        target_strike=target_strike_text,
                        sold_side=sold_side,
                        contract_name=contract_path.name,
                        option_entry_timestamp=option_entry_timestamp,
                        option_exit_timestamp=option_exit_timestamp,
                        remarks=remarks,
                    )
                    results.append(result)
                    logger.info(
                        "SKIPPED date=%s range=%s expiry=%s side=%s atm=%s target=%s reason=missing_entry_or_exit_timestamp",
                        entry_date,
                        spec.range_label,
                        expiry_date,
                        sold_side,
                        strike_text,
                        target_strike_text,
                    )
                    continue

                gross_pnl = (
                    leg_pnl_after_slippage(
                        entry_row.open_value - exit_row.open_value,
                        args.slippage_points_per_order,
                    )
                    * contract_multiplier
                )
                brokerage = round_trip_brokerage
                net_pnl = gross_pnl - brokerage
                result = make_result(
                    spec=spec,
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
                    target_strike=target_strike_text,
                    sold_side=sold_side,
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
                    "TRADED date=%s range=%s expiry=%s side=%s atm=%s target=%s gross=%s brokerage=%s net=%s",
                    entry_date,
                    spec.range_label,
                    expiry_date,
                    sold_side,
                    strike_text,
                    target_strike_text,
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
        "range_label",
        "moneyness",
        "offset_points",
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
        "target_strike",
        "sold_side",
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


def metrics_for_results(results: List[TradeResult]) -> Dict[str, object]:
    traded_results = [result for result in results if result.status == "TRADED"]
    skipped_results = [result for result in results if result.status == "SKIPPED"]
    gross_total = sum(float(result.gross_pnl) for result in traded_results)
    brokerage_total = sum(float(result.brokerage) for result in traded_results)
    net_total = sum(float(result.net_pnl) for result in traded_results)
    ce_sell_count = sum(1 for result in traded_results if result.sold_side == "CE")
    pe_sell_count = sum(1 for result in traded_results if result.sold_side == "PE")
    net_pnl_values = [float(result.net_pnl) for result in traded_results]
    winning_days = sum(1 for net_pnl in net_pnl_values if net_pnl > 0)
    losing_days = sum(1 for net_pnl in net_pnl_values if net_pnl < 0)
    break_even_days = sum(1 for net_pnl in net_pnl_values if net_pnl == 0)
    max_consecutive_wins, max_consecutive_losses = compute_max_consecutive_streaks(net_pnl_values)
    max_drawdown = compute_max_drawdown(net_pnl_values)
    max_profit_day = max(traded_results, key=lambda result: float(result.net_pnl), default=None)
    max_loss_day = min(traded_results, key=lambda result: float(result.net_pnl), default=None)

    return {
        "traded_results": traded_results,
        "skipped_results": skipped_results,
        "gross_total": gross_total,
        "brokerage_total": brokerage_total,
        "net_total": net_total,
        "ce_sell_count": ce_sell_count,
        "pe_sell_count": pe_sell_count,
        "winning_days": winning_days,
        "losing_days": losing_days,
        "break_even_days": break_even_days,
        "max_consecutive_wins": max_consecutive_wins,
        "max_consecutive_losses": max_consecutive_losses,
        "max_drawdown": max_drawdown,
        "max_profit_day": max_profit_day,
        "max_loss_day": max_loss_day,
    }


def write_range_detail(lines: List[str], range_label: str, results: List[TradeResult]) -> None:
    metrics = metrics_for_results(results)
    traded_results: List[TradeResult] = metrics["traded_results"]  # type: ignore[assignment]
    skipped_results: List[TradeResult] = metrics["skipped_results"]  # type: ignore[assignment]
    max_profit_day: Optional[TradeResult] = metrics["max_profit_day"]  # type: ignore[assignment]
    max_loss_day: Optional[TradeResult] = metrics["max_loss_day"]  # type: ignore[assignment]

    lines.extend(
        [
            f"### {range_label}",
            "",
            f"- Traded days: `{len(traded_results)}`",
            f"- Skipped days: `{len(skipped_results)}`",
            f"- CE-sell count: `{metrics['ce_sell_count']}`",
            f"- PE-sell count: `{metrics['pe_sell_count']}`",
            f"- Winning days: `{metrics['winning_days']}`",
            f"- Losing days: `{metrics['losing_days']}`",
            f"- Break-even days: `{metrics['break_even_days']}`",
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
            f"- Max consecutive wins: `{metrics['max_consecutive_wins']}`",
            f"- Max consecutive losses: `{metrics['max_consecutive_losses']}`",
            f"- Max drawdown: `{format_money(metrics['max_drawdown'])}`",
            f"- Total Profit/Loss: `{format_money(metrics['net_total'])}`",
            f"- Total Brokerage: `{format_money(metrics['brokerage_total'])}`",
            f"- Profit/Loss without Brokerage: `{format_money(metrics['gross_total'])}`",
            "",
        ]
    )


def write_summary(results: List[TradeResult], output_path: Path, args: argparse.Namespace) -> None:
    offset_specs = build_offset_specs(args)
    results_by_range = {
        spec.range_label: [result for result in results if result.range_label == spec.range_label]
        for spec in offset_specs
    }

    lines: List[str] = [
        "# 2025 Overnight Weekly Short NIFTY 25-SMA Strike-Offset Backtest",
        "",
        "## Strategy Details",
        "",
        "- Signal source: NIFTY 15-minute close",
        f"- Signal bar time: `{args.signal_time}` row as `15:30` close proxy",
        f"- MA rule: {args.ma_period}-SMA of spot closes including the signal bar",
        "- Direction rule: above SMA -> short PE; below SMA -> short CE; equal -> no trade",
        "- Strike ranges: OTM 100/200/300/400/500 and ITM 100/200/300, each tested independently",
        "- OTM/ITM is interpreted relative to the sold option side",
        f"- Entry execution time: `{args.entry_time}` option open",
        f"- Exit execution time: next trading day `{args.exit_time}` option open",
        "- Expiry rule: first weekly expiry strictly after entry date",
        "- ATM reference rule: nearest 50 using the spot signal close",
        f"- Contract multiplier: {args.lot_size} x {args.lots} = {args.lot_size * args.lots} rupees per option point",
        f"- Execution slippage: {format_money(args.slippage_points_per_order)} point per order, applied against every entry and exit",
        (
            f"- Brokerage rule: Rs {int(args.brokerage_per_order)} per order, "
            f"so one completed short leg pays Rs {int(args.brokerage_per_order * 2)}"
        ),
        "",
        "## Range Comparison",
        "",
        "| Range | Traded | Skipped | CE Sell | PE Sell | Wins | Losses | Max DD | Net P/L | Brokerage | Gross P/L |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for spec in offset_specs:
        metrics = metrics_for_results(results_by_range[spec.range_label])
        lines.append(
            "| "
            f"{spec.range_label} | "
            f"{len(metrics['traded_results'])} | "
            f"{len(metrics['skipped_results'])} | "
            f"{metrics['ce_sell_count']} | "
            f"{metrics['pe_sell_count']} | "
            f"{metrics['winning_days']} | "
            f"{metrics['losing_days']} | "
            f"{format_money(metrics['max_drawdown'])} | "
            f"{format_money(metrics['net_total'])} | "
            f"{format_money(metrics['brokerage_total'])} | "
            f"{format_money(metrics['gross_total'])} |"
        )

    lines.extend(
        [
            "",
            "## Range Details",
            "",
        ]
    )

    for spec in offset_specs:
        write_range_detail(lines, spec.range_label, results_by_range[spec.range_label])

    lines.extend(
        [
            "## Exceptions By Range",
            "",
        ]
    )

    for spec in offset_specs:
        skipped_results = [
            result
            for result in results_by_range[spec.range_label]
            if result.status == "SKIPPED"
        ]
        lines.extend([f"### {spec.range_label}", ""])
        if skipped_results:
            for result in skipped_results:
                lines.append(f"- `{result.entry_date}`: `{result.skip_reason}`. {result.remarks}")
        else:
            lines.append("- None")
        lines.append("")

    lines.extend(
        [
            "## Remarks",
            "",
            "- Exact timestamp matching is required; no nearest-candle fallback is allowed.",
            "- The `15:15` spot row is used as the `15:30` close proxy because the spot dataset has no exact `15:30` timestamp.",
            "- The `15:29` option row is used as the sell proxy because the options dataset has no exact `15:30` timestamp.",
            "- The NIFTY spot file is the source of truth for the trading calendar.",
            "- Expiry folder dates are used as truth, which naturally handles Tuesday special expiries and holiday shifts.",
            "- Equality between the spot close and the SMA produces no trade for every range on that date.",
            "- Missing option files or timestamps skip only the affected range/date.",
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
