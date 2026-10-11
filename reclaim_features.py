"""What separates a real look-below-and-fail (reclaim -> target) from a breakdown that keeps going?  And do the stops fit?

    python reclaim_features.py [dir with *_bars_1m.parquet]  -> reclaim_features.csv, reclaim_features_summary.md

EVENTS (all PharmD fade setups with 1m coverage, graded + ungraded; long described, shorts mirrored):
  touch = first 5m bar trading at the near edge; lost = first 5m close past the FAR edge after it;
  reclaim = first 5m close back through the NEAR edge after that (the best idealized variant in bounce_vs_reclaim).
  Trade: market at the reclaim close (+2 ticks), his stop (1 tick past the sweep, floor 1.5 ATR5), BE 1R, first target
  >= 1.5R, flat 15:55 — exactly bounce_vs_reclaim.reclaim_trade(r, 'near', 'close').  Also the idealized edge fill.
  win_T1 = first target reached before price takes out the sweep low.
FEATURES — use only data up to the reclaim bar's close (1m bars with bid/ask volume, delta signed in the trade direction):
  depth_atr5      how far the sweep went past the far edge, in ATR5
  mins_flush      minutes from the touch to the sweep low;  mins_reclaim: sweep low -> reclaim close
  mins_below      minutes between the lost close and the reclaim close
  flush_delta     net delta / volume from the touch to the sweep-low minute (negative = sellers drove it)
  reclaim_delta   net delta / volume from after the sweep-low minute to the reclaim close
  delta_swing     reclaim_delta - flush_delta
  cvd_div         (CVD at the sweep-low minute - lowest CVD before it) / flush volume  (> 0: delta bottomed before price = divergence)
  low_vol_share   volume of the 3 minutes around the sweep low / flush volume (capitulation / absorption at the low)
  rel_vol         volume per minute touch->reclaim / volume per minute in the 60 min before the touch
  rbar_delta      delta / volume of the 5m reclaim bar;  rbar_pos: where it closed in its range (1 = high)
  chase_atr5      reclaim close past the near edge (the cost of entering at market)
  width_atr5, room_R (first target distance / risk), hour (ET of the reclaim), rth (09:30-16:00), grade, sym
STOPS: for the bounce entry (limit at the near edge) and for the reclaim entry, how far past the zone / sweep the eventual
  winners went, in points and ATR5, and the market-fill P&L of the reclaim under different stop rules.
"""
import sys
import numpy as np, pandas as pd
import backtest_grid as bg, limit_test
from bounce_vs_reclaim import mirror, first, sim, reclaim_trade
from bounce_1m import load_1m
import contracts

TICK = bg.TICK; tz = "America/New_York"; SPLIT = "2026-06-09"


def window_1m(r, m1):
    t0 = pd.Timestamp(r["ts"][0]); t_end = pd.Timestamp(r["date"], tz=tz).replace(hour=16)
    x = m1[r["sym"]]
    a, b = x.time.searchsorted(t0 - pd.Timedelta(minutes=60)), x.time.searchsorted(t_end)
    w = x.iloc[a:b]; w = w[w.contract == contracts.norm(r["contract"])]
    s = w[w.time >= t0]
    if len(s) < 30 or s.time.iloc[0] > t0 + pd.Timedelta(minutes=30) or s.time.iloc[-1] < t_end - pd.Timedelta(minutes=10): return None
    return w


