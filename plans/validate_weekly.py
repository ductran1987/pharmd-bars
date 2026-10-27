"""Schema/sanity check for transcribed WEEKLY plans (see TRANSCRIBE_WEEKLY.md).
    python plans/validate_weekly.py plans/weekly-2026-10-25.json [--letter letter.txt]
With --letter (the letter's plain text) it also checks that every quote/line is verbatim in the letter."""
import json, sys, re, datetime as dt

RANGE = {"ES": (4000, 9000), "NQ": (14000, 36000)}
SPAN = {"ES": 600, "NQ": 3500}
REFS = {"WEEK_HIGH", "WEEK_LOW", "PREV_WEEK_HIGH", "PREV_WEEK_LOW", "FRI_HIGH", "FRI_LOW", "THU_HIGH", "THU_LOW",
        "MON_HIGH", "MON_LOW", "TUE_HIGH", "TUE_LOW", "WED_HIGH", "WED_LOW"}


def nums(x):
    if isinstance(x, bool) or x is None: return []
    if isinstance(x, (int, float)): return [float(x)]
    if isinstance(x, list): return [v for e in x for v in nums(e)]
    return []


def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def zone_ok(z, err, where):
    if not (isinstance(z, list) and len(z) == 2):
        err.append(f"{where}: zone must be [lo, hi]"); return
    if all(isinstance(v, (int, float)) for v in z) and z[0] > z[1]: err.append(f"{where}: lo > hi")


