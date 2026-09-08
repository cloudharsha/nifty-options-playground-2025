# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the centre strike and PE the same distance below
- Balance filter: CE and PE premiums must be within `20%` (min/max >= 80%)
- Balancing by **independent legs**: move the CE and PE strikes separately, each up to ±5 strikes, and take the closest-to-nominal pair whose premiums match. The strangle is no longer symmetric in strike distance. Offset 0 still uses a centre shift so it stays a true straddle.
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
| STRANGLE_100 | 330 | 4 | 68.5% | Rs 520,268 | 6.14% | Rs 1,109,225 | Rs 59,805 | 1.95 | Rs 1,577 |
| STRANGLE_200 | 331 | 3 | 52.9% | Rs 94,926 | 1.28% | Rs 1,111,500 | Rs 41,016 | 1.33 | Rs 287 |
| STRANGLE_300 | 331 | 3 | 38.7% | Rs 30,974 | 0.43% | Rs 1,113,775 | Rs 32,640 | 1.18 | Rs 94 |

## Stop-loss behaviour

| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |
|---|---:|---:|---:|---:|
| STRADDLE | 26 (17.9%) | 108 (74.5%) | 11 (7.6%) | 6 (4.1%) |
| STRANGLE_100 | 72 (21.8%) | 216 (65.5%) | 42 (12.7%) | 216 (65.5%) |
| STRANGLE_200 | 52 (15.7%) | 202 (61.0%) | 77 (23.3%) | 263 (79.5%) |
| STRANGLE_300 | 37 (11.2%) | 170 (51.4%) | 124 (37.5%) | 266 (80.4%) |

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

- Traded: `330`  Skipped: `4`
- Gross P/L: `Rs 553,267.76`  Costs: `Rs 33,000.00`
- **Net P/L: `Rs 520,267.76`**
- Win rate: `68.48%` (226W / 104L)
- Max drawdown: `Rs 59,805.00`
- Best day: `Rs 69,823.75`  Worst day: `Rs -26,295.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 52 | Rs 94,520 | 61.5% |
| 2021 | 52 | Rs 46,662 | 80.8% |
| 2022 | 52 | Rs 107,075 | 78.8% |
| 2023 | 52 | Rs 9,110 | 51.9% |
| 2024 | 52 | Rs 122,308 | 63.5% |
| 2025 | 53 | Rs 100,774 | 75.5% |
| 2026 | 17 | Rs 39,819 | 64.7% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |
| `balance_filter` | 1 |

## STRANGLE_200

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 128,026.38`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 94,926.38`**
- Win rate: `52.87%` (175W / 156L)
- Max drawdown: `Rs 41,016.25`
- Best day: `Rs 31,505.00`  Worst day: `Rs -22,442.50`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs -12,740 | 30.2% |
| 2021 | 52 | Rs 118 | 53.8% |
| 2022 | 52 | Rs 45,110 | 65.4% |
| 2023 | 52 | Rs -12,745 | 32.7% |
| 2024 | 52 | Rs 28,580 | 63.5% |
| 2025 | 53 | Rs 75,079 | 69.8% |
| 2026 | 17 | Rs -28,475 | 58.8% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_300

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 64,074.49`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 30,974.49`**
- Win rate: `38.67%` (128W / 203L)
- Max drawdown: `Rs 32,640.00`
- Best day: `Rs 21,422.00`  Worst day: `Rs -22,442.50`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs -30,995 | 13.2% |
| 2021 | 52 | Rs 282 | 44.2% |
| 2022 | 52 | Rs 16,775 | 48.1% |
| 2023 | 52 | Rs -15,138 | 21.2% |
| 2024 | 52 | Rs 25,100 | 51.9% |
| 2025 | 53 | Rs 48,284 | 52.8% |
| 2026 | 17 | Rs -13,335 | 41.2% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Expiry dates come from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Every offset is evaluated on the same expiry days, so the columns are directly comparable.
