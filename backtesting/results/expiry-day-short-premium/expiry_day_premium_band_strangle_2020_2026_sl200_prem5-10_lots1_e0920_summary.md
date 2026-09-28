# Expiry-Day Premium-Band Short Strangle (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `09:20` — sell 1 CE and 1 PE of the contract expiring that day
- Strike rule: **by premium, not by distance.** On each side independently, walk outward from ATM and take the strike whose `09:20` price is closest to the midpoint of the `Rs 5–10` band
- Ties on that distance go to the strike nearer ATM
- If no strike on a side is inside the band, the nearest-to-band strike is sold instead and the leg is marked `band_fallback` — **the day is never skipped for being out of band**
- Search depth: `60` strikes (3000 points) either side of ATM
- Stop loss: **independent per leg**, triggered when a leg reaches `200%` of its entry price (100% loss on that leg). The other leg keeps running.
- Exit: anything still open is closed at `15:20`
- No target, no adjustment, no re-entry
- Size: **1 lot(s)** — expiry-aware lot sizing (75/50/25/75/65 by era)
- Brokerage: Rs 25/order → Rs 100 per completed position (2 legs, in and out)
- Slippage: 0.50 pt/order
- Period: `2020-01-02` to `2026-06-16`

## Headline

Margin is modelled — 10% of contract value per naked short lot with the lighter side netted at 30% — not SPAN. A naked expiry-day short may attract more.

- Traded: `331`  Skipped: `3`
- **Net P/L: `Rs 4,132.50`**
- Gross P/L (after slippage, before brokerage): `Rs 37,232.50`
- CAGR on peak margin: `0.25%`  (peak margin `Rs 255,750`)
- Win rate: `36.25%` (120W / 211L)  Profit factor: `1.06`
- Max drawdown: `Rs 12,355.00`
- Best day: `Rs 1,021.25`  Worst day: `Rs -1,622.50`  Avg/day: `Rs 12.48`

## What the costs eat

The number that decides this strategy. Premium sold is small and the costs are flat, so the ratio is the whole story at one lot.

| Item | Value |
|---|---:|
| Premium collected | Rs 279,543 |
| Avg premium per trade | 14.18 pts |
| Brokerage | Rs 33,100 |
| Slippage | Rs 39,610 |
| **Total costs** | **Rs 72,710** |
| **Costs as % of premium collected** | **26.0%** |

## Stop-loss behaviour

| Outcome | Days | Share |
|---|---:|---:|
| Both legs stopped | 25 | 7.6% |
| One leg stopped | 193 | 58.3% |
| Neither stopped (both ran to 15:20) | 113 | 34.1% |

## Band behaviour

How often the `Rs 5–10` band was actually reachable at entry. A high fallback count means the band is the wrong one for this time of day, and the result is not really testing the stated strategy.

| Leg | Fell back outside the band | Share |
|---|---:|---:|
| CE | 40 | 12.1% |
| PE | 23 | 6.9% |
| Either leg | 57 | 17.2% |

- Avg strike distance from ATM: CE `176` pts, PE `209` pts

## Year by year

Strike distance is the check that the premium band is doing its job: a Rs 7.50 option sits further from spot as the index level and volatility rise, so these numbers should drift upward, not stay flat.

| Year | Days | Net P/L | Win % | Avg premium (pts) | Avg CE dist | Avg PE dist | Fallback days |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 53 | Rs -1,231 | 41.5% | 13.39 | 127 | 168 | 25 |
| 2021 | 52 | Rs 1,955 | 28.8% | 13.70 | 125 | 183 | 12 |
| 2022 | 52 | Rs 820 | 34.6% | 14.16 | 167 | 213 | 6 |
| 2023 | 52 | Rs -5,805 | 21.2% | 14.45 | 118 | 134 | 13 |
| 2024 | 52 | Rs -4,896 | 38.5% | 14.78 | 244 | 286 | 1 |
| 2025 | 53 | Rs 8,474 | 47.2% | 14.54 | 229 | 231 | 0 |
| 2026 | 17 | Rs 4,816 | 52.9% | 14.44 | 309 | 329 | 0 |

## Expiry weekday

NIFTY weekly expiry ran Thursday to 2025-08-28 and Tuesday from 2025-09-02; Monday and Wednesday rows are holiday shifts to the previous session. Expiry dates are read from the options folder names, so every transition is picked up from the data rather than hardcoded.

| Weekday | Days | Net P/L |
|---|---:|---:|
| Monday | 2 | Rs -466 |
| Tuesday | 33 | Rs 8,803 |
| Wednesday | 13 | Rs 1,204 |
| Thursday | 283 | Rs -5,409 |

## Skipped days

| Skip reason | Count |
|---|---:|
| `no_ce_candidate` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Entry price is the open of the exact `09:20` bar. A strike with no bar at that minute is not a candidate — no stale quote is ever used.
- **Fills are assumed.** These are the cheapest contracts in the chain and the least liquid; the real bid-ask at Rs 5–10 is a meaningful fraction of the premium, so the modelled slippage may still be optimistic.
