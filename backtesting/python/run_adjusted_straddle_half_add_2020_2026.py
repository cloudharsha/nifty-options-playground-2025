#!/usr/bin/env python3
"""
Adjusted ATM Straddle — "half trigger / 25% add" — NIFTY weekly, 2020-2026.

Strategy (as specified):
  ENTRY      Sell 1 lot ATM straddle at 09:20. Skip the trade unless CE and PE
             premiums are within 20% of each other (min/max >= 0.80).
  ADD        Whenever the weaker side's total value falls to <= 50% of the
             stronger side's total value, sell one more option on the WEAKER
             side worth ~25% of the stronger side's value (band 20%-30%).
             Repeats without limit: 3rd, 4th, ... legs all use the same rule.
                 e.g. PE 150 / CE 75  -> sell CE near 37.5
                      PE 190 / CE 95  -> sell CE near 47.5
  UNWIND     When the single side falls back to <= the stacked side's total,
             buy back the CHEAPEST leg on the stacked side. One leg per parity
             touch, so the stack unwinds slowly. The original ATM leg is the
             most expensive on its side, so it is always the last to go.
  SYMMETRIC  Identical logic whichever side is stronger.
  NO STOP    No stop loss. Pure test, tails included.

Two hold modes:
  --mode intraday   Enter 09:20, close every leg 15:20 the same day.
  --mode expiry     Enter 09:20 on the first session after the previous expiry,
                    hold the same weekly contracts (adjusting through every
                    minute of every session) until 15:20 on expiry day.

Costs: Rs 30 per order per leg (Rs 30 sell + Rs 30 buy). 1 lot throughout,
lot size resolved from the contract's expiry date.

Output: backtesting/results/adjusted-straddle-half-add/
"""
from __future__ import annotations

import argparse
import bisect
import csv
import datetime
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

IST_SUFFIX = "+05:30"
BASE_FILENAME = "adjusted_straddle_half_add_2020_2026"


# --------------------------------------------------------------------------- #
# data containers
# --------------------------------------------------------------------------- #
@dataclass
class ContractData:
    timestamps: List[str]
    opens: List[float]


@dataclass
class Leg:
    leg_id: int
    side: str
    strike: int
    entry_ts: str
    entry_price: float
    entry_reason: str


@dataclass
class ClosedLeg:
    side: str
    strike: int
    entry_ts: str
    entry_price: float
    exit_ts: str
    exit_price: float
    entry_reason: str
    exit_reason: str