def event(r, m1):
    up, sg, near, far, O, H, L, C, tg = mirror(r)
    if O[0] <= near: return None
    j_t = first(L <= near)
    if j_t is None: return None
    j_l = first(C < far, j_t)
    if j_l is None: return None
    j_r = first(C > near, j_l + 1)
    if j_r is None or j_r + 1 >= len(C): return None
    w = window_1m(r, m1)
    if w is None: return None
    ts5 = pd.to_datetime(r["ts"])
    t_touch, t_rc = ts5[j_t], ts5[j_r] + pd.Timedelta(minutes=5)
    pre = w[(w.time >= t_touch - pd.Timedelta(minutes=60)) & (w.time < t_touch)]
    ev = w[(w.time >= t_touch) & (w.time < t_rc)]
    if len(ev) < 3: return None
    lo = (ev.low.values if up else -ev.high.values)
    d = ev.delta.values * sg; v = ev.vol.values.astype(float)
    k = int(np.argmin(lo))                                   # sweep-low minute
    sweep = L[j_t:j_r + 1].min()
    cvd = np.cumsum(d)
    fv, rv = v[:k + 1].sum(), v[k + 1:].sum()
    mins = lambda a, b: (b - a) / pd.Timedelta(minutes=1)
    tk = ev.time.iloc[k]
    rb = ev[ev.time >= ts5[j_r]]
    rbH, rbL = H[j_r], L[j_r]
    tr = reclaim_trade(r, "near", "close"); te = reclaim_trade(r, "near", "edge")
    if tr is None: return None
    t1s = [x for x in tg if x > near]
    T1 = t1s[0] if t1s else None
    jw = first(H >= T1, j_r + 1) if T1 is not None else None
    jf = first(L < sweep, j_r + 1)
    win = jw is not None and (jf is None or jw < jf)
    # after entry: how far did price go back down before the first target (for stop sizing)
    end = jw if jw is not None else len(L) - 1
    mae_low = L[j_r + 1:end + 1].min() if end >= j_r + 1 else C[j_r]
    return dict(date=r["date"], id=r["id"], sym=r["sym"], dir=r["dir"], grade=r["grade"] or "U", graded=r["graded"],
                atr5=r["atr5"], width_atr5=(near - far) / r["atr5"],
                depth_atr5=(far - sweep) / r["atr5"], depth_pts=far - sweep,
                mins_flush=mins(t_touch, tk), mins_reclaim=mins(tk, t_rc), mins_below=(j_r - j_l) * 5,
                flush_delta=d[:k + 1].sum() / max(fv, 1), reclaim_delta=d[k + 1:].sum() / max(rv, 1) if rv > 0 else 0.0,
                cvd_div=(cvd[k] - cvd[:k + 1].min()) / max(fv, 1),
                low_vol_share=v[max(0, k - 1):k + 2].sum() / max(v.sum(), 1),
                rel_vol=(v.sum() / max(len(ev), 1)) / max(pre.vol.sum() / max(len(pre), 1), 1),
                rbar_delta=(rb.delta.values * sg).sum() / max(rb.vol.sum(), 1),
                rbar_pos=(C[j_r] - rbL) / max(rbH - rbL, TICK),
                chase_atr5=(C[j_r] - near) / r["atr5"], room_R=tr["R_to_tgt"],
                hour=ts5[j_r].hour + ts5[j_r].minute / 60, rth=int(9.5 <= ts5[j_r].hour + ts5[j_r].minute / 60 < 16),
                win_T1=int(win), R=tr["R"], R_edge=te["R"] if te else np.nan, exit=tr["exit"], risk_atr5=tr["risk_pts"] / r["atr5"],
                entry=C[j_r], sweep=sweep, mae_past_sweep_atr5=(sweep - mae_low) / r["atr5"],
                mae_from_entry_atr5=(C[j_r] - mae_low) / r["atr5"], reached_T1=int(jw is not None))


FEATS = ["depth_atr5", "mins_flush", "mins_reclaim", "mins_below", "flush_delta", "reclaim_delta", "delta_swing", "cvd_div",
         "low_vol_share", "rel_vol", "rbar_delta", "rbar_pos", "chase_atr5", "width_atr5", "room_R", "hour"]


def terciles(df, f):
    q = df[f].quantile([1 / 3, 2 / 3]).values
    b = np.where(df[f] <= q[0], 0, np.where(df[f] <= q[1], 1, 2))
    return b, q


