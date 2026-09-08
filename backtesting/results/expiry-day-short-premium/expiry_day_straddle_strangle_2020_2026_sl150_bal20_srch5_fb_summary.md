# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the centre strike and PE the same distance below
- Balance filter: CE and PE premiums must be within `20%` (min/max >= 80%)
- Balancing by **centre shift**: move both legs together by 50 points — 0, +50, -50, ... out to ±5 strikes. A strangle keeps its symmetric strike distance.
- Unbalanced days are entered at the best available pair
- Stop loss: **independent per leg**, triggered when a leg reaches `150%` of its entry price (50% loss on that leg). The other leg keeps running.
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
| STRADDLE | 331 | 3 | 73.4% | Rs 894,850 | 9.62% | Rs 1,106,950 | Rs 117,680 | 1.68 | Rs 2,703 |
| STRANGLE_100 | 331 | 3 | 66.2% | Rs 517,802 | 6.12% | Rs 1,109,225 | Rs 49,800 | 1.93 | Rs 1,564 |
| STRANGLE_200 | 331 | 3 | 51.1% | Rs 129,766 | 1.73% | Rs 1,111,500 | Rs 30,345 | 1.48 | Rs 392 |
| STRANGLE_300 | 331 | 3 | 36.3% | Rs 26,116 | 0.36% | Rs 1,113,775 | Rs 34,852 | 1.17 | Rs 79 |

## Stop-loss behaviour

| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |
|---|---:|---:|---:|---:|
| STRADDLE | 75 (22.7%) | 234 (70.7%) | 22 (6.6%) | 57 (17.2%) |
| STRANGLE_100 | 75 (22.7%) | 217 (65.6%) | 39 (11.8%) | 89 (26.9%) |
| STRANGLE_200 | 49 (14.8%) | 202 (61.0%) | 80 (24.2%) | 180 (54.4%) |
| STRANGLE_300 | 35 (10.6%) | 164 (49.5%) | 132 (39.9%) | 235 (71.0%) |

## STRADDLE

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 927,950.01`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 894,850.01`**
- Win rate: `73.41%` (243W / 88L)
- Max drawdown: `Rs 117,680.00`
- Best day: `Rs 76,551.25`  Worst day: `Rs -38,287.50`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 139,008 | 79.2% |
| 2021 | 52 | Rs 80,210 | 76.9% |
| 2022 | 52 | Rs 174,012 | 80.8% |
| 2023 | 52 | Rs -41,455 | 61.5% |
| 2024 | 52 | Rs 359,412 | 71.2% |
| 2025 | 53 | Rs 105,523 | 71.7% |
| 2026 | 17 | Rs 78,140 | 70.6% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_100

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 550,902.10`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 517,802.11`**
- Win rate: `66.16%` (219W / 112L)
- Max drawdown: `Rs 49,800.00`
- Best day: `Rs 69,823.75`  Worst day: `Rs -24,231.25`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 77,822 | 66.0% |
| 2021 | 52 | Rs 51,072 | 73.1% |
| 2022 | 52 | Rs 92,172 | 67.3% |
| 2023 | 52 | Rs -10,278 | 53.8% |
| 2024 | 52 | Rs 147,410 | 65.4% |
| 2025 | 53 | Rs 100,422 | 71.7% |
| 2026 | 17 | Rs 59,181 | 64.7% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_200

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 162,865.85`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 129,765.85`**
- Win rate: `51.06%` (169W / 162L)
- Max drawdown: `Rs 30,345.00`
- Best day: `Rs 31,505.00`  Worst day: `Rs -20,522.50`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs -19,422 | 24.5% |
| 2021 | 52 | Rs 6,530 | 50.0% |
| 2022 | 52 | Rs 53,578 | 67.3% |
| 2023 | 52 | Rs -13,600 | 32.7% |
| 2024 | 52 | Rs 37,888 | 61.5% |
| 2025 | 53 | Rs 81,192 | 67.9% |
| 2026 | 17 | Rs -16,398 | 58.8% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_300

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 59,215.89`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 26,115.89`**
- Win rate: `36.25%` (120W / 211L)
- Max drawdown: `Rs 34,852.50`
- Best day: `Rs 19,100.00`  Worst day: `Rs -14,950.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs -25,580 | 15.1% |
| 2021 | 52 | Rs -2,312 | 46.2% |
| 2022 | 52 | Rs 12,590 | 48.1% |
| 2023 | 52 | Rs -18,055 | 15.4% |
| 2024 | 52 | Rs 21,140 | 44.2% |
| 2025 | 53 | Rs 42,446 | 45.3% |
| 2026 | 17 | Rs -4,113 | 47.1% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Expiry dates come from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Every offset is evaluated on the same expiry days, so the columns are directly comparable.
