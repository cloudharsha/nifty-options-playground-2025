#!/usr/bin/env python3
"""
Expiry-day short premium — straddle and strangles — NIFTY 2020-2026.

Trades ONLY on weekly expiry days.

  ENTRY     09:20. Sell one CE and one PE of the contract expiring today.
            Offset 0 = ATM straddle. Offset 100/200/300 = strangle, CE sold
            `offset` points above the centre strike and PE the same distance
            below it.

  BALANCE   The two premiums must be within 20% of each other
            (min/max >= 0.80). If they are not, shift the CENTRE strike by
            50 points and look again - 0, +50, -50, +100, -100 ... out to
            --strike-search-steps. Both legs move together, so a strangle
            keeps its symmetric strike distance. First centre that passes is
            taken; if none does the day is skipped (--balance-fallback takes
            the best-balanced one instead).

  STOP      Independent per leg. A leg is bought back when its price reaches
            150% of what it was sold for (--sl-factor 1.50), i.e. a 50% loss
            on that leg. The other leg keeps running.

  EXIT      Anything still open is closed at 15:20.

  NO TARGET, no adjustment, no re-entry. One shot per expiry day.

Every offset is tested independently over the same days, so the four columns
are directly comparable.

Fill convention: a leg that gaps through its stop fills at the bar open; a leg
whose bar merely trades through the stop fills at the stop price itself. That
is the correct treatment for a resting order and it is what the audited
intraday-straddle scripts do - see backtesting/docs/lookahead-audit.md.

Output: backtesting/results/expiry-day-short-premium/
"""
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

BASE_FILENAME = "expiry_day_straddle_strangle_2020_2026"
IST_SUFFIX = "+05:30"
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday"]
STRIKE_STEP = 50

# Modelled margin, same convention as the finalized straddle specs:
# 10% of contract value per naked short lot, the lighter side netted at 30%.
MARGIN_NAKED_PCT = 0.10
MARGIN_NET_PCT = 0.30


@dataclass
class PriceRow:
    timestamp: str
    open_value: float
    high_value: float


@dataclass
class ContractData:
    path: Path
    rows_by_timestamp: Dict[str, PriceRow]


@dataclass
class LegOutcome:
    exit_timestamp: str
    exit_price: float
    exit_reason: str
    points: float
    gross: float


@dataclass
class DayResult:
    offset: int
    entry_date: str
    day_of_week: str
    status: str
    skip_reason: str
    expiry_date: str
    spot_open: str
    base_atm: str
    centre_strike: str
    centre_shift: str
    ce_strike: str
    pe_strike: str
    lot_size: str
    lots: str
    qty: str
    balance_ratio: str
    ce_entry: str
    ce_stop: str
    ce_exit_ts: str
    ce_exit_price: str
    ce_exit_reason: str
    pe_entry: str
    pe_stop: str
    pe_exit_ts: str
    pe_exit_price: str
    pe_exit_reason: str
    margin: str
    gross_pnl: str
    brokerage: str
    net_pnl: str
    remarks: str


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def fmt(v: float) -> str:
    return f"{v:.2f}"


def build_ts(day: str, time_text: str) -> str:
    h, m = time_text.split(":")
    return f"{day}T{h}:{m}:00{IST_SUFFIX}"


def expiry_suffix(expiry_date: str) -> str:
    return datetime.datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%d_%b_%y").upper()


def round_to_strike(price: float) -> int:
    return int(round(price / STRIKE_STEP) * STRIKE_STEP)


def lot_config(expiry_date: str) -> Tuple[int, int]:
    """(lot_size, num_lots) targeting ~300 quantity, keyed to the EXPIRY date."""
    d = datetime.date.fromisoformat(expiry_date)
    if d <= datetime.date(2021, 10, 6):
        return 75, 4
    if d <= datetime.date(2024, 4, 25):
        return 50, 6
    if d <= datetime.date(2024, 11, 21):
        return 25, 12
    if d <= datetime.date(2025, 12, 30):
        return 75, 4
    return 65, 5


def position_margin(ce_strike: int, pe_strike: int, qty: int) -> float:
    ce_notional = ce_strike * qty
    pe_notional = pe_strike * qty
    heavy, light = max(ce_notional, pe_notional), min(ce_notional, pe_notional)
    return MARGIN_NAKED_PCT * heavy + MARGIN_NET_PCT * MARGIN_NAKED_PCT * light


