# Opening Gap — Fade Small, Follow Large (NIFTY 2020-2026)

Spec: [`strategies/directional/opening-gap.md`](../../../strategies/directional/opening-gap.md)

## Strategy

- `gap = today's 09:15 open − previous normal session's last close`
- **FADE** when `0.15% <= |gap|/prev_close <= 0.5%` — trade against the gap, target the previous close, stop 1x the gap beyond the open
- Band is a **percentage of the previous close**, so the same kind of move is selected at Nifty 12,000 and at 25,000
- Fade confirmation: `stall` — wait for 3 bars with no new extreme in the gap's direction, enter the bar after; give up at `12:00`
- **GO** when `|gap|/prev_close >= 0.8%` **and** the 09:15 bar closes beyond its own open in the gap's direction — trade with the gap, stop at that bar's opposite extreme, target 1.5R
- The band between the fade maximum and the go threshold is deliberately not traded
- Exit `15:20`. One trade per session, no re-entry
- Size: 1 lot(s), expiry-aware (75/50/25/75/65)
- Costs, both columns: Rs 25/order (Rs 50 per round trip) + 0.50 pt/order
- Sessions with fewer than 70 bars, or not opening at 09:15, are excluded from trading and from setting reference levels
- Period: `2020-01-01` to `2026-06-19`

## How to read the two columns

**Spot** is the signal's raw edge as a futures-equivalent — no theta, no delta, no strike. It answers *does this signal predict direction*.

**Option** is the same signal bought as an ATM CE/PE of the nearest weekly, entered and exited at the same minutes. It answers *can that edge survive being expressed as a long option*.

The option column's benchmark is **not zero**. Buying random ATM options over this sample loses about **Rs 756,517** at its best setting ([heads-tails long grid](../heads-tails/)). A signal only has to pay for the theta a coin flip cannot. Spot positive with option negative is a working signal and a failed expression — not a failed strategy.

## Gap fill rate by size — every session, traded or not

The premise both variants rest on. If the fill rate does not decline as
the gap grows, small gaps are not more likely to fill than large ones and
there is no threshold to find.

| Gap (abs pts) | Sessions | Filled same day | Filled by 11:00 | Median mins to fill |
|---|---:|---:|---:|---:|
| 0–25 | 396 | 363 (91.7%) | 350 (88.4%) | 0 |
| 25–50 | 331 | 264 (79.8%) | 226 (68.3%) | 8 |
| 50–70 | 237 | 150 (63.3%) | 113 (47.7%) | 25 |
| 70–100 | 265 | 139 (52.5%) | 87 (32.8%) | 50 |
| 100–150 | 185 | 71 (38.4%) | 41 (22.2%) | 80 |
| 150–200 | 83 | 22 (26.5%) | 2 (2.4%) | 220 |
| 200+ | 96 | 9 (9.4%) | 3 (3.1%) | 290 |

Split by direction:

| Gap (abs pts) | Up sessions | Up filled | Down sessions | Down filled |
|---|---:|---:|---:|---:|
| 0–25 | 222 | 203 (91.4%) | 174 | 160 (92.0%) |
| 25–50 | 218 | 180 (82.6%) | 113 | 84 (74.3%) |
| 50–70 | 170 | 107 (62.9%) | 67 | 43 (64.2%) |
| 70–100 | 184 | 97 (52.7%) | 81 | 42 (51.9%) |
| 100–150 | 131 | 45 (34.4%) | 54 | 26 (48.1%) |
| 150–200 | 40 | 14 (35.0%) | 43 | 8 (18.6%) |
| 200+ | 46 | 3 (6.5%) | 50 | 6 (12.0%) |

## Results

### FADE

- Trades: `593`  (option priced on `582` of them)

| Column | Net P/L | Win% | PF | Max DD | Best | Worst | Avg/trade |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Spot** (futures-equivalent) | Rs 20,829 | 55.3% | 1.03 | Rs 173,846 | Rs 23,001 | Rs -8,840 | Rs 35 |
| **Option** (long ATM) | Rs -20,091 | 48.5% | 0.96 | Rs 106,616 | Rs 16,161 | Rs -6,571 | Rs -35 |

