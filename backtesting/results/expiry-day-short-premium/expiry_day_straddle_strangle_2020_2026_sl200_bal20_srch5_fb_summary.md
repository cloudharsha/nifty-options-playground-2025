# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the centre strike and PE the same distance below
- Balance filter: CE and PE premiums must be within `20%` (min/max >= 80%)
- Balancing by **centre shift**: move both legs together by 50 points — 0, +50, -50, ... out to ±5 strikes. A strangle keeps its symmetric strike distance.
- Unbalanced days are entered at the best available pair
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
| STRADDLE | 331 | 3 | 54.7% | Rs 823,196 | 9.00% | Rs 1,106,950 | Rs 95,760 | 1.62 | Rs 2,487 |
| STRANGLE_100 | 331 | 3 | 49.5% | Rs 617,756 | 7.10% | Rs 1,109,225 | Rs 60,450 | 1.99 | Rs 1,866 |
| STRANGLE_200 | 331 | 3 | 47.7% | Rs 338,905 | 4.21% | Rs 1,111,500 | Rs 36,045 | 2.26 | Rs 1,024 |
| STRANGLE_300 | 331 | 3 | 41.7% | Rs 152,313 | 2.01% | Rs 1,113,775 | Rs 22,180 | 1.94 | Rs 460 |

## Stop-loss behaviour

| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |
|---|---:|---:|---:|---:|
| STRADDLE | 20 (6.0%) | 218 (65.9%) | 93 (28.1%) | 57 (17.2%) |
| STRANGLE_100 | 28 (8.5%) | 213 (64.4%) | 90 (27.2%) | 89 (26.9%) |
| STRANGLE_200 | 19 (5.7%) | 169 (51.1%) | 143 (43.2%) | 180 (54.4%) |
| STRANGLE_300 | 12 (3.6%) | 125 (37.8%) | 194 (58.6%) | 235 (71.0%) |

## STRADDLE

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 856,296.25`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 823,196.25`**
- Win rate: `54.68%` (181W / 150L)
- Max drawdown: `Rs 95,760.00`
- Best day: `Rs 76,551.25`  Worst day: `Rs -66,475.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 82,585 | 50.9% |
| 2021 | 52 | Rs 52,580 | 46.2% |
| 2022 | 52 | Rs 86,675 | 59.6% |
| 2023 | 52 | Rs 43,040 | 53.8% |
| 2024 | 52 | Rs 365,795 | 59.6% |
| 2025 | 53 | Rs 11,815 | 50.9% |
| 2026 | 17 | Rs 180,706 | 76.5% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_100

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 650,855.75`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 617,755.75`**
- Win rate: `49.55%` (164W / 167L)
- Max drawdown: `Rs 60,450.00`
- Best day: `Rs 69,823.75`  Worst day: `Rs -41,680.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 44,155 | 56.6% |
| 2021 | 52 | Rs 57,425 | 48.1% |
| 2022 | 52 | Rs 35,765 | 40.4% |
| 2023 | 52 | Rs -3,490 | 42.3% |
| 2024 | 52 | Rs 198,320 | 51.9% |
| 2025 | 53 | Rs 139,357 | 49.1% |
| 2026 | 17 | Rs 146,224 | 76.5% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_200

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 372,004.75`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 338,904.75`**
- Win rate: `47.73%` (158W / 173L)
- Max drawdown: `Rs 36,045.00`
- Best day: `Rs 50,340.00`  Worst day: `Rs -25,420.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs -1,715 | 24.5% |
| 2021 | 52 | Rs 14,240 | 53.8% |
| 2022 | 52 | Rs 61,790 | 51.9% |
| 2023 | 52 | Rs -7,435 | 50.0% |
| 2024 | 52 | Rs 79,835 | 53.8% |
| 2025 | 53 | Rs 108,496 | 47.2% |
| 2026 | 17 | Rs 83,694 | 64.7% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_300

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 185,412.75`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 152,312.75`**
- Win rate: `41.69%` (138W / 193L)
- Max drawdown: `Rs 22,180.00`
- Best day: `Rs 35,910.00`  Worst day: `Rs -14,530.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 1,705 | 17.0% |
| 2021 | 52 | Rs -3,040 | 53.8% |
| 2022 | 52 | Rs 3,605 | 44.2% |
| 2023 | 52 | Rs -5,425 | 32.7% |
| 2024 | 52 | Rs 37,205 | 44.2% |
| 2025 | 53 | Rs 62,389 | 52.8% |
| 2026 | 17 | Rs 55,874 | 58.8% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Expiry dates come from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Every offset is evaluated on the same expiry days, so the columns are directly comparable.
