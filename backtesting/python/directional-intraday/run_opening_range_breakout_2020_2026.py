#!/usr/bin/env python3
"""
Opening Range Breakout — NIFTY 2020-2026.

Spec: strategies/directional/opening-range-breakout.md

  RANGE     The high and low of the first --or-minutes of the session. Only
            bars FULLY INSIDE the window count: on 5-minute bars a 30-minute
            range ends with the bar stamped 09:40, because that bar covers
            09:40-09:45. Taking the 09:45 bar too would put five minutes of the
            future inside the range.

  ENTRY     `close` mode: the first bar that CLOSES beyond the range. Entry is
            the open of the NEXT bar - the close is only known once the bar has
            ended.
            `touch` mode: price trades through the level. A resting stop order
            fills at the level itself, so the spot entry is the level; the
            option leg cannot be filled there and enters on the next bar.

            Direction is whichever side breaks FIRST in time order. Scanning
            the session to see which way it eventually went is the fastest way
            to build a strategy that cannot be traded.

  STOP      The opposite end of the range.
  TARGET    --target-r x the range width.
  EXIT      15:20. One trade per session; after a stop-out the day is done.

  FILTERS   --min-range-pts / --max-range-pts. The stop IS the range width, so
            a 25-point range risks 25 points to make 37 while costs alone are
            ~2 points round trip on spot and far more in option terms.

TWO P/L COLUMNS - SPOT (the signal's raw edge as a futures-equivalent) and
OPTION (the same signal bought as an ATM CE/PE of the nearest weekly). They
answer different questions. The option column's benchmark is not zero: a random
ATM option buyer loses about Rs 119.5 per trade per lot over this sample
(results/heads-tails/, best of 28 grid cells). A signal only has to pay for the
theta a coin flip cannot.

Stops and targets are ALWAYS defined on spot.

Output: backtesting/results/directional-intraday/
"""
from __future__ import annotations

import argparse
import csv
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

BASE_FILENAME = "opening_range_breakout_2020_2026"
IST_SUFFIX = "+05:30"
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday"]
STRIKE_STEP = 50
SESSION_OPEN = "09:15"
BAR_MINUTES = 5

# A normal NIFTY session is 75 five-minute bars (09:15..15:25). Muhurat evening
# sessions and the occasional special Saturday are far shorter; they must not be
# traded. Measured: 1,595 of 1,606 sessions are exactly 75 bars.
SESSION_MIN_BARS = 70


@dataclass
class PriceRow:
    timestamp: str
    open_value: float
    high_value: float
    low_value: float
    close_value: float


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


@dataclass
class DayResult:
    entry_date: str
    day_of_week: str
    status: str
    skip_reason: str
    or_high: str
    or_low: str
    range_pts: str
    break_side: str
    direction: str
    entry_ts: str
    entry_spot: str
    stop_spot: str
    target_spot: str
    exit_ts: str
    exit_spot: str
    exit_reason: str
    spot_points: str
    lot_size: str
    qty: str
    spot_gross: str
    spot_net: str
    expiry_date: str
    dte: str
    option_status: str
    option_side: str
    option_strike: str
    option_entry_ts: str
    option_entry: str
    option_exit: str
    option_points: str
    option_gross: str
    option_net: str
    remarks: str


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def fmt(v: float) -> str:
    return f"{v:.2f}"


def build_ts(day: str, time_text: str) -> str:
    h, m = time_text.split(":")
    return f"{day}T{h}:{m}:00{IST_SUFFIX}"


def ts_time(timestamp: str) -> str:
    return timestamp[11:16]


def expiry_suffix(expiry_date: str) -> str:
    return datetime.datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%d_%b_%y").upper()


def round_to_strike(price: float) -> int:
    return int(round(price / STRIKE_STEP) * STRIKE_STEP)