- Spot CAGR on ~Rs 197,258 modelled futures margin: `1.57%`

| Exit reason | Trades |
|---|---:|
| `target` | 292 |
| `sl` | 216 |
| `day_close` | 85 |

| Year | Trades | Spot net | Option net |
|---|---:|---:|---:|
| 2020 | 70 | Rs 41,061 | Rs 9,614 |
| 2021 | 79 | Rs 58,875 | Rs 12,648 |
| 2022 | 85 | Rs 62,460 | Rs 47,748 |
| 2023 | 115 | Rs -37,605 | Rs -18,010 |
| 2024 | 111 | Rs 2,916 | Rs -4,194 |
| 2025 | 96 | Rs -107,408 | Rs -65,599 |
| 2026 | 37 | Rs 529 | Rs -2,297 |

A fifth of all sessions are expiry days, so a 'nearest weekly' option is 0-DTE on many trades. This is where a long option is most likely to die:

| Days to expiry | Trades | Spot net | Option net |
|---|---:|---:|---:|
| 0 (expiry day) | 121 | Rs 22,087 | Rs -3,864 |
| 1-3 | 310 | Rs -8,476 | Rs -18,806 |
| 4+ | 162 | Rs 7,218 | Rs 2,579 |

### GO

- Trades: `87`  (option priced on `85` of them)

| Column | Net P/L | Win% | PF | Max DD | Best | Worst | Avg/trade |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Spot** (futures-equivalent) | Rs -5,462 | 41.4% | 0.97 | Rs 43,752 | Rs 20,530 | Rs -11,860 | Rs -63 |
| **Option** (long ATM) | Rs 22,041 | 44.7% | 1.23 | Rs 18,159 | Rs 18,524 | Rs -6,972 | Rs 259 |

- Spot CAGR on ~Rs 189,261 modelled futures margin: `-0.45%`

| Exit reason | Trades |
|---|---:|
| `sl` | 49 |
| `target` | 32 |
| `day_close` | 6 |

| Year | Trades | Spot net | Option net |
|---|---:|---:|---:|
| 2020 | 26 | Rs 3,035 | Rs 9,969 |
| 2021 | 14 | Rs 19,465 | Rs 12,998 |
| 2022 | 27 | Rs 1,062 | Rs 3,472 |
| 2024 | 4 | Rs -9,139 | Rs -6,076 |
| 2025 | 5 | Rs 11,189 | Rs 13,228 |
| 2026 | 11 | Rs -31,074 | Rs -11,549 |

A fifth of all sessions are expiry days, so a 'nearest weekly' option is 0-DTE on many trades. This is where a long option is most likely to die:

| Days to expiry | Trades | Spot net | Option net |
|---|---:|---:|---:|
| 0 (expiry day) | 15 | Rs -17,712 | Rs -8,382 |
| 1-3 | 49 | Rs 53,302 | Rs 43,555 |
| 4+ | 23 | Rs -41,052 | Rs -13,131 |

### Both variants combined

| Column | Trades | Net P/L | Win% | PF | Max DD |
|---|---:|---:|---:|---:|---:|
| Spot | 680 | Rs 15,368 | 53.5% | 1.01 | Rs 202,720 |
| Option | 667 | Rs 1,950 | 48.0% | 1.00 | Rs 110,852 |

## Sessions not traded

| Reason | Sessions |
|---|---:|
| `gap_below_threshold` | 454 |
| `gap_in_dead_band` | 229 |
| `go_not_confirmed` | 122 |
| `gap_already_filled` | 110 |
| `anomalous_session` | 11 |

| Option not priced | Trades |
|---|---:|
| `missing_entry_bar` | 12 |
| `missing_file` | 1 |

## Notes

- Entry is always the open of the bar AFTER the one that confirmed the signal. A bar stamped `T` closes at `T+5min` and cannot be read before then.
- A bar containing both the stop and the target resolves to the **stop**. The 5-minute series cannot order them; assuming the target would flatter every result.
- The option strike is taken from spot at the signal bar's close, not the entry bar's — the latter is not known when the order is placed.
- The option rides the spot signal: no premium stop, bought at entry and sold at whatever minute the spot leg exited.
- Gap fill statistics cover every session in range, including days that gapped and never came back.
