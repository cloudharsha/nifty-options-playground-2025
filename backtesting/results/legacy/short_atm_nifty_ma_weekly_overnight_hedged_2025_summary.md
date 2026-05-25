# 2025 Overnight Weekly Hedged Short ATM NIFTY 25-SMA Backtest

## Strategy Details

- Signal source: NIFTY 15-minute close
- Signal bar time: `15:15` row as `15:30` close proxy
- MA rule: 25-SMA of spot closes including the signal bar
- Direction rule: above SMA -> short ATM PE + long PE hedge 200 points lower; below SMA -> short ATM CE + long CE hedge 200 points higher; equal -> no trade
- Entry execution time: `15:29` option open
- Exit execution time: next trading day `09:16` option open
- Expiry rule: first weekly expiry strictly after entry date
- ATM rule: nearest 50 using the spot signal close
- Hedge distance: 200 points on the same option side
- Contract multiplier: 65 x 10 = 650 rupees per option point
- Execution slippage: 1.00 point per order, applied against every entry and exit
- Brokerage rule: Rs 25 per order, so one completed hedged spread pays Rs 100

## Results Summary

- Traded days: `244`
- Skipped days: `5`
- CE-spread count: `125`
- PE-spread count: `119`
- Winning days: `116`
- Losing days: `128`
- Break-even days: `0`
- Max profit day: `2025-05-09` with net P/L `37112.50`
- Max loss day: `2025-08-14` with net P/L `-45210.00`
- Max consecutive wins: `4`
- Max consecutive losses: `7`
- Max drawdown: `322592.50`
- Total Profit/Loss: `-218490.00`
- Total Brokerage: `24400.00`
- Profit/Loss without Brokerage: `-194090.00`

## Exceptions

- `2025-09-23`: `missing_entry_or_exit_timestamp`. NIFTY_25000_PE_30_SEP_25.csv missing entry timestamp 2025-09-23T15:29:00+05:30; NIFTY_25000_PE_30_SEP_25.csv missing exit timestamp 2025-09-24T09:16:00+05:30
- `2025-10-20`: `missing_entry_or_exit_timestamp`. NIFTY_25850_CE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; NIFTY_26050_CE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; Next trading day is a special session that starts at 13:45, so the exact 09:16 exit candle is unavailable.
- `2025-10-21`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2025-10-21T15:15:00+05:30
- `2025-12-30`: `no_next_weekly_expiry`. No weekly expiry folder exists strictly after the trade date.
- `2025-12-31`: `no_next_trading_day`. No next trading day exists in the dataset.

## Remarks

- Exact timestamp matching is required; no nearest-candle fallback is allowed.
- The `15:15` spot row is used as the `15:30` close proxy because the spot dataset has no exact `15:30` timestamp.
- The `15:29` option row is used as the sell and hedge-buy proxy because the options dataset has no exact `15:30` timestamp.
- The NIFTY spot file is the source of truth for the trading calendar.
- Expiry folder dates are used as truth, which naturally handles Tuesday special expiries and holiday shifts.
- Equality between the spot close and the SMA produces no trade for that day.
