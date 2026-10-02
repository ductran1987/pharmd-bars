"""Stop-placement analysis: composite profiles (1-wk 5m, 2-wk 1h) with LVN/HVN, ATR, and per-trade stop candidates.
Usage: python stops.py plans/plan-YYYY-MM-DD.json  -> charts/stops_<date>_<SYM>.png + stops_<date>.json
"""
import json, sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import charts
tz = "America/New_York"
INK, MUTE, GRID = charts.INK, charts.MUTE, charts.GRID
LONG, SHORT, PIVOT = charts.LONG, charts.SHORT, charts.PIVOT
LVN_C, HVN_C, STOP_C = "#c4383a", "#6b7280", "#b7791f"


def nodes(edges, vol, step, smooth=3):
    v = np.convolve(vol, np.ones(smooth) / smooth, mode="same"); mx = v.max()
    lv, hv = [], []
    for i in range(1, len(v) - 1):
        p = edges[i] + step / 2
        if v[i] < v[i-1] and v[i] <= v[i+1] and v[i] < 0.35 * mx: lv.append((float(p), float(v[i] / mx)))
        if v[i] > v[i-1] and v[i] >= v[i+1] and v[i] > 0.6 * mx: hv.append((float(p), float(v[i] / mx)))
    return lv, hv


def lvn_zones(edges, vol, step, smooth=3, thr=0.35):
    """Contiguous low-volume zones (smoothed volume < thr × peak).
    Each zone: dict(lo, hi, min_p, min_r, void_lo, void_hi) — lo/hi are the price edges where volume
    climbs back above threshold; void_* flags a zone that runs off the end of the profile (no volume beyond)."""
    v = np.convolve(vol, np.ones(smooth) / smooth, mode="same"); mx = v.max()
    below = v < thr * mx
    zones, i, n = [], 0, len(v)
    while i < n:
        if not below[i]: i += 1; continue
        j = i
        while j < n and below[j]: j += 1
        k = i + int(np.argmin(v[i:j]))
        zones.append(dict(lo=float(edges[i]), hi=float(edges[j]), min_p=float(edges[k] + step / 2),
                          min_r=float(v[k] / mx), void_lo=(i == 0), void_hi=(j == n)))
        i = j
    return zones


def lvn_candidate(zones, entry, direction):
    """Nearest LVN zone past the entry, in the stop direction. Returns (far_edge, zone) or (None, None).
    Far edge = where volume climbs back above threshold on the side away from the entry.
    If the zone is a void (runs off the profile), the far edge is undefined -> (None, zone) so the caller can say so."""
    if direction == "long":
        cands = [z for z in zones if z["hi"] <= entry or z["lo"] < entry <= z["hi"]]
        if not cands: return None, None
        z = max(cands, key=lambda z: z["hi"])
        return (None if z["void_lo"] else z["lo"]), z
    else:
        cands = [z for z in zones if z["lo"] >= entry or z["lo"] <= entry < z["hi"]]
        if not cands: return None, None
        z = min(cands, key=lambda z: z["lo"])
        return (None if z["void_hi"] else z["hi"]), z


def atr(d5, sessions_back=3, end=None):
    """ATR(14) on 5m and 15m RTH bars over the last `sessions_back` sessions ending at `end` (ref-session rule: nothing after the prior close)."""
    if end is not None: d5 = d5[d5.time <= end]
    r = d5[d5.time >= d5.time.iloc[-1].normalize() - pd.Timedelta(days=sessions_back + 2)]
    m = r.time.dt.hour * 60 + r.time.dt.minute; r = r[(m >= 570) & (m < 960)]
    def _atr(df, n=14):
        tr = np.maximum(df.High - df.Low, np.maximum((df.High - df.Close.shift()).abs(), (df.Low - df.Close.shift()).abs()))
        return float(tr.rolling(n).mean().dropna().iloc[-40:].mean())
    r15 = r.set_index("time").resample("15min").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna()
    return _atr(r), _atr(r15)


def analyze(sym, plan_date):
    d5, d1 = charts.load(sym), charts.load_1h(sym)
    step = 1.0 if sym == "ES" else 5.0
    end = pd.Timestamp(plan_date, tz=tz) - pd.Timedelta(hours=7)   # 5pm the day before
    w1 = (end - pd.Timedelta(days=7)).replace(hour=18, minute=0)
    w2 = (end - pd.Timedelta(days=14)).replace(hour=18, minute=0)
    w3 = (end - pd.Timedelta(days=28)).replace(hour=18, minute=0)   # ~20 sessions
    e1, v1, poc1, va1lo, va1hi = charts.profile(d5, w1, end, step)
    e2, v2, poc2, va2lo, va2hi = charts.profile(d1, w2, end, step * 2)
    # 20-session composite: 5m when the file reaches back that far, else 1h
    src3 = d5 if d5.time.min() <= w3 + pd.Timedelta(days=2) else d1
    e3, v3, poc3, va3lo, va3hi = charts.profile(src3, w3, end, step * 2)
    lv1, hv1 = nodes(e1, v1, step); lv2, hv2 = nodes(e2, v2, step * 2); lv3, hv3 = nodes(e3, v3, step * 2)
    a5, a15 = atr(d5, end=end)
    # 15m swings over the last 3 ETH sessions (for the swing candidate)
    st = (end - pd.Timedelta(days=4)).replace(hour=18, minute=0)
    b15 = d5[(d5.time >= st) & (d5.time <= end)].set_index("time").resample("15min").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna().reset_index()
    sh, sl = swings(b15, k=6)
    return dict(step=step, p1=(e1, v1, poc1, va1lo, va1hi), p2=(e2, v2, poc2, va2lo, va2hi), p3=(e3, v3, poc3, va3lo, va3hi),
                p3_src="5m" if src3 is d5 else "1h", lvn1=lv1, hvn1=hv1, lvn2=lv2, hvn2=hv2, lvn3=lv3, hvn3=hv3,
                swing_hi=[y for _, y in sh], swing_lo=[y for _, y in sl],
                atr5=a5, atr15=a15, w1=w1, w2=w2, w3=w3, end=end)