def lot_size_for(expiry_date: str) -> int:
    """Lot size active for this contract, keyed to its EXPIRY date."""
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
def load_spot_data(spot_file: Path) -> Tuple[List[str], Dict[str, Dict[str, PriceRow]],
                                             Dict[str, List[str]]]:
    """(trading_days, rows_by_day[day][ts], timestamps_by_day[day] -> ordered)."""
    trading_days: List[str] = []
    rows_by_day: Dict[str, Dict[str, PriceRow]] = {}
    timestamps_by_day: Dict[str, List[str]] = {}

    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            day = ts[:10]
            if day not in rows_by_day:
                rows_by_day[day] = {}
                timestamps_by_day[day] = []
                trading_days.append(day)
            rows_by_day[day][ts] = PriceRow(
                timestamp=ts,
                open_value=float(row["open"]),
                high_value=float(row["high"]),
                low_value=float(row["low"]),
                close_value=float(row["close"]),
            )
            timestamps_by_day[day].append(ts)

    for day in timestamps_by_day:
        timestamps_by_day[day].sort()
    trading_days.sort()
    return trading_days, rows_by_day, timestamps_by_day


def load_expiry_folders(options_dir: Path) -> List[str]:
    return sorted(p.name for p in options_dir.iterdir() if p.is_dir())


def first_expiry_on_or_after(expiries: List[str], day: str) -> Optional[str]:
    for e in expiries:
        if e >= day:
            return e
    return None


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
            rows[ts] = PriceRow(
                timestamp=ts,
                open_value=float(row["open"]),
                high_value=float(row["high"]),
                low_value=float(row["low"]),
                close_value=float(row["close"]),
            )
    data = ContractData(path=path, rows_by_timestamp=rows)
    cache[path] = data
    return data


def is_normal_session(timestamps: List[str]) -> bool:
    return len(timestamps) >= SESSION_MIN_BARS and ts_time(timestamps[0]) == SESSION_OPEN


# --------------------------------------------------------------------------- #
# the opening range
# --------------------------------------------------------------------------- #
def opening_range_bars(day_ts: List[str], or_minutes: int) -> List[str]:
    """Bars FULLY inside the opening window.

    A bar stamped T covers [T, T+5min), so it is inside a window ending at
    09:15+or_minutes only if T+5min <= that boundary. For a 30-minute range the
    last qualifying bar is stamped 09:40. Including the 09:45 bar would put
    five minutes of the future into the range - lookahead trap #1 in the spec.
    """
    end_minutes = 9 * 60 + 15 + or_minutes
    out = []
    for ts in day_ts:
        h, m = int(ts[11:13]), int(ts[14:16])
        if (h * 60 + m) + BAR_MINUTES <= end_minutes:
            out.append(ts)
    return out


def find_breakout(
    rows: Dict[str, PriceRow], day_ts: List[str], range_bars: List[str],
    or_high: float, or_low: float, entry_mode: str, cutoff_ts: str,
) -> Optional[Tuple[str, str, float, bool]]:
    """First break of either side, in time order.

    Returns (break_side, entry_ts, entry_price, entry_is_intrabar) or None.

    Direction comes from whichever side breaks first as the session actually
    unfolded. Deciding it by looking at where the day ended up is fatal and is
    the easiest mistake to make here.

    `close`: the bar must close beyond the level, so entry is the NEXT bar's
    open. `touch`: a resting stop order fills at the level itself, in the bar
    that reached it - but the option leg cannot fill there, which the caller
    handles via entry_is_intrabar.
    """
    after = [ts for ts in day_ts if ts > range_bars[-1]]
    for idx, ts in enumerate(after):
        if ts > cutoff_ts:
            return None
        row = rows[ts]
        if entry_mode == "close":
            up = row.close_value > or_high
            down = row.close_value < or_low
            if not (up or down):
                continue
            pos = day_ts.index(ts)
            if pos + 1 >= len(day_ts):
                return None
            nxt = day_ts[pos + 1]
            return ("up" if up else "down"), nxt, rows[nxt].open_value, False
        else:
            # A bar that gaps clean through the level fills at its open.
            if row.open_value > or_high:
                return "up", ts, row.open_value, False
            if row.open_value < or_low:
                return "down", ts, row.open_value, False
            if row.high_value >= or_high:
                return "up", ts, or_high, True
            if row.low_value <= or_low:
                return "down", ts, or_low, True
    return None


