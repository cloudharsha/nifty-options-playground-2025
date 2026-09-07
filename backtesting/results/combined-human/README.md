# Human-compatible strategy results

A deliberately low-attention strategy: check the market every 15 minutes, set
GTT-equivalent stop and target orders at entry, exit on an SMA cross at a check,
and stop trading for the day after two stop-outs.

Three variants, and the folder is the only thing telling them apart — the
filenames inside are identical:

| Folder | Variant | Net P/L |
|---|---|---:|
| `./` | Base: premium stop at 2.5x entry | −Rs 3,41,725 |
| `test-no-premsl/` | No premium stop | −Rs 4,45,047 |
| `test-wide-sl/` | Wider stop | −Rs 5,11,387 |

All three lose money over 2020–2026, and loosening the stop makes it worse.

Produced by [`../../python/combined-human/`](../../python/combined-human/).
Indexed in [combined-human.md](../../docs/results/combined-human.md).
