#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
import math
import re
from bisect import bisect_right
from collections import Counter
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Dict, List, Optional, Tuple


IST_SUFFIX = "+05:30"
BASE_FILENAME = "combined_expiry_adjusting_strangle_2025"
EXPIRY_TRADES_FILENAME = f"{BASE_FILENAME}_expiry_trades.csv"
ADJUST_CYCLES_FILENAME = f"{BASE_FILENAME}_adjust_cycles.csv"
EVENTS_FILENAME = f"{BASE_FILENAME}_events.csv"
EQUITY_FILENAME = f"{BASE_FILENAME}_equity.csv"
SUMMARY_CSV_FILENAME = f"{BASE_FILENAME}_summary.csv"
SUMMARY_MD_FILENAME = f"{BASE_FILENAME}_summary.md"
LOG_FILENAME = f"{BASE_FILENAME}.log"


@dataclass
class PriceRow:
    timestamp: str
    open_value: float
    open_text: str
    high_value: float
    high_text: str
    low_value: float
    low_text: str
    close_value: float
    close_text: str


@dataclass
class SpotData:
    rows_by_timestamp: Dict[str, PriceRow]
    rows_by_day: Dict[str, List[PriceRow]]
    timestamps_by_day: Dict[str, List[str]]
    trading_days: List[str]


@dataclass
class ContractData:
    path: Path
    rows_by_timestamp: Dict[str, PriceRow]
    ordered_rows: List[PriceRow]
    timestamps: List[str]

    def row_at_or_before(self, timestamp: str) -> Optional[PriceRow]:
        index = bisect_right(self.timestamps, timestamp) - 1
        if index < 0:
            return None
        return self.ordered_rows[index]


@dataclass
class LegEvent:
    strategy: str = ""
    cycle_id: int = 0
    pos_id: int = 0
    leg_no: int = 0
    trade_date: str = ""
    expiry: str = ""
    side: str = ""
    sell_strike: int = 0
    sell_time: str = ""
    sell_price: float = 0.0
    buy_time: str = ""
    buy_price: float = 0.0
    spot_at_open: float = 0.0
    spot_at_close: float = 0.0
    tp_points: float = 0.0
    sl_price: float = 0.0
    lots: int = 0
    lot_size: int = 0
    units: int = 0
    gross_pnl: float = 0.0
    charges: float = 0.0
    net_pnl: float = 0.0
    open_reason: str = ""
    close_reason: str = ""


@dataclass
class ExpiryTrade:
    trade_no: int = 0
    expiry: str = ""
    trade_date: str = ""
    status: str = ""
    skip_reason: str = ""
    capital_at_entry: float = 0.0
    spot_at_entry: float = 0.0
    spot_at_close: float = 0.0
    atm: int = 0
    lot_size: int = 0
    lots_per_leg: int = 0
    units_per_leg: int = 0
    margin_rate: float = 0.0
    margin_used: float = 0.0
    ce_strike: int = 0
    pe_strike: int = 0
    ce_entry_price: float = 0.0
    ce_exit_price: float = 0.0
    ce_exit_reason: str = ""
    pe_entry_price: float = 0.0
    pe_exit_price: float = 0.0
    pe_exit_reason: str = ""
    total_premium_points: float = 0.0
    gross_pnl: float = 0.0
    total_charges: float = 0.0
    net_pnl: float = 0.0
    remarks: str = ""


@dataclass
class AdjustCycle:
    cycle_no: int = 0
    period_start: str = ""
    period_end: str = ""
    expiry: str = ""
    status: str = ""
    skip_reason: str = ""
    capital_at_entry: float = 0.0
    spot_at_start: float = 0.0
    spot_at_end: float = 0.0
    lots: int = 0
    lot_size: int = 0
    margin_rate: float = 0.0
    margin_used: float = 0.0
    n_positions: int = 0
    n_intraday_adj: int = 0
    n_eod_adj: int = 0
    n_legs: int = 0
    net_points: float = 0.0
    gross_pnl: float = 0.0
    total_charges: float = 0.0
    net_pnl: float = 0.0
    remarks: str = ""


@dataclass
class EquityRow:
    date: str
    source: str
    ref: int
    expiry: str
    status: str
    net_pnl: float
    gross_pnl: float
    charges: float
    cum_pnl: float
    equity: float
    note: str


@dataclass
class LegState:
    leg_id: int
    side: str
    strike: int
    sell_prem: float
    sell_timestamp: str
    open_reason: str
    open: bool = True
    buy_prem: float = 0.0
    buy_timestamp: str = ""
    close_reason: str = ""

    def realised_points(self) -> float:
        if self.open:
            return 0.0
        return self.sell_prem - self.buy_prem


@dataclass
class Position:
    pos_id: int
    open_timestamp: str
    spot_at_open: float
    open_reason: str
    legs: List[LegState] = field(default_factory=list)
    ce_active_id: int = -1
    pe_active_id: int = -1
    tp_points: float = 0.0
    initial_total_premium: float = 0.0
    n_intraday_adj: int = 0
    n_eod_adj: int = 0
    close_timestamp: str = ""
    spot_at_close: float = 0.0
    close_reason: str = ""


