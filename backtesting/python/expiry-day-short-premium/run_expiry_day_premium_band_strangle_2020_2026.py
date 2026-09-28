#!/usr/bin/env python3
"""
Expiry-day premium-band short strangle — NIFTY 2020-2026.

Trades ONLY on weekly expiry days. One shot per expiry day.

  ENTRY     10:00. Sell one CE and one PE of the contract expiring today.
            Strikes are chosen by ABSOLUTE PREMIUM, not by a fixed distance
            from ATM: on each side independently, walk outward from the ATM
            strike and take the contract whose 10:00 price sits inside
            [--min-premium, --max-premium] and is CLOSEST TO THE MIDPOINT of
            that band. Ties go to the strike nearer ATM.

            This is the difference from the sibling script in this folder,
            which sells a fixed 0/100/200/300 points out. A fixed offset sells
            a different amount of premium in 2020 (Nifty 12,000) than in 2025
            (Nifty 25,000); a premium band sells the same amount throughout,
            and lets the strike distance float with volatility instead.

  FALLBACK  If no strike on a side is priced inside the band, take the one
            whose price is NEAREST to the band and mark the leg
            `band_fallback`. The day is never skipped for being out of band.

  STOP      Independent per leg. A leg is bought back when its price reaches
            --sl-factor times what it was sold for (default 2.0 = a 100% loss
            on that leg). The other leg keeps running.

  EXIT      Anything still open is closed at 15:20.

  NO TARGET, no adjustment, no re-entry.

Fill convention: a leg that gaps through its stop fills at the bar open; a leg
whose bar merely trades through the stop fills at the stop price itself. That
is the correct treatment for a resting order and it is what the audited
intraday-straddle scripts do - see backtesting/docs/lookahead-audit.md.

A warning about size. Costs here are flat per order but the premium sold is
tiny, so the cost ratio is brutal at one lot: selling 7.5 + 7.5 points on a
75-lot collects Rs 1,125, while Rs 25/order brokerage plus 0.50 pt/order
slippage takes Rs 250 of it. Read the "costs as % of premium" line in the
summary before reading the P/L.

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

BASE_FILENAME = "expiry_day_premium_band_strangle_2020_2026"
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
    entry_date: str
    day_of_week: str
    status: str
    skip_reason: str
    expiry_date: str
    spot_open: str
    base_atm: str
    ce_strike: str
    pe_strike: str
    ce_dist_pts: str
    pe_dist_pts: str
    ce_in_band: str
    pe_in_band: str
    lot_size: str
    lots: str
    qty: str
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
    premium_pts: str
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


def lot_size_for(expiry_date: str) -> int:
    """Lot size active for this contract, keyed to its EXPIRY date.

    Not the trade date: a weekly contract open across a lot-size change keeps
    the size it was introduced with. Getting this wrong silently rescales every
    number in the run.
    """
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


def scan_side(
    base_atm: int, side: str, expiry_date: str, entry_ts: str,
    options_dir: Path, cache: Dict[Path, Optional[ContractData]],
    min_price: float, max_price: float, max_search: int,
) -> Optional[dict]:
    """
    Choose one leg by premium.

    Walks strikes outward from ATM - upward for a CE, downward for a PE - and
    prices each at the exact `entry_ts` bar. A strike priced inside the band is
    ranked by |price - midpoint|; one outside it is ranked by how far outside.
    In-band always beats out-of-band, and ties break toward the nearer strike.

    The scan stops one strike AFTER the price first falls under `min_price`:
    further out is only cheaper, but that first cheap strike still has to be
    recorded, because on a day when the whole chain opens under the band it is
    the only fallback there is.

    Returns None only when nothing on this side was priceable at all.
    """
    suffix = expiry_suffix(expiry_date)
    step = STRIKE_STEP if side == "CE" else -STRIKE_STEP
    midpoint = (min_price + max_price) / 2.0
    in_band: List[dict] = []
    out_band: List[dict] = []

    for i in range(1, max_search + 1):
        strike = base_atm + i * step
        if strike <= 0:
            break
        path = options_dir / expiry_date / f"NIFTY_{strike}_{side}_{suffix}.csv"
        contract = load_contract(path, cache)
        if contract is None:
            continue
        row = contract.rows_by_timestamp.get(entry_ts)
        if row is None or row.open_value <= 0:
            continue
        price = row.open_value
        cand = {
            "strike": strike, "price": price, "contract": contract,
            "dist": i * STRIKE_STEP,
        }
        if min_price <= price <= max_price:
            cand["in_band"] = True
            cand["rank"] = abs(price - midpoint)
            in_band.append(cand)
        else:
            cand["in_band"] = False
            cand["rank"] = max(0.0, min_price - price, price - max_price)
            out_band.append(cand)
        if price < min_price:
            break

    pool = in_band or out_band
    if not pool:
        return None
    return min(pool, key=lambda c: (c["rank"], c["dist"]))


def select_premium_band(
    base_atm: int, expiry_date: str, entry_ts: str,
    options_dir: Path, cache: Dict[Path, Optional[ContractData]],
    min_price: float, max_price: float, max_search: int,
) -> Tuple[Optional[dict], str]:
    """
    Pick the CE and the PE independently by absolute premium.

    No cross-leg balance filter: the band already forces the two premiums into
    rough parity, and this family's own result is that a balance filter mostly
    just skips days (189 of 334 in the sibling script) without earning it.

    The legs cannot invert - every CE strike is above ATM and every PE strike
    below it.
    """
    ce = scan_side(base_atm, "CE", expiry_date, entry_ts, options_dir, cache,
                   min_price, max_price, max_search)
    if ce is None:
        return None, "no_ce_candidate"
    pe = scan_side(base_atm, "PE", expiry_date, entry_ts, options_dir, cache,
                   min_price, max_price, max_search)
    if pe is None:
        return None, "no_pe_candidate"
    return {"ce": ce, "pe": pe}, ""


def blank_row(day: str, day_name: str, **over) -> DayResult:
    base = {f: "" for f in DayResult.__dataclass_fields__}
    base.update(entry_date=day, day_of_week=day_name, expiry_date=day,
                status="SKIPPED")
    base.update(over)
    return DayResult(**base)


def run_days(
    expiry_days: List[str], spot_open: Dict[str, float],
    args: argparse.Namespace, cache: Dict[Path, Optional[ContractData]],
    logger: logging.Logger,
) -> List[DayResult]:
    results: List[DayResult] = []
    brokerage = args.brokerage_per_order * 4          # 2 legs in, 2 legs out

    for day in expiry_days:
        day_name = WEEKDAY_NAMES[datetime.date.fromisoformat(day).weekday()]
        entry_ts = build_ts(day, args.entry_time)
        exit_ts = build_ts(day, args.exit_time)

        spot = spot_open.get(day)
        if spot is None:
            results.append(blank_row(day, day_name, skip_reason="missing_spot_entry",
                                     remarks=f"No spot bar at {entry_ts}"))
            continue

        base_atm = round_to_strike(spot)
        lot_size = lot_size_for(day)
        qty = lot_size * args.lots

        chosen, reason = select_premium_band(
            base_atm, day, entry_ts, args.options_dir, cache,
            args.min_premium, args.max_premium, args.max_search_strikes,
        )
        if chosen is None:
            results.append(blank_row(day, day_name, skip_reason=reason,
                                     spot_open=fmt(spot), base_atm=str(base_atm),
                                     lot_size=str(lot_size), lots=str(args.lots),
                                     qty=str(qty)))
            continue

        ce, pe = chosen["ce"], chosen["pe"]
        ce_out = resolve_leg(ce["contract"], ce["price"], entry_ts, exit_ts,
                             args.sl_factor, args.slippage_per_order, qty)
        pe_out = resolve_leg(pe["contract"], pe["price"], entry_ts, exit_ts,
                             args.sl_factor, args.slippage_per_order, qty)
        gross = ce_out.gross + pe_out.gross
        net = gross - brokerage

        results.append(DayResult(
            entry_date=day, day_of_week=day_name, status="TRADED", skip_reason="",
            expiry_date=day, spot_open=fmt(spot), base_atm=str(base_atm),
            ce_strike=str(ce["strike"]), pe_strike=str(pe["strike"]),
            ce_dist_pts=str(ce["dist"]), pe_dist_pts=str(pe["dist"]),
            ce_in_band="yes" if ce["in_band"] else "no",
            pe_in_band="yes" if pe["in_band"] else "no",
            lot_size=str(lot_size), lots=str(args.lots), qty=str(qty),
            ce_entry=fmt(ce["price"]), ce_stop=fmt(ce["price"] * args.sl_factor),
            ce_exit_ts=ce_out.exit_timestamp, ce_exit_price=fmt(ce_out.exit_price),
            ce_exit_reason=ce_out.exit_reason,
            pe_entry=fmt(pe["price"]), pe_stop=fmt(pe["price"] * args.sl_factor),
            pe_exit_ts=pe_out.exit_timestamp, pe_exit_price=fmt(pe_out.exit_price),
            pe_exit_reason=pe_out.exit_reason,
            premium_pts=fmt(ce["price"] + pe["price"]),
            margin=fmt(position_margin(ce["strike"], pe["strike"], qty)),
            gross_pnl=fmt(gross), brokerage=fmt(brokerage), net_pnl=fmt(net),
            remarks="",
        ))
        logger.info("TRADED date=%s ce=%d@%.2f%s pe=%d@%.2f%s ce_exit=%s "
                    "pe_exit=%s net=%.2f",
                    day, ce["strike"], ce["price"], "" if ce["in_band"] else "*",
                    pe["strike"], pe["price"], "" if pe["in_band"] else "*",
                    ce_out.exit_reason, pe_out.exit_reason, net)
    return results


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #
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
    premium_pts = sum(float(r.premium_pts) for r in traded)
    premium_rs = sum(float(r.premium_pts) * float(r.qty) for r in traded)
    return {
        "traded": len(traded),
        "skipped": len(rows) - len(traded),
        "net": sum(nets),
        "gross": sum(float(r.gross_pnl) for r in traded),
        "brokerage": sum(float(r.brokerage) for r in traded),
        "wins": len(wins), "losses": len(losses),
        "win_rate": (len(wins) / len(traded) * 100) if traded else 0.0,
        "profit_factor": (sum(wins) / abs(sum(losses))) if losses else float("inf"),
        "max_dd": max_drawdown(nets),
        "best": max(nets) if nets else 0.0,
        "worst": min(nets) if nets else 0.0,
        "avg": (sum(nets) / len(nets)) if nets else 0.0,
        "both_sl": both_sl, "one_sl": one_sl, "no_sl": no_sl,
        "ce_fb": sum(1 for r in traded if r.ce_in_band == "no"),
        "pe_fb": sum(1 for r in traded if r.pe_in_band == "no"),
        "any_fb": sum(1 for r in traded if "no" in (r.ce_in_band, r.pe_in_band)),
        "premium_pts": premium_pts,
        "premium_rs": premium_rs,
        "avg_premium_pts": (premium_pts / len(traded)) if traded else 0.0,
        "avg_ce_dist": (sum(float(r.ce_dist_pts) for r in traded) / len(traded)) if traded else 0.0,
        "avg_pe_dist": (sum(float(r.pe_dist_pts) for r in traded) / len(traded)) if traded else 0.0,
        "peak_margin": max((float(r.margin) for r in traded), default=0.0),
        "nets": nets,
    }


def slippage_rs(rows: List[DayResult], slippage: float) -> float:
    """What the modelled slippage actually cost, in rupees.

    resolve_leg subtracts 2 * slippage points from each leg, so it is already
    inside gross_pnl. It has to be reconstructed here, or the cost ratio would
    report only the brokerage and understate what the trade really paid.
    """
    return sum(2 * slippage * 2 * float(r.qty)
               for r in rows if r.status == "TRADED")


def write_daywise_csv(rows: List[DayResult], path: Path) -> None:
    fields = list(DayResult.__dataclass_fields__.keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({f: getattr(r, f) for f in fields})


def write_summary(rows: List[DayResult], args: argparse.Namespace, path: Path,
                  first_day: str, last_day: str) -> None:
    s = stats_for(rows)
    slip = slippage_rs(rows, args.slippage_per_order)
    total_costs = s["brokerage"] + slip
    cost_pct = (total_costs / s["premium_rs"] * 100) if s["premium_rs"] else 0.0
    cagr = compute_cagr(s["net"], s["peak_margin"], first_day, last_day)
    pf = "inf" if s["profit_factor"] == float("inf") else f"{s['profit_factor']:.2f}"
    t = max(s["traded"], 1)

    lines = [
        "# Expiry-Day Premium-Band Short Strangle (NIFTY 2020-2026)",
        "",
        "## Strategy",
        "",
        "- **Expiry days only.** One trade per weekly expiry, no other day is traded.",
        f"- Entry: `{args.entry_time}` — sell 1 CE and 1 PE of the contract expiring that day",
        f"- Strike rule: **by premium, not by distance.** On each side independently, "
        f"walk outward from ATM and take the strike whose `{args.entry_time}` price is "
        f"closest to the midpoint of the `Rs {args.min_premium:g}–{args.max_premium:g}` band",
        "- Ties on that distance go to the strike nearer ATM",
        "- If no strike on a side is inside the band, the nearest-to-band strike is sold "
        "instead and the leg is marked `band_fallback` — **the day is never skipped for "
        "being out of band**",
        f"- Search depth: `{args.max_search_strikes}` strikes "
        f"({args.max_search_strikes * STRIKE_STEP} points) either side of ATM",
        f"- Stop loss: **independent per leg**, triggered when a leg reaches "
        f"`{args.sl_factor * 100:.0f}%` of its entry price "
        f"({(args.sl_factor - 1) * 100:.0f}% loss on that leg). The other leg keeps running.",
        f"- Exit: anything still open is closed at `{args.exit_time}`",
        "- No target, no adjustment, no re-entry",
        f"- Size: **{args.lots} lot(s)** — expiry-aware lot sizing (75/50/25/75/65 by era)",
        f"- Brokerage: Rs {args.brokerage_per_order:.0f}/order → "
        f"Rs {args.brokerage_per_order * 4:.0f} per completed position (2 legs, in and out)",
        f"- Slippage: {args.slippage_per_order:.2f} pt/order",
        f"- Period: `{first_day}` to `{last_day}`",
        "",
        "## Headline",
        "",
        "Margin is modelled — 10% of contract value per naked short lot with the lighter "
        "side netted at 30% — not SPAN. A naked expiry-day short may attract more.",
        "",
        f"- Traded: `{s['traded']}`  Skipped: `{s['skipped']}`",
        f"- **Net P/L: `Rs {s['net']:,.2f}`**",
        f"- Gross P/L (after slippage, before brokerage): `Rs {s['gross']:,.2f}`",
        f"- CAGR on peak margin: `{cagr:.2f}%`  (peak margin `Rs {s['peak_margin']:,.0f}`)",
        f"- Win rate: `{s['win_rate']:.2f}%` ({s['wins']}W / {s['losses']}L)  "
        f"Profit factor: `{pf}`",
        f"- Max drawdown: `Rs {s['max_dd']:,.2f}`",
        f"- Best day: `Rs {s['best']:,.2f}`  Worst day: `Rs {s['worst']:,.2f}`  "
        f"Avg/day: `Rs {s['avg']:,.2f}`",
        "",
        "## What the costs eat",
        "",
        "The number that decides this strategy. Premium sold is small and the costs are "
        "flat, so the ratio is the whole story at one lot.",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Premium collected | Rs {s['premium_rs']:,.0f} |",
        f"| Avg premium per trade | {s['avg_premium_pts']:.2f} pts |",
        f"| Brokerage | Rs {s['brokerage']:,.0f} |",
        f"| Slippage | Rs {slip:,.0f} |",
        f"| **Total costs** | **Rs {total_costs:,.0f}** |",
        f"| **Costs as % of premium collected** | **{cost_pct:.1f}%** |",
        "",
        "## Stop-loss behaviour",
        "",
        "| Outcome | Days | Share |",
        "|---|---:|---:|",
        f"| Both legs stopped | {s['both_sl']} | {s['both_sl']/t*100:.1f}% |",
        f"| One leg stopped | {s['one_sl']} | {s['one_sl']/t*100:.1f}% |",
        f"| Neither stopped (both ran to {args.exit_time}) | {s['no_sl']} | {s['no_sl']/t*100:.1f}% |",
        "",
        "## Band behaviour",
        "",
        f"How often the `Rs {args.min_premium:g}–{args.max_premium:g}` band was actually "
        "reachable at entry. A high fallback count means the band is the wrong one for "
        "this time of day, and the result is not really testing the stated strategy.",
        "",
        "| Leg | Fell back outside the band | Share |",
        "|---|---:|---:|",
        f"| CE | {s['ce_fb']} | {s['ce_fb']/t*100:.1f}% |",
        f"| PE | {s['pe_fb']} | {s['pe_fb']/t*100:.1f}% |",
        f"| Either leg | {s['any_fb']} | {s['any_fb']/t*100:.1f}% |",
        "",
        f"- Avg strike distance from ATM: CE `{s['avg_ce_dist']:.0f}` pts, "
        f"PE `{s['avg_pe_dist']:.0f}` pts",
        "",
    ]

    by_year: Dict[str, List[DayResult]] = {}
    for r in rows:
        if r.status == "TRADED":
            by_year.setdefault(r.entry_date[:4], []).append(r)
    lines += ["## Year by year", "",
              "Strike distance is the check that the premium band is doing its job: a "
              "Rs 7.50 option sits further from spot as the index level and volatility "
              "rise, so these numbers should drift upward, not stay flat.",
              "",
              "| Year | Days | Net P/L | Win % | Avg premium (pts) | Avg CE dist | Avg PE dist | Fallback days |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for y in sorted(by_year):
        v = by_year[y]
        nets = [float(r.net_pnl) for r in v]
        w = sum(1 for x in nets if x > 0)
        prem = sum(float(r.premium_pts) for r in v) / len(v)
        ced = sum(float(r.ce_dist_pts) for r in v) / len(v)
        ped = sum(float(r.pe_dist_pts) for r in v) / len(v)
        fb = sum(1 for r in v if "no" in (r.ce_in_band, r.pe_in_band))
        lines.append(f"| {y} | {len(v)} | Rs {sum(nets):,.0f} | {w/len(v)*100:.1f}% | "
                     f"{prem:.2f} | {ced:.0f} | {ped:.0f} | {fb} |")

    by_wd: Dict[str, List[float]] = {}
    for r in rows:
        if r.status == "TRADED":
            by_wd.setdefault(r.day_of_week, []).append(float(r.net_pnl))
    lines += ["", "## Expiry weekday", "",
              "NIFTY weekly expiry ran Thursday to 2025-08-28 and Tuesday from "
              "2025-09-02; Monday and Wednesday rows are holiday shifts to the previous "
              "session. Expiry dates are read from the options folder names, so every "
              "transition is picked up from the data rather than hardcoded.",
              "",
              "| Weekday | Days | Net P/L |", "|---|---:|---:|"]
    for wd in sorted(by_wd, key=lambda k: WEEKDAY_NAMES.index(k)):
        lines.append(f"| {wd} | {len(by_wd[wd])} | Rs {sum(by_wd[wd]):,.0f} |")

    skips: Dict[str, int] = {}
    for r in rows:
        if r.status != "TRADED":
            skips[r.skip_reason] = skips.get(r.skip_reason, 0) + 1
    if skips:
        lines += ["", "## Skipped days", "", "| Skip reason | Count |", "|---|---:|"]
        for k in sorted(skips, key=lambda k: -skips[k]):
            lines.append(f"| `{k}` | {skips[k]} |")

    lines += ["", "## Notes", "",
              "- A leg that gaps through its stop fills at the bar open; a leg that only "
              "trades through it fills at the stop price. Neither reads ahead of the trigger.",
              "- Entry price is the open of the exact "
              f"`{args.entry_time}` bar. A strike with no bar at that minute is not a "
              "candidate — no stale quote is ever used.",
              "- **Fills are assumed.** These are the cheapest contracts in the chain and "
              "the least liquid; the real bid-ask at Rs 5–10 is a meaningful fraction of "
              "the premium, so the modelled slippage may still be optimistic.",
              ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
def _num(v: float) -> str:
    return f"{v:g}".replace(".", "p")


def output_tag(args: argparse.Namespace) -> str:
    tag = f"sl{int(round(args.sl_factor * 100))}"
    tag += f"_prem{_num(args.min_premium)}-{_num(args.max_premium)}"
    tag += f"_lots{args.lots}"
    tag += "_e" + args.entry_time.replace(":", "")
    if args.slippage_per_order == 0:
        tag += "_slip0"
    return tag


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[3]
    p = argparse.ArgumentParser(
        description="Expiry-day short strangle with premium-band strike selection.")
    p.add_argument("--spot-file", type=Path,
                   default=repo_root / "nifty" / "NIFTY50_INDEX_5m_last_7y.csv")
    p.add_argument("--options-dir", type=Path,
                   default=repo_root / "NiftyOptions_2020_2026" / "Options")
    p.add_argument("--results-dir", type=Path,
                   default=repo_root / "backtesting" / "results" / "expiry-day-short-premium")
    p.add_argument("--entry-time", default="10:00")
    p.add_argument("--exit-time", default="15:20")
    p.add_argument("--sl-factor", type=float, default=2.0,
                   help="Leg is bought back at this multiple of its entry price.")
    p.add_argument("--min-premium", type=float, default=5.0)
    p.add_argument("--max-premium", type=float, default=10.0)
    p.add_argument("--lots", type=int, default=1)
    p.add_argument("--max-search-strikes", type=int, default=60,
                   help="Strikes either side of ATM to search for a priced contract.")
    p.add_argument("--brokerage-per-order", type=float, default=25.0)
    p.add_argument("--slippage-per-order", type=float, default=0.50)
    p.add_argument("--start-date", default="2020-01-01")
    p.add_argument("--end-date", default="2026-12-31")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.min_premium > args.max_premium:
        raise SystemExit("--min-premium must not exceed --max-premium")
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
    rows = run_days(expiry_days, spot_open, args, cache, logger)
    s = stats_for(rows)
    slip = slippage_rs(rows, args.slippage_per_order)
    prem = s["premium_rs"]
    print(f"  traded={s['traded']} skipped={s['skipped']} "
          f"net={s['net']:,.0f} maxdd={s['max_dd']:,.0f} win={s['win_rate']:.1f}%")
    print(f"  premium collected={prem:,.0f} costs={s['brokerage'] + slip:,.0f} "
          f"({(s['brokerage'] + slip) / prem * 100 if prem else 0:.1f}% of premium) "
          f"fallback days={s['any_fb']}")

    write_daywise_csv(rows, args.results_dir / f"{BASE_FILENAME}_{tag}_daywise.csv")
    summary = args.results_dir / f"{BASE_FILENAME}_{tag}_summary.md"
    write_summary(rows, args, summary, expiry_days[0], expiry_days[-1])
    print(f"Summary: {summary}")


if __name__ == "__main__":
    main()
