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
DAYWISE_FILENAME = "short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_daywise.csv"
SUMMARY_FILENAME = "short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md"
LOG_FILENAME = "short_atm_nifty_ma_weekly_overnight_offsets_2020_2026.log"
MONEYNESS_OTM = "OTM"
MONEYNESS_ITM = "ITM"
CAPITAL_FOR_CAGR = 10_00_000.0  # Rs 10L reference base


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
    lot_size: str
    lots: str
    qty: str
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


def compute_cagr(net_total: float, capital: float, first_day: str, last_day: str) -> float:
    start = datetime.date.fromisoformat(first_day)
    end = datetime.date.fromisoformat(last_day)
    days = (end - start).days
    if days <= 0 or capital <= 0:
        return 0.0
    return ((1.0 + net_total / capital) ** (365.25 / days) - 1.0) * 100.0


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Backtest 2020-2026 overnight weekly directional short option strategy using "
            "NIFTY 25-SMA signals across OTM and ITM strike offsets."
        ),
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
    parser.add_argument("--otm-offsets", type=int, nargs="+", default=[100, 200, 300, 400, 500])
    parser.add_argument("--itm-offsets", type=int, nargs="+", default=[100, 200, 300])
    parser.add_argument("--brokerage-per-order", type=float, default=25.0)
    parser.add_argument("--slippage-points-per-order", type=float, default=1.0)
    args = parser.parse_args()

    if any(offset <= 0 for offset in args.otm_offsets + args.itm_offsets):
        parser.error("--otm-offsets and --itm-offsets must contain positive point offsets")

    return args


def build_offset_specs(args: argparse.Namespace) -> List[OffsetSpec]:
    specs = [
        OffsetSpec(range_label=f"{MONEYNESS_OTM}_{offset}", moneyness=MONEYNESS_OTM, offset_points=offset)
        for offset in args.otm_offsets
    ]
    specs.extend(
        OffsetSpec(range_label=f"{MONEYNESS_ITM}_{offset}", moneyness=MONEYNESS_ITM, offset_points=offset)
        for offset in args.itm_offsets
    )
    return specs


def build_timestamp(day: str, time_text: str) -> str:
    h, m = time_text.split(":")
    return f"{day}T{h}:{m}:00{IST_SUFFIX}"


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


def leg_pnl_after_slippage(raw_pts: float, slip: float) -> float:
    return raw_pts - (2 * slip)


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("short_atm_nifty_ma_weekly_overnight_offsets_2020_2026")
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
        for row in csv.DictReader(handle):
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
    return sorted(path.name for path in options_dir.iterdir() if path.is_dir())


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
    with contract_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            ts = row["timestamp"]
            rows[ts] = OptionRow(timestamp=ts, open_value=float(row["open"]), open_text=row["open"])
    cd = ContractData(path=contract_path, rows_by_timestamp=rows)
    cache[contract_path] = cd
    return cd


def compute_spot_sma(spot_data: SpotData, timestamp: str, ma_period: int) -> Tuple[Optional[float], int]:
    idx = spot_data.index_by_timestamp.get(timestamp)
    if idx is None:
        return None, 0
    n = idx + 1
    if n < ma_period:
        return None, n
    sma = sum(r.close_value for r in spot_data.ordered_rows[idx - ma_period + 1: idx + 1]) / ma_period
    return sma, n


