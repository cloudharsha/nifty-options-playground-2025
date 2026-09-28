#!/usr/bin/env python3
"""
Opening Gap — fade the small ones, follow the large ones — NIFTY 2020-2026.

Spec: strategies/directional/opening-gap.md

One rule with a size threshold. The overnight gap is either noise (small, fades
back to yesterday's close) or information (large, keeps going). Both variants
are tested in one run so the threshold between them is visible.

  GAP       gap_pts = today's 09:15 open - previous session's 15:25 close

  FADE      Taken when  --min-fade <= |gap| <= --max-fade.
            Trade AGAINST the gap: short a gap up, long a gap down.
            Confirmation `stall` waits for the gap's direction to stop making
            new extremes for --stall-bars bars; `none` enters at 09:20.
            Target: the previous close (the gap fills).
            Stop:   --fade-stop-mult x the gap size, beyond the open.

  GO        Taken when  |gap| >= --min-go  AND the 09:15 bar closes beyond its
            own open in the gap's direction.
            Trade WITH the gap. Stop at the 09:15 bar's opposite extreme,
            target --go-target-r x that distance.

            The band between --max-fade and --min-go is deliberately not
            traded. Whether it should be is what the sweep answers.

  EXIT      15:20 for anything still open. One trade per session, no re-entry.

TWO P/L COLUMNS. Every trade is reported twice:

  * SPOT   - the signal's raw edge, as a futures-equivalent at one lot. No
             theta, no delta decay, no strike selection. This says whether the
             signal predicts direction at all.
  * OPTION - the same signal expressed as a long ATM CE/PE of the nearest
             weekly expiry, entered and exited at the same timestamps.

They answer different questions and must not be conflated. The benchmark for the
option column is not zero: buying random ATM options over this sample loses
roughly Rs 756,517 at its best setting (see results/heads-tails/). A signal only
has to pay for the theta a coin flip cannot.

Stops and targets are ALWAYS defined on spot. A premium-based stop would mix the
signal's edge with the option's gamma and the two could not be told apart.

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

BASE_FILENAME = "opening_gap_2020_2026"
IST_SUFFIX = "+05:30"
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday"]
STRIKE_STEP = 50
SESSION_OPEN = "09:15"

# A normal NIFTY session is 75 five-minute bars (09:15..15:25). Muhurat evening
# sessions and the occasional special Saturday are far shorter and have a
# different character; they must neither be traded nor set another day's
# reference levels. Measured: 1,595 of 1,606 sessions are exactly 75 bars.
SESSION_MIN_BARS = 70

# Gap buckets for the fill-rate table, in absolute points.
GAP_BUCKETS = [(0, 25), (25, 50), (50, 70), (70, 100),
               (100, 150), (150, 200), (200, 10_000)]


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
    variant: str
    prev_date: str
    prev_close: str
    day_open: str
    gap_pts: str
    gap_dir: str
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
    """Lot size active for this contract, keyed to its EXPIRY date.

    Not the trade date: a weekly contract open across a lot-size change keeps
    the size it was introduced with.
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


