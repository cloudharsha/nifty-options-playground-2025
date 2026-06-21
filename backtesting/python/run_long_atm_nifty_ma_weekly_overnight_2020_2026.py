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
DAYWISE_FILENAME = "long_atm_nifty_ma_weekly_overnight_2020_2026_daywise.csv"
SUMMARY_FILENAME = "long_atm_nifty_ma_weekly_overnight_2020_2026_summary.md"
LOG_FILENAME = "long_atm_nifty_ma_weekly_overnight_2020_2026.log"
CAPITAL_FOR_CAGR = 5_00_000.0  # Rs 5L reference base


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
    qty: str
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


def qty_for_expiry(expiry_date: str) -> Tuple[int, int]:
    """Return (lot_size, lots) targeting ~300 quantity, per NIFTY lot size history."""
    if expiry_date < "2021-10-07":
        return 75, 4   # 300
    if expiry_date <= "2024-04-25":
        return 50, 6   # 300
    if expiry_date <= "2024-11-21":
        return 25, 12  # 300
    if expiry_date <= "2025-12-30":
        return 75, 4   # 300
    return 65, 5       # 325


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Backtest overnight weekly long ATM NIFTY 25-SMA strategy over 2020-2026.",
    )
    parser.add_argument("--spot-file", type=Path,
                        default=repo_root / "nifty" / "NIFTY50_INDEX_15m_last_7y.csv")
    parser.add_argument("--options-dir", type=Path,
                        default=repo_root / "NiftyOptions_2020_2026" / "Options")
    parser.add_argument("--results-dir", type=Path,
                        default=repo_root / "backtesting" / "results")
    parser.add_argument("--signal-time", default="15:15")
    parser.add_argument("--entry-time", default="15:29")
    parser.add_argument("--exit-time", default="09:16")
    parser.add_argument("--ma-period", type=int, default=25)
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
    return parser.parse_args()


def build_timestamp(day: str, time_text: str) -> str:
    h, m = time_text.split(":")
    return f"{day}T{h}:{m}:00{IST_SUFFIX}"


def round_to_nearest_50(price: float) -> int:
    remainder = price % 50
    rounded_down = int(price - remainder)
    return rounded_down if remainder < 25 else rounded_down + 50


def format_money(value: float) -> str:
    return f"{value:.2f}"


def leg_pnl_after_slippage(raw_pts: float, slip: float) -> float:
    return raw_pts - (2 * slip)


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("long_atm_nifty_ma_weekly_overnight_2020_2026")
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

    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            spot_row = SpotRow(
                timestamp=ts,
                open_value=float(row["open"]), open_text=row["open"],
                close_value=float(row["close"]), close_text=row["close"],
            )
            index_by_timestamp[ts] = len(ordered_rows)
            ordered_rows.append(spot_row)
            rows_by_timestamp[ts] = spot_row
            day = ts[:10]
            if day not in seen_days:
                trading_days.append(day)
                seen_days.add(day)

    return SpotData(rows_by_timestamp, ordered_rows, index_by_timestamp), trading_days


def load_expiry_folders(options_dir: Path) -> List[str]:
    return sorted(p.name for p in options_dir.iterdir() if p.is_dir())


def next_expiry_after(expiries: List[str], entry_date: str) -> Optional[str]:
    for expiry in expiries:
        if expiry > entry_date:
            return expiry
    return None


def expiry_suffix(expiry_date: str) -> str:
    return datetime.datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%d_%b_%y").upper()


def load_contract(contract_path: Path, cache: Dict[Path, ContractData]) -> Optional[ContractData]:
    if contract_path in cache:
        return cache[contract_path]
    if not contract_path.exists():
        return None
    rows: Dict[str, OptionRow] = {}
    with contract_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            rows[ts] = OptionRow(timestamp=ts, open_value=float(row["open"]), open_text=row["open"])
    cd = ContractData(path=contract_path, rows_by_timestamp=rows)
    cache[contract_path] = cd
    return cd


def compute_sma(spot_data: SpotData, timestamp: str, period: int) -> Tuple[Optional[float], int]:
    idx = spot_data.index_by_timestamp.get(timestamp)
    if idx is None:
        return None, 0
    n = idx + 1
    if n < period:
        return None, n
    sma = sum(r.close_value for r in spot_data.ordered_rows[idx - period + 1: idx + 1]) / period
    return sma, n


