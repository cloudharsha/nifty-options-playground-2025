# Opening Gap — Fade Small, Follow Large (NIFTY 2020-2026)

Spec: [`strategies/directional/opening-gap.md`](../../../strategies/directional/opening-gap.md)

## Strategy

- `gap = today's 09:15 open − previous normal session's last close`
- **FADE** when `30 <= |gap| <= 100` — trade against the gap, target the previous close, stop 1x the gap beyond the open
- Fade confirmation: `stall` — wait for 3 bars with no new extreme in the gap's direction, enter the bar after; give up at `12:00`
- **GO** when `|gap| >= 150` **and** the 09:15 bar closes beyond its own open in the gap's direction — trade with the gap, stop at that bar's opposite extreme, target 1.5R
- The band `100 < |gap| < 150` is deliberately not traded
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

- Trades: `641`  (option priced on `633` of them)

| Column | Net P/L | Win% | PF | Max DD | Best | Worst | Avg/trade |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Spot** (futures-equivalent) | Rs 82,150 | 55.2% | 1.09 | Rs 129,972 | Rs 23,001 | Rs -7,479 | Rs 128 |
| **Option** (long ATM) | Rs 23,954 | 48.2% | 1.05 | Rs 71,673 | Rs 16,161 | Rs -6,245 | Rs 38 |

- Spot CAGR on ~Rs 196,872 modelled futures margin: `5.54%`

| Exit reason | Trades |
|---|---:|
| `target` | 305 |
| `sl` | 224 |
| `day_close` | 112 |

| Year | Trades | Spot net | Option net |
|---|---:|---:|---:|
| 2020 | 108 | Rs 33,975 | Rs 2,944 |
| 2021 | 87 | Rs 93,792 | Rs 33,505 |
| 2022 | 100 | Rs 65,415 | Rs 45,995 |
| 2023 | 119 | Rs -35,235 | Rs -16,565 |
| 2024 | 100 | Rs 23,360 | Rs 7,811 |
| 2025 | 92 | Rs -61,420 | Rs -30,798 |
| 2026 | 35 | Rs -37,737 | Rs -18,938 |

A fifth of all sessions are expiry days, so a 'nearest weekly' option is 0-DTE on many trades. This is where a long option is most likely to die:

| Days to expiry | Trades | Spot net | Option net |
|---|---:|---:|---:|
| 0 (expiry day) | 130 | Rs 20,870 | Rs -5,506 |
| 1-3 | 351 | Rs 89,104 | Rs 42,408 |
| 4+ | 160 | Rs -27,823 | Rs -12,948 |

### GO

- Trades: `73`  (option priced on `70` of them)

| Column | Net P/L | Win% | PF | Max DD | Best | Worst | Avg/trade |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Spot** (futures-equivalent) | Rs -31,671 | 38.4% | 0.84 | Rs 63,661 | Rs 20,530 | Rs -11,860 | Rs -434 |
| **Option** (long ATM) | Rs 4,108 | 41.4% | 1.04 | Rs 24,502 | Rs 18,524 | Rs -6,972 | Rs 59 |

- Spot CAGR on ~Rs 189,261 modelled futures margin: `-2.79%`

| Exit reason | Trades |
|---|---:|
| `sl` | 44 |
| `target` | 24 |
| `day_close` | 5 |

| Year | Trades | Spot net | Option net |
|---|---:|---:|---:|
| 2020 | 10 | Rs 7,304 | Rs 9,921 |
| 2021 | 8 | Rs 11,871 | Rs 5,408 |
| 2022 | 25 | Rs 150 | Rs 3,548 |
| 2024 | 5 | Rs -7,727 | Rs -5,754 |
| 2025 | 7 | Rs 2,772 | Rs 7,495 |
| 2026 | 18 | Rs -46,041 | Rs -16,509 |

A fifth of all sessions are expiry days, so a 'nearest weekly' option is 0-DTE on many trades. This is where a long option is most likely to die:

| Days to expiry | Trades | Spot net | Option net |
|---|---:|---:|---:|
| 0 (expiry day) | 7 | Rs -11,242 | Rs -6,425 |
| 1-3 | 37 | Rs 24,718 | Rs 24,320 |
| 4+ | 29 | Rs -45,148 | Rs -13,787 |

### Both variants combined

| Column | Trades | Net P/L | Win% | PF | Max DD |
|---|---:|---:|---:|---:|---:|
| Spot | 714 | Rs 50,479 | 53.5% | 1.04 | Rs 189,005 |
| Option | 703 | Rs 28,062 | 47.5% | 1.05 | Rs 96,175 |

## Sessions not traded

| Reason | Sessions |
|---|---:|
| `gap_below_threshold` | 471 |
| `gap_in_dead_band` | 184 |
| `gap_already_filled` | 120 |
| `go_not_confirmed` | 106 |
| `anomalous_session` | 11 |

| Option not priced | Trades |
|---|---:|
| `missing_entry_bar` | 10 |
| `missing_file` | 1 |

## Notes

- Entry is always the open of the bar AFTER the one that confirmed the signal. A bar stamped `T` closes at `T+5min` and cannot be read before then.
- A bar containing both the stop and the target resolves to the **stop**. The 5-minute series cannot order them; assuming the target would flatter every result.
- The option strike is taken from spot at the signal bar's close, not the entry bar's — the latter is not known when the order is placed.
- The option rides the spot signal: no premium stop, bought at entry and sold at whatever minute the spot leg exited.
- Gap fill statistics cover every session in range, including days that gapped and never came back.