TICK = 0.25
PT_VALUE = {"ES": 50.0, "NQ": 20.0}
MICRO_VALUE = {"ES": 5.0, "NQ": 2.0}     # MES / MNQ
MIN_R_FIRST = 1.0    # grey out trades under this R to the first target
ATR_CAP = 1.3        # recommendation never exceeds this × ATR15 unless structure itself demands it
LVN_THR = 0.35


def _tick(x, direction, away=True):
    """Round to tick, in the direction that widens (away=True) the stop."""
    f = np.floor if (direction == "long") == away else np.ceil
    return float(f(x / TICK) * TICK)


def _flat(tgts):
    """Plan targets may be [lo,hi] ranges: first target = nearer edge, in trade direction handled by caller."""
    return [t if isinstance(t, (int, float)) else list(t) for t in tgts]


BUFFER_ATR5 = 0.1    # structural buffer past the level, in 5m ATRs (~1 pt ES / ~4 NQ; to be replaced by MAE percentiles once logged)
RISK_USD = 500.0     # fixed $ risk per trade; sized in micros (MES/MNQ), full contracts shown when >=1 fits


def candidates(sym, A, pt, risk_usd=None, atr_mult=1.0, buffer_atr5=None, level=None, plan_levels=()):
    """Build the three stop candidates + recommendation for one plan trade `pt` (plans/plan-*.json entry).
    Entry assumption: long = top of gate, short = bottom of gate (the hold/LBAF fires from inside the gate).
    structural = his invalidation level, buffered past it by ½ ATR5.
    lvn        = far edge of the nearest sub-35% zone beyond the entry (1-wk 5m and 2-wk 1h profiles; nearer wins).
    atr        = entry ∓ atr_mult × ATR15.
    recommended: structural is the floor; an LVN beyond it pushes the stop to one tick past the zone's far edge
                 if that stays within ATR_CAP × ATR15; a void zone (profile ends) never pulls the stop into it."""
    d = pt["dir"]; L = pt["levels"]; step = A["step"]
    gate = sorted(L["gate"]); entry = gate[-1] if d == "long" else gate[0]
    sgn = -1 if d == "long" else 1
    level = level if level is not None else pt.get("stop_level", L["stop"][0])   # trade-specific invalidation; plan's levels.stop is often the bigger-picture failure
    b = BUFFER_ATR5 if buffer_atr5 is None else buffer_atr5
    structural = _tick(level + sgn * b * A["atr5"], d)
    z1 = lvn_zones(*A["p1"][:2], step, thr=LVN_THR); z2 = lvn_zones(*A["p2"][:2], step * 2, thr=LVN_THR); z3 = lvn_zones(*A["p3"][:2], step * 2, thr=LVN_THR)
    c1, zz1 = lvn_candidate(z1, entry, d); c2, zz2 = lvn_candidate(z2, entry, d); c3, zz3 = lvn_candidate(z3, entry, d)
    prof = ((c1, zz1, "1-wk"), (c2, zz2, "2-wk"), (c3, zz3, "20-day"))
    opts = [(c, z, src) for c, z, src in prof if c is not None]
    voids = [(z, src) for c, z, src in prof if z is not None and (z["void_lo"] if d == "long" else z["void_hi"])]
    if opts:   # a bounded zone: stop one tick past its far edge
        lvn_edge, zone, zsrc = min(opts, key=lambda o: abs(o[0] - entry)); void = False
        lvn = _tick(lvn_edge + sgn * TICK, d)
    elif voids:   # only a void beyond the entry: no far edge to use
        zone, zsrc = voids[0]; lvn, void = None, True
    else:
        lvn, zone, zsrc, void = None, None, None, False
    atr_c = _tick(entry + sgn * atr_mult * A["atr15"], d)
    cap = entry + sgn * ATR_CAP * A["atr15"]
    beyond = lambda a, b: (a < b) if d == "long" else (a > b)   # a is further from entry than b
    rec, basis = structural, "structural"
    if void: basis = "structural (thin volume beyond the entry is a void that runs off the profile — not chased)"
    elif lvn is not None and beyond(lvn, structural):
        if beyond(lvn, cap): basis = f"structural (LVN far edge {lvn:g} would be {abs(lvn-entry)/A['atr15']:.2f} ATR — over cap)"
        else: rec, basis = lvn, "LVN far edge"
    elif lvn is not None: basis = "structural (LVN sits inside it)"
    risk = abs(entry - rec)
    # targets: nearer edge of each range in trade direction
    tg = []
    for t in L["tgt"]:
        if isinstance(t, (list, tuple)): tg.append(min(t) if d == "long" else max(t))
        else: tg.append(t)
    rr = [round(abs(t - entry) / risk, 1) for t in tg]
    # ---- ladder: every defensible stop, nearest first; the trader picks ----
    ladder = [("tight", f"1 tick past {level:g}", _tick(level + sgn * TICK, d)),
              ("structural", f"{level:g} + {b:g} ATR5 buffer", structural)]
    for c_, z_, src_ in opts:
        ladder.append((f"lvn_{src_}", f"{src_} LVN far edge ({z_['lo']:g}–{z_['hi']:g})", _tick(c_ + sgn * TICK, d)))
    far_gate = gate[0] if d == "long" else gate[-1]
    sw = [y for y in (A["swing_lo"] if d == "long" else A["swing_hi"]) if beyond(y, far_gate)]   # a swing inside the gate is the gate
    if sw:
        y = max(sw) if d == "long" else min(sw)   # nearest swing beyond the entry
        ladder.append(("swing", f"15m swing {'low' if d == 'long' else 'high'} {y:g}", _tick(y + sgn * TICK, d)))
    ladder.append(("atr", f"{atr_mult:g} × ATR15", atr_c))
    nxt = [p for p in plan_levels if beyond(p, level)]
    if nxt:
        y = max(nxt) if d == "long" else min(nxt)
        ladder.append(("next_level", f"next plan level {y:g}", _tick(y + sgn * TICK, d)))
    options, seen = [], []
    for key, lab, y in sorted(ladder, key=lambda o: abs(o[2] - entry)):
        if any(abs(y - y0) <= TICK * 2 for y0 in seen): continue   # same spot twice: keep the first (nearer) label
        seen.append(y); rk = abs(entry - y)
        if rk < 0.2 * A["atr15"] or rk > 2.0 * A["atr15"]: continue
        o = dict(key=key, label=lab, stop=y, risk=round(rk, 2), risk_atr=round(rk / A["atr15"], 2),
                 rr=[round(abs(t - entry) / rk, 1) for t in tg], over_cap=bool(rk > ATR_CAP * A["atr15"]),
                 recommended=bool(abs(y - rec) <= TICK * 2))
        if risk_usd:
            o["micros"] = int(risk_usd // (rk * MICRO_VALUE[sym])); o["contracts"] = int(risk_usd // (rk * PT_VALUE[sym]))
            o["under_r"] = bool(o["rr"][0] < MIN_R_FIRST)
        options.append(o)
    out = dict(instrument=sym, id=pt["id"], short=pt["name"], dir=d, entry=float(entry), gate_pts=gate, options=options,
               structure_level=level, grade=pt.get("tag", ""),
               stop_pts=dict(structural=structural, lvn=lvn, atr=atr_c, recommended=rec),
               lvn_zone=(dict(lo=zone["lo"], hi=zone["hi"], min_p=zone["min_p"], min_r=round(zone["min_r"], 2), src=zsrc, void=bool(void)) if zone else None),
               basis=basis, buffer_atr5=b, atr15=round(A["atr15"], 2), atr5=round(A["atr5"], 2), atr_mult=atr_mult,
               risk=round(risk, 2), risk_atr=round(risk / A["atr15"], 2), tgts=tg, rr=rr,
               wide=bool(risk > ATR_CAP * A["atr15"]))
    if risk_usd:
        n = int(risk_usd // (risk * PT_VALUE[sym])); m = int(risk_usd // (risk * MICRO_VALUE[sym]))
        reason = None
        if rr[0] < MIN_R_FIRST: reason = f"under {MIN_R_FIRST:g}R to the first target"
        elif n < 1 and m < 1: reason = "even one micro risks more than the budget"
        out.update(risk_usd=risk_usd, contracts=n, micros=m, risk_per_contract_usd=round(risk * PT_VALUE[sym], 2),
                   risk_per_micro_usd=round(risk * MICRO_VALUE[sym], 2), skip=reason is not None, skip_reason=reason)
    return out


def draw(sym, A, trades, out, title):
    e1, v1, poc1, va1lo, va1hi = A["p1"]; e2, v2, poc2, va2lo, va2hi = A["p2"]; step = A["step"]
    lo = min(e1[0], e2[0], min(t["stop_pts"]["recommended"] for t in trades) - step * 4)
    hi = max(e1[-1], e2[-1])
    # focus the y-range on where the trades are
    ys = [t["entry"] for t in trades] + [t["stop_pts"]["recommended"] for t in trades] + [x for t in trades for x in t["tgts"]]
    lo = max(lo, min(ys) - (hi - lo) * 0.08); hi = min(hi, max(ys) + (hi - lo) * 0.08)
    fig, ax = plt.subplots(figsize=(9.6, 7.2), dpi=170); fig.patch.set_facecolor("white")
    colw = 1.0
    def bars(ax, edges, vol, x0, valo, vahi, poc, label, stepp):
        sc = colw / vol.max()
        for i in range(len(vol)):
            inva = valo <= edges[i] < vahi
            ax.barh(edges[i], vol[i] * sc, height=stepp, left=x0, align="edge", color="#8b96a3" if inva else "#c9ced4", alpha=0.75 if inva else 0.5, lw=0, zorder=2)
        ax.plot([x0, x0 + colw], [poc, poc], color="#b7791f", lw=1.6, zorder=4)
        ax.text(x0 + colw / 2, hi - step, label, ha="center", va="top", fontsize=8, color=MUTE)
        ax.text(x0 + 0.02, poc + stepp * 0.6, f"POC {poc:g}", fontsize=6.5, color="#b7791f", fontweight="bold", va="bottom")
    bars(ax, e1, v1, 0.0, va1lo, va1hi, poc1, "1-week (5m)", step)
    bars(ax, e2, v2, 1.15, va2lo, va2hi, poc2, "2-week (1h)", step * 2)
    # nodes
    for p, r in A["lvn1"]:
        if lo <= p <= hi: ax.plot([0, colw], [p, p], color=LVN_C, lw=1.0, ls=":", zorder=5); ax.text(colw + 0.02, p, f"LVN {p:g}", fontsize=6.5, color=LVN_C, va="center")
    for p, r in A["lvn2"]:
        if lo <= p <= hi: ax.plot([1.15, 1.15 + colw], [p, p], color=LVN_C, lw=1.0, ls=":", zorder=5); ax.text(1.15 + colw + 0.02, p, f"LVN {p:g}", fontsize=6.5, color=LVN_C, va="center")
    for p, r in A["hvn1"]:
        if lo <= p <= hi: ax.text(-0.02, p, f"HVN {p:g}", fontsize=6.5, color=HVN_C, va="center", ha="right")
    # trades
    x = 2.6
    for t in trades:
        c = LONG if t["dir"] == "long" else SHORT
        g = t["gate_pts"]
        ax.add_patch(plt.Rectangle((x, min(g)), 0.5, max(max(g) - min(g), step * 0.6), color=c, alpha=0.25, lw=0, zorder=3))
        s = t["stop_pts"]["recommended"]
        ax.plot([x, x + 0.5], [s, s], color=STOP_C, lw=2.0, zorder=5)
        ax.annotate("", xy=(x + 0.25, t["tgts"][0]), xytext=(x + 0.25, t["entry"]), arrowprops=dict(arrowstyle="-|>", color=c, lw=1.2, ls="--"), zorder=4)
        ax.text(x + 0.25, s - step * 0.8 if t["dir"] == "long" else s + step * 0.8, f"stop {s:g}", ha="center", va="top" if t["dir"] == "long" else "bottom", fontsize=6.5, color=STOP_C, fontweight="bold")
        ax.text(x + 0.25, hi - step, t["short"], ha="center", va="top", fontsize=7, color=c, fontweight="bold", rotation=0)
        x += 0.7
    ax.set_xlim(-0.75, x + 0.1); ax.set_ylim(lo, hi)
    ax.set_xticks([]); ax.tick_params(axis="y", labelsize=7, colors=MUTE)
    for sp in ("top", "right", "bottom"): ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color(GRID); ax.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    ax.set_title(title, loc="left", fontsize=9.5, color=INK, fontweight="bold", pad=8)
    ax.text(0, lo + step, f"ATR(14): 5m {A['atr5']:.1f} · 15m {A['atr15']:.1f}   LVN = volume < 35% of peak · HVN = > 60%", fontsize=6.8, color=MUTE, va="bottom")
    fig.subplots_adjust(left=0.12, right=0.98, top=0.93, bottom=0.05)
    fig.savefig(out, facecolor="white"); plt.close(fig)


def draw_trade(sym, A, t, out):
    """One chart per trade: profiles zoomed to the trade, entry, three stop candidates, recommended, targets."""
    e1, v1, poc1, va1lo, va1hi = A["p1"]; e2, v2, poc2, va2lo, va2hi = A["p2"]; step = A["step"]
    s = t["stop_pts"]; c = LONG if t["dir"] == "long" else SHORT
    ys = [t["entry"], s["structural"], s["lvn"], s["atr"], s["recommended"]] + list(t["tgts"]) + list(t["gate_pts"])
    pad = (max(ys) - min(ys)) * 0.12 + step * 2
    lo, hi = min(ys) - pad, max(ys) + pad
    fig, ax = plt.subplots(figsize=(7.6, 5.2), dpi=170); fig.patch.set_facecolor("white")
    colw = 1.0
    def bars(edges, vol, x0, valo, vahi, poc, label, stepp):
        m = (edges[:-1] >= lo - stepp) & (edges[:-1] <= hi)
        if not m.any(): return
        sc = colw / max(vol[m].max(), 1e-9)
        for i in np.where(m)[0]:
            inva = valo <= edges[i] < vahi
            ax.barh(edges[i], vol[i] * sc, height=stepp, left=x0, align="edge", color="#8b96a3" if inva else "#c9ced4", alpha=0.75 if inva else 0.5, lw=0, zorder=2)
        if lo <= poc <= hi:
            ax.plot([x0, x0 + colw], [poc, poc], color="#b7791f", lw=1.4, zorder=4)
            ax.text(x0 + 0.02, poc + stepp * 0.5, f"POC {poc:g}", fontsize=6.3, color="#b7791f", fontweight="bold", va="bottom")
        ax.text(x0 + colw / 2, hi - step * 0.3, label, ha="center", va="top", fontsize=7.5, color=MUTE)
    bars(e1, v1, 0.0, va1lo, va1hi, poc1, "1-wk", step)
    bars(e2, v2, 1.12, va2lo, va2hi, poc2, "2-wk", step * 2)
    for p, r in A["lvn1"]:
        if lo <= p <= hi: ax.plot([0, colw], [p, p], color=LVN_C, lw=1.0, ls=":", zorder=5); ax.text(-0.03, p, f"LVN {p:g}", fontsize=6.5, color=LVN_C, va="center", ha="right")
    for p, r in A["lvn2"]:
        if lo <= p <= hi: ax.plot([1.12, 1.12 + colw], [p, p], color=LVN_C, lw=1.0, ls=":", zorder=5)
    for p, r in A["hvn1"]:
        if lo <= p <= hi: ax.text(-0.03, p, f"HVN {p:g}", fontsize=6.5, color=HVN_C, va="center", ha="right")
    # trade column
    x = 2.5; w = 1.6
    g = t["gate_pts"]
    ax.add_patch(plt.Rectangle((x, min(g)), w, max(max(g) - min(g), step * 0.6), color=c, alpha=0.18, lw=0, zorder=3))
    ax.text(x + w + 0.05, (min(g) + max(g)) / 2, "gate", fontsize=7, color=c, va="center")
    ax.plot([x, x + w], [t["entry"]] * 2, color=c, lw=1.2, zorder=4); ax.text(x + w + 0.05, t["entry"], f"entry {t['entry']:g}", fontsize=7, color=c, va="center", fontweight="bold")
    for tg in t["tgts"]:
        ax.plot([x, x + w], [tg] * 2, color=PIVOT, lw=0.9, ls="--", zorder=4); ax.text(x + w + 0.05, tg, f"tgt {tg:g}", fontsize=7, color=PIVOT, va="center")
    cands = [("structural", s["structural"]), ("LVN", s["lvn"]), (f"{t['atr_mult']}×ATR", s["atr"])]
    for i, (lab, y) in enumerate(cands):
        ax.plot([x + i * w / 3, x + (i + 1) * w / 3], [y] * 2, color=STOP_C, lw=1.0, ls=":", zorder=4)
        ax.text(x + (i + 0.5) * w / 3, y + (step * 0.6 if t["dir"] == "short" else -step * 0.6), lab, fontsize=6, color=STOP_C, ha="center", va="bottom" if t["dir"] == "short" else "top")
    r = s["recommended"]
    ax.plot([x, x + w], [r] * 2, color=STOP_C, lw=2.4, zorder=6)
    ax.text(x + w + 0.05, r, f"STOP {r:g}  ({t['risk']:g} pts · {t['risk']/t['atr15']:.2f} ATR)", fontsize=7.5, color=STOP_C, va="center", fontweight="bold")
    ax.annotate("", xy=(x + w / 2, t["tgts"][0]), xytext=(x + w / 2, t["entry"]), arrowprops=dict(arrowstyle="-|>", color=c, lw=1.1, ls="--"), zorder=4)
    ax.set_xlim(-0.9, x + w + 1.9); ax.set_ylim(lo, hi)
    ax.set_xticks([]); ax.tick_params(axis="y", labelsize=7, colors=MUTE)
    for sp in ("top", "right", "bottom"): ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color(GRID); ax.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    ax.set_title(f"{sym}  {t['short']}  ·  {t['dir']}  ·  R: " + " / ".join(f"{v}" for v in t["rr"]), loc="left", fontsize=9.5, color=INK, fontweight="bold", pad=8)
    fig.subplots_adjust(left=0.14, right=0.98, top=0.92, bottom=0.04)
    fig.savefig(out, facecolor="white"); plt.close(fig)


def swings(bars, k=3):
    """Fractal swing highs/lows on the given bars (k bars each side)."""
    hi, lo = [], []
    H, L = bars.High.values, bars.Low.values
    for i in range(k, len(bars) - k):
        if H[i] == H[i-k:i+k+1].max(): hi.append((i, float(H[i])))
        if L[i] == L[i-k:i+k+1].min(): lo.append((i, float(L[i])))
    return hi, lo


def draw_trade2(sym, A, t, out, d5, plan_date, sessions=3):
    """Per-trade chart with structure: ETH candles (15m, last N sessions incl. overnight) + swing points + profiles + stop column."""
    e1, v1, poc1, va1lo, va1hi = A["p1"]; e2, v2, poc2, va2lo, va2hi = A["p2"]; e3, v3, poc3, va3lo, va3hi = A["p3"]; step = A["step"]
    s = t["stop_pts"]; c = LONG if t["dir"] == "long" else SHORT
    end = pd.Timestamp(plan_date, tz=tz) - pd.Timedelta(hours=7)
    start = (end - pd.Timedelta(days=sessions + 1)).replace(hour=18, minute=0)
    w = d5[(d5.time >= start) & (d5.time <= end)].set_index("time")
    bars = w.resample("15min").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna().reset_index()
    n = len(bars)
    rth = [(9*60+30 <= x.hour*60+x.minute < 16*60) for x in bars.time]
    # y-range: the trade's levels plus the bulk of the last two sessions (ETH) so earlier action doesn't clip
    ys = [t["entry"], s["structural"], s["atr"], s["recommended"]] + ([s["lvn"]] if s.get("lvn") is not None else []) + list(t["tgts"]) + list(t["gate_pts"])
    recent = bars.iloc[-int(n * 2 / (sessions + 1)):] if sessions > 1 else bars
    lo = min(min(ys), recent.Low.quantile(0.03)); hi = max(max(ys), recent.High.quantile(0.97))
    pad = (hi - lo) * 0.07 + step * 2
    lo, hi = lo - pad, hi + pad
    fig, (axc, axp) = plt.subplots(1, 2, figsize=(14.4, 6.2), dpi=170, gridspec_kw=dict(width_ratios=[2.7, 1.9], wspace=0.03), sharey=True)
    fig.patch.set_facecolor("white")
    # ---- candles ----
    i = 0
    while i < n:   # shade overnight
        if not rth[i]:
            j = i
            while j < n and not rth[j]: j += 1
            axc.axvspan(i - 0.5, j - 0.5, color="#eef0ee", zorder=0); i = j
        else: i += 1
    bw = 0.64
    for i, r in bars.iterrows():
        cc = charts.UP if r.Close >= r.Open else charts.DOWN
        axc.plot([i, i], [r.Low, r.High], color=cc, lw=0.9, zorder=2, solid_capstyle="butt")
        axc.add_patch(plt.Rectangle((i - bw / 2, min(r.Open, r.Close)), bw, max(abs(r.Close - r.Open), step * 0.15), color=cc, lw=0, zorder=3))
    # session dividers: ETH open (18:00) solid, RTH open (9:30) dotted; date label at the RTH open
    for i, x in enumerate(bars.time):
        hm = x.hour * 60 + x.minute
        if hm == 18 * 60: axc.axvline(i - 0.5, color="#b9bfc6", lw=0.9, zorder=1)
        if hm == 9 * 60 + 30:
            axc.axvline(i - 0.5, color="#b9bfc6", lw=0.8, ls=(0, (2, 2)), zorder=1)
            axc.text(i, hi - step * 0.4, x.strftime("%a %-m/%-d"), fontsize=7.2, color=MUTE, va="top", ha="left")
    # swings: mark the ones within the window and near the trade
    sh, sl = swings(bars, k=6)
    rel = sl if t["dir"] == "long" else sh
    band = (s["recommended"] - step * 6, t["entry"] + step * 6) if t["dir"] == "long" else (t["entry"] - step * 6, s["recommended"] + step * 6)
    done = []
    for i, y in rel:
        if band[0] <= y <= band[1]:
            if any(abs(i - i0) <= 8 and abs(y - y0) <= step * 1.5 for i0, y0 in done): continue   # one label per cluster
            done.append((i, y))
            axc.plot(i, y, marker="v" if t["dir"] == "long" else "^", color=c, ms=4.5, zorder=5)
            axc.annotate(f"{y:g}", (i, y), xytext=(0, -8 if t["dir"] == "long" else 8), textcoords="offset points", ha="center", va="top" if t["dir"] == "long" else "bottom", fontsize=6.3, color=c)
    # gate / entry / stop / targets across the candles
    g = t["gate_pts"]
    axc.axhspan(min(g), max(g) if max(g) > min(g) else min(g) + step * 0.6, color=c, alpha=0.12, lw=0, zorder=1)
    axc.axhline(t["entry"], color=c, lw=1.0, zorder=4)
    axc.axhline(s["recommended"], color=STOP_C, lw=2.0, zorder=5)
    for tg in t["tgts"]: axc.axhline(tg, color=PIVOT, lw=0.8, ls="--", zorder=1)
    # structural reference line(s) the stop hides behind
    for k_, (lab, y) in enumerate(t.get("structure", [])):
        if lo <= y <= hi:
            axc.axhline(y, color=INK, lw=0.8, ls=(0, (4, 2)), zorder=4)
            axc.text(0.3 + k_ * n * 0.34, y, lab, fontsize=6.5, color=INK, va="bottom" if t["dir"] == "long" else "top", bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85), zorder=7)
    axc.text(n - 0.5, s["recommended"], f" stop {s['recommended']:g}", fontsize=7, color=STOP_C, va="bottom" if t["dir"] == "long" else "top", ha="right", fontweight="bold", zorder=7)
    axc.set_xlim(-0.8, n + 0.3); axc.set_ylim(lo, hi)
    axc.set_xticks([]); axc.tick_params(axis="y", labelsize=7.5, colors=MUTE)
    for sp in ("top", "right", "bottom"): axc.spines[sp].set_visible(False)
    axc.spines["left"].set_color(GRID); axc.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    axc.set_title(f"{sym}  {t['short']}  ·  {t['dir']}  ·  ETH 15m, last {sessions} sessions (overnight shaded)", loc="left", fontsize=9.5, color=INK, fontweight="bold", pad=8)
    # ---- profiles + stop column ----
    colw = 1.0
    def bars_(edges, vol, x0, valo, vahi, poc, label, stepp):
        m = (edges[:-1] >= lo - stepp) & (edges[:-1] <= hi)
        if not m.any(): return
        sc = colw / max(vol[m].max(), 1e-9)
        for i in np.where(m)[0]:
            inva = valo <= edges[i] < vahi
            axp.barh(edges[i], vol[i] * sc, height=stepp, left=x0, align="edge", color="#8b96a3" if inva else "#c9ced4", alpha=0.75 if inva else 0.5, lw=0, zorder=2)
        if lo <= poc <= hi:
            axp.plot([x0, x0 + colw], [poc, poc], color="#b7791f", lw=1.4, zorder=4)
            axp.text(x0 + 0.02, poc + stepp * 0.5, f"POC {poc:g}", fontsize=6.3, color="#b7791f", fontweight="bold", va="bottom")
        axp.text(x0 + colw / 2, hi - step * 0.3, label, ha="center", va="top", fontsize=7.5, color=MUTE)
    bars_(e1, v1, 0.0, va1lo, va1hi, poc1, "1-wk", step)
    bars_(e2, v2, 1.12, va2lo, va2hi, poc2, "2-wk", step * 2)
    bars_(e3, v3, 2.24, va3lo, va3hi, poc3, f"20-day ({A.get('p3_src','1h')})", step * 2)
    for p, r in A["lvn3"]:
        if lo <= p <= hi: axp.plot([2.24, 2.24 + colw], [p, p], color=LVN_C, lw=1.0, ls=":", zorder=5)
    for p, r in A["lvn1"]:
        if lo <= p <= hi: axp.plot([0, colw], [p, p], color=LVN_C, lw=1.0, ls=":", zorder=5); axp.text(0.02, p + step * 0.3, f"LVN {p:g}", fontsize=6, color=LVN_C, va="bottom")
    for p, r in A["lvn2"]:
        if lo <= p <= hi: axp.plot([1.12, 1.12 + colw], [p, p], color=LVN_C, lw=1.0, ls=":", zorder=5)
    for p, r in A["hvn1"]:
        if lo <= p <= hi: axp.text(0.02, p + step * 0.3, f"HVN {p:g}", fontsize=6, color=HVN_C, va="bottom")
    x = 3.75; wdt = 1.5
    axp.add_patch(plt.Rectangle((x, min(g)), wdt, max(max(g) - min(g), step * 0.6), color=c, alpha=0.18, lw=0, zorder=3))
    axp.plot([x, x + wdt], [t["entry"]] * 2, color=c, lw=1.2, zorder=4); axp.text(x + wdt + 0.05, t["entry"], f"entry {t['entry']:g}", fontsize=7, color=c, va="center", fontweight="bold")
    for tg in t["tgts"]:
        axp.plot([x, x + wdt], [tg] * 2, color=PIVOT, lw=0.9, ls="--", zorder=4); axp.text(x + wdt + 0.05, tg, f"tgt {tg:g}", fontsize=7, color=PIVOT, va="center")
    z = t.get("lvn_zone")
    if z:   # the thin zone the LVN candidate comes from: its full extent, far edge emphasised
        zlo, zhi = max(z["lo"], lo), min(z["hi"], hi)
        for ax_ in (axc, axp): ax_.axhspan(zlo, zhi, color=LVN_C, alpha=0.06, lw=0, zorder=0)
        axp.text(x, zhi - step * 0.2, f"{z['src']} LVN zone {z['lo']:g}–{z['hi']:g}" + (" (void)" if z.get("void") else ""), fontsize=5.8, color=LVN_C, va="top")
    opts_ = t.get("options") or []
    short_lab = {"tight": "tight", "structural": "struct", "swing": "swing", "atr": "ATR", "next_level": "next lvl"}
    for o in opts_:
        y = o["stop"]
        if not (lo <= y <= hi): continue
        axp.plot([x, x + wdt], [y] * 2, color=STOP_C, lw=0.9, ls=":", zorder=4, alpha=0.9)
        lab = short_lab.get(o["key"], o["key"].replace("lvn_", "LVN "))
        axp.text(x - 0.04, y, f"{lab} {y:g}", fontsize=5.8, color=STOP_C, ha="right", va="center", alpha=0.95)
    r_ = s["recommended"]
    axp.plot([x, x + wdt], [r_] * 2, color=STOP_C, lw=2.4, zorder=6)
    sz = f"\n{t['micros']} micro{'s' if t['micros'] != 1 else ''} @ ${t['risk_usd']:g}" if t.get("micros") is not None else ""
    axp.text(x + wdt + 0.05, r_, f"STOP {r_:g}\n{t['risk']:g} pts · {t['risk']/t['atr15']:.2f} ATR" + sz, fontsize=7, color=STOP_C, va="center", fontweight="bold")
    axp.annotate("", xy=(x + wdt / 2, t["tgts"][0]), xytext=(x + wdt / 2, t["entry"]), arrowprops=dict(arrowstyle="-|>", color=c, lw=1.1, ls="--"), zorder=4)
    axp.set_xlim(-0.05, x + wdt + 1.6); axp.set_xticks([])
    for sp in ("top", "right", "bottom", "left"): axp.spines[sp].set_visible(False)
    axp.grid(axis="y", color=GRID, lw=0.5, zorder=0); axp.tick_params(axis="y", length=0)
    axp.set_title("R: " + " / ".join(f"{v}" for v in t["rr"]) + "   ·   volume & stop candidates", loc="left", fontsize=9, color=INK, fontweight="bold", pad=8)
    fig.subplots_adjust(left=0.045, right=0.99, top=0.92, bottom=0.03)
    fig.savefig(out, facecolor="white"); plt.close(fig)


def why_text(c):
    s = c["stop_pts"]; d = c["dir"]; past = "under" if d == "long" else "above"
    w = [f"Entry assumed {c['entry']:g} ({'top' if d == 'long' else 'bottom'} of the gate). Invalidation level {c['structure_level']:g}, buffered {abs(s['structural'] - c['structure_level']):g} pts {past} it → structural {s['structural']:g}."]
    z = c.get("lvn_zone")
    if z and s.get("lvn") is not None:
        w.append(f"Thin volume ({z['src']} profile) runs {z['lo']:g}–{z['hi']:g}, thinnest at {z['min_p']:g} ({z['min_r']:.0%} of peak); the LVN candidate is one tick past its far edge, {s['lvn']:g}, not its minimum.")
    elif z:
        w.append(f"Beyond the entry the {z['src']} profile is a void from {z['lo']:g} to {z['hi']:g} — no far edge to lean on, so the stop stays with structure.")
    else:
        w.append("No sub-35% zone beyond the entry on either profile.")
    w.append(f"Recommended {s['recommended']:g} on {c['basis']}: {c['risk']:g} pts = {c['risk_atr']:.2f} × ATR15" + (" — wider than the 1.3 ATR cap; structure demands it" if c.get("wide") else "") + ".")
    return " ".join(w)


def build(plan_path, levels_path=None, risk_usd=RISK_USD, chart_dir="charts"):
    """Full stop doc for one plan: instruments block + per-trade candidates/sizing + charts.
    levels_path: optional JSON {trade_id: invalidation level} overriding plans' levels.stop (which is often the bigger-picture failure)."""
    plan = json.load(open(plan_path)); date = plan["date"]
    over = json.load(open(levels_path)) if levels_path and pathlib.Path(levels_path).exists() else {}
    syms = sorted({t["instrument"] for t in plan["trades"]})
    A = {s: analyze(s, date) for s in syms}
    inst = {}
    for s in syms:
        a = A[s]
        inst[s] = dict(atr5=round(a["atr5"], 2), atr15=round(a["atr15"], 2), poc1=a["p1"][2], va1=[a["p1"][3], a["p1"][4]], poc2=a["p2"][2], va2=[a["p2"][3], a["p2"][4]],
                       poc3=a["p3"][2], va3=[a["p3"][3], a["p3"][4]], p3_src=a["p3_src"],
                       lvn1=a["lvn1"], hvn1=a["hvn1"], lvn2=a["lvn2"], hvn2=a["hvn2"], lvn3=a["lvn3"], hvn3=a["hvn3"],
                       lvn_zones1=lvn_zones(*a["p1"][:2], a["step"]), lvn_zones2=lvn_zones(*a["p2"][:2], a["step"] * 2), lvn_zones3=lvn_zones(*a["p3"][:2], a["step"] * 2))
    plan_levels = {b["instrument"]: sorted({float(p) for lv in b.get("levels", []) for p in lv["p"]}) for b in plan.get("brief", [])}
    trades = []
    pathlib.Path(chart_dir).mkdir(exist_ok=True)
    for pt in plan["trades"]:
        s = pt["instrument"]
        c = candidates(s, A[s], pt, risk_usd=risk_usd, level=over.get(pt["id"]), plan_levels=plan_levels.get(s, ()))
        c["why"] = why_text(c); c["caveat"] = pt.get("stop", "")
        c["chart_file"] = f"{chart_dir}/stops_{date}_{pt['id']}.png"
        draw_trade2(s, A[s], c, c["chart_file"], charts.load(s), date)
        trades.append(c)
    doc = dict(date=date, instruments=inst, trades=trades, params=dict(buffer_atr5=BUFFER_ATR5, atr_cap=ATR_CAP, lvn_thr=LVN_THR, min_r_first=MIN_R_FIRST, risk_usd=risk_usd))
    out = f"stops_{date}.json"; json.dump(doc, open(out, "w"), indent=1, default=float)
    return doc, out


if __name__ == "__main__":
    plan_path = sys.argv[1]
    lv = sys.argv[2] if len(sys.argv) > 2 else plan_path.replace("plan-", "stop-levels-")
    doc, out = build(plan_path, lv)
    for t in doc["trades"]:
        print(f"{t['id']:4} {t['dir']:5} stop {t['stop_pts']['recommended']:g} ({t['risk']:g} pts, {t['risk_atr']} ATR) R {t['rr']} {t.get('micros')} micro skip={t.get('skip')} {t.get('skip_reason') or ''}")
    print("wrote", out)
