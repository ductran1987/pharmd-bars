"""Grid backtest of trade-management variants over every transcribed PharmD plan with per-contract bars.

    python backtest_grid.py            -> backtest_grid.csv, backtest_grid_trades.csv, backtest_grid_summary.md (+ printed)

Data
  * plans/plan-*.json up to 2026-10-02, symbolic refs resolved by plan_refs from the SAME contract's bars.
  * plans/contract_map.json (contract_map.py): the contract each letter is on; only days with bars for BOTH ES and NQ
    are used ("the time frame we have of both").  Bars: contracts.load(sym, contract) — never spliced across a roll.
  * ATR5/ATR15 = stops.atr() on that contract (ATR(14) on RTH 5m/15m bars, last 3 sessions, mean of the last 40
    values, data through the prior close).  If the plan's contract doesn't yet have 3 prior sessions (first days after
    a roll), ATR comes from the previous contract alone (a range measure; levels are never mixed).

Baseline (the rule set from the Oct 3 stop-placement chat)
  entry  backtest.run_trade(): fade = first 5m close back through the near edge after price trades into the zone,
         break = first 5m close through the far side; fill at the edge.  Sweep extreme = furthest price between first
         touch and the entry close.
  stop   1 tick past the sweep extreme, never closer than 1.5 x ATR5 to the entry; min risk 0.2 x ATR15.
  BE     at +1R, stop to entry + 1 tick (from the next bar).
  exit   first listed target >= 1.5R (last target if none); else flat at the 16:00 close.  No partials.
  size   $500 / ((risk + 0.5) x $/pt) micros (MES $5, MNQ $2), $2.60 commission per micro round trip.
  slip   2 ticks (0.5 pt) on entry and 2 ticks on stop / BE exits; targets are limit orders (no slip).
  Within a bar the stop is checked before the target (conservative).  Targets on the wrong side of the entry are ignored.
  Graded = tag starting with A/B/C ("implied - not graded" is ungraded).

Corrections applied to every run (not in the original 24-day backtest):
  * a plan can only trade after its letter was published (plans/post_times.json, Substack post time; about half the
    letters go out after 18:00 ET, when the old session window already started);
  * the bar labelled 16:00 (16:00-16:05) is excluded, so "flat at 16:00" is the 15:55 bar's close;
  * break trades whose session opened entirely beyond the zone are dropped (run_trade would enter at an untraded price);
  * a stop in a bar that opens through it fills at the open; after breakeven a bar hitting both BE stop and target
    counts as the stop; drawdown is measured from starting equity.
Fill realism: the specified edge fill is NOT executable (the signal is a 5m close beyond the edge, so that price is gone).
The report re-runs everything with three executable fills: market at the confirming close, a limit back at the edge
(retest), and a resting stop order one tick through the edge (no close confirmation; fills at the open on gaps).

Legacy check: `legacy=True` reproduces backtest_pnl.py exactly on the original 24 plan days (continuous bars, slip once,
wrong-side targets not filtered, any non-empty tag counts as graded) -> must print $16,892.71.
"""
import glob, json, re, math, sys
import numpy as np, pandas as pd
import charts, stops, backtest, plan_refs, contracts, contract_map

tz = "America/New_York"
TICK = 0.25; RISK = 500.0; MICRO = {"ES": 5.0, "NQ": 2.0}; SLIP = 0.5; COMM = 2.6
LAST_DATE = "2026-10-02"
LEGACY_DATES = ("2026-08-31", "2026-10-05")     # the 24 plan days backtest_pnl.py ran on

STOPS = ([("tick", None)] + [("floor", k) for k in (0.5, 1.0, 1.25, 1.5, 2.0, 2.5)] +
         [("atr15", m) for m in (0.75, 1.0, 1.5)] + [("proxy", None)])
