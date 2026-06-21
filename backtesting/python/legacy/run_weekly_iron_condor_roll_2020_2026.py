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
DAYWISE_FILENAME = "weekly_iron_condor_roll_2020_2026_daywise.csv"
SUMMARY_FILENAME = "weekly_iron_condor_roll_2020_2026_summary.md"
LOG_FILENAME = "weekly_iron_condor_roll_2020_2026.log"


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
    entry_expiry: str          # expiry day just passed — the roll trigger date
    entry_date: str            # first trading day after entry_expiry — actual entry date
    status: str
    skip_reason: str
    target_expiry: str         # expiry the condor is targeting
    spot_entry_timestamp: str
    spot_entry_open: str
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
    net_entry_credit_points: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Backtest a weekly Nifty short iron condor that rolls each expiry cycle. "
            "Enters at 09:15 on the first trading day after each expiry, targeting the "
            "following expiry. Exits at 15:15 on that target expiry day."
        ),
    )
    parser.add_argument(
        "--spot-file",
        type=Path,
        default=repo_root / "nifty" / "NIFTY50_INDEX_15m_last_4y.csv",
        help="15-minute (or 1-minute) NIFTY spot CSV. Covers ~May 2022–May 2026.",
    )
    parser.add_argument(
        "--options-dir",
        type=Path,
        default=repo_root / "NiftyOptions_2020_2026" / "Options",
        help="Directory containing expiry-date sub-folders with option CSVs.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=repo_root / "backtesting" / "results",
    )
    parser.add_argument(
        "--entry-time",
        default="09:15",
        help="Time (HH:MM) to enter on the first trading day after expiry (default: 09:15).",
    )
    parser.add_argument(
        "--exit-time",
        default="15:15",
        help="Time (HH:MM) to exit on the target expiry day (default: 15:15, 15 min before close).",
    )
    parser.add_argument(
        "--sell-offset",
        type=int,
        default=250,
        help="Points away from ATM for the short CE and PE legs (default: 250).",
    )
    parser.add_argument(
        "--buy-offset",
        type=int,
        default=450,
        help="Points away from ATM for the long CE and PE hedge legs (default: 450).",
    )
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--lots", type=int, default=1)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
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


def leg_pnl_after_slippage(raw_points_pnl: float, slippage: float) -> float:
    return raw_points_pnl - (2 * slippage)


def lot_size_for_expiry(expiry_date: str) -> int:
    # Nifty lot size history (source: details.md):
    #   pre-Oct 7 2021 expiry  → 75
    #   Oct 7 2021 – Apr 25 2024 expiry → 50
    #   May 2 2024 expiry onwards → 25
    if expiry_date < "2021-10-07":
        return 75
    if expiry_date <= "2024-04-25":
        return 50
    return 25


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("weekly_iron_condor_roll_2020_2026")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def load_spot_data(spot_file: Path) -> Tuple[List[str], Dict[str, Dict[str, PriceRow]]]:
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
            ts = row["timestamp"]
            rows_by_timestamp[ts] = PriceRow(
                timestamp=ts,
                open_value=float(row["open"]),
                open_text=row["open"],
            )

    contract_data = ContractData(path=contract_path, rows_by_timestamp=rows_by_timestamp)
    cache[contract_path] = contract_data
    return contract_data


def make_skipped_result(
    entry_expiry: str,
    entry_date: str,
    target_expiry: str,
    spot_entry_timestamp: str,
    spot_entry_open: str,
    atm_strike: str,
    skip_reason: str,
    remarks: str,
) -> TradeResult:
    return TradeResult(
        entry_expiry=entry_expiry,
        entry_date=entry_date,
        status="SKIPPED",
        skip_reason=skip_reason,
        target_expiry=target_expiry,
        spot_entry_timestamp=spot_entry_timestamp,
        spot_entry_open=spot_entry_open,
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
        net_entry_credit_points="0.00",
        gross_pnl="0.00",
        brokerage="0.00",
        net_pnl="0.00",
        remarks=remarks,
    )


