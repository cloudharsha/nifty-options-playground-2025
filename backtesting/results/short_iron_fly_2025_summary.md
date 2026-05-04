# 2025 Overnight Short Iron Fly Backtest

## Strategy Details

- Entry time: `15:20`
- Exit time: `09:16`
- ATM rule: nearest 50 using spot 15:20 open
- Expiry rule: first weekly expiry strictly after entry date
- Sold legs: ATM CE and ATM PE at exact entry timestamp open price
- Wing selection rule: buy OTM CE and OTM PE with entry premiums in the 25% to 35% band of their respective sold ATM leg, choosing the candidate closest to 33.33%
- Pricing rule: option open price at exact timestamps
- Contract multiplier: 65 x 4 = 260 rupees per option point
- Execution slippage: 1.00 point per order, applied against every entry and exit
- Brokerage rule: Rs 25 per order per leg, Rs 200 per completed iron fly
- Adjustments: none

## Results Summary

- No of trades: `232`
- No of adjustments: `0`
- Total Profit/Loss: `-433828.60`
- Total Brokerage: `46400.00`
- Profit/Loss without Brokerage: `-387428.60`

## Exceptions

- `2025-06-04`: `no_valid_wing_in_premium_band`. No PE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.
- `2025-07-23`: `no_valid_wing_in_premium_band`. No CE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.
- `2025-08-20`: `no_valid_wing_in_premium_band`. No CE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.
- `2025-08-25`: `no_valid_wing_in_premium_band`. No CE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.
- `2025-09-29`: `no_valid_wing_in_premium_band`. No CE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.
- `2025-10-03`: `no_valid_wing_in_premium_band`. No CE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.
- `2025-10-09`: `no_valid_wing_in_premium_band`. No CE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.
- `2025-10-13`: `no_valid_wing_in_premium_band`. No CE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.
- `2025-10-20`: `missing_atm_entry_or_exit_timestamp`. NIFTY_25850_CE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; NIFTY_25850_PE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; Next trading day is a special session that starts at 13:45, so the exact 09:16 exit candle is unavailable.
- `2025-11-28`: `no_valid_wing_in_premium_band`. No CE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.
- `2025-12-01`: `no_valid_wing_in_premium_band`. No CE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.
- `2025-12-15`: `no_valid_wing_in_premium_band`. No CE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.; No PE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.
- `2025-12-24`: `no_valid_wing_in_premium_band`. No CE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.
- `2025-12-29`: `no_valid_wing_in_premium_band`. No CE wing contract satisfied the 25%-35% premium band with exact entry/exit timestamps.
- `2025-12-30`: `no_next_weekly_expiry`. No later weekly expiry folder exists in the dataset.
- `2025-12-31`: `no_next_trading_day`. No next trading day exists in the dataset.

## Remarks

- The backtest uses exact timestamp matching for both entry and exit; no nearest-candle fallback is allowed.
- Profit/Loss without Brokerage includes the configured execution slippage but excludes brokerage.
- The NIFTY spot file is the source of truth for the trading calendar.
- The OTM call wing is selected from strikes above ATM, and the OTM put wing is selected from strikes below ATM.
- If no valid wing exists in the requested premium band on either side, the full trade is skipped.
- Special-session and end-of-dataset skips are recorded in the exceptions section rather than stopping the run.
