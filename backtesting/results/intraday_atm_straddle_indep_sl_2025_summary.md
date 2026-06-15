# 2025 Intraday ATM Straddle — Independent SL per Leg

## Strategy Details

- Entry time: `09:20` (sell ATM CE + PE)
- Exit time: `15:20` if SL not hit (day close)
- Stop loss: `2.0x` entry premium, independent per leg
- SL rule: each leg exits only itself when its own SL is hit; partner continues
- ATM rule: nearest 50 to spot open at entry time
- Expiry rule: expiry day → next week; otherwise current week
- Contract multiplier: 75 × 1 = 75 per point
- Slippage: 0.50 point per order
- Brokerage: Rs 25.00 per order, Rs 100.00 per straddle

## Results Summary

- Total traded days: `244`
- Total skipped days: `4`
- Winning days: `145`
- Losing days: `99`
- Days CE SL hit: `24`
- Days PE SL hit: `28`
- Days both SL hit: `0`
- Days neither SL hit: `192`
- Total Gross P/L: `65156.25`
- Total Brokerage: `24400.00`
- Total Net P/L: `40756.25`
- Max profit day: `2025-05-28` (Wednesday) net `12901.25`
- Max loss day: `2025-05-15` (Thursday) net `-9715.00`
- Peak cumulative profit: `41623.75`
- Max drawdown: `38647.00`

## Results by Day of Week

### Monday
- Trades: `50`  Win: `33`  Loss: `17`  CE-SL: `4`  PE-SL: `6`
- Net P/L: `19834.75`  Gross: `24834.75`  Brokerage: `5000.00`

### Tuesday
- Trades: `50`  Win: `35`  Loss: `15`  CE-SL: `3`  PE-SL: `8`
- Net P/L: `61268.50`  Gross: `66268.50`  Brokerage: `5000.00`

### Wednesday
- Trades: `48`  Win: `25`  Loss: `23`  CE-SL: `9`  PE-SL: `5`
- Net P/L: `-17877.00`  Gross: `-13077.00`  Brokerage: `4800.00`

### Thursday
- Trades: `47`  Win: `27`  Loss: `20`  CE-SL: `4`  PE-SL: `2`
- Net P/L: `-23768.75`  Gross: `-19068.75`  Brokerage: `4700.00`

### Friday
- Trades: `49`  Win: `25`  Loss: `24`  CE-SL: `4`  PE-SL: `7`
- Net P/L: `1298.75`  Gross: `6198.75`  Brokerage: `4900.00`

## Exceptions

- `2025-03-20` (Thursday): `missing_entry_candle`. NIFTY_23000_CE_27_MAR_25.csv missing 2025-03-20T09:20:00+05:30; NIFTY_23000_PE_27_MAR_25.csv missing 2025-03-20T09:20:00+05:30
- `2025-10-21` (Tuesday): `missing_spot_entry`. No spot candle at 2025-10-21T09:20:00+05:30.
- `2025-12-30` (Tuesday): `no_expiry_found`. No suitable expiry found.
- `2025-12-31` (Wednesday): `no_expiry_found`. No suitable expiry found.

## Remarks

- Each leg is managed independently — SL on one side does NOT affect the other.
- SL fill: gap open ≥ SL → fill at candle open; intrabar high ≥ SL → fill at SL price.
- Exact timestamp matching; no nearest-candle fallback.
- NIFTY spot file is source of truth for the trading calendar.
