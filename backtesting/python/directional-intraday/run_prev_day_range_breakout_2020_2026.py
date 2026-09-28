#!/usr/bin/env python3
"""
Previous-Day High / Low Breakout — NIFTY 2020-2026.

Spec: strategies/directional/previous-day-range-breakout.md

  LEVELS    PDH / PDL - the high and low of the previous NORMAL session. Not
            the previous calendar day: weekends, holidays and the nine
            anomalous sessions (Muhurat evenings, special Saturdays) are all
            stepped over.

  ENTRY     The first bar that CLOSES beyond a level. Entry is the open of the
            NEXT bar. Direction is whichever side breaks FIRST in time order.

  GAP       The crux of this strategy: the level is known before the session
            starts, so an open beyond it means the level is already broken at
            09:15 and there is nothing left to break.
              skip      - no trade (strictest, and the cleanest test)
              immediate - treat the open itself as the break, enter at 09:20
              retest    - wait for price to come back to the level and HOLD it
                          (a bar that touches it from the far side and closes
                          back beyond). No trade if it never retests.

  STOP      --stop-mode: `atr` (--stop-atr-mult x ATR-14 on 5m bars),
            `opposite` (the other level), or `fixed` points.
            `opposite` deserves a warning: PDH-PDL can be 300 points, and
            risking 300 to make 450 is not the same strategy as risking 40,
            even though the rules read identically.

  TARGET    --target-r x the stop distance.  EXIT 15:20. One trade per session.

ATR is written here because nothing in this repo computes one - grep the whole
of backtesting/ for true_range and it returns nothing.

TWO P/L COLUMNS - SPOT (the raw signal as a futures-equivalent) and OPTION (the
same signal bought as an ATM CE/PE of the nearest weekly). The option column's
benchmark is not zero: a random ATM buyer loses about Rs 119.5 per trade per lot
over this sample (results/heads-tails/).

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

BASE_FILENAME = "prev_day_range_breakout_2020_2026"
IST_SUFFIX = "+05:30"
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday"]
STRIKE_STEP = 50
SESSION_OPEN = "09:15"
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
    prev_date: str
    pdh: str
    pdl: str
    prev_range: str
    day_open: str
    open_state: str
    break_side: str
    direction: str
    atr: str
    entry_ts: str
    entry_spot: str
    stop_spot: str
    target_spot: str
    risk_pts: str
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
@dataclass
class SpotData:
    trading_days: List[str]
    rows_by_day: Dict[str, Dict[str, PriceRow]]
    timestamps_by_day: Dict[str, List[str]]
    ordered: List[PriceRow]                 # every bar, in time order
    index_by_ts: Dict[str, int]             # timestamp -> position in `ordered`


def load_spot_data(spot_file: Path) -> SpotData:
    """Both shapes at once.

    The per-session index drives the session loop; the flat ordered list with
    its position map is what makes a causal ATR possible across session
    boundaries. Nothing in this repo returned both before.
    """
    trading_days: List[str] = []
    rows_by_day: Dict[str, Dict[str, PriceRow]] = {}
    timestamps_by_day: Dict[str, List[str]] = {}
    rows: List[PriceRow] = []

    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            day = ts[:10]
            if day not in rows_by_day:
                rows_by_day[day] = {}
                timestamps_by_day[day] = []
                trading_days.append(day)
            pr = PriceRow(
                timestamp=ts,
                open_value=float(row["open"]),
                high_value=float(row["high"]),
                low_value=float(row["low"]),
                close_value=float(row["close"]),
            )
            rows_by_day[day][ts] = pr
            timestamps_by_day[day].append(ts)
            rows.append(pr)

    for day in timestamps_by_day:
        timestamps_by_day[day].sort()
    trading_days.sort()
    rows.sort(key=lambda r: r.timestamp)
    return SpotData(trading_days, rows_by_day, timestamps_by_day, rows,
                    {r.timestamp: i for i, r in enumerate(rows)})


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
            rows[ts] = PriceRow(ts, float(row["open"]), float(row["high"]),
                                float(row["low"]), float(row["close"]))
    data = ContractData(path=path, rows_by_timestamp=rows)
    cache[path] = data
    return data


def is_normal_session(timestamps: List[str]) -> bool:
    return len(timestamps) >= SESSION_MIN_BARS and ts_time(timestamps[0]) == SESSION_OPEN


def previous_normal_session(trading_days: List[str],
                            timestamps_by_day: Dict[str, List[str]],
                            day_index: int) -> Optional[str]:
    """The most recent NORMAL session strictly before day_index."""
    for i in range(day_index - 1, -1, -1):
        prev = trading_days[i]
        if is_normal_session(timestamps_by_day[prev]):
            return prev
    return None


# --------------------------------------------------------------------------- #
# ATR — written here because the repo has none
# --------------------------------------------------------------------------- #
def true_range(row: PriceRow, prev_close: Optional[float]) -> float:
    """max(h-l, |h-prev_close|, |l-prev_close|).

    Falls back to the bar's own range when there is no previous close, which
    happens only on the very first bar of the series.
    """
    if prev_close is None:
        return row.high_value - row.low_value
    return max(row.high_value - row.low_value,
               abs(row.high_value - prev_close),
               abs(row.low_value - prev_close))


def atr_at(spot: SpotData, timestamp: str, period: int) -> Optional[float]:
    """ATR over the `period` bars ending at `timestamp` — CAUSAL.

    The caller must pass a bar that has already CLOSED before the moment of the
    decision. A bar stamped T closes at T+5min, so passing the entry bar itself
    would read five minutes of the future.
    """
    idx = spot.index_by_ts.get(timestamp)
    if idx is None or idx + 1 < period:
        return None
    total = 0.0
    for i in range(idx - period + 1, idx + 1):
        prev_close = spot.ordered[i - 1].close_value if i > 0 else None
        total += true_range(spot.ordered[i], prev_close)
    return total / period


# --------------------------------------------------------------------------- #
# signal
# --------------------------------------------------------------------------- #
def classify_open(day_open: float, pdh: float, pdl: float) -> str:
    if day_open > pdh:
        return "above_pdh"
    if day_open < pdl:
        return "below_pdl"
    return "inside"


def find_breakout(
    rows: Dict[str, PriceRow], day_ts: List[str], pdh: float, pdl: float,
    buffer_pts: float, cutoff_ts: str, start_ts: str,
) -> Optional[Tuple[str, str, float]]:
    """First close beyond a level, in time order. Entry is the NEXT bar's open.

    Direction is whichever side breaks first as the session unfolded, never
    where the day eventually ended up.
    """
    up_level, down_level = pdh + buffer_pts, pdl - buffer_pts
    for ts in day_ts:
        if ts < start_ts:
            continue
        if ts > cutoff_ts:
            return None
        row = rows[ts]
        up = row.close_value > up_level
        down = row.close_value < down_level
        if not (up or down):
            continue
        pos = day_ts.index(ts)
        if pos + 1 >= len(day_ts):
            return None
        nxt = day_ts[pos + 1]
        return ("up" if up else "down"), nxt, rows[nxt].open_value
    return None


def find_retest(
    rows: Dict[str, PriceRow], day_ts: List[str], level: float, side: str,
    cutoff_ts: str,
) -> Optional[Tuple[str, float]]:
    """Price returns to a level it gapped past and HOLDS it.

    For a gap above PDH: a bar whose low touches PDH from above and whose close
    is still above it. The hold is only known once that bar has CLOSED, so entry
    is the next bar's open. Deciding at the moment of the touch that it will
    hold is reading the future - the trap the spec names.
    """
    for ts in day_ts:
        if ts > cutoff_ts:
            return None
        row = rows[ts]
        touched = row.low_value <= level if side == "up" else row.high_value >= level
        held = row.close_value > level if side == "up" else row.close_value < level
        if touched and held:
            pos = day_ts.index(ts)
            if pos + 1 >= len(day_ts):
                return None
            nxt = day_ts[pos + 1]
            return nxt, rows[nxt].open_value
    return None


# --------------------------------------------------------------------------- #
# leg resolution
# --------------------------------------------------------------------------- #
def resolve_spot_leg(
    rows: Dict[str, PriceRow], day_ts: List[str], entry_ts: str, exit_ts: str,
    entry_price: float, direction: int, stop: float, target: Optional[float],
) -> LegOutcome:
    """Stop is checked before target within a bar — the conservative ordering."""
    for ts in day_ts:
        if not (entry_ts <= ts <= exit_ts):
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
        return LegOutcome(exit_ts, exit_row.open_value, "day_close",
                          direction * (exit_row.open_value - entry_price))
    earlier = [t for t in day_ts if t <= exit_ts]
    if earlier:
        last = earlier[-1]
        px = rows[last].open_value
        return LegOutcome(last, px, "last_bar_before_exit", direction * (px - entry_price))
    return LegOutcome(exit_ts, entry_price, "missing_exit_bar", 0.0)


INTRABAR_REASONS = {"sl", "target"}


def next_bar(ts: str, day_ts: List[str]) -> str:
    try:
        idx = day_ts.index(ts)
    except ValueError:
        return ts
    return day_ts[idx + 1] if idx + 1 < len(day_ts) else ts


def option_exit_timestamp(spot_exit_ts: str, reason: str, day_ts: List[str]) -> str:
    """An intrabar trigger cannot be sold at that bar's own open."""
    if reason not in INTRABAR_REASONS:
        return spot_exit_ts
    return next_bar(spot_exit_ts, day_ts)