def compute_cagr(net_total: float, capital: float, first_day: str, last_day: str) -> float:
    days = (datetime.date.fromisoformat(last_day) - datetime.date.fromisoformat(first_day)).days
    if days <= 0 or capital <= 0:
        return 0.0
    ratio = 1.0 + net_total / capital
    if ratio <= 0.0:
        return -100.0
    return (ratio ** (365.25 / days) - 1.0) * 100.0


def max_drawdown(net_pnls: Sequence[float]) -> float:
    equity = peak = dd = 0.0
    for v in net_pnls:
        equity += v
        peak = max(peak, equity)
        dd = max(dd, peak - equity)
    return dd


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger(BASE_FILENAME)
    for h in logger.handlers:
        h.close()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


# --------------------------------------------------------------------------- #
# data loading
# --------------------------------------------------------------------------- #
def load_spot(spot_file: Path, entry_time: str) -> Tuple[List[str], Dict[str, float]]:
    marker = f"T{entry_time}:00"
    days: List[str] = []
    seen: Set[str] = set()
    open_at_entry: Dict[str, float] = {}
    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            day = ts[:10]
            if day not in seen:
                seen.add(day)
                days.append(day)
            if marker in ts:
                open_at_entry[day] = float(row["open"])
    return days, open_at_entry


def load_expiry_folders(options_dir: Path) -> Set[str]:
    return {p.name for p in options_dir.iterdir() if p.is_dir()}


def load_contract(path: Path, cache: Dict[Path, Optional[ContractData]]) -> Optional[ContractData]:
    if path in cache:
        return cache[path]
    if not path.exists():
        cache[path] = None
        return None
    rows: Dict[str, PriceRow] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            rows[ts] = PriceRow(ts, float(row["open"]), float(row["high"]))
    data = ContractData(path=path, rows_by_timestamp=rows)
    cache[path] = data
    return data


# --------------------------------------------------------------------------- #
# strategy
# --------------------------------------------------------------------------- #
def resolve_leg(contract: ContractData, entry_open: float, entry_ts: str,
                exit_ts: str, sl_factor: float, slippage: float,
                qty: int) -> LegOutcome:
    """
    Walk the 1-minute bars from entry to exit.

    A bar whose OPEN is already at or beyond the stop gapped through it, so it
    fills at that open. A bar that only reaches the stop intrabar fills at the
    stop price - a resting order would have been taken there. Both are prices
    reachable at or after the moment the stop became live, so neither reads
    ahead of the trigger.
    """
    stop = entry_open * sl_factor
    for ts in sorted(t for t in contract.rows_by_timestamp if entry_ts <= t <= exit_ts):
        row = contract.rows_by_timestamp[ts]
        if row.open_value >= stop:
            pts = entry_open - row.open_value - 2 * slippage
            return LegOutcome(ts, row.open_value, "gap_sl", pts, pts * qty)
        if row.high_value >= stop:
            pts = entry_open - stop - 2 * slippage
            return LegOutcome(ts, stop, "sl", pts, pts * qty)

    exit_row = contract.rows_by_timestamp.get(exit_ts)
    if exit_row is not None:
        pts = entry_open - exit_row.open_value - 2 * slippage
        return LegOutcome(exit_ts, exit_row.open_value, "day_close", pts, pts * qty)

    earlier = [t for t in contract.rows_by_timestamp if t <= exit_ts]
    if earlier:
        last = max(earlier)
        px = contract.rows_by_timestamp[last].open_value
        pts = entry_open - px - 2 * slippage
        return LegOutcome(last, px, "last_bar_before_exit", pts, pts * qty)

    return LegOutcome(exit_ts, entry_open, "missing_exit_bar", 0.0, 0.0)


def centre_candidates(base_atm: int, steps: int) -> List[int]:
    """0, +50, -50, +100, -100 ... out to `steps` strikes either side."""
    out = [base_atm]
    for i in range(1, steps + 1):
        out.append(base_atm + i * STRIKE_STEP)
        out.append(base_atm - i * STRIKE_STEP)
    return out