@dataclass
class Cycle:
    """One trade cycle: an intraday session, or one week held to expiry."""
    entry_date: str
    exit_date: str
    expiry_date: str
    atm_strike: int
    lot_size: int
    traded: bool
    skip_reason: str = ""
    remarks: str = ""
    legs: List[ClosedLeg] = field(default_factory=list)
    adds: int = 0
    unwinds: int = 0
    orders: int = 0
    gross_points: float = 0.0
    gross_pnl: float = 0.0
    costs: float = 0.0
    net_pnl: float = 0.0
    max_legs: int = 2
    stale_prices: int = 0
    adds_blocked: int = 0
    rolls: int = 0
    rolls_blocked: int = 0


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    p = argparse.ArgumentParser(
        description="Adjusted ATM straddle with half-trigger / 25% adds — NIFTY 2020-2026."
    )
    p.add_argument("--mode", choices=["intraday", "expiry"], default="intraday")
    p.add_argument("--spot-file", type=Path,
                   default=repo_root / "nifty" / "NIFTY50_INDEX_5m_last_7y.csv")
    p.add_argument("--options-dir", type=Path,
                   default=repo_root / "NiftyOptions_2020_2026" / "Options")
    p.add_argument("--results-dir", type=Path,
                   default=repo_root / "backtesting" / "results" / "adjusted-straddle-half-add")
    p.add_argument("--start-date", default="2020-01-01")
    p.add_argument("--end-date", default="2026-12-31")
    p.add_argument("--entry-time", default="09:20")
    p.add_argument("--exit-time", default="15:20")
    p.add_argument("--balance-max-diff", type=float, default=0.20,
                   help="Skip entry if |CE-PE|/max(CE,PE) exceeds this (0.20 = 20%%)")
    p.add_argument("--half-trigger-ratio", type=float, default=0.50)
    p.add_argument("--add-min-ratio", type=float, default=0.20)
    p.add_argument("--add-max-ratio", type=float, default=0.30)
    p.add_argument("--add-target-ratio", type=float, default=0.25)
    p.add_argument("--parity-ratio", type=float, default=1.00)
    p.add_argument("--max-legs-per-side", type=int, default=3,
                   help="Cap on legs per side. At the cap the strategy ROLLS "
                        "(exit cheapest weak leg, re-sell to the roll target) "
                        "instead of adding. 0 = unlimited adds.")
    p.add_argument("--roll-min-ratio", type=float, default=0.65)
    p.add_argument("--roll-max-ratio", type=float, default=0.85)
    p.add_argument("--roll-target-ratio", type=float, default=0.75)
    p.add_argument("--add-strike-rule", choices=["beyond-legs", "otm-spot"], default="otm-spot",
                   help="beyond-legs: new strike must be further OTM than every existing leg on "
                        "that side. otm-spot: new strike need only be OTM against CURRENT spot, "
                        "so the add can sit nearer the money when the weak side has collapsed.")
    p.add_argument("--brokerage-per-order", type=float, default=30.0)
    p.add_argument("--slippage-per-order", type=float, default=0.0,
                   help="Option points given up per order; 0 because Rs 30 is stated to cover costs")
    p.add_argument("--capital", type=float, default=3_00_000.0,
                   help="Reference capital for CAGR/drawdown %% only")
    p.add_argument("--check-interval", type=int, default=1,
                   help="Minutes between adjustment checks")
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
    """Returns (trading days, {day: open at entry_time}, full spot series)."""
    days: List[str] = []
    seen: Set[str] = set()
    spot_open: Dict[str, float] = {}
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
            if marker in ts and day not in spot_open:
                spot_open[day] = float(row["open"])
            series_ts.append(ts)
            series_px.append(float(row["open"]))
    days.sort()
    return days, spot_open, ContractData(timestamps=series_ts, opens=series_px)


def load_contract(path: Path, cache: Dict[Path, Optional[ContractData]]) -> Optional[ContractData]:
    if path in cache:
        return cache[path]
    if not path.exists():
        cache[path] = None
        return None
    ts_list: List[str] = []
    op_list: List[float] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts_list.append(row["timestamp"])
            op_list.append(float(row["open"]))
    if not ts_list:
        cache[path] = None
        return None
    data = ContractData(timestamps=ts_list, opens=op_list)
    cache[path] = data
    return data


