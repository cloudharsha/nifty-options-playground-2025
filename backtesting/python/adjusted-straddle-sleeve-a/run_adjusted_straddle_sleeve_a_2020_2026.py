#!/usr/bin/env python3
"""
NIFTY Adjusted Straddle — "Sleeve A" replication spec — weekly, 2020-2026.

One cycle per weekly expiry. No overlap.

  ENTRY   09:20 on the first session after the previous expiry.
          1. Skip the cycle if the PREVIOUS day's India VIX close < 12.
          2. ATM = round(spot / 50) * 50.
          3. Require min(CE,PE) / max(CE,PE) >= 0.80.
          4. If ATM fails, walk out ATM, -50, +50, -100, +100 ... to +/-250 and
             take the first strike that passes; if none passes, skip the cycle.
          5. Both legs must price off an EXACT 09:20 bar (no stale quote).
          6. Sell 1 CE + 1 PE at that strike.

  EVERY MINUTE until exit, up to 12 actions per minute, in this order:

    Step 1  UNWIND (checked first). If the leg counts differ, the side with more
            legs is "stacked". If single_value <= stacked_value * 1.00, buy back
            the CHEAPEST stacked leg.

    Step 2  ADD. If weak_value <= 0.50 * strong_value:
              - weak side has < 4 legs -> sell one new leg, target
                0.20 * strong_value, accepted in band [0.15, 0.25] * strong.
                The strike must be OTM against CURRENT spot, not already held,
                and must have an exact bar this minute. Pick closest to target;
                tie-break by closeness to the original ATM.
              - weak side has 4 legs -> ROLL: buy back the cheapest weak leg and
                sell one so the weak side totals ~0.75 * strong (band 0.65-0.85).

    Step 3  EXIT every leg at 15:20 on expiry day.

  No stop loss. No take profit.

Costs, applied per fill:
  Rs 20 / order  ·  STT sell-side (0.05% -> 0.0625% -> 0.10% -> 0.15% by era)
  exchange 0.03503%  ·  SEBI 0.0001%  ·  stamp 0.003% buy-side
  GST 18% on (brokerage + exchange + SEBI)  ·  0.25 points slippage per side.

Sizing:
  lots = floor(10,00,000 / (spot * lot_size * margin_rate)), fixed at entry,
  non-compounding. Run once at --margin-rate 0.50 and once at 0.19.

Output: backtesting/results/adjusted-straddle-sleeve-a/
"""
from __future__ import annotations

import argparse
import bisect
import csv
import datetime
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

IST_SUFFIX = "+05:30"
BASE_FILENAME = "adjusted_straddle_sleeve_a_2020_2026"


# --------------------------------------------------------------------------- #
# data containers
# --------------------------------------------------------------------------- #
@dataclass
class ContractData:
    timestamps: List[str]
    closes: List[float]


@dataclass
class Leg:
    leg_id: int
    side: str
    strike: int
    entry_ts: str
    entry_price: float      # fill price, slippage already applied
    entry_quote: float      # raw bar close
    entry_reason: str


@dataclass
class ClosedLeg:
    side: str
    strike: int
    entry_ts: str
    entry_price: float
    entry_quote: float
    exit_ts: str
    exit_price: float
    exit_quote: float
    entry_reason: str
    exit_reason: str


@dataclass
class Cycle:
    entry_date: str
    exit_date: str
    expiry_date: str
    atm_strike: int
    lot_size: int
    traded: bool
    skip_reason: str = ""
    remarks: str = ""
    legs: List[ClosedLeg] = field(default_factory=list)
    lots: int = 0
    qty: int = 0
    entry_spot: float = 0.0
    prev_vix: float = float("nan")
    adds: int = 0
    unwinds: int = 0
    rolls: int = 0
    orders: int = 0
    gross_points: float = 0.0
    gross_pnl: float = 0.0
    costs: float = 0.0
    net_pnl: float = 0.0
    max_legs: int = 2
    stale_prices: int = 0
    adds_blocked: int = 0
    rolls_blocked: int = 0
    entry_offset: int = 0
    entry_balance: float = 0.0


# --------------------------------------------------------------------------- #
# static reference data
# --------------------------------------------------------------------------- #
def get_lot_size(expiry_date: str) -> int:
    """NSE NIFTY lot size active on the contract's expiry date."""
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


# STT on the SALE of an option, as a fraction of premium turnover.
# 0.05%    up to  2023-03-31
# 0.0625%  from   2023-04-01  (Finance Act 2023)
# 0.10%    from   2024-10-01  (Finance (No. 2) Act 2024)
# 0.15%    from   2026-04-01
STT_ERAS: List[Tuple[datetime.date, float]] = [
    (datetime.date(2023, 3, 31), 0.000500),
    (datetime.date(2024, 9, 30), 0.000625),
    (datetime.date(2026, 3, 31), 0.001000),
    (datetime.date(9999, 12, 31), 0.001500),
]