def make_result(entry_date: str, status: str, skip_reason: str, lot_size: int = 0, lots: int = 0,
                expiry_date: str = "", next_trading_day: str = "", spot_signal_timestamp: str = "",
                spot_signal_close: str = "", spot_sma_25: str = "", spot_signal_relation: str = "",
                atm_strike: str = "", bought_side: str = "", contract_name: str = "",
                option_entry_timestamp: str = "", option_entry_open: str = "",
                option_exit_timestamp: str = "", option_exit_open: str = "",
                gross_pnl: float = 0.0, brokerage: float = 0.0, net_pnl: float = 0.0,
                remarks: str = "") -> TradeResult:
    return TradeResult(
        entry_date=entry_date, status=status, skip_reason=skip_reason,
        expiry_date=expiry_date, next_trading_day=next_trading_day,
        lot_size=str(lot_size), lots=str(lots), qty=str(lot_size * lots),
        spot_signal_timestamp=spot_signal_timestamp, spot_signal_close=spot_signal_close,
        spot_sma_25=spot_sma_25, spot_signal_relation=spot_signal_relation,
        atm_strike=atm_strike, bought_side=bought_side, contract_name=contract_name,
        option_entry_timestamp=option_entry_timestamp, option_entry_open=option_entry_open,
        option_exit_timestamp=option_exit_timestamp, option_exit_open=option_exit_open,
        gross_pnl=format_money(gross_pnl), brokerage=format_money(brokerage),
        net_pnl=format_money(net_pnl), remarks=remarks,
    )


def run_backtest(args: argparse.Namespace) -> List[TradeResult]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    spot_data, trading_days = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    contract_cache: Dict[Path, ContractData] = {}
    results: List[TradeResult] = []
    next_day_by_day = {
        trading_days[i]: trading_days[i + 1] if i + 1 < len(trading_days) else ""
        for i in range(len(trading_days))
    }
    round_trip_brokerage = args.brokerage_per_order * 2

    try:
        for entry_date in trading_days:
            sig_ts = build_timestamp(entry_date, args.signal_time)
            entry_ts = build_timestamp(entry_date, args.entry_time)
            sig_row = spot_data.rows_by_timestamp.get(sig_ts)
            if sig_row is None:
                results.append(make_result(entry_date, "SKIPPED", "missing_spot_signal_timestamp",
                                           spot_signal_timestamp=sig_ts,
                                           remarks=f"Missing spot signal timestamp {sig_ts}"))
                continue

            sma, n = compute_sma(spot_data, sig_ts, args.ma_period)
            if sma is None:
                results.append(make_result(entry_date, "SKIPPED", "insufficient_spot_history",
                                           spot_signal_timestamp=sig_ts,
                                           spot_signal_close=sig_row.close_text,
                                           remarks=f"{sig_ts} has {n} bars; needs {args.ma_period}"))
                continue

            sma_text = format_money(sma)
            atm = round_to_nearest_50(sig_row.close_value)

            if sig_row.close_value > sma:
                relation, side = "ABOVE_SMA", "CE"
            elif sig_row.close_value < sma:
                relation, side = "BELOW_SMA", "PE"
            else:
                results.append(make_result(entry_date, "SKIPPED", "equal_close_and_sma",
                                           spot_signal_timestamp=sig_ts,
                                           spot_signal_close=sig_row.close_text,
                                           spot_sma_25=sma_text, spot_signal_relation="EQUAL_SMA",
                                           atm_strike=str(atm),
                                           remarks=f"Close {sig_row.close_text} equals SMA {sma_text}"))
                continue

            next_day = next_day_by_day[entry_date]
            if not next_day:
                results.append(make_result(entry_date, "SKIPPED", "no_next_trading_day",
                                           spot_signal_timestamp=sig_ts, spot_signal_close=sig_row.close_text,
                                           spot_sma_25=sma_text, spot_signal_relation=relation,
                                           atm_strike=str(atm), bought_side=side,
                                           remarks="No next trading day in dataset."))
                continue

            expiry = next_expiry_after(expiries, entry_date)
            if expiry is None:
                results.append(make_result(entry_date, "SKIPPED", "no_next_weekly_expiry",
                                           next_trading_day=next_day,
                                           spot_signal_timestamp=sig_ts, spot_signal_close=sig_row.close_text,
                                           spot_sma_25=sma_text, spot_signal_relation=relation,
                                           atm_strike=str(atm), bought_side=side,
                                           remarks="No weekly expiry folder strictly after entry date."))
                continue

            lot_size, lots = qty_for_expiry(expiry)
            contract_multiplier = lot_size * lots
            exit_ts = build_timestamp(next_day, args.exit_time)
            suffix = expiry_suffix(expiry)
            contract_path = args.options_dir / expiry / f"NIFTY_{atm}_{side}_{suffix}.csv"
            cd = load_contract(contract_path, contract_cache)
            if cd is None:
                results.append(make_result(entry_date, "SKIPPED", "missing_option_file",
                                           lot_size=lot_size, lots=lots,
                                           expiry_date=expiry, next_trading_day=next_day,
                                           spot_signal_timestamp=sig_ts, spot_signal_close=sig_row.close_text,
                                           spot_sma_25=sma_text, spot_signal_relation=relation,
                                           atm_strike=str(atm), bought_side=side,
                                           contract_name=contract_path.name,
                                           remarks=f"Missing: {contract_path.name}"))
                continue

            entry_row = cd.rows_by_timestamp.get(entry_ts)
            exit_row = cd.rows_by_timestamp.get(exit_ts)
            missing = []
            if entry_row is None:
                missing.append(f"{contract_path.name} missing entry {entry_ts}")
            if exit_row is None:
                missing.append(f"{contract_path.name} missing exit {exit_ts}")
            if missing:
                results.append(make_result(entry_date, "SKIPPED", "missing_entry_or_exit_timestamp",
                                           lot_size=lot_size, lots=lots,
                                           expiry_date=expiry, next_trading_day=next_day,
                                           spot_signal_timestamp=sig_ts, spot_signal_close=sig_row.close_text,
                                           spot_sma_25=sma_text, spot_signal_relation=relation,
                                           atm_strike=str(atm), bought_side=side,
                                           contract_name=contract_path.name,
                                           option_entry_timestamp=entry_ts, option_exit_timestamp=exit_ts,
                                           remarks="; ".join(missing)))
                continue

            gross = leg_pnl_after_slippage(exit_row.open_value - entry_row.open_value,
                                           args.slippage_points_per_order) * contract_multiplier
            net = gross - round_trip_brokerage
            results.append(make_result(entry_date, "TRADED", "",
                                       lot_size=lot_size, lots=lots,
                                       expiry_date=expiry, next_trading_day=next_day,
                                       spot_signal_timestamp=sig_ts, spot_signal_close=sig_row.close_text,
                                       spot_sma_25=sma_text, spot_signal_relation=relation,
                                       atm_strike=str(atm), bought_side=side,
                                       contract_name=contract_path.name,
                                       option_entry_timestamp=entry_ts,
                                       option_entry_open=entry_row.open_text,
                                       option_exit_timestamp=exit_ts,
                                       option_exit_open=exit_row.open_text,
                                       gross_pnl=gross, brokerage=round_trip_brokerage, net_pnl=net))
            logger.info("TRADED date=%s expiry=%s side=%s atm=%s lot=%sx%s net=%s",
                        entry_date, expiry, side, atm, lot_size, lots, format_money(net))
    except Exception:
        logger.exception("Unexpected failure")
        raise

    return results


