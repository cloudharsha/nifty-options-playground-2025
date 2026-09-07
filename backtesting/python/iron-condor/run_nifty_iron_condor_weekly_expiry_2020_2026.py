#!/usr/bin/env python3
"""
NIFTY Weekly Iron Condor — Expiry-Day Intraday — 2020-2026
===========================================================

Structure (per condor, N lots):
  long  CE @ ATM + SHORT_DIST + WING_WIDTH   upper wing
  short CE @ ATM + SHORT_DIST                short upper
  short PE @ ATM - SHORT_DIST                short lower
  long  PE @ ATM - SHORT_DIST - WING_WIDTH   lower wing

Entry  : 09:20 open on the weekly expiry day.
Exit   : 15:25 OR SL trigger (whichever first).
SL     : exit all 4 legs when current liq cost >= SL_MULT × entry credit.
         liq_cost = (sc_price + sp_price) - (lc_price + lp_price)

Sizing : margin_per_condor = WING_WIDTH × lot_size + 2 × ELM_RATE × spot × lot_size
         condors = floor(CAPITAL / margin_per_condor)

Capital: Rs 10,00,000 fixed.

Outputs:
  nifty_iron_condor_weekly_expiry_2020_2026_daywise.csv
  nifty_iron_condor_weekly_expiry_2020_2026_summary.md
  nifty_iron_condor_weekly_expiry_2020_2026.log
"""
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

IST_SUFFIX = "+05:30"
BASE_FILENAME = "nifty_iron_condor_weekly_expiry_2020_2026"
DAYWISE_FILENAME = f"{BASE_FILENAME}_daywise.csv"
SUMMARY_FILENAME = f"{BASE_FILENAME}_summary.md"
LOG_FILENAME = f"{BASE_FILENAME}.log"

CAPITAL = 1_000_000.0
ELM_RATE = 0.02        # per short leg
BROKERAGE_PER_ORDER = 20.0
SLIPPAGE_PER_ORDER = 0.5


# ─── lot size schedule ───────────────────────────────────────────────────────

def lot_size_for(expiry_date: str) -> int:
    d = datetime.date.fromisoformat(expiry_date)
    if d <= datetime.date(2021, 10, 6):
        return 75
    if d <= datetime.date(2024, 4, 25):
        return 50
    if d <= datetime.date(2024, 11, 21):
        return 25
    if d <= datetime.date(2025, 12, 30):
        return 75
    return 65


def margin_per_condor(spot: float, lot_size: int, wing_width: int) -> float:
    span = wing_width * lot_size
    elm = 2 * ELM_RATE * spot * lot_size
    return span + elm