def main(d1m):
    m1 = load_1m(d1m)
    recs = limit_test.collect()
    E = pd.DataFrame([e for e in (event(r, m1) for r in recs) if e is not None])
    E["delta_swing"] = E.reclaim_delta - E.flush_delta
    E["half"] = np.where(E.date <= SPLIT, "H1", "H2")
    E.to_csv("reclaim_features.csv", index=False)
    out = []; P = lambda s="": (print(s), out.append(s))
    P("# What makes a look-below-and-fail work — and do the stops fit?\n")
    P(f"{len(E)} fail-and-reclaim events (5m close past the far edge, then 5m close back through the near edge) on "
      f"{E.date.nunique()} days, graded + ungraded, with 1m order-flow data. Base: T1-before-new-low {E.win_T1.mean():.0%}, "
      f"market-fill avg {E.R.mean():+.2f}R, idealized edge fill {E.R_edge.mean():+.2f}R. H1 n={int((E.half=='H1').sum())}, H2 n={int((E.half=='H2').sum())}.\n")
    P("## Each measurement split into thirds (low / mid / high) — win% = T1 before a new low; R = market fill\n")
    P("A feature is only useful if the same third wins in BOTH halves. ✓ = the best third beats the worst by ≥ 10 pts of "
      "win% and ≥ 0.15R in both H1 and H2.\n")
    P("| feature | cut points | low third win% / R | mid | high | H1 low→high R | H2 low→high R | stable |\n|---|---|---|---|---|---|---|---|")
    stable = []
    for f in FEATS:
        b, q = terciles(E, f)
        cells = [f"{E.win_T1[b == i].mean():.0%} / {E.R[b == i].mean():+.2f}" for i in range(3)]
        hh = {}
        for h in ("H1", "H2"):
            m = (E.half == h).values
            hh[h] = [E.R[(b == i) & m].mean() for i in range(3)], [E.win_T1[(b == i) & m].mean() for i in range(3)]
        best = int(np.argmax([E.R[b == i].mean() for i in range(3)])); worst = int(np.argmin([E.R[b == i].mean() for i in range(3)]))
        ok = all(hh[h][0][best] - hh[h][0][worst] >= 0.15 and hh[h][1][best] - hh[h][1][worst] >= 0.10 for h in hh)
        if ok: stable.append((f, best, q))
        P(f"| {f} | {q[0]:.2f} / {q[1]:.2f} | " + " | ".join(cells) +
          f" | {' → '.join(f'{x:+.2f}' for x in hh['H1'][0])} | {' → '.join(f'{x:+.2f}' for x in hh['H2'][0])} | {'✓' if ok else ''} |")
    P()
    for f, lab in (("grade", "grade"), ("sym", "instrument"), ("rth", "RTH (1) vs overnight (0)")):
        P(f"**By {lab}:** " + " · ".join(f"{k}: n {len(g)}, win {g.win_T1.mean():.0%}, {g.R.mean():+.2f}R (H1 {g[g.half=='H1'].R.mean():+.2f} / H2 {g[g.half=='H2'].R.mean():+.2f})"
                                         for k, g in E.groupby(f)) + "\n")

    # combined score: logistic regression trained on H1 only, tested on H2
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    X = E[FEATS + ["rth"]].fillna(0).values; y = (E.R > 0).astype(int).values
    tr_m = (E.half == "H1").values
    sc = StandardScaler().fit(X[tr_m]); lr = LogisticRegression(C=0.3, max_iter=2000).fit(sc.transform(X[tr_m]), y[tr_m])
    E["score"] = lr.predict_proba(sc.transform(X))[:, 1]
    P("## Combined score (logistic regression on all measurements, fit on H1 only, judged on H2)\n")
    coefs = sorted(zip(FEATS + ["rth"], lr.coef_[0]), key=lambda z: -abs(z[1]))
    P("Weights (standardized; + = more likely to win): " + ", ".join(f"{f} {c:+.2f}" for f, c in coefs[:8]) + "\n")
    P("| H2 events ranked by the H1 score | n | win% | avg R (market) | avg R (edge fill) |\n|---|---|---|---|---|")
    h2 = E[E.half == "H2"].copy(); h2["q"] = pd.qcut(h2.score, 3, labels=["bottom third", "middle third", "top third"])
    for k, g in h2.groupby("q", observed=True):
        P(f"| {k} | {len(g)} | {g.win_T1.mean():.0%} | {g.R.mean():+.2f} | {g.R_edge.mean():+.2f} |")
    P(f"| all H2 | {len(h2)} | {h2.win_T1.mean():.0%} | {h2.R.mean():+.2f} | {h2.R_edge.mean():+.2f} |\n")

    # ---------------- stops
    P("## Do the stops fit the overshoot?\n")
    P("### Reclaim entry: after buying the reclaim, how far did eventual WINNERS (reached T1) come back down first?\n")
    W = E[E.reached_T1 == 1]
    P("| | n | median | 75th pct | 90th pct |\n|---|---|---|---|---|")
    for s in ("ES", "NQ"):
        g = W[W.sym == s]
        P(f"| {s}: pullback from entry, ATR5 | {len(g)} | {g.mae_from_entry_atr5.median():.2f} | {g.mae_from_entry_atr5.quantile(.75):.2f} | {g.mae_from_entry_atr5.quantile(.9):.2f} |")
        pts = g.mae_from_entry_atr5 * g.atr5
        P(f"| {s}: same, points | | {pts.median():.1f} | {pts.quantile(.75):.1f} | {pts.quantile(.9):.1f} |")
        P(f"| {s}: ATR5 itself, points | | {g.atr5.median():.1f} | | |")
    P(f"\nWinners that went back below the sweep low before T1: {(W.mae_past_sweep_atr5 > 0).mean():.0%}. "
      f"His stop (tick past sweep, floor 1.5 ATR5) sits a median {E.risk_atr5.median():.2f} ATR5 from the market entry.\n")
    surv = lambda k: (W.mae_from_entry_atr5 < k).mean()
    P("Share of eventual winners a stop k × ATR5 below the market entry would have kept: " +
      " · ".join(f"{k}: {surv(k):.0%}" for k in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0)) + "\n")
    P("### Reclaim entry P&L under different stops (market fill, everything else unchanged)\n")
    P("| stop | n | win% | avg R | H1 | H2 | PF |\n|---|---|---|---|---|---|---|")
    pairs = [(r, e) for r in recs for e in [None]]
    keyed = {(r["date"], r["id"]): r for r in recs}
    for name, fn in [("tick past sweep only", lambda e, sw, a: sw - TICK),
                     ("his rule: sweep, floor 1.0 ATR5", lambda e, sw, a: min(sw - TICK, e - 1.0 * a)),
                     ("his rule: sweep, floor 1.5 ATR5 (current)", lambda e, sw, a: min(sw - TICK, e - 1.5 * a)),
                     ("sweep, floor 2.0 ATR5", lambda e, sw, a: min(sw - TICK, e - 2.0 * a)),
                     ("sweep, floor 2.5 ATR5", lambda e, sw, a: min(sw - TICK, e - 2.5 * a)),
                     ("sweep, floor 3.0 ATR5", lambda e, sw, a: min(sw - TICK, e - 3.0 * a)),
                     ("sweep − 0.25 ATR5", lambda e, sw, a: sw - 0.25 * a),
                     ("sweep − 0.5 ATR5", lambda e, sw, a: sw - 0.5 * a),
                     ("sweep − 1.0 ATR5", lambda e, sw, a: sw - 1.0 * a)]:
        rows = []
        for _, ev in E.iterrows():
            r = keyed[(ev.date, ev.id)]
            up, sg, near, far, O, H, L, C, tg = mirror(r)
            j_t = first(L <= near); j_l = first(C < far, j_t); j_r = first(C > near, j_l + 1)
            e = C[j_r]; stp = fn(e, ev.sweep, r["atr5"])
            s = sim(r, e, stp, j_r + 1, H, L, O, C, sg, limit_fill=False)
            if s: rows.append(dict(R=s["R"], pnl=s["pnl"], half=ev.half))
        d = pd.DataFrame(rows); w_ = d[d.pnl > 0].pnl.sum(); l_ = -d[d.pnl < 0].pnl.sum()
        P(f"| {name} | {len(d)} | {(d.pnl > 0).mean():.0%} | {d.R.mean():+.2f} | {d[d.half=='H1'].R.mean():+.2f} | {d[d.half=='H2'].R.mean():+.2f} | {w_ / l_:.2f} |")
    P()
    open("reclaim_features_summary.md", "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads/SierraChart/claude_export/footprint")