BES = [None, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
TGTS = ["t1", "t1|t2", "t2", "ge1.0", "ge1.5", "ge2.0", "ge2.5"]
PARTIALS = [None, 1.0, 1.5]
BASE = dict(stop=("floor", 1.5), be=1.0, tgt="ge1.5", partial=None, atr="prior")


def grade(tag):
    m = re.match(r"\s*\(?([ABCabc])(?![a-z])", tag or "")
    return m.group(1).upper() if m else ""


def name_stop(s):
    k, v = s
    return {"tick": "tick past extreme", "floor": f"floor {v}xATR5", "atr15": f"entry-{v}xATR15", "proxy": "his level proxy"}[k]


def cell_name(stop, be, tgt, partial, atr="prior"):
    s = f"{name_stop(stop)} | BE {'none' if be is None else f'{be}R'} | tgt {tgt}"
    if partial: s += f" | half@{partial}R+BE"
    if atr != "prior": s += f" | {atr} ATR5"
    return s


# ---------------------------------------------------------------- setups
def plan_zones(p, sym):
    out = []
    for z in (p.get("zones") or {}).get(sym, []):
        v = [float(x) for x in (z if isinstance(z, list) else [z]) if isinstance(x, (int, float))]
        if v: out.append((min(v), max(v)))
    for b in p.get("brief", []) or []:
        if b.get("instrument") == sym:
            for lv in b.get("levels", []):
                v = [float(x) for x in lv.get("p", []) if isinstance(x, (int, float))]
                if v: out.append((min(v), max(v)))
    return out


def full_sessions_before(sym, c, date, days=7):
    cov = contracts.coverage(sym, c); day = pd.Timestamp(date).date()
    lo = (pd.Timestamp(date) - pd.Timedelta(days=days)).date()
    return sum(1 for x in cov if lo <= x < day)


def atr_for(sym, c, date):
    """ATR5/ATR15 at the prior close from ONE contract: the plan's contract if it has 3 cash sessions in the 5 days
    before the plan date (stops.atr's window), else the previous contract if it does (first days after a roll)."""
    end = pd.Timestamp(date, tz=tz) - pd.Timedelta(hours=7)          # 17:00 the day before (same as stops.analyze)
    prev = contract_map.neighbours(c)[0]
    n_c, n_p = full_sessions_before(sym, c, date, 5), full_sessions_before(sym, prev, date, 5)
    cc = c if (n_c >= 3 or n_c >= n_p) else prev
    if max(n_c, n_p) == 0: return None
    a5, a15 = stops.atr(contracts.load(sym, cc), end=end)
    return (a5, a15, cc) if a5 == a5 else None


def run_trade_stop(bars, pt, kind):
    """Executable version of the edge fill: a resting stop order one tick through the edge, armed once price has traded
    into the zone (no close confirmation).  Fade long: armed when a bar trades at/below the zone top; fills on the first
    LATER bar trading >= top + 1 tick.  Break long: armed when price reaches the zone; fills >= zone top + 1 tick.
    Shorts mirrored.  Sweep extreme = extreme from the arming bar through the bar before the fill (break: zone far side).
    Returns dict(e, far, j) or None; e is the fill price (edge +/- 1 tick, or the bar's open if it gapped through)."""
    d = pt["dir"]; gate = sorted(pt["levels"]["gate"]); H, Lo = bars.High.values, bars.Low.values
    up = d == "long"
    if kind == "fade":
        edge = gate[-1] if up else gate[0]
        armed = np.flatnonzero(Lo <= edge) if up else np.flatnonzero(H >= edge)
    else:   # break: price must have been on the near side of the far edge (long: low <= zone top)
        edge = gate[-1] if up else gate[0]
        armed = np.flatnonzero(Lo <= gate[-1]) if up else np.flatnonzero(H >= gate[0])
    if not len(armed): return None
    i_t = armed[0]
    fill = np.flatnonzero(H[i_t + 1:] >= edge + TICK) if up else np.flatnonzero(Lo[i_t + 1:] <= edge - TICK)
    if not len(fill): return None
    j = i_t + 1 + fill[0]
    if kind == "fade": far = Lo[i_t:j].min() if up else H[i_t:j].max()
    else: far = gate[0] if up else gate[-1]
    O = bars.Open.values
    px = max(edge + TICK, O[j]) if up else min(edge - TICK, O[j])   # a bar that opens through the stop price fills at its open
    return dict(e=float(px), far=float(far), j=int(j))


POST_TIMES = json.load(open("plans/post_times.json")) if __import__("os").path.exists("plans/post_times.json") else {}


def _tg(pt):
    d = pt["dir"]
    return [(min(x) if d == "long" else max(x)) if isinstance(x, (list, tuple)) else x for x in pt["levels"]["tgt"]]


def _break_armed_ok(bars, pt, i0):
    """Break trades: price must actually have been on the near side of the zone's far edge at or before the entry
    bar (long: some low <= zone top; short: some high >= zone bottom).  run_trade's 'price has been at the zone'
    test also fires when the session opens entirely beyond the zone, which books an entry at a price that never traded."""
    g = sorted(pt["levels"]["gate"])
    if pt["dir"] == "long": return bool((bars.Low.values[:i0 + 1] <= g[-1]).any())
    return bool((bars.High.values[:i0 + 1] >= g[0]).any())


def build_setups(legacy=False, variants=("post", "free")):
    """Triggered trades per variant.  'post': session bars start at the letter's publish time (plans/post_times.json)
    if that is after 18:00 the evening before — nothing can be traded before the plan exists.  'free': the old
    18:00 session start.  Both end at 15:55 (the 16:00-labelled bar is 16:00-16:05, after the cash close).
    legacy=True: backtest_pnl.py conventions exactly (continuous bars, 18:00-16:00 incl. the 16:00 bar)."""
    files = sorted(glob.glob("plans/plan-*.json"))
    cmap = None if legacy else contract_map.build()
    cont = {s: charts.load(s) for s in ("ES", "NQ")} if legacy else None
    if legacy: variants = ("legacy",)
    out = {v: [] for v in variants}
    info = dict(trades=0, triggered=0, untriggered=0, unresolved=0, days=0, skipped_days=0, phantom_break=0, pre_publication=0)
    for f in files:
        date = json.load(open(f))["date"]
        if legacy:
            if not (LEGACY_DATES[0] <= date <= LEGACY_DATES[1]): continue
            p, trades = plan_refs.load_plan(f)
        else:
            if date > LAST_DATE or date not in cmap: continue
            if not cmap[date]["both"]: info["skipped_days"] += 1; continue
            C = {s: cmap[date][s]["contract"] for s in ("ES", "NQ")}
            p, trades = plan_refs.load_plan(f, bars_for=lambda s: contracts.load(s, C[s]), skip=set())
        info["days"] += 1; info["unresolved"] += len(p["_dropped"])
        post = pd.Timestamp(POST_TIMES[date]["posted_et"], tz=tz) if (not legacy and date in POST_TIMES) else None
        cache = {}
        for pt in trades:
            s = pt["instrument"]; info["trades"] += 1
            if s not in cache:
                if legacy:
                    d5 = cont[s]; a = stops.atr(d5, end=pd.Timestamp(date, tz=tz) - pd.Timedelta(hours=7)); ac = "continuous"
                    cache[s] = (d5, {"legacy": backtest.session(d5, date)}, a, ac)
                else:
                    d5 = contracts.load(s, C[s]); r = atr_for(s, C[s], date)
                    if r is None: cache[s] = None
                    else:
                        full = backtest.session(d5, date)
                        full = full[full.time < pd.Timestamp(date, tz=tz).replace(hour=16)].reset_index(drop=True)
                        sess = {"free": full}
                        sess["post"] = full[full.time >= post].reset_index(drop=True) if post is not None else full
                        cache[s] = (d5, sess, r[:2], r[2])
            if cache[s] is None: info["unresolved"] += 1; continue
            d5, sess, (a5, a15), atr_src = cache[s]
            tag = pt.get("tag", "") or ""; d = pt["dir"]
            base = dict(date=date, id=pt["id"], sym=s, dir=d, tag=tag,
                        grade=("X" if tag else "") if legacy else grade(tag), graded=bool(tag) if legacy else bool(grade(tag)),
                        gate=sorted(pt["levels"]["gate"]), tg=_tg(pt), zones=plan_zones(p, s), atr5=a5, atr15=a15,
                        atr_src=atr_src, contract="cont" if legacy else C[s])
            trig_any = False
            for v in variants:
                bars = sess[v]
                if len(bars) == 0: continue
                try: r = backtest.run_trade(bars, pt)
                except ValueError:      # entry on the session's last bar (run_trade's long branch can't compute MFE): nothing to trade
                    r = dict(triggered=False, kind=pt.get("kind"))
                kind = r.get("kind") or pt.get("kind") or "fade"
                ok = r["triggered"]
                if ok and not legacy:
                    i0 = int(bars.index[bars.time == pd.Timestamp(r["entry_time"])][0])
                    if kind == "break" and not _break_armed_ok(bars, pt, i0):
                        ok = False
                        if v == "post": info["phantom_break"] += 1
                se = None
                if not legacy:
                    rs = run_trade_stop(bars, pt, kind)
                    if rs is not None:
                        jj = rs["j"]; Hs = bars.High.values[jj:].astype(float).copy(); Ls = bars.Low.values[jj:].astype(float).copy()
                        Os = bars.Open.values[jj:].astype(float).copy(); Os[0] = rs["e"]
                        if d == "long": Hs[0] = rs["e"]       # fill bar: no target credit; its extreme still counts against the stop
                        else: Ls[0] = rs["e"]
                        se = dict(e=rs["e"], far=rs["far"], entry_time=str(bars.time[jj]), H=Hs, L=Ls, O=Os, C=bars.Close.values[jj:].astype(float))
                if not ok:
                    if se is None: continue
                    out[v].append(dict(base, kind=kind, close_trig=False, e=se["e"], eclose=se["e"], far=se["far"], live5=a5,
                                       entry_time=se["entry_time"], H=np.array([]), L=np.array([]), O=np.array([]), C=np.array([]), se=se))
                    continue
                trig_any = True
                if legacy: i0 = int(bars.index[bars.time == pd.Timestamp(r["entry_time"])][0])
                after = bars.loc[i0 + 1:]
                hist = d5[d5.time <= pd.Timestamp(r["entry_time"])].tail(15)   # live ATR5: 14 bars up to the entry bar
                tr = np.maximum(hist.High - hist.Low, np.maximum((hist.High - hist.Close.shift()).abs(), (hist.Low - hist.Close.shift()).abs()))
                out[v].append(dict(base, kind=r["kind"], close_trig=True, e=r["entry"], eclose=float(bars.Close[i0]), far=r["far"],
                                   live5=float(tr.iloc[1:].mean()), entry_time=r["entry_time"], se=se,
                                   H=after.High.values.astype(float), L=after.Low.values.astype(float),
                                   O=after.Open.values.astype(float), C=after.Close.values.astype(float)))
            if not legacy and "post" in variants and "free" in variants:
                fr = [t for t in out["free"] if t["date"] == date and t["id"] == pt["id"] and t["close_trig"]]
                po = [t for t in out["post"] if t["date"] == date and t["id"] == pt["id"] and t["close_trig"]]
                if fr and (not po or po[0]["entry_time"] != fr[0]["entry_time"]): info["pre_publication"] += 1
            info["triggered" if trig_any else "untriggered"] += 1
    for v in out: out[v].sort(key=lambda t: (t["date"], t["entry_time"]))
    return (out["legacy"], info) if legacy else (out, info)


# ---------------------------------------------------------------- stops / targets / simulation
def stop_for(t, rule, atr="prior", fill="edge"):
    """Returns (stop price, risk pts, at_floor, proxy_fallback).  Stop rules are defined from the zone edge; with
    fill='close' the trade is filled at the confirming bar's close and risk is measured from there."""
    k, v = rule; a5 = t["live5"] if atr == "live" else t["atr5"]; a15 = t["atr15"]
    adv = -1 if t["dir"] == "long" else 1; e = t["e"]
    ef = t["eclose"] if fill == "close" else e
    tick = t["far"] + adv * TICK
    far_of = (min if adv < 0 else max)
    fb = False
    if k == "tick": stp = tick
    elif k == "floor": stp = far_of(tick, e + adv * v * a5)
    elif k == "atr15": stp = e + adv * v * a15
    else:   # far edge of the next zone beyond the gate on the adverse side, + 0.1 ATR5; never inside the sweep
        g0, g1 = min(t["gate"]), max(t["gate"])
        if adv < 0: cand = [z for z in t["zones"] if z[1] < g0 - 1e-9]; z = max(cand, key=lambda z: z[1]) if cand else None
        else: cand = [z for z in t["zones"] if z[0] > g1 + 1e-9]; z = min(cand, key=lambda z: z[0]) if cand else None
        if z is None: stp = far_of(tick, e + adv * 1.5 * a5); fb = True
        else: stp = far_of(tick, (z[0] if adv < 0 else z[1]) + adv * 0.1 * a5)
    rk = abs(ef - stp); floor = False
    if rk < 0.2 * a15: rk = 0.2 * a15; stp = ef + adv * rk; floor = True
    return stp, rk, floor, fb


def pick_target(tg, e, rk, up, rule, legacy=False):
    sg = 1 if up else -1
    if not legacy: tg = [x for x in tg if (x - e) * sg > 0]
    if not tg: return None
    R = [abs(x - e) / rk for x in tg]
    if rule == "t1": return tg[0]
    if rule == "t1|t2": return tg[0] if (R[0] >= 1 or len(tg) < 2) else tg[1]
    if rule == "t2": return tg[1] if len(tg) > 1 else tg[0]
    x = float(rule[2:])
    return next((p for p, r in zip(tg, R) if r >= x), tg[-1])


def _first(mask, start=0):
    idx = np.flatnonzero(mask[start:])
    return start + idx[0] if len(idx) else 10 ** 9


def simulate_one(t, stp, rk, n, tgt, be, partial, legacy=False):
    """Exit of one trade -> (pnl $, exit type, pts on the main leg).  Bars are those after the entry bar (or, for
    retest / stop-entry fills, starting with the fill bar).  Within a bar the stop is checked before the target.
    A stop (or BE stop) in a bar that OPENS through it fills at the open (not in legacy mode)."""
    up = t["dir"] == "long"; sg = 1 if up else -1; e = t["e"]
    H, L, C = t["H"], t["L"], t["C"]
    if len(C) == 0:
        pts = -SLIP; return pts * MICRO[t["sym"]] * n - COMM * n, "close", pts
    fav = (H - e) * sg if up else (e - L)
    adv = (L - e) * sg if up else (e - H)
    O = t.get("O"); opx = None if (legacy or O is None or len(O) != len(C)) else (O - e) * sg
    T = (tgt - e) * sg if tgt is not None else None
    if legacy and T is not None and T <= 0: T_hit = np.ones(len(C), bool)       # backtest_pnl: wrong-side target fills at once
    else: T_hit = fav >= T if T is not None else np.zeros(len(C), bool)
    s0 = adv <= -rk
    ent_slip = SLIP; stop_slip = 0.0 if legacy else SLIP
    i_s = _first(s0); i_t = _first(T_hit)
    trig_R = partial if partial else be
    i_b = _first(fav >= trig_R * rk) if trig_R is not None else 10 ** 9
    k1 = int(n // 2) if partial else 0          # 1 micro can't be halved: it just gets the breakeven at the partial level
    if trig_R is None or i_b >= min(i_s, i_t):
        if i_s <= i_t and i_s < 10 ** 9:
            pts, how = (-rk if opx is None else min(-rk, opx[i_s])) - stop_slip, "stop"
        elif i_t < 10 ** 9: pts, how = abs(T), "target"
        else: pts, how = (C[-1] - e) * sg, "close"
        pts -= ent_slip
        return pts * MICRO[t["sym"]] * n - COMM * n, how, pts
    # trigger hit at bar i_b, before stop and target: move stop to entry + 1 tick from the next bar (and bank half if partial)
    s1 = adv <= TICK
    j_s = _first(s1, i_b + 1); j_t = i_t
    if j_s <= j_t and j_s < 10 ** 9:            # same bar hits the BE stop and the target: the stop wins (conservative)
        pts, how = (TICK if opx is None else min(TICK, opx[j_s])) - stop_slip, "be"
    elif j_t < 10 ** 9: pts, how = abs(T), "target"
    else: pts, how = (C[-1] - e) * sg, "close"
    pts -= ent_slip
    if partial and k1 > 0:
        part_pts = partial * rk - ent_slip
        pnl = (part_pts * k1 + pts * (n - k1)) * MICRO[t["sym"]] - COMM * n
        return pnl, how + "+half", pts
    return pts * MICRO[t["sym"]] * n - COMM * n, how, pts


def run_cell(setups, stop, be, tgt, partial=None, atr="prior", legacy=False, fill="edge"):
    rows = []
    for t in setups:
        if fill in ("stop_entry", "stop_entry_opt"):
            if t.get("se") is None: continue
            se = t["se"]; far, H, L = se["far"], se["H"], se["L"]
            if fill == "stop_entry_opt":   # optimistic intrabar order: the fill bar's adverse extreme came BEFORE the fill
                up = t["dir"] == "long"; H, L = H.copy(), L.copy()
                if t["kind"] == "fade": far = min(far, L[0]) if up else max(far, H[0])
                if up: L[0] = se["e"]
                else: H[0] = se["e"]
            t = dict(t, e=se["e"], far=far, H=H, L=L, O=se["O"], C=se["C"], entry_time=se["entry_time"])
        elif not t.get("close_trig", True): continue
        if fill == "retest":
            # limit order at the zone edge placed after the confirming close; fills only if price comes back to the edge
            up = t["dir"] == "long"
            hit = np.flatnonzero(t["L"] <= t["e"]) if up else np.flatnonzero(t["H"] >= t["e"])
            if not len(hit): continue
            j = hit[0]; H, L, O = t["H"][j:].copy(), t["L"][j:].copy(), t["O"][j:].copy()
            if up: H[0] = t["e"]          # no target credit in the fill bar; its low still counts against the stop
            else: L[0] = t["e"]
            O[0] = t["e"]
            t = dict(t, H=H, L=L, O=O, C=t["C"][j:])
        stp, rk, floor, fb = stop_for(t, stop, atr, "close" if fill == "close" else "edge")
        if fill == "close": t = dict(t, e=t["eclose"])
        n = int(RISK // ((rk + SLIP) * MICRO[t["sym"]]))
        if n < 1: continue
        tp = pick_target(t["tg"], t["e"], rk, t["dir"] == "long", tgt, legacy)
        pnl, how, pts = simulate_one(t, stp, rk, n, tp, be, partial, legacy)
        rows.append(dict(date=t["date"], entry_time=t["entry_time"], id=t["id"], sym=t["sym"], dir=t["dir"], kind=t["kind"],
                         grade=t["grade"], tag=t["tag"], contract=t["contract"], entry=t["e"], sweep=t["far"], stop=stp,
                         risk_pts=rk, risk_atr15=rk / t["atr15"], at_floor=floor, proxy_fallback=fb, micros=n, target=tp,
                         R_to_target=(abs(tp - t["e"]) / rk) if tp is not None else np.nan, exit=how, pts=pts, pnl=pnl,
                         R=pnl / RISK, depth_atr5=abs(t["e"] - t["far"]) / t["atr5"], atr5=t["atr5"], atr15=t["atr15"]))
    return pd.DataFrame(rows)


def metrics(d, sort=True, dd_from_zero=True):
    if len(d) == 0: return dict(n=0)
    if sort: d = d.sort_values(["date", "entry_time"])
    cum = d.pnl.cumsum()
    peak = np.maximum(cum.cummax(), 0) if dd_from_zero else cum.cummax()   # drawdown measured from starting equity too
    w = d[d.pnl > 0].pnl.sum(); l = -d[d.pnl < 0].pnl.sum()
    top3 = d.pnl.nlargest(3).sum()
    return dict(n=len(d), win=(d.pnl > 0).mean(), avgR_cap3=d.R.clip(upper=3).mean(), avgR=d.R.mean(), medR=d.R.median(),
                total=d.pnl.sum(), max_dd=min(0.0, (cum - peak).min()), pf=w / l if l > 0 else np.inf,
                es=d[d.sym == "ES"].pnl.sum(), nq=d[d.sym == "NQ"].pnl.sum(), n_es=int((d.sym == "ES").sum()),
                n_nq=int((d.sym == "NQ").sum()), pct_floor=d.at_floor.mean(), worst=d.pnl.min(), total_ex_top3=d.pnl.sum() - top3)


# ---------------------------------------------------------------- report
def fmt(m, cols=("n", "win", "avgR_cap3", "avgR", "medR", "total", "max_dd", "pf", "es", "nq", "pct_floor")):
    if not m or m.get("n", 0) == 0: return "n=0"
    f = {"n": "{:.0f}", "win": "{:.0%}", "avgR_cap3": "{:+.2f}", "avgR": "{:+.2f}", "medR": "{:+.2f}", "total": "${:,.0f}",
         "max_dd": "${:,.0f}", "pf": "{:.2f}", "es": "${:,.0f}", "nq": "${:,.0f}", "pct_floor": "{:.0%}"}
    return " · ".join(f"{c} " + f[c].format(m[c]) for c in cols)


def md_table(rows, cols):
    h = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    return h + "\n".join("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows) + "\n"


def mrow(label, m):
    if not m or m.get("n", 0) == 0: return dict(cell=label, n=0)
    return dict(cell=label, n=m["n"], win=f"{m['win']:.0%}", avgR3=f"{m['avgR_cap3']:+.2f}", avgR=f"{m['avgR']:+.2f}",
                medR=f"{m['medR']:+.2f}", total=f"${m['total']:,.0f}", maxDD=f"${m['max_dd']:,.0f}", PF=f"{m['pf']:.2f}",
                ES=f"${m['es']:,.0f}", NQ=f"${m['nq']:,.0f}", floor=f"{m['pct_floor']:.0%}")


COLS = ["cell", "n", "win", "avgR3", "avgR", "medR", "total", "maxDD", "PF", "ES", "NQ", "floor"]


def main():
    out = []
    P = lambda *a: (print(*a), out.append(" ".join(str(x) for x in a)))

    # 1. reproduction check
    L, Linfo = build_setups(legacy=True)
    Lg = [t for t in L if t["graded"]]
    Lg.sort(key=lambda t: (t["date"], t["id"][:2] != "es", int(re.sub(r"\D", "", t["id"]) or 0)))   # plan-file order, as backtest_pnl
    leg = run_cell(Lg, ("floor", 1.5), 1.0, "ge1.5", legacy=True)
    P("# PharmD management grid\n")
    P(f"**Reproduction check** (backtest_pnl.py conventions, original 24 plan days, continuous bars): "
      f"{len(leg)} trades, total ${leg.pnl.sum():,.2f}, PF {metrics(leg)['pf']:.2f}, max DD ${metrics(leg, sort=False, dd_from_zero=False)['max_dd']:,.0f} "
      f"(expected $16,892.71 / 2.45 / -$1,896).\n")

    # 2. setups on per-contract bars
    SS, info = build_setups()
    S = SS["post"]; Sfree = SS["free"]
    G = [t for t in S if t["graded"]]; U = [t for t in S if not t["graded"]]
    Gc = [t for t in G if t["close_trig"]]
    # split so each half holds ~half the graded triggered trades
    cnt = pd.Series([t["date"] for t in Gc]).value_counts().sort_index().cumsum()
    split = cnt.index[np.searchsorted(cnt.values, len(Gc) / 2)]
    H1 = [t for t in Gc if t["date"] <= split]; H2 = [t for t in Gc if t["date"] > split]
    P(f"**Data**: {info['days']} plan days with bars for both ES and NQ ({info['skipped_days']} letter days skipped for lack of one "
      f"instrument's contract bars), {info['trades']} resolved trades ({info['unresolved']} dropped: unresolvable refs / no bars), "
      f"{len([t for t in S if t['close_trig']])} triggered on a 5m close after the letter was published, of which {len(Gc)} graded. "
      f"Range {S[0]['date']} -> {S[-1]['date']}. Corrections vs. the original backtest: sessions start at the letter's publish time "
      f"when that is after 18:00 ({info['pre_publication']} trades had triggered before their letter existed); the 16:00-16:05 bar is "
      f"excluded; {info['phantom_break']} break trades whose session opened entirely beyond the zone (entry at a price that never traded) are dropped.")
    P(f"**Halves** (by time, equal graded-trade counts): H1 = {G[0]['date']} -> {split} ({len(H1)} trades), "
      f"H2 = after {split} -> {Gc[-1]['date']} ({len(H2)} trades).\n")

    # 3. full grid
    cells = [(s, b, tg, None) for s in STOPS for b in BES for tg in TGTS] + [(s, None, tg, p) for s in STOPS for p in PARTIALS[1:] for tg in TGTS]
    rows = []; per = {}
    for i, (s, b, tg, p) in enumerate(cells):
        d = run_cell(G, s, b, tg, p)
        if len(d) == 0: continue
        name = cell_name(s, b, tg, p)
        per[name] = d
        for lab, sub in (("all", d), ("H1", d[d.date <= split]), ("H2", d[d.date > split])):
            m = metrics(sub); m.update(cell=name, period=lab, stop=name_stop(s), be=b, tgt=tg, partial=p, atr="prior")
            rows.append(m)
    # live-ATR5 runs: baseline + the ATR5-floor cells with the baseline management
    for s in [x for x in STOPS if x[0] == "floor"]:
        d = run_cell(G, s, 1.0, "ge1.5", None, atr="live"); name = cell_name(s, 1.0, "ge1.5", None, "live"); per[name] = d
        for lab, sub in (("all", d), ("H1", d[d.date <= split]), ("H2", d[d.date > split])):
            m = metrics(sub); m.update(cell=name, period=lab, stop=name_stop(s), be=1.0, tgt="ge1.5", partial=None, atr="live"); rows.append(m)
    grid = pd.DataFrame(rows)
    grid.to_csv("backtest_grid.csv", index=False)

    base = cell_name(BASE["stop"], BASE["be"], BASE["tgt"], None)
    bd = per[base]; bd.to_csv("backtest_grid_trades.csv", index=False)
    gb = lambda lab: grid[(grid.cell == base) & (grid.period == lab)].iloc[0].to_dict()
    P("## Baseline (floor 1.5xATR5 | BE 1R | first target >= 1.5R)\n")
    P(f"{info['days']} plan days ≈ {info['days'] / 21:.1f} trading months → baseline ≈ ${gb('all')['total'] / (info['days'] / 21):,.0f}/month "
      f"(the original 24-day window ran ≈ $17k/month).\n")
    P(md_table([mrow("all", gb("all")), mrow("H1 (in-sample)", gb("H1")), mrow("H2 (out-of-sample)", gb("H2"))], COLS))
    old = run_cell([t for t in G if LEGACY_DATES[0] <= t["date"] <= LEGACY_DATES[1]], ("floor", 1.5), 1.0, "ge1.5")
    P(f"Same rules on just the original 24-day window, per-contract bars and 2+2-tick slippage: {fmt(metrics(old))}\n")
    Gf = [t for t in Sfree if t["graded"]]
    fb_ = run_cell(Gf, ("floor", 1.5), 1.0, "ge1.5")
    P(f"Without the publish-time correction (sessions from 18:00 as before): {fmt(metrics(fb_))}\n")

    # 4. selection on H1, report on H2
    h1 = grid[(grid.period == "H1") & (grid.n >= 30)].copy()
    h2 = grid[grid.period == "H2"].set_index("cell"); al = grid[grid.period == "all"].set_index("cell")
    b1 = gb("H1")
    h1["fragile"] = (h1.total > b1["total"]) & (h1.total_ex_top3 <= b1["total_ex_top3"])
    top = h1.sort_values("avgR_cap3", ascending=False).head(5)
    P("## Top 5 cells chosen on H1 (by avg R, wins capped at 3R), with their H2 (out-of-sample) numbers\n")
    tr = []
    for _, r in top.iterrows():
        tr.append(mrow(r.cell + (" ⚠ fragile (edge from <=3 trades)" if r.fragile else "") + " — H1", r.to_dict()))
        tr.append(mrow("   ↳ H2", h2.loc[r.cell].to_dict()))
    tr.append(mrow("BASELINE — H1", b1)); tr.append(mrow("   ↳ H2", gb("H2")))
    P(md_table(tr, COLS))
    top_tot = h1.sort_values("total", ascending=False).head(5)
    P("Top 5 on H1 by total $ (same cells may repeat):\n")
    P(md_table(sum([[mrow(r.cell + (" ⚠" if r.fragile else "") + " — H1", r.to_dict()), mrow("   ↳ H2", h2.loc[r.cell].to_dict())]
                    for _, r in top_tot.iterrows()], []), COLS))
    best = top.iloc[0].cell
    # rank of the H1 winner on H2 and how many cells beat baseline on both halves
    h2r = grid[(grid.period == "H2") & (grid.n >= 30)].sort_values("avgR_cap3", ascending=False).reset_index(drop=True)
    rank = int(h2r.index[h2r.cell == best][0]) + 1 if best in set(h2r.cell) else None
    both = grid.pivot_table(index="cell", columns="period", values="avgR_cap3")
    beat = both[(both.H1 > b1["avgR_cap3"]) & (both.H2 > gb("H2")["avgR_cap3"])]
    P(f"H1 winner ranks #{rank} of {len(h2r)} cells on H2. {len(beat)} of {len(both)} cells beat the baseline's capped avg R in BOTH halves.\n")

    # 5. one-factor views (all data) around the baseline
    def one(label, cells_):
        P(f"### {label}\n"); P(md_table([mrow(c + (" (baseline)" if c == base else ""), al.loc[c].to_dict()) | {"H2": f"{h2.loc[c]['avgR_cap3']:+.2f}"} for c in cells_ if c in al.index], COLS + ["H2"]))
    P("## One factor at a time (others at baseline; 'H2' = out-of-sample capped avg R)\n")
    one("Stop", [cell_name(s, 1.0, "ge1.5", None) for s in STOPS])
    one("Breakeven", [cell_name(BASE["stop"], b, "ge1.5", None) for b in BES])
    one("Target", [cell_name(BASE["stop"], 1.0, tg, None) for tg in TGTS])
    one("Partials (BE comes from the partial)", [cell_name(BASE["stop"], None, "ge1.5", p) if p else base for p in PARTIALS])
    one("ATR5 source (prior close vs live at entry)", [base, cell_name(BASE["stop"], 1.0, "ge1.5", None, "live")] +
        [cell_name(s, 1.0, "ge1.5", None, "live") for s in STOPS if s[0] == "floor" and s != BASE["stop"]])
    fbk = per[cell_name(("proxy", None), 1.0, "ge1.5", None)].proxy_fallback.mean()
    P(f"(His-level proxy had no zone beyond the gate on {fbk:.0%} of trades; those fall back to the 1.5xATR5 floor.)\n")

    # 5b. fill sensitivity: the edge fill flatters tight stops (the confirming bar has already closed beyond the edge)
    P("## Fill sensitivity — filled at the confirming bar's close instead of at the zone edge\n")
    P("The baseline assumes a fill at the zone edge, but the entry signal is a 5m CLOSE beyond the edge, so a real order fills "
      "at or near that close (or needs a retest). This matters most for tight stops.\n")
    fr = []
    for c in [base, cell_name(("tick", None), 1.0, "ge1.5", None)] + list(top.cell[:5]):
        spec = next((x for x in cells if cell_name(*x) == c), None)
        if spec is None: continue
        dfc = run_cell(G, spec[0], spec[1], spec[2], spec[3], fill="close")
        dfr = run_cell(G, spec[0], spec[1], spec[2], spec[3], fill="retest")
        dfs = run_cell(G, spec[0], spec[1], spec[2], spec[3], fill="stop_entry")
        dfo = run_cell(G, spec[0], spec[1], spec[2], spec[3], fill="stop_entry_opt")
        for lab, f_ in (("all", lambda d: d), ("H1", lambda d: d[d.date <= split]), ("H2", lambda d: d[d.date > split])):
            m = metrics(f_(dfc)); mr = metrics(f_(dfr)); ms = metrics(f_(dfs)); mo = metrics(f_(dfo)); edge = grid[(grid.cell == c) & (grid.period == lab)].iloc[0]
            fr.append(dict(cell=(c + (" (baseline)" if c == base else "")) if lab == "all" else "   ↳ " + lab,
                           edge=f"n {edge.n:.0f} · {edge.avgR_cap3:+.2f}R · ${edge.total:,.0f}",
                           close_fill=f"n {m['n']} · {m['avgR_cap3']:+.2f}R · ${m['total']:,.0f} · PF {m['pf']:.2f}",
                           retest_fill=f"n {mr['n']} · {mr['avgR_cap3']:+.2f}R · ${mr['total']:,.0f} · PF {mr['pf']:.2f}",
                           stop_entry=f"n {ms['n']} · {ms['avgR_cap3']:+.2f}R · ${ms['total']:,.0f} · PF {ms['pf']:.2f}",
                           stop_entry_optimistic=f"{mo['avgR_cap3']:+.2f}R · ${mo['total']:,.0f} · PF {mo['pf']:.2f}"))
    P(md_table(fr, ["cell", "edge", "close_fill", "retest_fill", "stop_entry", "stop_entry_optimistic"]))
    gap = pd.Series([abs(t["eclose"] - t["e"]) / t["atr5"] for t in Gc])
    P(f"Confirming close beyond the edge: median {gap.median():.2f} ATR5, mean {gap.mean():.2f}, 75th pct {gap.quantile(.75):.2f}. "
      f"Retest = limit at the edge after the close, filled only if price returns to it that session; stop-entry = resting stop "
      f"order 1 tick through the edge once price has traded into the zone (no close confirmation, so it also takes the failed reclaims; "
      f"'conservative' counts the fill bar's adverse extreme against the stop, 'optimistic' assumes it came before the fill) "
      f"({len(run_cell(G, BASE['stop'], 1.0, 'ge1.5', fill='retest'))} of {len(Gc)} graded close-triggers fill).\n")

    # 5c. does ANY management cell work with an executable fill?
    P("## Full grid re-run with executable fills (selection on H1, report H2)\n")
    frows = []
    for fill in ("close", "stop_entry"):
        for (s_, b_, tg_, p_) in cells:
            d = run_cell(G, s_, b_, tg_, p_, fill=fill)
            if len(d) == 0: continue
            for lab, sub in (("all", d), ("H1", d[d.date <= split]), ("H2", d[d.date > split])):
                m = metrics(sub); m.update(cell=cell_name(s_, b_, tg_, p_), period=lab, fill=fill); frows.append(m)
    fg = pd.DataFrame(frows); fg.to_csv("backtest_grid_fills.csv", index=False)
    for fill, label in (("close", "market at the confirming close"), ("stop_entry", "resting stop order 1 tick through the edge")):
        f1 = fg[(fg.fill == fill) & (fg.period == "H1") & (fg.n >= 30)].sort_values("avgR_cap3", ascending=False).head(5)
        f2 = fg[(fg.fill == fill) & (fg.period == "H2")].set_index("cell")
        fa = fg[(fg.fill == fill) & (fg.period == "all")].set_index("cell")
        rr = []
        for _, r in f1.iterrows():
            rr.append(mrow(r.cell + " — H1", r.to_dict())); rr.append(mrow("   ↳ H2", f2.loc[r.cell].to_dict()))
        bb = fg[(fg.fill == fill) & (fg.cell == base)].set_index("period")
        rr.append(mrow("BASELINE — H1", bb.loc["H1"].to_dict())); rr.append(mrow("   ↳ H2", bb.loc["H2"].to_dict()))
        pos = int(((fa.avgR_cap3 > 0) & (fa.n >= 100)).sum())
        P(f"**Fill = {label}** — {pos} of {len(fa)} cells have positive capped avg R over the whole sample.\n")
        P(md_table(rr, COLS))

    # 6. slices of the baseline
    P("## Baseline slices\n")
    sl = [mrow(f"grade {g}", metrics(bd[bd.grade == g])) for g in ("A", "B", "C")]
    sl += [mrow(k, metrics(bd[bd.kind == k])) for k in ("fade", "break")]
    sl += [mrow(s, metrics(bd[bd.sym == s])) for s in ("ES", "NQ")]
    for s in ("ES", "NQ"):
        for lab, sub in (("H1", bd[bd.date <= split]), ("H2", bd[bd.date > split])): sl.append(mrow(f"{s} {lab}", metrics(sub[sub.sym == s])))
    ung = run_cell(U, BASE["stop"], 1.0, "ge1.5")
    sl.append(mrow("UNGRADED (not in headline)", metrics(ung)))
    P(md_table(sl, COLS))

    # 7. sweep depth buckets (fade trades): tick stop survival vs baseline stop, target hit
    P("## Sweep depth (fade trades, graded) — does the stop survive, does the target get hit?\n")
    tick = per[cell_name(("tick", None), None, "ge1.5", None)]; flo = per[cell_name(BASE["stop"], None, "ge1.5", None)]
    keyc = ["date", "id", "sym"]
    j = flo.merge(tick[keyc + ["exit", "R"]], on=keyc, suffixes=("", "_tick"))
    j = j[j.kind == "fade"]
    br = []
    for lo, hi in ((0, 0.5), (0.5, 1.5), (1.5, 3), (3, 99)):
        g = j[(j.depth_atr5 >= lo) & (j.depth_atr5 < hi)]
        if not len(g): continue
        br.append(dict(depth=f"{lo}-{hi if hi < 99 else '∞'} ATR5", n=len(g),
                       tick_stop_survives=f"{(g.exit_tick != 'stop').mean():.0%}", floor15_stop_survives=f"{(g.exit != 'stop').mean():.0%}",
                       target_hit_floor15=f"{(g.exit == 'target').mean():.0%}", avgR3_tick=f"{g.R_tick.clip(upper=3).mean():+.2f}",
                       avgR3_floor15=f"{g.R.clip(upper=3).mean():+.2f}"))
    P(md_table(br, ["depth", "n", "tick_stop_survives", "floor15_stop_survives", "target_hit_floor15", "avgR3_tick", "avgR3_floor15"]))
    P("(no breakeven in this table, so 'survives' means the original stop was never hit before the target or the close)\n")
    open("backtest_grid_summary.md", "w").write("\n".join(out) + "\n")
    print("\nwrote backtest_grid.csv, backtest_grid_trades.csv, backtest_grid_summary.md")


if __name__ == "__main__":
    main()
