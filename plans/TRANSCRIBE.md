# Transcribing a PharmD_KS daily letter into plans/plan-YYYY-MM-DD.json

Read the Gmail thread with `mcp__Gmail__get_thread` (messageFormat PLAIN_TEXT). The letter is "Market Analysis and Trades for M/D";
the plan date is that M/D in 2026 (the letter is sent the evening before). Write ONE file: `plans/plan-YYYY-MM-DD.json`.

## Output schema (JSON)
```
{
 "source": "pharmdks", "date": "YYYY-MM-DD", "status": "transcribed",
 "ref_date_note": "<one line: anything odd, e.g. holiday, roll, 'ES is less clean'>",
 "zones": { "ES": [[lo,hi], ...], "NQ": [[lo,hi], ...] },      // every explicit price zone or single level mentioned, full prices
 "trades": [
   {
    "id": "es1" | "nq1" ... (instrument prefix + running number, in letter order),
    "instrument": "ES" | "NQ",
    "name": "<short name, e.g. 'LBAF of 7749-7752', 'LAAF of today's high'>",
    "dir": "long" | "short",
    "tag": "<grade exactly as written, e.g. 'B/B+', 'A/A-', 'C+/B-'>",
    "quote": "<the trade sentence verbatim>",
    "kind": "fade" | "break",
    "gate": [lo, hi]            // the zone the trade fires from (see rules)
    "tgt": [ [lo,hi] | price | REF, ... ]   // targets in order, nearest first
    "stop_hint": "<verbatim words about invalidation if any, else ''>"
   }
 ]
}
```

## Rules
- Only trades from the **TRADES:** section (NQ: / ES: subsections). Skip GC/gold, SPY, QQQ, YM. Skip "implied" generic
  sentences with no level ("other trades are implied…"). Include conditional trades that name a level.
- **Full prices.** He abbreviates: "49-52" in an ES section where prices are 77xx means 7749-7752; "639-669" in NQ means
  30639-30669. Resolve from the nearest full price in the same letter. ES ~ 6xxx–8xxx, NQ ~ 2xxxx–3xxxx.
- **Symbolic references** stay symbolic (strings) — do NOT guess numbers for them. Allowed REF strings:
  `RTH_HIGH`, `RTH_LOW` ("today's high/low"), `IB_HIGH`, `IB_LOW` (initial balance = first hour 9:30–10:30 ET),
  `ON_HIGH`, `ON_LOW` ("overnight / last night's" high/low), `PREV_RTH_HIGH`, `PREV_RTH_LOW` ("yesterday's high/low"),
  `WEEK_HIGH`, `WEEK_LOW`, `FRI_HIGH`, `FRI_LOW`, `MON_HIGH`, `MON_LOW`, `TUE_HIGH`, `TUE_LOW`, `WED_HIGH`, `WED_LOW`, `THU_HIGH`, `THU_LOW`,
  `APBL` (afternoon pullback low — only if he gives no number), `OR5_HIGH`, `OR5_LOW` (5-minute opening range).
  If he gives the number in the letter (e.g. "today's high (7783-7787)" or "APBL of 30622"), use the number.
- **kind**: `fade` for hold / LBAF / LAAF / failed reclaim / fail of a level / gap-fill reversal (price goes into the zone and fails);
  `break` for "persistent weakness below", "persistent strength above", "breakdown short", "breakout long", "session downtrend/uptrend below/above", "true gap up which holds".
- **gate** (a 2-element list, lo ≤ hi; a single price → [p, p]):
  - hold/LBAF/LAAF/failed reclaim of a zone → that zone.
  - LBAF/LAAF of a specific low/high → [REF, REF] or [price, price].
  - break trades → the zone being broken.
  - "LBAF of X, ideally holding Y" → gate is X; mention Y in stop_hint.
- **tgt**: targets in the order he gives them; "targeting roughly 600" in NQ → 30600; "monitor for continuation" adds nothing.
  If no target is stated for the trade, take the first level in the trade's direction from the Trading Higher/Lower commentary for that instrument.
- dir: long for Long/LBAF/hold/reclaim trades; short for Short/LAAF/fail/weakness trades.
- Keep `quote` verbatim including the grade.
- Do not invent trades, levels or grades. If something is ambiguous, pick the most literal reading and note it in `ref_date_note`.
