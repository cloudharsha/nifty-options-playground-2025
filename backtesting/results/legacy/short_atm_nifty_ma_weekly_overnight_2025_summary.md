# 2025 Overnight Weekly Short ATM NIFTY 25-SMA Backtest

## Strategy Details

- Signal source: NIFTY 15-minute close
- Signal bar time: `15:15` row as `15:30` close proxy
- MA rule: 25-SMA of spot closes including the signal bar
- Direction rule: above SMA -> short ATM PE; below SMA -> short ATM CE; equal -> no trade
- Entry execution time: `15:29` option open
- Exit execution time: next trading day `09:16` option open
- Expiry rule: first weekly expiry strictly after entry date
- ATM rule: nearest 50 using the spot signal close
- Contract multiplier: 65 x 4 = 260 rupees per option point
- Execution slippage: 1.00 point per order, applied against every entry and exit
- Brokerage rule: Rs 25 per order, so one completed short leg pays Rs 50

## Results Summary

- Traded days: `245`
- Skipped days: `4`
- CE-sell count: `125`
- PE-sell count: `120`
- Winning days: `141`
- Losing days: `104`
- Break-even days: `0`
- Max profit day: `2025-05-09` with net P/L `57462.00`
- Max loss day: `2025-08-14` with net P/L `-55820.00`
- Max consecutive wins: `7`
- Max consecutive losses: `6`
- Max drawdown: `76221.00`
- Total Profit/Loss: `446015.60`
- Total Brokerage: `12250.00`
- Profit/Loss without Brokerage: `458265.60`

## Exceptions

- `2025-10-20`: `missing_entry_or_exit_timestamp`. NIFTY_25850_CE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; Next trading day is a special session that starts at 13:45, so the exact 09:16 exit candle is unavailable.
- `2025-10-21`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2025-10-21T15:15:00+05:30
- `2025-12-30`: `no_next_weekly_expiry`. No weekly expiry folder exists strictly after the trade date.
- `2025-12-31`: `no_next_trading_day`. No next trading day exists in the dataset.

## Remarks

- Exact timestamp matching is required; no nearest-candle fallback is allowed.
- The `15:15` spot row is used as the `15:30` close proxy because the spot dataset has no exact `15:30` timestamp.
- The `15:29` option row is used as the sell proxy because the options dataset has no exact `15:30` timestamp.
- The NIFTY spot file is the source of truth for the trading calendar.
- Expiry folder dates are used as truth, which naturally handles Tuesday special expiries and holiday shifts.
- Equality between the spot close and the SMA produces no trade for that day.
