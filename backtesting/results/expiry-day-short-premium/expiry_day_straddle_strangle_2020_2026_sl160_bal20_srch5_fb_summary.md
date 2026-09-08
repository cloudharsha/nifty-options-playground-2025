# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the centre strike and PE the same distance below
- Balance filter: CE and PE premiums must be within `20%` (min/max >= 80%)
- Balancing by **centre shift**: move both legs together by 50 points — 0, +50, -50, ... out to ±5 strikes. A strangle keeps its symmetric strike distance.
- Unbalanced days are entered at the best available pair
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
| STRADDLE | 331 | 3 | 70.4% | Rs 769,434 | 8.52% | Rs 1,106,950 | Rs 133,046 | 1.56 | Rs 2,325 |
| STRANGLE_100 | 331 | 3 | 62.2% | Rs 551,476 | 6.45% | Rs 1,109,225 | Rs 57,749 | 2.02 | Rs 1,666 |
| STRANGLE_200 | 331 | 3 | 52.6% | Rs 299,723 | 3.77% | Rs 1,111,500 | Rs 26,403 | 2.25 | Rs 906 |
| STRANGLE_300 | 331 | 3 | 37.5% | Rs 106,517 | 1.43% | Rs 1,113,775 | Rs 22,610 | 1.76 | Rs 322 |

## Stop-loss behaviour

| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |
|---|---:|---:|---:|---:|
| STRADDLE | 61 (18.4%) | 236 (71.3%) | 34 (10.3%) | 57 (17.2%) |
| STRANGLE_100 | 60 (18.1%) | 222 (67.1%) | 49 (14.8%) | 89 (26.9%) |
| STRANGLE_200 | 39 (11.8%) | 189 (57.1%) | 103 (31.1%) | 180 (54.4%) |
| STRANGLE_300 | 24 (7.3%) | 155 (46.8%) | 152 (45.9%) | 235 (71.0%) |

## STRADDLE

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 802,534.45`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 769,434.45`**
- Win rate: `70.39%` (233W / 98L)
- Max drawdown: `Rs 133,046.00`
- Best day: `Rs 76,551.25`  Worst day: `Rs -45,795.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 91,714 | 75.5% |
| 2021 | 52 | Rs 94,133 | 69.2% |
| 2022 | 52 | Rs 184,865 | 76.9% |
| 2023 | 52 | Rs -43,735 | 57.7% |
| 2024 | 52 | Rs 257,729 | 71.2% |
| 2025 | 53 | Rs 98,847 | 69.8% |
| 2026 | 17 | Rs 85,882 | 76.5% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_100

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 584,576.10`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 551,476.10`**
- Win rate: `62.24%` (206W / 125L)
- Max drawdown: `Rs 57,749.00`
- Best day: `Rs 69,823.75`  Worst day: `Rs -28,927.50`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 64,549 | 62.3% |
| 2021 | 52 | Rs 58,514 | 61.5% |
| 2022 | 52 | Rs 86,009 | 61.5% |
| 2023 | 52 | Rs -16,159 | 48.1% |
| 2024 | 52 | Rs 194,474 | 71.2% |
| 2025 | 53 | Rs 122,714 | 66.0% |
| 2026 | 17 | Rs 41,376 | 70.6% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_200

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 332,822.85`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 299,722.85`**
- Win rate: `52.57%` (174W / 157L)
- Max drawdown: `Rs 26,403.00`
- Best day: `Rs 50,340.00`  Worst day: `Rs -17,159.25`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 23,281 | 28.3% |
| 2021 | 52 | Rs 12,110 | 55.8% |
| 2022 | 52 | Rs 59,321 | 63.5% |
| 2023 | 52 | Rs -12,076 | 38.5% |
| 2024 | 52 | Rs 94,313 | 63.5% |
| 2025 | 53 | Rs 78,581 | 62.3% |
| 2026 | 17 | Rs 44,193 | 64.7% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_300

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 139,616.65`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 106,516.65`**
- Win rate: `37.46%` (124W / 207L)
- Max drawdown: `Rs 22,610.00`
- Best day: `Rs 35,910.00`  Worst day: `Rs -9,720.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 8,980 | 18.9% |
| 2021 | 52 | Rs -1,003 | 46.2% |
| 2022 | 52 | Rs 12,173 | 44.2% |
| 2023 | 52 | Rs -14,770 | 17.3% |
| 2024 | 52 | Rs 19,394 | 46.2% |
| 2025 | 53 | Rs 40,734 | 45.3% |
| 2026 | 17 | Rs 41,008 | 58.8% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Expiry dates come from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Every offset is evaluated on the same expiry days, so the columns are directly comparable.