def _price_pair(
    ce_strike: int, pe_strike: int, expiry_date: str, entry_ts: str,
    options_dir: Path, cache: Dict[Path, Optional[ContractData]],
) -> Optional[Tuple[ContractData, ContractData, float, float]]:
    suffix = expiry_suffix(expiry_date)
    ce = load_contract(options_dir / expiry_date / f"NIFTY_{ce_strike}_CE_{suffix}.csv", cache)
    pe = load_contract(options_dir / expiry_date / f"NIFTY_{pe_strike}_PE_{suffix}.csv", cache)
    if ce is None or pe is None:
        return None
    ce_row = ce.rows_by_timestamp.get(entry_ts)
    pe_row = pe.rows_by_timestamp.get(entry_ts)
    if ce_row is None or pe_row is None:
        return None
    if ce_row.open_value <= 0 or pe_row.open_value <= 0:
        return None
    return ce, pe, ce_row.open_value, pe_row.open_value


def select_strikes_legs(
    base_atm: int, offset: int, expiry_date: str, entry_ts: str,
    options_dir: Path, cache: Dict[Path, Optional[ContractData]],
    balance_max_diff: float, steps: int, fallback: bool,
) -> Tuple[Optional[dict], str]:
    """
    Balance by moving each leg independently.

    On expiry day the strike nearest spot is already the most balanced pair, so
    shifting both legs together (select_strikes) can only make the ratio worse.
    Moving the CE and the PE separately can genuinely equalise the two premiums:
    sell the call further out and the put nearer in, or the reverse.

    The strangle stops being symmetric in strike distance, which is the price of
    being symmetric in premium. Candidates are ranked by how little they deviate
    from the nominal strikes, then by balance.
    """
    ce_nominal, pe_nominal = base_atm + offset, base_atm - offset
    best: Optional[dict] = None
    saw_any = False
    passing: List[dict] = []

    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            ce_strike = ce_nominal + i * STRIKE_STEP
            pe_strike = pe_nominal + j * STRIKE_STEP
            if ce_strike < pe_strike:
                continue                      # never invert the two legs
            got = _price_pair(ce_strike, pe_strike, expiry_date, entry_ts,
                              options_dir, cache)
            if got is None:
                continue
            ce, pe, ce_open, pe_open = got
            saw_any = True
            ratio = min(ce_open, pe_open) / max(ce_open, pe_open)
            cand = {
                "centre": base_atm, "shift": 0,
                "ce_shift": i, "pe_shift": j,
                "ce_strike": ce_strike, "pe_strike": pe_strike,
                "ce": ce, "pe": pe, "ce_open": ce_open, "pe_open": pe_open,
                "ratio": ratio, "deviation": abs(i) + abs(j),
            }
            if ratio >= 1.0 - balance_max_diff:
                passing.append(cand)
            if best is None or ratio > best["ratio"]:
                best = cand

    if passing:
        passing.sort(key=lambda c: (c["deviation"], -c["ratio"]))
        return passing[0], ""
    if not saw_any:
        return None, "no_priceable_pair"
    if fallback and best is not None:
        return best, ""
    return None, "balance_filter"


def select_strikes(
    base_atm: int, offset: int, expiry_date: str, entry_ts: str,
    options_dir: Path, cache: Dict[Path, Optional[ContractData]],
    balance_max_diff: float, steps: int, fallback: bool,
) -> Tuple[Optional[dict], str]:
    """
    Find a centre strike whose CE and PE premiums are within tolerance.

    Both legs move together, so a strangle keeps its symmetric strike distance.

    Returns (chosen, skip_reason). `chosen` carries the contracts, their entry
    prices, the centre used and how far it was shifted.
    """
    suffix = expiry_suffix(expiry_date)
    best: Optional[dict] = None
    saw_any = False

    for centre in centre_candidates(base_atm, steps):
        ce_strike, pe_strike = centre + offset, centre - offset
        ce_path = options_dir / expiry_date / f"NIFTY_{ce_strike}_CE_{suffix}.csv"
        pe_path = options_dir / expiry_date / f"NIFTY_{pe_strike}_PE_{suffix}.csv"
        ce = load_contract(ce_path, cache)
        pe = load_contract(pe_path, cache)
        if ce is None or pe is None:
            continue
        ce_row = ce.rows_by_timestamp.get(entry_ts)
        pe_row = pe.rows_by_timestamp.get(entry_ts)
        if ce_row is None or pe_row is None:
            continue
        ce_open, pe_open = ce_row.open_value, pe_row.open_value
        if ce_open <= 0 or pe_open <= 0:
            continue

        saw_any = True
        ratio = min(ce_open, pe_open) / max(ce_open, pe_open)
        cand = {
            "centre": centre, "shift": (centre - base_atm) // STRIKE_STEP,
            "ce_strike": ce_strike, "pe_strike": pe_strike,
            "ce": ce, "pe": pe, "ce_open": ce_open, "pe_open": pe_open,
            "ratio": ratio,
        }
        if ratio >= 1.0 - balance_max_diff:
            return cand, ""
        if best is None or ratio > best["ratio"]:
            best = cand

    if not saw_any:
        return None, "no_priceable_pair"
    if fallback and best is not None:
        return best, ""
    return None, "balance_filter"