# --------------------------------------------------------------------------- #
# leg resolution
# --------------------------------------------------------------------------- #
def resolve_spot_leg(
    rows: Dict[str, PriceRow], day_ts: List[str], entry_ts: str, exit_ts: str,
    entry_price: float, direction: int, stop: float, target: Optional[float],
    skip_entry_bar: bool,
) -> LegOutcome:
    """Walk spot bars from entry to exit.

    direction: +1 long, -1 short.

    The stop is checked before the target within a bar, so a bar containing
    both resolves to the stop - the conservative assumption, and the only one a
    5-minute series can justify.

    `skip_entry_bar` is for a `touch` entry: the position opened partway
    through that bar, so the bar's own high and low include movement from
    before the entry existed and cannot be used to stop it out.
    """
    for ts in day_ts:
        if not (entry_ts <= ts <= exit_ts):
            continue
        if skip_entry_bar and ts == entry_ts:
            continue
        row = rows[ts]
        if direction > 0:
            if row.open_value <= stop:
                return LegOutcome(ts, row.open_value, "gap_sl", row.open_value - entry_price)
            if target is not None and row.open_value >= target:
                return LegOutcome(ts, row.open_value, "gap_target", row.open_value - entry_price)
            if row.low_value <= stop:
                return LegOutcome(ts, stop, "sl", stop - entry_price)
            if target is not None and row.high_value >= target:
                return LegOutcome(ts, target, "target", target - entry_price)
        else:
            if row.open_value >= stop:
                return LegOutcome(ts, row.open_value, "gap_sl", entry_price - row.open_value)
            if target is not None and row.open_value <= target:
                return LegOutcome(ts, row.open_value, "gap_target", entry_price - row.open_value)
            if row.high_value >= stop:
                return LegOutcome(ts, stop, "sl", entry_price - stop)
            if target is not None and row.low_value <= target:
                return LegOutcome(ts, target, "target", entry_price - target)

    exit_row = rows.get(exit_ts)
    if exit_row is not None:
        return LegOutcome(exit_ts, exit_row.open_value,
                          "day_close", direction * (exit_row.open_value - entry_price))
    earlier = [t for t in day_ts if t <= exit_ts]
    if earlier:
        last = earlier[-1]
        px = rows[last].open_value
        return LegOutcome(last, px, "last_bar_before_exit", direction * (px - entry_price))
    return LegOutcome(exit_ts, entry_price, "missing_exit_bar", 0.0)


# Reasons where the trigger happened INSIDE the bar rather than at its open.
# The spot leg fills at the level - a resting order would have been taken there
# - but nothing else can be filled at that bar's open, which is a price from
# before the trigger existed. Lookahead bug #1 in the audit.
INTRABAR_REASONS = {"sl", "target"}


def next_bar(ts: str, day_ts: List[str]) -> str:
    try:
        idx = day_ts.index(ts)
    except ValueError:
        return ts
    return day_ts[idx + 1] if idx + 1 < len(day_ts) else ts


def option_exit_timestamp(spot_exit_ts: str, reason: str, day_ts: List[str]) -> str:
    """The first minute at which the option can be sold after the spot trigger."""
    if reason not in INTRABAR_REASONS:
        return spot_exit_ts
    return next_bar(spot_exit_ts, day_ts)


