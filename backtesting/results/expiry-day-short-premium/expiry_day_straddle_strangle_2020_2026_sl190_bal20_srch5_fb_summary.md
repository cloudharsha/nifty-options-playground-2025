# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the centre strike and PE the same distance below
- Balance filter: CE and PE premiums must be within `20%` (min/max >= 80%)
- Balancing by **centre shift**: move both legs together by 50 points — 0, +50, -50, ... out to ±5 strikes. A strangle keeps its symmetric strike distance.
- Unbalanced days are entered at the best available pair
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
| STRADDLE | 331 | 3 | 57.4% | Rs 855,210 | 9.28% | Rs 1,106,950 | Rs 80,540 | 1.69 | Rs 2,584 |
| STRANGLE_100 | 331 | 3 | 52.3% | Rs 544,245 | 6.38% | Rs 1,109,225 | Rs 66,006 | 1.84 | Rs 1,644 |
| STRANGLE_200 | 331 | 3 | 49.2% | Rs 301,113 | 3.78% | Rs 1,111,500 | Rs 31,796 | 2.00 | Rs 910 |
| STRANGLE_300 | 331 | 3 | 40.8% | Rs 146,075 | 1.93% | Rs 1,113,775 | Rs 21,441 | 1.88 | Rs 441 |

## Stop-loss behaviour

| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |
|---|---:|---:|---:|---:|
| STRADDLE | 24 (7.3%) | 235 (71.0%) | 72 (21.8%) | 57 (17.2%) |
| STRANGLE_100 | 35 (10.6%) | 217 (65.6%) | 79 (23.9%) | 89 (26.9%) |
| STRANGLE_200 | 24 (7.3%) | 170 (51.4%) | 137 (41.4%) | 180 (54.4%) |
| STRANGLE_300 | 15 (4.5%) | 128 (38.7%) | 188 (56.8%) | 235 (71.0%) |

## STRADDLE

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 888,309.88`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 855,209.88`**
- Win rate: `57.40%` (190W / 141L)
- Max drawdown: `Rs 80,540.30`
- Best day: `Rs 76,551.25`  Worst day: `Rs -65,419.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs -140 | 58.5% |
| 2021 | 52 | Rs 66,948 | 50.0% |
| 2022 | 52 | Rs 103,757 | 57.7% |
| 2023 | 52 | Rs 65,476 | 55.8% |
| 2024 | 52 | Rs 409,136 | 65.4% |
| 2025 | 53 | Rs 3,629 | 47.2% |
| 2026 | 17 | Rs 206,404 | 88.2% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_100

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 577,344.54`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 544,244.54`**
- Win rate: `52.27%` (173W / 158L)
- Max drawdown: `Rs 66,006.00`
- Best day: `Rs 69,823.75`  Worst day: `Rs -43,016.25`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 46,981 | 58.5% |
| 2021 | 52 | Rs 39,274 | 44.2% |
| 2022 | 52 | Rs 64,298 | 55.8% |
| 2023 | 52 | Rs -20,660 | 42.3% |
| 2024 | 52 | Rs 174,749 | 53.8% |
| 2025 | 53 | Rs 127,370 | 52.8% |
| 2026 | 17 | Rs 112,234 | 70.6% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_200

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 334,213.27`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 301,113.27`**
- Win rate: `49.24%` (163W / 168L)
- Max drawdown: `Rs 31,795.50`
- Best day: `Rs 50,340.00`  Worst day: `Rs -25,363.88`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 4,818 | 24.5% |
| 2021 | 52 | Rs 9,642 | 51.9% |
| 2022 | 52 | Rs 67,130 | 57.7% |
| 2023 | 52 | Rs -6,943 | 50.0% |
| 2024 | 52 | Rs 86,126 | 53.8% |
| 2025 | 53 | Rs 102,899 | 50.9% |
| 2026 | 17 | Rs 37,441 | 70.6% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_300

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 179,174.59`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 146,074.59`**
- Win rate: `40.79%` (135W / 196L)
- Max drawdown: `Rs 21,441.00`
- Best day: `Rs 35,910.00`  Worst day: `Rs -14,205.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 3,256 | 18.9% |
| 2021 | 52 | Rs -3,319 | 51.9% |
| 2022 | 52 | Rs 6,386 | 44.2% |
| 2023 | 52 | Rs -5,806 | 30.8% |
| 2024 | 52 | Rs 37,824 | 44.2% |
| 2025 | 53 | Rs 64,916 | 50.9% |
| 2026 | 17 | Rs 42,817 | 52.9% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Expiry dates come from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Every offset is evaluated on the same expiry days, so the columns are directly comparable.