def run_offset(
    offset: int, expiry_days: List[str], spot_open: Dict[str, float],
    args: argparse.Namespace, cache: Dict[Path, Optional[ContractData]],
    logger: logging.Logger,
) -> List[DayResult]:
    results: List[DayResult] = []
    brokerage = args.brokerage_per_order * 4          # 2 legs in, 2 legs out

    for day in expiry_days:
        wd = datetime.date.fromisoformat(day).weekday()
        day_name = WEEKDAY_NAMES[wd]
        entry_ts = build_ts(day, args.entry_time)
        exit_ts = build_ts(day, args.exit_time)
        blank = dict(offset=offset, entry_date=day, day_of_week=day_name,
                     expiry_date=day)

        spot = spot_open.get(day)
        if spot is None:
            results.append(DayResult(**blank, status="SKIPPED",
                                     skip_reason="missing_spot_entry",
                                     spot_open="", base_atm="", centre_strike="",
                                     centre_shift="", ce_strike="", pe_strike="",
                                     lot_size="", lots="", qty="", balance_ratio="",
                                     ce_entry="", ce_stop="", ce_exit_ts="",
                                     ce_exit_price="", ce_exit_reason="",
                                     pe_entry="", pe_stop="", pe_exit_ts="",
                                     pe_exit_price="", pe_exit_reason="",
                                     margin="", gross_pnl="", brokerage="",
                                     net_pnl="", remarks=f"No spot bar at {entry_ts}"))
            continue

        base_atm = round_to_strike(spot)
        lot_size, lots = lot_config(day)
        qty = lot_size * lots

        # offset 0 must stay a true straddle, so it always balances by centre.
        picker = (select_strikes_legs
                  if args.balance_mode == "legs" and offset != 0
                  else select_strikes)
        chosen, reason = picker(
            base_atm, offset, day, entry_ts, args.options_dir, cache,
            args.balance_max_diff, args.strike_search_steps, args.balance_fallback,
        )
        if chosen is None:
            results.append(DayResult(**blank, status="SKIPPED", skip_reason=reason,
                                     spot_open=fmt(spot), base_atm=str(base_atm),
                                     centre_strike="", centre_shift="",
                                     ce_strike="", pe_strike="",
                                     lot_size=str(lot_size), lots=str(lots),
                                     qty=str(qty), balance_ratio="",
                                     ce_entry="", ce_stop="", ce_exit_ts="",
                                     ce_exit_price="", ce_exit_reason="",
                                     pe_entry="", pe_stop="", pe_exit_ts="",
                                     pe_exit_price="", pe_exit_reason="",
                                     margin="", gross_pnl="", brokerage="",
                                     net_pnl="", remarks=""))
            continue

        ce_out = resolve_leg(chosen["ce"], chosen["ce_open"], entry_ts, exit_ts,
                             args.sl_factor, args.slippage_per_order, qty)
        pe_out = resolve_leg(chosen["pe"], chosen["pe_open"], entry_ts, exit_ts,
                             args.sl_factor, args.slippage_per_order, qty)
        gross = ce_out.gross + pe_out.gross
        net = gross - brokerage

        results.append(DayResult(
            **blank, status="TRADED", skip_reason="",
            spot_open=fmt(spot), base_atm=str(base_atm),
            centre_strike=str(chosen["centre"]),
            centre_shift=(f"ce{chosen['ce_shift']:+d}/pe{chosen['pe_shift']:+d}"
                          if "ce_shift" in chosen else str(chosen["shift"])),
            ce_strike=str(chosen["ce_strike"]), pe_strike=str(chosen["pe_strike"]),
            lot_size=str(lot_size), lots=str(lots), qty=str(qty),
            balance_ratio=fmt(chosen["ratio"]),
            ce_entry=fmt(chosen["ce_open"]),
            ce_stop=fmt(chosen["ce_open"] * args.sl_factor),
            ce_exit_ts=ce_out.exit_timestamp, ce_exit_price=fmt(ce_out.exit_price),
            ce_exit_reason=ce_out.exit_reason,
            pe_entry=fmt(chosen["pe_open"]),
            pe_stop=fmt(chosen["pe_open"] * args.sl_factor),
            pe_exit_ts=pe_out.exit_timestamp, pe_exit_price=fmt(pe_out.exit_price),
            pe_exit_reason=pe_out.exit_reason,
            margin=fmt(position_margin(chosen["ce_strike"], chosen["pe_strike"], qty)),
            gross_pnl=fmt(gross), brokerage=fmt(brokerage), net_pnl=fmt(net),
            remarks="",
        ))
        logger.info("TRADED offset=%d date=%s ce=%d pe=%d shift=%d ratio=%.2f "
                    "ce_exit=%s pe_exit=%s net=%.2f",
                    offset, day, chosen["ce_strike"], chosen["pe_strike"],
                    chosen["shift"], chosen["ratio"], ce_out.exit_reason,
                    pe_out.exit_reason, net)
    return results


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #
def label_for(offset: int) -> str:
    return "STRADDLE" if offset == 0 else f"STRANGLE_{offset}"


