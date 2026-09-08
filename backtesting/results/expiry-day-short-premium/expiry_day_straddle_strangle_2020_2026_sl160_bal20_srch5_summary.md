# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the centre strike and PE the same distance below
- Balance filter: CE and PE premiums must be within `20%` (min/max >= 80%)
- Balancing by **centre shift**: move both legs together by 50 points — 0, +50, -50, ... out to ±5 strikes. A strangle keeps its symmetric strike distance.
- Unbalanced days are **skipped**
- Stop loss: **independent per leg**, triggered when a leg reaches `160%` of its entry price (60% loss on that leg). The other leg keeps running.
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
| STRADDLE | 145 | 189 | 82.1% | Rs 718,596 | 8.06% | Rs 1,106,950 | Rs 65,422 | 2.35 | Rs 4,956 |
| STRANGLE_100 | 132 | 202 | 75.8% | Rs 423,431 | 5.14% | Rs 1,109,225 | Rs 58,975 | 2.78 | Rs 3,208 |
| STRANGLE_200 | 137 | 197 | 56.2% | Rs 211,244 | 2.73% | Rs 1,111,500 | Rs 23,783 | 2.66 | Rs 1,542 |
| STRANGLE_300 | 211 | 123 | 37.9% | Rs 63,451 | 0.86% | Rs 1,113,775 | Rs 17,649 | 1.67 | Rs 301 |

## Stop-loss behaviour

| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |
|---|---:|---:|---:|---:|
| STRADDLE | 21 (14.5%) | 106 (73.1%) | 18 (12.4%) | 6 (4.1%) |
| STRANGLE_100 | 23 (17.4%) | 89 (67.4%) | 20 (15.2%) | 18 (13.6%) |
| STRANGLE_200 | 18 (13.1%) | 74 (54.0%) | 45 (32.8%) | 69 (50.4%) |
| STRANGLE_300 | 18 (8.5%) | 85 (40.3%) | 108 (51.2%) | 146 (69.2%) |

## STRADDLE

- Traded: `145`  Skipped: `189`
- Gross P/L: `Rs 733,095.50`  Costs: `Rs 14,500.00`
- **Net P/L: `Rs 718,595.50`**
- Win rate: `82.07%` (119W / 26L)
- Max drawdown: `Rs 65,422.00`
- Best day: `Rs 76,551.25`  Worst day: `Rs -45,795.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 24 | Rs 98,256 | 91.7% |
| 2021 | 23 | Rs 58,495 | 78.3% |
| 2022 | 18 | Rs 83,760 | 94.4% |
| 2023 | 15 | Rs -18,015 | 60.0% |
| 2024 | 28 | Rs 279,935 | 85.7% |
| 2025 | 27 | Rs 179,726 | 81.5% |
| 2026 | 10 | Rs 36,439 | 70.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 186 |
| `no_priceable_pair` | 3 |

## STRANGLE_100

- Traded: `132`  Skipped: `202`
- Gross P/L: `Rs 436,631.10`  Costs: `Rs 13,200.00`
- **Net P/L: `Rs 423,431.10`**
- Win rate: `75.76%` (100W / 32L)
- Max drawdown: `Rs 58,974.75`
- Best day: `Rs 69,823.75`  Worst day: `Rs -28,927.50`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 12 | Rs 39,417 | 66.7% |
| 2021 | 20 | Rs 18,631 | 70.0% |
| 2022 | 21 | Rs 43,050 | 85.7% |
| 2023 | 13 | Rs 5,246 | 61.5% |
| 2024 | 33 | Rs 206,256 | 81.8% |
| 2025 | 25 | Rs 93,867 | 80.0% |
| 2026 | 8 | Rs 16,964 | 62.5% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 199 |
| `no_priceable_pair` | 3 |

## STRANGLE_200

- Traded: `137`  Skipped: `197`
- Gross P/L: `Rs 224,943.60`  Costs: `Rs 13,700.00`
- **Net P/L: `Rs 211,243.60`**
- Win rate: `56.20%` (77W / 60L)
- Max drawdown: `Rs 23,783.00`
- Best day: `Rs 50,340.00`  Worst day: `Rs -17,159.25`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 15 | Rs 19,386 | 33.3% |
| 2021 | 24 | Rs 10,665 | 62.5% |
| 2022 | 15 | Rs 23,940 | 66.7% |
| 2023 | 18 | Rs -3,651 | 22.2% |
| 2024 | 24 | Rs 61,755 | 66.7% |
| 2025 | 31 | Rs 69,300 | 67.7% |
| 2026 | 10 | Rs 29,849 | 60.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 194 |
| `no_priceable_pair` | 3 |

## STRANGLE_300

- Traded: `211`  Skipped: `123`
- Gross P/L: `Rs 84,551.30`  Costs: `Rs 21,100.00`
- **Net P/L: `Rs 63,451.30`**
- Win rate: `37.91%` (80W / 131L)
- Max drawdown: `Rs 17,649.00`
- Best day: `Rs 35,910.00`  Worst day: `Rs -9,720.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 24 | Rs -14,100 | 8.3% |
| 2021 | 40 | Rs -607 | 47.5% |
| 2022 | 33 | Rs 10,656 | 45.5% |
| 2023 | 39 | Rs -11,406 | 17.9% |
| 2024 | 31 | Rs 17,105 | 45.2% |
| 2025 | 34 | Rs 22,627 | 47.1% |
| 2026 | 10 | Rs 39,176 | 70.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 120 |
| `no_priceable_pair` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Expiry dates come from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Every offset is evaluated on the same expiry days, so the columns are directly comparable.
