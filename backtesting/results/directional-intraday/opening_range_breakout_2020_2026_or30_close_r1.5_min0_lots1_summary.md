# Opening Range Breakout (NIFTY 2020-2026)

Spec: [`strategies/directional/opening-range-breakout.md`](../../../strategies/directional/opening-range-breakout.md)

## Strategy

- Opening range: the first `30` minutes. On 5-minute bars that is every bar fully inside the window — the last one is stamped `09:40`, not the one on the boundary
- Entry mode `close`: a bar must CLOSE beyond the range; entry is the next bar's open
- Direction is whichever side breaks **first in time order**
- Stop: the opposite end of the range
- Target: `1.5x` the range width
- No entry after `14:00`; exit `15:20`
- Range filters: min `0` pts, no max
- One trade per session, no re-entry after a stop-out
- Size: 1 lot(s), expiry-aware (75/50/25/75/65)
- Costs both columns: Rs 25/order + 0.50 pt/order
- Period: `2020-01-01` to `2026-06-19`

## Results

- Trades: `1522` (option priced on `1502`)

| Column | Net P/L | Win% | PF | Max DD | Best | Worst | Avg/trade |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Spot** (futures-equivalent) | Rs 17,610 | 49.7% | 1.01 | Rs 182,941 | Rs 29,896 | Rs -25,498 | Rs 12 |
| **Option** (long ATM) | Rs -226,543 | 38.9% | 0.88 | Rs 300,853 | Rs 22,461 | Rs -15,132 | Rs -151 |

- Spot CAGR on ~Rs 197,246 modelled futures margin: `1.33%`
- Option, per trade per lot: **Rs -150.8** against a random ATM buyer's **Rs −119.5** ([heads-tails long grid](../heads-tails/), best of 28 cells)

| Exit reason | Trades |
|---|---:|
| `day_close` | 764 |
| `sl` | 460 |
| `target` | 298 |

### By break direction

A source claims shorts produced 75% of ORB profit despite a bull market. This is where that gets checked.

| Side | Trades | Spot net | Spot win% | Option net |
|---|---:|---:|---:|---:|
| up | 767 | Rs -54,912 | 49.3% | Rs -115,345 |
| down | 755 | Rs 72,522 | 50.2% | Rs -111,198 |

### By opening-range width

The stop IS the range width, so a narrow range risks little but is also the setup most easily overwhelmed by costs and noise.

| Range (pts) | Trades | Spot net | Spot win% | Option net |
|---|---:|---:|---:|---:|
| 0–40 | 64 | Rs 34,954 | 56.2% | Rs 16,560 |
| 40–70 | 475 | Rs 8,373 | 47.2% | Rs -49,766 |
| 70–100 | 490 | Rs 101,928 | 51.0% | Rs -47,750 |
| 100–150 | 352 | Rs -96,460 | 50.3% | Rs -105,778 |
| 150+ | 141 | Rs -31,185 | 49.6% | Rs -39,810 |

### By year

| Year | Trades | Spot net | Spot win% | Option net |
|---|---:|---:|---:|---:|
| 2020 | 236 | Rs 39,734 | 48.3% | Rs -7,750 |
| 2021 | 243 | Rs 46,341 | 49.8% | Rs 12,655 |
| 2022 | 239 | Rs 26,390 | 51.9% | Rs -15,865 |
| 2023 | 232 | Rs -12,352 | 49.1% | Rs -43,505 |
| 2024 | 235 | Rs 36,861 | 47.7% | Rs -27,901 |
| 2025 | 229 | Rs -10,341 | 54.1% | Rs -105,640 |
| 2026 | 108 | Rs -109,023 | 44.4% | Rs -38,537 |

### By days to expiry

A fifth of sessions are expiry days, so the nearest weekly option is 0-DTE on many trades.

| DTE | Trades | Spot net | Option net |
|---|---:|---:|---:|
| 0 (expiry day) | 317 | Rs 11,913 | Rs -95,181 |
| 1-3 | 823 | Rs -64,769 | Rs -143,357 |
| 4+ | 382 | Rs 70,466 | Rs 11,995 |

## Sessions not traded

| Reason | Sessions |
|---|---:|
| `no_breakout` | 73 |
| `anomalous_session` | 11 |

## Notes

- The opening range uses only bars fully inside the window. A bar stamped `T` covers `[T, T+5min)`, so a 30-minute range ends at the bar stamped 09:40.
- In `close` mode entry is the next bar's open; the confirming close is not knowable until the bar ends.
- In `touch` mode the spot fills at the level (a resting order would have been taken there) but the option enters on the next bar, and the entry bar's own high/low cannot stop the trade out — that movement partly precedes the entry.
- A bar containing both stop and target resolves to the **stop**.
- Direction is the first break in time order, never the day's eventual outcome.
