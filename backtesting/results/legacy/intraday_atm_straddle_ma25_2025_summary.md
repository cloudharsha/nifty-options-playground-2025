# 2025 Intraday ATM Straddle — 25-period 15m MA Filter

## Strategy Details

- Entry time: `09:40` — sell ATM CE/PE only if price < 25-period 15m MA
- Exit time: `15:20` if SL not triggered (1m candle open)
- MA period: `25` candles on 15-minute chart
- MA check candle: `09:15` (last complete 15m bar before entry)
- Entry condition: option open at 09:40 < 25-period MA → sell; else skip that leg
- SL rule: exit when price crosses above rolling 25-period 15m MA (dynamic level)
- SL fill: gap open ≥ MA → fill at candle open; intrabar high ≥ MA → fill at MA
- Partial straddle: only qualifying legs are sold
- ATM rule: nearest 50 to spot open at 09:40
- Expiry rule: expiry day → next week; otherwise current week
- Contract multiplier: 75 × 1 = 75 per point
- Slippage: 0.50 pts per order (entry + exit = 2× per leg)
- Brokerage: Rs 25.00 per order; partial = Rs 50.00, full = Rs 100.00
- Data: 1m from `Options_2025/` (entry/exit prices); 15m from `Options_2025_15m/` (MA + SL)

## Results Summary

- Total active days: `243` (full straddle: `73`, partial: `170`)
- Total skipped days: `5`
- Winning days: `120`
- Losing days: `123`
- Days CE SL hit: `112`
- Days PE SL hit: `117`
- Total Gross P/L: `51510.36`
- Total Brokerage: `15800.00`
- Total Net P/L: `35710.36`
- Max profit day: `2025-01-02` (Thursday) net `10476.25`
- Max loss day: `2025-05-02` (Friday) net `-8683.34`
- Peak cumulative profit: `48038.37`
- Max drawdown: `24078.33`

## Results by Day of Week

### Monday
- Trades: `50`  Full: `14`  Partial: `36`  Win: `24`  Loss: `26`  CE-SL: `24`  PE-SL: `20`
- Net P/L: `-515.60`  Gross: `2684.40`  Brokerage: `3200.00`

### Tuesday
- Trades: `50`  Full: `15`  Partial: `35`  Win: `24`  Loss: `26`  CE-SL: `20`  PE-SL: `27`
- Net P/L: `-2564.26`  Gross: `685.74`  Brokerage: `3250.00`

### Wednesday
- Trades: `47`  Full: `25`  Partial: `22`  Win: `21`  Loss: `26`  CE-SL: `29`  PE-SL: `28`
- Net P/L: `-5586.39`  Gross: `-1986.39`  Brokerage: `3600.00`

### Thursday
- Trades: `47`  Full: `12`  Partial: `35`  Win: `22`  Loss: `25`  CE-SL: `18`  PE-SL: `27`
- Net P/L: `7861.46`  Gross: `10811.46`  Brokerage: `2950.00`

### Friday
- Trades: `49`  Full: `7`  Partial: `42`  Win: `29`  Loss: `20`  CE-SL: `21`  PE-SL: `15`
- Net P/L: `36515.15`  Gross: `39315.15`  Brokerage: `2800.00`

## Skipped Summary

- `no_ma_signal`: 2 days
- `no_expiry_found`: 2 days
- `missing_spot_entry`: 1 days

## Exceptions

- `2025-03-06` (Thursday): `no_ma_signal`. CE price 204.75 >= MA 202.12; PE price 151.40 >= MA 151.18
- `2025-05-07` (Wednesday): `no_ma_signal`. CE price 94.75 >= MA 66.54; PE price 93.60 >= MA 78.83
- `2025-10-21` (Tuesday): `missing_spot_entry`. No spot candle at 2025-10-21T09:40:00+05:30.
- `2025-12-30` (Tuesday): `no_expiry_found`. No suitable expiry found.
- `2025-12-31` (Wednesday): `no_expiry_found`. No suitable expiry found.

## Remarks

- 25-period MA is computed from `Options_2025_15m/` (15-minute bars).
- MA at entry uses the `09:15` candle — last complete 15m bar before 09:40.
- SL monitoring starts from `09:45` candle; the 09:40–09:44 window is unmonitored.
- MA is re-computed at every 15m candle intraday (rolling window — dynamic SL level).
- If MA unavailable at a monitoring candle, that candle is skipped for SL purposes.
- Partial straddle: if only one leg is below MA, only that leg is sold.
- NIFTY spot file is source of truth for the trading-day calendar.
