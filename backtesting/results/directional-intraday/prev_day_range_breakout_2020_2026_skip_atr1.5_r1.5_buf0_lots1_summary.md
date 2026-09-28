# Previous-Day High / Low Breakout (NIFTY 2020-2026)

Spec: [`strategies/directional/previous-day-range-breakout.md`](../../../strategies/directional/previous-day-range-breakout.md)

## Strategy

- `PDH` / `PDL` from the previous **normal** session — weekends, holidays and the nine anomalous sessions are stepped over
- Entry: first bar that CLOSES beyond a level (buffer `0` pts); entry is the next bar's open
- Direction is whichever side breaks **first in time order**
- Gap handling `skip`: an open already beyond a level is not traded
- Stop `atr`: `1.5` x ATR-14 on 5-minute bars
- Target: `1.5x` the stop distance
- No entry after `14:00`; exit `15:20`
- Size: 1 lot(s), expiry-aware (75/50/25/75/65)
- Costs both columns: Rs 25/order + 0.50 pt/order
- Period: `2020-01-01` to `2026-06-19`

## Results

- Trades: `628` (option priced on `622`)

| Column | Net P/L | Win% | PF | Max DD | Best | Worst | Avg/trade |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Spot** (futures-equivalent) | Rs 63,188 | 43.3% | 1.08 | Rs 66,739 | Rs 17,557 | Rs -7,264 | Rs 101 |
| **Option** (long ATM) | Rs -30,267 | 42.1% | 0.94 | Rs 88,920 | Rs 13,581 | Rs -5,330 | Rs -49 |

- Spot CAGR on ~Rs 195,795 modelled futures margin: `4.42%`
- Option, per trade per lot: **Rs -48.7** against a random ATM buyer's **Rs −119.5** ([heads-tails long grid](../heads-tails/))

### By break direction

| Side | Trades | Spot net | Spot win% | Option net |
|---|---:|---:|---:|---:|
| down | 345 | Rs 26,710 | 44.1% | Rs -29,015 |
| up | 283 | Rs 36,478 | 42.4% | Rs -1,252 |

### By how the session opened

`inside` is a genuine intraday break of a level that held at the open. The others only appear when `--gap-mode` is not `skip`.

| Open state | Trades | Spot net | Spot win% | Option net |
|---|---:|---:|---:|---:|
| inside | 628 | Rs 63,188 | 43.3% | Rs -30,267 |

### By year

| Year | Trades | Spot net | Spot win% | Option net |
|---|---:|---:|---:|---:|
| 2020 | 93 | Rs 53,493 | 47.3% | Rs 25,241 |
| 2021 | 105 | Rs -12,793 | 40.0% | Rs -16,546 |
| 2022 | 76 | Rs -21,797 | 35.5% | Rs -30,912 |
| 2023 | 101 | Rs 7,144 | 46.5% | Rs -10,222 |
| 2024 | 102 | Rs -4,366 | 39.2% | Rs -13,791 |
| 2025 | 107 | Rs 31,574 | 48.6% | Rs 11,601 |
| 2026 | 44 | Rs 9,933 | 45.5% | Rs 4,364 |

### By days to expiry

| DTE | Trades | Spot net | Spot win% | Option net |
|---|---:|---:|---:|---:|
| 0 (expiry day) | 129 | Rs 7,705 | 45.7% | Rs -28,450 |
| 1-3 | 334 | Rs 41,950 | 43.4% | Rs -10,196 |
| 4+ | 165 | Rs 13,533 | 41.2% | Rs 8,379 |

| Exit reason | Trades |
|---|---:|
| `sl` | 351 |
| `target` | 264 |
| `day_close` | 13 |

## Sessions not traded

| Reason | Sessions |
|---|---:|
| `opened_beyond_level` | 698 |
| `no_breakout` | 269 |
| `anomalous_session` | 11 |

## Notes

- ATR is computed here because nothing else in this repo does. It is causal: the window ends on the last bar that CLOSED before the entry decision.
- `retest` only enters after the holding bar has closed. Deciding at the moment of the touch that the level will hold reads the future.
- A bar containing both stop and target resolves to the **stop**.
- An intrabar spot exit sells the option on the NEXT bar — that bar's own open is a price from before the trigger.
