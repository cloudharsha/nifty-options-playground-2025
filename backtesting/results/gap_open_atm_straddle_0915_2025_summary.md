# 2025 09:15 Gap-Open ATM Straddle Backtest

## Strategy Details

- Entry and exit candle: `09:15`
- Gap rule: compare NIFTY 09:15 open with the previous trading day's last close
- Negative open: buy ATM CE and ATM PE at option open, exit both at option close
- Positive open: short ATM CE and ATM PE at option open, cover both at option close
- Flat open: skip
- ATM rule: nearest 50 using NIFTY 09:15 open
- Expiry rule: first expiry folder on or after the trade date
- Pricing rule: option open to option close of the same 09:15 candle
- Contract multiplier: 65 x 4 = 260 rupees per option point
- Slippage: 2.00 points per order, 4.00 points per leg round trip
- Brokerage: Rs 25.00 per order, Rs 100.00 per completed straddle

## Results Summary

- Total traded days: `245`
- Total skipped days: `4`
- Total leg trades: `490`
- Long straddle days: `105`
- Short straddle days: `140`
- Winning days: `95`
- Losing days: `150`
- Raw Profit/Loss before costs: `260975.00`
- Slippage loss: `509600.00`
- Brokerage: `24500.00`
- Net Profit/Loss: `-273125.00`
- Max profit day: `2025-04-07` with net P/L `86376.00`
- Max loss day: `2025-07-30` with net P/L `-14517.00`

## Output Files

- Daywise file: `gap_open_atm_straddle_0915_2025_daywise.csv`
- Trades file: `gap_open_atm_straddle_0915_2025_trades.csv`
- Log file: `gap_open_atm_straddle_0915_2025.log`

## Exceptions

- `2025-01-01`: `no_previous_close`. No previous trading day close exists in the dataset.
- `2025-04-16`: `flat_open`. Open matched previous close exactly.
- `2025-10-21`: `missing_spot_timestamp`. Missing spot entry timestamp 2025-10-21T09:15:00+05:30
- `2025-12-31`: `no_same_week_expiry`. No expiry folder exists on or after this trade date.

## Remarks

- The NIFTY spot file is the source of truth for trading days and previous-close detection.
- Raw 1-minute option candles from `Options_2025` are used directly.
- Slippage loss is reported separately and deducted from net P/L.
- Expiry folder dates are used as truth, which naturally handles non-Thursday expiry weeks.
