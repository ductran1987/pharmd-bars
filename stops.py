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


def atr(d5, sessions_back=3):
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
    e1, v1, poc1, va1lo, va1hi = charts.profile(d5, w1, end, step)
    e2, v2, poc2, va2lo, va2hi = charts.profile(d1, w2, end, step * 2)
    lv1, hv1 = nodes(e1, v1, step); lv2, hv2 = nodes(e2, v2, step * 2)
    a5, a15 = atr(d5)
    return dict(step=step, p1=(e1, v1, poc1, va1lo, va1hi), p2=(e2, v2, poc2, va2lo, va2hi),
                lvn1=lv1, hvn1=hv1, lvn2=lv2, hvn2=hv2, atr5=a5, atr15=a15, w1=w1, w2=w2, end=end)


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