def stt_sell_rate(trade_date: str) -> float:
    d = datetime.date.fromisoformat(trade_date)
    for cutoff, rate in STT_ERAS:
        if d <= cutoff:
            return rate
    return STT_ERAS[-1][1]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[3]
    p = argparse.ArgumentParser(
        description="NIFTY adjusted straddle, Sleeve A replication spec, 2020-2026."
    )
    p.add_argument("--spot-file", type=Path,
                   default=repo_root / "nifty" / "NIFTY50_INDEX_5m_last_7y.csv")
    p.add_argument("--options-dir", type=Path,
                   default=repo_root / "NiftyOptions_2020_2026" / "Options")
    p.add_argument("--vix-file", type=Path,
                   default=repo_root / "backtesting" / "data" / "india_vix_daily.csv")
    p.add_argument("--results-dir", type=Path,
                   default=repo_root / "backtesting" / "results" / "adjusted-straddle-sleeve-a")
    p.add_argument("--start-date", default="2020-01-01")
    p.add_argument("--end-date", default="2026-12-31")
    p.add_argument("--entry-time", default="09:20")
    p.add_argument("--exit-time", default="15:20")

    p.add_argument("--vix-floor", type=float, default=12.0,
                   help="Skip the cycle if the previous day's India VIX close is below this. "
                        "0 disables the gate.")
    p.add_argument("--min-balance", type=float, default=0.80,
                   help="Require min(CE,PE)/max(CE,PE) >= this at entry")
    p.add_argument("--strike-search-steps", type=int, default=5,
                   help="Strikes searched either side of ATM, 50 pts each (5 = +/-250)")

    p.add_argument("--half-trigger-ratio", type=float, default=0.50)
    p.add_argument("--add-target-ratio", type=float, default=0.20)
    p.add_argument("--add-min-ratio", type=float, default=0.15)
    p.add_argument("--add-max-ratio", type=float, default=0.25)
    p.add_argument("--parity-ratio", type=float, default=1.00)
    p.add_argument("--max-legs-per-side", type=int, default=4)
    p.add_argument("--roll-target-ratio", type=float, default=0.75)
    p.add_argument("--roll-min-ratio", type=float, default=0.65)
    p.add_argument("--roll-max-ratio", type=float, default=0.85)
    p.add_argument("--actions-per-minute", type=int, default=12)
    p.add_argument("--check-interval", type=int, default=1)

    p.add_argument("--capital", type=float, default=10_00_000.0)
    p.add_argument("--margin-rate", type=float, default=0.50,
                   help="Fraction of contract value assumed held as margin per lot")
    p.add_argument("--brokerage-per-order", type=float, default=20.0)
    p.add_argument("--exchange-rate", type=float, default=0.0003503)
    p.add_argument("--sebi-rate", type=float, default=0.000001)
    p.add_argument("--stamp-rate", type=float, default=0.00003)
    p.add_argument("--gst-rate", type=float, default=0.18)
    p.add_argument("--slippage-points", type=float, default=0.25,
                   help="Option points given up on every fill, each side")
    p.add_argument("--label", default="",
                   help="Extra tag appended to every output filename")
    return p.parse_args()


def fmt(v: float) -> str:
    return f"{v:.2f}"


def money(v: float) -> str:
    return f"{v:,.2f}"


def build_ts(day: str, hhmm: str) -> str:
    return f"{day}T{hhmm}:00{IST_SUFFIX}"


def round_to_50(price: float) -> int:
    rem = price % 50
    base = int(price - rem)
    return base if rem < 25 else base + 50


def expiry_suffix(expiry_date: str) -> str:
    return datetime.datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%d_%b_%y").upper()


def minute_grid(day: str, start_hhmm: str, end_hhmm: str, step: int) -> List[str]:
    sh, sm = (int(x) for x in start_hhmm.split(":"))
    eh, em = (int(x) for x in end_hhmm.split(":"))
    cur = datetime.datetime(2000, 1, 1, sh, sm)
    end = datetime.datetime(2000, 1, 1, eh, em)
    out: List[str] = []
    while cur <= end:
        out.append(build_ts(day, cur.strftime("%H:%M")))
        cur += datetime.timedelta(minutes=step)
    return out


def output_tag(args: argparse.Namespace) -> str:
    """Filename tag encoding every option that changes a run's numbers."""
    tag = f"m{int(round(args.margin_rate * 100)):03d}"
    if args.vix_floor <= 0:
        tag += "_novix"
    elif abs(args.vix_floor - 12.0) > 1e-9:
        tag += f"_vix{args.vix_floor:g}"
    if abs(args.slippage_points - 0.25) > 1e-9:
        tag += f"_slip{args.slippage_points:g}"
    if args.max_legs_per_side != 4:
        tag += f"_cap{args.max_legs_per_side}"
    if args.check_interval != 1:
        tag += f"_ci{args.check_interval}"
    if args.label:
        tag += f"_{args.label}"
    return tag


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger(BASE_FILENAME)
    for h in logger.handlers:
        h.close()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    h = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(h)
    logger.propagate = False
    return logger


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #
def load_spot(spot_file: Path, entry_time: str
              ) -> Tuple[List[str], Dict[str, float], ContractData]:
    """Returns (trading days, {day: close at entry_time}, full spot series)."""
    days: List[str] = []
    seen: Set[str] = set()
    spot_entry: Dict[str, float] = {}
    series_ts: List[str] = []
    series_px: List[float] = []
    marker = f"T{entry_time}:00"
    with spot_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = row["timestamp"]
            day = ts[:10]
            if day not in seen:
                seen.add(day)
                days.append(day)
            if marker in ts and day not in spot_entry:
                spot_entry[day] = float(row["close"])
            series_ts.append(ts)
            series_px.append(float(row["close"]))
    days.sort()
    return days, spot_entry, ContractData(timestamps=series_ts, closes=series_px)


