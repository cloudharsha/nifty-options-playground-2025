# 2025 Intraday Joint-SL Short Strangle Backtest

## Strategy Details

- Entry time: `09:20` (sell OTM CE + PE)
- Exit time: `15:20` if no SL hit (day close)
- Stop loss: `2.0x` entry premium per leg
- Joint SL rule: if either leg hits SL, exit BOTH immediately at same candle
  - SL leg: exits at stop price (or candle open if gap)
  - Partner leg: exits at current candle open
- Expiry rule: expiry day → next week; otherwise current week
- Premium bands (primary → fallback):
  - Monday: 5-10 → 5-15
  - Tuesday (expiry, next week): 20-25 → 20-30
  - Wednesday: 20-25 → 20-30
  - Thursday: 15-20 → 15-25
  - Friday: 10-15 → 10-20
- Contract multiplier: 75 × 1 = 75 per point
- Slippage: 0.50 point per order
- Brokerage: Rs 25.00 per order, Rs 100.00 per strangle

## Results Summary

- Total traded days: `244`
- Total skipped days: `4`
- Winning days: `129`
- Losing days: `115`
- Days SL triggered: `85`
- Days closed at 15:20: `159`
- Total Gross P/L: `-2804.25`
- Total Brokerage: `24400.00`
- Total Net P/L: `-27204.25`
- Max profit day: `2025-05-28` (Wednesday) net `2431.25`
- Max loss day: `2025-01-29` (Wednesday) net `-2848.75`
- Peak cumulative profit: `2260.75`
- Max drawdown: `35332.00`

## Results by Day of Week

### Monday
- Trades: `49`  Win: `28`  Loss: `21`  SL hits: `11`
- Net P/L: `-3818.50`  Gross: `1081.50`  Brokerage: `4900.00`

### Tuesday
- Trades: `50`  Win: `31`  Loss: `19`  SL hits: `17`
- Net P/L: `6700.75`  Gross: `11700.75`  Brokerage: `5000.00`

### Wednesday
- Trades: `48`  Win: `23`  Loss: `25`  SL hits: `21`
- Net P/L: `-8616.75`  Gross: `-3816.75`  Brokerage: `4800.00`

### Thursday
- Trades: `48`  Win: `24`  Loss: `24`  SL hits: `16`
- Net P/L: `-9629.25`  Gross: `-4829.25`  Brokerage: `4800.00`

### Friday
- Trades: `49`  Win: `23`  Loss: `26`  SL hits: `20`
- Net P/L: `-11840.50`  Gross: `-6940.50`  Brokerage: `4900.00`

## Exceptions

- `2025-04-07` (Monday): `no_valid_strangle`. No OTM PE in [5.00, 15.00] at 2025-04-07T09:20:00+05:30.
- `2025-10-21` (Tuesday): `missing_spot_entry`. No spot candle at 2025-10-21T09:20:00+05:30.
- `2025-12-30` (Tuesday): `no_expiry_found`. No suitable expiry found.
- `2025-12-31` (Wednesday): `no_expiry_found`. No suitable expiry found.

## Remarks

- SL fill rule: gap open above SL → fill at candle open; intrabar high crosses SL → fill at SL price.
- Partner leg fill: exits at the same candle's open when SL fires on the other leg.
- Exact timestamp matching; no nearest-candle fallback.
- NIFTY spot file is the source of truth for the trading calendar.
