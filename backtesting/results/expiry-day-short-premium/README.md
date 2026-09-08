# Expiry-day short premium results

Straddles and strangles sold at 09:20 on weekly expiry day, closed 15:20, with an
independent per-leg stop at 150% of entry price.

One run sweeps all four widths — straddle (ATM) and strangles at OTM 100 / 200 /
300 — over the same 334 expiry days, so the variants in a single file are
directly comparable. `offset` is the first column of the daywise CSV.

Filenames encode the variant:

| Token | Meaning |
|---|---|
| `sl150` … `sl200` | Leg bought back at that % of its entry price — `sl150` is a 50% loss, `sl190` a 90% loss, `sl200` a 100% loss |
| `bal20` | CE and PE premiums must be within 20% at entry |
| `srch5` | Strikes searched ±5 either side for a balanced pair |
| `legs` | CE and PE strikes moved **independently** to balance, instead of shifting the centre together |
| `fb` | Balance fallback — enter the best-balanced pair rather than skipping the day |

Without `fb` the strict filter skips 189 of 334 expiry days; see the
[index doc](../../docs/results/expiry-day-short-premium.md#the-balance-filter-is-the-binding-constraint)
for why the ATM strike is already the most balanced pair on expiry day.

## Files

| File | Description |
|------|-------------|
| `*_daywise.csv` | One row per expiry day per offset — strikes, entry premiums, both stop prices, both exit reasons, modelled margin, P&L |
| `*_summary.md` | Comparison table across widths, stop-loss behaviour, per-variant yearly breakdown |
| `*.log` | Run log |

## Headline

Best configuration found, at each width (CAGR on modelled peak margin, ~Rs 11.1L
for ~300 quantity — not a fixed reference base):

| Variant | Best stop | Days | Net P/L | CAGR | Max DD |
|---|---|---:|---:|---:|---:|
| **Straddle, strict filter** | **90% loss** | 145 | Rs 7,96,202 | 8.75% | **Rs 60,536** |
| Straddle, fallback | 80% loss | 331 | Rs 8,47,574 | 9.20% | Rs 73,667 |
| Strangle 100 | 80% loss | 331 | Rs 6,25,094 | 7.16% | Rs 55,431 |
| Strangle 200 | 100% loss | 331 | Rs 3,38,905 | 4.21% | Rs 36,045 |
| Strangle 300 | 100% loss | 331 | Rs 1,52,313 | 2.00% | Rs 22,180 |

Two results this family settles:

**The straddle wins at every stop level**, and the decay outward is steep, because
a percentage stop on a cheap option is an absolute distance measured in noise —
26.5 points from entry on the straddle, 2.0 points at OTM 300.

**A 50% stop is too tight for everything.** Widening it to 80–90% cuts the
straddle's drawdown by roughly a quarter, nearly triples strangle 200 and lifts
strangle 300 almost sixfold. The further out the strike, the wider the stop has
to be. Both the strict and full samples were swept so the chosen levels are ones
that rank well in both, not just the luckier one.

Produced by [`../../python/expiry-day-short-premium/`](../../python/expiry-day-short-premium/).
Indexed in [expiry-day-short-premium.md](../../docs/results/expiry-day-short-premium.md).
