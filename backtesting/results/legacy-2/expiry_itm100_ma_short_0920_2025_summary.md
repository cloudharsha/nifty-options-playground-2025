# 2025 Expiry-Day Short ITM 100 NIFTY 25-SMA Backtest

## Strategy Details

- Signal source: NIFTY spot versus 15-minute NIFTY SMA
- Trading days: expiry dates only from `C:\Users\harsh\Desktop\workspace\git\nifty-options-playground-2025\Options_2025` that overlap the 2025 spot calendar
- Entry time: `09:20`
- Exit time: `15:00`
- Signal mode: `live-entry`
- Signal value: `09:20` 1-minute NIFTY open on the expiry date
- MA rule: prior 24 completed 15-minute NIFTY closes plus the entry signal value
- Direction rule: above SMA -> short ITM PE; below SMA -> short ITM CE; equal -> no trade
- ITM rule: PE strike = ATM + 100; CE strike = ATM - 100
- ATM rule: nearest 50 using the signal value
- Expiry rule: trade only the option expiring that same day
- Pricing rule: exact option open price at exact timestamps
- Contract multiplier: 65 x 4 = 260 rupees per option point
- Execution slippage: 1.00 point per order, applied against every entry and exit
- Brokerage rule: Rs 25 per order, so one completed short leg pays Rs 50

## Results Summary

- Expiry days tested: `53`
- Traded days: `53`
- Skipped expiry days: `0`
- Completed trades: `53`
- Skipped trade rows: `0`
- CE-sell count: `22`
- PE-sell count: `31`
- Winning days: `26`
- Losing days: `27`
- Break-even days: `0`
- Win rate: `49.06%`
- Max profit day: `2025-01-02` with net P/L `45359.00`
- Max loss day: `2025-05-15` with net P/L `-112224.40`
- Max consecutive wins: `6`
- Max consecutive losses: `5`
- Max drawdown: `240921.00`
- Total Profit/Loss: `15760.60`
- Total Brokerage: `2650.00`
- Profit/Loss without Brokerage: `18410.60`

## Exceptions

- None

## Remarks

- Exact timestamp matching is required; no nearest-candle fallback is allowed.
- The 15-minute NIFTY rows are treated as candle-start timestamps.
- The `09:20` entry avoids using the unfinished `09:15` 15-minute close by default; `--signal-mode signal-15m-row` can reproduce that alternate interpretation.
- `15:00` is the scheduled expiry-day square-off proxy.
- Expiry folder dates are used as truth, which naturally handles Tuesday special expiries and holiday shifts.
