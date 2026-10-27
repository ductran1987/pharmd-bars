# Transcribing a PharmD_KS WEEKLY letter into plans/weekly-YYYY-MM-DD.json

The weekly letter is "Market Analysis for the Week of M/D" from pharmdks@substack.com, sent Friday night or Saturday.
Read it with `mcp__Gmail__get_thread` (messageFormat PLAIN_TEXT). The file date is the **Sunday** that starts that week
(the title's M/D is normally that Sunday; if not, use the Sunday on or before the first trading day and say so in `ref_note`).
Write ONE file: `plans/weekly-YYYY-MM-DD.json`. Nothing in `TRANSCRIBE.md` (daily letters) changes.

The general rules of `TRANSCRIBE.md` apply here too: **full prices** (resolve "623-656" in an NQ section where prices are
29xxx to 29623-29656, from the nearest full price in the same letter), **verbatim quotes**, **contract field**, symbolic
references stay symbolic, never invent levels or trades, note anything ambiguous.

## Output schema (JSON)
```
{
 "source": "pharmdks", "type": "weekly", "week_of": "YYYY-MM-DD",          // Sunday
 "title": "Market Analysis for the Week of M/D", "sent": "<email date, ISO UTC>", "url": "<post URL>",
 "status": "transcribed",
 "contract": {"ES": "ESZ6", "NQ": "NQZ6"},  "roll_note": "<his roll sentence(s) verbatim, else ''>",
 "ref_note": "<one line: anything odd or ambiguous>",

 "levels": {                     // the "ES Levels/Ranges:" and "NQ Levels/Ranges:" lists, top to bottom, exactly as listed
   "ES": [ {"zone": [lo, hi], "strong": true|false, "tag": "monitor for LAAF" | "monitor for LBAF" | "" , "line": "<the list line verbatim>"} ],
   "NQ": [ ... ]
 },

 "zones": {                      // prices from his commentary that are NOT in the level list
   "ES": [ {"zone": [lo, hi], "type": "zone" | "ref", "label": "<short label>", "quote": "<the sentence verbatim>"} ],
   "NQ": [ ... ]
 },

 "trades": [
   {
    "id": "wes1" | "wnq1" ...    // w + instrument + running number, letter order (commentary trades first, then tag-only trades)
    "instrument": "ES" | "NQ",
    "section": "Trading Lower" | "Trading Higher" | "levels",
    "source": "commentary" | "level_tag",
    "name": "<short name, e.g. 'LBAF of 7644-7649', 'fail/LAAF of 7712-7717'>",
    "dir": "long" | "short",
    "kind": "fade" | "break",
    "gate": [lo, hi],
    "tgt": [ [lo,hi] | price | REF, ... ],         // in the order he gives them; [] if he names none
    "mindful": [ [lo,hi] | price, ... ],            // "mindful of X in between" levels; else []
    "condition": "<his condition words verbatim, e.g. 'If this three-month range is distributive (limited evidence thus far to suggest that it is)'; else ''>",
    "quote": "<the trade sentence(s) verbatim>",
    "stop_hint": "<verbatim invalidation words if any, else ''>"
   }
 ],

 "cautions": [                   // ranges where he says he is wary / extremely cautious / won't initiate
   {"instrument": "ES" | "NQ", "side": "long" | "short", "range": [lo|null, hi|null], "zones": [[lo,hi], ...], "quote": "<verbatim>"}
 ]
}
```

## Rules
- **levels**: every line of the two level lists, in list order. `strong` = the line has `*`. `tag` = any "monitor for LBAF/LAAF"
  text on that line, lower-cased as written. A single price ("30625", "28181") → [p, p]. Skip GC and anything after "GC:".
  Skip "See last week's levels for higher" / "Will add lower if needed" (mention in `ref_note` if relevant).
- **zones**: every price range or price in COMMENTARY / PRICE / Trading Higher / Trading Lower that is not already a list level,
  e.g. a bearish RTH gap, "supply ... call it 870-960", a daily level he mentions ("29200-29226 ... daily level"), this past week's
  high/low with a number, September/July/8-3 lows, a high-time-frame decision range ("the entire 7460-7520 range").
  `type`: "ref" for a single reference price (a high, low, open), "zone" otherwise. Don't repeat a list level here, even when
  the commentary writes it slightly differently — note the difference in `ref_note` instead (e.g. list 7733-7735 vs text 7731-7735).
- **trades** — an if/then line that names a level and a direction:
  - commentary trades: "A LBAF of X can rotate back to Y", "A fail or LAAF of X can come back to Y", "Above X should magnet to Y",
    "a firm base above X is likely to resolve to Y", "X is likely to inflect price back toward Y", "if X holds ... Y trades",
    "likely to look for shorts if X trades", "X ... could produce a LBAF", "Holding below X (inclusive a fresh failed reclaim)
    is objectively bearish" (short), "If X is reclaimed after a LBAF, then the trading higher scenario comes into play" (long),
    "I would expect [that high] to be taken out above X" (long, tgt that high), "it would need to trigger a fresh loss of X to open
    a move back to Y" (short), "It is possible X is strong enough to trigger a fresh loss of Y" (fade at X, condition "It is
    possible"), "I see X as the first meaningful reclaim and opens a potential move to A and B" (long, tgt [A, B]).
    **One trade per sentence** — never merge two sentences into one trade.
    Plain "supply/resistance/sellers could be responsive" mentions with no trade are NOT trades (they may be `zones`), and
    neither are requirements ("Any fresh loss of X must produce a loss of at least Y for sellers to have clear control").
    Borderline lines you leave out go in `ref_note`.
  - kind: `fade` = LBAF / LAAF / fail / failed reclaim / hold / inflect / rejection; `break` = continuation, firm base above,
    sustain above, above X magnets to Y, fresh loss of X resolves to Y, breakdown.
  - gate: the level the trade fires from, as written in that sentence (full prices).
  - tgt: what he says it goes to, in his order. A target only implied ("the trading lower scenario comes into play") → [].
    "mindful of Z (in between)" → `mindful`, not `tgt`.
  - condition: a real qualifier only — never a restatement of the gate, never a caveat already in the quote — verbatim ("after any failure in the gap", "following a rejection at 7784-7788",
    "If this three-month range is distributive (limited evidence thus far to suggest that it is)", "on a first pass").
  - level_tag trades: every list level tagged "monitor for LAAF" (short) or "monitor for LBAF" (long) that has no commentary
    trade in the same direction at the same level → `source: "level_tag"`, `section: "levels"`, quote = the list line,
    tgt [], kind fade. If a commentary trade covers it, don't add a tag trade (the level's tag still shows in `levels`).
- **cautions**: "I will be extremely cautious on the long side between X and Y on a first pass" → side long, range [X.lo, Y.hi],
  zones [X, Y]. "wary of initiating any short near X and Y" → side short, zones [X, Y], range spanning them.
  "pause on initiating any shorts once below Z" → side short, range [null, Z]. "a bit cautious ... into X" counts too.
  One caution per sentence; the range uses only numbers that sentence states (or one it names, like "the September ETH low
  (28816.25)" just before) — never a number borrowed from a different sentence. Keep the quote verbatim.
- zones also include spanning areas: "strong supply in the 7780-7784 up to 7815-7820 range" → the non-list part [7780, 7784];
  "this general area (30210-30237 to 30520-30546 ...) ... higher time frame lower high" → [30210, 30546].
- Both instruments always; GC/YM/SPY/QQQ are skipped.
- **Daily corrections win.** If a later daily letter corrects a weekly level, the daily plan wins at run time; this file stays
  as the weekly letter wrote it.
- `python plans/validate_weekly.py plans/weekly-<date>.json` checks the schema and price sanity; fix every ERROR.
