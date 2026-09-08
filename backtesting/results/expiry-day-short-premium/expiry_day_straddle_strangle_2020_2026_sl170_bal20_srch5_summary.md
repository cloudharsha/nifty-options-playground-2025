# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the centre strike and PE the same distance below
- Balance filter: CE and PE premiums must be within `20%` (min/max >= 80%)
- Balancing by **centre shift**: move both legs together by 50 points — 0, +50, -50, ... out to ±5 strikes. A strangle keeps its symmetric strike distance.
- Unbalanced days are **skipped**
- Stop loss: **independent per leg**, triggered when a leg reaches `170%` of its entry price (70% loss on that leg). The other leg keeps running.
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
| STRADDLE | 145 | 189 | 86.9% | Rs 736,349 | 8.22% | Rs 1,106,950 | Rs 56,511 | 2.67 | Rs 5,078 |
| STRANGLE_100 | 132 | 202 | 75.0% | Rs 494,430 | 5.88% | Rs 1,109,225 | Rs 46,402 | 3.23 | Rs 3,746 |
| STRANGLE_200 | 137 | 197 | 53.3% | Rs 197,165 | 2.56% | Rs 1,111,500 | Rs 22,879 | 2.46 | Rs 1,439 |
| STRANGLE_300 | 211 | 123 | 38.4% | Rs 55,627 | 0.76% | Rs 1,113,775 | Rs 21,980 | 1.55 | Rs 264 |

## Stop-loss behaviour

| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |
|---|---:|---:|---:|---:|
| STRADDLE | 14 (9.7%) | 109 (75.2%) | 22 (15.2%) | 6 (4.1%) |
| STRANGLE_100 | 19 (14.4%) | 86 (65.2%) | 27 (20.5%) | 18 (13.6%) |
| STRANGLE_200 | 15 (10.9%) | 73 (53.3%) | 49 (35.8%) | 69 (50.4%) |
| STRANGLE_300 | 17 (8.1%) | 78 (37.0%) | 116 (55.0%) | 146 (69.2%) |

## STRADDLE

- Traded: `145`  Skipped: `189`
- Gross P/L: `Rs 750,849.14`  Costs: `Rs 14,500.00`
- **Net P/L: `Rs 736,349.14`**
- Win rate: `86.90%` (126W / 19L)
- Max drawdown: `Rs 56,511.00`
- Best day: `Rs 76,551.25`  Worst day: `Rs -53,302.50`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 24 | Rs 145,132 | 95.8% |
| 2021 | 23 | Rs 87,283 | 87.0% |
| 2022 | 18 | Rs 50,420 | 94.4% |
| 2023 | 15 | Rs -2,724 | 73.3% |
| 2024 | 28 | Rs 259,505 | 89.3% |
| 2025 | 27 | Rs 133,358 | 81.5% |
| 2026 | 10 | Rs 63,375 | 80.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 186 |
| `no_priceable_pair` | 3 |

## STRANGLE_100

- Traded: `132`  Skipped: `202`
- Gross P/L: `Rs 507,629.82`  Costs: `Rs 13,200.00`
- **Net P/L: `Rs 494,429.82`**
- Win rate: `75.00%` (99W / 33L)
- Max drawdown: `Rs 46,401.50`
- Best day: `Rs 69,823.75`  Worst day: `Rs -33,623.75`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 12 | Rs 39,116 | 66.7% |
| 2021 | 20 | Rs 10,903 | 60.0% |
| 2022 | 21 | Rs 52,170 | 90.5% |
| 2023 | 13 | Rs 5,764 | 61.5% |
| 2024 | 33 | Rs 189,896 | 78.8% |
| 2025 | 25 | Rs 114,584 | 80.0% |
| 2026 | 8 | Rs 81,999 | 75.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 199 |
| `no_priceable_pair` | 3 |

## STRANGLE_200

- Traded: `137`  Skipped: `197`
- Gross P/L: `Rs 210,865.46`  Costs: `Rs 13,700.00`
- **Net P/L: `Rs 197,165.46`**
- Win rate: `53.28%` (73W / 64L)
- Max drawdown: `Rs 22,878.74`
- Best day: `Rs 50,340.00`  Worst day: `Rs -19,894.12`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 15 | Rs 17,127 | 33.3% |
| 2021 | 24 | Rs 12,596 | 62.5% |
| 2022 | 15 | Rs 22,845 | 66.7% |
| 2023 | 18 | Rs -5,128 | 27.8% |
| 2024 | 24 | Rs 50,468 | 62.5% |
| 2025 | 31 | Rs 69,270 | 58.1% |
| 2026 | 10 | Rs 29,989 | 50.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 194 |
| `no_priceable_pair` | 3 |

## STRANGLE_300

- Traded: `211`  Skipped: `123`
- Gross P/L: `Rs 76,726.60`  Costs: `Rs 21,100.00`
- **Net P/L: `Rs 55,626.60`**
- Win rate: `38.39%` (81W / 130L)
- Max drawdown: `Rs 21,980.50`
- Best day: `Rs 35,910.00`  Worst day: `Rs -11,215.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 24 | Rs -14,648 | 8.3% |
| 2021 | 40 | Rs -1,356 | 50.0% |
| 2022 | 33 | Rs 10,100 | 45.5% |
| 2023 | 39 | Rs -10,522 | 20.5% |
| 2024 | 31 | Rs 11,240 | 41.9% |
| 2025 | 34 | Rs 24,360 | 50.0% |
| 2026 | 10 | Rs 36,453 | 60.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 120 |
| `no_priceable_pair` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Expiry dates come from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Every offset is evaluated on the same expiry days, so the columns are directly comparable.
