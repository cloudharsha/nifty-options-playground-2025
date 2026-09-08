# Adjusted straddle — Sleeve A results

A replication of an externally supplied spec. Same family idea as
[adjusted-straddle-half-add](../adjusted-straddle-half-add/) — sell an ATM
straddle, add to the weak side when it decays to half the strong side, unwind at
parity — but with five differences that all had to be implemented from scratch:

| | half-add family | **Sleeve A** |
|---|---|---|
| Entry gate | balance filter only | balance filter **plus** previous-day India VIX >= 12 |
| Add size | 0.25 x strong, band 0.20-0.30 | **0.20** x strong, band **0.15-0.25** |
| Leg cap | 3 per side | **4** per side, then roll to 0.75 x strong |
| Costs | flat Rs 30 / order | **full statutory stack** — Rs 20 brokerage, STT by era, exchange, SEBI, stamp, GST, 0.25 pt slippage per side |
| Size | 1 lot | **`floor(10L / (spot x lot_size x margin_rate))`**, fixed at entry |
| Pricing | 1-minute bar `open` | 1-minute bar **`close`** |

Filenames encode the variant:

| Token | Meaning |
|---|---|
| `m050` | Margin rate 0.50 in the sizing formula |
| `m019` | Margin rate 0.19 — the same trades, roughly 2.6x the lots |
| `novix` | India VIX entry gate disabled (`--vix-floor 0`) |
| `slip<x>` | Slippage other than the 0.25 points per side default |
| `cap<n>` | Legs per side other than the default 4 |
| `ci<n>` | Adjustment checks every n minutes instead of every minute |

Each run writes `_cycles.csv` (one row per weekly cycle), `_legs.csv` (one row
per option leg, with both the raw quote and the slipped fill), `_equity.csv`
(per-cycle equity and drawdown) and `_summary.md`.

The margin rate changes only the lot count and the turnover-linked costs — the
add, unwind and roll decisions are identical across `m050` and `m019`, so the
two runs share a trade path and differ only in scale.

Produced by [`../../python/adjusted-straddle-sleeve-a/`](../../python/adjusted-straddle-sleeve-a/).
Indexed in [adjusted-straddle-sleeve-a.md](../../docs/results/adjusted-straddle-sleeve-a.md).
