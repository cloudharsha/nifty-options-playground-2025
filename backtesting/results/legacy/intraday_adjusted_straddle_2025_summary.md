# 2025 Intraday Adjusted Weekly Straddle Backtest

## Strategy Details

- Entry time: `09:30`
- Exit time: `15:20`
- Expiry rule: first weekly expiry on or after the entry date
- ATM rule: nearest 50 using spot 09:30 open
- Lot size and lots: `65` x `2`
- Contract multiplier: `130` rupees per option point
- Slippage: `1.00` point per order, applied against every executed entry and exit
- Brokerage: `Rs 25` per order per leg
- First-add band and target: `20%-30%`, target `25.00%` of the stronger-side value
- Rebalance band and target: `65%-85%`, target `75.00%` combined with the retained weak-side short
- Reversal rule: exit the smaller leg on the two-short side when the single-side value is `<= 100.00%` of the combined two-short side
- Adjustments are symmetric for upside and downside moves
- Final exit happens at the exact 15:20 open

## Results Summary

- No of trades: `79`
- No of adjustments: `121`
- Total Profit/Loss: `177017.00`
- Total Brokerage: `11600.00`
- Profit/Loss without Brokerage: `188617.00`

## Exception Trade Results

- No of exception trades: `168`
- No of exception adjustments before forced exit: `303`
- Total Exception Profit/Loss: `-371870.00`
- Total Exception Brokerage: `28150.00`
- Exception Profit/Loss without Brokerage: `-343720.00`
- Daywise file: `intraday_adjusted_straddle_2025_exception_daywise.csv`
- Events file: `intraday_adjusted_straddle_2025_exception_events.csv`
- These rows are not included in the main Results Summary totals.

## Exceptions

- `2025-12-31`: `no_same_or_next_weekly_expiry`. No weekly expiry folder exists on or after this entry date.

## Remarks

- Candidate days are limited to sessions with exact spot candles at `09:30` and `15:20`.
- The engine evaluates at most one adjustment cycle per minute, with `REVERSAL_EXIT` taking priority over trend adds and rebalances.
- Profit/Loss without Brokerage includes the configured execution slippage but excludes brokerage.
- Candidate-selection failures after entry are force-closed immediately and reported only in the exception trade result files.
- Other validation failures remain skipped when the engine cannot price every active leg.
- Same-day expiry trades are allowed because the expiry rule is `expiry >= entry_date`.
- `2025-10-21` is excluded as a candidate day because the spot dataset does not contain an exact `09:30` candle for that special session.
