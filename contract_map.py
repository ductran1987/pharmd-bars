"""Per-plan-day contract map: which ES/NQ contract each letter's numbers are on, and whether bars exist for it.

python contract_map.py   -> writes plans/contract_map.json and prints a check table.

Source of the contract, in order:
  1. the plan file's "contract" field (transcriptions since the Oct 2026 addendum — read from the letter);
  2. for older transcriptions without the field (2026-08-31 .. 2026-10-02): the 2026 Sep->Dec roll as he wrote it —
     Sep contract through the 9/14 plan ("I will personally probably trade the ESU/NQU contracts on Monday"),
     Dec contract from the 9/15 plan ("moving to ESZ only").
Check: the plan's numeric gate levels are compared with the prior session's close in the mapped contract and in the
neighbouring quarterlies; a mapped contract that is much farther away than a neighbour is flagged (the roll basis is
~50-70 ES / ~300-400 NQ points, so a wrong contract stands out).
"""
import glob, json
import numpy as np, pandas as pd
import contracts

tz = "America/New_York"
MONTHS = "HMUZ"


def neighbours(c):
    """ESU6 -> [ESM6, ESZ6]"""
    root, m, y = c[:2], c[2], int(c[3])
    i = MONTHS.index(m)
    prev = (MONTHS[i - 1], y - (i == 0)); nxt = (MONTHS[(i + 1) % 4], y + (i == 3))
    return [f"{root}{prev[0]}{prev[1] % 10}", f"{root}{nxt[0]}{nxt[1] % 10}"]


def default_contract(sym, date):
    return f"{sym}U6" if date <= "2026-09-14" else f"{sym}Z6"


def plan_levels(p, sym):
    out = []
    for t in p.get("trades", []):
        if t.get("instrument") != sym: continue
        g = t.get("gate") if isinstance(t.get("gate"), list) else (t.get("levels") or {}).get("gate", [])
        out += [float(x) for x in g if isinstance(x, (int, float))]
    if not out:
        for z in (p.get("zones") or {}).get(sym, []):
            out += [float(x) for x in (z if isinstance(z, list) else [z]) if isinstance(x, (int, float))]
    return out


def inside_share(sym, c, date, levels, sessions=5):
    """Share of the plan's levels inside the contract's range over the last `sessions` cash sessions (+-1% pad)."""
    d = contracts.load(sym, c)
    r = contracts.rth(d[d.time < pd.Timestamp(date, tz=tz)])
    if not len(r): return None
    days = sorted(set(r.time.dt.date))[-sessions:]
    w = r[r.time.dt.date.isin(days)]
    lo, hi = w.Low.min() * 0.99, w.High.max() * 1.01
    return float(np.mean([lo <= x <= hi for x in levels]))


def has_session(sym, c, date, prior=1):
    """The plan day's cash session and at least `prior` earlier sessions (for refs) exist in this contract's bars."""
    cov = contracts.coverage(sym, c)
    day = pd.Timestamp(date).date()
    if day not in cov: return False
    lo = (pd.Timestamp(date) - pd.Timedelta(days=5)).date()
    return sum(1 for x in cov if lo <= x < day) >= prior


def build():
    out = {}
    for f in sorted(glob.glob("plans/plan-*.json")):
        p = json.load(open(f)); date = p["date"]
        if date > "2026-10-02": continue
        row = {}
        for sym in ("ES", "NQ"):
            c = (p.get("contract") or {}).get(sym)
            src = "letter" if c else "default"
            c = contracts.norm(c) if c else default_contract(sym, date)
            lv = plan_levels(p, sym)
            chk = ""
            if lv:
                sh = inside_share(sym, c, date, lv)
                alts = {a: inside_share(sym, a, date, lv) for a in neighbours(c)}
                if sh is not None:
                    better = [f"{a} {v:.0%}" for a, v in alts.items() if v is not None and v > sh + 0.3]
                    chk = f"{sh:.0%} of {len(lv)} gate levels inside the last 5 sessions' range" + (f"  ** fits better: {better}" if better else "")
                else:
                    chk = "no bars for mapped contract before this date"
            row[sym] = dict(contract=c, source=src, bars=has_session(sym, c, date), check=chk)
        row["both"] = row["ES"]["bars"] and row["NQ"]["bars"]
        out[date] = row
    return out


if __name__ == "__main__":
    m = build()
    json.dump(m, open("plans/contract_map.json", "w"), indent=1)
    flagged = 0
    for d, r in m.items():
        line = f"{d}  ES {r['ES']['contract']:5} {'bars' if r['ES']['bars'] else 'NO BARS':7}  NQ {r['NQ']['contract']:5} {'bars' if r['NQ']['bars'] else 'NO BARS':7}  {'BOTH' if r['both'] else '-'}"
        warn = [f"{s}: {r[s]['check']}" for s in ("ES", "NQ") if "**" in r[s]["check"]]
        flagged += bool(warn)
        print(line + ("   " + " | ".join(warn) if warn else ""))
    print(f"\n{len(m)} plan days, {sum(r['both'] for r in m.values())} with bars for both ES and NQ, {flagged} flagged")
