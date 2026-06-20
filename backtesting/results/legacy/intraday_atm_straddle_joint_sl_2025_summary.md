# 2025 Intraday ATM Straddle Joint-SL Backtest

## Strategy Details

- Entry time: `09:20` (sell ATM CE + PE)
- Exit time: `15:20` if no SL hit
- Stop loss: `2.0x` entry premium per leg
- Joint SL rule: if either leg hits SL, exit BOTH at same candle
  - SL leg: exits at stop price (or candle open if gap)
  - Partner leg: exits at current candle open
- ATM rule: nearest 50 to spot open at entry time
- Expiry rule: expiry day → next week; otherwise current week
- Contract multiplier: 75 × 1 = 75 per point
- Slippage: 0.50 point per order
- Brokerage: Rs 25.00 per order, Rs 100.00 per straddle

## Results Summary

- Total traded days: `244`
- Total skipped days: `4`
- Winning days: `143`
- Losing days: `101`
- Days SL triggered: `52`
- Days closed at 15:20: `192`
- Total Gross P/L: `40995.00`
- Total Brokerage: `24400.00`
- Total Net P/L: `16595.00`
- Max profit day: `2025-05-28` (Wednesday) net `12901.25`
- Max loss day: `2025-05-15` (Thursday) net `-11635.00`
- Peak cumulative profit: `26913.25`
- Max drawdown: `53756.50`

## Results by Day of Week

### Monday
- Trades: `50`  Win: `31`  Loss: `19`  SL hits: `10`
- Net P/L: `11561.50`  Gross: `16561.50`  Brokerage: `5000.00`

### Tuesday
- Trades: `50`  Win: `35`  Loss: `15`  SL hits: `11`
- Net P/L: `42241.00`  Gross: `47241.00`  Brokerage: `5000.00`

### Wednesday
- Trades: `48`  Win: `25`  Loss: `23`  SL hits: `14`
- Net P/L: `-7878.75`  Gross: `-3078.75`  Brokerage: `4800.00`

### Thursday
- Trades: `47`  Win: `27`  Loss: `20`  SL hits: `6`
- Net P/L: `-27788.75`  Gross: `-23088.75`  Brokerage: `4700.00`

### Friday
- Trades: `49`  Win: `25`  Loss: `24`  SL hits: `11`
- Net P/L: `-1540.00`  Gross: `3360.00`  Brokerage: `4900.00`

## Exceptions

- `2025-03-20` (Thursday): `missing_entry_candle`. NIFTY_23000_CE_27_MAR_25.csv missing 2025-03-20T09:20:00+05:30; NIFTY_23000_PE_27_MAR_25.csv missing 2025-03-20T09:20:00+05:30
- `2025-10-21` (Tuesday): `missing_spot_entry`. No spot candle at 2025-10-21T09:20:00+05:30.
- `2025-12-30` (Tuesday): `no_expiry_found`. No suitable expiry found.
- `2025-12-31` (Wednesday): `no_expiry_found`. No suitable expiry found.

## Remarks

- SL fill: gap open ≥ SL → fill at candle open; intrabar high ≥ SL → fill at SL price.
- Partner leg exits at same candle open when SL fires on the other leg.
- Exact timestamp matching; no nearest-candle fallback.
- NIFTY spot file is source of truth for the trading calendar.