def make_result(
    spec: OffsetSpec, entry_date: str, status: str, skip_reason: str,
    lot_size: int = 0, lots: int = 0,
    expiry_date: str = "", next_trading_day: str = "",
    spot_signal_timestamp: str = "", spot_signal_close: str = "",
    spot_sma_25: str = "", spot_signal_relation: str = "",
    atm_strike: str = "", target_strike: str = "", sold_side: str = "",
    contract_name: str = "", option_entry_timestamp: str = "",
    option_entry_open: str = "", option_exit_timestamp: str = "", option_exit_open: str = "",
    gross_pnl: float = 0.0, brokerage: float = 0.0, net_pnl: float = 0.0,
    remarks: str = "",
) -> TradeResult:
    return TradeResult(
        range_label=spec.range_label, moneyness=spec.moneyness, offset_points=str(spec.offset_points),
        entry_date=entry_date, status=status, skip_reason=skip_reason,
        expiry_date=expiry_date, next_trading_day=next_trading_day,
        lot_size=str(lot_size), lots=str(lots), qty=str(lot_size * lots),
        spot_signal_timestamp=spot_signal_timestamp, spot_signal_close=spot_signal_close,
        spot_sma_25=spot_sma_25, spot_signal_relation=spot_signal_relation,
        atm_strike=atm_strike, target_strike=target_strike, sold_side=sold_side,
        contract_name=contract_name, option_entry_timestamp=option_entry_timestamp,
        option_entry_open=option_entry_open, option_exit_timestamp=option_exit_timestamp,
        option_exit_open=option_exit_open,
        gross_pnl=format_money(gross_pnl), brokerage=format_money(brokerage),
        net_pnl=format_money(net_pnl), remarks=remarks,
    )


def add_common_skip_results(
    results: List[TradeResult], offset_specs: List[OffsetSpec],
    entry_date: str, status: str, skip_reason: str,
    lot_size: int = 0, lots: int = 0,
    expiry_date: str = "", next_trading_day: str = "",
    spot_signal_timestamp: str = "", spot_signal_close: str = "",
    spot_sma_25: str = "", spot_signal_relation: str = "",
    atm_strike: str = "", sold_side: str = "", remarks: str = "",
) -> None:
    for spec in offset_specs:
        ts = ""
        if atm_strike and sold_side:
            ts = str(target_strike_for_offset(int(atm_strike), sold_side, spec))
        results.append(make_result(
            spec=spec, entry_date=entry_date, status=status, skip_reason=skip_reason,
            lot_size=lot_size, lots=lots,
            expiry_date=expiry_date, next_trading_day=next_trading_day,
            spot_signal_timestamp=spot_signal_timestamp, spot_signal_close=spot_signal_close,
            spot_sma_25=spot_sma_25, spot_signal_relation=spot_signal_relation,
            atm_strike=atm_strike, target_strike=ts, sold_side=sold_side, remarks=remarks,
        ))