def price_option(
    options_dir: Path, expiry: str, strike: int, side: str, entry_ts: str,
    exit_ts: str, cache: Dict[Path, Optional[ContractData]],
) -> Tuple[str, Optional[float], Optional[float]]:
    """(status, entry_open, exit_open) for a long option held entry -> exit."""
    if exit_ts < entry_ts:
        return "exit_before_entry", None, None
    suffix = expiry_suffix(expiry)
    path = options_dir / expiry / f"NIFTY_{strike}_{side}_{suffix}.csv"
    contract = load_contract(path, cache)
    if contract is None:
        return "missing_file", None, None
    entry_row = contract.rows_by_timestamp.get(entry_ts)
    if entry_row is None or entry_row.open_value <= 0:
        return "missing_entry_bar", None, None
    exit_row = contract.rows_by_timestamp.get(exit_ts)
    if exit_row is None:
        earlier = [t for t in contract.rows_by_timestamp if t <= exit_ts]
        if not earlier:
            return "missing_exit_bar", None, None
        exit_row = contract.rows_by_timestamp[max(earlier)]
    return "TRADED", entry_row.open_value, exit_row.open_value


def blank_row(day: str, day_name: str, **over) -> DayResult:
    base = {f: "" for f in DayResult.__dataclass_fields__}
    base.update(entry_date=day, day_of_week=day_name, status="SKIPPED")
    base.update(over)
    return DayResult(**base)