def first_trading_day_after(date: str, trading_days: List[str]) -> Optional[str]:
    for day in trading_days:
        if day > date:
            return day
    return None


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    trading_days, spot_rows_by_day = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    contract_cache: Dict[Path, ContractData] = {}
    cached_expiry = ""
    results: List[TradeResult] = []
    round_trip_brokerage = args.brokerage_per_order * 8

    try:
        # Each consecutive pair: (entry_expiry, target_expiry)
        # entry_expiry = the expiry that just passed (triggers the roll)
        # target_expiry = the expiry we're now selling into
        # actual entry = first trading day strictly after entry_expiry
        for idx, entry_expiry in enumerate(expiries[:-1]):
            target_expiry = expiries[idx + 1]

            entry_date = first_trading_day_after(entry_expiry, trading_days)
            if entry_date is None or entry_date >= target_expiry:
                result = make_skipped_result(
                    entry_expiry=entry_expiry,
                    entry_date=entry_date or "",
                    target_expiry=target_expiry,
                    spot_entry_timestamp="",
                    spot_entry_open="",
                    atm_strike="",
                    skip_reason="no_trading_day_between_expiries",
                    remarks=(
                        f"No spot trading day found strictly between {entry_expiry} "
                        f"and {target_expiry}."
                    ),
                )
                results.append(result)
                logger.info("SKIPPED entry_expiry=%s reason=%s", entry_expiry, result.skip_reason)
                continue

            entry_timestamp = build_timestamp(entry_date, args.entry_time)
            exit_timestamp = build_timestamp(target_expiry, args.exit_time)

            spot_entry_row = spot_rows_by_day.get(entry_date, {}).get(entry_timestamp)
            if spot_entry_row is None:
                result = make_skipped_result(
                    entry_expiry=entry_expiry,
                    entry_date=entry_date,
                    target_expiry=target_expiry,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open="",
                    atm_strike="",
                    skip_reason="missing_spot_entry_timestamp",
                    remarks=f"Spot file has no candle at {entry_timestamp}.",
                )
                results.append(result)
                logger.info("SKIPPED entry_expiry=%s reason=%s", entry_expiry, result.skip_reason)
                continue

            atm_strike = round_to_nearest_50(spot_entry_row.open_value)
            sell_ce_strike = round_to_nearest_50(float(atm_strike + args.sell_offset))
            sell_pe_strike = round_to_nearest_50(float(atm_strike - args.sell_offset))
            buy_ce_strike = round_to_nearest_50(float(atm_strike + args.buy_offset))
            buy_pe_strike = round_to_nearest_50(float(atm_strike - args.buy_offset))
            atm_strike_text = str(atm_strike)

            if target_expiry != cached_expiry:
                contract_cache.clear()
                cached_expiry = target_expiry

            suffix = expiry_suffix(target_expiry)
            sell_ce_path = args.options_dir / target_expiry / f"NIFTY_{sell_ce_strike}_CE_{suffix}.csv"
            sell_pe_path = args.options_dir / target_expiry / f"NIFTY_{sell_pe_strike}_PE_{suffix}.csv"
            buy_ce_path = args.options_dir / target_expiry / f"NIFTY_{buy_ce_strike}_CE_{suffix}.csv"
            buy_pe_path = args.options_dir / target_expiry / f"NIFTY_{buy_pe_strike}_PE_{suffix}.csv"

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
                    entry_expiry=entry_expiry,
                    entry_date=entry_date,
                    target_expiry=target_expiry,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    atm_strike=atm_strike_text,
                    skip_reason="missing_contract_file",
                    remarks=f"Missing: {', '.join(missing_files)}",
                )
                results.append(result)
                logger.info(
                    "SKIPPED entry_expiry=%s entry=%s expiry=%s atm=%s reason=%s",
                    entry_expiry, entry_date, target_expiry, atm_strike_text, result.remarks,
                )
                continue

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
                (f"{sell_ce_path.name} entry@{entry_timestamp}", sell_ce_entry),
                (f"{sell_ce_path.name} exit@{exit_timestamp}", sell_ce_exit),
                (f"{sell_pe_path.name} entry@{entry_timestamp}", sell_pe_entry),
                (f"{sell_pe_path.name} exit@{exit_timestamp}", sell_pe_exit),
                (f"{buy_ce_path.name} entry@{entry_timestamp}", buy_ce_entry),
                (f"{buy_ce_path.name} exit@{exit_timestamp}", buy_ce_exit),
                (f"{buy_pe_path.name} entry@{entry_timestamp}", buy_pe_entry),
                (f"{buy_pe_path.name} exit@{exit_timestamp}", buy_pe_exit),
            ]:
                if row is None:
                    missing_candles.append(label)

            if missing_candles:
                result = make_skipped_result(
                    entry_expiry=entry_expiry,
                    entry_date=entry_date,
                    target_expiry=target_expiry,
                    spot_entry_timestamp=entry_timestamp,
                    spot_entry_open=spot_entry_row.open_text,
                    atm_strike=atm_strike_text,
                    skip_reason="missing_candle_at_timestamp",
                    remarks="; ".join(missing_candles),
                )
                results.append(result)
                logger.info(
                    "SKIPPED entry_expiry=%s entry=%s expiry=%s atm=%s reason=%s",
                    entry_expiry, entry_date, target_expiry, atm_strike_text, result.remarks,
                )
                continue

            # P&L: short legs profit when premium decays; long legs profit when they gain value
            lot_size = lot_size_for_expiry(target_expiry)
            contract_multiplier = lot_size * args.lots

            sell_ce_pnl = leg_pnl_after_slippage(
                sell_ce_entry.open_value - sell_ce_exit.open_value,  # type: ignore[union-attr]
                args.slippage_points_per_order,
            )
            sell_pe_pnl = leg_pnl_after_slippage(
                sell_pe_entry.open_value - sell_pe_exit.open_value,  # type: ignore[union-attr]
                args.slippage_points_per_order,
            )
            buy_ce_pnl = leg_pnl_after_slippage(
                buy_ce_exit.open_value - buy_ce_entry.open_value,  # type: ignore[union-attr]
                args.slippage_points_per_order,
            )
            buy_pe_pnl = leg_pnl_after_slippage(
                buy_pe_exit.open_value - buy_pe_entry.open_value,  # type: ignore[union-attr]
                args.slippage_points_per_order,
            )
            gross_pnl = (sell_ce_pnl + sell_pe_pnl + buy_ce_pnl + buy_pe_pnl) * contract_multiplier
            net_pnl = gross_pnl - round_trip_brokerage

            net_entry_credit = (
                sell_ce_entry.open_value + sell_pe_entry.open_value  # type: ignore[union-attr]
                - buy_ce_entry.open_value - buy_pe_entry.open_value  # type: ignore[union-attr]
            )

            result = TradeResult(
                entry_expiry=entry_expiry,
                entry_date=entry_date,
                status="TRADED",
                skip_reason="",
                target_expiry=target_expiry,
                spot_entry_timestamp=entry_timestamp,
                spot_entry_open=spot_entry_row.open_text,
                atm_strike=atm_strike_text,
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
                net_entry_credit_points=format_money(net_entry_credit),
                gross_pnl=format_money(gross_pnl),
                brokerage=format_money(round_trip_brokerage),
                net_pnl=format_money(net_pnl),
                remarks="",
            )
            results.append(result)
            logger.info(
                "TRADED entry_expiry=%s entry=%s expiry=%s atm=%s lot_size=%s "
                "sell_ce=%s sell_pe=%s buy_ce=%s buy_pe=%s credit=%.2f gross=%s net=%s",
                entry_expiry, entry_date, target_expiry, atm_strike_text, lot_size,
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
        "entry_expiry",
        "entry_date",
        "status",
        "skip_reason",
        "target_expiry",
        "spot_entry_timestamp",
        "spot_entry_open",
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
        "net_entry_credit_points",
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


def write_summary(results: List[TradeResult], output_path: Path, args: argparse.Namespace) -> None:
    traded = [r for r in results if r.status == "TRADED"]
    skipped = [r for r in results if r.status == "SKIPPED"]
    gross_total = sum(float(r.gross_pnl) for r in traded)
    brokerage_total = sum(float(r.brokerage) for r in traded)
    net_total = sum(float(r.net_pnl) for r in traded)

    lines: List[str] = [
        "# Weekly Nifty Short Iron Condor Roll (2020-2026) — Backtest",
        "",
        "## Strategy Details",
        "",
        "- **Structure**: Short iron condor — sell CE and PE at `ATM + sell_offset` / "
        "`ATM - sell_offset`, buy CE and PE at `ATM + buy_offset` / `ATM - buy_offset` as hedge",
        f"- **Sell offset**: {args.sell_offset} points from ATM",
        f"- **Buy offset (hedge)**: {args.buy_offset} points from ATM",
        "- **Roll trigger**: each weekly expiry day in the options dataset",
        f"- **Entry**: {args.entry_time} on the first spot-data trading day strictly after each expiry",
        f"- **Exit**: {args.exit_time} on the target expiry day (15 min before market close)",
        "- **Expiry targeted**: the next available expiry folder after the entry expiry",
        "- **ATM rule**: nearest 50 using spot open at entry timestamp",
        f"- **Data source**: `{args.options_dir.name}` options + `{args.spot_file.name}` spot",
        f"- **Lot size**: dynamic per expiry date — 75 (pre-Oct 2021), 50 (Oct 2021–Apr 2024), "
        f"25 (May 2024+); multiplied by {args.lots} lot(s)",
        f"- **Slippage**: {format_money(args.slippage_points_per_order)} pt per order "
        f"(entry + exit = {format_money(2 * args.slippage_points_per_order)} pts per leg)",
        f"- **Brokerage**: Rs {int(args.brokerage_per_order)} per order, "
        f"Rs {int(args.brokerage_per_order * 8)} per completed condor (4 legs x 2 sides)",
        "- **No stop-loss, no adjustments**",
        "",
        "## Results Summary",
        "",
        f"- Expiry pairs processed : `{len(results)}`",
        f"- Trades executed        : `{len(traded)}`",
        f"- Trades skipped         : `{len(skipped)}`",
        f"- Gross P&L              : `{format_money(gross_total)}`",
        f"- Total Brokerage        : `{format_money(brokerage_total)}`",
        f"- Net P&L                : `{format_money(net_total)}`",
        "",
        "## Skipped Trades",
        "",
    ]

    if skipped:
        for r in skipped:
            lines.append(
                f"- `{r.entry_expiry}` (entry `{r.entry_date}`) -> `{r.target_expiry}`: "
                f"`{r.skip_reason}`. {r.remarks}"
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Each expiry folder in `NiftyOptions_2020_2026/Options` contains option data "
            "starting from the day after the previous expiry through the expiry day itself. "
            "Entry is therefore placed on the first available spot trading day after each expiry, "
            "not on the expiry day itself.",
            "- Exit is at 15:15 on the target expiry day. Deeply OTM contracts that see no "
            "trading volume at 15:15 will cause a skip.",
            "- Lot size is applied dynamically per trade based on the target expiry date "
            "(75 pre-Oct 2021, 50 Oct 2021-Apr 2024, 25 May 2024+). "
            "The `lot_size` column in the daywise CSV shows the value used for each trade.",
            "- The spot file covers roughly May 2022 to May 2026; expiry dates before that "
            "window are skipped due to missing spot data.",
            "- Gross P&L includes slippage but excludes brokerage.",
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
