"""Render one annotated candlestick PNG per trade for the PharmD review page.

Usage: python charts.py plan.json outdir
plan.json is the review-page document (source/date/trades[]); each trade may carry
"levels": {"gate":[lo,hi] | [p], "tgt":[...], "stop":[p]} and "instrument": "ES"|"NQ".
Charts show the letter's reference session (the day before plan date) plus overnight
and the plan day's RTH, with a divider at the plan day's open.
"""
import json, sys, pathlib
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

INK, MUTE, GRID = "#15181c", "#6b7280", "#e6e8eb"
UP, DOWN = "#1f8a4c", "#c4383a"
LONG, SHORT, PIVOT = "#1f8a4c", "#c4383a", "#1c4f9c"


def load(sym):
    d = pd.read_csv(f"bars/{sym}_5m.csv")
    d["time"] = pd.to_datetime(d["time"], utc=True).dt.tz_convert("America/New_York")
    return d


def window(d, plan_date, with_overnight=False):
    pd_ = pd.Timestamp(plan_date, tz="America/New_York")
    ref = pd_ - pd.Timedelta(days=1)
    while ref.weekday() > 4:
        ref -= pd.Timedelta(days=1)
    start = (ref - pd.Timedelta(days=1)).replace(hour=18, minute=0) if with_overnight else ref.replace(hour=9, minute=30)
    end = ref.replace(hour=16, minute=0)   # review happens after the reference close; nothing later exists yet
    w = d[(d.time >= start) & (d.time <= end)].set_index("time")
    w = w.resample("15min").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()
    w = w.reset_index()
    return w, ref, pd_


def draw(trade, bars, ref, pday, out):
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=170)
    fig.patch.set_facecolor("white")
    x = range(len(bars))
    for i, r in bars.iterrows():
        c = UP if r.Close >= r.Open else DOWN
        ax.plot([i, i], [r.Low, r.High], color=c, lw=0.6, zorder=2)
        ax.add_patch(Rectangle((i - 0.35, min(r.Open, r.Close)), 0.7,
                               max(abs(r.Close - r.Open), 0.01), color=c, lw=0, zorder=3))
    # session shading + divider
    def idx(ts):
        m = bars.index[bars.time >= ts]
        return int(m[0]) if len(m) else len(bars) - 1
    ax.text(0, ax.get_ylim()[1], f"{ref:%a %-m/%-d} RTH  ·  plan for {pday:%a %-m/%-d}", va="top", fontsize=7, color=MUTE)

    lv = trade.get("levels", {})
    dirc = LONG if trade["dir"] == "long" else SHORT
    n = len(bars)

    def band(vals, color, label, alpha=0.18, ls="-"):
        if not vals:
            return
        if len(vals) == 2:
            ax.axhspan(vals[0], vals[1], color=color, alpha=alpha, lw=0, zorder=1)
            y = (vals[0] + vals[1]) / 2
            txt = f"{label} {vals[0]:g}-{vals[1]:g}"
        else:
            ax.axhline(vals[0], color=color, lw=1.1, ls=ls, zorder=1)
            y = vals[0]
            txt = f"{label} {vals[0]:g}"
        ax.text(n + 1, y, txt, va="center", fontsize=7.5, color=color, fontweight="bold")

    band(lv.get("gate"), dirc, "GATE")
    for t in lv.get("tgt", []):
        band(t if isinstance(t, list) else [t], PIVOT, "tgt", alpha=0.12, ls="--")
    g = lv.get("gate") or []
    if lv.get("stop") and not (g and min(g) - 3 <= lv["stop"][0] <= max(g) + 3):
        band(lv["stop"], MUTE, "fail", ls=":")

    # setup arrow: LBAF hooks below gate then up; LAAF pokes above then down
    if lv.get("gate"):
        g = lv["gate"]
        glo, ghi = (g[0], g[-1])
        span = bars.High.max() - bars.Low.min()
        ax_x = n * 0.97
        if trade["dir"] == "long":
            ax.annotate("", xy=(ax_x, ghi + span * 0.10), xytext=(ax_x, glo - span * 0.05),
                        arrowprops=dict(arrowstyle="-|>", color=LONG, lw=1.6,
                                        connectionstyle="arc3,rad=-0.35"))
        else:
            ax.annotate("", xy=(ax_x, glo - span * 0.10), xytext=(ax_x, ghi + span * 0.05),
                        arrowprops=dict(arrowstyle="-|>", color=SHORT, lw=1.6,
                                        connectionstyle="arc3,rad=-0.35"))

    # axes cosmetics
    ticks = [i for i, t in enumerate(bars.time) if t.minute == 0]
    ax.set_xticks(ticks)
    ax.set_xticklabels([bars.time[i].strftime("%H") for i in ticks], fontsize=7, color=MUTE)
    ax.tick_params(axis="y", labelsize=7, colors=MUTE)
    ax.set_xlim(-1, n + 1)
    lo, hi = bars.Low.min(), bars.High.max()
    allv = [v for k in ("gate", "stop") for v in (lv.get(k) or [])] + [v for t in lv.get("tgt", []) for v in (t if isinstance(t, list) else [t])]
    lo = min([lo] + allv); hi = max([hi] + allv)
    pad = (hi - lo) * 0.06
    ax.set_ylim(lo - pad, hi + pad)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    title = f"{trade['instrument']}  {trade['name']}  ·  {trade['dir']}  ·  {trade.get('tag','')}"
    ax.set_title(title, loc="left", fontsize=9.5, color=INK, fontweight="bold", pad=8)
    fig.subplots_adjust(left=0.08, right=0.80, top=0.90, bottom=0.10)
    fig.savefig(out, facecolor="white")
    plt.close(fig)


