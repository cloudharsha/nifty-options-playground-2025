# 2025 15-Minute Same-Week ATM MA Short Options Backtest With Intraday First Entry

## Strategy Details

- ATM reference time: `09:30`
- Last fresh-entry time: `15:00`
- Exit time: `15:15`
- Spot ATM rule: fixed nearest 50 using the NIFTY 09:30 open
- Expiry rule: first expiry folder on or after the trade date
- Entry rule: monitor the fixed 09:30 ATM CE and PE independently from 09:30 through 15:00; sell the first bar whose open is below the prior 25-close SMA
- Trailing stop rule: every later 15-minute bar recalculates the prior 25-close SMA; exit when that bar open is above the updated SMA
- MA source: option close
- Re-entry rule: each leg may trade at most once per day
- Pricing rule: exact option open price at exact timestamps
- Contract multiplier: 65 x 4 = 260 rupees per option point
- Execution slippage: 1.00 point per order, applied against every entry and exit
- Brokerage rule: Rs 25 per order, so one-leg trades pay Rs 50 and two-leg trades pay Rs 100 at the current settings

## Results Summary

- Total traded days: `247`
- Total skipped days: `2`
- CE-only trade count: `21`
- PE-only trade count: `23`
- Both-legs trade count: `203`
- Total Profit/Loss: `510661.20`
- Total Brokerage: `22500.00`
- Profit/Loss without Brokerage: `533161.20`

## Exceptions

- `2025-10-21`: `missing_spot_timestamp`. Missing spot monitoring timestamps: 2025-10-21T09:30:00+05:30, 2025-10-21T09:45:00+05:30, 2025-10-21T10:00:00+05:30, 2025-10-21T10:15:00+05:30, 2025-10-21T10:30:00+05:30, 2025-10-21T10:45:00+05:30, 2025-10-21T11:00:00+05:30, 2025-10-21T11:15:00+05:30, 2025-10-21T11:30:00+05:30, 2025-10-21T11:45:00+05:30, 2025-10-21T12:00:00+05:30, 2025-10-21T12:15:00+05:30, 2025-10-21T12:30:00+05:30, 2025-10-21T12:45:00+05:30, 2025-10-21T13:00:00+05:30, 2025-10-21T13:15:00+05:30, 2025-10-21T13:30:00+05:30, 2025-10-21T15:00:00+05:30, 2025-10-21T15:15:00+05:30
- `2025-12-31`: `no_same_week_expiry`. No expiry folder exists on or after this trade date.

## Remarks

- Exact timestamp matching is required; no nearest-candle fallback is allowed.
- ATM is fixed once from the 09:30 spot open and does not roll intraday.
- CE and PE are monitored independently for first entry through the last-entry bar.
- `15:15` is exit-only in this strategy variant.
- Expiry folder dates are used as truth, which naturally handles Tuesday special expiries.
- No intraday re-entry is allowed after a leg exits.