def stats_for(rows: List[DayResult]) -> dict:
    traded = [r for r in rows if r.status == "TRADED"]
    nets = [float(r.net_pnl) for r in traded]
    wins = [n for n in nets if n > 0]
    losses = [n for n in nets if n < 0]
    both_sl = sum(1 for r in traded if "sl" in r.ce_exit_reason and "sl" in r.pe_exit_reason)
    one_sl = sum(1 for r in traded
                 if ("sl" in r.ce_exit_reason) != ("sl" in r.pe_exit_reason))
    no_sl = sum(1 for r in traded
                if "sl" not in r.ce_exit_reason and "sl" not in r.pe_exit_reason)
    shifted = sum(1 for r in traded
                  if r.centre_shift not in ("", "0", "ce+0/pe+0"))
    return {
        "traded": len(traded),
        "skipped": len(rows) - len(traded),
        "net": sum(nets),
        "gross": sum(float(r.gross_pnl) for r in traded),
        "costs": sum(float(r.brokerage) for r in traded),
        "wins": len(wins), "losses": len(losses),
        "win_rate": (len(wins) / len(traded) * 100) if traded else 0.0,
        "profit_factor": (sum(wins) / abs(sum(losses))) if losses else float("inf"),
        "max_dd": max_drawdown(nets),
        "best": max(nets) if nets else 0.0,
        "worst": min(nets) if nets else 0.0,
        "avg": (sum(nets) / len(nets)) if nets else 0.0,
        "both_sl": both_sl, "one_sl": one_sl, "no_sl": no_sl,
        "shifted": shifted,
        "peak_margin": max((float(r.margin) for r in traded), default=0.0),
        "nets": nets,
    }


