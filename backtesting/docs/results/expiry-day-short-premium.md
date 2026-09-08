# Expiry-Day Short Premium

Straddles and strangles sold at 09:20 on weekly expiry day and closed at 15:20,
with an **independent per-leg stop**: a leg is bought back once it has lost a set
percentage of its premium, and the other leg keeps running. Entry premiums must be
within 20% of each other or the strike is shifted to find a balanced pair.

Two things settled here: **sell the straddle, not the strangles**, and **stop at a
80–90% loss, not 50%** — see the [stop-loss sweep](#the-stop-loss-sweep--50-is-too-tight-for-everything).

- Scripts: [`backtesting/python/expiry-day-short-premium/`](../../python/expiry-day-short-premium/)
- Results: [`backtesting/results/expiry-day-short-premium/`](../../results/expiry-day-short-premium/)

Back to the [backtesting index](../../README.md).

Capital Base is what the strategy actually needs, not a fixed reference - read the
[index notes](../../README.md#reading-the-numbers) before comparing rows across families.

All rows are ~300 quantity on the same 334 expiry days, so the peak margin is
effectively identical (Rs 11.1L) and the columns are directly comparable.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Current | 2020–2026 | Expiry-Day ATM Straddle — **90% per-leg SL**, strict 20% balance filter | Profit | Rs 11.07L | Rs 7,96,202 | 8.75% CAGR | Rs 60,536 | [Summary](../../results/expiry-day-short-premium/expiry_day_straddle_strangle_2020_2026_sl190_bal20_srch5_summary.md) | **Best risk-adjusted.** 145 days, ret/DD 13.2. See the [stop-loss sweep](#the-stop-loss-sweep--50-is-too-tight-for-everything) |
| Current | 2020–2026 | Expiry-Day ATM Straddle — **80% per-leg SL**, balance fallback (never skips) | Profit | Rs 11.07L | Rs 8,47,574 | 9.20% CAGR | Rs 73,667 | [Summary](../../results/expiry-day-short-premium/expiry_day_straddle_strangle_2020_2026_sl180_bal20_srch5_fb_summary.md) | Best ret/DD on the full 331-day sample (11.5) |
| Current | 2020–2026 | Expiry-Day ATM Straddle — 150% per-leg SL, balance filter with fallback (never skips) | Profit | Rs 11.07L | Rs 8,94,850 | 9.62% CAGR | Rs 1,17,680 | [Summary](../../results/expiry-day-short-premium/expiry_day_straddle_strangle_2020_2026_sl150_bal20_srch5_fb_summary.md) | **Best of the family.** 331 of 334 expiry days, win 73.4%, PF 1.68. 2023 was a loss (−Rs 41,455) |
| Current | 2020–2026 | Expiry-Day ATM Straddle — 150% per-leg SL, strict 20% balance filter | Profit | Rs 11.07L | Rs 7,27,339 | 8.14% CAGR | Rs 75,388 | [Summary](../../results/expiry-day-short-premium/expiry_day_straddle_strangle_2020_2026_sl150_bal20_srch5_summary.md) | **Only 145 of 334 days traded** — on expiry day the ATM strike is already the most balanced pair, so shifting the centre cannot rescue an unbalanced open. Lower drawdown, less than half the sample |
| Current | 2020–2026 | Expiry-Day OTM 100 Strangle — 150% per-leg SL, legs balanced independently | Profit | Rs 11.09L | Rs 5,20,268 | 6.14% CAGR | Rs 59,805 | [Summary](../../results/expiry-day-short-premium/expiry_day_straddle_strangle_2020_2026_sl150_bal20_legs_srch5_summary.md) | 330 days; moving CE and PE strikes separately removes almost every skip |
| Current | 2020–2026 | Expiry-Day OTM 100 Strangle — 150% per-leg SL, centre-shift balance with fallback | Profit | Rs 11.09L | Rs 5,17,802 | 6.12% CAGR | Rs 49,800 | [Summary](../../results/expiry-day-short-premium/expiry_day_straddle_strangle_2020_2026_sl150_bal20_srch5_fb_summary.md) | Same result as balancing the legs independently — for a 100-wide strangle the two methods converge |
| Current | 2020–2026 | Expiry-Day OTM 200 Strangle — 150% per-leg SL, centre-shift balance with fallback | Profit | Rs 11.12L | Rs 1,29,766 | 1.73% CAGR | Rs 30,345 | [Summary](../../results/expiry-day-short-premium/expiry_day_straddle_strangle_2020_2026_sl150_bal20_srch5_fb_summary.md) | Win rate falls to 51.1%; the 150% stop is only ~4 points away at this width |
| Current | 2020–2026 | Expiry-Day OTM 300 Strangle — 150% per-leg SL, centre-shift balance with fallback | Profit | Rs 11.14L | Rs 26,116 | 0.36% CAGR | Rs 34,852 | [Summary](../../results/expiry-day-short-premium/expiry_day_straddle_strangle_2020_2026_sl150_bal20_srch5_fb_summary.md) | **Effectively dead.** Win 36.3%, stop sits 2 points from entry, costs eat 16.6% of premium collected |

## Which structure to sell

**Sell the straddle, not the strangles.** Returns decay monotonically as the
strikes move out, and the decay is steep:

| Variant | Net P/L | CAGR | Win rate | Profit factor |
|---|---:|---:|---:|---:|
| Straddle (ATM) | Rs 8,94,850 | **9.62%** | 73.4% | 1.68 |
| Strangle OTM 100 | Rs 5,17,802 | 6.12% | 66.2% | 1.93 |
| Strangle OTM 200 | Rs 1,29,766 | 1.73% | 51.1% | 1.48 |
| Strangle OTM 300 | Rs 26,116 | 0.36% | 36.3% | 1.17 |

*(figures in this section are at the original 50%-loss stop, so the widths are
compared on equal terms; the [sweep below](#the-stop-loss-sweep--50-is-too-tight-for-everything)
shows every width improves with a wider stop, and the ranking does not change.)*

**The reason is the stop, not the strikes.** A proportional stop is, on a cheap
option, an absolute distance measured in noise:

| Variant | Avg premium collected | Stop distance per leg | Costs as % of premium |
|---|---:|---:|---:|
| Straddle | 106.2 pts | **26.5 pts** | 1.3% |
| OTM 100 | 40.5 pts | 10.1 pts | 3.3% |
| OTM 200 | 16.5 pts | 4.1 pts | 8.1% |
| OTM 300 | 8.0 pts | **2.0 pts** | **16.6%** |

At OTM 300 the stop sits two points from entry. NIFTY crosses two points
constantly, and two points is inside a realistic bid-ask on a far option, so the
backtest's fills there are optimistic on top of everything else. Costs then take
a sixth of the premium before the trade starts.

If you want to sell strangles on expiry day, the stop has to be defined in
points or in premium terms, not as a percentage of a small number.

## The stop-loss sweep — 50% is too tight for everything

The 150% stop (a 50% loss on the leg) was the starting specification. Sweeping it
from a 50% to a 100% loss, across all four widths and **both** sample definitions,
shows 50% is the worst or near-worst setting for every strangle and leaves the
straddle carrying unnecessary drawdown.

Two samples are reported because 145 days is thin for choosing between adjacent
stop levels. A setting is only called robust if it ranks top-3 on
return-per-drawdown in **both**.

### Straddle

| SL loss | Strict net | Strict ret/DD | Full net | Full ret/DD | Verdict |
|---|---:|---:|---:|---:|---|
| 50% | Rs 7,27,339 | 9.6 | **Rs 8,94,850** | 7.6 | highest raw net, worst drawdown |
| 60% | Rs 7,18,596 | 11.0 | Rs 7,69,434 | 5.8 | |
| 70% | Rs 7,36,349 | **13.0** | Rs 7,81,936 | 6.1 | strict only — does not survive |
| **80%** | Rs 7,55,862 | 12.4 | Rs 8,47,574 | **11.5** | **robust** |
| **90%** | **Rs 7,96,202** | **13.2** | Rs 8,55,210 | 10.6 | **robust** |
| 100% | Rs 6,63,966 | 9.5 | Rs 8,23,196 | 8.6 | |

**80–90% is the answer.** 70% looks excellent on the filtered sample (ret/DD 13.0,
second best) and falls to fifth on the full sample — a good illustration of why a
single sample is not enough to pick a parameter.

The honest wrinkle: on the full sample the original 50% earns the **most money**
(Rs 8,94,850) — but on Rs 1,17,680 of drawdown against Rs 73,667 at 80%. About 5%
more profit for about 60% more drawdown. That is a trade, not an error.

### Strangles

Full-sample net P/L:

| Width | 50% | 70% | 80% | 90% | 100% | Robust optimum |
|---|---:|---:|---:|---:|---:|---|
| Strangle 100 | Rs 5,17,802 | Rs 5,98,907 | **Rs 6,25,094** | Rs 5,44,245 | Rs 6,17,756 | **70–80%** |
| Strangle 200 | Rs 1,29,766 | Rs 2,69,706 | **Rs 3,26,144** | Rs 3,01,113 | Rs 3,38,905 | **60–80%** |
| Strangle 300 | Rs 26,116 | Rs 89,619 | Rs 1,14,461 | Rs 1,46,075 | **Rs 1,52,313** | **80–100%** |

Strangle 200 nearly triples and strangle 300 rises almost sixfold simply by
widening the stop. 50% is last for all three in both samples.

**The further out the strike, the wider the stop has to be** — the same mechanism
as the width comparison above. A percentage stop on a cheap option is a tiny
absolute distance, so far strikes get whipsawed out of positions that would have
expired worthless. Widening the stop does not make the strangles competitive with
the straddle; it stops them bleeding.

### It does not change which structure to trade

The straddle beats every strangle at every stop level. Best straddle 9.60% CAGR
against best strangle-100 at 7.16%.

## The balance filter is the binding constraint

On expiry day the strike nearest spot is **already** the most balanced pair
available, so shifting the centre by 50 points can only make the ratio worse.
Where spot opens far from a 50-point strike, the intrinsic value of the ITM leg
dominates and no centre passes a 20% test.

Example — 2025-01-16, spot 23335.50, ATM 23350:

| Centre | CE | PE | min/max |
|---:|---:|---:|---:|
| **23350** | 29.75 | 54.35 | **0.55** |
| 23300 | 53.30 | 28.00 | 0.53 |
| 23400 | 18.50 | 95.00 | 0.19 |
| 23250 | 88.90 | 15.10 | 0.17 |

The ATM is the best on offer and it still fails a 20% test. Applied strictly,
the filter skips **189 of 334 expiry days**.

Three ways to handle it, all tested:

| Handling | Days traded | Straddle CAGR | Max DD |
|---|---:|---:|---:|
| Strict — skip unbalanced days | 145 | 8.14% | Rs 75,388 |
| Fallback — take the best pair anyway | 331 | **9.62%** | Rs 1,17,680 |
| Independent legs (strangles only) | 330 | n/a | n/a |

Skipping does buy a materially lower drawdown (Rs 75,388 vs Rs 1,17,680) but
halves the sample and lowers the return. For strangles, balancing the two legs
independently removes nearly every skip — but for the 100-wide strangle it lands
in the same place as the fallback, so it is not doing much work.

## Honest caveats

- **Peak margin is Rs 11.1L for ~300 quantity**, modelled at 10% of contract
  value with the lighter side netted at 30%. Not SPAN. A naked expiry-day short
  may attract more.
- The best row here returns **9.62%**, below the
  [low-touch weekly straddle](../../finalized/weekly-adjusted-straddle-low-touch/)
  at 12.54% on Rs 6.46L — roughly a third of the capital for more return and a
  much smaller drawdown. This family is interesting, not better.
- **2023 lost money** on the straddle (−Rs 41,455) and 2024 carried the sample
  (+Rs 3,59,412). One year is 40% of the total.
- Costs are Rs 25/order plus 0.5 pt/order slippage. Expiry-day far strikes are
  the least liquid contracts in the dataset and the most likely to fill worse
  than modelled.
