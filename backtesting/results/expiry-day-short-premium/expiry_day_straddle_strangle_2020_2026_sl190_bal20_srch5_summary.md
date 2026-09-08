# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the centre strike and PE the same distance below
- Balance filter: CE and PE premiums must be within `20%` (min/max >= 80%)
- Balancing by **centre shift**: move both legs together by 50 points — 0, +50, -50, ... out to ±5 strikes. A strangle keeps its symmetric strike distance.
- Unbalanced days are **skipped**
- Stop loss: **independent per leg**, triggered when a leg reaches `190%` of its entry price (90% loss on that leg). The other leg keeps running.
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
| STRADDLE | 145 | 189 | 68.3% | Rs 796,202 | 8.76% | Rs 1,106,950 | Rs 60,536 | 3.62 | Rs 5,491 |
| STRANGLE_100 | 132 | 202 | 53.0% | Rs 457,457 | 5.50% | Rs 1,109,225 | Rs 62,801 | 2.87 | Rs 3,466 |
| STRANGLE_200 | 137 | 197 | 48.2% | Rs 218,702 | 2.82% | Rs 1,111,500 | Rs 33,568 | 2.24 | Rs 1,596 |
| STRANGLE_300 | 211 | 123 | 40.3% | Rs 81,150 | 1.10% | Rs 1,113,775 | Rs 20,260 | 1.72 | Rs 385 |

## Stop-loss behaviour

| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |
|---|---:|---:|---:|---:|
| STRADDLE | 5 (3.4%) | 105 (72.4%) | 35 (24.1%) | 6 (4.1%) |
| STRANGLE_100 | 12 (9.1%) | 89 (67.4%) | 31 (23.5%) | 18 (13.6%) |
| STRANGLE_200 | 14 (10.2%) | 62 (45.3%) | 61 (44.5%) | 69 (50.4%) |
| STRANGLE_300 | 12 (5.7%) | 72 (34.1%) | 127 (60.2%) | 146 (69.2%) |

## STRADDLE

- Traded: `145`  Skipped: `189`
- Gross P/L: `Rs 810,702.20`  Costs: `Rs 14,500.00`
- **Net P/L: `Rs 796,202.20`**
- Win rate: `68.28%` (99W / 46L)
- Max drawdown: `Rs 60,536.00`
- Best day: `Rs 76,551.25`  Worst day: `Rs -59,897.50`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 24 | Rs 88,658 | 75.0% |
| 2021 | 23 | Rs 51,542 | 56.5% |
| 2022 | 18 | Rs 11,853 | 50.0% |
| 2023 | 15 | Rs 48,474 | 73.3% |
| 2024 | 28 | Rs 333,750 | 67.9% |
| 2025 | 27 | Rs 109,551 | 70.4% |
| 2026 | 10 | Rs 152,374 | 100.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 186 |
| `no_priceable_pair` | 3 |

## STRANGLE_100

- Traded: `132`  Skipped: `202`
- Gross P/L: `Rs 470,657.28`  Costs: `Rs 13,200.00`
- **Net P/L: `Rs 457,457.28`**
- Win rate: `53.03%` (70W / 62L)
- Max drawdown: `Rs 62,801.00`
- Best day: `Rs 69,823.75`  Worst day: `Rs -43,016.25`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 12 | Rs 33,633 | 58.3% |
| 2021 | 20 | Rs 6,538 | 25.0% |
| 2022 | 21 | Rs 34,630 | 71.4% |
| 2023 | 13 | Rs 9,218 | 38.5% |
| 2024 | 33 | Rs 186,459 | 54.5% |
| 2025 | 25 | Rs 123,216 | 60.0% |
| 2026 | 8 | Rs 63,763 | 62.5% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 199 |
| `no_priceable_pair` | 3 |

## STRANGLE_200

- Traded: `137`  Skipped: `197`
- Gross P/L: `Rs 232,402.27`  Costs: `Rs 13,700.00`
- **Net P/L: `Rs 218,702.27`**
- Win rate: `48.18%` (66W / 71L)
- Max drawdown: `Rs 33,567.88`
- Best day: `Rs 50,340.00`  Worst day: `Rs -25,363.88`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 15 | Rs 12,588 | 26.7% |
| 2021 | 24 | Rs 12,951 | 62.5% |
| 2022 | 15 | Rs 20,655 | 60.0% |
| 2023 | 18 | Rs -6,032 | 33.3% |
| 2024 | 24 | Rs 61,923 | 50.0% |
| 2025 | 31 | Rs 91,131 | 45.2% |
| 2026 | 10 | Rs 25,486 | 60.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 194 |
| `no_priceable_pair` | 3 |

## STRANGLE_300

- Traded: `211`  Skipped: `123`
- Gross P/L: `Rs 102,250.38`  Costs: `Rs 21,100.00`
- **Net P/L: `Rs 81,150.38`**
- Win rate: `40.28%` (85W / 126L)
- Max drawdown: `Rs 20,260.50`
- Best day: `Rs 35,910.00`  Worst day: `Rs -14,205.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 24 | Rs -15,044 | 8.3% |
| 2021 | 40 | Rs -2,932 | 52.5% |
| 2022 | 33 | Rs 8,643 | 45.5% |
| 2023 | 39 | Rs -7,448 | 25.6% |
| 2024 | 31 | Rs 39,094 | 45.2% |
| 2025 | 34 | Rs 26,026 | 50.0% |
| 2026 | 10 | Rs 32,811 | 60.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 120 |
| `no_priceable_pair` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Expiry dates come from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Every offset is evaluated on the same expiry days, so the columns are directly comparable.