def load_vix(vix_file: Path) -> Tuple[List[str], Dict[str, float]]:
    """Returns (sorted dates, {date: close})."""
    closes: Dict[str, float] = {}
    if not vix_file.exists():
        return [], closes
    with vix_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("close"):
                closes[row["date"]] = float(row["close"])
    return sorted(closes), closes


def load_contract(path: Path, cache: Dict[Path, Optional[ContractData]]) -> Optional[ContractData]:
    if path in cache:
        return cache[path]
    if not path.exists():
        cache[path] = None
        return None
    ts_list: List[str] = []
    cl_list: List[float] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts_list.append(row["timestamp"])
            cl_list.append(float(row["close"]))
    if not ts_list:
        cache[path] = None
        return None
    data = ContractData(timestamps=ts_list, closes=cl_list)
    cache[path] = data
    return data


def price_at(data: ContractData, ts: str) -> Optional[Tuple[float, bool]]:
    """Last close at or before ts. Returns (price, is_stale)."""
    idx = bisect.bisect_right(data.timestamps, ts) - 1
    if idx < 0:
        return None
    return data.closes[idx], data.timestamps[idx] != ts


def strike_index(options_dir: Path, expiry: str,
                 cache: Dict[str, Dict[str, List[int]]]) -> Dict[str, List[int]]:
    if expiry in cache:
        return cache[expiry]
    idx: Dict[str, List[int]] = {"CE": [], "PE": []}
    folder = options_dir / expiry
    if folder.is_dir():
        for f in folder.iterdir():
            parts = f.stem.split("_")
            if len(parts) >= 3 and parts[0] == "NIFTY" and parts[2] in ("CE", "PE"):
                try:
                    idx[parts[2]].append(int(parts[1]))
                except ValueError:
                    continue
    idx["CE"].sort()
    idx["PE"].sort()
    cache[expiry] = idx
    return idx


# --------------------------------------------------------------------------- #
# costs
# --------------------------------------------------------------------------- #
def order_cost(args: argparse.Namespace, fill_price: float, qty: int,
               is_sell: bool, trade_date: str) -> float:
    """Statutory + broker charges on one order, in rupees."""
    turnover = max(fill_price, 0.0) * qty
    brokerage = args.brokerage_per_order
    exchange = args.exchange_rate * turnover
    sebi = args.sebi_rate * turnover
    stt = stt_sell_rate(trade_date) * turnover if is_sell else 0.0
    stamp = 0.0 if is_sell else args.stamp_rate * turnover
    gst = args.gst_rate * (brokerage + exchange + sebi)
    return brokerage + exchange + sebi + stt + stamp + gst