def main(plan_path, outdir):
    plan = json.load(open(plan_path))
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    data = {s: load(s) for s in ("ES", "NQ")}
    for t in plan["trades"]:
        sym = t.get("instrument") or ("NQ" if t["id"].startswith("nq") else "ES")
        t["instrument"] = sym
        bars, ref, pday = window(data[sym], plan["date"])
        out = outdir / f"{plan['date']}_{t['id']}.png"
        draw(t, bars, ref, pday, out)
        print(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])


# ---------- volume profile from 5-min bars (volume spread evenly across each bar's range) ----------
def profile(d5, start, end, step):
    import numpy as np
    w = d5[(d5.time >= start) & (d5.time < end)]
    lo = np.floor(w.Low.min() / step) * step; hi = np.ceil(w.High.max() / step) * step
    edges = np.arange(lo, hi + step, step); vol = np.zeros(len(edges) - 1)
    for _, r in w.iterrows():
        a, b = r.Low, r.High
        if b <= a: b = a + step * 0.01
        for i in range(len(vol)):
            ov = max(0, min(b, edges[i+1]) - max(a, edges[i]))
            if ov > 0: vol[i] += r.Volume * ov / (b - a)
    poc = edges[vol.argmax()] + step / 2
    # value area: expand from POC until 70% of volume
    order = [vol.argmax()]; total = vol.sum(); acc = vol[order[0]]; lo_i = hi_i = order[0]
    while acc < 0.7 * total:
        up = vol[hi_i+1] if hi_i + 1 < len(vol) else -1; dn = vol[lo_i-1] if lo_i - 1 >= 0 else -1
        if up >= dn: hi_i += 1; acc += up
        else: lo_i -= 1; acc += dn
    return edges, vol, poc, edges[lo_i], edges[hi_i+1]