def check(path, letter=None):
    err, warn = [], []
    p = json.load(open(path))
    for k in ("source", "type", "week_of", "title", "status", "contract", "roll_note", "ref_note", "levels", "zones", "trades", "cautions"):
        if k not in p: err.append(f"missing key {k}")
    if p.get("type") != "weekly": err.append("type must be 'weekly'")
    if p.get("status") != "transcribed": err.append("status must be 'transcribed'")
    try:
        d = dt.date.fromisoformat(p.get("week_of", ""))
        if d.weekday() != 6: err.append("week_of must be a Sunday")
    except Exception:
        err.append("bad week_of")
    if not path.endswith(f"weekly-{p.get('week_of')}.json"): err.append("file name does not match week_of")
    for s in ("ES", "NQ"):
        c = (p.get("contract") or {}).get(s, "")
        if not re.match(rf"^{s}[HMUZ]\d$", c): err.append(f"bad/missing contract {s}: {c!r}")
    L = norm(letter) if letter else None

    def verbatim(txt, where):
        if L is not None and txt and norm(txt) not in L:
            err.append(f"{where}: not verbatim in the letter: {txt[:80]!r}")

    for s in ("ES", "NQ"):
        allv = []
        lv = p.get("levels", {}).get(s, [])
        if not lv: err.append(f"no {s} levels")
        for i, l in enumerate(lv):
            zone_ok(l.get("zone"), err, f"{s} level {i}")
            if not isinstance(l.get("strong"), bool): err.append(f"{s} level {i}: strong must be true/false")
            if l.get("tag") not in ("", "monitor for laaf", "monitor for lbaf"): err.append(f"{s} level {i}: tag {l.get('tag')!r}")
            if ("*" in l.get("line", "")) != l.get("strong"): err.append(f"{s} level {i}: strong flag disagrees with the line")
            verbatim(l.get("line", ""), f"{s} level {i}")
            allv += nums(l.get("zone"))
        hi_first = [max(nums(l["zone"])) for l in lv if nums(l.get("zone"))]
        if any(a < b for a, b in zip(hi_first, hi_first[1:])): warn.append(f"{s} level list is not top-to-bottom")
        listed = {tuple(l["zone"]) for l in lv if isinstance(l.get("zone"), list)}
        for i, z in enumerate(p.get("zones", {}).get(s, [])):
            zone_ok(z.get("zone"), err, f"{s} zone {i}")
            if tuple(z.get("zone") or []) in listed: warn.append(f"{s} zone {z.get('zone')} repeats a list level")
            if z.get("type") not in ("zone", "ref"): err.append(f"{s} zone {i}: type")
            verbatim(z.get("quote", ""), f"{s} zone {i}")
            allv += nums(z.get("zone"))
        for t in p.get("trades", []):
            if t.get("instrument") == s: allv += nums(t.get("gate")) + nums(t.get("tgt")) + nums(t.get("mindful"))
        for c in p.get("cautions", []):
            if c.get("instrument") == s: allv += nums(c.get("range")) + nums(c.get("zones"))
        if allv:
            lo, hi = RANGE[s]
            bad = [v for v in allv if not lo <= v <= hi]
            if bad: err.append(f"{s} prices out of range: {bad[:5]}")
            med = sorted(allv)[len(allv) // 2]
            far = [v for v in allv if abs(v - med) > SPAN[s]]
            if far: warn.append(f"{s} prices far from the median {med}: {far[:5]} (abbreviation resolved wrongly?)")

    ids = set()
    for t in p.get("trades", []):
        tid = t.get("id", "?")
        if tid in ids: err.append(f"duplicate id {tid}")
        ids.add(tid)
        for k in ("id", "instrument", "section", "source", "name", "dir", "kind", "gate", "tgt", "mindful", "condition", "quote", "stop_hint"):
            if k not in t: err.append(f"{tid}: missing {k}")
        if not str(tid).startswith("w" + str(t.get("instrument", "")).lower()): err.append(f"{tid}: id prefix must be w+instrument")
        if t.get("dir") not in ("long", "short"): err.append(f"{tid}: dir")
        if t.get("kind") not in ("fade", "break"): err.append(f"{tid}: kind")
        if t.get("source") not in ("commentary", "level_tag"): err.append(f"{tid}: source")
        if t.get("section") not in ("Trading Lower", "Trading Higher", "levels"): err.append(f"{tid}: section")
        g = t.get("gate")
        zone_ok(g, err, f"{tid} gate")
        for e in nums(g) and []: pass
        for e in (g or []):
            if isinstance(e, str) and e not in REFS: err.append(f"{tid}: unknown REF {e}")
        for e in t.get("tgt", []):
            for v in (e if isinstance(e, list) else [e]):
                if isinstance(v, str) and v not in REFS: err.append(f"{tid}: unknown REF in tgt {v}")
        verbatim(t.get("quote", ""), tid)
        if t.get("condition") and norm(t["condition"]) not in norm(t.get("quote", "")):
            warn.append(f"{tid}: condition is not part of the quote")
        gn = nums(g)
        tn = [min(nums(e)) if t.get("dir") == "long" else max(nums(e)) for e in t.get("tgt", []) if nums(e)]
        if gn and tn:
            ref = max(gn) if t.get("dir") == "long" else min(gn)
            wrong = [v for v in tn if (v <= ref if t.get("dir") == "long" else v >= ref)]
            if wrong: warn.append(f"{tid}: targets on the wrong side of the gate: {wrong}")
        if t.get("source") == "level_tag":
            tagd = {"short": "monitor for laaf", "long": "monitor for lbaf"}[t.get("dir", "long")] if t.get("dir") in ("long", "short") else ""
            if not any(l.get("zone") == g and l.get("tag") == tagd for l in p.get("levels", {}).get(t.get("instrument"), [])):
                err.append(f"{tid}: level_tag trade has no matching tagged list level")
    for i, c in enumerate(p.get("cautions", [])):
        if c.get("side") not in ("long", "short"): err.append(f"caution {i}: side")
        r = c.get("range")
        if not (isinstance(r, list) and len(r) == 2): err.append(f"caution {i}: range must be [lo|null, hi|null]")
        verbatim(c.get("quote", ""), f"caution {i}")
    return err, warn


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--letter"]
    letter = None
    if "--letter" in sys.argv:
        lf = sys.argv[sys.argv.index("--letter") + 1]
        letter = open(lf, encoding="utf-8").read()
        args.remove(lf)
    bad = 0
    for f in args:
        e, w = check(f, letter)
        print(f"{f}: {'OK' if not e else 'ERRORS'}" + (f" ({len(w)} warnings)" if w else ""))
        for x in e: print("  ERROR", x)
        for x in w: print("  warn ", x)
        bad += bool(e)
    sys.exit(1 if bad else 0)
