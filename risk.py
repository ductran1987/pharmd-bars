"""Fill the per-trade risk block (stop = edge -/+ 1.5*ATR5, BE = entry +/- 1R, R per target,
target pick = first >= 1.5R else last, micros for $500/$1000) into a plan JSON.

Usage: python risk.py plans/plan-YYYY-MM-DD.json [es_edge_overrides as id=price ...]
Entry edge defaults to the near edge of the gate (long: top, short: bottom).
"""
import json, sys, numpy as np, pandas as pd, charts

PT = {"ES": 5, "NQ": 2}; MIC = {"ES": "MES", "NQ": "MNQ"}; TICK = 0.25


def atr5(sym, plan_date, sessions=3):
    d = charts.load(sym).set_index("time")
    pd_ = pd.Timestamp(plan_date, tz="America/New_York")
    days = sorted({t.date() for t in d.index if t < pd_ and t.weekday() < 5})[-sessions:]
    r = d[[t.date() in days for t in d.index]]
    r = r[(r.index.time >= pd.Timestamp("09:30").time()) & (r.index.time < pd.Timestamp("16:00").time())]
    tr = np.maximum(r.High - r.Low, np.maximum((r.High - r.Close.shift()).abs(), (r.Low - r.Close.shift()).abs()))
    return float(tr.rolling(14).mean().iloc[-1])


def fill(plan, overrides=None):
    overrides = overrides or {}
    atr = {s: atr5(s, plan["date"]) for s in ("ES", "NQ")}
    floor = {s: round(1.5 * a / TICK) * TICK for s, a in atr.items()}
    plan["atr5"] = {s: round(a, 2) for s, a in atr.items()}
    plan["stop_floor"] = floor
    for t in plan["trades"]:
        sym = t["instrument"]; lv = t["levels"]; lng = t["dir"] == "long"
        e = overrides.get(t["id"], max(lv["gate"]) if lng else min(lv["gate"]))
        f = floor[sym]
        stop = e - f if lng else e + f
        be = e + f if lng else e - f
        lv["stop"] = [stop]; lv["be"] = [be]
        his = abs(lv["invalid"][0] - e) if lv.get("invalid") else None
        tg = []
        for g in lv["tgt"]:
            p = (min(g) if lng else max(g)) if isinstance(g, list) else g
            lab = f"{g[0]:g}-{g[1]:g}" if isinstance(g, list) else f"{g:g}"
            tg.append({"p": lab, "ours": f"{abs(p - e) / f:.1f}", "his": f"{abs(p - e) / his:.1f}" if his else "—"})
        rs = [float(g["ours"]) for g in tg]
        pick = next((i for i, x in enumerate(rs) if x >= 1.5), len(rs) - 1)
        c = lambda pts, r: f"{r / (pts * PT[sym]):.1f}"
        t["risk"] = {"entry": f"{e:g}", "stop": f"{stop:g}", "stop_pts": f"{f:g}", "be": f"{be:g}",
                     "his": f"{lv['invalid'][0]:g}" if his else "—", "his_pts": f"{his:g}" if his else "—",
                     "mic": MIC[sym], "ours": [c(f, 500), c(f, 1000)],
                     "his_n": [c(his, 500), c(his, 1000)] if his else ["—", "—"],
                     "tgts": tg, "pick": pick, "skip": rs[pick] < 1}
    return plan


if __name__ == "__main__":
    path = sys.argv[1]
    ov = {k: float(v) for k, v in (a.split("=") for a in sys.argv[2:])}
    plan = fill(json.load(open(path)), ov)
    json.dump(plan, open(path, "w"), indent=1, ensure_ascii=False)
    print("ATR5", plan["atr5"], "floor", plan["stop_floor"])
    for t in plan["trades"]:
        r = t["risk"]; print(t["id"], r["entry"], "stop", r["stop"], "BE", r["be"], "pick", r["pick"] + 1, [g["ours"] for g in r["tgts"]], "skip" if r["skip"] else "")
