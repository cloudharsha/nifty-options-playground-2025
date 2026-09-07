# Intraday Iron Condor — Weekly Expiry (2020–2026) Backtest

## Strategy Details

- **Structure**: Short iron condor — sell CE/PE at `ATM ± sell_offset`, buy CE/PE at `ATM ± buy_offset` as hedge
- **Sell offset**: 250 points from ATM
- **Buy offset (hedge)**: 450 points from ATM
- **Entry**: 09:20 open candle (options), every trading day
- **Exit**: 15:20 open candle (options), same day
- **ATM source**: 09:15 spot open (15-minute bar), rounded to nearest 50
- **Expiry**: current active weekly expiry (first expiry ≥ trading day)
- **Target quantity**: 300 per side (nearest lot multiple per era)
- **Lot size**: dynamic per expiry — 75 (pre-Oct 2021), 50 (Oct 2021–Apr 2024), 25 (May 2024–Nov 2024), 75 (Nov 2024–Dec 2025), 65 (Jan 2026+)
- **Slippage**: 1.00 pt per order (2.00 pts round-trip per leg)
- **Brokerage**: Rs 25 per order, Rs 200 per completed condor (4 legs × 2 sides)
- **Spot file**: `NIFTY50_INDEX_15m_last_4y.csv` (~May 2022–2026; earlier dates skipped)
- **Options data**: `Options`
- **No stop-loss, no intraday adjustments**

## Results Summary

- Trading days processed : `992`
- Trades executed        : `972`
- Trades skipped         : `20`
- Gross P&L              : `-2092818.50`
- Total Brokerage        : `194400.00`
- Net P&L                : `-2287218.50`

## Skip Reason Summary

- `missing_candle_at_timestamp`: 12
- `missing_spot_entry_timestamp`: 4
- `missing_contract_file`: 4

## Notes

- ATM is determined from the 09:15 spot candle open (first 15-minute bar). The strategy enters at 09:20 using the open of the first 1-minute candle in the options data.
- The active expiry for each trading day is the earliest available weekly expiry folder on or after that date, including expiry day itself.
- Trading days before ~May 2022 are skipped because the spot file does not cover that range.
- Lot sizes are applied per the target expiry date. From Jan 2026 (lot size 65), 5 lots (325 units) are used as the nearest multiple to 300.
- Deeply OTM or illiquid contracts may lack candles at 09:20 or 15:20, causing skips.
- Gross P&L includes slippage deduction but excludes brokerage.
