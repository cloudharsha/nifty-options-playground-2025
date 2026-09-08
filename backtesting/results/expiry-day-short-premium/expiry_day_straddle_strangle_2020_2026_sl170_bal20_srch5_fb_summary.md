# Expiry-Day Short Premium — Straddle vs Strangles (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Offset 0 = ATM straddle; offset 100/200/300 = strangle, CE that far above the centre strike and PE the same distance below
- Balance filter: CE and PE premiums must be within `20%` (min/max >= 80%)
- Balancing by **centre shift**: move both legs together by 50 points — 0, +50, -50, ... out to ±5 strikes. A strangle keeps its symmetric strike distance.
- Unbalanced days are entered at the best available pair
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
| STRADDLE | 331 | 3 | 67.4% | Rs 781,936 | 8.63% | Rs 1,106,950 | Rs 127,907 | 1.59 | Rs 2,362 |
| STRANGLE_100 | 331 | 3 | 59.2% | Rs 598,907 | 6.92% | Rs 1,109,225 | Rs 47,019 | 2.05 | Rs 1,809 |
| STRANGLE_200 | 331 | 3 | 51.7% | Rs 269,706 | 3.42% | Rs 1,111,500 | Rs 30,538 | 2.03 | Rs 815 |
| STRANGLE_300 | 331 | 3 | 36.6% | Rs 89,619 | 1.21% | Rs 1,113,775 | Rs 26,118 | 1.59 | Rs 271 |

## Stop-loss behaviour

| Variant | Both legs stopped | One leg stopped | Neither stopped | Centre shifted for balance |
|---|---:|---:|---:|---:|
| STRADDLE | 46 (13.9%) | 240 (72.5%) | 45 (13.6%) | 57 (17.2%) |
| STRANGLE_100 | 53 (16.0%) | 216 (65.3%) | 62 (18.7%) | 89 (26.9%) |
| STRANGLE_200 | 35 (10.6%) | 182 (55.0%) | 114 (34.4%) | 180 (54.4%) |
| STRANGLE_300 | 22 (6.6%) | 146 (44.1%) | 163 (49.2%) | 235 (71.0%) |

## STRADDLE

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 815,036.30`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 781,936.30`**
- Win rate: `67.37%` (223W / 108L)
- Max drawdown: `Rs 127,907.00`
- Best day: `Rs 76,551.25`  Worst day: `Rs -53,302.50`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 112,090 | 71.7% |
| 2021 | 52 | Rs 111,010 | 71.2% |
| 2022 | 52 | Rs 173,154 | 75.0% |
| 2023 | 52 | Rs -6,301 | 50.0% |
| 2024 | 52 | Rs 233,456 | 71.2% |
| 2025 | 53 | Rs 57,944 | 60.4% |
| 2026 | 17 | Rs 100,584 | 82.4% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_100

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 632,007.21`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 598,907.21`**
- Win rate: `59.21%` (196W / 135L)
- Max drawdown: `Rs 47,019.00`
- Best day: `Rs 69,823.75`  Worst day: `Rs -33,623.75`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 62,624 | 60.4% |
| 2021 | 52 | Rs 36,911 | 55.8% |
| 2022 | 52 | Rs 79,427 | 59.6% |
| 2023 | 52 | Rs -13,790 | 46.2% |
| 2024 | 52 | Rs 199,403 | 69.2% |
| 2025 | 53 | Rs 127,274 | 62.3% |
| 2026 | 17 | Rs 107,058 | 64.7% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_200

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 302,805.96`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 269,705.96`**
- Win rate: `51.66%` (171W / 160L)
- Max drawdown: `Rs 30,538.50`
- Best day: `Rs 50,340.00`  Worst day: `Rs -19,894.12`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 17,844 | 30.2% |
| 2021 | 52 | Rs 10,486 | 55.8% |
| 2022 | 52 | Rs 56,548 | 61.5% |
| 2023 | 52 | Rs -9,415 | 42.3% |
| 2024 | 52 | Rs 80,582 | 61.5% |
| 2025 | 53 | Rs 71,900 | 56.6% |
| 2026 | 17 | Rs 41,762 | 58.8% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## STRANGLE_300

- Traded: `331`  Skipped: `3`
- Gross P/L: `Rs 122,719.43`  Costs: `Rs 33,100.00`
- **Net P/L: `Rs 89,619.43`**
- Win rate: `36.56%` (121W / 210L)
- Max drawdown: `Rs 26,117.50`
- Best day: `Rs 35,910.00`  Worst day: `Rs -11,215.00`

| Year | Days | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 7,309 | 18.9% |
| 2021 | 52 | Rs -926 | 50.0% |
| 2022 | 52 | Rs 9,708 | 40.4% |
| 2023 | 52 | Rs -13,250 | 21.2% |
| 2024 | 52 | Rs 10,715 | 42.3% |
| 2025 | 53 | Rs 39,139 | 43.4% |
| 2026 | 17 | Rs 36,925 | 47.1% |

| Skip reason | Count |
|---|---:|
| `no_priceable_pair` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Expiry dates come from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Every offset is evaluated on the same expiry days, so the columns are directly comparable.