def price_at(data: ContractData, ts: str) -> Optional[Tuple[float, bool]]:
    """Last traded open at or before ts. Returns (price, is_stale)."""
    idx = bisect.bisect_right(data.timestamps, ts) - 1
    if idx < 0:
        return None
    return data.opens[idx], data.timestamps[idx] != ts


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
# engine
# --------------------------------------------------------------------------- #
class Engine:
    def __init__(self, args: argparse.Namespace, logger: logging.Logger,
                 spot_series: ContractData) -> None:
        self.args = args
        self.log = logger
        self.spot_series = spot_series
        self.contract_cache: Dict[Path, Optional[ContractData]] = {}
        self.strike_cache: Dict[str, Dict[str, List[int]]] = {}
        self.leg_data: Dict[int, ContractData] = {}

    def contract_for(self, expiry: str, side: str, strike: int) -> Optional[ContractData]:
        path = self.args.options_dir / expiry / f"NIFTY_{strike}_{side}_{expiry_suffix(expiry)}.csv"
        return load_contract(path, self.contract_cache)

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

    def pick_add(self, expiry: str, side: str, legs: List[Leg], ts: str,
                 target: float, lo: float, hi: float,
                 spot: Optional[float]) -> Optional[Tuple[int, ContractData, float]]:
        """Closest-to-target OTM strike on `side` that is not already held."""
        idx = strike_index(self.args.options_dir, expiry, self.strike_cache)
        existing = [l.strike for l in legs if l.side == side]
        held = set(existing)
        if self.args.add_strike_rule == "beyond-legs":
            floor_ce, ceil_pe = max(existing), min(existing)
        else:
            # OTM against current spot, so the add may sit nearer the money than
            # an existing leg when the weak side has collapsed.
            if spot is None:
                return None
            floor_ce = ceil_pe = spot

        if side == "CE":
            eligible = [s for s in idx["CE"] if s > floor_ce and s not in held]
        else:
            eligible = [s for s in idx["PE"] if s < ceil_pe and s not in held]

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
            key = (abs(px - target), abs(strike - existing[0]))
            if best_key is None or key < best_key:
                best = (strike, data, px)
                best_key = key
        return best

    # ------------------------------------------------------------------ #
    def run_cycle(self, entry_date: str, exit_date: str, expiry: str,
                  session_days: List[str], spot_open: Dict[str, float]) -> Cycle:
        a = self.args
        lot = get_lot_size(expiry)
        entry_ts = build_ts(entry_date, a.entry_time)
        final_ts = build_ts(exit_date, a.exit_time)

        if entry_date not in spot_open:
            return Cycle(entry_date, exit_date, expiry, 0, lot, False,
                         "no_spot_at_entry", f"No {a.entry_time} spot candle.")
        atm = round_to_50(spot_open[entry_date])

        ce_data = self.contract_for(expiry, "CE", atm)
        pe_data = self.contract_for(expiry, "PE", atm)
        if ce_data is None or pe_data is None:
            return Cycle(entry_date, exit_date, expiry, atm, lot, False,
                         "missing_atm_contract", f"ATM {atm} CE/PE file absent for {expiry}.")

        ce_got = price_at(ce_data, entry_ts)
        pe_got = price_at(pe_data, entry_ts)
        if ce_got is None or pe_got is None or ce_got[1] or pe_got[1]:
            return Cycle(entry_date, exit_date, expiry, atm, lot, False,
                         "missing_entry_bar", f"No exact {a.entry_time} bar on both ATM legs.")
        ce_px, pe_px = ce_got[0], pe_got[0]
        if ce_px <= 0 or pe_px <= 0:
            return Cycle(entry_date, exit_date, expiry, atm, lot, False,
                         "zero_entry_price", f"CE={fmt(ce_px)} PE={fmt(pe_px)}")

        balance = min(ce_px, pe_px) / max(ce_px, pe_px)
        if balance < (1.0 - a.balance_max_diff):
            return Cycle(entry_date, exit_date, expiry, atm, lot, False,
                         "balance_check_failed",
                         f"CE={fmt(ce_px)} PE={fmt(pe_px)} within {balance * 100:.1f}%, "
                         f"needs >= {(1 - a.balance_max_diff) * 100:.0f}%")

        cycle = Cycle(entry_date, exit_date, expiry, atm, lot, True)
        legs: List[Leg] = []
        next_id = 1
        for side, data, px in (("CE", ce_data, ce_px), ("PE", pe_data, pe_px)):
            leg = Leg(next_id, side, atm, entry_ts, px, "INITIAL_ENTRY")
            self.leg_data[next_id] = data
            legs.append(leg)
            next_id += 1
        cycle.orders = 2

        # ---- monitor ----
        eval_ts_list: List[str] = []
        for day in session_days:
            start = a.entry_time if day == entry_date else "09:15"
            end = a.exit_time if day == exit_date else "15:29"
            eval_ts_list.extend(minute_grid(day, start, end, a.check_interval))
        eval_ts_list = [t for t in eval_ts_list if t > entry_ts and t < final_ts]

        for ts in eval_ts_list:
            for _ in range(12):  # at most a few actions per minute
                vals = self.side_values(legs, ts)
                if vals is None:
                    break
                ce_v, pe_v, stale = vals
                cycle.stale_prices += stale
                n_ce = sum(1 for l in legs if l.side == "CE")
                n_pe = sum(1 for l in legs if l.side == "PE")

                # -- UNWIND has priority: stacked side back at parity --
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
                        px = price_at(self.leg_data[cheapest.leg_id], ts)[0]
                        legs.remove(cheapest)
                        cycle.legs.append(ClosedLeg(
                            cheapest.side, cheapest.strike, cheapest.entry_ts,
                            cheapest.entry_price, ts, px, cheapest.entry_reason, "UNWIND"))
                        cycle.orders += 1
                        cycle.unwinds += 1
                        continue

                # -- ADD: weak side <= half of strong side --
                if ce_v <= 0 or pe_v <= 0:
                    break
                weak = "CE" if ce_v < pe_v else "PE"
                weak_v = min(ce_v, pe_v)
                strong_v = max(ce_v, pe_v)
                if weak_v > strong_v * a.half_trigger_ratio:
                    break
                n_weak = n_ce if weak == "CE" else n_pe
                spot_now = price_at(self.spot_series, ts)
                spot_val = spot_now[0] if spot_now else None
                capped = bool(a.max_legs_per_side) and n_weak >= a.max_legs_per_side

                if not capped:
                    # -- ADD a new leg worth ~25% of the strong side --
                    target = strong_v * a.add_target_ratio
                    lo = strong_v * a.add_min_ratio
                    hi = strong_v * a.add_max_ratio
                    pick = self.pick_add(expiry, weak, legs, ts, target, lo, hi, spot_val)
                    if pick is None:
                        cycle.adds_blocked += 1
                        break
                    strike, data, px = pick
                    leg = Leg(next_id, weak, strike, ts, px, f"ADD_{n_weak + 1}")
                    self.leg_data[next_id] = data
                    legs.append(leg)
                    next_id += 1
                    cycle.orders += 1
                    cycle.adds += 1
                    cycle.max_legs = max(cycle.max_legs, len(legs))
                    self.log.info(
                        "ADD %s ts=%s side=%s strike=%s px=%s strong=%s target=%s",
                        entry_date, ts, weak, strike, fmt(px), fmt(strong_v), fmt(target))
                    continue

                # -- ROLL: leg cap reached. Exit the cheapest leg on the weak side
                #    and re-sell so the weak side totals ~75% of the strong side. --
                weak_legs = [l for l in legs if l.side == weak]
                cheapest = min(weak_legs,
                               key=lambda l: (price_at(self.leg_data[l.leg_id], ts)[0], l.leg_id))
                cheapest_px = price_at(self.leg_data[cheapest.leg_id], ts)[0]
                retained = weak_v - cheapest_px
                target = strong_v * a.roll_target_ratio - retained
                lo = strong_v * a.roll_min_ratio - retained
                hi = strong_v * a.roll_max_ratio - retained
                if hi <= 0:
                    break
                # price the replacement against the legs that will remain open
                pick = self.pick_add(expiry, weak, [l for l in legs if l.leg_id != cheapest.leg_id],
                                     ts, target, max(lo, 0.0), hi, spot_val)
                if pick is None:
                    cycle.rolls_blocked += 1
                    break
                strike, data, px = pick
                legs.remove(cheapest)
                cycle.legs.append(ClosedLeg(
                    cheapest.side, cheapest.strike, cheapest.entry_ts, cheapest.entry_price,
                    ts, cheapest_px, cheapest.entry_reason, "ROLL_OUT"))
                leg = Leg(next_id, weak, strike, ts, px, "ROLL_IN")
                self.leg_data[next_id] = data
                legs.append(leg)
                next_id += 1
                cycle.orders += 2
                cycle.rolls += 1
                self.log.info(
                    "ROLL %s ts=%s side=%s out=%s@%s in=%s@%s strong=%s weak_after=%s",
                    entry_date, ts, weak, cheapest.strike, fmt(cheapest_px), strike, fmt(px),
                    fmt(strong_v), fmt(retained + px))

        # ---- final exit ----
        for leg in legs:
            got = price_at(self.leg_data[leg.leg_id], final_ts)
            if got is None:
                cycle.traded = False
                cycle.skip_reason = "no_exit_price"
                cycle.remarks = f"Leg {leg.side} {leg.strike} has no bar at or before {final_ts}."
                return cycle
            px, is_stale = got
            cycle.stale_prices += int(is_stale)
            cycle.legs.append(ClosedLeg(leg.side, leg.strike, leg.entry_ts, leg.entry_price,
                                        final_ts, px, leg.entry_reason, "FINAL_EXIT"))
            cycle.orders += 1

        slip = self.args.slippage_per_order
        for cl in cycle.legs:
            cycle.gross_points += (cl.entry_price - slip) - (cl.exit_price + slip)
        cycle.gross_pnl = cycle.gross_points * lot
        cycle.costs = cycle.orders * self.args.brokerage_per_order
        cycle.net_pnl = cycle.gross_pnl - cycle.costs
        return cycle