def run_backtest(args: argparse.Namespace) -> Tuple[List[TradeResult], List[str]]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    offset_specs = build_offset_specs(args)
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
                add_common_skip_results(results, offset_specs, entry_date, "SKIPPED",
                                        "missing_spot_signal_timestamp",
                                        spot_signal_timestamp=sig_ts,
                                        remarks=f"Missing spot signal timestamp {sig_ts}")
                continue

            sma, n = compute_spot_sma(spot_data, sig_ts, args.ma_period)
            if sma is None:
                add_common_skip_results(results, offset_specs, entry_date, "SKIPPED",
                                        "insufficient_spot_history",
                                        spot_signal_timestamp=sig_ts,
                                        spot_signal_close=sig_row.close_text,
                                        remarks=f"{sig_ts} has {n} bars; needs {args.ma_period}")
                continue

            sma_text = format_money(sma)
            atm = round_to_nearest_50(sig_row.close_value)
            strike_text = str(atm)

            if sig_row.close_value > sma:
                relation, sold_side = "ABOVE_SMA", "PE"
            elif sig_row.close_value < sma:
                relation, sold_side = "BELOW_SMA", "CE"
            else:
                add_common_skip_results(results, offset_specs, entry_date, "SKIPPED",
                                        "equal_close_and_sma",
                                        spot_signal_timestamp=sig_ts, spot_signal_close=sig_row.close_text,
                                        spot_sma_25=sma_text, spot_signal_relation="EQUAL_SMA",
                                        atm_strike=strike_text,
                                        remarks=f"Close {sig_row.close_text} equals SMA {sma_text}")
                continue

            next_day = next_day_by_day[entry_date]
            if not next_day:
                add_common_skip_results(results, offset_specs, entry_date, "SKIPPED",
                                        "no_next_trading_day",
                                        spot_signal_timestamp=sig_ts, spot_signal_close=sig_row.close_text,
                                        spot_sma_25=sma_text, spot_signal_relation=relation,
                                        atm_strike=strike_text, sold_side=sold_side,
                                        remarks="No next trading day in dataset.")
                continue

            expiry_date = next_expiry_after(expiries, entry_date)
            if expiry_date is None:
                add_common_skip_results(results, offset_specs, entry_date, "SKIPPED",
                                        "no_next_weekly_expiry",
                                        next_trading_day=next_day,
                                        spot_signal_timestamp=sig_ts, spot_signal_close=sig_row.close_text,
                                        spot_sma_25=sma_text, spot_signal_relation=relation,
                                        atm_strike=strike_text, sold_side=sold_side,
                                        remarks="No weekly expiry folder strictly after entry date.")
                continue

            lot_size, lots = qty_for_expiry(expiry_date)
            contract_multiplier = lot_size * lots
            exit_ts = build_timestamp(next_day, args.exit_time)
            suffix = expiry_suffix(expiry_date)

            for spec in offset_specs:
                tgt = target_strike_for_offset(atm, sold_side, spec)
                tgt_text = str(tgt)
                if tgt <= 0:
                    results.append(make_result(
                        spec=spec, entry_date=entry_date, status="SKIPPED",
                        skip_reason="invalid_target_strike",
                        lot_size=lot_size, lots=lots,
                        expiry_date=expiry_date, next_trading_day=next_day,
                        spot_signal_timestamp=sig_ts, spot_signal_close=sig_row.close_text,
                        spot_sma_25=sma_text, spot_signal_relation=relation,
                        atm_strike=strike_text, target_strike=tgt_text, sold_side=sold_side,
                        remarks=f"Computed target strike {tgt_text} is not valid."))
                    continue

                contract_path = args.options_dir / expiry_date / f"NIFTY_{tgt}_{sold_side}_{suffix}.csv"
                cd = load_contract(contract_path, contract_cache)
                if cd is None:
                    results.append(make_result(
                        spec=spec, entry_date=entry_date, status="SKIPPED",
                        skip_reason="missing_option_file",
                        lot_size=lot_size, lots=lots,
                        expiry_date=expiry_date, next_trading_day=next_day,
                        spot_signal_timestamp=sig_ts, spot_signal_close=sig_row.close_text,
                        spot_sma_25=sma_text, spot_signal_relation=relation,
                        atm_strike=strike_text, target_strike=tgt_text, sold_side=sold_side,
                        contract_name=contract_path.name,
                        option_entry_timestamp=entry_ts, option_exit_timestamp=exit_ts,
                        remarks=f"Missing option file: {contract_path.name}"))
                    continue

                entry_row = cd.rows_by_timestamp.get(entry_ts)
                exit_row = cd.rows_by_timestamp.get(exit_ts)
                missing = []
                if entry_row is None:
                    missing.append(f"{contract_path.name} missing entry {entry_ts}")
                if exit_row is None:
                    missing.append(f"{contract_path.name} missing exit {exit_ts}")
                if missing:
                    results.append(make_result(
                        spec=spec, entry_date=entry_date, status="SKIPPED",
                        skip_reason="missing_entry_or_exit_timestamp",
                        lot_size=lot_size, lots=lots,
                        expiry_date=expiry_date, next_trading_day=next_day,
                        spot_signal_timestamp=sig_ts, spot_signal_close=sig_row.close_text,
                        spot_sma_25=sma_text, spot_signal_relation=relation,
                        atm_strike=strike_text, target_strike=tgt_text, sold_side=sold_side,
                        contract_name=contract_path.name,
                        option_entry_timestamp=entry_ts, option_exit_timestamp=exit_ts,
                        remarks="; ".join(missing)))
                    continue

                gross = leg_pnl_after_slippage(entry_row.open_value - exit_row.open_value,
                                               args.slippage_points_per_order) * contract_multiplier
                net = gross - round_trip_brokerage
                results.append(make_result(
                    spec=spec, entry_date=entry_date, status="TRADED", skip_reason="",
                    lot_size=lot_size, lots=lots,
                    expiry_date=expiry_date, next_trading_day=next_day,
                    spot_signal_timestamp=sig_ts, spot_signal_close=sig_row.close_text,
                    spot_sma_25=sma_text, spot_signal_relation=relation,
                    atm_strike=strike_text, target_strike=tgt_text, sold_side=sold_side,
                    contract_name=contract_path.name,
                    option_entry_timestamp=entry_ts, option_entry_open=entry_row.open_text,
                    option_exit_timestamp=exit_ts, option_exit_open=exit_row.open_text,
                    gross_pnl=gross, brokerage=round_trip_brokerage, net_pnl=net))
                logger.info("TRADED date=%s range=%s expiry=%s side=%s atm=%s tgt=%s lot=%sx%s net=%s",
                            entry_date, spec.range_label, expiry_date, sold_side, atm, tgt,
                            lot_size, lots, format_money(net))
    except Exception:
        logger.exception("ERROR unexpected failure")
        raise

    return results, trading_days