def condors_for_capital(spot: float, lot_size: int, wing_width: int) -> int:
    m = margin_per_condor(spot, lot_size, wing_width)
    return max(1, int(CAPITAL // m)) if m > 0 else 1


# ─── helpers ─────────────────────────────────────────────────────────────────

def expiry_suffix(expiry_date: str) -> str:
    return datetime.datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%d_%b_%y").upper()


def round_to_50(price: float) -> int:
    rem = price % 50
    base = int(price - rem)
    return base if rem < 25 else base + 50


def build_ts(day: str, time_str: str) -> str:
    h, m = time_str.split(":")
    return f"{day}T{h}:{m}:00{IST_SUFFIX}"


def fmt(v: float) -> str:
    return f"{v:.2f}"


def compute_cagr(net: float, capital: float, first_day: str, last_day: str) -> float:
    start = datetime.date.fromisoformat(first_day)
    end = datetime.date.fromisoformat(last_day)
    days = (end - start).days
    if days <= 0 or capital <= 0:
        return 0.0
    final = capital + net
    if final <= 0:
        return -100.0
    return ((final / capital) ** (365.25 / days) - 1.0) * 100.0


# ─── data loading ────────────────────────────────────────────────────────────

@dataclass
class OptionBar:
    open_v: float
    high_v: float
    low_v: float
    close_v: float


def load_option(path: Path) -> Optional[Dict[str, OptionBar]]:
    if not path.exists():
        return None
    rows: Dict[str, OptionBar] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            rows[row["timestamp"]] = OptionBar(
                open_v=float(row["open"]),
                high_v=float(row["high"]),
                low_v=float(row["low"]),
                close_v=float(row["close"]),
            )
    return rows


def load_spot_data(spot_file: Path) -> Dict[str, Dict[str, OptionBar]]:
    """Returns {day: {timestamp: OptionBar}}."""
    by_day: Dict[str, Dict[str, OptionBar]] = {}
    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            day = ts[:10]
            if day not in by_day:
                by_day[day] = {}
            by_day[day][ts] = OptionBar(
                open_v=float(row["open"]),
                high_v=float(row["high"]),
                low_v=float(row["low"]),
                close_v=float(row["close"]),
            )
    return by_day


def load_expiry_dates(options_dir: Path) -> List[str]:
    return sorted(p.name for p in options_dir.iterdir() if p.is_dir())


# ─── dataclass ───────────────────────────────────────────────────────────────

@dataclass
class DayResult:
    entry_date: str
    status: str
    skip_reason: str
    expiry_date: str
    spot_entry: str
    atm: str
    short_dist: str
    wing_width: str
    short_ce: str
    long_ce: str
    short_pe: str
    long_pe: str
    short_ce_entry: str
    long_ce_entry: str
    short_pe_entry: str
    long_pe_entry: str
    entry_credit: str
    sl_trigger: str
    lot_size: str
    condors: str
    units: str
    exit_time: str
    exit_reason: str
    short_ce_exit: str
    long_ce_exit: str
    short_pe_exit: str
    long_pe_exit: str
    liq_cost_exit: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    cum_pnl: str
    remarks: str


def make_skip(entry_date: str, skip_reason: str, remarks: str = "",
              expiry_date: str = "") -> DayResult:
    return DayResult(
        entry_date=entry_date, status="SKIPPED", skip_reason=skip_reason,
        expiry_date=expiry_date, spot_entry="", atm="",
        short_dist="", wing_width="",
        short_ce="", long_ce="", short_pe="", long_pe="",
        short_ce_entry="", long_ce_entry="", short_pe_entry="", long_pe_entry="",
        entry_credit="", sl_trigger="",
        lot_size="", condors="", units="",
        exit_time="", exit_reason="",
        short_ce_exit="", long_ce_exit="", short_pe_exit="", long_pe_exit="",
        liq_cost_exit="",
        gross_pnl="0.00", brokerage="0.00", net_pnl="0.00", cum_pnl="",
        remarks=remarks,
    )


# ─── simulation ──────────────────────────────────────────────────────────────

def simulate_condor(
    expiry_date: str,
    spot_bars: Dict[str, OptionBar],
    options_dir: Path,
    short_dist: int,
    wing_width: int,
    sl_mult: float,
    entry_time: str,
    exit_time: str,
) -> DayResult:

    entry_ts = build_ts(expiry_date, entry_time)
    exit_ts = build_ts(expiry_date, exit_time)

    spot_bar = spot_bars.get(entry_ts)
    if spot_bar is None:
        return make_skip(expiry_date, "no_spot_entry_candle",
                         f"No spot bar at {entry_ts}", expiry_date)

    spot = spot_bar.open_v
    atm = round_to_50(spot)

    sc_strike = atm + short_dist
    lc_strike = atm + short_dist + wing_width
    sp_strike = atm - short_dist
    lp_strike = atm - short_dist - wing_width

    suffix = expiry_suffix(expiry_date)
    folder = options_dir / expiry_date

    sc_data = load_option(folder / f"NIFTY_{sc_strike}_CE_{suffix}.csv")
    lc_data = load_option(folder / f"NIFTY_{lc_strike}_CE_{suffix}.csv")
    sp_data = load_option(folder / f"NIFTY_{sp_strike}_PE_{suffix}.csv")
    lp_data = load_option(folder / f"NIFTY_{lp_strike}_PE_{suffix}.csv")

    missing = []
    if sc_data is None: missing.append(f"NIFTY_{sc_strike}_CE_{suffix}")
    if lc_data is None: missing.append(f"NIFTY_{lc_strike}_CE_{suffix}")
    if sp_data is None: missing.append(f"NIFTY_{sp_strike}_PE_{suffix}")
    if lp_data is None: missing.append(f"NIFTY_{lp_strike}_PE_{suffix}")
    if missing:
        return make_skip(expiry_date, "missing_option_files",
                         "Missing: " + ", ".join(missing), expiry_date)

    sc_entry_bar = sc_data.get(entry_ts)
    lc_entry_bar = lc_data.get(entry_ts)
    sp_entry_bar = sp_data.get(entry_ts)
    lp_entry_bar = lp_data.get(entry_ts)

    if None in (sc_entry_bar, lc_entry_bar, sp_entry_bar, lp_entry_bar):
        return make_skip(expiry_date, "missing_entry_candle",
                         f"One or more legs missing open at {entry_ts}", expiry_date)

    sc_ep = sc_entry_bar.open_v
    lc_ep = lc_entry_bar.open_v
    sp_ep = sp_entry_bar.open_v
    lp_ep = lp_entry_bar.open_v

    if any(p <= 0 or p > 5000 for p in (sc_ep, lc_ep, sp_ep, lp_ep)):
        return make_skip(expiry_date, "premium_out_of_range",
                         f"sc={sc_ep} lc={lc_ep} sp={sp_ep} lp={lp_ep}", expiry_date)

    entry_credit = (sc_ep + sp_ep) - (lc_ep + lp_ep)
    if entry_credit <= 0:
        return make_skip(expiry_date, "debit_condor",
                         f"credit={fmt(entry_credit)} (wings cost more than shorts)", expiry_date)

    lot_size = lot_size_for(expiry_date)
    n_condors = condors_for_capital(spot, lot_size, wing_width)
    units = n_condors * lot_size
    sl_trigger = sl_mult * entry_credit

    # walk forward: collect all timestamps between entry and exit
    all_ts = sorted(
        ts for ts in (
            set(sc_data) | set(lc_data) | set(sp_data) | set(lp_data)
        )
        if entry_ts < ts <= exit_ts
    )

    last_sc = sc_ep; last_lc = lc_ep
    last_sp = sp_ep; last_lp = lp_ep
    exit_ts_actual = exit_ts
    exit_reason = "eod"

    for ts in all_ts:
        if ts in sc_data: last_sc = sc_data[ts].close_v
        if ts in lc_data: last_lc = lc_data[ts].close_v
        if ts in sp_data: last_sp = sp_data[ts].close_v
        if ts in lp_data: last_lp = lp_data[ts].close_v

        liq = (last_sc + last_sp) - (last_lc + last_lp)
        if liq >= sl_trigger:
            exit_ts_actual = ts
            exit_reason = "sl"
            break

    # final prices at actual exit
    sc_exit = sc_data.get(exit_ts_actual)
    lc_exit = lc_data.get(exit_ts_actual)
    sp_exit = sp_data.get(exit_ts_actual)
    lp_exit = lp_data.get(exit_ts_actual)

    def last_at_or_before(data: Dict[str, OptionBar], ts: str) -> float:
        cands = [t for t in data if t <= ts]
        return data[max(cands)].close_v if cands else 0.0

    sc_xp = sc_exit.close_v if sc_exit else last_at_or_before(sc_data, exit_ts_actual)
    lc_xp = lc_exit.close_v if lc_exit else last_at_or_before(lc_data, exit_ts_actual)
    sp_xp = sp_exit.close_v if sp_exit else last_at_or_before(sp_data, exit_ts_actual)
    lp_xp = lp_exit.close_v if lp_exit else last_at_or_before(lp_data, exit_ts_actual)

    liq_at_exit = (sc_xp + sp_xp) - (lc_xp + lp_xp)
    gross = (entry_credit - liq_at_exit) * units

    # slippage: 4 legs × 2 sides (entry+exit) × slippage per order
    slippage_total = 4 * 2 * SLIPPAGE_PER_ORDER * units
    # brokerage: 4 legs × 2 orders each
    brokerage = 4 * 2 * BROKERAGE_PER_ORDER * n_condors
    net = gross - brokerage - slippage_total

    exit_hhmm = exit_ts_actual[11:16]

    return DayResult(
        entry_date=expiry_date, status="TRADED", skip_reason="",
        expiry_date=expiry_date,
        spot_entry=fmt(spot), atm=str(atm),
        short_dist=str(short_dist), wing_width=str(wing_width),
        short_ce=str(sc_strike), long_ce=str(lc_strike),
        short_pe=str(sp_strike), long_pe=str(lp_strike),
        short_ce_entry=fmt(sc_ep), long_ce_entry=fmt(lc_ep),
        short_pe_entry=fmt(sp_ep), long_pe_entry=fmt(lp_ep),
        entry_credit=fmt(entry_credit),
        sl_trigger=fmt(sl_trigger),
        lot_size=str(lot_size), condors=str(n_condors), units=str(units),
        exit_time=exit_hhmm, exit_reason=exit_reason,
        short_ce_exit=fmt(sc_xp), long_ce_exit=fmt(lc_xp),
        short_pe_exit=fmt(sp_xp), long_pe_exit=fmt(lp_xp),
        liq_cost_exit=fmt(liq_at_exit),
        gross_pnl=fmt(gross), brokerage=fmt(brokerage + slippage_total),
        net_pnl=fmt(net), cum_pnl="",
        remarks="",
    )


# ─── output ──────────────────────────────────────────────────────────────────

def write_daywise_csv(results: List[DayResult], path: Path) -> None:
    fields = list(DayResult.__dataclass_fields__)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow(r.__dict__)


def compute_max_drawdown(vals: List[float]) -> float:
    peak = cum = dd = 0.0
    for v in vals:
        cum += v
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    return dd


def compute_streaks(vals: List[float]) -> Tuple[int, int]:
    max_w = max_l = cur_w = cur_l = 0
    for v in vals:
        if v > 0:
            cur_w += 1; cur_l = 0; max_w = max(max_w, cur_w)
        elif v < 0:
            cur_l += 1; cur_w = 0; max_l = max(max_l, cur_l)
        else:
            cur_w = cur_l = 0
    return max_w, max_l


def write_summary(results: List[DayResult], path: Path, args: argparse.Namespace) -> None:
    traded = [r for r in results if r.status == "TRADED"]
    skipped = [r for r in results if r.status == "SKIPPED"]

    if not traded:
        path.write_text("# No trades recorded.\n", encoding="utf-8")
        return

    nets = [float(r.net_pnl) for r in traded]
    gross_total = sum(float(r.gross_pnl) for r in traded)
    brok_total = sum(float(r.brokerage) for r in traded)
    net_total = sum(nets)
    wins = sum(1 for v in nets if v > 0)
    losses = sum(1 for v in nets if v < 0)
    max_dd = compute_max_drawdown(nets)
    max_w, max_l = compute_streaks(nets)
    n_sl = sum(1 for r in traded if r.exit_reason == "sl")
    n_eod = sum(1 for r in traded if r.exit_reason == "eod")
    best_r = max(traded, key=lambda r: float(r.net_pnl))
    worst_r = min(traded, key=lambda r: float(r.net_pnl))
    avg_credit = sum(float(r.entry_credit) for r in traded) / len(traded)
    avg_condors = sum(int(r.condors) for r in traded) / len(traded)
    avg_net = net_total / len(traded)

    first_day = traded[0].entry_date
    last_day = traded[-1].entry_date
    cagr = compute_cagr(net_total, CAPITAL, first_day, last_day)
    wr = wins / len(traded) * 100 if traded else 0.0

    by_year: Dict[str, List[float]] = {}
    for r in traded:
        by_year.setdefault(r.entry_date[:4], []).append(float(r.net_pnl))

    skip_by_reason: Dict[str, int] = {}
    for r in skipped:
        skip_by_reason[r.skip_reason] = skip_by_reason.get(r.skip_reason, 0) + 1

    lines = [
        f"# NIFTY Weekly Iron Condor — Expiry Day Intraday (2020–2026)",
        "",
        "## Strategy Details",
        "",
        f"- Structure: short CE/PE @ ATM ± {args.short_dist}pts, long wings ± {args.short_dist + args.wing_width}pts",
        f"- Entry: `{args.entry_time}` open on weekly expiry day",
        f"- Exit: `{args.exit_time}` or SL trigger",
        f"- SL: liq cost ≥ `{args.sl_mult:.1f}×` entry credit (locks in 1× credit loss at 2×)",
        f"- Sizing: floor(₹{int(CAPITAL):,} / margin_per_condor); margin = wing×lot + 2×{ELM_RATE*100:.0f}%×spot×lot",
        f"- Brokerage: ₹{BROKERAGE_PER_ORDER:.0f}/order × 8 orders (4 legs × entry+exit)",
        f"- Slippage: {SLIPPAGE_PER_ORDER} pt/order × 8 orders × units",
        f"- Capital reference (CAGR): ₹{int(CAPITAL):,}",
        f"- Data range: `{first_day}` to `{last_day}`",
        "",
        "## Results Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total expiry days | `{len(results)}` |",
        f"| Traded days | `{len(traded)}` |",
        f"| Skipped days | `{len(skipped)}` |",
        f"| Win days | `{wins}` |",
        f"| Loss days | `{losses}` |",
        f"| Win rate | `{wr:.1f}%` |",
        f"| EOD exits | `{n_eod}` |",
        f"| SL hits | `{n_sl}` |",
        f"| Avg entry credit | `{fmt(avg_credit)}` pts |",
        f"| Avg condors/day | `{avg_condors:.1f}` |",
        f"| Avg net P/L/day | `₹{fmt(avg_net)}` |",
        f"| Best day | `{best_r.entry_date}` ₹{best_r.net_pnl} |",
        f"| Worst day | `{worst_r.entry_date}` ₹{worst_r.net_pnl} |",
        f"| Max consec wins | `{max_w}` |",
        f"| Max consec losses | `{max_l}` |",
        f"| Max drawdown | `₹{fmt(max_dd)}` |",
        f"| Gross P/L | `₹{fmt(gross_total)}` |",
        f"| Total brokerage + slippage | `₹{fmt(brok_total)}` |",
        f"| **Net P/L** | **`₹{fmt(net_total)}`** |",
        f"| **CAGR (on ₹{int(CAPITAL):,})** | **`{cagr:.2f}%`** |",
        "",
        "## Yearly Summary",
        "",
        "| Year | Expiry Days | Wins | Losses | Win% | Net P/L |",
        "|------|------------|------|--------|------|---------|",
    ]

    for y in sorted(by_year):
        yv = by_year[y]
        yw = sum(1 for v in yv if v > 0)
        yl = sum(1 for v in yv if v < 0)
        pct = yw / len(yv) * 100 if yv else 0.0
        lines.append(f"| {y} | {len(yv)} | {yw} | {yl} | {pct:.1f}% | ₹{fmt(sum(yv))} |")

    lines += [
        "",
        "## Skip Reason Summary",
        "",
    ]
    for reason, count in sorted(skip_by_reason.items(), key=lambda x: -x[1]):
        lines.append(f"- `{reason}`: {count}")

    lines += [
        "",
        "## Remarks",
        "",
        "- SL is checked bar-by-bar using close prices of all 4 legs.",
        "- Entry uses the open price of the 09:20 candle.",
        "- Exit uses close price of the bar at or before the exit time.",
        "- Lot sizing is dynamic per NIFTY lot schedule (75/50/25/75/65).",
        f"- Short distance: {args.short_dist} pts each side; wing: {args.wing_width} pts.",
    ]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ─── main ────────────────────────────────────────────────────────────────────

def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger(BASE_FILENAME)
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    h = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(h)
    logger.propagate = False
    return logger


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    p = argparse.ArgumentParser(
        description="NIFTY Weekly Iron Condor — expiry-day intraday — 2020-2026"
    )
    p.add_argument("--spot-file", type=Path,
                   default=repo_root / "nifty" / "NIFTY50_INDEX_5m_last_7y.csv")
    p.add_argument("--options-dir", type=Path,
                   default=repo_root / "NiftyOptions_2020_2026" / "Options")
    p.add_argument("--results-dir", type=Path,
                   default=repo_root / "backtesting" / "results" / "legacy-3")
    p.add_argument("--entry-time", default="09:20")
    p.add_argument("--exit-time", default="15:25")
    p.add_argument("--short-dist", type=int, default=200,
                   help="OTM distance from ATM for short legs (default 200)")
    p.add_argument("--wing-width", type=int, default=100,
                   help="Additional OTM for wing legs beyond short legs (default 100)")
    p.add_argument("--sl-mult", type=float, default=2.0,
                   help="SL trigger as multiple of entry credit (default 2.0)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)

    logger = configure_logger(args.results_dir / LOG_FILENAME)
    logger.info("START short_dist=%s wing_width=%s sl_mult=%s entry=%s exit=%s",
                args.short_dist, args.wing_width, args.sl_mult,
                args.entry_time, args.exit_time)

    print("Loading spot data...")
    spot_by_day = load_spot_data(args.spot_file)
    expiry_dates = load_expiry_dates(args.options_dir)
    print(f"  {len(spot_by_day)} spot days  |  {len(expiry_dates)} expiry folders")

    results: List[DayResult] = []
    cum = 0.0

    for expiry_date in expiry_dates:
        spot_bars = spot_by_day.get(expiry_date)
        if spot_bars is None:
            r = make_skip(expiry_date, "no_spot_data_for_expiry",
                          f"Expiry {expiry_date} not in spot data", expiry_date)
            results.append(r)
            logger.info("SKIPPED date=%s reason=no_spot_data", expiry_date)
            continue

        r = simulate_condor(
            expiry_date=expiry_date,
            spot_bars=spot_bars,
            options_dir=args.options_dir,
            short_dist=args.short_dist,
            wing_width=args.wing_width,
            sl_mult=args.sl_mult,
            entry_time=args.entry_time,
            exit_time=args.exit_time,
        )

        if r.status == "TRADED":
            cum += float(r.net_pnl)
            r.cum_pnl = fmt(cum)
            logger.info(
                "TRADED date=%s atm=%s sc=%s sp=%s credit=%s exit=%s reason=%s net=%s cum=%s",
                expiry_date, r.atm, r.short_ce, r.short_pe,
                r.entry_credit, r.exit_time, r.exit_reason,
                r.net_pnl, r.cum_pnl,
            )
        else:
            r.cum_pnl = fmt(cum)
            logger.info("SKIPPED date=%s reason=%s remarks=%s",
                        expiry_date, r.skip_reason, r.remarks)

        results.append(r)

    traded = [r for r in results if r.status == "TRADED"]
    skipped = [r for r in results if r.status == "SKIPPED"]
    net_total = sum(float(r.net_pnl) for r in traded)

    write_daywise_csv(results, args.results_dir / DAYWISE_FILENAME)
    write_summary(results, args.results_dir / SUMMARY_FILENAME, args)
    logger.info("DONE traded=%s skipped=%s net=%.2f", len(traded), len(skipped), net_total)

    print(f"Done. Traded={len(traded)}  Skipped={len(skipped)}  Net=Rs{fmt(net_total)}")
    print(f"Daywise : {args.results_dir / DAYWISE_FILENAME}")
    print(f"Summary : {args.results_dir / SUMMARY_FILENAME}")


if __name__ == "__main__":
    main()
