# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the centre strike and PE the same distance below
- Balance filter: CE and PE premiums must be within `20%` (min/max >= 80%)
- Balancing by **centre shift**: move both legs together by 50 points — 0, +50, -50, ... out to ±5 strikes. A strangle keeps its symmetric strike distance.
- Unbalanced days are **skipped**
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
| STRADDLE | 145 | 189 | 77.9% | Rs 727,339 | 8.14% | Rs 1,106,950 | Rs 75,388 | 2.36 | Rs 5,016 |
| STRANGLE_100 | 132 | 202 | 76.5% | Rs 415,984 | 5.06% | Rs 1,109,225 | Rs 46,769 | 2.66 | Rs 3,151 |
| STRANGLE_200 | 137 | 197 | 54.0% | Rs 91,563 | 1.23% | Rs 1,111,500 | Rs 31,643 | 1.67 | Rs 668 |
| STRANGLE_300 | 211 | 123 | 35.1% | Rs 21,553 | 0.30% | Rs 1,113,775 | Rs 22,305 | 1.23 | Rs 102 |

## Stop-loss behaviour

| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |
|---|---:|---:|---:|---:|
| STRADDLE | 26 (17.9%) | 108 (74.5%) | 11 (7.6%) | 6 (4.1%) |
| STRANGLE_100 | 28 (21.2%) | 87 (65.9%) | 17 (12.9%) | 18 (13.6%) |
| STRANGLE_200 | 23 (16.8%) | 84 (61.3%) | 30 (21.9%) | 69 (50.4%) |
| STRANGLE_300 | 24 (11.4%) | 98 (46.4%) | 89 (42.2%) | 146 (69.2%) |

## STRADDLE

- Traded: `145`  Skipped: `189`
- Gross P/L: `Rs 741,839.00`  Costs: `Rs 14,500.00`
- **Net P/L: `Rs 727,339.00`**
- Win rate: `77.93%` (113W / 32L)
- Max drawdown: `Rs 75,387.50`
- Best day: `Rs 76,551.25`  Worst day: `Rs -38,287.50`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 24 | Rs 131,498 | 91.7% |
| 2021 | 23 | Rs 44,830 | 78.3% |
| 2022 | 18 | Rs 53,722 | 83.3% |
| 2023 | 15 | Rs -54,090 | 40.0% |
| 2024 | 28 | Rs 328,685 | 85.7% |
| 2025 | 27 | Rs 155,126 | 77.8% |
| 2026 | 10 | Rs 67,568 | 70.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 186 |
| `no_priceable_pair` | 3 |

## STRANGLE_100

- Traded: `132`  Skipped: `202`
- Gross P/L: `Rs 429,183.74`  Costs: `Rs 13,200.00`
- **Net P/L: `Rs 415,983.74`**
- Win rate: `76.52%` (101W / 31L)
- Max drawdown: `Rs 46,769.38`
- Best day: `Rs 69,823.75`  Worst day: `Rs -24,231.25`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 12 | Rs 43,995 | 75.0% |
| 2021 | 20 | Rs 24,018 | 80.0% |
| 2022 | 21 | Rs 59,700 | 85.7% |
| 2023 | 13 | Rs 6,440 | 76.9% |
| 2024 | 33 | Rs 180,375 | 75.8% |
| 2025 | 25 | Rs 75,785 | 76.0% |
| 2026 | 8 | Rs 25,671 | 50.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 199 |
| `no_priceable_pair` | 3 |

## STRANGLE_200

- Traded: `137`  Skipped: `197`
- Gross P/L: `Rs 105,263.24`  Costs: `Rs 13,700.00`
- **Net P/L: `Rs 91,563.24`**
- Win rate: `54.01%` (74W / 63L)
- Max drawdown: `Rs 31,643.13`
- Best day: `Rs 31,505.00`  Worst day: `Rs -15,250.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 15 | Rs 8,258 | 26.7% |
| 2021 | 24 | Rs 8,498 | 58.3% |
| 2022 | 15 | Rs 17,032 | 80.0% |
| 2023 | 18 | Rs -4,860 | 22.2% |
| 2024 | 24 | Rs 12,465 | 54.2% |
| 2025 | 31 | Rs 65,260 | 67.7% |
| 2026 | 10 | Rs -15,089 | 60.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 194 |
| `no_priceable_pair` | 3 |

## STRANGLE_300

- Traded: `211`  Skipped: `123`
- Gross P/L: `Rs 42,652.88`  Costs: `Rs 21,100.00`
- **Net P/L: `Rs 21,552.88`**
- Win rate: `35.07%` (74W / 137L)
- Max drawdown: `Rs 22,305.00`
- Best day: `Rs 19,100.00`  Worst day: `Rs -8,225.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 24 | Rs -14,752 | 4.2% |
| 2021 | 40 | Rs -2,402 | 47.5% |
| 2022 | 33 | Rs 9,165 | 45.5% |
| 2023 | 39 | Rs -13,560 | 15.4% |
| 2024 | 31 | Rs 20,240 | 41.9% |
| 2025 | 34 | Rs 21,011 | 44.1% |
| 2026 | 10 | Rs 1,852 | 50.0% |

| Skip reason | Count |
|---|---:|
| `balance_filter` | 120 |
| `no_priceable_pair` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Expiry dates come from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Every offset is evaluated on the same expiry days, so the columns are directly comparable.