def compute_max_drawdown(net_pnls: List[float]) -> float:
    peak = dd = cum = 0.0
    for v in net_pnls:
        cum += v
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    return dd


def compute_cagr(net_total: float, capital: float, first_day: str, last_day: str) -> float:
    start = datetime.date.fromisoformat(first_day)
    end = datetime.date.fromisoformat(last_day)
    days = (end - start).days
    if days <= 0 or capital <= 0:
        return 0.0
    return ((1.0 + net_total / capital) ** (365.25 / days) - 1.0) * 100.0


def write_daywise_csv(results: List[TradeResult], path: Path) -> None:
    fields = [f.name for f in TradeResult.__dataclass_fields__.values()]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow(r.__dict__)


def write_summary(results: List[TradeResult], path: Path, args: argparse.Namespace,
                  trading_days: List[str]) -> None:
    traded = [r for r in results if r.status == "TRADED"]
    skipped = [r for r in results if r.status == "SKIPPED"]
    net_pnls = [float(r.net_pnl) for r in traded]
    gross_total = sum(float(r.gross_pnl) for r in traded)
    brok_total = sum(float(r.brokerage) for r in traded)
    net_total = sum(net_pnls)
    wins = sum(1 for v in net_pnls if v > 0)
    losses = sum(1 for v in net_pnls if v < 0)
    max_dd = compute_max_drawdown(net_pnls)
    best = max(traded, key=lambda r: float(r.net_pnl), default=None)
    worst = min(traded, key=lambda r: float(r.net_pnl), default=None)
    cagr = compute_cagr(net_total, CAPITAL_FOR_CAGR, trading_days[0], trading_days[-1]) if trading_days else 0.0
    ce_count = sum(1 for r in traded if r.bought_side == "CE")
    pe_count = sum(1 for r in traded if r.bought_side == "PE")

    lines = [
        "# Overnight Weekly Long ATM NIFTY 25-SMA Backtest (2020–2026)",
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
        "- Quantity: ~300 per trade (dynamic lot sizing by expiry era)",
        "  - pre-2021-10-07: 75 × 4 = 300 | 2021-10-07–2024-04-25: 50 × 6 = 300",
        "  - 2024-04-26–2024-11-21: 25 × 12 = 300 | 2024-11-22–2025-12-30: 75 × 4 = 300",
        "  - 2026+: 65 × 5 = 325",
        f"- Slippage: {format_money(args.slippage_points_per_order)} pt/order",
        f"- Brokerage: Rs {int(args.brokerage_per_order)}/order → Rs {int(args.brokerage_per_order * 2)}/trade",
        f"- Capital reference (CAGR): Rs {int(CAPITAL_FOR_CAGR):,}",
        "",
        "## Overall Results",
        "",
        f"- Traded days: `{len(traded)}`",
        f"- Skipped days: `{len(skipped)}`",
        f"- CE-buy count: `{ce_count}`",
        f"- PE-buy count: `{pe_count}`",
        f"- Winning days: `{wins}`",
        f"- Losing days: `{losses}`",
        f"- Win rate: `{wins / len(traded) * 100:.1f}%`" if traded else "- Win rate: `N/A`",
        f"- Net P/L: `{format_money(net_total)}`",
        f"- Total Brokerage: `{format_money(brok_total)}`",
        f"- Gross P/L: `{format_money(gross_total)}`",
        f"- Max drawdown: `{format_money(max_dd)}`",
        f"- CAGR (on Rs {int(CAPITAL_FOR_CAGR):,}): `{cagr:.2f}%`",
        f"- Best day: `{best.entry_date}` net `{best.net_pnl}`" if best else "- Best day: N/A",
        f"- Worst day: `{worst.entry_date}` net `{worst.net_pnl}`" if worst else "- Worst day: N/A",
        f"- Data range: `{trading_days[0]}` to `{trading_days[-1]}`" if trading_days else "",
        "",
        "## Yearly Summary",
        "",
        "| Year | Traded | Wins | Losses | Win% | Net P/L |",
        "|------|--------|------|--------|------|---------|",
    ]

    years: Dict[str, List[float]] = {}
    for r in traded:
        y = r.entry_date[:4]
        years.setdefault(y, []).append(float(r.net_pnl))
    for y in sorted(years):
        vals = years[y]
        w = sum(1 for v in vals if v > 0)
        l = sum(1 for v in vals if v < 0)
        pct = w / len(vals) * 100 if vals else 0.0
        lines.append(f"| {y} | {len(vals)} | {w} | {l} | {pct:.1f}% | {format_money(sum(vals))} |")

    lines += [
        "",
        "## Monthly P/L",
        "",
        "| Month | Traded | Win% | Net P/L |",
        "|-------|--------|------|---------|",
    ]
    months: Dict[str, List[float]] = {}
    for r in traded:
        m = r.entry_date[:7]
        months.setdefault(m, []).append(float(r.net_pnl))
    for m in sorted(months):
        vals = months[m]
        w = sum(1 for v in vals if v > 0)
        pct = w / len(vals) * 100 if vals else 0.0
        lines.append(f"| {m} | {len(vals)} | {pct:.1f}% | {format_money(sum(vals))} |")

    lines += [
        "",
        "## Exceptions",
        "",
    ]
    if skipped:
        for r in skipped:
            lines.append(f"- `{r.entry_date}`: `{r.skip_reason}`. {r.remarks}")
    else:
        lines.append("- None")

    lines += [
        "",
        "## Remarks",
        "",
        "- Exact timestamp matching; no nearest-candle fallback.",
        "- The 15:15 spot row is the 15:30 close proxy; 15:29 option open is the entry proxy.",
        "- Expiry folder dates are the source of truth for expiry selection.",
        "- Lot sizes are applied by expiry date to maintain ~300 quantity throughout the period.",
    ]

    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    spot_data, trading_days = load_spot_data(args.spot_file)
    results = run_backtest(args)
    write_daywise_csv(results, args.results_dir / DAYWISE_FILENAME)
    write_summary(results, args.results_dir / SUMMARY_FILENAME, args, trading_days)
    traded = sum(1 for r in results if r.status == "TRADED")
    net = sum(float(r.net_pnl) for r in results if r.status == "TRADED")
    print(f"Done. Traded={traded} Net={format_money(net)}")
    print(f"Summary: {args.results_dir / SUMMARY_FILENAME}")


if __name__ == "__main__":
    main()
