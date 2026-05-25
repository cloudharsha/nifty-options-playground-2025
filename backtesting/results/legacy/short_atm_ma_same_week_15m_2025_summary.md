# 2025 15-Minute Same-Week ATM MA Short Options Backtest

## Strategy Details

- Entry time: `09:30`
- Exit time: `15:15`
- Spot ATM rule: nearest 50 using the NIFTY 09:30 open
- Expiry rule: first expiry folder on or after the trade date
- Signal rule: option 09:30 open below prior 25-close SMA
- Stop rule: later bar open above prior 25-close SMA
- MA source: option close
- Re-entry rule: none
- Pricing rule: exact option open price at exact timestamps
- Contract multiplier: 65 x 4 = 260 rupees per option point
- Execution slippage: 1.00 point per order, applied against every entry and exit
- Brokerage rule: Rs 25 per order, so one-leg trades pay Rs 50 and two-leg trades pay Rs 100 at the current settings

## Results Summary

- Total traded days: `246`
- Total skipped days: `3`
- CE-only trade count: `82`
- PE-only trade count: `76`
- Both-legs trade count: `88`
- Total Profit/Loss: `493017.00`
- Total Brokerage: `16700.00`
- Profit/Loss without Brokerage: `509717.00`

## Exceptions

- `2025-05-07`: `no_entry_signal`. NIFTY_24450_CE_08_MAY_25.csv open 71.7 is not below SMA 44.45 at 2025-05-07T09:30:00+05:30; NIFTY_24450_PE_08_MAY_25.csv open 111.2 is not below SMA 106.66 at 2025-05-07T09:30:00+05:30
- `2025-10-21`: `missing_spot_timestamp`. Missing spot entry timestamp 2025-10-21T09:30:00+05:30; Missing spot exit timestamp 2025-10-21T15:15:00+05:30
- `2025-12-31`: `no_same_week_expiry`. No expiry folder exists on or after this trade date.

## Remarks

- Exact timestamp matching is required; no nearest-candle fallback is allowed.
- This strategy uses the 15-minute NIFTY spot file and the derived 15-minute options dataset.
- `15:15` is the end-of-day execution proxy because the dataset does not contain an exact `15:20` timestamp.
- Expiry folder dates are used as truth, which naturally handles Tuesday special expiries.
- One side may trade even if the other side is unavailable or has no signal.
- No intraday re-entry is allowed after a side exits.