# --------------------------------------------------------------------------- #
# strategy
# --------------------------------------------------------------------------- #
def run_days(
    trading_days: List[str], rows_by_day: Dict[str, Dict[str, PriceRow]],
    timestamps_by_day: Dict[str, List[str]], expiries: List[str],
    args: argparse.Namespace, cache: Dict[Path, Optional[ContractData]],
    logger: logging.Logger,
) -> List[DayResult]:
    results: List[DayResult] = []
    brokerage = args.brokerage_per_order * 2

    for day in trading_days:
        if not (args.start_date <= day <= args.end_date):
            continue
        day_name = WEEKDAY_NAMES[datetime.date.fromisoformat(day).weekday()]
        day_ts = timestamps_by_day[day]

        if not is_normal_session(day_ts):
            results.append(blank_row(day, day_name, skip_reason="anomalous_session",
                                     remarks=f"{len(day_ts)} bars, opens {ts_time(day_ts[0])}"))
            continue

        range_bars = opening_range_bars(day_ts, args.or_minutes)
        if not range_bars:
            results.append(blank_row(day, day_name, skip_reason="no_range_bars"))
            continue
        or_high = max(rows_by_day[day][t].high_value for t in range_bars)
        or_low = min(rows_by_day[day][t].low_value for t in range_bars)
        width = or_high - or_low
        common = dict(or_high=fmt(or_high), or_low=fmt(or_low), range_pts=fmt(width))

        if width < args.min_range_pts:
            results.append(blank_row(day, day_name, skip_reason="range_too_narrow", **common))
            continue
        if args.max_range_pts > 0 and width > args.max_range_pts:
            results.append(blank_row(day, day_name, skip_reason="range_too_wide", **common))
            continue

        cutoff_ts = build_ts(day, args.entry_cutoff)
        exit_ts = build_ts(day, args.exit_time)
        found = find_breakout(rows_by_day[day], day_ts, range_bars,
                              or_high, or_low, args.entry_mode, cutoff_ts)
        if found is None:
            results.append(blank_row(day, day_name, skip_reason="no_breakout", **common))
            continue
        break_side, entry_ts, entry_price, intrabar_entry = found

        direction = 1 if break_side == "up" else -1
        stop = or_low if direction > 0 else or_high
        target = (entry_price + args.target_r * width if direction > 0
                  else entry_price - args.target_r * width)
        if args.target_r <= 0:
            target = None

        spot_out = resolve_spot_leg(rows_by_day[day], day_ts, entry_ts, exit_ts,
                                    entry_price, direction, stop, target,
                                    skip_entry_bar=intrabar_entry)

        expiry = first_expiry_on_or_after(expiries, day)
        lot = lot_size_for(expiry) if expiry else 75
        dte = (str((datetime.date.fromisoformat(expiry)
                    - datetime.date.fromisoformat(day)).days) if expiry else "")
        qty = lot * args.lots

        spot_pts_net = spot_out.points - 2 * args.slippage_per_order
        spot_gross = spot_pts_net * qty
        spot_net = spot_gross - brokerage

        # ---- option leg -------------------------------------------------- #
        # A `touch` entry happened partway through its bar, so the option can
        # only be bought on the next one. The strike comes from spot at the
        # last bar that CLOSED before the order - never the entry bar's own
        # close, which is not known when the order is placed.
        opt_status, opt_side, opt_strike = "no_expiry", "", ""
        opt_entry_ts = opt_entry = opt_exit = opt_pts = opt_gross = opt_net = ""
        if expiry is not None:
            o_entry_ts = next_bar(entry_ts, day_ts) if intrabar_entry else entry_ts
            idx = day_ts.index(o_entry_ts)
            signal_row = rows_by_day[day][day_ts[idx - 1]] if idx > 0 else rows_by_day[day][day_ts[0]]
            strike = round_to_strike(signal_row.close_value)
            side = "CE" if direction > 0 else "PE"
            o_exit_ts = option_exit_timestamp(spot_out.exit_timestamp,
                                              spot_out.exit_reason, day_ts)
            status, oe, ox = price_option(args.options_dir, expiry, strike, side,
                                          o_entry_ts, o_exit_ts, cache)
            opt_status, opt_side, opt_strike = status, side, str(strike)
            opt_entry_ts = o_entry_ts
            if status == "TRADED" and oe is not None and ox is not None:
                raw = ox - oe                          # always a LONG option
                g = (raw - 2 * args.slippage_per_order) * qty
                opt_entry, opt_exit = fmt(oe), fmt(ox)
                opt_pts, opt_gross = fmt(raw), fmt(g)
                opt_net = fmt(g - brokerage)

        results.append(DayResult(
            entry_date=day, day_of_week=day_name, status="TRADED", skip_reason="",
            or_high=fmt(or_high), or_low=fmt(or_low), range_pts=fmt(width),
            break_side=break_side, direction="long" if direction > 0 else "short",
            entry_ts=entry_ts, entry_spot=fmt(entry_price), stop_spot=fmt(stop),
            target_spot=fmt(target) if target is not None else "",
            exit_ts=spot_out.exit_timestamp, exit_spot=fmt(spot_out.exit_price),
            exit_reason=spot_out.exit_reason, spot_points=fmt(spot_out.points),
            lot_size=str(lot), qty=str(qty),
            spot_gross=fmt(spot_gross), spot_net=fmt(spot_net),
            expiry_date=expiry or "", dte=dte,
            option_status=opt_status, option_side=opt_side, option_strike=opt_strike,
            option_entry_ts=opt_entry_ts, option_entry=opt_entry, option_exit=opt_exit,
            option_points=opt_pts, option_gross=opt_gross, option_net=opt_net,
            remarks="",
        ))
        logger.info("TRADED date=%s range=%.2f side=%s entry=%s exit=%s reason=%s "
                    "spot_net=%.2f opt=%s",
                    day, width, break_side, ts_time(entry_ts),
                    ts_time(spot_out.exit_timestamp), spot_out.exit_reason,
                    spot_net, opt_net or opt_status)
    return results


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #
def stats_for(rows: List[DayResult], column: str) -> dict:
    field = "spot_net" if column == "spot" else "option_net"
    traded = [r for r in rows if r.status == "TRADED" and getattr(r, field) != ""]
    nets = [float(getattr(r, field)) for r in traded]
    wins = [n for n in nets if n > 0]
    losses = [n for n in nets if n < 0]
    return {
        "traded": len(traded), "net": sum(nets),
        "wins": len(wins), "losses": len(losses),
        "win_rate": (len(wins) / len(traded) * 100) if traded else 0.0,
        "profit_factor": (sum(wins) / abs(sum(losses))) if losses else float("inf"),
        "max_dd": max_drawdown(nets),
        "best": max(nets) if nets else 0.0,
        "worst": min(nets) if nets else 0.0,
        "avg": (sum(nets) / len(nets)) if nets else 0.0,
    }