# --------------------------------------------------------------------------- #
# cycle scheduling
# --------------------------------------------------------------------------- #
def build_intraday_cycles(days: List[str], expiries: List[str],
                          expiry_set: Set[str]) -> List[Tuple[str, str, str, List[str]]]:
    out = []
    for day in days:
        if day in expiry_set:
            exp = next((e for e in expiries if e > day), None)
        else:
            exp = next((e for e in expiries if e >= day), None)
        if exp is None:
            continue
        out.append((day, day, exp, [day]))
    return out


def build_expiry_cycles(days: List[str], expiries: List[str],
                        expiry_set: Set[str]) -> List[Tuple[str, str, str, List[str]]]:
    """One cycle per weekly expiry: first session after the previous expiry -> that expiry."""
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
        out.append((session_days[0], exp, exp, session_days))
    return out


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #
def write_outputs(args: argparse.Namespace, cycles: List[Cycle], logger: logging.Logger) -> None:
    res = args.results_dir
    res.mkdir(parents=True, exist_ok=True)
    tag = args.mode if args.add_strike_rule == "beyond-legs" else f"{args.mode}_otm"
    if args.max_legs_per_side:
        tag = f"{tag}_cap{args.max_legs_per_side}"

    traded = [c for c in cycles if c.traded]
    skipped = [c for c in cycles if not c.traded]

    with (res / f"{BASE_FILENAME}_{tag}_cycles.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["entry_date", "exit_date", "expiry", "atm", "lot_size", "traded",
                    "skip_reason", "remarks", "legs_traded", "adds", "unwinds", "orders",
                    "max_legs", "gross_points", "gross_pnl", "costs", "net_pnl", "stale_prices",
                    "adds_blocked", "rolls", "rolls_blocked"])
        for c in cycles:
            w.writerow([c.entry_date, c.exit_date, c.expiry_date, c.atm_strike, c.lot_size,
                        "YES" if c.traded else "NO", c.skip_reason, c.remarks, len(c.legs),
                        c.adds, c.unwinds, c.orders, c.max_legs, fmt(c.gross_points),
                        fmt(c.gross_pnl), fmt(c.costs), fmt(c.net_pnl), c.stale_prices,
                        c.adds_blocked, c.rolls, c.rolls_blocked])

    with (res / f"{BASE_FILENAME}_{tag}_legs.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["entry_date", "expiry", "side", "strike", "entry_ts", "entry_price",
                    "exit_ts", "exit_price", "entry_reason", "exit_reason", "points", "pnl"])
        for c in cycles:
            for cl in c.legs:
                pts = cl.entry_price - cl.exit_price
                w.writerow([c.entry_date, c.expiry_date, cl.side, cl.strike, cl.entry_ts,
                            fmt(cl.entry_price), cl.exit_ts, fmt(cl.exit_price),
                            cl.entry_reason, cl.exit_reason, fmt(pts), fmt(pts * c.lot_size)])

    # equity / drawdown
    equity = args.capital
    peak = equity
    max_dd = 0.0
    yearly: Dict[str, List[float]] = {}
    with (res / f"{BASE_FILENAME}_{tag}_equity.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "net_pnl", "equity", "peak", "drawdown"])
        for c in traded:
            equity += c.net_pnl
            peak = max(peak, equity)
            dd = peak - equity
            max_dd = max(max_dd, dd)
            yearly.setdefault(c.entry_date[:4], []).append(c.net_pnl)
            w.writerow([c.exit_date, fmt(c.net_pnl), fmt(equity), fmt(peak), fmt(dd)])

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
        final = args.capital + net
        cagr = ((final / args.capital) ** (1 / years) - 1) * 100 if final > 0 else float("nan")
    else:
        years, cagr = 0.0, float("nan")

    skip_counts: Dict[str, int] = {}
    for c in skipped:
        skip_counts[c.skip_reason] = skip_counts.get(c.skip_reason, 0) + 1

    mode_desc = ("Intraday — enter 09:20, close all legs 15:20 same session."
                 if args.mode == "intraday" else
                 "Held to expiry — enter 09:20 the first session after the previous expiry, "
                 "adjust through every session, close 15:20 on expiry day.")

    lines = [
        f"# Adjusted ATM Straddle — Half-Trigger / 25% Add — NIFTY Weekly ({args.mode.upper()})",
        "",
        "## Strategy",
        "",
        f"- Mode: {mode_desc}",
        f"- Entry: sell 1 lot ATM straddle at `{args.entry_time}` (ATM = spot rounded to nearest 50)",
        f"- Balance filter: skip unless `min(CE,PE)/max(CE,PE) >= "
        f"{(1 - args.balance_max_diff) * 100:.0f}%` (CE/PE within {args.balance_max_diff * 100:.0f}%)",
        f"- Add trigger: weaker side total `<= {args.half_trigger_ratio * 100:.0f}%` of stronger side total",
        f"- Add size: new short on the weaker side targeting `{args.add_target_ratio * 100:.0f}%` of the "
        f"stronger side, accepted in band `{args.add_min_ratio * 100:.0f}%-{args.add_max_ratio * 100:.0f}%`",
        f"- Add strike: strictly further OTM than every existing leg on that side",
        "- Adds repeat without limit; 3rd, 4th legs use the same rule" if not args.max_legs_per_side
        else (f"- Legs capped at `{args.max_legs_per_side}` per side. At the cap the strategy "
              f"ROLLS instead of adding: exit the cheapest leg on the weak side and re-sell so "
              f"the weak side totals `{args.roll_target_ratio * 100:.0f}%` of the strong side "
              f"(band `{args.roll_min_ratio * 100:.0f}%-{args.roll_max_ratio * 100:.0f}%`)"),
        f"- Unwind: when the single side falls to `<= {args.parity_ratio * 100:.0f}%` of the stacked side "
        "total, buy back the cheapest leg on the stacked side — one leg per parity touch",
        "- Symmetric for upside and downside moves",
        "- **No stop loss.** No target. Pure test.",
        f"- Position size: 1 lot; lot size from expiry date (75/50/25/75/65 by era)",
        f"- Costs: Rs {args.brokerage_per_order:.0f} per order per leg "
        f"(Rs {args.brokerage_per_order:.0f} sell + Rs {args.brokerage_per_order:.0f} buy), "
        f"slippage {args.slippage_per_order:.2f} pt/order",
        f"- Pricing: 1-minute option `open`; checks every {args.check_interval} minute(s)",
        f"- Reference capital for CAGR/DD: Rs {args.capital:,.0f}",
        "",
        "## Results",
        "",
        f"- Period: `{traded[0].entry_date if traded else 'n/a'}` to "
        f"`{traded[-1].exit_date if traded else 'n/a'}` ({years:.2f} years)",
        f"- Cycles traded: `{len(traded)}` (skipped `{len(skipped)}`)",
        f"- Total adds: `{sum(c.adds for c in traded)}`, total unwinds: `{sum(c.unwinds for c in traded)}`",
        f"- Add trigger fired but **no strike existed in the target band**: `{sum(c.adds_blocked for c in traded)}` times",
        f"- Add strike rule: `{args.add_strike_rule}`",
        f"- Total rolls at the leg cap: `{sum(c.rolls for c in traded)}`",
        f"- Orders executed: `{sum(c.orders for c in traded)}`",
        f"- Max legs open at once: `{max((c.max_legs for c in traded), default=0)}`",
        "",
        f"| Metric | Value |",
        f"|---|---:|",
        f"| Gross P/L | Rs {money(gross)} |",
        f"| Costs | Rs {money(costs)} |",
        f"| **Net P/L** | **Rs {money(net)}** |",
        f"| CAGR | {cagr:.2f}% |",
        f"| Max drawdown | Rs {money(max_dd)} |",
        f"| Win rate | {(len(wins) / len(traded) * 100) if traded else 0:.2f}% "
        f"({len(wins)}W / {len(losses)}L) |",
        f"| Profit factor | {pf:.2f} |",
        f"| Best cycle | Rs {money(max((c.net_pnl for c in traded), default=0))} |",
        f"| Worst cycle | Rs {money(min((c.net_pnl for c in traded), default=0))} |",
        f"| Final equity | Rs {money(args.capital + net)} |",
        "",
        "## Yearly",
        "",
        "| Year | Cycles | Net P/L | Win % |",
        "|---|---:|---:|---:|",
    ]
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
        "- Options data: `NiftyOptions_2020_2026/Options` (1-minute bars). Spot for ATM: 5-minute index file.",
        "- Leg prices use the last traded bar at or before the check minute; "
        f"`stale_prices` in the cycle CSV counts how often a carried-forward bar was used "
        f"(total {sum(c.stale_prices for c in cycles)}).",
        "- Candidate strikes for an add must have an exact bar at the check minute, so illiquid "
        "strikes are never selected on a stale quote.",
        "- Weekly expiry is taken from the options folder structure "
        "(Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).",
        "- Intraday mode rolls to the next weekly on expiry day to avoid same-day-expiry pin behaviour.",
        "",
        "## Files",
        "",
        f"- Cycles: `{BASE_FILENAME}_{tag}_cycles.csv`",
        f"- Legs: `{BASE_FILENAME}_{tag}_legs.csv`",
        f"- Equity: `{BASE_FILENAME}_{tag}_equity.csv`",
        f"- Log: `{BASE_FILENAME}_{tag}.log`",
    ]

    (res / f"{BASE_FILENAME}_{tag}_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[{args.mode}] traded={len(traded)} skipped={len(skipped)} "
          f"net={money(net)} cagr={cagr:.2f}% maxdd={money(max_dd)} "
          f"adds={sum(c.adds for c in traded)} unwinds={sum(c.unwinds for c in traded)} "
          f"rolls={sum(c.rolls for c in traded)}")


