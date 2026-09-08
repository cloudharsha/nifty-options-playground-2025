# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the centre strike and PE the same distance below
- Balance filter: CE and PE premiums must be within `20%` (min/max >= 80%)
- Balancing by **centre shift**: move both legs together by 50 points — 0, +50, -50, ... out to ±5 strikes. A strangle keeps its symmetric strike distance.
- Unbalanced days are entered at the best available pair
- Stop loss: **independent per leg**, triggered when a leg reaches `180%` of its entry price (80% loss on that leg). The other leg keeps running.
- Exit: anything still open is closed at `15:20`
- No target, no adjustment, no re-entry
- Quantity: ~300 (expiry-aware lot sizing: 75/50/25/75/65 by era)
- Brokerage: Rs 25/order → Rs 100 per completed position
- Slippage: 0.50 pt/order
- Period: `2020-01-02` to `2026-06-16`

## Comparison

Margin is modelled — 10% of contract value per naked short lot with the lighter side netted at 30% — not SPAN. Verify before sizing.

| Variant | Traded | Skipped | Win% | Net P/L | CAGR on peak margin | Peak margin | Max DD | PF | Avg/day |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| STRADDLE | 331 | 3 | 61.9% | Rs 847,574 | 9.21% | Rs 1,106,950 | Rs 73,667 | 1.69 | Rs 2,561 |
| STRANGLE_100 | 331 | 3 | 55.6% | Rs 625,094 | 7.17% | Rs 1,109,225 | Rs 55,431 | 2.08 | Rs 1,889 |
| STRANGLE_200 | 331 | 3 | 51.4% | Rs 326,144 | 4.07% | Rs 1,111,500 | Rs 27,141 | 2.22 | Rs 985 |
| STRANGLE_300 | 331 | 3 | 38.7% | Rs 114,461 | 1.53% | Rs 1,113,775 | Rs 19,954 | 1.74 | Rs 346 |

## Stop-loss behaviour

| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |
|---|---:|---:|---:|---:|
| STRADDLE | 32 (9.7%) | 240 (72.5%) | 59 (17.8%) | 57 (17.2%) |
| STRANGLE_100 | 40 (12.1%) | 217 (65.6%) | 74 (22.4%) | 89 (26.9%) |
| STRANGLE_200 | 28 (8.5%) | 176 (53.2%) | 127 (38.4%) | 180 (54.4%) |
| STRANGLE_300 | 16 (4.8%) | 138 (41.7%) | 177 (53.5%) | 235 (71.0%) |

## STRADDLE

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 880,673.50`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 847,573.50`**
- Win rate: `61.93%` (205W / 126L)
- Max drawdown: `Rs 73,667.00`
- Best day: `Rs 76,551.25`  Worst day: `Rs -60,810.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 68,350 | 62.3% |
| 2021 | 52 | Rs 61,091 | 59.6% |
| 2022 | 52 | Rs 118,574 | 63.5% |
| 2023 | 52 | Rs 93,461 | 59.6% |
| 2024 | 52 | Rs 357,566 | 73.1% |
| 2025 | 53 | Rs 34,743 | 49.1% |
| 2026 | 17 | Rs 113,788 | 76.5% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_100

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 658,193.80`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 625,093.80`**
- Win rate: `55.59%` (184W / 147L)
- Max drawdown: `Rs 55,431.00`
- Best day: `Rs 69,823.75`  Worst day: `Rs -38,320.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 52,654 | 56.6% |
| 2021 | 52 | Rs 47,798 | 51.9% |
| 2022 | 52 | Rs 92,312 | 57.7% |
| 2023 | 52 | Rs -19,108 | 44.2% |
| 2024 | 52 | Rs 214,439 | 59.6% |
| 2025 | 53 | Rs 124,143 | 58.5% |
| 2026 | 17 | Rs 112,856 | 70.6% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_200

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 359,243.80`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 326,143.80`**
- Win rate: `51.36%` (170W / 161L)
- Max drawdown: `Rs 27,141.00`
- Best day: `Rs 50,340.00`  Worst day: `Rs -22,629.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 11,269 | 26.4% |
| 2021 | 52 | Rs 12,167 | 53.8% |
| 2022 | 52 | Rs 64,274 | 59.6% |
| 2023 | 52 | Rs -7,081 | 50.0% |
| 2024 | 52 | Rs 101,054 | 59.6% |
| 2025 | 53 | Rs 103,404 | 54.7% |
| 2026 | 17 | Rs 41,057 | 64.7% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_300

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 147,561.30`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 114,461.30`**
- Win rate: `38.67%` (128W / 203L)
- Max drawdown: `Rs 19,954.00`
- Best day: `Rs 35,910.00`  Worst day: `Rs -12,710.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 5,761 | 18.9% |
| 2021 | 52 | Rs -1,663 | 51.9% |
| 2022 | 52 | Rs 8,135 | 42.3% |
| 2023 | 52 | Rs -9,232 | 25.0% |
| 2024 | 52 | Rs 29,141 | 46.2% |
| 2025 | 53 | Rs 39,774 | 43.4% |
| 2026 | 17 | Rs 42,546 | 52.9% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Expiry dates come from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Every offset is evaluated on the same expiry days, so the columns are directly comparable.