def price_option(
    options_dir: Path, expiry: str, strike: int, side: str, entry_ts: str,
    exit_ts: str, cache: Dict[Path, Optional[ContractData]],
) -> Tuple[str, Optional[float], Optional[float]]:
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
    spot: SpotData, expiries: List[str], args: argparse.Namespace,
    cache: Dict[Path, Optional[ContractData]], logger: logging.Logger,
) -> List[DayResult]:
    results: List[DayResult] = []
    brokerage = args.brokerage_per_order * 2

    for i, day in enumerate(spot.trading_days):
        if not (args.start_date <= day <= args.end_date):
            continue
        day_name = WEEKDAY_NAMES[datetime.date.fromisoformat(day).weekday()]
        day_ts = spot.timestamps_by_day[day]

        if not is_normal_session(day_ts):
            results.append(blank_row(day, day_name, skip_reason="anomalous_session",
                                     remarks=f"{len(day_ts)} bars"))
            continue
        prev = previous_normal_session(spot.trading_days, spot.timestamps_by_day, i)
        if prev is None:
            results.append(blank_row(day, day_name, skip_reason="no_previous_session"))
            continue

        prev_rows = spot.rows_by_day[prev]
        pdh = max(prev_rows[t].high_value for t in spot.timestamps_by_day[prev])
        pdl = min(prev_rows[t].low_value for t in spot.timestamps_by_day[prev])
        open_row = spot.rows_by_day[day].get(build_ts(day, SESSION_OPEN))
        if open_row is None:
            results.append(blank_row(day, day_name, skip_reason="missing_open_bar",
                                     prev_date=prev, pdh=fmt(pdh), pdl=fmt(pdl)))
            continue
        state = classify_open(open_row.open_value, pdh, pdl)
        common = dict(prev_date=prev, pdh=fmt(pdh), pdl=fmt(pdl),
                      prev_range=fmt(pdh - pdl), day_open=fmt(open_row.open_value),
                      open_state=state)

        if pdh - pdl < args.min_prev_range:
            results.append(blank_row(day, day_name, skip_reason="prev_range_too_narrow",
                                     **common))
            continue

        cutoff_ts = build_ts(day, args.entry_cutoff)
        exit_ts = build_ts(day, args.exit_time)

        # ---- how to handle an open already beyond a level ----------------- #
        if state == "inside":
            found = find_breakout(spot.rows_by_day[day], day_ts, pdh, pdl,
                                  args.buffer_pts, cutoff_ts, day_ts[0])
            if found is None:
                results.append(blank_row(day, day_name, skip_reason="no_breakout", **common))
                continue
            break_side, entry_ts, entry_price = found
        elif args.gap_mode == "skip":
            results.append(blank_row(day, day_name, skip_reason="opened_beyond_level",
                                     **common))
            continue
        elif args.gap_mode == "immediate":
            break_side = "up" if state == "above_pdh" else "down"
            entry_ts = build_ts(day, args.entry_time)
            entry_row = spot.rows_by_day[day].get(entry_ts)
            if entry_row is None:
                results.append(blank_row(day, day_name, skip_reason="missing_entry_bar",
                                         **common))
                continue
            entry_price = entry_row.open_value
        else:                                              # retest
            break_side = "up" if state == "above_pdh" else "down"
            level = pdh if break_side == "up" else pdl
            got = find_retest(spot.rows_by_day[day], day_ts, level, break_side, cutoff_ts)
            if got is None:
                results.append(blank_row(day, day_name, skip_reason="no_retest", **common))
                continue
            entry_ts, entry_price = got

        direction = 1 if break_side == "up" else -1

        # ---- stop, from a bar that has already closed --------------------- #
        signal_ts = day_ts[max(0, day_ts.index(entry_ts) - 1)]
        atr = atr_at(spot, signal_ts, args.atr_period)
        if args.stop_mode == "atr":
            if atr is None:
                results.append(blank_row(day, day_name, skip_reason="atr_unavailable",
                                         **common))
                continue
            risk = args.stop_atr_mult * atr
        elif args.stop_mode == "opposite":
            risk = abs(entry_price - (pdl if direction > 0 else pdh))
        else:
            risk = args.fixed_stop_pts
        if risk <= 0:
            results.append(blank_row(day, day_name, skip_reason="zero_risk_distance",
                                     **common))
            continue
        stop = entry_price - risk if direction > 0 else entry_price + risk
        target = (entry_price + args.target_r * risk if direction > 0
                  else entry_price - args.target_r * risk) if args.target_r > 0 else None

        spot_out = resolve_spot_leg(spot.rows_by_day[day], day_ts, entry_ts, exit_ts,
                                    entry_price, direction, stop, target)

        expiry = first_expiry_on_or_after(expiries, day)
        lot = lot_size_for(expiry) if expiry else 75
        dte = (str((datetime.date.fromisoformat(expiry)
                    - datetime.date.fromisoformat(day)).days) if expiry else "")
        qty = lot * args.lots
        spot_gross = (spot_out.points - 2 * args.slippage_per_order) * qty
        spot_net = spot_gross - brokerage

        opt_status, opt_side, opt_strike = "no_expiry", "", ""
        opt_entry = opt_exit = opt_pts = opt_gross = opt_net = ""
        if expiry is not None:
            strike = round_to_strike(spot.rows_by_day[day][signal_ts].close_value)
            side = "CE" if direction > 0 else "PE"
            o_exit_ts = option_exit_timestamp(spot_out.exit_timestamp,
                                              spot_out.exit_reason, day_ts)
            status, oe, ox = price_option(args.options_dir, expiry, strike, side,
                                          entry_ts, o_exit_ts, cache)
            opt_status, opt_side, opt_strike = status, side, str(strike)
            if status == "TRADED" and oe is not None and ox is not None:
                raw = ox - oe
                g = (raw - 2 * args.slippage_per_order) * qty
                opt_entry, opt_exit = fmt(oe), fmt(ox)
                opt_pts, opt_gross = fmt(raw), fmt(g)
                opt_net = fmt(g - brokerage)

        results.append(DayResult(
            entry_date=day, day_of_week=day_name, status="TRADED", skip_reason="",
            prev_date=prev, pdh=fmt(pdh), pdl=fmt(pdl), prev_range=fmt(pdh - pdl),
            day_open=fmt(open_row.open_value), open_state=state,
            break_side=break_side, direction="long" if direction > 0 else "short",
            atr=fmt(atr) if atr is not None else "",
            entry_ts=entry_ts, entry_spot=fmt(entry_price), stop_spot=fmt(stop),
            target_spot=fmt(target) if target is not None else "", risk_pts=fmt(risk),
            exit_ts=spot_out.exit_timestamp, exit_spot=fmt(spot_out.exit_price),
            exit_reason=spot_out.exit_reason, spot_points=fmt(spot_out.points),
            lot_size=str(lot), qty=str(qty),
            spot_gross=fmt(spot_gross), spot_net=fmt(spot_net),
            expiry_date=expiry or "", dte=dte,
            option_status=opt_status, option_side=opt_side, option_strike=opt_strike,
            option_entry=opt_entry, option_exit=opt_exit, option_points=opt_pts,
            option_gross=opt_gross, option_net=opt_net, remarks="",
        ))
        logger.info("TRADED date=%s state=%s side=%s risk=%.1f entry=%s exit=%s "
                    "reason=%s spot_net=%.2f opt=%s",
                    day, state, break_side, risk, ts_time(entry_ts),
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


def group_table(traded: List[DayResult], lines: List[str], label: str, keyfn) -> None:
    lines += [f"| {label} | Trades | Spot net | Spot win% | Option net |",
              "|---|---:|---:|---:|---:|"]
    groups: Dict[str, List[DayResult]] = {}
    for r in traded:
        groups.setdefault(keyfn(r), []).append(r)
    for k in sorted(groups):
        v = groups[k]
        sn = [float(r.spot_net) for r in v]
        on = sum(float(r.option_net) for r in v if r.option_net)
        w = sum(1 for x in sn if x > 0)
        lines.append(f"| {k} | {len(v)} | Rs {sum(sn):,.0f} | "
                     f"{w/len(v)*100:.1f}% | Rs {on:,.0f} |")
    lines.append("")


def write_summary(rows: List[DayResult], args: argparse.Namespace, path: Path,
                  first_day: str, last_day: str) -> None:
    traded = [r for r in rows if r.status == "TRADED"]
    s_spot, s_opt = stats_for(traded, "spot"), stats_for(traded, "option")
    capital = max((float(r.qty) * float(r.entry_spot) * 0.10
                   for r in traded if r.entry_spot), default=0.0)
    lines = [
        "# Previous-Day High / Low Breakout (NIFTY 2020-2026)",
        "",
        "Spec: [`strategies/directional/previous-day-range-breakout.md`]"
        "(../../../strategies/directional/previous-day-range-breakout.md)",
        "",
        "## Strategy",
        "",
        "- `PDH` / `PDL` from the previous **normal** session — weekends, holidays and "
        "the nine anomalous sessions are stepped over",
        f"- Entry: first bar that CLOSES beyond a level (buffer `{args.buffer_pts:g}` pts); "
        "entry is the next bar's open",
        "- Direction is whichever side breaks **first in time order**",
        f"- Gap handling `{args.gap_mode}`: "
        + {"skip": "an open already beyond a level is not traded",
           "immediate": "an open beyond a level is treated as the break; enter at "
                        f"`{args.entry_time}`",
           "retest": "wait for price to return to the level and close back beyond it"}[args.gap_mode],
        f"- Stop `{args.stop_mode}`: "
        + {"atr": f"`{args.stop_atr_mult:g}` x ATR-{args.atr_period} on 5-minute bars",
           "opposite": "the other level (warning: PDH−PDL can be 300 points)",
           "fixed": f"`{args.fixed_stop_pts:g}` points"}[args.stop_mode],
        f"- Target: `{args.target_r:g}x` the stop distance"
        + (" (none — time exit only)" if args.target_r <= 0 else ""),
        f"- No entry after `{args.entry_cutoff}`; exit `{args.exit_time}`",
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
        f"- Option, per trade per lot: **Rs {s_opt['avg']:,.1f}** against a random ATM "
        "buyer's **Rs −119.5** ([heads-tails long grid](../heads-tails/))",
        "",
    ]

    lines += ["### By break direction", ""]
    group_table(traded, lines, "Side", lambda r: r.break_side)
    lines += ["### By how the session opened", "",
              "`inside` is a genuine intraday break of a level that held at the open. "
              "The others only appear when `--gap-mode` is not `skip`.", ""]
    group_table(traded, lines, "Open state", lambda r: r.open_state)
    lines += ["### By year", ""]
    group_table(traded, lines, "Year", lambda r: r.entry_date[:4])
    lines += ["### By days to expiry", ""]
    group_table(traded, lines, "DTE",
                lambda r: "0 (expiry day)" if r.dte == "0"
                else ("1-3" if r.dte in ("1", "2", "3") else "4+"))

    by_reason: Dict[str, int] = {}
    for r in traded:
        by_reason[r.exit_reason] = by_reason.get(r.exit_reason, 0) + 1
    lines += ["| Exit reason | Trades |", "|---|---:|"]
    for k in sorted(by_reason, key=lambda k: -by_reason[k]):
        lines.append(f"| `{k}` | {by_reason[k]} |")
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
        "- ATR is computed here because nothing else in this repo does. It is causal: "
        "the window ends on the last bar that CLOSED before the entry decision.",
        "- `retest` only enters after the holding bar has closed. Deciding at the moment "
        "of the touch that the level will hold reads the future.",
        "- A bar containing both stop and target resolves to the **stop**.",
        "- An intrabar spot exit sells the option on the NEXT bar — that bar's own open "
        "is a price from before the trigger.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
def output_tag(args: argparse.Namespace) -> str:
    tag = f"{args.gap_mode}_{args.stop_mode}"
    if args.stop_mode == "atr":
        tag += f"{args.stop_atr_mult:g}"
    elif args.stop_mode == "fixed":
        tag += f"{args.fixed_stop_pts:g}"
    tag += f"_r{args.target_r:g}_buf{args.buffer_pts:g}_lots{args.lots}"
    if args.slippage_per_order == 0:
        tag += "_slip0"
    return tag


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[3]
    p = argparse.ArgumentParser(description="Previous-day high/low breakout on NIFTY.")
    p.add_argument("--spot-file", type=Path,
                   default=repo_root / "nifty" / "NIFTY50_INDEX_5m_last_7y.csv")
    p.add_argument("--options-dir", type=Path,
                   default=repo_root / "NiftyOptions_2020_2026" / "Options")
    p.add_argument("--results-dir", type=Path,
                   default=repo_root / "backtesting" / "results" / "directional-intraday")
    p.add_argument("--gap-mode", choices=["skip", "immediate", "retest"], default="skip")
    p.add_argument("--stop-mode", choices=["atr", "opposite", "fixed"], default="atr")
    p.add_argument("--stop-atr-mult", type=float, default=1.5)
    p.add_argument("--atr-period", type=int, default=14)
    p.add_argument("--fixed-stop-pts", type=float, default=40.0)
    p.add_argument("--target-r", type=float, default=1.5)
    p.add_argument("--buffer-pts", type=float, default=0.0)
    p.add_argument("--min-prev-range", type=float, default=0.0)
    p.add_argument("--entry-time", default="09:20")
    p.add_argument("--entry-cutoff", default="14:00")
    p.add_argument("--exit-time", default="15:20")
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

    spot = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    in_range = [d for d in spot.trading_days if args.start_date <= d <= args.end_date]
    if not in_range:
        raise SystemExit("No sessions in range — check --spot-file and dates.")
    print(f"sessions in range: {len(in_range)} ({in_range[0]} .. {in_range[-1]})")

    cache: Dict[Path, Optional[ContractData]] = {}
    rows = run_days(spot, expiries, args, cache, logger)
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
