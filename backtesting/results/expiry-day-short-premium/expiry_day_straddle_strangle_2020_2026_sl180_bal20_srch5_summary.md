# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the centre strike and PE the same distance below
- Balance filter: CE and PE premiums must be within `20%` (min/max >= 80%)
- Balancing by **centre shift**: move both legs together by 50 points — 0, +50, -50, ... out to ±5 strikes. A strangle keeps its symmetric strike distance.
- Unbalanced days are **skipped**
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
| STRADDLE | 145 | 189 | 80.7% | Rs 755,862 | 8.40% | Rs 1,106,950 | Rs 60,810 | 3.15 | Rs 5,213 |
| STRANGLE_100 | 132 | 202 | 62.9% | Rs 498,894 | 5.92% | Rs 1,109,225 | Rs 54,686 | 3.31 | Rs 3,779 |
| STRANGLE_200 | 137 | 197 | 51.8% | Rs 239,452 | 3.07% | Rs 1,111,500 | Rs 27,914 | 2.59 | Rs 1,748 |
| STRANGLE_300 | 211 | 123 | 40.3% | Rs 77,160 | 1.04% | Rs 1,113,775 | Rs 18,492 | 1.77 | Rs 366 |

## Stop-loss behaviour

| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |
|---|---:|---:|---:|---:|
| STRADDLE | 8 (5.5%) | 108 (74.5%) | 29 (20.0%) | 6 (4.1%) |
| STRANGLE_100 | 14 (10.6%) | 89 (67.4%) | 29 (22.0%) | 18 (13.6%) |
| STRANGLE_200 | 14 (10.2%) | 66 (48.2%) | 57 (41.6%) | 69 (50.4%) |
| STRANGLE_300 | 12 (5.7%) | 74 (35.1%) | 125 (59.2%) | 146 (69.2%) |

## STRADDLE

- Traded: `145`  Skipped: `189`
- Gross P/L: `Rs 770,361.90`  Costs: `Rs 14,500.00`
- **Net P/L: `Rs 755,861.90`**
- Win rate: `80.69%` (117W / 28L)
- Max drawdown: `Rs 60,810.00`
- Best day: `Rs 76,551.25`  Worst day: `Rs -60,810.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 24 | Rs 116,895 | 79.2% |
| 2021 | 23 | Rs 65,497 | 82.6% |
| 2022 | 18 | Rs 16,455 | 72.2% |
| 2023 | 15 | Rs 62,238 | 93.3% |
| 2024 | 28 | Rs 320,006 | 85.7% |
| 2025 | 27 | Rs 122,906 | 74.1% |
| 2026 | 10 | Rs 51,864 | 80.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 186 |
| `no_priceable_pair` | 3 |

## STRANGLE_100

- Traded: `132`  Skipped: `202`
- Gross P/L: `Rs 512,093.55`  Costs: `Rs 13,200.00`
- **Net P/L: `Rs 498,893.55`**
- Win rate: `62.88%` (83W / 49L)
- Max drawdown: `Rs 54,686.00`
- Best day: `Rs 69,823.75`  Worst day: `Rs -38,320.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 12 | Rs 33,999 | 50.0% |
| 2021 | 20 | Rs 3,007 | 45.0% |
| 2022 | 21 | Rs 48,969 | 76.2% |
| 2023 | 13 | Rs 10,097 | 53.8% |
| 2024 | 33 | Rs 209,637 | 63.6% |
| 2025 | 25 | Rs 120,304 | 72.0% |
| 2026 | 8 | Rs 72,881 | 75.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 199 |
| `no_priceable_pair` | 3 |

## STRANGLE_200

- Traded: `137`  Skipped: `197`
- Gross P/L: `Rs 253,152.05`  Costs: `Rs 13,700.00`
- **Net P/L: `Rs 239,452.05`**
- Win rate: `51.82%` (71W / 66L)
- Max drawdown: `Rs 27,914.50`
- Best day: `Rs 50,340.00`  Worst day: `Rs -22,629.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 15 | Rs 14,868 | 26.7% |
| 2021 | 24 | Rs 12,963 | 62.5% |
| 2022 | 15 | Rs 21,750 | 60.0% |
| 2023 | 18 | Rs -5,148 | 33.3% |
| 2024 | 24 | Rs 70,128 | 58.3% |
| 2025 | 31 | Rs 93,037 | 54.8% |
| 2026 | 10 | Rs 31,854 | 60.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 194 |
| `no_priceable_pair` | 3 |

## STRANGLE_300

- Traded: `211`  Skipped: `123`
- Gross P/L: `Rs 98,260.00`  Costs: `Rs 21,100.00`
- **Net P/L: `Rs 77,160.00`**
- Win rate: `40.28%` (85W / 126L)
- Max drawdown: `Rs 18,492.00`
- Best day: `Rs 35,910.00`  Worst day: `Rs -12,710.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 24 | Rs -14,523 | 8.3% |
| 2021 | 40 | Rs -1,684 | 52.5% |
| 2022 | 33 | Rs 9,708 | 45.5% |
| 2023 | 39 | Rs -7,803 | 23.1% |
| 2024 | 31 | Rs 27,701 | 45.2% |
| 2025 | 34 | Rs 28,322 | 50.0% |
| 2026 | 10 | Rs 35,439 | 70.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 120 |
| `no_priceable_pair` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Expiry dates come from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Every offset is evaluated on the same expiry days, so the columns are directly comparable.
