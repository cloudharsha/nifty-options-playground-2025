# 2025 Next-Week Short Iron Condor Backtest

## Strategy Details

- Entry rule: trading Mondays at exact `09:30` open
- Exit rule: next calendar Monday at exact `09:25` open
- Expiry rule: first available expiry folder strictly after the planned next-Monday exit date
- ATM rule: nearest 50 using spot entry open
- Short selection rule: sell OTM CE and OTM PE with entry premiums in the 25.00-35.00 band, choosing closest to 30.00
- Wing selection rule: buy further OTM CE and PE with entry premiums in the 25%-35% band of each sold leg, choosing closest to 33.33%
- Pricing rule: option open price at exact timestamps
- Contract multiplier: 65 x 4 = 260 rupees per option point
- Execution slippage: 1.00 point per order, applied against every entry and exit
- Brokerage rule: Rs 25 per order per leg, Rs 200 per completed iron condor
- Adjustments: none

## Results Summary

- No of Monday candidates: `50`
- No of trades: `46`
- No of adjustments: `0`
- Total Profit/Loss: `-21321.20`
- Total Brokerage: `9200.00`
- Profit/Loss without Brokerage: `-12121.20`

## Exceptions

- `2025-03-24`: `no_planned_exit_trading_day`. Spot file is missing exact planned exit timestamp 2025-03-31T09:25:00+05:30.
- `2025-04-07`: `no_planned_exit_trading_day`. Spot file is missing exact planned exit timestamp 2025-04-14T09:25:00+05:30.
- `2025-05-12`: `no_valid_wing_candidate`. No OTM PE buy wing contract satisfied the premium band 7.31-10.24 at 2025-05-12T09:30:00+05:30 while also having exact exit timestamp 2025-05-19T09:25:00+05:30.
- `2025-12-29`: `no_planned_exit_trading_day`. Spot file is missing exact planned exit timestamp 2026-01-05T09:25:00+05:30.

## Remarks

- The backtest uses exact timestamp matching for both entry and exit; no nearest-candle fallback is allowed.
- Profit/Loss without Brokerage includes the configured execution slippage but excludes brokerage.
- The NIFTY spot file is the source of truth for Monday entries and planned exit-session availability.
- The OTM call side is selected from strikes above the reference strike, and the OTM put side is selected from strikes below it.
- If no valid sell or wing candidate exists in the requested premium band on either side, the full trade is skipped.
- Missing next-Monday sessions, special sessions, and end-of-dataset gaps are recorded in the exceptions section.