class RepoChain:
    def __init__(self, options_dir: Path, expiries: List[str]) -> None:
        self.options_dir = options_dir
        self.expiries = expiries
        self.contract_cache: Dict[Path, ContractData] = {}
        self.row_cache: Dict[Tuple[Path, str], Optional[PriceRow]] = {}
        self.strikes_by_exp_side: Dict[Tuple[str, str], List[int]] = {}
        self._index_strikes()

    def _index_strikes(self) -> None:
        pattern = re.compile(r"^NIFTY_(\d+)_(CE|PE)_[A-Z0-9_]+\.csv$")
        for expiry in self.expiries:
            ce_strikes: List[int] = []
            pe_strikes: List[int] = []
            expiry_dir = self.options_dir / expiry
            if not expiry_dir.is_dir():
                continue
            for contract_path in expiry_dir.iterdir():
                if not contract_path.is_file():
                    continue
                match = pattern.match(contract_path.name)
                if not match:
                    continue
                strike = int(match.group(1))
                side = match.group(2)
                if side == "CE":
                    ce_strikes.append(strike)
                else:
                    pe_strikes.append(strike)
            self.strikes_by_exp_side[(expiry, "CE")] = sorted(set(ce_strikes))
            self.strikes_by_exp_side[(expiry, "PE")] = sorted(set(pe_strikes))

    def strikes_for(self, expiry: str, side: str) -> List[int]:
        return self.strikes_by_exp_side.get((expiry, side), [])

    def path_for(self, expiry: str, side: str, strike: int) -> Path:
        suffix = expiry_suffix(expiry)
        return self.options_dir / expiry / f"NIFTY_{strike}_{side}_{suffix}.csv"

    def load_contract(self, expiry: str, side: str, strike: int) -> Optional[ContractData]:
        contract_path = self.path_for(expiry, side, strike)
        if contract_path in self.contract_cache:
            return self.contract_cache[contract_path]
        if not contract_path.exists():
            return None

        rows_by_timestamp: Dict[str, PriceRow] = {}
        ordered_rows: List[PriceRow] = []
        with contract_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                price_row = price_row_from_csv(row)
                rows_by_timestamp[price_row.timestamp] = price_row
                ordered_rows.append(price_row)

        ordered_rows.sort(key=lambda row: row.timestamp)
        contract_data = ContractData(
            path=contract_path,
            rows_by_timestamp=rows_by_timestamp,
            ordered_rows=ordered_rows,
            timestamps=[row.timestamp for row in ordered_rows],
        )
        self.contract_cache[contract_path] = contract_data
        return contract_data

    def row_at_or_before(self, expiry: str, side: str, strike: int, timestamp: str) -> Optional[PriceRow]:
        contract_path = self.path_for(expiry, side, strike)
        loaded = self.contract_cache.get(contract_path)
        if loaded is not None:
            return loaded.row_at_or_before(timestamp)

        key = (contract_path, timestamp)
        if key in self.row_cache:
            return self.row_cache[key]
        if not contract_path.exists():
            self.row_cache[key] = None
            return None

        latest: Optional[PriceRow] = None
        with contract_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                row_timestamp = row["timestamp"]
                if row_timestamp > timestamp:
                    break
                latest = price_row_from_csv(row)
        self.row_cache[key] = latest
        return latest

    def price_at(
        self,
        expiry: str,
        side: str,
        strike: int,
        timestamp: str,
        min_premium: float,
        max_premium: float,
    ) -> Optional[Tuple[float, PriceRow]]:
        contract_data = self.load_contract(expiry, side, strike)
        if contract_data is None:
            return None
        row = contract_data.row_at_or_before(timestamp)
        if row is None:
            return None
        price = row.close_value
        if not (min_premium <= price <= max_premium):
            return None
        return price, row

    def candidate_price_at(
        self,
        expiry: str,
        side: str,
        strike: int,
        timestamp: str,
        min_premium: float,
        max_premium: float,
    ) -> Optional[Tuple[float, PriceRow]]:
        contract_data = self.load_contract(expiry, side, strike)
        if contract_data is None:
            return None
        row = contract_data.row_at_or_before(timestamp)
        if row is None:
            return None
        price = row.close_value
        if not (min_premium <= price <= max_premium):
            return None
        return price, row

    def clear_caches(self) -> None:
        self.contract_cache.clear()
        self.row_cache.clear()

    def nearest_strike(self, target: int, expiry: str, side: str) -> Optional[int]:
        strikes = self.strikes_for(expiry, side)
        if not strikes:
            return None
        return min(strikes, key=lambda strike: abs(strike - target))

    def find_entry_strike(
        self,
        expiry: str,
        side: str,
        timestamp: str,
        spot: float,
        premium_min: float,
        premium_max: float,
        min_otm_points: float,
        min_premium: float,
        max_premium: float,
    ) -> Optional[Tuple[int, float]]:
        strikes = self.strikes_for(expiry, side)
        if not strikes:
            return None
        target = (premium_min + premium_max) / 2.0
        best: Optional[Tuple[int, float, Tuple[float, float, int]]] = None
        for strike in strikes:
            if side == "CE" and strike < spot + min_otm_points:
                continue
            if side == "PE" and strike > spot - min_otm_points:
                continue
            price_row = self.candidate_price_at(expiry, side, strike, timestamp, min_premium, max_premium)
            if price_row is None:
                continue
            price, _ = price_row
            if not (premium_min <= price <= premium_max):
                continue
            tie_break = strike if side == "CE" else -strike
            key = (abs(price - target), abs(strike - spot), tie_break)
            if best is None or key < best[2]:
                best = (strike, price, key)
        return (best[0], best[1]) if best else None

    def find_roll_strike(
        self,
        expiry: str,
        side: str,
        timestamp: str,
        atm: int,
        premium_min: float,
        premium_max: float,
        old_strike: int,
        opposite_strike: int,
        min_premium: float,
        max_premium: float,
    ) -> Optional[Tuple[int, float]]:
        strikes = self.strikes_for(expiry, side)
        if not strikes:
            return None
        old_distance = abs(old_strike - atm)
        best: Optional[Tuple[int, float, Tuple[int, float]]] = None
        for strike in strikes:
            if side == "CE" and strike <= opposite_strike:
                continue
            if side == "PE" and strike >= opposite_strike:
                continue
            new_distance = abs(strike - atm)
            if new_distance >= old_distance:
                continue
            price_row = self.candidate_price_at(expiry, side, strike, timestamp, min_premium, max_premium)
            if price_row is None:
                continue
            price, _ = price_row
            if not (premium_min <= price <= premium_max):
                continue
            key = (new_distance, -price)
            if best is None or key < best[2]:
                best = (strike, price, key)
        return (best[0], best[1]) if best else None


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Backtest the 2025 combined expiry-day short strangle and inter-expiry adjusting strangle.",
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
    parser.add_argument("--exp-entry-time", default="09:20")
    parser.add_argument("--exp-exit-time", default="15:25")
    parser.add_argument("--exp-strike-dist", type=int, default=100)
    parser.add_argument("--exp-sl-mult", type=float, default=2.0)
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
        (args.exp_entry_time, "--exp-entry-time"),
        (args.exp_exit_time, "--exp-exit-time"),
        (args.adj_entry_time, "--adj-entry-time"),
        (args.adj_eod_time, "--adj-eod-time"),
    ]:
        validate_time(parser, time_value, name)
    if args.capital <= 0:
        parser.error("--capital must be positive")
    if args.compound_min_capital <= 0:
        parser.error("--compound-min-capital must be positive")
    if args.lot_size <= 0:
        parser.error("--lot-size must be positive")
    if args.margin_rate <= 0:
        parser.error("--margin-rate must be positive")
    if args.exp_sl_mult <= 1:
        parser.error("--exp-sl-mult must be greater than 1")
    if args.min_premium < 0 or args.max_premium < args.min_premium:
        parser.error("--min-premium and --max-premium define an invalid premium range")
    return args


def validate_time(parser: argparse.ArgumentParser, value: str, name: str) -> None:
    parts = value.split(":")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        parser.error(f"{name} must be HH:MM")
    hour, minute = (int(part) for part in parts)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        parser.error(f"{name} must be HH:MM")


def build_timestamp(day: str, time_text: str) -> str:
    hour, minute = time_text.split(":")
    return f"{day}T{hour}:{minute}:00{IST_SUFFIX}"


def timestamp_date(timestamp: str) -> str:
    return timestamp[:10]


def timestamp_time(timestamp: str) -> str:
    return timestamp[11:16]