# ---------- roadmap chart: one per instrument, all key levels ----------
def roadmap(sym, levels, bars, ref, pday, out, d5=None):
    """levels: list of {p:[lo,hi]|[p], label, kind: up|down|pivot|ref}"""
    fig, ax = plt.subplots(figsize=(8.8, 6.0), dpi=170)
    fig.patch.set_facecolor("white")
    for i, r in bars.iterrows():
        c = UP if r.Close >= r.Open else DOWN
        ax.plot([i, i], [r.Low, r.High], color=c, lw=0.6, zorder=2)
        ax.add_patch(Rectangle((i - 0.35, min(r.Open, r.Close)), 0.7,
                               max(abs(r.Close - r.Open), 0.01), color=c, lw=0, zorder=3))
    n = len(bars)
    m = bars.index[bars.time >= ref.replace(hour=9, minute=30)]
    rth0 = int(m[0]) if len(m) else 0
    if rth0 > 0:
        ax.axvspan(-1, rth0 - 0.5, color="#f3f4f2", zorder=0)
        ax.text(rth0 / 2, bars.High.max(), "overnight", ha="center", va="bottom", fontsize=7, color=MUTE)
    col = {"up": LONG, "down": SHORT, "pivot": PIVOT, "ref": MUTE}
    labels = []
    for L in levels:
        p, c = L["p"], col[L["kind"]]
        strong = L["kind"] == "pivot"
        if len(p) == 2:
            ax.axhspan(p[0], p[1], color=c, alpha=0.22 if strong else 0.12, lw=0, zorder=1)
            y = (p[0] + p[1]) / 2; txt = f"{p[0]:g}-{p[1]:g}  {L['label']}"
        else:
            ax.axhline(p[0], color=c, lw=1.3 if strong else 0.9, ls="-" if strong else "--", zorder=1)
            y = p[0]; txt = f"{p[0]:g}  {L['label']}"
        labels.append([y, txt, c, strong])
    # push labels apart so none overlap (min gap = 2.6% of the plotted range)
    allv0 = [v for L in levels for v in L["p"]]
    rng = max([bars.High.max()] + allv0) - min([bars.Low.min()] + allv0)
    gap = rng * 0.026
    labels.sort(key=lambda l: l[0])
    for i in range(1, len(labels)):
        if labels[i][0] - labels[i-1][0] < gap:
            labels[i][0] = labels[i-1][0] + gap
    for y, txt, c, strong in labels:
        ax.text(n + 1, y, txt, va="center", fontsize=7, color=c, fontweight="bold" if strong else "normal")
    prof_w = 0
    prof_lo, prof_hi = [], []
    if d5 is not None:
        step = 1.0 if sym == "ES" else 5.0
        end = ref.replace(hour=16, minute=0)
        def sess_start(days_back):
            t = ref
            for _ in range(days_back):
                t -= pd.Timedelta(days=1)
                while t.weekday() > 4: t -= pd.Timedelta(days=1)
            return t.replace(hour=18, minute=0)
        specs = [("1-day", bars.time.iloc[0]), ("3-day", sess_start(3))]
        colw = n * 0.2; gapw = n * 0.035; x0 = n + 1.5
        for label, start in specs:
            edges, vol, poc, valo, vahi = profile(d5, start, end, step)
            prof_lo.append(edges[0]); prof_hi.append(edges[-1])
            scale = colw / vol.max()
            for i in range(len(vol)):
                inva = valo <= edges[i] < vahi
                ax.barh(edges[i], vol[i] * scale, height=step, left=x0, align="edge",
                        color="#8b96a3" if inva else "#c9ced4", alpha=0.75 if inva else 0.5, lw=0, zorder=2)
            ax.plot([x0, x0 + colw], [poc, poc], color="#b7791f", lw=1.6, zorder=4)
            ax.text(x0 + 0.5, poc + step * 0.6, f"{poc:g}", va="bottom", fontsize=6.2, color="#b7791f", fontweight="bold")
            ax.text(x0 + colw / 2, edges[-1] + step * 0.8, label, ha="center", va="bottom", fontsize=6.5, color=MUTE)
            ax.text(x0 + colw / 2, edges[0] - step * 0.8, f"VA {valo:g}-{vahi:g}", ha="center", va="top", fontsize=5.6, color=MUTE)
            x0 += colw + gapw
        prof_w = x0 - (n + 1.5)
        for t in ax.texts:
            if t.get_position()[0] == n + 1: t.set_x(n + 1.5 + prof_w + 1)
    ticks = [i for i, t in enumerate(bars.time) if t.minute == 0 and t.hour % 2 == 0]
    ax.set_xticks(ticks); ax.set_xticklabels([bars.time[i].strftime("%H") for i in ticks], fontsize=7, color=MUTE)
    ax.tick_params(axis="y", labelsize=7, colors=MUTE)
    ax.set_xlim(-1, n + 1.5 + prof_w + 1)
    allv = [v for L in levels for v in L["p"]]
    lo, hi = min([bars.Low.min()] + allv + prof_lo), max([bars.High.max()] + allv + prof_hi)
    pad = (hi - lo) * 0.035; ax.set_ylim(lo - pad, hi + pad)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
    ax.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    ax.set_title(f"{sym} roadmap  ·  {ref:%a %-m/%-d} RTH  ·  plan for {pday:%a %-m/%-d}", loc="left", fontsize=9.5, color=INK, fontweight="bold", pad=8)
    fig.subplots_adjust(left=0.065, right=0.74, top=0.93, bottom=0.07)
    fig.savefig(out, facecolor="white"); plt.close(fig)


def main_roadmaps(plan_path, outdir):
    plan = json.load(open(plan_path))
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    for b in plan.get("brief", []):
        sym = b["instrument"]
        d5 = load(sym)
        bars, ref, pday = window(d5, plan["date"], with_overnight=True)
        out = outdir / f"{plan['date']}_{sym}_roadmap.png"
        roadmap(sym, b["levels"], bars, ref, pday, out, d5=d5); print(out)


