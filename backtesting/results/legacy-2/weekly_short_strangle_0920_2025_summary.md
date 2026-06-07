# 2025 Weekly Short Strangle 09:20 Backtest

## Strategy Details

- Entry time: `09:20` option open
- Exit time: `15:20` option open
- Spot ATM rule: nearest 50 using the NIFTY entry-time open
- Expiry rule: first expiry folder on or after the trade date
- Short selection rule: sell OTM CE and OTM PE with each entry premium in the `20.00`-`30.00` band, choosing closest to `25.00`
- Stop rule: independent stop at `2.00x` each sold option's entry premium
- Target rule: independent target when each option trades at or below `10.00` points
- Stop fill rule: use stop price when touched intrabar; use candle open when it opens above the stop
- Target fill rule: use target price when touched intrabar; use candle open when it opens below the target
- Same-candle stop/target rule: stop-first fill
- Re-entry rule: none
- Pricing rule: exact timestamp matching; no nearest-candle fallback
- Contract multiplier: 65 x 4 = 260 rupees per option point
- Execution slippage: 1.00 point per order
- Brokerage rule: Rs 25.00 per order, Rs 100.00 per completed strangle

## Results Summary

- Total traded days: `218`
- Total skipped days: `31`
- Total leg trades: `436`
- Target leg exits: `139`
- Gap target leg exits: `1`
- Stop-loss leg exits: `103`
- Gap stop-loss leg exits: `1`
- Day-close leg exits: `192`
- Winning days: `111`
- Losing days: `107`
- Total Profit/Loss: `-147728.40`
- Total Brokerage: `21800.00`
- Profit/Loss without Brokerage: `-125928.40`
- Max profit day: `2025-09-09` with net P/L `7635.00`
- Max loss day: `2025-04-17` with net P/L `-16220.00`

## Output Files

- Daywise file: `weekly_short_strangle_0920_2025_daywise.csv`
- Trades file: `weekly_short_strangle_0920_2025_trades.csv`
- Log file: `weekly_short_strangle_0920_2025.log`

## Exceptions

- `2025-01-16`: `no_valid_strangle_in_premium_band`. No OTM CE contract satisfied the sell premium band 20.00-30.00 at 2025-01-16T09:20:00+05:30.
- `2025-02-06`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-02-06T09:20:00+05:30.
- `2025-02-20`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-02-20T09:20:00+05:30.
- `2025-02-27`: `no_valid_strangle_in_premium_band`. No OTM CE contract satisfied the sell premium band 20.00-30.00 at 2025-02-27T09:20:00+05:30.; No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-02-27T09:20:00+05:30.
- `2025-03-06`: `no_valid_strangle_in_premium_band`. No OTM CE contract satisfied the sell premium band 20.00-30.00 at 2025-03-06T09:20:00+05:30.
- `2025-03-13`: `no_valid_strangle_in_premium_band`. No OTM CE contract satisfied the sell premium band 20.00-30.00 at 2025-03-13T09:20:00+05:30.
- `2025-04-03`: `no_valid_strangle_in_premium_band`. No OTM CE contract satisfied the sell premium band 20.00-30.00 at 2025-04-03T09:20:00+05:30.
- `2025-04-07`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-04-07T09:20:00+05:30.
- `2025-04-24`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-04-24T09:20:00+05:30.
- `2025-04-30`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-04-30T09:20:00+05:30.
- `2025-05-08`: `no_valid_strangle_in_premium_band`. No OTM CE contract satisfied the sell premium band 20.00-30.00 at 2025-05-08T09:20:00+05:30.
- `2025-07-10`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-07-10T09:20:00+05:30.
- `2025-07-17`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-07-17T09:20:00+05:30.
- `2025-07-24`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-07-24T09:20:00+05:30.
- `2025-08-07`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-08-07T09:20:00+05:30.
- `2025-08-21`: `no_valid_strangle_in_premium_band`. No OTM CE contract satisfied the sell premium band 20.00-30.00 at 2025-08-21T09:20:00+05:30.; No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-08-21T09:20:00+05:30.
- `2025-09-02`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-09-02T09:20:00+05:30.
- `2025-09-16`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-09-16T09:20:00+05:30.
- `2025-09-22`: `no_valid_strangle_in_premium_band`. No OTM CE contract satisfied the sell premium band 20.00-30.00 at 2025-09-22T09:20:00+05:30.
- `2025-09-23`: `no_valid_strangle_in_premium_band`. No OTM CE contract satisfied the sell premium band 20.00-30.00 at 2025-09-23T09:20:00+05:30.; No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-09-23T09:20:00+05:30.
- `2025-10-06`: `no_valid_strangle_in_premium_band`. No OTM CE contract satisfied the sell premium band 20.00-30.00 at 2025-10-06T09:20:00+05:30.
- `2025-10-07`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-10-07T09:20:00+05:30.
- `2025-10-21`: `missing_spot_timestamp`. Missing spot entry timestamp 2025-10-21T09:20:00+05:30
- `2025-11-10`: `no_valid_strangle_in_premium_band`. No OTM CE contract satisfied the sell premium band 20.00-30.00 at 2025-11-10T09:20:00+05:30.
- `2025-12-02`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-12-02T09:20:00+05:30.
- `2025-12-16`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-12-16T09:20:00+05:30.
- `2025-12-22`: `no_valid_strangle_in_premium_band`. No OTM CE contract satisfied the sell premium band 20.00-30.00 at 2025-12-22T09:20:00+05:30.
- `2025-12-23`: `no_valid_strangle_in_premium_band`. No OTM CE contract satisfied the sell premium band 20.00-30.00 at 2025-12-23T09:20:00+05:30.
- `2025-12-29`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-12-29T09:20:00+05:30.
- `2025-12-30`: `no_valid_strangle_in_premium_band`. No OTM PE contract satisfied the sell premium band 20.00-30.00 at 2025-12-30T09:20:00+05:30.
- `2025-12-31`: `no_same_week_expiry`. No expiry folder exists on or after this trade date.

## Remarks

- The NIFTY spot file is the source of truth for the trading calendar and intraday monitoring timestamps.
- Raw 1-minute option candles from `Options_2025` are used directly.
- A day is skipped if either strangle leg lacks the needed entry, monitoring, or scheduled exit candle.
- Expiry folder dates are used as truth, which naturally handles non-Thursday expiry weeks.