def write_daywise_csv(results: List[TradeResult], path: Path) -> None:
    fields = [f.name for f in TradeResult.__dataclass_fields__.values()]
    with path.open("w", encoding="utf-8", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow(r.__dict__)


def compute_max_consecutive_streaks(vals: List[float]) -> Tuple[int, int]:
    max_w = max_l = cur_w = cur_l = 0
    for v in vals:
        if v > 0:
            cur_w += 1; cur_l = 0; max_w = max(max_w, cur_w)
        elif v < 0:
            cur_l += 1; cur_w = 0; max_l = max(max_l, cur_l)
        else:
            cur_w = cur_l = 0
    return max_w, max_l


def compute_max_drawdown(vals: List[float]) -> float:
    peak = dd = cum = 0.0
    for v in vals:
        cum += v; peak = max(peak, cum); dd = max(dd, peak - cum)
    return dd


def metrics_for_results(results: List[TradeResult]) -> Dict:
    traded = [r for r in results if r.status == "TRADED"]
    skipped = [r for r in results if r.status == "SKIPPED"]
    vals = [float(r.net_pnl) for r in traded]
    gross = sum(float(r.gross_pnl) for r in traded)
    brok = sum(float(r.brokerage) for r in traded)
    net = sum(vals)
    wins = sum(1 for v in vals if v > 0)
    losses = sum(1 for v in vals if v < 0)
    be = sum(1 for v in vals if v == 0)
    max_w, max_l = compute_max_consecutive_streaks(vals)
    dd = compute_max_drawdown(vals)
    best = max(traded, key=lambda r: float(r.net_pnl), default=None)
    worst = min(traded, key=lambda r: float(r.net_pnl), default=None)
    ce = sum(1 for r in traded if r.sold_side == "CE")
    pe = sum(1 for r in traded if r.sold_side == "PE")
    return dict(traded=traded, skipped=skipped, gross=gross, brok=brok, net=net,
                wins=wins, losses=losses, be=be, max_w=max_w, max_l=max_l, dd=dd,
                best=best, worst=worst, ce=ce, pe=pe)


def write_range_detail(lines: List[str], label: str, results: List[TradeResult],
                       trading_days: List[str]) -> None:
    m = metrics_for_results(results)
    best: Optional[TradeResult] = m["best"]
    worst: Optional[TradeResult] = m["worst"]
    cagr = compute_cagr(m["net"], CAPITAL_FOR_CAGR, trading_days[0], trading_days[-1]) if trading_days else 0.0
    lines.extend([
        f"### {label}", "",
        f"- Traded days: `{len(m['traded'])}`",
        f"- Skipped days: `{len(m['skipped'])}`",
        f"- CE-sell count: `{m['ce']}`",
        f"- PE-sell count: `{m['pe']}`",
        f"- Winning days: `{m['wins']}`",
        f"- Losing days: `{m['losses']}`",
        f"- Break-even days: `{m['be']}`",
        f"- Max profit day: `{best.entry_date}` net `{best.net_pnl}`" if best else "- Max profit day: `N/A`",
        f"- Max loss day: `{worst.entry_date}` net `{worst.net_pnl}`" if worst else "- Max loss day: `N/A`",
        f"- Max consecutive wins: `{m['max_w']}`",
        f"- Max consecutive losses: `{m['max_l']}`",
        f"- Max drawdown: `{format_money(m['dd'])}`",
        f"- Total Profit/Loss: `{format_money(m['net'])}`",
        f"- Total Brokerage: `{format_money(m['brok'])}`",
        f"- Gross P/L: `{format_money(m['gross'])}`",
        f"- CAGR (on Rs {int(CAPITAL_FOR_CAGR):,}): `{cagr:.2f}%`",
        "",
    ])


def write_summary(results: List[TradeResult], path: Path,
                  args: argparse.Namespace, trading_days: List[str]) -> None:
    offset_specs = build_offset_specs(args)
    by_range = {
        spec.range_label: [r for r in results if r.range_label == spec.range_label]
        for spec in offset_specs
    }

    lines: List[str] = [
        "# Overnight Weekly Short NIFTY 25-SMA Strike-Offset Backtest (2020-2026)",
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
        "- Quantity: ~300 per trade (dynamic lot sizing by expiry era)",
        "  - pre-2021-10-07: 75x4=300 | 2021-10-07-2024-04-25: 50x6=300",
        "  - 2024-04-26-2024-11-21: 25x12=300 | 2024-11-22-2025-12-30: 75x4=300",
        "  - 2026+: 65x5=325",
        f"- Slippage: {format_money(args.slippage_points_per_order)} pt/order",
        f"- Brokerage: Rs {int(args.brokerage_per_order)}/order -> Rs {int(args.brokerage_per_order * 2)}/trade",
        f"- Capital reference (CAGR): Rs {int(CAPITAL_FOR_CAGR):,}",
        f"- Data range: `{trading_days[0]}` to `{trading_days[-1]}`" if trading_days else "",
        "",
        "## Range Comparison",
        "",
        "| Range | Traded | Skipped | Wins | Losses | Max DD | Net P/L | Gross P/L | CAGR% |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for spec in offset_specs:
        m = metrics_for_results(by_range[spec.range_label])
        cagr = compute_cagr(m["net"], CAPITAL_FOR_CAGR, trading_days[0], trading_days[-1]) if trading_days else 0.0
        lines.append(
            f"| {spec.range_label} | {len(m['traded'])} | {len(m['skipped'])} | "
            f"{m['wins']} | {m['losses']} | {format_money(m['dd'])} | "
            f"{format_money(m['net'])} | {format_money(m['gross'])} | {cagr:.2f}% |"
        )

    lines.extend(["", "## Range Details", ""])
    for spec in offset_specs:
        write_range_detail(lines, spec.range_label, by_range[spec.range_label], trading_days)

    lines.extend(["## Exceptions By Range", ""])
    for spec in offset_specs:
        skipped = [r for r in by_range[spec.range_label] if r.status == "SKIPPED"]
        lines.extend([f"### {spec.range_label}", ""])
        if skipped:
            for r in skipped:
                lines.append(f"- `{r.entry_date}`: `{r.skip_reason}`. {r.remarks}")
        else:
            lines.append("- None")
        lines.append("")

    lines.extend([
        "## Remarks",
        "",
        "- Exact timestamp matching; no nearest-candle fallback.",
        "- The 15:15 spot row is the 15:30 close proxy; 15:29 option open is the entry proxy.",
        "- Expiry folder dates are the source of truth for expiry selection.",
        "- Lot sizes are dynamic per expiry era to maintain ~300 quantity throughout the period.",
    ])

    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    results, trading_days = run_backtest(args)
    write_daywise_csv(results, args.results_dir / DAYWISE_FILENAME)
    write_summary(results, args.results_dir / SUMMARY_FILENAME, args, trading_days)
    traded = sum(1 for r in results if r.status == "TRADED")
    print(f"Done. Traded rows={traded} of {len(results)} total")
    print(f"Summary: {args.results_dir / SUMMARY_FILENAME}")


if __name__ == "__main__":
    main()