def median(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


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


# --------------------------------------------------------------------------- #
# session helpers
# --------------------------------------------------------------------------- #
def is_normal_session(timestamps: List[str]) -> bool:
    """A full-length session that opens at 09:15.

    Muhurat evening sessions and special Saturdays fail both tests.
    """
    return len(timestamps) >= SESSION_MIN_BARS and ts_time(timestamps[0]) == SESSION_OPEN


def previous_normal_session(
    trading_days: List[str], timestamps_by_day: Dict[str, List[str]], day_index: int,
) -> Optional[str]:
    """The most recent NORMAL session strictly before day_index.

    Not the previous calendar day - weekends, holidays and the nine anomalous
    sessions all have to be stepped over.
    """
    for i in range(day_index - 1, -1, -1):
        prev = trading_days[i]
        if is_normal_session(timestamps_by_day[prev]):
            return prev
    return None


# --------------------------------------------------------------------------- #
# gap statistics - computed over EVERY session, traded or not
# --------------------------------------------------------------------------- #
@dataclass
class GapStat:
    day: str
    gap_pts: float
    filled: bool
    fill_minutes: Optional[int]


def minutes_from_open(timestamp: str) -> int:
    h, m = int(timestamp[11:13]), int(timestamp[14:16])
    return (h * 60 + m) - (9 * 60 + 15)


def gap_fill_stats(
    trading_days: List[str], rows_by_day: Dict[str, Dict[str, PriceRow]],
    timestamps_by_day: Dict[str, List[str]], start_date: str, end_date: str,
) -> List[GapStat]:
    """Did the gap fill, and when.

    Measured over every session in range regardless of whether a trade was
    taken. Restricting this to days a trade triggered would inflate the fill
    rate - the days that gap and never look back are exactly the ones a trade
    filter removes.
    """
    out: List[GapStat] = []
    for i, day in enumerate(trading_days):
        if not (start_date <= day <= end_date):
            continue
        day_ts = timestamps_by_day[day]
        if not is_normal_session(day_ts):
            continue
        prev = previous_normal_session(trading_days, timestamps_by_day, i)
        if prev is None:
            continue
        prev_close = rows_by_day[prev][timestamps_by_day[prev][-1]].close_value
        open_ts = build_ts(day, SESSION_OPEN)
        open_row = rows_by_day[day].get(open_ts)
        if open_row is None:
            continue
        gap = open_row.open_value - prev_close
        if gap == 0.0:
            continue

        filled, fill_min = False, None
        for ts in day_ts:
            row = rows_by_day[day][ts]
            # A gap up fills when price trades back DOWN to the previous close.
            if (gap > 0 and row.low_value <= prev_close) or \
               (gap < 0 and row.high_value >= prev_close):
                filled, fill_min = True, minutes_from_open(ts)
                break
        out.append(GapStat(day, gap, filled, fill_min))
    return out


def write_gap_fill_table(stats: List[GapStat], lines: List[str]) -> None:
    lines += [
        "## Gap fill rate by size — every session, traded or not",
        "",
        "The premise both variants rest on. If the fill rate does not decline as",
        "the gap grows, small gaps are not more likely to fill than large ones and",
        "there is no threshold to find.",
        "",
        "| Gap (abs pts) | Sessions | Filled same day | Filled by 11:00 | Median mins to fill |",
        "|---|---:|---:|---:|---:|",
    ]
    for lo, hi in GAP_BUCKETS:
        bucket = [s for s in stats if lo <= abs(s.gap_pts) < hi]
        if not bucket:
            continue
        filled = [s for s in bucket for _ in (0,) if s.filled]
        by11 = [s for s in filled if s.fill_minutes is not None and s.fill_minutes <= 105]
        med = median([float(s.fill_minutes) for s in filled if s.fill_minutes is not None])
        label = f"{lo}–{hi}" if hi < 10_000 else f"{lo}+"
        lines.append(
            f"| {label} | {len(bucket)} | {len(filled)} ({len(filled)/len(bucket)*100:.1f}%) | "
            f"{len(by11)} ({len(by11)/len(bucket)*100:.1f}%) | {med:.0f} |")

    lines += ["", "Split by direction:", "",
              "| Gap (abs pts) | Up sessions | Up filled | Down sessions | Down filled |",
              "|---|---:|---:|---:|---:|"]
    for lo, hi in GAP_BUCKETS:
        up = [s for s in stats if lo <= s.gap_pts < hi]
        dn = [s for s in stats if lo <= -s.gap_pts < hi]
        if not up and not dn:
            continue
        uf = sum(1 for s in up if s.filled)
        df = sum(1 for s in dn if s.filled)
        label = f"{lo}–{hi}" if hi < 10_000 else f"{lo}+"
        lines.append(
            f"| {label} | {len(up)} | {uf} ({uf/len(up)*100:.1f}%) | "
            f"{len(dn)} | {df} ({df/len(dn)*100:.1f}%) |"
            if up and dn else
            f"| {label} | {len(up)} | {uf} | {len(dn)} | {df} |")
    lines.append("")


# --------------------------------------------------------------------------- #
# strategy
# --------------------------------------------------------------------------- #
def resolve_spot_leg(
    rows: Dict[str, PriceRow], day_ts: List[str], entry_ts: str, exit_ts: str,
    entry_price: float, direction: int, stop: float, target: Optional[float],
) -> LegOutcome:
    """Walk spot bars from entry to exit.

    direction: +1 long, -1 short.

    A bar whose OPEN is already beyond the level gapped through it and fills at
    that open. A bar that only reaches the level intrabar fills at the level.
    The stop is checked before the target within a bar, so a bar containing both
    resolves to the stop - the conservative assumption, and the only one the
    5-minute series can justify.
    """
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
        pts = direction * (exit_row.open_value - entry_price)
        return LegOutcome(exit_ts, exit_row.open_value, "day_close", pts)

    earlier = [t for t in day_ts if t <= exit_ts]
    if earlier:
        last = earlier[-1]
        px = rows[last].open_value
        return LegOutcome(last, px, "last_bar_before_exit", direction * (px - entry_price))
    return LegOutcome(exit_ts, entry_price, "missing_exit_bar", 0.0)


def find_stall_entry(
    rows: Dict[str, PriceRow], day_ts: List[str], gap_dir: int,
    stall_bars: int, cutoff_ts: str,
) -> Optional[str]:
    """First bar open at which the gap's direction has stalled.

    A gap up has stalled when no new high has been made for `stall_bars`
    consecutive bars. The run is only known once the last of those bars has
    CLOSED, so the entry is the open of the bar after it - never the bar that
    completed the run.

    Returns the entry timestamp, or None if no stall completes before cutoff.
    """
    extreme: Optional[float] = None
    consecutive = 0
    for idx, ts in enumerate(day_ts):
        row = rows[ts]
        level = row.high_value if gap_dir > 0 else row.low_value
        if extreme is None:
            extreme = level
            continue
        made_new = level > extreme if gap_dir > 0 else level < extreme
        if made_new:
            extreme = level
            consecutive = 0
        else:
            consecutive += 1
        if consecutive >= stall_bars:
            if idx + 1 >= len(day_ts):
                return None
            entry_ts = day_ts[idx + 1]
            return entry_ts if entry_ts <= cutoff_ts else None
    return None


# Exit reasons where the trigger happened somewhere INSIDE the bar rather than
# at its open. The spot leg fills at the level itself - a resting order would
# have been taken there - but nothing else can be filled at that bar's open,
# which is a price from before the trigger existed. This is lookahead bug #1
# from backtesting/docs/lookahead-audit.md.
INTRABAR_REASONS = {"sl", "target"}


def option_exit_timestamp(spot_exit_ts: str, reason: str, day_ts: List[str]) -> str:
    """When the option leg can actually be sold.

    An intrabar stop or target was touched at an unknown moment inside the
    5-minute bar. The first price we can be certain is after the touch is the
    next bar's open, so that is where the option exits. Selling it at the
    trigger bar's own open would book a price from before the move happened.
    """
    if reason not in INTRABAR_REASONS:
        return spot_exit_ts
    try:
        idx = day_ts.index(spot_exit_ts)
    except ValueError:
        return spot_exit_ts
    return day_ts[idx + 1] if idx + 1 < len(day_ts) else spot_exit_ts


def price_option(
    options_dir: Path, expiry: str, strike: int, side: str, entry_ts: str,
    exit_ts: str, cache: Dict[Path, Optional[ContractData]],
) -> Tuple[str, Optional[float], Optional[float]]:
    """(status, entry_open, exit_open) for a long option held entry -> exit.

    The option rides the spot signal: it is bought at the entry minute and sold
    at whatever minute the spot leg exited. No premium-based stop.
    """
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


def band_thresholds(args: argparse.Namespace, prev_close: float) -> Tuple[float, float, float]:
    """(min_fade, max_fade, min_go) in points, for this day.

    `points` mode uses the same absolute thresholds throughout. That sounds
    neutral and is not: NIFTY roughly doubled across this sample, so a fixed
    30-100 point band was 0.27-0.88% of spot in 2020 and only 0.12-0.40% by
    2025. The band quietly becomes a different strategy as the index level
    rises - the same defect the Rs 5-10 premium band had in the expiry-day
    family.

    `pct` mode fixes the band as a fraction of the previous close, so the same
    kind of move is selected in every era.
    """
    if args.band_mode == "pct":
        return (prev_close * args.min_fade_pct / 100.0,
                prev_close * args.max_fade_pct / 100.0,
                prev_close * args.min_go_pct / 100.0)
    return args.min_fade, args.max_fade, args.min_go


def blank_row(day: str, day_name: str, **over) -> DayResult:
    base = {f: "" for f in DayResult.__dataclass_fields__}
    base.update(entry_date=day, day_of_week=day_name, status="SKIPPED", variant="NONE")
    base.update(over)
    return DayResult(**base)


def run_days(
    trading_days: List[str], rows_by_day: Dict[str, Dict[str, PriceRow]],
    timestamps_by_day: Dict[str, List[str]], expiries: List[str],
    args: argparse.Namespace, cache: Dict[Path, Optional[ContractData]],
    logger: logging.Logger,
) -> List[DayResult]:
    results: List[DayResult] = []
    spot_brokerage = args.brokerage_per_order * 2      # in and out, one instrument
    opt_brokerage = args.brokerage_per_order * 2

    for i, day in enumerate(trading_days):
        if not (args.start_date <= day <= args.end_date):
            continue
        day_name = WEEKDAY_NAMES[datetime.date.fromisoformat(day).weekday()]
        day_ts = timestamps_by_day[day]

        if not is_normal_session(day_ts):
            results.append(blank_row(day, day_name, skip_reason="anomalous_session",
                                     remarks=f"{len(day_ts)} bars, opens {ts_time(day_ts[0])}"))
            continue

        prev = previous_normal_session(trading_days, timestamps_by_day, i)
        if prev is None:
            results.append(blank_row(day, day_name, skip_reason="no_previous_session"))
            continue

        prev_close = rows_by_day[prev][timestamps_by_day[prev][-1]].close_value
        open_ts = build_ts(day, SESSION_OPEN)
        open_row = rows_by_day[day].get(open_ts)
        if open_row is None:
            results.append(blank_row(day, day_name, skip_reason="missing_open_bar",
                                     prev_date=prev, prev_close=fmt(prev_close)))
            continue

        gap = open_row.open_value - prev_close
        gap_dir = 1 if gap > 0 else -1
        common = dict(prev_date=prev, prev_close=fmt(prev_close),
                      day_open=fmt(open_row.open_value), gap_pts=fmt(gap),
                      gap_dir="up" if gap_dir > 0 else "down")
        agap = abs(gap)
        min_fade, max_fade, min_go = band_thresholds(args, prev_close)

        # ---- which variant, if any -------------------------------------- #
        variant = ""
        if min_fade <= agap <= max_fade:
            variant = "FADE"
        elif agap >= min_go:
            variant = "GO"
        elif agap < min_fade:
            results.append(blank_row(day, day_name, skip_reason="gap_below_threshold", **common))
            continue
        else:
            results.append(blank_row(day, day_name, skip_reason="gap_in_dead_band", **common))
            continue

        exit_ts = build_ts(day, args.exit_time)
        cutoff_ts = build_ts(day, args.entry_cutoff)

        if variant == "FADE":
            direction = -gap_dir                      # trade against the gap
            if args.fade_confirm == "stall":
                entry_ts = find_stall_entry(rows_by_day[day], day_ts, gap_dir,
                                            args.stall_bars, cutoff_ts)
                if entry_ts is None:
                    results.append(blank_row(day, day_name, variant="FADE",
                                             skip_reason="fade_not_confirmed", **common))
                    continue
            else:
                entry_ts = build_ts(day, args.entry_time)
            entry_row = rows_by_day[day].get(entry_ts)
            if entry_row is None:
                results.append(blank_row(day, day_name, variant="FADE",
                                         skip_reason="missing_entry_bar", **common))
                continue
            entry_price = entry_row.open_value
            # The gap can fill while the stall is still forming. Entering then
            # would open a trade that is already past its own target, which
            # exits on the entry bar for a guaranteed cost-only loss. There is
            # no gap left to fade, so there is no trade.
            if (entry_price - prev_close) * gap_dir <= 0:
                results.append(blank_row(day, day_name, variant="FADE",
                                         skip_reason="gap_already_filled", **common))
                continue
            target = prev_close
            stop = (entry_price + args.fade_stop_mult * agap if direction < 0
                    else entry_price - args.fade_stop_mult * agap)
        else:                                          # GO
            if gap_dir > 0 and open_row.close_value <= open_row.open_value:
                results.append(blank_row(day, day_name, variant="GO",
                                         skip_reason="go_not_confirmed", **common))
                continue
            if gap_dir < 0 and open_row.close_value >= open_row.open_value:
                results.append(blank_row(day, day_name, variant="GO",
                                         skip_reason="go_not_confirmed", **common))
                continue
            direction = gap_dir                        # trade with the gap
            entry_ts = build_ts(day, args.entry_time)
            entry_row = rows_by_day[day].get(entry_ts)
            if entry_row is None:
                results.append(blank_row(day, day_name, variant="GO",
                                         skip_reason="missing_entry_bar", **common))
                continue
            entry_price = entry_row.open_value
            stop = open_row.low_value if direction > 0 else open_row.high_value
            risk = abs(entry_price - stop)
            if risk <= 0:
                results.append(blank_row(day, day_name, variant="GO",
                                         skip_reason="zero_risk_distance", **common))
                continue
            target = (entry_price + args.go_target_r * risk if direction > 0
                      else entry_price - args.go_target_r * risk)

        # ---- spot leg ---------------------------------------------------- #
        spot_out = resolve_spot_leg(rows_by_day[day], day_ts, entry_ts, exit_ts,
                                    entry_price, direction, stop, target)

        expiry = first_expiry_on_or_after(expiries, day)
        if expiry is None:
            lot = 75
            dte = ""
        else:
            lot = lot_size_for(expiry)
            dte = str((datetime.date.fromisoformat(expiry)
                       - datetime.date.fromisoformat(day)).days)
        qty = lot * args.lots

        spot_pts_net = spot_out.points - 2 * args.slippage_per_order
        spot_gross = spot_pts_net * qty
        spot_net = spot_gross - spot_brokerage

        # ---- option leg -------------------------------------------------- #
        # The strike comes from spot at the SIGNAL bar's close, i.e. the bar
        # that closed immediately before entry - not the entry bar's own close,
        # which is not known when the order is placed.
        opt_status, opt_side, opt_strike = "no_expiry", "", ""
        opt_entry = opt_exit = opt_pts = opt_gross = opt_net = ""
        if expiry is not None:
            idx = day_ts.index(entry_ts)
            signal_row = rows_by_day[day][day_ts[idx - 1]] if idx > 0 else open_row
            strike = round_to_strike(signal_row.close_value)
            side = "CE" if direction > 0 else "PE"
            opt_exit_ts = option_exit_timestamp(spot_out.exit_timestamp,
                                                spot_out.exit_reason, day_ts)
            status, oe, ox = price_option(args.options_dir, expiry, strike, side,
                                          entry_ts, opt_exit_ts, cache)
            opt_status, opt_side, opt_strike = status, side, str(strike)
            if status == "TRADED" and oe is not None and ox is not None:
                raw = ox - oe                          # always a LONG option
                net_pts = raw - 2 * args.slippage_per_order
                g = net_pts * qty
                opt_entry, opt_exit = fmt(oe), fmt(ox)
                opt_pts, opt_gross = fmt(raw), fmt(g)
                opt_net = fmt(g - opt_brokerage)

        results.append(DayResult(
            entry_date=day, day_of_week=day_name, status="TRADED", skip_reason="",
            variant=variant, prev_date=prev, prev_close=fmt(prev_close),
            day_open=fmt(open_row.open_value), gap_pts=fmt(gap),
            gap_dir="up" if gap_dir > 0 else "down",
            direction="long" if direction > 0 else "short",
            entry_ts=entry_ts, entry_spot=fmt(entry_price), stop_spot=fmt(stop),
            target_spot=fmt(target) if target is not None else "",
            exit_ts=spot_out.exit_timestamp, exit_spot=fmt(spot_out.exit_price),
            exit_reason=spot_out.exit_reason, spot_points=fmt(spot_out.points),
            lot_size=str(lot), qty=str(qty),
            spot_gross=fmt(spot_gross), spot_net=fmt(spot_net),
            expiry_date=expiry or "", dte=dte,
            option_status=opt_status, option_side=opt_side, option_strike=opt_strike,
            option_entry=opt_entry, option_exit=opt_exit, option_points=opt_pts,
            option_gross=opt_gross, option_net=opt_net, remarks="",
        ))
        logger.info("TRADED date=%s variant=%s gap=%.2f dir=%s entry=%s exit=%s "
                    "reason=%s spot_net=%.2f opt=%s",
                    day, variant, gap, "long" if direction > 0 else "short",
                    ts_time(entry_ts), ts_time(spot_out.exit_timestamp),
                    spot_out.exit_reason, spot_net, opt_net or opt_status)
    return results


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #
def stats_for(rows: List[DayResult], column: str) -> dict:
    """column: 'spot' or 'option'."""
    field = "spot_net" if column == "spot" else "option_net"
    traded = [r for r in rows if r.status == "TRADED" and getattr(r, field) != ""]
    nets = [float(getattr(r, f)) for r in traded for f in (field,)]
    wins = [n for n in nets if n > 0]
    losses = [n for n in nets if n < 0]
    return {
        "traded": len(traded),
        "net": sum(nets),
        "wins": len(wins), "losses": len(losses),
        "win_rate": (len(wins) / len(traded) * 100) if traded else 0.0,
        "profit_factor": (sum(wins) / abs(sum(losses))) if losses else float("inf"),
        "max_dd": max_drawdown(nets),
        "best": max(nets) if nets else 0.0,
        "worst": min(nets) if nets else 0.0,
        "avg": (sum(nets) / len(nets)) if nets else 0.0,
        "nets": nets,
    }


def write_daywise_csv(rows: List[DayResult], path: Path) -> None:
    fields = list(DayResult.__dataclass_fields__.keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({f: getattr(r, f) for f in fields})


def pf_text(pf: float) -> str:
    return "inf" if pf == float("inf") else f"{pf:.2f}"


def variant_block(rows: List[DayResult], variant: str, args: argparse.Namespace,
                  lines: List[str], first_day: str, last_day: str) -> None:
    sub = [r for r in rows if r.variant == variant and r.status == "TRADED"]
    if not sub:
        lines += [f"### {variant}", "", "No trades.", ""]
        return
    s_spot = stats_for(sub, "spot")
    s_opt = stats_for(sub, "option")
    capital = max((float(r.qty) * float(r.entry_spot) * 0.10
                   for r in sub if r.entry_spot), default=0.0)
    lines += [
        f"### {variant}", "",
        f"- Trades: `{s_spot['traded']}`  "
        f"(option priced on `{s_opt['traded']}` of them)",
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
        "",
    ]

    by_reason: Dict[str, int] = {}
    for r in sub:
        by_reason[r.exit_reason] = by_reason.get(r.exit_reason, 0) + 1
    lines += ["| Exit reason | Trades |", "|---|---:|"]
    for k in sorted(by_reason, key=lambda k: -by_reason[k]):
        lines.append(f"| `{k}` | {by_reason[k]} |")
    lines.append("")

    by_year: Dict[str, List[DayResult]] = {}
    for r in sub:
        by_year.setdefault(r.entry_date[:4], []).append(r)
    lines += ["| Year | Trades | Spot net | Option net |", "|---|---:|---:|---:|"]
    for y in sorted(by_year):
        v = by_year[y]
        sn = sum(float(r.spot_net) for r in v)
        on = sum(float(r.option_net) for r in v if r.option_net)
        lines.append(f"| {y} | {len(v)} | Rs {sn:,.0f} | Rs {on:,.0f} |")
    lines.append("")

    by_dte: Dict[str, List[DayResult]] = {}
    for r in sub:
        key = "0 (expiry day)" if r.dte == "0" else ("1-3" if r.dte in ("1", "2", "3") else "4+")
        by_dte.setdefault(key, []).append(r)
    lines += ["A fifth of all sessions are expiry days, so a 'nearest weekly' option "
              "is 0-DTE on many trades. This is where a long option is most likely "
              "to die:", "",
              "| Days to expiry | Trades | Spot net | Option net |", "|---|---:|---:|---:|"]
    for k in sorted(by_dte):
        v = by_dte[k]
        sn = sum(float(r.spot_net) for r in v)
        on = sum(float(r.option_net) for r in v if r.option_net)
        lines.append(f"| {k} | {len(v)} | Rs {sn:,.0f} | Rs {on:,.0f} |")
    lines.append("")


def write_summary(rows: List[DayResult], gstats: List[GapStat],
                  args: argparse.Namespace, path: Path,
                  first_day: str, last_day: str) -> None:
    traded = [r for r in rows if r.status == "TRADED"]
    lines = [
        "# Opening Gap — Fade Small, Follow Large (NIFTY 2020-2026)",
        "",
        "Spec: [`strategies/directional/opening-gap.md`](../../../strategies/directional/opening-gap.md)",
        "",
        "## Strategy",
        "",
        f"- `gap = today's {SESSION_OPEN} open − previous normal session's last close`",
        (f"- **FADE** when `{args.min_fade_pct:g}% <= |gap|/prev_close <= "
         f"{args.max_fade_pct:g}%`"
         if args.band_mode == "pct" else
         f"- **FADE** when `{args.min_fade:g} <= |gap| <= {args.max_fade:g}` points")
        + f" — trade against the gap, target the previous close, stop "
          f"{args.fade_stop_mult:g}x the gap beyond the open",
        (f"- Band is a **percentage of the previous close**, so the same kind of move "
         f"is selected at Nifty 12,000 and at 25,000"
         if args.band_mode == "pct" else
         "- Band is in **absolute points**. Note this is not neutral across the "
         "sample: NIFTY roughly doubled, so a fixed band selects progressively "
         "smaller relative moves as the index rises"),
        f"- Fade confirmation: `{args.fade_confirm}`"
        + (f" — wait for {args.stall_bars} bars with no new extreme in the gap's direction, "
           f"enter the bar after; give up at `{args.entry_cutoff}`"
           if args.fade_confirm == "stall" else f" — enter at `{args.entry_time}`"),
        (f"- **GO** when `|gap|/prev_close >= {args.min_go_pct:g}%`"
         if args.band_mode == "pct" else
         f"- **GO** when `|gap| >= {args.min_go:g}` points")
        + f" **and** the {SESSION_OPEN} bar closes beyond "
        "its own open in the gap's direction — trade with the gap, stop at that bar's "
        f"opposite extreme, target {args.go_target_r:g}R",
        "- The band between the fade maximum and the go threshold is deliberately "
        "not traded",
        f"- Exit `{args.exit_time}`. One trade per session, no re-entry",
        f"- Size: {args.lots} lot(s), expiry-aware (75/50/25/75/65)",
        f"- Costs, both columns: Rs {args.brokerage_per_order:.0f}/order "
        f"(Rs {args.brokerage_per_order*2:.0f} per round trip) + "
        f"{args.slippage_per_order:.2f} pt/order",
        f"- Sessions with fewer than {SESSION_MIN_BARS} bars, or not opening at "
        f"{SESSION_OPEN}, are excluded from trading and from setting reference levels",
        f"- Period: `{first_day}` to `{last_day}`",
        "",
        "## How to read the two columns",
        "",
        "**Spot** is the signal's raw edge as a futures-equivalent — no theta, no delta, "
        "no strike. It answers *does this signal predict direction*.",
        "",
        "**Option** is the same signal bought as an ATM CE/PE of the nearest weekly, "
        "entered and exited at the same minutes. It answers *can that edge survive being "
        "expressed as a long option*.",
        "",
        "The option column's benchmark is **not zero**. Buying random ATM options over "
        "this sample loses about **Rs 756,517** at its best setting "
        "([heads-tails long grid](../heads-tails/)). A signal only has to pay for the "
        "theta a coin flip cannot. Spot positive with option negative is a working "
        "signal and a failed expression — not a failed strategy.",
        "",
    ]

    write_gap_fill_table(gstats, lines)

    lines += ["## Results", ""]
    for variant in ("FADE", "GO"):
        variant_block(rows, variant, args, lines, first_day, last_day)

    s_all_spot = stats_for(traded, "spot")
    s_all_opt = stats_for(traded, "option")
    lines += [
        "### Both variants combined", "",
        "| Column | Trades | Net P/L | Win% | PF | Max DD |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Spot | {s_all_spot['traded']} | Rs {s_all_spot['net']:,.0f} | "
        f"{s_all_spot['win_rate']:.1f}% | {pf_text(s_all_spot['profit_factor'])} | "
        f"Rs {s_all_spot['max_dd']:,.0f} |",
        f"| Option | {s_all_opt['traded']} | Rs {s_all_opt['net']:,.0f} | "
        f"{s_all_opt['win_rate']:.1f}% | {pf_text(s_all_opt['profit_factor'])} | "
        f"Rs {s_all_opt['max_dd']:,.0f} |",
        "",
    ]

    skips: Dict[str, int] = {}
    for r in rows:
        if r.status != "TRADED":
            skips[r.skip_reason] = skips.get(r.skip_reason, 0) + 1
    if skips:
        lines += ["## Sessions not traded", "", "| Reason | Sessions |", "|---|---:|"]
        for k in sorted(skips, key=lambda k: -skips[k]):
            lines.append(f"| `{k}` | {skips[k]} |")
        lines.append("")

    opt_fail: Dict[str, int] = {}
    for r in traded:
        if r.option_status != "TRADED":
            opt_fail[r.option_status] = opt_fail.get(r.option_status, 0) + 1
    if opt_fail:
        lines += ["| Option not priced | Trades |", "|---|---:|"]
        for k in sorted(opt_fail, key=lambda k: -opt_fail[k]):
            lines.append(f"| `{k}` | {opt_fail[k]} |")
        lines.append("")

    lines += [
        "## Notes", "",
        "- Entry is always the open of the bar AFTER the one that confirmed the signal. "
        "A bar stamped `T` closes at `T+5min` and cannot be read before then.",
        "- A bar containing both the stop and the target resolves to the **stop**. The "
        "5-minute series cannot order them; assuming the target would flatter every result.",
        "- The option strike is taken from spot at the signal bar's close, not the entry "
        "bar's — the latter is not known when the order is placed.",
        "- The option rides the spot signal: no premium stop, bought at entry and sold at "
        "whatever minute the spot leg exited.",
        "- Gap fill statistics cover every session in range, including days that gapped "
        "and never came back.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
def output_tag(args: argparse.Namespace) -> str:
    if args.band_mode == "pct":
        tag = (f"pct{args.min_fade_pct:g}-{args.max_fade_pct:g}"
               f"_go{args.min_go_pct:g}")
    else:
        tag = f"fade{args.min_fade:g}-{args.max_fade:g}_go{args.min_go:g}"
    tag += f"_{args.fade_confirm}"
    if args.fade_confirm == "stall":
        tag += str(args.stall_bars)
    tag += f"_r{args.go_target_r:g}_lots{args.lots}"
    if args.slippage_per_order == 0:
        tag += "_slip0"
    return tag


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[3]
    p = argparse.ArgumentParser(
        description="Opening gap — fade the small ones, follow the large ones.")
    p.add_argument("--spot-file", type=Path,
                   default=repo_root / "nifty" / "NIFTY50_INDEX_5m_last_7y.csv")
    p.add_argument("--options-dir", type=Path,
                   default=repo_root / "NiftyOptions_2020_2026" / "Options")
    p.add_argument("--results-dir", type=Path,
                   default=repo_root / "backtesting" / "results" / "directional-intraday")
    p.add_argument("--band-mode", choices=["points", "pct"], default="points",
                   help="pct fixes the gap band as a %% of the previous close, so "
                        "the same kind of move is selected at Nifty 12,000 and 25,000.")
    p.add_argument("--min-fade", type=float, default=30.0)
    p.add_argument("--max-fade", type=float, default=100.0)
    p.add_argument("--fade-confirm", choices=["none", "stall"], default="stall")
    p.add_argument("--stall-bars", type=int, default=3)
    p.add_argument("--fade-stop-mult", type=float, default=1.0)
    p.add_argument("--min-go", type=float, default=150.0)
    p.add_argument("--min-fade-pct", type=float, default=0.15)
    p.add_argument("--max-fade-pct", type=float, default=0.50)
    p.add_argument("--min-go-pct", type=float, default=0.80)
    p.add_argument("--go-target-r", type=float, default=1.5)
    p.add_argument("--entry-time", default="09:20",
                   help="Used by GO, and by FADE when --fade-confirm none.")
    p.add_argument("--entry-cutoff", default="12:00",
                   help="Latest a stalled fade may be entered.")
    p.add_argument("--exit-time", default="15:20")
    p.add_argument("--lots", type=int, default=1)
    p.add_argument("--brokerage-per-order", type=float, default=25.0)
    p.add_argument("--slippage-per-order", type=float, default=0.50)
    p.add_argument("--start-date", default="2020-01-01")
    p.add_argument("--end-date", default="2026-12-31")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    lo, hi, go = ((args.min_fade_pct, args.max_fade_pct, args.min_go_pct)
                  if args.band_mode == "pct" else
                  (args.min_fade, args.max_fade, args.min_go))
    if lo > hi:
        raise SystemExit("fade band is inverted — min must not exceed max")
    if hi > go:
        raise SystemExit("fade band must not overlap the go threshold")
    args.results_dir.mkdir(parents=True, exist_ok=True)
    tag = output_tag(args)
    logger = configure_logger(args.results_dir / f"{BASE_FILENAME}_{tag}.log")

    trading_days, rows_by_day, timestamps_by_day = load_spot_data(args.spot_file)
    expiries = load_expiry_folders(args.options_dir)
    in_range = [d for d in trading_days if args.start_date <= d <= args.end_date]
    if not in_range:
        raise SystemExit("No sessions in range — check --spot-file and dates.")
    print(f"sessions in range: {len(in_range)} ({in_range[0]} .. {in_range[-1]})")

    gstats = gap_fill_stats(trading_days, rows_by_day, timestamps_by_day,
                            args.start_date, args.end_date)
    filled = sum(1 for s in gstats if s.filled)
    print(f"gap stats: {len(gstats)} sessions with a gap, "
          f"{filled} filled same day ({filled/len(gstats)*100:.1f}%)")

    cache: Dict[Path, Optional[ContractData]] = {}
    rows = run_days(trading_days, rows_by_day, timestamps_by_day, expiries,
                    args, cache, logger)

    for variant in ("FADE", "GO"):
        sub = [r for r in rows if r.variant == variant and r.status == "TRADED"]
        if not sub:
            print(f"  {variant:<5} no trades")
            continue
        ss, so = stats_for(sub, "spot"), stats_for(sub, "option")
        print(f"  {variant:<5} trades={ss['traded']:>4}  "
              f"spot_net={ss['net']:>11,.0f} pf={pf_text(ss['profit_factor']):>5} "
              f"win={ss['win_rate']:.1f}%   "
              f"opt_net={so['net']:>11,.0f} pf={pf_text(so['profit_factor']):>5}")

    write_daywise_csv(rows, args.results_dir / f"{BASE_FILENAME}_{tag}_daywise.csv")
    summary = args.results_dir / f"{BASE_FILENAME}_{tag}_summary.md"
    write_summary(rows, gstats, args, summary, in_range[0], in_range[-1])
    print(f"Summary: {summary}")


if __name__ == "__main__":
    main()
