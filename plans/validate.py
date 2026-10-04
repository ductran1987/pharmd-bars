"""Schema/sanity check for transcribed plans.  python plans/validate.py plans/plan-2026-09-14.json [...]
Checks the TRANSCRIBE.md schema, allowed REF strings, lo<=hi gates, price ranges per instrument, contract codes,
and that numeric levels sit within a plausible distance of each other (catches '49-52' resolved to the wrong hundred)."""
import json, sys, re

REFS = {"RTH_HIGH", "RTH_LOW", "IB_HIGH", "IB_LOW", "ON_HIGH", "ON_LOW", "PREV_RTH_HIGH", "PREV_RTH_LOW", "WEEK_HIGH",
        "WEEK_LOW", "APBL", "OR5_HIGH", "OR5_LOW"} | {f"{d}_{x}" for d in ("MON", "TUE", "WED", "THU", "FRI") for x in ("HIGH", "LOW")}
RANGE = {"ES": (4000, 9000), "NQ": (14000, 36000)}
SPAN = {"ES": 400, "NQ": 2500}      # max plausible distance of any level from the plan's median level
TAGRE = re.compile(r"^[ABC][+-]?(/[ABC][+-]?)?$")


def nums(x):
    if isinstance(x, (int, float)): return [float(x)]
    if isinstance(x, list): return [v for e in x for v in nums(e)]
    return []


def check(path):
    err, warn = [], []
    p = json.load(open(path))
    for k in ("source", "date", "status", "ref_date_note", "zones", "trades"):
        if k not in p: err.append(f"missing key {k}")
    if p.get("status") != "transcribed": err.append("status must be 'transcribed'")
    if not re.match(r"\d{4}-\d{2}-\d{2}$", p.get("date", "")): err.append("bad date")
    if not path.endswith(f"plan-{p.get('date')}.json"): err.append("file name does not match date")
    for s, c in (p.get("contract") or {}).items():
        if not re.match(rf"^{s}[HMUZ]\d$", c or ""): err.append(f"bad contract code {s}: {c}")
    ids = set()
    for s in ("ES", "NQ"):
        allv = [v for z in p.get("zones", {}).get(s, []) for v in nums(z)]
        for t in p.get("trades", []):
            if t.get("instrument") == s: allv += nums(t.get("gate")) + nums(t.get("tgt"))
        if allv:
            lo, hi = RANGE[s]
            bad = [v for v in allv if not lo <= v <= hi]
            if bad: err.append(f"{s} prices out of range: {bad[:5]}")
            med = sorted(allv)[len(allv) // 2]
            far = [v for v in allv if abs(v - med) > SPAN[s]]
            if far: warn.append(f"{s} levels far from the median {med}: {far[:5]} (abbreviation resolved wrongly?)")
        if any(t.get("instrument") == s for t in p.get("trades", [])) and s not in (p.get("contract") or {}):
            (err if "url" in p else warn).append(f"contract missing for {s}")   # required for Substack-era transcriptions
    for t in p.get("trades", []):
        tid = t.get("id", "?")
        if tid in ids: err.append(f"duplicate id {tid}")
        ids.add(tid)
        for k in ("id", "instrument", "name", "dir", "tag", "quote", "kind", "gate", "tgt", "stop_hint"):
            if k not in t: err.append(f"{tid}: missing {k}")
        if t.get("instrument") not in ("ES", "NQ"): err.append(f"{tid}: instrument")
        if not str(tid).startswith(str(t.get("instrument", "")).lower()): err.append(f"{tid}: id prefix")
        if t.get("dir") not in ("long", "short"): err.append(f"{tid}: dir")
        if t.get("kind") not in ("fade", "break"): err.append(f"{tid}: kind")
        if t.get("tag") and not TAGRE.match(t["tag"].split(" ")[0]): warn.append(f"{tid}: unusual tag '{t['tag']}'")
        g = t.get("gate")
        if not (isinstance(g, list) and len(g) == 2): err.append(f"{tid}: gate must be [lo, hi]")
        else:
            for e in g:
                if isinstance(e, str) and e not in REFS: err.append(f"{tid}: unknown REF {e}")
            if all(isinstance(e, (int, float)) for e in g) and g[0] > g[1]: err.append(f"{tid}: gate lo > hi")
        if not t.get("tgt"): warn.append(f"{tid}: no targets")
        for e in t.get("tgt", []):
            for v in (e if isinstance(e, list) else [e]):
                if isinstance(v, str) and v not in REFS: err.append(f"{tid}: unknown REF in tgt {v}")
            if isinstance(e, list) and (len(e) != 2 or (all(isinstance(v, (int, float)) for v in e) and e[0] > e[1])):
                err.append(f"{tid}: tgt range must be [lo, hi]")
        # targets should lie in the trade direction from the gate (numeric only)
        gn = nums(g) if isinstance(g, list) else []
        tn = [min(nums(e)) if t.get("dir") == "long" else max(nums(e)) for e in t.get("tgt", []) if nums(e)]
        if gn and tn:
            ref = max(gn) if t.get("dir") == "long" else min(gn)
            wrong = [v for v in tn if (v <= ref if t.get("dir") == "long" else v >= ref)]
            if wrong: warn.append(f"{tid}: targets on the wrong side of the gate: {wrong}")
    return err, warn


if __name__ == "__main__":
    bad = 0
    for f in sys.argv[1:]:
        e, w = check(f)
        print(f"{f}: {'OK' if not e else 'ERRORS'}" + (f" ({len(w)} warnings)" if w else ""))
        for x in e: print("   ERROR", x)
        for x in w: print("   warn ", x)
        bad += bool(e)
    sys.exit(1 if bad else 0)
