# Adjusted straddle results

ATM straddle with a half-trigger / 25% add rule: when one side decays to half the
other, sell more of the weak side sized at 25% of the strong side; unwind one leg
at a time as the position returns to parity.

Filenames encode the variant, and the differences matter:

| Token | Meaning |
|---|---|
| `expiry` / `intraday` | Held to weekly expiry, or closed the same session |
| `otm` | Adds may sit nearer the money (OTM vs current spot) rather than beyond existing legs |
| `cap3` | At most 3 legs per side; at the cap the strategy rolls instead of adding |
| `srch5` | Entry strike searched ±5 strikes for a balanced CE/PE pair |
| `stale` | Entry allowed on the last bar at or before 09:20 (bias probe) |
| `fb` | Never skip on the balance filter; take the best available strike |
| `nobal` | Balance filter disabled entirely |
| `monthly` | Monthly contracts instead of weekly |

Produced by [`../../python/adjusted-straddle-half-add/`](../../python/adjusted-straddle-half-add/).
Indexed in [adjusted-straddle.md](../../docs/results/adjusted-straddle.md).
