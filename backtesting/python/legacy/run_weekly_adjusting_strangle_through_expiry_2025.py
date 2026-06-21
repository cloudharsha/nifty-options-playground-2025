#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import logging
from collections import Counter
from dataclasses import asdict, fields
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import run_combined_expiry_adjusting_strangle_2025 as base


BASE_FILENAME = "weekly_adjusting_strangle_through_expiry_2025"
ADJUST_CYCLES_FILENAME = f"{BASE_FILENAME}_adjust_cycles.csv"
EVENTS_FILENAME = f"{BASE_FILENAME}_events.csv"
EQUITY_FILENAME = f"{BASE_FILENAME}_equity.csv"
SUMMARY_CSV_FILENAME = f"{BASE_FILENAME}_summary.csv"
SUMMARY_MD_FILENAME = f"{BASE_FILENAME}_summary.md"
LOG_FILENAME = f"{BASE_FILENAME}.log"


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Backtest the 2025 weekly adjusting short strangle through expiry day, "
            "without the separate expiry-day ATM +/-100 strangle."
        ),
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
    parser.add_argument("--capital", type=float, default=1_000_000.0)
    parser.add_argument("--compound", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--compound-min-capital", type=float, default=100_000.0)
    parser.add_argument("--lot-size", type=int, default=65)
    parser.add_argument("--margin-rate", type=float, default=0.20)
    parser.add_argument("--gap", type=int, default=50)
    parser.add_argument("--min-premium", type=float, default=0.5)
    parser.add_argument("--max-premium", type=float, default=2000.0)
    parser.add_argument("--adj-entry-time", default="09:30")
    parser.add_argument("--adj-eod-time", default="15:20")
    parser.add_argument("--adj-min-otm-pct", type=float, default=0.01250)
    parser.add_argument("--adj-prem-min-pct", type=float, default=0.000833)
    parser.add_argument("--adj-prem-max-pct", type=float, default=0.001250)
    parser.add_argument("--adj-re-prem-min-pct", type=float, default=0.000417)
    parser.add_argument("--adj-re-prem-max-pct", type=float, default=0.000625)
    parser.add_argument("--adj-tp-points-init", type=float, default=25.0)
    parser.add_argument("--adj-decay-pct", type=float, default=0.50)
    parser.add_argument("--adj-band-low", type=float, default=0.60)
    parser.add_argument("--adj-band-high", type=float, default=0.90)
    parser.add_argument("--adj-eod-gap-max", type=float, default=0.20)
    parser.add_argument("--adj-max-rolls-per-day", type=int, default=50)
    parser.add_argument("--adj-max-pos-per-cycle", type=int, default=20)
    parser.add_argument("--brokerage-per-order", type=float, default=20.0)
    parser.add_argument("--stt-sell-rate", type=float, default=0.001)
    parser.add_argument("--exchange-txn-rate", type=float, default=0.0003503)
    parser.add_argument("--sebi-rate", type=float, default=0.000001)
    parser.add_argument("--stamp-buy-rate", type=float, default=0.00003)
    parser.add_argument("--gst-rate", type=float, default=0.18)
    args = parser.parse_args()

    for time_value, name in [
        (args.adj_entry_time, "--adj-entry-time"),
        (args.adj_eod_time, "--adj-eod-time"),
    ]:
        base.validate_time(parser, time_value, name)
    if args.capital <= 0:
        parser.error("--capital must be positive")
    if args.compound_min_capital <= 0:
        parser.error("--compound-min-capital must be positive")
    if args.lot_size <= 0:
        parser.error("--lot-size must be positive")
    if args.margin_rate <= 0:
        parser.error("--margin-rate must be positive")
    if args.min_premium < 0 or args.max_premium < args.min_premium:
        parser.error("--min-premium and --max-premium define an invalid premium range")
    return args


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger(BASE_FILENAME)
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def close_logger(logger: logging.Logger) -> None:
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()


def run_backtest(args: argparse.Namespace) -> Tuple[List[base.AdjustCycle], List[base.LegEvent]]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    try:
        spot_data = base.load_spot_data(args.spot_file)
        expiries = base.load_expiry_folders(args.options_dir)
        day_set = set(spot_data.trading_days)
        expiries = [expiry for expiry in expiries if expiry in day_set]
        chain = base.RepoChain(args.options_dir, expiries)
        adjust_cycles: List[base.AdjustCycle] = []
        events: List[base.LegEvent] = []
        running_pnl = 0.0
        previous_expiry: Optional[str] = None
        cycle_no = 0

        for expiry in expiries:
            if previous_expiry is None:
                period_start = spot_data.trading_days[0]
            else:
                period_start = next((day for day in spot_data.trading_days if day > previous_expiry), None)

            if period_start is None or period_start > expiry:
                previous_expiry = expiry
                chain.clear_caches()
                continue

            cycle_no += 1
            capital = base.capital_for_sizing(args, running_pnl)
            cycle_rows = base.spot_window_rows(spot_data, period_start, expiry)
            cycle, cycle_events = base.simulate_adjust_cycle(
                chain,
                cycle_rows,
                expiry,
                period_start,
                expiry,
                cycle_no,
                capital,
                args,
            )
            adjust_cycles.append(cycle)
            events.extend(cycle_events)
            if cycle.status == "TRADED":
                running_pnl += cycle.net_pnl

            logger.info(
                "ADJUST_THROUGH_EXPIRY cycle=%s expiry=%s start=%s end=%s status=%s net=%s reason=%s",
                cycle_no,
                expiry,
                period_start,
                expiry,
                cycle.status,
                cycle.net_pnl,
                cycle.skip_reason,
            )
            previous_expiry = expiry
            chain.clear_caches()

        logger.info(
            "COMPLETED adjust_cycles=%s events=%s running_pnl=%s",
            len([cycle for cycle in adjust_cycles if cycle.status == "TRADED"]),
            len(events),
            running_pnl,
        )
        return adjust_cycles, events
    finally:
        close_logger(logger)


def build_equity_curve(adjust_cycles: List[base.AdjustCycle], capital: float) -> List[base.EquityRow]:
    return base.build_equity_curve([], adjust_cycles, capital)


def write_dataclass_csv(items: List[object], item_type: type, output_path: Path) -> None:
    fieldnames = [field.name for field in fields(item_type)]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(asdict(item))


def summary_row(overall: Dict[str, object], adjust_cycles: List[base.AdjustCycle]) -> Dict[str, object]:
    row = dict(overall)
    row["period"] = "ALL"
    row["n_adjust"] = len([cycle for cycle in adjust_cycles if cycle.status == "TRADED"])
    row["n_expiry"] = 0
    row["adjust_pnl"] = round(sum(cycle.net_pnl for cycle in adjust_cycles if cycle.status == "TRADED"), 2)
    row["expiry_pnl"] = 0.0
    return row


def markdown_metrics_table(rows: List[Dict[str, object]]) -> List[str]:
    lines = [
        "| Period | Active Cycles | Adjust P/L | Total P/L | Return % | Max DD | Win % | PF |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.get('period', '')} | "
            f"{row.get('n', 0)} | "
            f"{base.format_number(float(row.get('adjust_pnl', 0.0) or 0.0))} | "
            f"{base.format_number(float(row.get('total_pnl', 0.0) or 0.0))} | "
            f"{base.format_number(float(row.get('return_pct', 0.0) or 0.0))} | "
            f"{base.format_number(float(row.get('max_drawdown', 0.0) or 0.0))} | "
            f"{base.format_number(float(row.get('win_rate_pct', 0.0) or 0.0))} | "
            f"{row.get('profit_factor', '')} |"
        )
    return lines


def write_summary_csv(
    per_year: List[Dict[str, object]],
    overall: Dict[str, object],
    adjust_cycles: List[base.AdjustCycle],
    output_path: Path,
) -> None:
    rows: List[Dict[str, object]] = []
    for row in per_year:
        out = dict(row)
        out["period"] = row.get("period", "")
        out["n_expiry"] = 0
        out["expiry_pnl"] = 0.0
        rows.append(out)
    if overall:
        rows.append(summary_row(overall, adjust_cycles))

    preferred = [
        "period",
        "n",
        "n_adjust",
        "n_expiry",
        "adjust_pnl",
        "expiry_pnl",
        "total_pnl",
        "return_pct",
        "cagr_pct",
        "years",
        "wins",
        "losses",
        "breakeven",
        "win_rate_pct",
        "profit_factor",
        "expectancy",
        "best",
        "worst",
        "max_drawdown",
        "max_drawdown_pct",
        "max_consecutive_losses",
        "first_date",
        "last_date",
    ]
    keys = {key for row in rows for key in row}
    fieldnames = [key for key in preferred if key in keys] + sorted(key for key in keys if key not in preferred)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_summary_md(
    adjust_cycles: List[base.AdjustCycle],
    events: List[base.LegEvent],
    equity_rows: List[base.EquityRow],
    per_year: List[Dict[str, object]],
    overall: Dict[str, object],
    output_path: Path,
    args: argparse.Namespace,
) -> None:
    traded_cycles = [cycle for cycle in adjust_cycles if cycle.status == "TRADED"]
    skipped_cycles = [cycle for cycle in adjust_cycles if cycle.status != "TRADED"]
    close_reasons = Counter(event.close_reason for event in events)
    overall_for_table = summary_row(overall, adjust_cycles) if overall else {}

    yearly_rows: List[Dict[str, object]] = []
    for row in per_year:
        out = dict(row)
        out["adjust_pnl"] = row.get("adjust_pnl", row.get("total_pnl", 0.0))
        yearly_rows.append(out)

    lines: List[str] = [
        "# 2025 Weekly Adjusting Short Strangle Through Expiry Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Spot file: `{args.spot_file}`",
        f"- Options directory: `{args.options_dir}`",
        "- Strategy: run the weekly adjusting short strangle from the day after previous expiry through this expiry date.",
        "- No separate expiry-day ATM +/-100 strangle is run.",
        "- The same expiry's weekly options are used throughout each cycle, including expiry day.",
        "- Cycle close: any open position is closed at the last available bar of the expiry date.",
        "- Entry band: 0.0833%-0.1250% of spot, min OTM 1.25% of spot.",
        "- Re-entry band: 0.0417%-0.0625% of spot after a position closes.",
        "- Intraday roll: when one active leg decays to 50% or less of its sell price, roll that leg closer to ATM.",
        "- EOD rebalance: from 15:20, roll the cheaper leg closer to ATM when CE/PE premium gap is above 20%, except on cycle-end day.",
        f"- Sizing: capital Rs {base.format_number(args.capital)}, compound `{args.compound}`, lot size `{args.lot_size}`, margin rate `{base.format_number(args.margin_rate)}`.",
        "- Pricing: option close is used for entries, monitoring, rolls, and exits; last available row at or before the timestamp is used.",
        "",
        "## Overall Results",
        "",
        *markdown_metrics_table([overall_for_table] if overall_for_table else []),
        "",
        "## Yearly Results",
        "",
        *markdown_metrics_table(yearly_rows),
        "",
        "## Counts",
        "",
        f"- Adjust cycles: `{len(traded_cycles)}` traded, `{len(skipped_cycles)}` skipped",
        f"- Expiry-day strategy trades: `0`",
        f"- Leg events: `{len(events)}`",
        f"- Final equity: `Rs {base.format_number(equity_rows[-1].equity if equity_rows else args.capital)}`",
        "",
        "## Close Reasons",
        "",
    ]
    if close_reasons:
        for reason, count in sorted(close_reasons.items()):
            lines.append(f"- `{reason}`: `{count}`")
    else:
        lines.append("- None")

    lines.extend(["", "## Skips", ""])
    if skipped_cycles:
        for cycle in skipped_cycles:
            lines.append(
                f"- Adjust `{cycle.expiry}` ({cycle.period_start} to {cycle.period_end}): "
                f"`{cycle.skip_reason}`. {cycle.remarks}"
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- Adjust cycles: `{ADJUST_CYCLES_FILENAME}`",
            f"- Leg events: `{EVENTS_FILENAME}`",
            f"- Equity curve: `{EQUITY_FILENAME}`",
            f"- Summary CSV: `{SUMMARY_CSV_FILENAME}`",
            f"- Log: `{LOG_FILENAME}`",
        ]
    )

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def write_outputs(
    adjust_cycles: List[base.AdjustCycle],
    events: List[base.LegEvent],
    equity_rows: List[base.EquityRow],
    args: argparse.Namespace,
) -> None:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    write_dataclass_csv(adjust_cycles, base.AdjustCycle, args.results_dir / ADJUST_CYCLES_FILENAME)
    write_dataclass_csv(events, base.LegEvent, args.results_dir / EVENTS_FILENAME)
    write_dataclass_csv(equity_rows, base.EquityRow, args.results_dir / EQUITY_FILENAME)

    overall = base.compute_metrics(equity_rows, args.capital)
    per_year = base.per_year_metrics(equity_rows, args.capital)
    write_summary_csv(per_year, overall, adjust_cycles, args.results_dir / SUMMARY_CSV_FILENAME)
    write_summary_md(
        adjust_cycles,
        events,
        equity_rows,
        per_year,
        overall,
        args.results_dir / SUMMARY_MD_FILENAME,
        args,
    )


def main() -> None:
    args = parse_args()
    adjust_cycles, events = run_backtest(args)
    equity_rows = build_equity_curve(adjust_cycles, args.capital)
    write_outputs(adjust_cycles, events, equity_rows, args)


if __name__ == "__main__":
    main()
