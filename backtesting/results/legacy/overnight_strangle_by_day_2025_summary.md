# 2025 Overnight Short Strangle by Day Backtest

## Strategy Details

- Entry time: `15:20` (sell)
- Exit time: `09:20` next trading day (buy back)
- ATM rule: nearest 50 using spot open at entry time
- Expiry rule: if entry day is expiry day → next week expiry; otherwise → current week expiry
- CE selection: OTM CE closest to ATM with price in band
- PE selection: OTM PE closest to ATM with price in band
- Premium bands by day (primary → fallback if not found):
  - Monday: 5-10 → 5-15
  - Tuesday (expiry, next week): 20-25 → 20-30
  - Wednesday: 20-25 → 20-30
  - Thursday: 15-20 → 15-25
  - Friday: 10-15 → 10-20
- Contract multiplier: 75 × 1 = 75 per point
- Slippage: 0.50 point per order
- Brokerage: Rs 25.00 per order, Rs 100.00 per strangle

## Results Summary

- Total traded days: `238`
- Total skipped days: `10`
- Winning days: `149`
- Losing days: `89`
- Total Gross P/L: `-2981.25`
- Total Brokerage: `23800.00`
- Total Net P/L: `-26781.25`
- Max profit day: `2025-04-08` (Tuesday) net `2371.25`
- Max loss day: `2025-04-04` (Friday) net `-40771.75`
- Peak cumulative profit: `1400.25`
- Max drawdown: `43118.50`

## Results by Day of Week

### Monday
- Trades: `48`  Win: `32`  Loss: `16`
- Net P/L: `-3131.25`  Gross: `1668.75`  Brokerage: `4800.00`

### Tuesday
- Trades: `48`  Win: `31`  Loss: `17`
- Net P/L: `12378.00`  Gross: `17178.00`  Brokerage: `4800.00`

### Wednesday
- Trades: `45`  Win: `37`  Loss: `8`
- Net P/L: `20566.50`  Gross: `25066.50`  Brokerage: `4500.00`

### Thursday
- Trades: `48`  Win: `20`  Loss: `28`
- Net P/L: `-12091.50`  Gross: `-7291.50`  Brokerage: `4800.00`

### Friday
- Trades: `49`  Win: `29`  Loss: `20`
- Net P/L: `-44503.00`  Gross: `-39603.00`  Brokerage: `4900.00`

## Exceptions

- `2025-03-05` (Wednesday): `no_valid_strangle`. No OTM CE contract with premium in [20.00, 30.00] having both entry 2025-03-05T15:20:00+05:30 and exit 2025-03-06T09:20:00+05:30.
- `2025-03-18` (Tuesday): `no_valid_strangle`. No OTM CE contract with premium in [20.00, 30.00] having both entry 2025-03-18T15:20:00+05:30 and exit 2025-03-19T09:20:00+05:30.
- `2025-03-19` (Wednesday): `no_valid_strangle`. No OTM CE contract with premium in [20.00, 30.00] having both entry 2025-03-19T15:20:00+05:30 and exit 2025-03-20T09:20:00+05:30.
- `2025-03-25` (Tuesday): `no_valid_strangle`. No OTM CE contract with premium in [20.00, 30.00] having both entry 2025-03-25T15:20:00+05:30 and exit 2025-03-26T09:20:00+05:30.
- `2025-04-07` (Monday): `no_valid_strangle`. No OTM PE contract with premium in [5.00, 15.00] having both entry 2025-04-07T15:20:00+05:30 and exit 2025-04-08T09:20:00+05:30.
- `2025-08-20` (Wednesday): `no_valid_strangle`. No OTM CE contract with premium in [20.00, 30.00] having both entry 2025-08-20T15:20:00+05:30 and exit 2025-08-21T09:20:00+05:30.
- `2025-10-20` (Monday): `no_valid_strangle`. No OTM CE contract with premium in [5.00, 15.00] having both entry 2025-10-20T15:20:00+05:30 and exit 2025-10-21T09:20:00+05:30.; No OTM PE contract with premium in [5.00, 15.00] having both entry 2025-10-20T15:20:00+05:30 and exit 2025-10-21T09:20:00+05:30.
- `2025-10-21` (Tuesday): `missing_spot_entry`. No spot candle at 2025-10-21T15:20:00+05:30.
- `2025-12-30` (Tuesday): `no_expiry_found`. No suitable expiry folder found.
- `2025-12-31` (Wednesday): `no_next_trading_day`. No next trading day in dataset.

## Remarks

- Exact timestamp matching only; no nearest-candle fallback.
- A day is skipped if no OTM CE or PE satisfies the band with both entry and exit candles.
- NIFTY spot file is the source of truth for the trading calendar.
- Tuesday is treated as expiry day when that date has an expiry folder.