def pf_text(pf: float) -> str:
    return "inf" if pf == float("inf") else f"{pf:.2f}"


def write_daywise_csv(rows: List[DayResult], path: Path) -> None:
    fields = list(DayResult.__dataclass_fields__.keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({f: getattr(r, f) for f in fields})


def bucket_table(rows: List[DayResult], lines: List[str], key, label: str,
                 buckets: List[Tuple[float, float]]) -> None:
    lines += [f"| {label} | Trades | Spot net | Spot win% | Option net |",
              "|---|---:|---:|---:|---:|"]
    for lo, hi in buckets:
        sub = [r for r in rows if lo <= key(r) < hi]
        if not sub:
            continue
        sn = [float(r.spot_net) for r in sub]
        on = sum(float(r.option_net) for r in sub if r.option_net)
        w = sum(1 for x in sn if x > 0)
        name = f"{lo:g}–{hi:g}" if hi < 100_000 else f"{lo:g}+"
        lines.append(f"| {name} | {len(sub)} | Rs {sum(sn):,.0f} | "
                     f"{w/len(sub)*100:.1f}% | Rs {on:,.0f} |")
    lines.append("")


def write_summary(rows: List[DayResult], args: argparse.Namespace, path: Path,
                  first_day: str, last_day: str) -> None:
    traded = [r for r in rows if r.status == "TRADED"]
    s_spot, s_opt = stats_for(traded, "spot"), stats_for(traded, "option")
    capital = max((float(r.qty) * float(r.entry_spot) * 0.10
                   for r in traded if r.entry_spot), default=0.0)
    lines = [
        "# Opening Range Breakout (NIFTY 2020-2026)",
        "",
        "Spec: [`strategies/directional/opening-range-breakout.md`]"
        "(../../../strategies/directional/opening-range-breakout.md)",
        "",
        "## Strategy",
        "",
        f"- Opening range: the first `{args.or_minutes}` minutes. On 5-minute bars that "
        f"is every bar fully inside the window — the last one is stamped "
        f"`{9*60+15+args.or_minutes-BAR_MINUTES>=0 and f'{(9*60+15+args.or_minutes-BAR_MINUTES)//60:02d}:{(9*60+15+args.or_minutes-BAR_MINUTES)%60:02d}'}`, "
        "not the one on the boundary",
        f"- Entry mode `{args.entry_mode}`: "
        + ("a bar must CLOSE beyond the range; entry is the next bar's open"
           if args.entry_mode == "close" else
           "a resting stop fills at the level itself when price trades through it"),
        "- Direction is whichever side breaks **first in time order**",
        "- Stop: the opposite end of the range",
        f"- Target: `{args.target_r:g}x` the range width"
        + (" (none — time exit only)" if args.target_r <= 0 else ""),
        f"- No entry after `{args.entry_cutoff}`; exit `{args.exit_time}`",
        f"- Range filters: min `{args.min_range_pts:g}` pts"
        + (f", max `{args.max_range_pts:g}` pts" if args.max_range_pts > 0 else ", no max"),
        "- One trade per session, no re-entry after a stop-out",
        f"- Size: {args.lots} lot(s), expiry-aware (75/50/25/75/65)",
        f"- Costs both columns: Rs {args.brokerage_per_order:.0f}/order + "
        f"{args.slippage_per_order:.2f} pt/order",
        f"- Period: `{first_day}` to `{last_day}`",
        "",
        "## Results",
        "",
        f"- Trades: `{s_spot['traded']}` (option priced on `{s_opt['traded']}`)",
        "",
        "| Column | Net P/L | Win% | PF | Max DD | Best | Worst | Avg/trade |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        f"| **Spot** (futures-equivalent) | Rs {s_spot['net']:,.0f} | {s_spot['win_rate']:.1f}% | "
        f"{pf_text(s_spot['profit_factor'])} | Rs {s_spot['max_dd']:,.0f} | "
        f"Rs {s_spot['best']:,.0f} | Rs {s_spot['worst']:,.0f} | Rs {s_spot['avg']:,.0f} |",
        f"| **Option** (long ATM) | Rs {s_opt['net']:,.0f} | {s_opt['win_rate']:.1f}% | "
        f"{pf_text(s_opt['profit_factor'])} | Rs {s_opt['max_dd']:,.0f} | "
        f"Rs {s_opt['best']:,.0f} | Rs {s_opt['worst']:,.0f} | Rs {s_opt['avg']:,.0f} |",
        "",
        f"- Spot CAGR on ~Rs {capital:,.0f} modelled futures margin: "
        f"`{compute_cagr(s_spot['net'], capital, first_day, last_day):.2f}%`",
        f"- Option, per trade per lot: **Rs {s_opt['avg']:,.1f}** against a random "
        "ATM buyer's **Rs −119.5** ([heads-tails long grid](../heads-tails/), best of "
        "28 cells)",
        "",
    ]

    by_reason: Dict[str, int] = {}
    for r in traded:
        by_reason[r.exit_reason] = by_reason.get(r.exit_reason, 0) + 1
    lines += ["| Exit reason | Trades |", "|---|---:|"]
    for k in sorted(by_reason, key=lambda k: -by_reason[k]):
        lines.append(f"| `{k}` | {by_reason[k]} |")
    lines.append("")

    lines += ["### By break direction", "",
              "A source claims shorts produced 75% of ORB profit despite a bull market. "
              "This is where that gets checked.", "",
              "| Side | Trades | Spot net | Spot win% | Option net |", "|---|---:|---:|---:|---:|"]
    for side in ("up", "down"):
        sub = [r for r in traded if r.break_side == side]
        if not sub:
            continue
        sn = [float(r.spot_net) for r in sub]
        on = sum(float(r.option_net) for r in sub if r.option_net)
        w = sum(1 for x in sn if x > 0)
        lines.append(f"| {side} | {len(sub)} | Rs {sum(sn):,.0f} | "
                     f"{w/len(sub)*100:.1f}% | Rs {on:,.0f} |")
    lines.append("")

    lines += ["### By opening-range width", "",
              "The stop IS the range width, so a narrow range risks little but is also "
              "the setup most easily overwhelmed by costs and noise.", ""]
    bucket_table(traded, lines, lambda r: float(r.range_pts), "Range (pts)",
                 [(0, 40), (40, 70), (70, 100), (100, 150), (150, 100_000)])

    lines += ["### By year", "", "| Year | Trades | Spot net | Spot win% | Option net |",
              "|---|---:|---:|---:|---:|"]
    by_year: Dict[str, List[DayResult]] = {}
    for r in traded:
        by_year.setdefault(r.entry_date[:4], []).append(r)
    for y in sorted(by_year):
        v = by_year[y]
        sn = [float(r.spot_net) for r in v]
        on = sum(float(r.option_net) for r in v if r.option_net)
        w = sum(1 for x in sn if x > 0)
        lines.append(f"| {y} | {len(v)} | Rs {sum(sn):,.0f} | {w/len(v)*100:.1f}% | Rs {on:,.0f} |")
    lines.append("")

    lines += ["### By days to expiry", "",
              "A fifth of sessions are expiry days, so the nearest weekly option is "
              "0-DTE on many trades.", "",
              "| DTE | Trades | Spot net | Option net |", "|---|---:|---:|---:|"]
    by_dte: Dict[str, List[DayResult]] = {}
    for r in traded:
        key = "0 (expiry day)" if r.dte == "0" else ("1-3" if r.dte in ("1", "2", "3") else "4+")
        by_dte.setdefault(key, []).append(r)
    for k in sorted(by_dte):
        v = by_dte[k]
        sn = sum(float(r.spot_net) for r in v)
        on = sum(float(r.option_net) for r in v if r.option_net)
        lines.append(f"| {k} | {len(v)} | Rs {sn:,.0f} | Rs {on:,.0f} |")
    lines.append("")

    skips: Dict[str, int] = {}
    for r in rows:
        if r.status != "TRADED":
            skips[r.skip_reason] = skips.get(r.skip_reason, 0) + 1
    if skips:
        lines += ["## Sessions not traded", "", "| Reason | Sessions |", "|---|---:|"]
        for k in sorted(skips, key=lambda k: -skips[k]):
            lines.append(f"| `{k}` | {skips[k]} |")
        lines.append("")

    lines += [
        "## Notes", "",
        "- The opening range uses only bars fully inside the window. A bar stamped `T` "
        "covers `[T, T+5min)`, so a 30-minute range ends at the bar stamped 09:40.",
        "- In `close` mode entry is the next bar's open; the confirming close is not "
        "knowable until the bar ends.",
        "- In `touch` mode the spot fills at the level (a resting order would have been "
        "taken there) but the option enters on the next bar, and the entry bar's own "
        "high/low cannot stop the trade out — that movement partly precedes the entry.",
        "- A bar containing both stop and target resolves to the **stop**.",
        "- Direction is the first break in time order, never the day's eventual outcome.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
def output_tag(args: argparse.Namespace) -> str:
    tag = f"or{args.or_minutes}_{args.entry_mode}_r{args.target_r:g}"
    tag += f"_min{args.min_range_pts:g}"
    if args.max_range_pts > 0:
        tag += f"_max{args.max_range_pts:g}"
    tag += f"_lots{args.lots}"
    if args.slippage_per_order == 0:
        tag += "_slip0"
    return tag


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[3]
    p = argparse.ArgumentParser(description="Opening range breakout on NIFTY.")
    p.add_argument("--spot-file", type=Path,
                   default=repo_root / "nifty" / "NIFTY50_INDEX_5m_last_7y.csv")
    p.add_argument("--options-dir", type=Path,
                   default=repo_root / "NiftyOptions_2020_2026" / "Options")
    p.add_argument("--results-dir", type=Path,
                   default=repo_root / "backtesting" / "results" / "directional-intraday")
    p.add_argument("--or-minutes", type=int, default=30, choices=[15, 30, 45, 60])
    p.add_argument("--entry-mode", choices=["close", "touch"], default="close")
    p.add_argument("--target-r", type=float, default=1.5,
                   help="Target as a multiple of the range width. 0 = time exit only.")
    p.add_argument("--entry-cutoff", default="14:00")
    p.add_argument("--exit-time", default="15:20")
    p.add_argument("--min-range-pts", type=float, default=0.0)
    p.add_argument("--max-range-pts", type=float, default=0.0, help="0 = no maximum.")
    p.add_argument("--lots", type=int, default=1)
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

    trading_days, rows_by_day, timestamps_by_day = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    in_range = [d for d in trading_days if args.start_date <= d <= args.end_date]
    if not in_range:
        raise SystemExit("No sessions in range — check --spot-file and dates.")
    print(f"sessions in range: {len(in_range)} ({in_range[0]} .. {in_range[-1]})")

    cache: Dict[Path, Optional[ContractData]] = {}
    rows = run_days(trading_days, rows_by_day, timestamps_by_day, expiries,
                    args, cache, logger)
    traded = [r for r in rows if r.status == "TRADED"]
    ss, so = stats_for(traded, "spot"), stats_for(traded, "option")
    print(f"  trades={ss['traded']:>4}  spot_net={ss['net']:>11,.0f} "
          f"pf={pf_text(ss['profit_factor']):>5} win={ss['win_rate']:.1f}%   "
          f"opt_net={so['net']:>11,.0f} pf={pf_text(so['profit_factor']):>5} "
          f"per-trade={so['avg']:,.0f}")

    write_daywise_csv(rows, args.results_dir / f"{BASE_FILENAME}_{tag}_daywise.csv")
    summary = args.results_dir / f"{BASE_FILENAME}_{tag}_summary.md"
    write_summary(rows, args, summary, in_range[0], in_range[-1])
    print(f"Summary: {summary}")


if __name__ == "__main__":
    main()