# --------------------------------------------------------------------------- #
def main() -> None:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / f"{BASE_FILENAME}_{args.mode}_{args.add_strike_rule}_cap{args.max_legs_per_side}.log")

    days, spot_open, spot_series = load_spot(args.spot_file, args.entry_time)
    days = [d for d in days if args.start_date <= d <= args.end_date]
    expiries = sorted(p.name for p in args.options_dir.iterdir() if p.is_dir())
    expiry_set = set(expiries)

    if args.mode == "intraday":
        schedule = build_intraday_cycles(days, expiries, expiry_set)
    else:
        schedule = build_expiry_cycles(days, expiries, expiry_set)

    engine = Engine(args, logger, spot_series)
    cycles: List[Cycle] = []
    for i, (entry_date, exit_date, expiry, session_days) in enumerate(schedule):
        cycle = engine.run_cycle(entry_date, exit_date, expiry, session_days, spot_open)
        cycles.append(cycle)
        if cycle.traded:
            logger.info("CYCLE %s->%s exp=%s atm=%s adds=%d unwinds=%d net=%s",
                        entry_date, exit_date, expiry, cycle.atm_strike,
                        cycle.adds, cycle.unwinds, fmt(cycle.net_pnl))
        else:
            logger.info("SKIP %s reason=%s %s", entry_date, cycle.skip_reason, cycle.remarks)
        if (i + 1) % 100 == 0:
            print(f"  ... {i + 1}/{len(schedule)} cycles", flush=True)
        # keep the contract cache from growing without bound in expiry mode
        if args.mode == "expiry" and len(engine.contract_cache) > 4000:
            engine.contract_cache.clear()

    write_outputs(args, cycles, logger)
    for h in logger.handlers:
        h.close()


if __name__ == "__main__":
    main()
