# Expiry-Day Premium-Band Short Strangle (NIFTY 2020-2026)

## Strategy

- **Expiry days only.** One trade per weekly expiry, no other day is traded.
- Entry: `10:00` — sell 1 CE and 1 PE of the contract expiring that day
- Strike rule: **by premium, not by distance.** On each side independently, walk outward from ATM and take the strike whose `10:00` price is closest to the midpoint of the `Rs 5–10` band
- Ties on that distance go to the strike nearer ATM
- If no strike on a side is inside the band, the nearest-to-band strike is sold instead and the leg is marked `band_fallback` — **the day is never skipped for being out of band**
- Search depth: `60` strikes (3000 points) either side of ATM
- Stop loss: **independent per leg**, triggered when a leg reaches `200%` of its entry price (100% loss on that leg). The other leg keeps running.
- Exit: anything still open is closed at `15:20`
- No target, no adjustment, no re-entry
- Size: **1 lot(s)** — expiry-aware lot sizing (75/50/25/75/65 by era)
- Brokerage: Rs 25/order → Rs 100 per completed position (2 legs, in and out)
- Slippage: 0.00 pt/order
- Period: `2020-01-02` to `2026-06-16`

## Headline

Margin is modelled — 10% of contract value per naked short lot with the lighter side netted at 30% — not SPAN. A naked expiry-day short may attract more.

- Traded: `331`  Skipped: `3`
- **Net P/L: `Rs 45,909.25`**
- Gross P/L (after slippage, before brokerage): `Rs 79,009.25`
- CAGR on peak margin: `2.59%`  (peak margin `Rs 255,862`)
- Win rate: `47.13%` (156W / 174L)  Profit factor: `2.06`
- Max drawdown: `Rs 5,630.00`
- Best day: `Rs 1,336.25`  Worst day: `Rs -1,573.75`  Avg/day: `Rs 138.70`

## What the costs eat

The number that decides this strategy. Premium sold is small and the costs are flat, so the ratio is the whole story at one lot.

| Item | Value |
|---|---:|
| Premium collected | Rs 284,972 |
| Avg premium per trade | 14.43 pts |
| Brokerage | Rs 33,100 |
| Slippage | Rs 0 |
| **Total costs** | **Rs 33,100** |
| **Costs as % of premium collected** | **11.6%** |

## Stop-loss behaviour

| Outcome | Days | Share |
|---|---:|---:|
| Both legs stopped | 23 | 6.9% |
| One leg stopped | 191 | 57.7% |
| Neither stopped (both ran to 15:20) | 117 | 35.3% |

## Band behaviour

How often the `Rs 5–10` band was actually reachable at entry. A high fallback count means the band is the wrong one for this time of day, and the result is not really testing the stated strategy.

| Leg | Fell back outside the band | Share |
|---|---:|---:|
| CE | 48 | 14.5% |
| PE | 19 | 5.7% |
| Either leg | 64 | 19.3% |

- Avg strike distance from ATM: CE `155` pts, PE `181` pts

## Year by year

Strike distance is the check that the premium band is doing its job: a Rs 7.50 option sits further from spot as the index level and volatility rise, so these numbers should drift upward, not stay flat.

| Year | Days | Net P/L | Win % | Avg premium (pts) | Avg CE dist | Avg PE dist | Fallback days |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 53 | Rs 7,656 | 56.6% | 14.14 | 115 | 148 | 25 |
| 2021 | 52 | Rs 12,082 | 51.9% | 14.13 | 115 | 159 | 12 |
| 2022 | 52 | Rs 6,982 | 46.2% | 14.47 | 154 | 187 | 6 |
| 2023 | 52 | Rs 2,080 | 40.4% | 14.18 | 104 | 126 | 19 |
| 2024 | 52 | Rs -2,118 | 38.5% | 14.86 | 226 | 233 | 0 |
| 2025 | 53 | Rs 17,022 | 49.1% | 14.74 | 191 | 203 | 2 |
| 2026 | 17 | Rs 2,203 | 47.1% | 14.69 | 241 | 268 | 0 |

## Expiry weekday

NIFTY weekly expiry ran Thursday to 2025-08-28 and Tuesday from 2025-09-02; Monday and Wednesday rows are holiday shifts to the previous session. Expiry dates are read from the options folder names, so every transition is picked up from the data rather than hardcoded.

| Weekday | Days | Net P/L |
|---|---:|---:|
| Monday | 2 | Rs 1,866 |
| Tuesday | 33 | Rs 7,646 |
| Wednesday | 13 | Rs 3,675 |
| Thursday | 283 | Rs 32,722 |

## Skipped days

| Skip reason | Count |
|---|---:|
| `no_ce_candidate` | 3 |

## Notes

- A leg that gaps through its stop fills at the bar open; a leg that only trades through it fills at the stop price. Neither reads ahead of the trigger.
- Entry price is the open of the exact `10:00` bar. A strike with no bar at that minute is not a candidate — no stale quote is ever used.
- **Fills are assumed.** These are the cheapest contracts in the chain and the least liquid; the real bid-ask at Rs 5–10 is a meaningful fraction of the premium, so the modelled slippage may still be optimistic.