# --------------------------------------------------------------------------- #
# engine
# --------------------------------------------------------------------------- #
class Engine:
    def __init__(self, args: argparse.Namespace, logger: logging.Logger,
                 spot_series: ContractData, vix_dates: List[str],
                 vix_close: Dict[str, float]) -> None:
        self.args = args
        self.log = logger
        self.spot_series = spot_series
        self.vix_dates = vix_dates
        self.vix_close = vix_close
        self.contract_cache: Dict[Path, Optional[ContractData]] = {}
        self.strike_cache: Dict[str, Dict[str, List[int]]] = {}
        self.leg_data: Dict[int, ContractData] = {}

    def contract_for(self, expiry: str, side: str, strike: int) -> Optional[ContractData]:
        path = self.args.options_dir / expiry / f"NIFTY_{strike}_{side}_{expiry_suffix(expiry)}.csv"
        return load_contract(path, self.contract_cache)

    def prev_vix(self, day: str) -> Optional[float]:
        """India VIX close on the last session strictly before `day`."""
        i = bisect.bisect_left(self.vix_dates, day) - 1
        if i < 0:
            return None
        return self.vix_close[self.vix_dates[i]]

    def side_values(self, legs: List[Leg], ts: str) -> Optional[Tuple[float, float, int]]:
        """(ce_total, pe_total, stale_count) or None if any leg is unpriceable."""
        ce = pe = 0.0
        stale = 0
        for leg in legs:
            got = price_at(self.leg_data[leg.leg_id], ts)
            if got is None:
                return None
            px, is_stale = got
            stale += int(is_stale)
            if leg.side == "CE":
                ce += px
            else:
                pe += px
        return ce, pe, stale

    def pick_add(self, expiry: str, side: str, held: Set[int], ts: str,
                 target: float, lo: float, hi: float, spot: float,
                 atm: int) -> Optional[Tuple[int, ContractData, float]]:
        """Closest-to-target strike on `side` that is OTM vs spot and not held.

        Tie-break is closeness to the cycle's original ATM strike.
        """
        idx = strike_index(self.args.options_dir, expiry, self.strike_cache)
        if side == "CE":
            eligible = [s for s in idx["CE"] if s > spot and s not in held]
        else:
            eligible = [s for s in idx["PE"] if s < spot and s not in held]

        best: Optional[Tuple[int, ContractData, float]] = None
        best_key: Optional[Tuple[float, int]] = None
        for strike in eligible:
            data = self.contract_for(expiry, side, strike)
            if data is None:
                continue
            got = price_at(data, ts)
            if got is None:
                continue
            px, is_stale = got
            if is_stale or px <= 0 or not (lo <= px <= hi):
                continue
            key = (abs(px - target), abs(strike - atm))
            if best_key is None or key < best_key:
                best = (strike, data, px)
                best_key = key
        return best

    # ------------------------------------------------------------------ #
    def run_cycle(self, entry_date: str, exit_date: str, expiry: str,
                  session_days: List[str], spot_entry: Dict[str, float]) -> Cycle:
        a = self.args
        lot = get_lot_size(expiry)
        entry_ts = build_ts(entry_date, a.entry_time)
        final_ts = build_ts(exit_date, a.exit_time)

        # -- Step 1 of the entry rules: previous day's India VIX gate --
        pv = self.prev_vix(entry_date)
        if a.vix_floor > 0:
            if pv is None:
                return Cycle(entry_date, exit_date, expiry, 0, lot, False,
                             "no_prev_vix", f"No India VIX close before {entry_date}.")
            if pv < a.vix_floor:
                c = Cycle(entry_date, exit_date, expiry, 0, lot, False,
                          "vix_below_floor",
                          f"Previous day India VIX {pv:.2f} < {a.vix_floor:g}.")
                c.prev_vix = pv
                return c

        if entry_date not in spot_entry:
            c = Cycle(entry_date, exit_date, expiry, 0, lot, False,
                      "no_spot_at_entry", f"No {a.entry_time} spot candle.")
            c.prev_vix = pv if pv is not None else float("nan")
            return c
        spot_px = spot_entry[entry_date]
        atm = round_to_50(spot_px)

        # -- Steps 2-5: walk out from ATM to the first balanced, exactly-priced strike --
        offsets = [0]
        for step in range(1, a.strike_search_steps + 1):
            offsets.extend((-50 * step, 50 * step))

        chosen = None            # (strike, ce_data, pe_data, ce_px, pe_px, balance)
        best_seen = None
        priceable = False
        for off in offsets:
            strike = atm + off
            cd = self.contract_for(expiry, "CE", strike)
            pd_ = self.contract_for(expiry, "PE", strike)
            if cd is None or pd_ is None:
                continue
            cg, pg = price_at(cd, entry_ts), price_at(pd_, entry_ts)
            if cg is None or pg is None:
                continue
            if cg[1] or pg[1]:          # rule 5: exact 09:20 bar on both legs
                continue
            if cg[0] <= 0 or pg[0] <= 0:
                continue
            priceable = True
            bal = min(cg[0], pg[0]) / max(cg[0], pg[0])
            cand = (strike, cd, pd_, cg[0], pg[0], bal)
            if best_seen is None or bal > best_seen[5]:
                best_seen = cand
            if bal >= a.min_balance:
                chosen = cand
                break

        if chosen is None:
            reason = "missing_entry_bar" if not priceable else "balance_check_failed"
            note = (f"No exactly-priced straddle within {a.strike_search_steps} strikes of "
                    f"ATM {atm} at {a.entry_time}." if not priceable else
                    f"Best of {len(offsets)} strikes near ATM {atm} was {best_seen[0]} at "
                    f"{best_seen[5] * 100:.1f}%, needs >= {a.min_balance * 100:.0f}%")
            c = Cycle(entry_date, exit_date, expiry, atm, lot, False, reason, note)
            c.prev_vix = pv if pv is not None else float("nan")
            c.entry_spot = spot_px
            return c

        strike_sel, ce_data, pe_data, ce_px, pe_px, balance = chosen

        # -- sizing: fixed at entry, non-compounding --
        lots = max(1, int(a.capital // (spot_px * lot * a.margin_rate)))
        qty = lots * lot

        cycle = Cycle(entry_date, exit_date, expiry, strike_sel, lot, True)
        cycle.entry_offset = strike_sel - atm
        cycle.entry_balance = balance
        cycle.lots = lots
        cycle.qty = qty
        cycle.entry_spot = spot_px
        cycle.prev_vix = pv if pv is not None else float("nan")
        atm = strike_sel

        slip = a.slippage_points
        legs: List[Leg] = []
        next_id = 1
        for side, data, px in (("CE", ce_data, ce_px), ("PE", pe_data, pe_px)):
            fill = px - slip
            leg = Leg(next_id, side, atm, entry_ts, fill, px, "INITIAL_ENTRY")
            self.leg_data[next_id] = data
            legs.append(leg)
            cycle.costs += order_cost(a, fill, qty, True, entry_date)
            cycle.orders += 1
            next_id += 1

        # -- monitor every minute of every session in the cycle --
        eval_ts_list: List[str] = []
        for day in session_days:
            start = a.entry_time if day == entry_date else "09:15"
            end = a.exit_time if day == exit_date else "15:29"
            eval_ts_list.extend(minute_grid(day, start, end, a.check_interval))
        eval_ts_list = sorted({t for t in eval_ts_list if entry_ts < t < final_ts})

        for ts in eval_ts_list:
            trade_day = ts[:10]
            for _ in range(a.actions_per_minute):
                vals = self.side_values(legs, ts)
                if vals is None:
                    break
                ce_v, pe_v, stale = vals
                cycle.stale_prices += stale
                n_ce = sum(1 for l in legs if l.side == "CE")
                n_pe = sum(1 for l in legs if l.side == "PE")

                # ---- Step 1: UNWIND, checked first ----
                if n_ce != n_pe:
                    stacked = "CE" if n_ce > n_pe else "PE"
                    stacked_v = ce_v if stacked == "CE" else pe_v
                    single_v = pe_v if stacked == "CE" else ce_v
                    if single_v <= stacked_v * a.parity_ratio:
                        stack_legs = [l for l in legs if l.side == stacked]
                        cheapest = min(
                            stack_legs,
                            key=lambda l: (price_at(self.leg_data[l.leg_id], ts)[0], l.leg_id),
                        )
                        quote = price_at(self.leg_data[cheapest.leg_id], ts)[0]
                        fill = quote + slip
                        legs.remove(cheapest)
                        cycle.legs.append(ClosedLeg(
                            cheapest.side, cheapest.strike, cheapest.entry_ts,
                            cheapest.entry_price, cheapest.entry_quote,
                            ts, fill, quote, cheapest.entry_reason, "UNWIND"))
                        cycle.costs += order_cost(a, fill, qty, False, trade_day)
                        cycle.orders += 1
                        cycle.unwinds += 1
                        continue

                # ---- Step 2: ADD / ROLL ----
                if ce_v <= 0 or pe_v <= 0:
                    break
                weak = "CE" if ce_v < pe_v else "PE"
                weak_v = min(ce_v, pe_v)
                strong_v = max(ce_v, pe_v)
                if weak_v > strong_v * a.half_trigger_ratio:
                    break
                n_weak = n_ce if weak == "CE" else n_pe
                spot_now = price_at(self.spot_series, ts)
                if spot_now is None:
                    break
                spot_val = spot_now[0]
                held = {l.strike for l in legs if l.side == weak}

                if n_weak < a.max_legs_per_side:
                    target = strong_v * a.add_target_ratio
                    lo = strong_v * a.add_min_ratio
                    hi = strong_v * a.add_max_ratio
                    pick = self.pick_add(expiry, weak, held, ts, target, lo, hi, spot_val, atm)
                    if pick is None:
                        cycle.adds_blocked += 1
                        break
                    strike, data, quote = pick
                    fill = quote - slip
                    leg = Leg(next_id, weak, strike, ts, fill, quote, f"ADD_{n_weak + 1}")
                    self.leg_data[next_id] = data
                    legs.append(leg)
                    next_id += 1
                    cycle.costs += order_cost(a, fill, qty, True, trade_day)
                    cycle.orders += 1
                    cycle.adds += 1
                    cycle.max_legs = max(cycle.max_legs, len(legs))
                    self.log.info(
                        "ADD %s ts=%s side=%s strike=%s px=%s strong=%s target=%s",
                        entry_date, ts, weak, strike, fmt(quote), fmt(strong_v), fmt(target))
                    continue

                # ---- ROLL: weak side is at the 4-leg cap ----
                weak_legs = [l for l in legs if l.side == weak]
                cheapest = min(weak_legs,
                               key=lambda l: (price_at(self.leg_data[l.leg_id], ts)[0], l.leg_id))
                cheapest_quote = price_at(self.leg_data[cheapest.leg_id], ts)[0]
                retained = weak_v - cheapest_quote
                target = strong_v * a.roll_target_ratio - retained
                lo = strong_v * a.roll_min_ratio - retained
                hi = strong_v * a.roll_max_ratio - retained
                if hi <= 0:
                    break
                pick = self.pick_add(expiry, weak, held - {cheapest.strike}, ts,
                                     target, max(lo, 0.0), hi, spot_val, atm)
                if pick is None:
                    cycle.rolls_blocked += 1
                    break
                strike, data, quote = pick
                out_fill = cheapest_quote + slip
                legs.remove(cheapest)
                cycle.legs.append(ClosedLeg(
                    cheapest.side, cheapest.strike, cheapest.entry_ts, cheapest.entry_price,
                    cheapest.entry_quote, ts, out_fill, cheapest_quote,
                    cheapest.entry_reason, "ROLL_OUT"))
                cycle.costs += order_cost(a, out_fill, qty, False, trade_day)

                in_fill = quote - slip
                leg = Leg(next_id, weak, strike, ts, in_fill, quote, "ROLL_IN")
                self.leg_data[next_id] = data
                legs.append(leg)
                next_id += 1
                cycle.costs += order_cost(a, in_fill, qty, True, trade_day)
                cycle.orders += 2
                cycle.rolls += 1
                self.log.info(
                    "ROLL %s ts=%s side=%s out=%s@%s in=%s@%s strong=%s weak_after=%s",
                    entry_date, ts, weak, cheapest.strike, fmt(cheapest_quote), strike,
                    fmt(quote), fmt(strong_v), fmt(retained + quote))

        # ---- Step 3: final exit ----
        for leg in legs:
            got = price_at(self.leg_data[leg.leg_id], final_ts)
            if got is None:
                cycle.traded = False
                cycle.skip_reason = "no_exit_price"
                cycle.remarks = f"Leg {leg.side} {leg.strike} has no bar at or before {final_ts}."
                return cycle
            quote, is_stale = got
            cycle.stale_prices += int(is_stale)
            fill = quote + slip
            cycle.legs.append(ClosedLeg(leg.side, leg.strike, leg.entry_ts, leg.entry_price,
                                        leg.entry_quote, final_ts, fill, quote,
                                        leg.entry_reason, "FINAL_EXIT"))
            cycle.costs += order_cost(a, fill, qty, False, exit_date)
            cycle.orders += 1

        for cl in cycle.legs:
            cycle.gross_points += cl.entry_price - cl.exit_price
        cycle.gross_pnl = cycle.gross_points * qty
        cycle.net_pnl = cycle.gross_pnl - cycle.costs
        return cycle


# --------------------------------------------------------------------------- #
# cycle scheduling
# --------------------------------------------------------------------------- #
def build_expiry_cycles(days: List[str], expiries: List[str]
                        ) -> List[Tuple[str, str, str, List[str]]]:
    """One cycle per expiry: first session after the previous expiry -> that expiry."""
    out = []
    day_pos = {d: i for i, d in enumerate(days)}
    tradable = [e for e in expiries if e in day_pos]
    for i, exp in enumerate(tradable):
        prev_exp = tradable[i - 1] if i > 0 else None
        start_idx = day_pos[prev_exp] + 1 if prev_exp else 0
        end_idx = day_pos[exp]
        if start_idx > end_idx:
            continue
        session_days = days[start_idx:end_idx + 1]
        out.append((session_days[0], days[end_idx], exp, session_days))
    return out


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #
def sharpe_ratio(returns: List[float], periods_per_year: float) -> float:
    n = len(returns)
    if n < 2:
        return float("nan")
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / (n - 1)
    sd = math.sqrt(var)
    if sd == 0:
        return float("nan")
    return (mean / sd) * math.sqrt(periods_per_year)


def cagr_of(capital: float, net: float, years: float) -> float:
    if years <= 0:
        return float("nan")
    final = capital + net
    if final <= 0:
        return float("nan")
    return ((final / capital) ** (1 / years) - 1) * 100


def write_outputs(args: argparse.Namespace, cycles: List[Cycle], logger: logging.Logger) -> None:
    res = args.results_dir
    res.mkdir(parents=True, exist_ok=True)
    tag = output_tag(args)

    traded = [c for c in cycles if c.traded]
    skipped = [c for c in cycles if not c.traded]

    with (res / f"{BASE_FILENAME}_{tag}_cycles.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["entry_date", "exit_date", "expiry", "atm", "entry_spot", "prev_vix",
                    "lot_size", "lots", "qty", "traded", "skip_reason", "remarks",
                    "legs_traded", "adds", "unwinds", "rolls", "orders", "max_legs",
                    "gross_points", "gross_pnl", "costs", "net_pnl", "stale_prices",
                    "adds_blocked", "rolls_blocked", "entry_offset", "entry_balance"])
        for c in cycles:
            w.writerow([c.entry_date, c.exit_date, c.expiry_date, c.atm_strike,
                        fmt(c.entry_spot), ("" if math.isnan(c.prev_vix) else fmt(c.prev_vix)),
                        c.lot_size, c.lots, c.qty, "YES" if c.traded else "NO",
                        c.skip_reason, c.remarks, len(c.legs), c.adds, c.unwinds, c.rolls,
                        c.orders, c.max_legs, fmt(c.gross_points), fmt(c.gross_pnl),
                        fmt(c.costs), fmt(c.net_pnl), c.stale_prices, c.adds_blocked,
                        c.rolls_blocked, c.entry_offset, fmt(c.entry_balance)])

    with (res / f"{BASE_FILENAME}_{tag}_legs.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["entry_date", "expiry", "side", "strike", "entry_ts", "entry_quote",
                    "entry_fill", "exit_ts", "exit_quote", "exit_fill", "entry_reason",
                    "exit_reason", "points", "pnl"])
        for c in cycles:
            for cl in c.legs:
                pts = cl.entry_price - cl.exit_price
                w.writerow([c.entry_date, c.expiry_date, cl.side, cl.strike, cl.entry_ts,
                            fmt(cl.entry_quote), fmt(cl.entry_price), cl.exit_ts,
                            fmt(cl.exit_quote), fmt(cl.exit_price), cl.entry_reason,
                            cl.exit_reason, fmt(pts), fmt(pts * c.qty)])

    # equity / drawdown, in rupees and as a percentage of the fixed capital base
    equity = args.capital
    peak = equity
    max_dd = 0.0
    max_dd_pct = 0.0
    yearly: Dict[str, List[float]] = {}
    with (res / f"{BASE_FILENAME}_{tag}_equity.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "net_pnl", "equity", "peak", "drawdown", "drawdown_pct"])
        for c in traded:
            equity += c.net_pnl
            peak = max(peak, equity)
            dd = peak - equity
            ddp = dd / peak * 100 if peak > 0 else 0.0
            max_dd = max(max_dd, dd)
            max_dd_pct = max(max_dd_pct, ddp)
            yearly.setdefault(c.entry_date[:4], []).append(c.net_pnl)
            w.writerow([c.exit_date, fmt(c.net_pnl), fmt(equity), fmt(peak), fmt(dd), fmt(ddp)])

    net = sum(c.net_pnl for c in traded)
    gross = sum(c.gross_pnl for c in traded)
    costs = sum(c.costs for c in traded)
    wins = [c for c in traded if c.net_pnl > 0]
    losses = [c for c in traded if c.net_pnl <= 0]
    gp = sum(c.net_pnl for c in wins)
    gl = -sum(c.net_pnl for c in losses)
    pf = (gp / gl) if gl > 0 else float("inf")

    if traded:
        d0 = datetime.date.fromisoformat(traded[0].entry_date)
        d1 = datetime.date.fromisoformat(traded[-1].exit_date)
        years = max((d1 - d0).days / 365.25, 1e-9)
        cagr = cagr_of(args.capital, net, years)
        per_year = len(traded) / years
        sharpe = sharpe_ratio([c.net_pnl / args.capital for c in traded], per_year)
    else:
        years, cagr, sharpe, per_year = 0.0, float("nan"), float("nan"), 0.0

    # equal-thirds sub-period CAGR ("splits")
    splits: List[Tuple[str, str, int, float, float]] = []
    if traded:
        n = len(traded)
        bounds = [(0, n // 3), (n // 3, 2 * n // 3), (2 * n // 3, n)]
        for lo, hi in bounds:
            chunk = traded[lo:hi]
            if not chunk:
                continue
            s0 = datetime.date.fromisoformat(chunk[0].entry_date)
            s1 = datetime.date.fromisoformat(chunk[-1].exit_date)
            yrs = max((s1 - s0).days / 365.25, 1e-9)
            sub_net = sum(c.net_pnl for c in chunk)
            splits.append((chunk[0].entry_date, chunk[-1].exit_date, len(chunk),
                           sub_net, cagr_of(args.capital, sub_net, yrs)))

    skip_counts: Dict[str, int] = {}
    for c in skipped:
        skip_counts[c.skip_reason] = skip_counts.get(c.skip_reason, 0) + 1

    avg_lots = sum(c.lots for c in traded) / len(traded) if traded else 0.0

    lines = [
        f"# NIFTY Adjusted Straddle — Sleeve A replication (margin {args.margin_rate:.2f})",
        "",
        "## Strategy",
        "",
        "- One cycle per weekly expiry, no overlap. Entry is the first session after the "
        "previous expiry; exit is expiry day.",
        f"- **Entry {args.entry_time}:** skip if the previous day's India VIX close < "
        f"`{args.vix_floor:g}`; ATM = `round(spot/50)*50`; require "
        f"`min(CE,PE)/max(CE,PE) >= {args.min_balance:.2f}`; if ATM fails, walk out "
        f"`ATM, -50, +50, ... +/-{args.strike_search_steps * 50}` and take the first strike "
        "that passes, else skip the cycle. Both legs must price off an exact "
        f"`{args.entry_time}` bar. Sell 1 CE + 1 PE.",
        f"- **Every minute**, up to `{args.actions_per_minute}` actions per minute, in order:",
        f"  1. **Unwind** — if the leg counts differ and "
        f"`single <= stacked * {args.parity_ratio:.2f}`, buy back the cheapest stacked leg.",
        f"  2. **Add** — if `weak <= {args.half_trigger_ratio:.2f} * strong`: with "
        f"`< {args.max_legs_per_side}` legs on the weak side, sell one new leg targeting "
        f"`{args.add_target_ratio:.2f} * strong` "
        f"(band `{args.add_min_ratio:.2f}`-`{args.add_max_ratio:.2f}`), OTM against current "
        "spot, not already held, exact bar this minute, closest to target with the original "
        f"ATM as tie-break. At `{args.max_legs_per_side}` legs, **roll** instead: buy back "
        f"the cheapest weak leg and sell so the weak side totals "
        f"`{args.roll_target_ratio:.2f} * strong` "
        f"(band `{args.roll_min_ratio:.2f}`-`{args.roll_max_ratio:.2f}`).",
        f"  3. **Exit** every leg at `{args.exit_time}` on expiry day.",
        "- **No stop loss. No take profit.**",
        "",
        "## Sizing and costs",
        "",
        f"- `lots = floor({args.capital:,.0f} / (spot x lot_size x {args.margin_rate:.2f}))`, "
        f"fixed at entry, non-compounding. Mean lots per cycle: `{avg_lots:.2f}`.",
        "- Lot size from the contract's expiry date (75 / 50 / 25 / 75 / 65 by era).",
        f"- Costs per order: Rs {args.brokerage_per_order:.0f} brokerage; STT "
        "`0.05% -> 0.0625% (2023-04-01) -> 0.10% (2024-10-01) -> 0.15% (2026-04-01)` on "
        f"sell-side premium; exchange `{args.exchange_rate * 100:.5f}%`; SEBI "
        f"`{args.sebi_rate * 100:.4f}%`; stamp `{args.stamp_rate * 100:.3f}%` buy-side; "
        f"GST `{args.gst_rate * 100:.0f}%` on brokerage + exchange + SEBI.",
        f"- Slippage `{args.slippage_points:.2f}` points per side on every fill.",
        "",
        "## Results",
        "",
        f"- Period: `{traded[0].entry_date if traded else 'n/a'}` to "
        f"`{traded[-1].exit_date if traded else 'n/a'}` ({years:.2f} years)",
        f"- Cycles traded: `{len(traded)}` (skipped `{len(skipped)}` of `{len(cycles)}`)",
        f"- Adds `{sum(c.adds for c in traded)}` · unwinds "
        f"`{sum(c.unwinds for c in traded)}` · rolls `{sum(c.rolls for c in traded)}`",
        f"- Minute-checks where the add trigger was live but no strike sat in the target "
        f"band: `{sum(c.adds_blocked for c in traded)}` (the trigger stays live until a "
        f"strike qualifies, so this counts minutes, not distinct events); same for rolls: "
        f"`{sum(c.rolls_blocked for c in traded)}`",
        f"- Orders executed: `{sum(c.orders for c in traded)}`",
        f"- Max legs open at once: `{max((c.max_legs for c in traded), default=0)}`",
        f"- Entries away from ATM: `{sum(1 for c in traded if c.entry_offset)}` of "
        f"`{len(traded)}`",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Gross P/L | Rs {money(gross)} |",
        f"| Costs | Rs {money(costs)} |",
        f"| **Net P/L** | **Rs {money(net)}** |",
        f"| CAGR | {cagr:.2f}% |",
        f"| Sharpe | {sharpe:.2f} |",
        f"| Max drawdown | Rs {money(max_dd)} ({max_dd_pct:.2f}%) |",
        f"| Profit factor | {pf:.2f} |",
        f"| Win rate | {(len(wins) / len(traded) * 100) if traded else 0:.2f}% "
        f"({len(wins)}W / {len(losses)}L) |",
        f"| Best cycle | Rs {money(max((c.net_pnl for c in traded), default=0))} |",
        f"| Worst cycle | Rs {money(min((c.net_pnl for c in traded), default=0))} |",
        f"| Final equity | Rs {money(args.capital + net)} |",
        "",
        "## Splits (equal thirds of the traded cycles)",
        "",
        "| Segment | From | To | Cycles | Net P/L | CAGR |",
        "|---|---|---|---:|---:|---:|",
    ]
    for i, (s0, s1, cnt, sub_net, sub_cagr) in enumerate(splits, 1):
        lines.append(f"| {i} | {s0} | {s1} | {cnt} | Rs {money(sub_net)} | {sub_cagr:.2f}% |")

    lines += ["", "## Yearly", "", "| Year | Cycles | Net P/L | Win % |", "|---|---:|---:|---:|"]
    for yr in sorted(yearly):
        vals = yearly[yr]
        w_ = sum(1 for v in vals if v > 0)
        lines.append(f"| {yr} | {len(vals)} | Rs {money(sum(vals))} | {w_ / len(vals) * 100:.1f}% |")

    lines += ["", "## Skips", "", "| Reason | Count |", "|---|---:|"]
    for reason, cnt in sorted(skip_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{reason}` | {cnt} |")

    lines += [
        "",
        "## Notes",
        "",
        "- Option prices are the 1-minute bar **close**; a leg already open is marked at the "
        "last close at or before the check minute. `stale_prices` in the cycle CSV counts how "
        f"often a carried-forward bar was used (total {sum(c.stale_prices for c in cycles)}).",
        "- A candidate strike for an add or roll must have an **exact** bar at the check "
        "minute, so an illiquid strike is never sold on a stale quote.",
        "- Spot is the 5-minute index close (the repo has no 1-minute spot before 2025), used "
        "for the entry ATM and for the OTM test on adds.",
        "- India VIX is the daily close from `backtesting/data/india_vix_daily.csv`; the gate "
        "reads the last session strictly before the entry date.",
        f"- Sharpe is computed on per-cycle returns over the fixed Rs {args.capital:,.0f} base, "
        f"annualised by sqrt({per_year:.1f}) cycles/year, with a zero risk-free rate.",
        "- Weekly expiry comes from the options folder structure (Thursday to Aug 2025, "
        "Tuesday from Sep 2025, holiday-shifted).",
        "",
        "## Files",
        "",
        f"- Cycles: `{BASE_FILENAME}_{tag}_cycles.csv`",
        f"- Legs: `{BASE_FILENAME}_{tag}_legs.csv`",
        f"- Equity: `{BASE_FILENAME}_{tag}_equity.csv`",
    ]

    (res / f"{BASE_FILENAME}_{tag}_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[margin {args.margin_rate:.2f}] traded={len(traded)} skipped={len(skipped)} "
          f"net={money(net)} cagr={cagr:.2f}% sharpe={sharpe:.2f} "
          f"dd={max_dd_pct:.2f}% pf={pf:.2f} "
          f"wr={(len(wins) / len(traded) * 100) if traded else 0:.2f}% "
          f"adds={sum(c.adds for c in traded)} unwinds={sum(c.unwinds for c in traded)} "
          f"rolls={sum(c.rolls for c in traded)}")


# --------------------------------------------------------------------------- #
def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / f"{BASE_FILENAME}_{output_tag(args)}.log")

    days, spot_entry, spot_series = load_spot(args.spot_file, args.entry_time)
    days = [d for d in days if args.start_date <= d <= args.end_date]
    vix_dates, vix_close = load_vix(args.vix_file)
    if args.vix_floor > 0 and not vix_dates:
        raise SystemExit(f"VIX gate is on but no data at {args.vix_file}. "
                         f"Pass --vix-floor 0 to disable it.")

    expiries = sorted(p.name for p in args.options_dir.iterdir() if p.is_dir())
    schedule = build_expiry_cycles(days, expiries)

    engine = Engine(args, logger, spot_series, vix_dates, vix_close)
    cycles: List[Cycle] = []
    for i, (entry_date, exit_date, expiry, session_days) in enumerate(schedule):
        cycle = engine.run_cycle(entry_date, exit_date, expiry, session_days, spot_entry)
        cycles.append(cycle)
        if cycle.traded:
            logger.info("CYCLE %s->%s exp=%s atm=%s lots=%d adds=%d unwinds=%d rolls=%d net=%s",
                        entry_date, exit_date, expiry, cycle.atm_strike, cycle.lots,
                        cycle.adds, cycle.unwinds, cycle.rolls, fmt(cycle.net_pnl))
        else:
            logger.info("SKIP %s reason=%s %s", entry_date, cycle.skip_reason, cycle.remarks)
        if (i + 1) % 50 == 0:
            print(f"  ... {i + 1}/{len(schedule)} cycles", flush=True)
        if len(engine.contract_cache) > 4000:
            engine.contract_cache.clear()

    write_outputs(args, cycles, logger)
    for h in logger.handlers:
        h.close()


if __name__ == "__main__":
    main()
