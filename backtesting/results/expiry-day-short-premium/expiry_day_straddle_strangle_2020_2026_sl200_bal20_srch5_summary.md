# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the centre strike and PE the same distance below
- Balance filter: CE and PE premiums must be within `20%` (min/max >= 80%)
- Balancing by **centre shift**: move both legs together by 50 points — 0, +50, -50, ... out to ±5 strikes. A strangle keeps its symmetric strike distance.
- Unbalanced days are **skipped**
- Stop loss: **independent per leg**, triggered when a leg reaches `200%` of its entry price (100% loss on that leg). The other leg keeps running.
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
| STRADDLE | 145 | 189 | 55.2% | Rs 663,966 | 7.55% | Rs 1,106,950 | Rs 69,765 | 2.66 | Rs 4,579 |
| STRANGLE_100 | 132 | 202 | 40.9% | Rs 461,946 | 5.54% | Rs 1,109,225 | Rs 54,785 | 3.02 | Rs 3,500 |
| STRANGLE_200 | 137 | 197 | 47.4% | Rs 261,750 | 3.33% | Rs 1,111,500 | Rs 31,960 | 2.80 | Rs 1,911 |
| STRANGLE_300 | 211 | 123 | 42.2% | Rs 94,814 | 1.27% | Rs 1,113,775 | Rs 19,755 | 1.93 | Rs 449 |

## Stop-loss behaviour

| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |
|---|---:|---:|---:|---:|
| STRADDLE | 5 (3.4%) | 100 (69.0%) | 40 (27.6%) | 6 (4.1%) |
| STRANGLE_100 | 9 (6.8%) | 90 (68.2%) | 33 (25.0%) | 18 (13.6%) |
| STRANGLE_200 | 12 (8.8%) | 61 (44.5%) | 64 (46.7%) | 69 (50.4%) |
| STRANGLE_300 | 9 (4.3%) | 71 (33.6%) | 131 (62.1%) | 146 (69.2%) |

## STRADDLE

- Traded: `145`  Skipped: `189`
- Gross P/L: `Rs 678,465.50`  Costs: `Rs 14,500.00`
- **Net P/L: `Rs 663,965.50`**
- Win rate: `55.17%` (80W / 65L)
- Max drawdown: `Rs 69,765.00`
- Best day: `Rs 76,551.25`  Worst day: `Rs -66,475.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 24 | Rs 60,345 | 45.8% |
| 2021 | 23 | Rs 27,055 | 39.1% |
| 2022 | 18 | Rs 17,250 | 44.4% |
| 2023 | 15 | Rs 36,900 | 66.7% |
| 2024 | 28 | Rs 299,225 | 53.6% |
| 2025 | 27 | Rs 88,620 | 70.4% |
| 2026 | 10 | Rs 134,570 | 80.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 186 |
| `no_priceable_pair` | 3 |

## STRANGLE_100

- Traded: `132`  Skipped: `202`
- Gross P/L: `Rs 475,145.50`  Costs: `Rs 13,200.00`
- **Net P/L: `Rs 461,945.50`**
- Win rate: `40.91%` (54W / 78L)
- Max drawdown: `Rs 54,785.00`
- Best day: `Rs 69,823.75`  Worst day: `Rs -30,820.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 12 | Rs 25,980 | 50.0% |
| 2021 | 20 | Rs 1,885 | 20.0% |
| 2022 | 21 | Rs 20,160 | 33.3% |
| 2023 | 13 | Rs 9,380 | 23.1% |
| 2024 | 33 | Rs 180,990 | 48.5% |
| 2025 | 25 | Rs 119,408 | 48.0% |
| 2026 | 8 | Rs 104,142 | 75.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 199 |
| `no_priceable_pair` | 3 |

## STRANGLE_200

- Traded: `137`  Skipped: `197`
- Gross P/L: `Rs 275,450.25`  Costs: `Rs 13,700.00`
- **Net P/L: `Rs 261,750.25`**
- Win rate: `47.45%` (65W / 72L)
- Max drawdown: `Rs 31,960.00`
- Best day: `Rs 50,340.00`  Worst day: `Rs -25,420.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 15 | Rs 10,350 | 26.7% |
| 2021 | 24 | Rs 16,590 | 62.5% |
| 2022 | 15 | Rs 19,560 | 53.3% |
| 2023 | 18 | Rs -7,950 | 33.3% |
| 2024 | 24 | Rs 53,475 | 50.0% |
| 2025 | 31 | Rs 95,699 | 45.2% |
| 2026 | 10 | Rs 74,026 | 60.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 194 |
| `no_priceable_pair` | 3 |

## STRANGLE_300

- Traded: `211`  Skipped: `123`
- Gross P/L: `Rs 115,914.00`  Costs: `Rs 21,100.00`
- **Net P/L: `Rs 94,814.00`**
- Win rate: `42.18%` (89W / 122L)
- Max drawdown: `Rs 19,755.00`
- Best day: `Rs 35,910.00`  Worst day: `Rs -14,530.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 24 | Rs -15,225 | 8.3% |
| 2021 | 40 | Rs -2,245 | 55.0% |
| 2022 | 33 | Rs 7,665 | 45.5% |
| 2023 | 39 | Rs -6,930 | 28.2% |
| 2024 | 31 | Rs 41,240 | 48.4% |
| 2025 | 34 | Rs 23,729 | 50.0% |
| 2026 | 10 | Rs 46,580 | 70.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 120 |
| `no_priceable_pair` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Expiry dates come from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Every offset is evaluated on the same expiry days, so the columns are directly comparable.
