# 2025 Intraday Weekly Short ATM NIFTY 25-SMA Trailing Backtest

## Strategy Details

- Signal source: NIFTY 15-minute close
- Entry window: `09:30` through `15:00`
- Exit time: `15:15`
- MA rule: 25-SMA of 15-minute NIFTY closes including the signal candle
- Signal timing: each entry uses the completed 15-minute candle ending at that entry timestamp
- Direction rule: above SMA -> short ATM PE; below SMA -> short ATM CE; equal -> no trade
- Stop source: NIFTY 1-minute candles
- Stop rule: short PE exits when 1-minute NIFTY low touches the trailing MA; short CE exits when high touches it
- Trailing MA rule: latest completed 15-minute NIFTY SMA stays fixed until the next 15-minute close
- Re-entry rule: one active trade at a time; after a stop, the next entry can only use a later 15-minute close
- Expiry rule: first weekly expiry folder on or after the trade date
- ATM rule: nearest 50 using the signal candle close
- Pricing rule: exact option open price at exact timestamps
- Contract multiplier: 65 x 4 = 260 rupees per option point
- Execution slippage: 1.00 point per order, applied against every entry and exit
- Brokerage rule: Rs 25 per order, so one completed short leg pays Rs 50

## Results Summary

- Traded days: `247`
- Skipped days: `2`
- Completed trades: `1116`
- Skipped trade/signal rows: `2`
- CE-sell count: `538`
- PE-sell count: `578`
- Stop-loss exits: `922`
- Day-close exits: `194`
- Winning days: `152`
- Losing days: `95`
- Break-even days: `0`
- Max profit day: `2025-01-31` with net P/L `35297.00`
- Max loss day: `2025-06-02` with net P/L `-37872.00`
- Max consecutive wins: `9`
- Max consecutive losses: `5`
- Max drawdown: `130612.40`
- Total Profit/Loss: `660341.40`
- Total Brokerage: `55800.00`
- Profit/Loss without Brokerage: `716141.40`

## Exceptions

- `2025-10-21`: `missing_spot_1m_timestamp`. Missing 1-minute NIFTY monitoring timestamps: 285 missing timestamps from 2025-10-21T09:30:00+05:30 through 2025-10-21T15:15:00+05:30; first 5: 2025-10-21T09:30:00+05:30, 2025-10-21T09:31:00+05:30, 2025-10-21T09:32:00+05:30, 2025-10-21T09:33:00+05:30, 2025-10-21T09:34:00+05:30; last 5: 2025-10-21T15:11:00+05:30, 2025-10-21T15:12:00+05:30, 2025-10-21T15:13:00+05:30, 2025-10-21T15:14:00+05:30, 2025-10-21T15:15:00+05:30
- `2025-12-31`: `no_same_week_expiry`. No expiry folder exists on or after this trade date.

## Remarks

- Exact timestamp matching is required; no nearest-candle fallback is allowed.
- The 15-minute NIFTY rows are treated as candle-start timestamps.
- The `09:30` entry uses the prior `09:15` signal row.
- Stop checking starts from the minute after entry and excludes the scheduled day-close timestamp.
- `15:15` is the scheduled day-close execution proxy.
- The NIFTY 15-minute spot file is the source of truth for the trading calendar.
- Expiry folder dates are used as truth, which naturally handles Tuesday special expiries and holiday shifts.
