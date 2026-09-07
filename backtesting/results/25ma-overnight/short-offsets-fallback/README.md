# Strike-offset sweep — fallback variant

The same overnight strike-offset sweep as
[`../short-offsets/`](../short-offsets/), re-run with a fallback rule that
accepts a nearby strike when the exact offset has no tradable contract.

**The filenames here are identical to those in `short-offsets/` but the numbers
differ.** Check which folder you are reading. For ITM 200 this variant reports
Rs 16,10,318 / 13.72%; the canonical exact-match run reports Rs 18,24,282 /
14.93%. Note that the 30-minute fallback is the script's *default*, so the
canonical folder must be regenerated with `--fallback-window-minutes 0`.

> **Corrected 2026-09-08** alongside the canonical run: the signal bar moved from
> 15:15 (which closes at 15:30, after the 15:29 entry) to 15:00. Pre-fix this
> variant reported Rs 25,26,751 / 18.40% for ITM 200. See the
> [lookahead audit](../../docs/lookahead-audit.md).

The results index links to `short-offsets/`, not to this folder.
