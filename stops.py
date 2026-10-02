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
    """Per-trade chart with structure: candles (15m, last N sessions) + swing points + profiles + stop column."""
    e1, v1, poc1, va1lo, va1hi = A["p1"]; e2, v2, poc2, va2lo, va2hi = A["p2"]; step = A["step"]
    s = t["stop_pts"]; c = LONG if t["dir"] == "long" else SHORT
    end = pd.Timestamp(plan_date, tz=tz) - pd.Timedelta(hours=7)
    start = (end - pd.Timedelta(days=sessions + 1)).replace(hour=18, minute=0)
    w = d5[(d5.time >= start) & (d5.time <= end)].set_index("time")
    bars = w.resample("15min").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna().reset_index()
    n = len(bars)
    ys = [t["entry"], s["structural"], s["lvn"], s["atr"], s["recommended"]] + list(t["tgts"]) + list(t["gate_pts"])
    pad = (max(ys) - min(ys)) * 0.15 + step * 2
    lo, hi = min(ys) - pad, max(ys) + pad
    fig, (axc, axp) = plt.subplots(1, 2, figsize=(10.4, 5.4), dpi=170, gridspec_kw=dict(width_ratios=[2.1, 1.9], wspace=0.04), sharey=True)
    fig.patch.set_facecolor("white")
    # ---- candles ----
    rth = [(9*60+30 <= x.hour*60+x.minute < 16*60) for x in bars.time]
    i = 0
    while i < n:
        if not rth[i]:
            j = i
            while j < n and not rth[j]: j += 1
            axc.axvspan(i - 0.5, j - 0.5, color="#f3f4f2", zorder=0); i = j
        else: i += 1
    for i, r in bars.iterrows():
        cc = charts.UP if r.Close >= r.Open else charts.DOWN
        axc.plot([i, i], [r.Low, r.High], color=cc, lw=0.6, zorder=2)
        axc.add_patch(plt.Rectangle((i - 0.35, min(r.Open, r.Close)), 0.7, max(abs(r.Close - r.Open), step * 0.1), color=cc, lw=0, zorder=3))
    seen = set()
    for i, x in enumerate(bars.time):
        if rth[i] and x.date() not in seen:
            seen.add(x.date()); axc.text(i, lo + step * 0.3, x.strftime("%a %-m/%-d"), fontsize=6.5, color=MUTE, va="bottom")
    # swings: mark the ones within the window and near the trade
    sh, sl = swings(bars, k=6)
    rel = sl if t["dir"] == "long" else sh
    band = (s["recommended"] - step * 6, t["entry"] + step * 6) if t["dir"] == "long" else (t["entry"] - step * 6, s["recommended"] + step * 6)
    for i, y in rel:
        if band[0] <= y <= band[1]:
            axc.plot(i, y, marker="v" if t["dir"] == "long" else "^", color=c, ms=4, zorder=5)
            axc.annotate(f"{y:g}", (i, y), xytext=(0, -8 if t["dir"] == "long" else 8), textcoords="offset points", ha="center", va="top" if t["dir"] == "long" else "bottom", fontsize=5.8, color=c)
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
    axc.text(n - 0.5, s["recommended"], f" stop {s['recommended']:g}", fontsize=6.8, color=STOP_C, va="bottom" if t["dir"] == "long" else "top", ha="right", fontweight="bold", zorder=7)
    axc.set_xlim(-0.5, n + 0.5); axc.set_ylim(lo, hi)
    axc.set_xticks([]); axc.tick_params(axis="y", labelsize=7, colors=MUTE)
    for sp in ("top", "right", "bottom"): axc.spines[sp].set_visible(False)
    axc.spines["left"].set_color(GRID); axc.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    axc.set_title(f"{sym}  {t['short']}  ·  {t['dir']}  ·  structure (15m, last {sessions} sessions)", loc="left", fontsize=9, color=INK, fontweight="bold", pad=8)
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
    for p, r in A["lvn1"]:
        if lo <= p <= hi: axp.plot([0, colw], [p, p], color=LVN_C, lw=1.0, ls=":", zorder=5); axp.text(0.02, p + step * 0.3, f"LVN {p:g}", fontsize=6, color=LVN_C, va="bottom")
    for p, r in A["lvn2"]:
        if lo <= p <= hi: axp.plot([1.12, 1.12 + colw], [p, p], color=LVN_C, lw=1.0, ls=":", zorder=5)
    for p, r in A["hvn1"]:
        if lo <= p <= hi: axp.text(0.02, p + step * 0.3, f"HVN {p:g}", fontsize=6, color=HVN_C, va="bottom")
    x = 2.45; wdt = 1.5
    axp.add_patch(plt.Rectangle((x, min(g)), wdt, max(max(g) - min(g), step * 0.6), color=c, alpha=0.18, lw=0, zorder=3))
    axp.plot([x, x + wdt], [t["entry"]] * 2, color=c, lw=1.2, zorder=4); axp.text(x + wdt + 0.05, t["entry"], f"entry {t['entry']:g}", fontsize=7, color=c, va="center", fontweight="bold")
    for tg in t["tgts"]:
        axp.plot([x, x + wdt], [tg] * 2, color=PIVOT, lw=0.9, ls="--", zorder=4); axp.text(x + wdt + 0.05, tg, f"tgt {tg:g}", fontsize=7, color=PIVOT, va="center")
    cands = [("structural", s["structural"]), ("LVN", s["lvn"]), (f"{t['atr_mult']}×ATR", s["atr"])]
    for i, (lab, y) in enumerate(cands):
        axp.plot([x + i * wdt / 3, x + (i + 1) * wdt / 3], [y] * 2, color=STOP_C, lw=1.0, ls=":", zorder=4)
        axp.text(x + (i + 0.5) * wdt / 3, y + (step * 0.6 if t["dir"] == "short" else -step * 0.6), lab, fontsize=5.8, color=STOP_C, ha="center", va="bottom" if t["dir"] == "short" else "top")
    r_ = s["recommended"]
    axp.plot([x, x + wdt], [r_] * 2, color=STOP_C, lw=2.4, zorder=6)
    axp.text(x + wdt + 0.05, r_, f"STOP {r_:g}\n{t['risk']:g} pts · {t['risk']/t['atr15']:.2f} ATR", fontsize=7, color=STOP_C, va="center", fontweight="bold")
    axp.annotate("", xy=(x + wdt / 2, t["tgts"][0]), xytext=(x + wdt / 2, t["entry"]), arrowprops=dict(arrowstyle="-|>", color=c, lw=1.1, ls="--"), zorder=4)
    axp.set_xlim(-0.05, x + wdt + 1.6); axp.set_xticks([])
    for sp in ("top", "right", "bottom", "left"): axp.spines[sp].set_visible(False)
    axp.grid(axis="y", color=GRID, lw=0.5, zorder=0); axp.tick_params(axis="y", length=0)
    axp.set_title("R: " + " / ".join(f"{v}" for v in t["rr"]) + "   ·   volume & stop candidates", loc="left", fontsize=9, color=INK, fontweight="bold", pad=8)
    fig.subplots_adjust(left=0.06, right=0.99, top=0.91, bottom=0.04)
    fig.savefig(out, facecolor="white"); plt.close(fig)