def date_from_text(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def format_number(value: float) -> str:
    return f"{value:.2f}"


def round_to_gap(price: float, gap: int) -> int:
    return int(round(price / gap) * gap)


def expiry_suffix(expiry_date: str) -> str:
    expiry_dt = dt.datetime.strptime(expiry_date, "%Y-%m-%d")
    return expiry_dt.strftime("%d_%b_%y").upper()


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


def price_row_from_csv(row: Dict[str, str]) -> PriceRow:
    return PriceRow(
        timestamp=row["timestamp"],
        open_value=float(row["open"]),
        open_text=row["open"],
        high_value=float(row["high"]),
        high_text=row["high"],
        low_value=float(row["low"]),
        low_text=row["low"],
        close_value=float(row["close"]),
        close_text=row["close"],
    )


def load_spot_data(spot_file: Path) -> SpotData:
    rows_by_timestamp: Dict[str, PriceRow] = {}
    rows_by_day: Dict[str, List[PriceRow]] = {}
    timestamps_by_day: Dict[str, List[str]] = {}
    trading_days: List[str] = []

    with spot_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = row["timestamp"]
            if not timestamp.startswith("2025-"):
                continue
            day = timestamp_date(timestamp)
            price_row = price_row_from_csv(row)
            rows_by_timestamp[timestamp] = price_row
            if day not in rows_by_day:
                rows_by_day[day] = []
                timestamps_by_day[day] = []
                trading_days.append(day)
            rows_by_day[day].append(price_row)
            timestamps_by_day[day].append(timestamp)

    for day in trading_days:
        rows_by_day[day].sort(key=lambda price_row: price_row.timestamp)
        timestamps_by_day[day] = [price_row.timestamp for price_row in rows_by_day[day]]

    return SpotData(
        rows_by_timestamp=rows_by_timestamp,
        rows_by_day=rows_by_day,
        timestamps_by_day=timestamps_by_day,
        trading_days=trading_days,
    )


def load_expiry_folders(options_dir: Path) -> List[str]:
    return sorted(path.name for path in options_dir.iterdir() if path.is_dir() and path.name.startswith("2025-"))


def spot_row_at_or_before(spot_data: SpotData, day: str, timestamp: str) -> Optional[PriceRow]:
    timestamps = spot_data.timestamps_by_day.get(day, [])
    index = bisect_right(timestamps, timestamp) - 1
    if index < 0:
        return None
    return spot_data.rows_by_day[day][index]


def spot_window_rows(spot_data: SpotData, start_day: str, end_day: str) -> List[PriceRow]:
    rows: List[PriceRow] = []
    for day in spot_data.trading_days:
        if day < start_day:
            continue
        if day > end_day:
            break
        rows.extend(spot_data.rows_by_day.get(day, []))
    return rows


def row_at_or_before_in_window(rows: List[PriceRow], timestamps: List[str], timestamp: str) -> Optional[PriceRow]:
    index = bisect_right(timestamps, timestamp) - 1
    if index < 0:
        return None
    return rows[index]


def capital_for_sizing(args: argparse.Namespace, running_pnl: float) -> float:
    if not args.compound:
        return args.capital
    return max(args.capital + running_pnl, args.compound_min_capital)


def lots_for(spot: float, args: argparse.Namespace, capital: float) -> int:
    margin_per_lot = spot * args.lot_size * args.margin_rate
    if margin_per_lot <= 0:
        return 1
    return max(1, int(capital // margin_per_lot))


def order_charges(sell_value: float, buy_value: float, args: argparse.Namespace) -> float:
    brokerage = 2 * args.brokerage_per_order
    stt = args.stt_sell_rate * sell_value
    exchange = args.exchange_txn_rate * (sell_value + buy_value)
    sebi = args.sebi_rate * (sell_value + buy_value)
    stamp = args.stamp_buy_rate * buy_value
    gst = args.gst_rate * (brokerage + exchange + sebi)
    return brokerage + stt + exchange + sebi + stamp + gst


def premium_band(spot: float, args: argparse.Namespace, *, reentry: bool = False) -> Tuple[float, float, float]:
    if reentry:
        min_pct = args.adj_re_prem_min_pct
        max_pct = args.adj_re_prem_max_pct
    else:
        min_pct = args.adj_prem_min_pct
        max_pct = args.adj_prem_max_pct
    return (
        round(min_pct * spot, 2),
        round(max_pct * spot, 2),
        round(args.adj_min_otm_pct * spot, 0),
    )


def active_legs(position: Position) -> Tuple[LegState, LegState]:
    ce_leg = next(leg for leg in position.legs if leg.leg_id == position.ce_active_id)
    pe_leg = next(leg for leg in position.legs if leg.leg_id == position.pe_active_id)
    return ce_leg, pe_leg


def position_net_points(position: Position, ce_price: float, pe_price: float) -> float:
    realised = sum(leg.realised_points() for leg in position.legs if not leg.open)
    ce_leg, pe_leg = active_legs(position)
    return realised + (ce_leg.sell_prem - ce_price) + (pe_leg.sell_prem - pe_price)


def open_adjust_position(
    chain: RepoChain,
    expiry: str,
    timestamp: str,
    spot: float,
    premium_min: float,
    premium_max: float,
    min_otm: float,
    reason: str,
    leg_counter: List[int],
    positions: List[Position],
    args: argparse.Namespace,
) -> Optional[Position]:
    ce_pick = chain.find_entry_strike(
        expiry,
        "CE",
        timestamp,
        spot,
        premium_min,
        premium_max,
        min_otm,
        args.min_premium,
        args.max_premium,
    )
    pe_pick = chain.find_entry_strike(
        expiry,
        "PE",
        timestamp,
        spot,
        premium_min,
        premium_max,
        min_otm,
        args.min_premium,
        args.max_premium,
    )
    if ce_pick is None or pe_pick is None:
        return None

    ce_strike, ce_premium = ce_pick
    pe_strike, pe_premium = pe_pick
    if ce_strike <= pe_strike:
        return None

    position = Position(
        pos_id=len(positions) + 1,
        open_timestamp=timestamp,
        spot_at_open=round(spot, 2),
        open_reason=reason,
        initial_total_premium=ce_premium + pe_premium,
    )
    if reason == "cycle_start":
        position.tp_points = args.adj_tp_points_init
    else:
        base_min, base_max, _ = premium_band(spot, args)
        baseline = base_min + base_max
        position.tp_points = round(args.adj_tp_points_init * position.initial_total_premium / max(baseline, 0.01), 2)

    ce_leg = LegState(
        leg_id=leg_counter[0],
        side="CE",
        strike=ce_strike,
        sell_prem=ce_premium,
        sell_timestamp=timestamp,
        open_reason=reason,
    )
    leg_counter[0] += 1
    pe_leg = LegState(
        leg_id=leg_counter[0],
        side="PE",
        strike=pe_strike,
        sell_prem=pe_premium,
        sell_timestamp=timestamp,
        open_reason=reason,
    )
    leg_counter[0] += 1
    position.legs.extend([ce_leg, pe_leg])
    position.ce_active_id = ce_leg.leg_id
    position.pe_active_id = pe_leg.leg_id
    positions.append(position)
    return position


def close_adjust_position(
    position: Position,
    timestamp: str,
    spot: float,
    ce_leg: LegState,
    pe_leg: LegState,
    ce_price: float,
    pe_price: float,
    reason: str,
) -> None:
    for leg, price in [(ce_leg, ce_price), (pe_leg, pe_price)]:
        leg.open = False
        leg.buy_prem = price
        leg.buy_timestamp = timestamp
        leg.close_reason = reason
    position.close_timestamp = timestamp
    position.spot_at_close = round(spot, 2)
    position.close_reason = reason


def roll_adjust_leg(
    chain: RepoChain,
    position: Position,
    expiry: str,
    timestamp: str,
    atm: int,
    weak_side: str,
    weak_price: float,
    strong_price: float,
    reason: str,
    leg_counter: List[int],
    args: argparse.Namespace,
    premium_min: Optional[float] = None,
    premium_max: Optional[float] = None,
) -> bool:
    ce_leg, pe_leg = active_legs(position)
    if weak_side == "CE":
        old_leg = ce_leg
        opposite_strike = pe_leg.strike
    else:
        old_leg = pe_leg
        opposite_strike = ce_leg.strike

    min_value = args.adj_band_low * strong_price if premium_min is None else premium_min
    max_value = args.adj_band_high * strong_price if premium_max is None else premium_max
    pick = chain.find_roll_strike(
        expiry,
        weak_side,
        timestamp,
        atm,
        min_value,
        max_value,
        old_leg.strike,
        opposite_strike,
        args.min_premium,
        args.max_premium,
    )
    if pick is None:
        return False

    new_strike, new_premium = pick
    old_leg.open = False
    old_leg.buy_prem = weak_price
    old_leg.buy_timestamp = timestamp
    old_leg.close_reason = reason

    new_leg = LegState(
        leg_id=leg_counter[0],
        side=weak_side,
        strike=new_strike,
        sell_prem=new_premium,
        sell_timestamp=timestamp,
        open_reason=reason,
    )
    leg_counter[0] += 1
    position.legs.append(new_leg)
    if weak_side == "CE":
        position.ce_active_id = new_leg.leg_id
    else:
        position.pe_active_id = new_leg.leg_id
    if reason == "decay_50":
        position.n_intraday_adj += 1
    elif reason == "eod_gap":
        position.n_eod_adj += 1
    return True


def eod_rebalance(
    chain: RepoChain,
    position: Position,
    expiry: str,
    timestamp: str,
    atm: int,
    ce_price: float,
    pe_price: float,
    leg_counter: List[int],
    args: argparse.Namespace,
) -> Tuple[bool, str]:
    for _ in range(args.adj_max_rolls_per_day):
        if abs(ce_price - pe_price) / max(ce_price, pe_price, 0.01) <= args.adj_eod_gap_max:
            return True, ""

        if ce_price < pe_price:
            weak_side, weak_price, strong_price = "CE", ce_price, pe_price
        else:
            weak_side, weak_price, strong_price = "PE", pe_price, ce_price

        ok = roll_adjust_leg(
            chain,
            position,
            expiry,
            timestamp,
            atm,
            weak_side,
            weak_price,
            strong_price,
            "eod_gap",
            leg_counter,
            args,
            premium_min=0.80 * strong_price,
            premium_max=1.20 * strong_price,
        )
        if not ok:
            return False, "no_roll_available"

        ce_leg, pe_leg = active_legs(position)
        ce_now = chain.price_at(expiry, "CE", ce_leg.strike, timestamp, args.min_premium, args.max_premium)
        pe_now = chain.price_at(expiry, "PE", pe_leg.strike, timestamp, args.min_premium, args.max_premium)
        if ce_now is not None:
            ce_price = ce_now[0]
        if pe_now is not None:
            pe_price = pe_now[0]
    return True, ""


def simulate_expiry_leg(
    chain: RepoChain,
    expiry: str,
    side: str,
    strike: int,
    trade_day: str,
    entry_timestamp: str,
    exit_timestamp: str,
    args: argparse.Namespace,
) -> Optional[Tuple[str, float, str, float, str]]:
    contract = chain.load_contract(expiry, side, strike)
    if contract is None:
        return None
    day_rows = [
        row
        for row in contract.ordered_rows
        if timestamp_date(row.timestamp) == trade_day and row.timestamp >= entry_timestamp
    ]
    if not day_rows:
        return None

    entry_row = day_rows[0]
    entry_price = entry_row.close_value
    if not (args.min_premium <= entry_price <= args.max_premium):
        return None

    stop_price = entry_price * args.exp_sl_mult
    monitoring_rows = [
        row
        for row in day_rows
        if entry_row.timestamp < row.timestamp <= exit_timestamp
    ]
    for row in monitoring_rows:
        if row.close_value >= stop_price:
            return entry_row.timestamp, entry_price, row.timestamp, row.close_value, f"sl_{format_number(args.exp_sl_mult)}x"

    if monitoring_rows:
        exit_row = monitoring_rows[-1]
    else:
        exit_row = entry_row
    exit_reason = "scheduled_exit" if exit_row.timestamp >= exit_timestamp else "last_available"
    return entry_row.timestamp, entry_price, exit_row.timestamp, exit_row.close_value, exit_reason


def simulate_expiry_day(
    chain: RepoChain,
    spot_data: SpotData,
    expiry: str,
    trade_no: int,
    capital: float,
    args: argparse.Namespace,
) -> Tuple[ExpiryTrade, List[LegEvent]]:
    trade_day = expiry
    entry_timestamp = build_timestamp(trade_day, args.exp_entry_time)
    exit_timestamp = build_timestamp(trade_day, args.exp_exit_time)
    spot_entry_row = spot_row_at_or_before(spot_data, trade_day, entry_timestamp)
    spot_day_rows = spot_data.rows_by_day.get(trade_day, [])
    if spot_entry_row is None or not spot_day_rows:
        return ExpiryTrade(
            trade_no=trade_no,
            expiry=expiry,
            trade_date=trade_day,
            status="SKIPPED",
            skip_reason="missing_spot_entry",
            remarks=f"Missing spot row at or before {entry_timestamp}",
        ), []

    spot_entry = spot_entry_row.close_value
    spot_close = spot_day_rows[-1].close_value
    atm = round_to_gap(spot_entry, args.gap)
    ce_strike = chain.nearest_strike(atm + args.exp_strike_dist, expiry, "CE")
    pe_strike = chain.nearest_strike(atm - args.exp_strike_dist, expiry, "PE")
    if ce_strike is None or pe_strike is None or ce_strike <= pe_strike:
        return ExpiryTrade(
            trade_no=trade_no,
            expiry=expiry,
            trade_date=trade_day,
            status="SKIPPED",
            skip_reason="missing_strikes",
            capital_at_entry=round(capital, 2),
            spot_at_entry=round(spot_entry, 2),
            spot_at_close=round(spot_close, 2),
            atm=atm,
            remarks="Could not find valid +/- expiry-day strangle strikes.",
        ), []

    ce_result = simulate_expiry_leg(chain, expiry, "CE", ce_strike, trade_day, entry_timestamp, exit_timestamp, args)
    pe_result = simulate_expiry_leg(chain, expiry, "PE", pe_strike, trade_day, entry_timestamp, exit_timestamp, args)
    if ce_result is None or pe_result is None:
        return ExpiryTrade(
            trade_no=trade_no,
            expiry=expiry,
            trade_date=trade_day,
            status="SKIPPED",
            skip_reason="missing_or_invalid_option_entry",
            capital_at_entry=round(capital, 2),
            spot_at_entry=round(spot_entry, 2),
            spot_at_close=round(spot_close, 2),
            atm=atm,
            ce_strike=ce_strike,
            pe_strike=pe_strike,
            remarks="CE or PE option data missing, or entry premium outside sanity band.",
        ), []

    lot_size = args.lot_size
    lots = lots_for(spot_entry, args, capital)
    units = lots * lot_size
    margin_used = lots * spot_entry * lot_size * args.margin_rate

    def build_event(side: str, strike: int, result: Tuple[str, float, str, float, str], leg_no: int) -> LegEvent:
        sell_time, sell_price, buy_time, buy_price, close_reason = result
        sell_value = sell_price * units
        buy_value = buy_price * units
        gross = (sell_price - buy_price) * units
        charges = order_charges(sell_value, buy_value, args)
        spot_open = spot_data.rows_by_timestamp.get(sell_time, spot_entry_row).close_value
        spot_close_value = spot_data.rows_by_timestamp.get(buy_time, spot_day_rows[-1]).close_value
        return LegEvent(
            strategy="expiry",
            cycle_id=trade_no,
            pos_id=0,
            leg_no=leg_no,
            trade_date=trade_day,
            expiry=expiry,
            side=side,
            sell_strike=strike,
            sell_time=sell_time,
            sell_price=round(sell_price, 2),
            buy_time=buy_time,
            buy_price=round(buy_price, 2),
            spot_at_open=round(spot_open, 2),
            spot_at_close=round(spot_close_value, 2),
            tp_points=0.0,
            sl_price=round(sell_price * args.exp_sl_mult, 2),
            lots=lots,
            lot_size=lot_size,
            units=units,
            gross_pnl=round(gross, 2),
            charges=round(charges, 2),
            net_pnl=round(gross - charges, 2),
            open_reason="expiry_entry",
            close_reason=close_reason,
        )

    ce_event = build_event("CE", ce_strike, ce_result, 1)
    pe_event = build_event("PE", pe_strike, pe_result, 2)
    trade = ExpiryTrade(
        trade_no=trade_no,
        expiry=expiry,
        trade_date=trade_day,
        status="TRADED",
        skip_reason="",
        capital_at_entry=round(capital, 2),
        spot_at_entry=round(spot_entry, 2),
        spot_at_close=round(spot_close, 2),
        atm=atm,
        lot_size=lot_size,
        lots_per_leg=lots,
        units_per_leg=units,
        margin_rate=round(args.margin_rate, 4),
        margin_used=round(margin_used, 2),
        ce_strike=ce_strike,
        pe_strike=pe_strike,
        ce_entry_price=ce_event.sell_price,
        ce_exit_price=ce_event.buy_price,
        ce_exit_reason=ce_event.close_reason,
        pe_entry_price=pe_event.sell_price,
        pe_exit_price=pe_event.buy_price,
        pe_exit_reason=pe_event.close_reason,
        total_premium_points=round(ce_event.sell_price + pe_event.sell_price, 2),
        gross_pnl=round(ce_event.gross_pnl + pe_event.gross_pnl, 2),
        total_charges=round(ce_event.charges + pe_event.charges, 2),
        net_pnl=round(ce_event.net_pnl + pe_event.net_pnl, 2),
    )
    return trade, [ce_event, pe_event]


def simulate_adjust_cycle(
    chain: RepoChain,
    spot_rows: List[PriceRow],
    expiry: str,
    period_start: str,
    period_end: str,
    cycle_no: int,
    capital: float,
    args: argparse.Namespace,
) -> Tuple[AdjustCycle, List[LegEvent]]:
    cycle = AdjustCycle(
        cycle_no=cycle_no,
        period_start=period_start,
        period_end=period_end,
        expiry=expiry,
        status="SKIPPED",
        capital_at_entry=round(capital, 2),
        lot_size=args.lot_size,
        margin_rate=round(args.margin_rate, 4),
    )
    if not spot_rows:
        cycle.skip_reason = "no_spot_data"
        cycle.remarks = "No spot rows inside adjustment cycle window."
        return cycle, []

    spot_timestamps = [row.timestamp for row in spot_rows]
    cycle.spot_at_start = round(spot_rows[0].close_value, 2)
    cycle.spot_at_end = round(spot_rows[-1].close_value, 2)
    cycle.lots = lots_for(cycle.spot_at_start, args, capital)
    cycle.margin_used = round(cycle.lots * cycle.spot_at_start * args.lot_size * args.margin_rate, 2)

    entry_timestamp = build_timestamp(period_start, args.adj_entry_time)
    entry_row = row_at_or_before_in_window(spot_rows, spot_timestamps, entry_timestamp)
    if entry_row is None:
        entry_row = spot_rows[0]
        entry_timestamp = entry_row.timestamp
    spot_entry = entry_row.close_value

    entry_min, entry_max, min_otm = premium_band(spot_entry, args)
    positions: List[Position] = []
    leg_counter = [1]
    active_position = open_adjust_position(
        chain,
        expiry,
        entry_timestamp,
        spot_entry,
        entry_min,
        entry_max,
        min_otm,
        "cycle_start",
        leg_counter,
        positions,
        args,
    )
    if active_position is None:
        cycle.skip_reason = "no_initial_entry_strikes"
        cycle.remarks = (
            f"No initial CE/PE strikes found in premium band {format_number(entry_min)}-"
            f"{format_number(entry_max)} with min OTM {format_number(min_otm)}."
        )
        return cycle, []

    last_eod_date = ""
    for spot_row in spot_rows:
        if spot_row.timestamp <= entry_timestamp:
            continue
        timestamp = spot_row.timestamp
        spot_now = spot_row.close_value
        atm_now = round_to_gap(spot_now, args.gap)

        if active_position is None:
            if len(positions) >= args.adj_max_pos_per_cycle:
                continue
            re_min, re_max, re_otm = premium_band(spot_now, args, reentry=True)
            active_position = open_adjust_position(
                chain,
                expiry,
                timestamp,
                spot_now,
                re_min,
                re_max,
                re_otm,
                "reentry",
                leg_counter,
                positions,
                args,
            )
            if active_position is None:
                continue

        ce_leg, pe_leg = active_legs(active_position)
        ce_quote = chain.price_at(expiry, "CE", ce_leg.strike, timestamp, args.min_premium, args.max_premium)
        pe_quote = chain.price_at(expiry, "PE", pe_leg.strike, timestamp, args.min_premium, args.max_premium)
        if ce_quote is None or pe_quote is None:
            continue
        ce_price = ce_quote[0]
        pe_price = pe_quote[0]

        if ce_leg.strike <= pe_leg.strike:
            close_adjust_position(active_position, timestamp, spot_now, ce_leg, pe_leg, ce_price, pe_price, "sl_breach")
            active_position = None
            continue

        if position_net_points(active_position, ce_price, pe_price) >= active_position.tp_points:
            close_adjust_position(active_position, timestamp, spot_now, ce_leg, pe_leg, ce_price, pe_price, "tp")
            active_position = None
            continue

        ce_decay = ce_price / max(ce_leg.sell_prem, 0.01)
        pe_decay = pe_price / max(pe_leg.sell_prem, 0.01)
        ce_triggered = ce_decay <= args.adj_decay_pct
        pe_triggered = pe_decay <= args.adj_decay_pct
        if ce_triggered or pe_triggered:
            if ce_triggered and pe_triggered:
                weak_side = "CE" if ce_decay <= pe_decay else "PE"
            else:
                weak_side = "CE" if ce_triggered else "PE"
            weak_price, strong_price = (ce_price, pe_price) if weak_side == "CE" else (pe_price, ce_price)
            ok = roll_adjust_leg(
                chain,
                active_position,
                expiry,
                timestamp,
                atm_now,
                weak_side,
                weak_price,
                strong_price,
                "decay_50",
                leg_counter,
                args,
            )
            if not ok:
                close_adjust_position(
                    active_position,
                    timestamp,
                    spot_now,
                    ce_leg,
                    pe_leg,
                    ce_price,
                    pe_price,
                    "no_roll_available",
                )
                active_position = None
                continue

        current_date = timestamp_date(timestamp)
        if timestamp_time(timestamp) >= args.adj_eod_time and current_date != last_eod_date and current_date != period_end:
            last_eod_date = current_date
            ce_leg, pe_leg = active_legs(active_position)
            ce_quote = chain.price_at(expiry, "CE", ce_leg.strike, timestamp, args.min_premium, args.max_premium)
            pe_quote = chain.price_at(expiry, "PE", pe_leg.strike, timestamp, args.min_premium, args.max_premium)
            if ce_quote is None or pe_quote is None:
                continue
            still_open, close_reason = eod_rebalance(
                chain,
                active_position,
                expiry,
                timestamp,
                atm_now,
                ce_quote[0],
                pe_quote[0],
                leg_counter,
                args,
            )
            if not still_open:
                ce_leg, pe_leg = active_legs(active_position)
                ce_quote = chain.price_at(expiry, "CE", ce_leg.strike, timestamp, args.min_premium, args.max_premium)
                pe_quote = chain.price_at(expiry, "PE", pe_leg.strike, timestamp, args.min_premium, args.max_premium)
                ce_price = ce_quote[0] if ce_quote is not None else ce_price
                pe_price = pe_quote[0] if pe_quote is not None else pe_price
                close_adjust_position(
                    active_position,
                    timestamp,
                    spot_now,
                    ce_leg,
                    pe_leg,
                    ce_price,
                    pe_price,
                    close_reason,
                )
                active_position = None

    if active_position is not None and not active_position.close_timestamp:
        last_row = spot_rows[-1]
        ce_leg, pe_leg = active_legs(active_position)
        ce_quote = chain.price_at(expiry, "CE", ce_leg.strike, last_row.timestamp, 0.0, args.max_premium)
        pe_quote = chain.price_at(expiry, "PE", pe_leg.strike, last_row.timestamp, 0.0, args.max_premium)
        ce_price = ce_quote[0] if ce_quote is not None else max(0.0, last_row.close_value - ce_leg.strike)
        pe_price = pe_quote[0] if pe_quote is not None else max(0.0, pe_leg.strike - last_row.close_value)
        close_adjust_position(
            active_position,
            last_row.timestamp,
            last_row.close_value,
            ce_leg,
            pe_leg,
            ce_price,
            pe_price,
            "cycle_end",
        )

    units = cycle.lots * cycle.lot_size
    events: List[LegEvent] = []
    total_points = 0.0
    total_charges = 0.0
    leg_no = 1

    def spot_close_at(timestamp: str) -> float:
        row = row_at_or_before_in_window(spot_rows, spot_timestamps, timestamp)
        return row.close_value if row is not None else 0.0

    for position in positions:
        for leg in position.legs:
            if leg.open:
                continue
            points = leg.realised_points()
            total_points += points
            sell_value = leg.sell_prem * units
            buy_value = leg.buy_prem * units
            gross = points * units
            charges = order_charges(sell_value, buy_value, args)
            total_charges += charges
            events.append(
                LegEvent(
                    strategy="adjust",
                    cycle_id=cycle_no,
                    pos_id=position.pos_id,
                    leg_no=leg_no,
                    trade_date=timestamp_date(leg.sell_timestamp),
                    expiry=expiry,
                    side=leg.side,
                    sell_strike=leg.strike,
                    sell_time=leg.sell_timestamp,
                    sell_price=round(leg.sell_prem, 2),
                    buy_time=leg.buy_timestamp,
                    buy_price=round(leg.buy_prem, 2),
                    spot_at_open=round(spot_close_at(leg.sell_timestamp), 2),
                    spot_at_close=round(spot_close_at(leg.buy_timestamp), 2),
                    tp_points=round(position.tp_points, 2),
                    sl_price=0.0,
                    lots=cycle.lots,
                    lot_size=cycle.lot_size,
                    units=units,
                    gross_pnl=round(gross, 2),
                    charges=round(charges, 2),
                    net_pnl=round(gross - charges, 2),
                    open_reason=leg.open_reason,
                    close_reason=leg.close_reason,
                )
            )
            leg_no += 1

    cycle.status = "TRADED"
    cycle.skip_reason = ""
    cycle.n_positions = len(positions)
    cycle.n_intraday_adj = sum(position.n_intraday_adj for position in positions)
    cycle.n_eod_adj = sum(position.n_eod_adj for position in positions)
    cycle.n_legs = sum(len(position.legs) for position in positions)
    cycle.net_points = round(total_points, 2)
    cycle.gross_pnl = round(total_points * units, 2)
    cycle.total_charges = round(total_charges, 2)
    cycle.net_pnl = round(cycle.gross_pnl - total_charges, 2)
    return cycle, events


def run_backtest(args: argparse.Namespace) -> Tuple[List[ExpiryTrade], List[AdjustCycle], List[LegEvent]]:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(args.results_dir / LOG_FILENAME)

    try:
        spot_data = load_spot_data(args.spot_file)
        expiries = load_expiry_folders(args.options_dir)
        day_set = set(spot_data.trading_days)
        expiries = [expiry for expiry in expiries if expiry in day_set]
        chain = RepoChain(args.options_dir, expiries)
        expiry_trades: List[ExpiryTrade] = []
        adjust_cycles: List[AdjustCycle] = []
        events: List[LegEvent] = []
        running_pnl = 0.0
        previous_expiry: Optional[str] = None
        cycle_no = 0
        trade_no = 0

        for expiry in expiries:
            if previous_expiry is None:
                period_start = spot_data.trading_days[0]
            else:
                period_start = next((day for day in spot_data.trading_days if day > previous_expiry), None)

            if period_start is not None and period_start < expiry:
                period_end = max((day for day in spot_data.trading_days if period_start <= day < expiry), default=None)
                if period_end is not None:
                    cycle_no += 1
                    capital = capital_for_sizing(args, running_pnl)
                    cycle_rows = spot_window_rows(spot_data, period_start, period_end)
                    cycle, cycle_events = simulate_adjust_cycle(
                        chain,
                        cycle_rows,
                        expiry,
                        period_start,
                        period_end,
                        cycle_no,
                        capital,
                        args,
                    )
                    adjust_cycles.append(cycle)
                    events.extend(cycle_events)
                    if cycle.status == "TRADED":
                        running_pnl += cycle.net_pnl
                    logger.info(
                        "ADJUST cycle=%s expiry=%s status=%s net=%s reason=%s",
                        cycle_no,
                        expiry,
                        cycle.status,
                        cycle.net_pnl,
                        cycle.skip_reason,
                    )

            trade_no += 1
            capital = capital_for_sizing(args, running_pnl)
            expiry_trade, expiry_events = simulate_expiry_day(
                chain,
                spot_data,
                expiry,
                trade_no,
                capital,
                args,
            )
            expiry_trades.append(expiry_trade)
            events.extend(expiry_events)
            if expiry_trade.status == "TRADED":
                running_pnl += expiry_trade.net_pnl
            logger.info(
                "EXPIRY trade=%s expiry=%s status=%s net=%s reason=%s",
                trade_no,
                expiry,
                expiry_trade.status,
                expiry_trade.net_pnl,
                expiry_trade.skip_reason,
            )

            previous_expiry = expiry
            chain.clear_caches()

        logger.info(
            "COMPLETED expiry_trades=%s adjust_cycles=%s events=%s running_pnl=%s",
            len([trade for trade in expiry_trades if trade.status == "TRADED"]),
            len([cycle for cycle in adjust_cycles if cycle.status == "TRADED"]),
            len(events),
            running_pnl,
        )
        return expiry_trades, adjust_cycles, events
    finally:
        close_logger(logger)


def build_equity_curve(
    expiry_trades: List[ExpiryTrade],
    adjust_cycles: List[AdjustCycle],
    capital: float,
) -> List[EquityRow]:
    raw_rows: List[Dict[str, object]] = []
    for cycle in adjust_cycles:
        row_date = cycle.period_end or cycle.period_start
        raw_rows.append(
            {
                "date": row_date,
                "source": "adjust",
                "ref": cycle.cycle_no,
                "expiry": cycle.expiry,
                "status": cycle.status,
                "net_pnl": cycle.net_pnl if cycle.status == "TRADED" else 0.0,
                "gross_pnl": cycle.gross_pnl if cycle.status == "TRADED" else 0.0,
                "charges": cycle.total_charges if cycle.status == "TRADED" else 0.0,
                "note": cycle.skip_reason,
            }
        )
    for trade in expiry_trades:
        raw_rows.append(
            {
                "date": trade.trade_date,
                "source": "expiry",
                "ref": trade.trade_no,
                "expiry": trade.expiry,
                "status": trade.status,
                "net_pnl": trade.net_pnl if trade.status == "TRADED" else 0.0,
                "gross_pnl": trade.gross_pnl if trade.status == "TRADED" else 0.0,
                "charges": trade.total_charges if trade.status == "TRADED" else 0.0,
                "note": trade.skip_reason,
            }
        )

    raw_rows.sort(key=lambda row: (str(row["date"]), str(row["source"])))
    output: List[EquityRow] = []
    cumulative = 0.0
    for row in raw_rows:
        net_pnl = float(row["net_pnl"])
        cumulative += net_pnl
        output.append(
            EquityRow(
                date=str(row["date"]),
                source=str(row["source"]),
                ref=int(row["ref"]),
                expiry=str(row["expiry"]),
                status=str(row["status"]),
                net_pnl=round(net_pnl, 2),
                gross_pnl=round(float(row["gross_pnl"]), 2),
                charges=round(float(row["charges"]), 2),
                cum_pnl=round(cumulative, 2),
                equity=round(capital + cumulative, 2),
                note=str(row["note"]),
            )
        )
    return output


def max_drawdown(values: List[float], capital: float) -> float:
    equity = capital
    peak = capital
    max_dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return max_dd


def max_consecutive_losses(values: List[float]) -> int:
    max_loss_streak = 0
    current = 0
    for value in values:
        if value < 0:
            current += 1
            max_loss_streak = max(max_loss_streak, current)
        else:
            current = 0
    return max_loss_streak


def compute_metrics(rows: List[EquityRow], capital: float) -> Dict[str, object]:
    active = [row for row in rows if row.status == "TRADED"]
    if not active:
        return {}
    values = [row.net_pnl for row in active]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    breakeven = [value for value in values if value == 0]
    total = sum(values)
    first_date = active[0].date
    last_date = active[-1].date
    first_dt = date_from_text(first_date)
    last_dt = date_from_text(last_date)
    years = max((last_dt - first_dt).days / 365.25, 1 / 365.25)
    final_equity = capital + total
    cagr = ((final_equity / capital) ** (1 / years) - 1) * 100 if final_equity > 0 else -100.0
    dd = max_drawdown(values, capital)
    loss_sum = abs(sum(losses))
    profit_factor = sum(wins) / loss_sum if loss_sum else math.inf
    expectancy = total / len(values)
    return {
        "n": len(values),
        "wins": len(wins),
        "losses": len(losses),
        "breakeven": len(breakeven),
        "win_rate_pct": round(len(wins) / len(values) * 100, 2),
        "total_pnl": round(total, 2),
        "return_pct": round(total / capital * 100, 2),
        "cagr_pct": round(cagr, 2),
        "years": round(years, 2),
        "max_drawdown": round(dd, 2),
        "max_drawdown_pct": round(dd / capital * 100, 2),
        "profit_factor": round(profit_factor, 2) if math.isfinite(profit_factor) else "inf",
        "avg_win": round(sum(wins) / len(wins), 2) if wins else 0.0,
        "avg_loss": round(sum(losses) / len(losses), 2) if losses else 0.0,
        "expectancy": round(expectancy, 2),
        "best": round(max(values), 2),
        "worst": round(min(values), 2),
        "max_consecutive_losses": max_consecutive_losses(values),
        "first_date": first_date,
        "last_date": last_date,
    }


def per_year_metrics(rows: List[EquityRow], capital: float) -> List[Dict[str, object]]:
    output: List[Dict[str, object]] = []
    years = sorted({row.date[:4] for row in rows if row.status == "TRADED"})
    for year in years:
        year_rows = [row for row in rows if row.date.startswith(year)]
        metrics = compute_metrics(year_rows, capital)
        if not metrics:
            continue
        metrics["period"] = year
        metrics["adjust_pnl"] = round(sum(row.net_pnl for row in year_rows if row.source == "adjust"), 2)
        metrics["expiry_pnl"] = round(sum(row.net_pnl for row in year_rows if row.source == "expiry"), 2)
        metrics["n_adjust"] = sum(1 for row in year_rows if row.source == "adjust" and row.status == "TRADED")
        metrics["n_expiry"] = sum(1 for row in year_rows if row.source == "expiry" and row.status == "TRADED")
        output.append(metrics)
    return output


def write_dataclass_csv(items: List[object], item_type: type, output_path: Path) -> None:
    fieldnames = [field.name for field in fields(item_type)]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(asdict(item))


def write_summary_csv(per_year: List[Dict[str, object]], overall: Dict[str, object], output_path: Path) -> None:
    rows = [dict(row) for row in per_year]
    if overall:
        all_row = dict(overall)
        all_row["period"] = "ALL"
        rows.append(all_row)
    if not rows:
        return
    preferred = [
        "period",
        "n",
        "n_expiry",
        "n_adjust",
        "expiry_pnl",
        "adjust_pnl",
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


def markdown_metrics_table(rows: List[Dict[str, object]]) -> List[str]:
    lines = [
        "| Period | Active | Expiry | Adjust | Expiry P/L | Adjust P/L | Total P/L | Return % | Max DD | Win % | PF |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.get('period', '')} | "
            f"{row.get('n', 0)} | "
            f"{row.get('n_expiry', '')} | "
            f"{row.get('n_adjust', '')} | "
            f"{format_number(float(row.get('expiry_pnl', 0.0) or 0.0))} | "
            f"{format_number(float(row.get('adjust_pnl', 0.0) or 0.0))} | "
            f"{format_number(float(row.get('total_pnl', 0.0) or 0.0))} | "
            f"{format_number(float(row.get('return_pct', 0.0) or 0.0))} | "
            f"{format_number(float(row.get('max_drawdown', 0.0) or 0.0))} | "
            f"{format_number(float(row.get('win_rate_pct', 0.0) or 0.0))} | "
            f"{row.get('profit_factor', '')} |"
        )
    return lines


def write_summary_md(
    expiry_trades: List[ExpiryTrade],
    adjust_cycles: List[AdjustCycle],
    events: List[LegEvent],
    equity_rows: List[EquityRow],
    per_year: List[Dict[str, object]],
    overall: Dict[str, object],
    output_path: Path,
    args: argparse.Namespace,
) -> None:
    traded_expiry = [trade for trade in expiry_trades if trade.status == "TRADED"]
    skipped_expiry = [trade for trade in expiry_trades if trade.status != "TRADED"]
    traded_cycles = [cycle for cycle in adjust_cycles if cycle.status == "TRADED"]
    skipped_cycles = [cycle for cycle in adjust_cycles if cycle.status != "TRADED"]
    close_reasons = Counter(event.close_reason for event in events)
    overall_row = dict(overall)
    overall_row["period"] = "ALL"
    overall_row["adjust_pnl"] = round(sum(row.net_pnl for row in equity_rows if row.source == "adjust"), 2)
    overall_row["expiry_pnl"] = round(sum(row.net_pnl for row in equity_rows if row.source == "expiry"), 2)
    overall_row["n_adjust"] = len(traded_cycles)
    overall_row["n_expiry"] = len(traded_expiry)

    lines: List[str] = [
        "# 2025 Combined Expiry + Adjusting Short Strangle Backtest",
        "",
        "## Strategy Details",
        "",
        f"- Spot file: `{args.spot_file}`",
        f"- Options directory: `{args.options_dir}`",
        "- Expiry-day strategy: sell expiring ATM+100 CE and ATM-100 PE at 09:20, per-leg SL at 2x entry, exit at 15:25.",
        "- Adjustment-cycle strategy: sell this-expiry far OTM strangle from the day after previous expiry through the day before this expiry.",
        "- Adjustment entry band: 0.0833%-0.1250% of spot, min OTM 1.25% of spot.",
        "- Re-entry band: 0.0417%-0.0625% of spot after a position closes.",
        "- Intraday roll: when one active leg decays to 50% or less of its sell price, roll that leg closer to ATM.",
        "- EOD rebalance: from 15:20, roll the cheaper leg closer to ATM when CE/PE premium gap is above 20%, except on cycle-end day.",
        f"- Sizing: capital Rs {format_number(args.capital)}, compound `{args.compound}`, lot size `{args.lot_size}`, margin rate `{format_number(args.margin_rate)}`.",
        "- Pricing: option close is used for entries, monitoring, rolls, and exits; last available row at or before the timestamp is used.",
        "- Events file support from the provided script is not used because this repo does not include that market-events config.",
        "",
        "## Overall Results",
        "",
        *markdown_metrics_table([overall_row]),
        "",
        "## Yearly Results",
        "",
        *markdown_metrics_table(per_year),
        "",
        "## Counts",
        "",
        f"- Expiry trades: `{len(traded_expiry)}` traded, `{len(skipped_expiry)}` skipped",
        f"- Adjust cycles: `{len(traded_cycles)}` traded, `{len(skipped_cycles)}` skipped",
        f"- Leg events: `{len(events)}`",
        f"- Final equity: `Rs {format_number(equity_rows[-1].equity if equity_rows else args.capital)}`",
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
    skip_lines: List[str] = []
    for trade in skipped_expiry:
        skip_lines.append(f"- Expiry `{trade.expiry}`: `{trade.skip_reason}`. {trade.remarks}")
    for cycle in skipped_cycles:
        skip_lines.append(f"- Adjust `{cycle.expiry}` ({cycle.period_start} to {cycle.period_end}): `{cycle.skip_reason}`. {cycle.remarks}")
    lines.extend(skip_lines if skip_lines else ["- None"])

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- Expiry trades: `{EXPIRY_TRADES_FILENAME}`",
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
    expiry_trades: List[ExpiryTrade],
    adjust_cycles: List[AdjustCycle],
    events: List[LegEvent],
    equity_rows: List[EquityRow],
    args: argparse.Namespace,
) -> None:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    write_dataclass_csv(expiry_trades, ExpiryTrade, args.results_dir / EXPIRY_TRADES_FILENAME)
    write_dataclass_csv(adjust_cycles, AdjustCycle, args.results_dir / ADJUST_CYCLES_FILENAME)
    write_dataclass_csv(events, LegEvent, args.results_dir / EVENTS_FILENAME)
    write_dataclass_csv(equity_rows, EquityRow, args.results_dir / EQUITY_FILENAME)

    overall = compute_metrics(equity_rows, args.capital)
    per_year = per_year_metrics(equity_rows, args.capital)
    if overall:
        overall["adjust_pnl"] = round(sum(row.net_pnl for row in equity_rows if row.source == "adjust"), 2)
        overall["expiry_pnl"] = round(sum(row.net_pnl for row in equity_rows if row.source == "expiry"), 2)
        overall["n_adjust"] = sum(1 for row in equity_rows if row.source == "adjust" and row.status == "TRADED")
        overall["n_expiry"] = sum(1 for row in equity_rows if row.source == "expiry" and row.status == "TRADED")
    write_summary_csv(per_year, overall, args.results_dir / SUMMARY_CSV_FILENAME)
    write_summary_md(
        expiry_trades,
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
    expiry_trades, adjust_cycles, events = run_backtest(args)
    equity_rows = build_equity_curve(expiry_trades, adjust_cycles, args.capital)
    write_outputs(expiry_trades, adjust_cycles, events, equity_rows, args)


if __name__ == "__main__":
    main()
