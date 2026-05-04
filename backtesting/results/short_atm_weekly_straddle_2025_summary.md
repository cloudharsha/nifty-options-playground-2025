# 2025 Overnight Weekly Short ATM Straddle Backtest

## Strategy Details

- Entry time: `15:20`
- Exit time: `09:16`
- ATM rule: nearest 50 using spot 15:20 open
- Expiry rule: first weekly expiry strictly after entry date
- Pricing rule: option open price at exact timestamps
- Brokerage rule: Rs 25 per order per leg, Rs 100 per completed straddle
- Adjustments: none

## Results Summary

- No of trades: `245`
- No of adjustments: `0`
- Total Profit/Loss: `-23467.40`
- Total Brokerage: `24500.00`
- Profit/Loss without Brokerage: `1032.60`

## Exceptions

- `2025-10-20`: `missing_entry_or_exit_timestamp`. NIFTY_25850_CE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; NIFTY_25850_PE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; Next trading day is a special session that starts at 13:45, so the exact 09:16 exit candle is unavailable.
- `2025-12-30`: `no_next_weekly_expiry`. No later weekly expiry folder exists in the dataset.
- `2025-12-31`: `no_next_trading_day`. No next trading day exists in the dataset.

## Remarks

- The backtest uses exact timestamp matching for both entry and exit; no nearest-candle fallback is allowed.
- The NIFTY spot file is the source of truth for the trading calendar.
- `2025-10-21` is a special session that starts at `13:45`, which is why the `2025-10-20` trade is skipped.
- `2025-12-30` is skipped because there is no later weekly expiry folder in the dataset.
- `2025-12-31` is skipped because there is no next trading day available in the dataset.
