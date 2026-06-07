# 2025 Intraday Same-Week ATM Short Straddle With 50-Point SL

## Strategy Details

- Entry time: `09:20`
- Exit time: `15:20`
- Spot ATM rule: nearest 50 using the NIFTY entry-time open
- Expiry rule: first expiry folder on or after the trade date
- Stop rule: independent `50.00` point premium stop per short leg
- Stop fill rule: use stop price when touched intrabar; use candle open when it opens above the stop
- Scheduled exit rule: open price of the option candle at the configured exit time
- Re-entry rule: none
- Pricing rule: exact timestamp matching; no nearest-candle fallback
- Contract multiplier: 65 x 4 = 260 rupees per option point
- Execution slippage: 1.00 point per order
- Brokerage rule: Rs 25.00 per order, Rs 100.00 per completed straddle

## Results Summary

- Total traded days: `247`
- Total skipped days: `2`
- Total leg trades: `494`
- Stop-loss leg exits: `215`
- Gap stop-loss leg exits: `1`
- Day-close leg exits: `278`
- Winning days: `143`
- Losing days: `104`
- Total Profit/Loss: `-123796.40`
- Total Brokerage: `24700.00`
- Profit/Loss without Brokerage: `-99096.40`
- Max profit day: `2025-04-09` with net P/L `65095.00`
- Max loss day: `2025-01-13` with net P/L `-27140.00`

## Output Files

- Daywise file: `short_atm_same_week_intraday_sl_2025_daywise.csv`
- Trades file: `short_atm_same_week_intraday_sl_2025_trades.csv`
- Log file: `short_atm_same_week_intraday_sl_2025.log`

## Exceptions

- `2025-10-21`: `missing_spot_timestamp`. Missing spot entry timestamp 2025-10-21T09:20:00+05:30
- `2025-12-31`: `no_same_week_expiry`. No expiry folder exists on or after this trade date.

## Remarks

- The NIFTY spot file is the source of truth for the trading calendar and intraday monitoring timestamps.
- Raw 1-minute option candles from `Options_2025` are used directly.
- A day is skipped if either straddle leg lacks the needed entry, monitoring, or scheduled exit candle.
- Expiry folder dates are used as truth, which naturally handles non-Thursday expiry weeks.
