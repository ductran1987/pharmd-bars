# Entry-model lab: which trigger to use once price reaches a PharmD level

Backtest of 55 entry triggers at PharmD levels (RSI / MACD-line / MACD-histogram regular divergence on
5/10/15/30/60m, RSI hooks, market-structure shift, rejection and engulfing candles, the 5m/15m reclaim close,
and a resting limit at the level), with executable fills only.

Run from the repo root:

```
python entry_lab/run.py AB      # universes A (PharmD fade trades) and B (every plan level) + random-entry pool
python entry_lab/run.py C       # the same triggers anywhere in the session (at-level vs away control)
python entry_lab/reaction.py    # first-passage odds at PharmD levels vs pseudo-levels
python entry_lab/mtf.py         # multi-timeframe / multi-oscillator confluence entries
python entry_lab/nullmatch.py   # random-timing benchmark per trigger (same delays and stop sizes, no price signal)
python entry_lab/analyze.py     # summaries (needs out/light and out/gross runs for the cost columns)
python entry_lab/export_dash.py # JSON datasets for the report page (out/dash/)
```

The light-cost and no-cost runs re-use `run.run()` with `lab.SLIP` / `lab.COMM` changed and `run.OUT` pointed at
`out/light` or `out/gross`.

Files
- `lab.py` — data (per-contract 5m bars via `contracts.load`, plan refs via `plan_refs`), indicators, triggers, exits.
- `run.py` — runs every trigger x exit; random-entry candidate pool; universe C.
- `reaction.py` — does price move k x ATR15 the trade's way first after a level fill? Real levels vs pseudo-levels.
- `mtf.py` — confluence combos (e.g. 30m divergence, then a 5m divergence).
- `nullmatch.py` — the benchmark each trigger is judged against. (`run.py`'s first null pool and `paired.py` are kept
  for reference but are biased: that pool only enters on bars whose own low is at the level, which over-samples
  breakdowns, and the paired test conditions on a second low having formed.)
- `analyze.py`, `paired.py`, `report_data.py`, `export_dash.py` — statistics, nulls, report datasets.

Conventions (see the docstring at the top of `lab.py`): a trigger is known at the close of its own bar and fills at
the next 5m open + 2 ticks; stops 1 tick past the trigger's swing extreme, never closer than 1 x ATR5, 2 ticks slip;
targets = PharmD's first target >= 1.5R (skip if < 1R), 1-tick trade-through; stop checked first inside a bar;
$500 risk, $2.60 per micro round trip; entries from the letter's posting time to 15:30 ET, flat at the 15:55 bar.

Large outputs (`out/**/*.pkl`) are not committed; re-run the scripts to rebuild them.
