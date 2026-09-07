# Combined Human Strategy — NIFTY Intraday (2020-2026)

## Strategy Parameters

| Parameter | Value |
|-----------|-------|
| Signal | 25-SMA direction on 15-min NIFTY spot at 09:30 |
| Entry filter | |spot - SMA| >= 50 pts (skip indecision) |
| Re-entry filter | |spot - SMA| >= 25 pts |
| SL (GTT) | Premium rises to 2.50x entry |
| Target (GTT) | Premium falls to 0.40x entry (60% credit captured) |
| Monitoring | Every 15 minutes |
| Daily stop-out cap | 2 (premium_sl + sma_cross_exit) |
| Last entry | 13:30 |
| Mandatory close | 15:15 |
| Brokerage/order | Rs 25 |
| Slippage/order | 1.0 pts |

## Overall Results (2020-2026)

| Metric | Value |
|--------|-------|
| Capital base | Rs 10,00,000 |
| Net P/L | -Rs 341,725 |
| Gross P/L | -Rs 245,625 |
| Brokerage + slippage | Rs 96,100 |
| CAGR | -5.45% |
| Total days in data | 1851 |
| Traded days | 1441 |
| Skipped days | 410 |
| Win days | 766 |
| Loss days | 675 |
| Win rate (day) | 53.2% |
| Max drawdown | Rs 790,135 |
| Max consec win days | 8 |
| Max consec loss days | 11 |
| Days with 2-SL cap hit | 330 |
| Best day | 2024-06-04 — Rs 93,370 |
| Worst day | 2020-03-19 — -Rs 95,965 |

## Trade-Level Stats

| Metric | Value |
|--------|-------|
| Total trades executed | 1922 |
| CE trades | 889 |
| PE trades | 1033 |

## Exit Reason Breakdown

| Exit Reason | Count | % | Notes |
|-------------|-------|---|-------|
| target_hit | 328 | 17.1% | 60% credit captured — done for day |
| premium_sl | 28 | 1.5% | GTT SL fired (counts toward cap) |
| sma_touch_exit | 1245 | 64.8% | SMA touched in 15-min candle (counts toward cap) |
| day_close | 321 | 16.7% | Mandatory close at 15:15 |

## Yearly Breakdown

| Year | Traded Days | Wins | Losses | Win% | Net P/L |
|------|-------------|------|--------|------|---------|
| 2020 | 222 | 120 | 102 | 54.1% | -Rs 75,290 |
| 2021 | 227 | 126 | 101 | 55.5% | Rs 198,985 |
| 2022 | 234 | 115 | 119 | 49.1% | -Rs 410,830 |
| 2023 | 205 | 104 | 101 | 50.7% | -Rs 136,265 |
| 2024 | 232 | 118 | 114 | 50.9% | -Rs 77,332 |
| 2025 | 224 | 130 | 94 | 58.0% | Rs 203,898 |
| 2026 | 97 | 53 | 44 | 54.6% | -Rs 44,891 |

## vs Baseline Strategies

| Strategy | CAGR | Max DD | Notes |
|----------|------|--------|-------|
| Base intraday (full participation) | 31.48% | Rs 1,36,705 | Trailing SMA stop, no cap |
| With-SL-cap 30% skip | 27.43% | Rs 1,16,493 | 2-SL cap + random skip |
| MA-gap-100 + SL-cap 30% | 22.83% | Rs 1,21,120 | Additional max-gap filter |
| **This strategy (combined-human)** | **-5.45%** | **Rs 790,135** | Min-gap + premium SL + target + 15-min monitoring |

## Notes

- **Min-gap filter**: entry skipped when |spot - SMA| < 50 pts. Unlike the magap backtest (which skips when gap is TOO LARGE), this skips when the market is too flat (no directional conviction).
- **Premium SL** (2.50x): simulates a GTT buy-back order placed at entry. Fires automatically even if the human is not watching.
- **Target** (0.40x = 60% credit): simulates a GTT take-profit. When hit, trading stops for the day.
- **SMA cross exit**: at each 15-min check, if NIFTY 15-min close is on the wrong side of SMA, exit manually at the next candle open price.
- **15-min monitoring**: option premium checked at candle OPEN; NIFTY spot checked at the CLOSE of the just-completed candle.
- **2-SL cap**: after 2 stop-outs (premium_sl or sma_cross_exit) in one day, no further entries taken.
- **Re-entry direction**: always determined fresh from SMA position at re-entry time (not locked to original trade direction).
- CAGR uses Rs 10,00,000 capital reference. Actual deployed capital should be 70% of account (30% buffer for margin safety — not modeled here).