# ---------- weekly chart: multi-day candles, weekly ladder, week profile ----------
def weekly(sym, levels, d5, start, end, out, title, profile_ranges=None, marks=None):
    """levels: [{p, label, kind, strong?}]; marks: [{t: timestamp, y, label}] point annotations."""
    w = d5[(d5.time >= start) & (d5.time <= end)].set_index("time")
    bars = w.resample("30min").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna().reset_index()
    n = len(bars)
    fig, ax = plt.subplots(figsize=(10.5, 6.4), dpi=170); fig.patch.set_facecolor("white")
    # shade non-RTH
    rth = [(9*60+30 <= t.hour*60+t.minute < 16*60) for t in bars.time]
    i = 0
    while i < n:
        if not rth[i]:
            j = i
            while j < n and not rth[j]: j += 1
            ax.axvspan(i - 0.5, j - 0.5, color="#f3f4f2", zorder=0); i = j
        else: i += 1
    for i, r in bars.iterrows():
        c = UP if r.Close >= r.Open else DOWN
        ax.plot([i, i], [r.Low, r.High], color=c, lw=0.6, zorder=2)
        ax.add_patch(Rectangle((i - 0.35, min(r.Open, r.Close)), 0.7, max(abs(r.Close - r.Open), 0.01), color=c, lw=0, zorder=3))
    # day labels at each RTH open
    for i, t in enumerate(bars.time):
        if t.hour == 9 and t.minute == 30:
            ax.text(i, ax.get_ylim()[0], t.strftime("%a %-m/%-d"), fontsize=7, color=MUTE, ha="left", va="bottom")
    col = {"up": LONG, "down": SHORT, "pivot": PIVOT, "ref": MUTE}
    labels = []
    for L in levels:
        p, c = L["p"], col[L["kind"]]; strong = L.get("strong") or L["kind"] == "pivot"
        if len(p) == 2:
            ax.axhspan(p[0], p[1], color=c, alpha=0.24 if strong else 0.11, lw=0, zorder=1)
            y = (p[0] + p[1]) / 2; txt = f"{p[0]:g}-{p[1]:g}{'*' if L.get('strong') else ''}  {L['label']}"
        else:
            ax.axhline(p[0], color=c, lw=1.3 if strong else 0.9, ls="-" if strong else "--", zorder=1)
            y = p[0]; txt = f"{p[0]:g}  {L['label']}"
        labels.append([y, txt, c, strong])
    # profile(s)
    prof_w = 0; plo, phi = [], []
    if profile_ranges:
        step = 1.0 if sym == "ES" else 5.0
        colw = n * 0.13; gapw = n * 0.03; x0 = n + 1.5
        for label, ps, pe in profile_ranges:
            edges, vol, poc, valo, vahi = profile(d5, ps, pe, step)
            plo.append(edges[0]); phi.append(edges[-1]); scale = colw / vol.max()
            for i in range(len(vol)):
                inva = valo <= edges[i] < vahi
                ax.barh(edges[i], vol[i] * scale, height=step, left=x0, align="edge", color="#8b96a3" if inva else "#c9ced4", alpha=0.75 if inva else 0.5, lw=0, zorder=2)
            ax.plot([x0, x0 + colw], [poc, poc], color="#b7791f", lw=1.6, zorder=4)
            ax.text(x0 + 0.5, poc + step * 0.6, f"{poc:g}", va="bottom", fontsize=6.2, color="#b7791f", fontweight="bold")
            ax.text(x0 + colw / 2, edges[-1] + step * 0.8, label, ha="center", va="bottom", fontsize=6.5, color=MUTE)
            ax.text(x0 + colw / 2, edges[0] - step * 0.8, f"VA {valo:g}-{vahi:g}", ha="center", va="top", fontsize=5.6, color=MUTE)
            x0 += colw + gapw
        prof_w = x0 - (n + 1.5)
    allv = [v for L in levels for v in L["p"]] + plo + phi
    lo, hi = min([bars.Low.min()] + allv), max([bars.High.max()] + allv)
    rng = hi - lo; gap = rng * 0.022
    labels.sort(key=lambda l: l[0])
    for i in range(1, len(labels)):
        if labels[i][0] - labels[i-1][0] < gap: labels[i][0] = labels[i-1][0] + gap
    for y, txt, c, strong in labels:
        ax.text(n + 1.5 + prof_w + 1, y, txt, va="center", fontsize=6.8, color=c, fontweight="bold" if strong else "normal")
    for m in (marks or []):
        idx = bars.index[bars.time >= m["t"]]
        if len(idx):
            xi = int(idx[0]); ax.annotate(m["label"], xy=(xi, m["y"]), xytext=(xi + m.get("dx", 6), m["y"] + m.get("dy", rng * 0.04)),
                fontsize=6.8, color=INK, arrowprops=dict(arrowstyle="-", color=INK, lw=0.7), ha="left", va="center",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=GRID, lw=0.6))
    pad = rng * 0.035; ax.set_ylim(lo - pad, hi + pad)
    ax.set_xlim(-1, n + 1.5 + prof_w + 1)
    ax.set_xticks([]); ax.tick_params(axis="y", labelsize=7, colors=MUTE)
    for s in ("top", "right", "bottom"): ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(GRID); ax.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    ax.set_title(title, loc="left", fontsize=9.5, color=INK, fontweight="bold", pad=8)
    fig.subplots_adjust(left=0.06, right=0.76, top=0.93, bottom=0.04)
    fig.savefig(out, facecolor="white"); plt.close(fig)
