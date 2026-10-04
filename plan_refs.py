"""Resolve symbolic references in transcribed plans (RTH_HIGH, FRI_LOW, IB_LOW, ...) to prices from the bar files,
and adapt the transcribed schema to the trade dict backtest.run_trade() expects."""
import json, glob
import pandas as pd
import charts
tz = "America/New_York"
SKIP_DATES = {"2026-09-14"}   # letter in the Sep contract, bars already rolled to Dec


def _rth(d5, day):
    w = d5[(d5.time.dt.date == day)]
    m = w.time.dt.hour * 60 + w.time.dt.minute
    return w[(m >= 570) & (m < 960)]


def resolver(sym, plan_date, d5=None):
    """d5: bars to resolve from (default: the yfinance continuous file). Pass a single contract's bars
    (contracts.load(sym, contract)) so refs come from the same contract the letter quotes."""
    if d5 is None: d5 = charts.load(sym)
    pday = pd.Timestamp(plan_date, tz=tz)
    days = sorted(set(d5[d5.time < pday].time.dt.date))
    rth_days = [x for x in days if len(_rth(d5, x)) >= 60]   # real cash sessions only
    ref = rth_days[-1]; prev = rth_days[-2]
    R = _rth(d5, ref); P = _rth(d5, prev)
    ib = R[R.time.dt.hour * 60 + R.time.dt.minute < 630]
    or5 = R.iloc[:1]
    on_start = (pd.Timestamp(ref, tz=tz) - pd.Timedelta(days=1)).replace(hour=18)
    ON = d5[(d5.time >= on_start) & (d5.time < pd.Timestamp(ref, tz=tz).replace(hour=9, minute=30))]
    wk_start = pd.Timestamp(ref, tz=tz) - pd.Timedelta(days=pd.Timestamp(ref).weekday())
    W = d5[(d5.time >= wk_start.replace(hour=0)) & (d5.time < pday)]
    out = dict(RTH_HIGH=R.High.max(), RTH_LOW=R.Low.min(), PREV_RTH_HIGH=P.High.max(), PREV_RTH_LOW=P.Low.min(),
               IB_HIGH=ib.High.max(), IB_LOW=ib.Low.min(), OR5_HIGH=or5.High.max(), OR5_LOW=or5.Low.min(),
               ON_HIGH=ON.High.max(), ON_LOW=ON.Low.min(), WEEK_HIGH=W.High.max(), WEEK_LOW=W.Low.min())
    for wd, nm in enumerate(("MON", "TUE", "WED", "THU", "FRI")):
        cands = [x for x in rth_days if x.weekday() == wd]
        if cands:
            D = _rth(d5, cands[-1]); out[f"{nm}_HIGH"] = D.High.max(); out[f"{nm}_LOW"] = D.Low.min()
    return {k: float(v) for k, v in out.items() if v == v}


def _num(x, res):
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str): return res.get(x)
    if isinstance(x, (list, tuple)):
        v = [_num(e, res) for e in x]
        return None if any(e is None for e in v) else v
    return None


def load_plan(path, bars_for=None, skip=SKIP_DATES):
    """Return (plan, trades) with numeric levels in the old schema; unresolved trades are dropped (listed in plan['_dropped']).
    bars_for(sym) -> 5m bars of the contract this plan is on (default: continuous file); skip = plan dates to drop."""
    p = json.load(open(path)); trades, dropped = [], []
    if p.get("status") != "transcribed":
        for t in p["trades"]:
            t = dict(t); t.setdefault("kind", None); trades.append(t)
        p["_dropped"] = []; return p, trades
    if p["date"] in skip: p["_dropped"] = [t["id"] for t in p["trades"]]; return p, []
    res = {}
    for s in {t["instrument"] for t in p["trades"]}:
        try: res[s] = resolver(s, p["date"], bars_for(s) if bars_for else None)
        except IndexError: res[s] = {}          # no bars for that contract before the plan date: refs unresolvable
    for t in p["trades"]:
        r = res[t["instrument"]]
        gate = _num(t["gate"], r); tg = [_num(x, r) for x in t["tgt"]]; tg = [x for x in tg if x is not None]
        if gate is None or not tg: dropped.append(t["id"]); continue
        gate = sorted(gate)
        far = gate[0] if t["dir"] == "long" else gate[-1]
        trades.append(dict(id=t["id"], instrument=t["instrument"], name=t["name"], dir=t["dir"], tag=t.get("tag", ""),
                           kind=t.get("kind"), quote=t.get("quote", ""), stop=t.get("stop_hint", ""),
                           levels=dict(gate=gate, tgt=tg, stop=[far])))
    p["_dropped"] = dropped
    return p, trades


if __name__ == "__main__":
    n = 0
    for f in sorted(glob.glob("plans/plan-*.json")):
        p, tr = load_plan(f); n += len(tr)
        print(p["date"], len(tr), "trades", ("dropped " + ",".join(p["_dropped"])) if p["_dropped"] else "")
    print("total", n)