def write_daywise_csv(rows: List[DayResult], path: Path) -> None:
    fields = list(DayResult.__dataclass_fields__.keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({f: getattr(r, f) for f in fields})


def write_summary(all_rows: Dict[int, List[DayResult]], args: argparse.Namespace,
                  path: Path, first_day: str, last_day: str) -> None:
    offsets = sorted(all_rows)
    lines = [
        "# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)",
        "",
        "## Strategy",
        "",
        "- **Expiry days only.** One trade per weekly expiry, no other day is traded.",
        f"- Entry: `{args.entry_time}` — sell 1 CE and 1 PE of the contract expiring that day",
        "- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the "
        "centre strike and PE the same distance below",
        f"- Balance filter: CE and PE premiums must be within "
        f"`{args.balance_max_diff * 100:.0f}%` (min/max >= "
        f"{(1 - args.balance_max_diff) * 100:.0f}%)",
        (f"- Balancing by **centre shift**: move both legs together by {STRIKE_STEP} points "
          f"— 0, +{STRIKE_STEP}, -{STRIKE_STEP}, ... out to ±{args.strike_search_steps} strikes. "
          "A strangle keeps its symmetric strike distance."
          if args.balance_mode == "centre" else
          f"- Balancing by **independent legs**: move the CE and PE strikes separately, "
          f"each up to ±{args.strike_search_steps} strikes, and take the closest-to-nominal "
          "pair whose premiums match. The strangle is no longer symmetric in strike "
          "distance. Offset 0 still uses a centre shift so it stays a true straddle."),
        f"- Unbalanced days are {'entered at the best available pair' if args.balance_fallback else '**skipped**'}",
        f"- Stop loss: **independent per leg**, triggered when a leg reaches "
        f"`{args.sl_factor * 100:.0f}%` of its entry price "
        f"({(args.sl_factor - 1) * 100:.0f}% loss on that leg). The other leg keeps running.",
        f"- Exit: anything still open is closed at `{args.exit_time}`",
        "- No target, no adjustment, no re-entry",
        "- Quantity: ~300 (expiry-aware lot sizing: 75/50/25/75/65 by era)",
        f"- Brokerage: Rs {args.brokerage_per_order:.0f}/order → "
        f"Rs {args.brokerage_per_order * 4:.0f} per completed position",
        f"- Slippage: {args.slippage_per_order:.2f} pt/order",
        f"- Period: `{first_day}` to `{last_day}`",
        "",
        "## Comparison",
        "",
        "Margin is modelled — 10% of contract value per naked short lot with the lighter "
        "side netted at 30% — not SPAN. Verify before sizing.",
        "",
        "| Variant | Traded | Skipped | Win% | Net P/L | CAGR on peak margin | Peak margin | Max DD | PF | Avg/day |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for off in offsets:
        s = stats_for(all_rows[off])
        cg = compute_cagr(s["net"], s["peak_margin"], first_day, last_day) if s["peak_margin"] else 0.0
        pf = "inf" if s["profit_factor"] == float("inf") else f"{s['profit_factor']:.2f}"
        lines.append(
            f"| {label_for(off)} | {s['traded']} | {s['skipped']} | {s['win_rate']:.1f}% | "
            f"Rs {s['net']:,.0f} | {cg:.2f}% | Rs {s['peak_margin']:,.0f} | "
            f"Rs {s['max_dd']:,.0f} | {pf} | Rs {s['avg']:,.0f} |"
        )

    lines += ["", "## Stop-loss behaviour", "",
              "| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |",
              "|---|---:|---:|---:|---:|"]
    for off in offsets:
        s = stats_for(all_rows[off])
        t = max(s["traded"], 1)
        lines.append(
            f"| {label_for(off)} | {s['both_sl']} ({s['both_sl']/t*100:.1f}%) | "
            f"{s['one_sl']} ({s['one_sl']/t*100:.1f}%) | {s['no_sl']} ({s['no_sl']/t*100:.1f}%) | "
            f"{s['shifted']} ({s['shifted']/t*100:.1f}%) |")

    for off in offsets:
        rows = all_rows[off]
        s = stats_for(rows)
        lines += ["", f"## {label_for(off)}", "",
                  f"- Traded: `{s['traded']}`  Skipped: `{s['skipped']}`",
                  f"- Gross P/L: `Rs {s['gross']:,.2f}`  Costs: `Rs {s['costs']:,.2f}`",
                  f"- **Net P/L: `Rs {s['net']:,.2f}`**",
                  f"- Win rate: `{s['win_rate']:.2f}%` ({s['wins']}W / {s['losses']}L)",
                  f"- Max drawdown: `Rs {s['max_dd']:,.2f}`",
                  f"- Best day: `Rs {s['best']:,.2f}`  Worst day: `Rs {s['worst']:,.2f}`",
                  ""]
        by_year: Dict[str, List[float]] = {}
        for r in rows:
            if r.status == "TRADED":
                by_year.setdefault(r.entry_date[:4], []).append(float(r.net_pnl))
        lines += ["| Year | Days | Net P/L | Win % |", "|---|---:|---:|---:|"]
        for y in sorted(by_year):
            v = by_year[y]
            w = sum(1 for x in v if x > 0)
            lines.append(f"| {y} | {len(v)} | Rs {sum(v):,.0f} | {w/len(v)*100:.1f}% |")
        skips: Dict[str, int] = {}
        for r in rows:
            if r.status != "TRADED":
                skips[r.skip_reason] = skips.get(r.skip_reason, 0) + 1
        if skips:
            lines += ["", "| Skip reason | Count |", "|---|---:|"]
            for k in sorted(skips, key=lambda k: -skips[k]):
                lines.append(f"| `{k}` | {skips[k]} |")

    lines += ["", "## Notes", "",
              "- A leg that gaps through its stop fills at the bar open; a leg that only "
              "trades through it fills at the stop price. Neither reads ahead of the trigger.",
              "- Expiry dates come from the options folder structure (Thursday to Aug 2025, "
              "Tuesday from Sep 2025, holiday-shifted).",
              "- Every offset is evaluated on the same expiry days, so the columns are "
              "directly comparable.",
              ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
def output_tag(args: argparse.Namespace) -> str:
    tag = f"sl{int(round(args.sl_factor * 100))}"
    tag += f"_bal{int(round(args.balance_max_diff * 100))}"
    if args.balance_mode != "centre":
        tag += f"_{args.balance_mode}"
    tag += f"_srch{args.strike_search_steps}"
    if args.balance_fallback:
        tag += "_fb"
    if args.entry_time != "09:20":
        tag += "_e" + args.entry_time.replace(":", "")
    return tag


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[3]
    p = argparse.ArgumentParser(
        description="Expiry-day short straddle and strangles with independent per-leg stops.")
    p.add_argument("--spot-file", type=Path,
                   default=repo_root / "nifty" / "NIFTY50_INDEX_5m_last_7y.csv")
    p.add_argument("--options-dir", type=Path,
                   default=repo_root / "NiftyOptions_2020_2026" / "Options")
    p.add_argument("--results-dir", type=Path,
                   default=repo_root / "backtesting" / "results" / "expiry-day-short-premium")
    p.add_argument("--offsets", type=int, nargs="+", default=[0, 100, 200, 300],
                   help="0 = ATM straddle; 100/200/300 = strangle width in points.")
    p.add_argument("--entry-time", default="09:20")
    p.add_argument("--exit-time", default="15:20")
    p.add_argument("--sl-factor", type=float, default=1.50,
                   help="Leg is bought back at this multiple of its entry price.")
    p.add_argument("--balance-max-diff", type=float, default=0.20,
                   help="Max |CE-PE|/max(CE,PE) accepted at entry.")
    p.add_argument("--strike-search-steps", type=int, default=5,
                   help="Strikes either side of ATM to search for a balanced pair.")
    p.add_argument("--balance-mode", choices=["centre", "legs"], default="centre",
                   help="centre: shift both legs together, keeping a strangle "
                        "symmetric in strike distance. legs: move the CE and PE "
                        "strikes independently to equalise the premiums instead "
                        "(offset 0 always uses centre, or it stops being a straddle).")
    p.add_argument("--balance-fallback", action="store_true",
                   help="Enter the best-balanced pair instead of skipping the day.")
    p.add_argument("--brokerage-per-order", type=float, default=25.0)
    p.add_argument("--slippage-per-order", type=float, default=0.50)
    p.add_argument("--start-date", default="2020-01-01")
    p.add_argument("--end-date", default="2026-12-31")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    tag = output_tag(args)
    logger = configure_logger(args.results_dir / f"{BASE_FILENAME}_{tag}.log")

    days, spot_open = load_spot(args.spot_file, args.entry_time)
    expiries = load_expiry_folders(args.options_dir)
    expiry_days = [d for d in days
                   if d in expiries and args.start_date <= d <= args.end_date]
    if not expiry_days:
        raise SystemExit("No expiry days in range — check --options-dir and dates.")

    print(f"expiry days in range: {len(expiry_days)} "
          f"({expiry_days[0]} .. {expiry_days[-1]})")

    cache: Dict[Path, Optional[ContractData]] = {}
    all_rows: Dict[int, List[DayResult]] = {}
    for off in args.offsets:
        rows = run_offset(off, expiry_days, spot_open, args, cache, logger)
        all_rows[off] = rows
        s = stats_for(rows)
        print(f"  {label_for(off):<14} traded={s['traded']:>4} skipped={s['skipped']:>3} "
              f"net={s['net']:>12,.0f} maxdd={s['max_dd']:>10,.0f} win={s['win_rate']:.1f}%")

    flat = [r for off in sorted(all_rows) for r in all_rows[off]]
    write_daywise_csv(flat, args.results_dir / f"{BASE_FILENAME}_{tag}_daywise.csv")
    summary = args.results_dir / f"{BASE_FILENAME}_{tag}_summary.md"
    write_summary(all_rows, args, summary, expiry_days[0], expiry_days[-1])
    print(f"Summary: {summary}")


if __name__ == "__main__":
    main()
