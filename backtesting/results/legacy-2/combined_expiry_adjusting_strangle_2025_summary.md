# 2025 Combined Expiry + Adjusting Short Strangle Backtest

## Strategy Details

- Spot file: `C:\Users\harsh\Desktop\workspace\git\nifty-options-playground-2025\nifty\NIFTY50_INDEX_1m_2025.csv`
- Options directory: `C:\Users\harsh\Desktop\workspace\git\nifty-options-playground-2025\Options_2025`
- Expiry-day strategy: sell expiring ATM+100 CE and ATM-100 PE at 09:20, per-leg SL at 2x entry, exit at 15:25.
- Adjustment-cycle strategy: sell this-expiry far OTM strangle from the day after previous expiry through the day before this expiry.
- Adjustment entry band: 0.0833%-0.1250% of spot, min OTM 1.25% of spot.
- Re-entry band: 0.0417%-0.0625% of spot after a position closes.
- Intraday roll: when one active leg decays to 50% or less of its sell price, roll that leg closer to ATM.
- EOD rebalance: from 15:20, roll the cheaper leg closer to ATM when CE/PE premium gap is above 20%, except on cycle-end day.
- Sizing: capital Rs 1000000.00, compound `True`, lot size `65`, margin rate `0.20`.
- Pricing: option close is used for entries, monitoring, rolls, and exits; last available row at or before the timestamp is used.
- Events file support from the provided script is not used because this repo does not include that market-events config.

## Overall Results

| Period | Active | Expiry | Adjust | Expiry P/L | Adjust P/L | Total P/L | Return % | Max DD | Win % | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ALL | 99 | 53 | 46 | 162742.31 | 89300.38 | 252042.69 | 25.20 | 69261.93 | 66.67 | 2.13 |

## Yearly Results

| Period | Active | Expiry | Adjust | Expiry P/L | Adjust P/L | Total P/L | Return % | Max DD | Win % | PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2025 | 99 | 53 | 46 | 162742.31 | 89300.38 | 252042.69 | 25.20 | 69261.93 | 66.67 | 2.13 |

## Counts

- Expiry trades: `53` traded, `0` skipped
- Adjust cycles: `46` traded, `7` skipped
- Leg events: `540`
- Final equity: `Rs 1252042.69`

## Close Reasons

- `cycle_end`: `36`
- `decay_50`: `124`
- `eod_gap`: `70`
- `no_roll_available`: `34`
- `scheduled_exit`: `68`
- `sl_2.00x`: `38`
- `tp`: `170`

## Skips

- Adjust `2025-09-02` (2025-08-29 to 2025-09-01): `no_initial_entry_strikes`. No initial CE/PE strikes found in premium band 20.42-30.65 with min OTM 306.00.
- Adjust `2025-09-23` (2025-09-17 to 2025-09-22): `no_initial_entry_strikes`. No initial CE/PE strikes found in premium band 21.08-31.63 with min OTM 316.00.
- Adjust `2025-09-30` (2025-09-24 to 2025-09-29): `no_initial_entry_strikes`. No initial CE/PE strikes found in premium band 20.87-31.32 with min OTM 313.00.
- Adjust `2025-10-14` (2025-10-08 to 2025-10-13): `no_initial_entry_strikes`. No initial CE/PE strikes found in premium band 20.96-31.46 with min OTM 315.00.
- Adjust `2025-10-20` (2025-10-15 to 2025-10-17): `no_initial_entry_strikes`. No initial CE/PE strikes found in premium band 21.04-31.58 with min OTM 316.00.
- Adjust `2025-12-23` (2025-12-17 to 2025-12-22): `no_initial_entry_strikes`. No initial CE/PE strikes found in premium band 21.57-32.37 with min OTM 324.00.
- Adjust `2025-12-30` (2025-12-24 to 2025-12-29): `no_initial_entry_strikes`. No initial CE/PE strikes found in premium band 21.84-32.77 with min OTM 328.00.

## Output Files

- Expiry trades: `combined_expiry_adjusting_strangle_2025_expiry_trades.csv`
- Adjust cycles: `combined_expiry_adjusting_strangle_2025_adjust_cycles.csv`
- Leg events: `combined_expiry_adjusting_strangle_2025_events.csv`
- Equity curve: `combined_expiry_adjusting_strangle_2025_equity.csv`
- Summary CSV: `combined_expiry_adjusting_strangle_2025_summary.csv`
- Log: `combined_expiry_adjusting_strangle_2025.log`
