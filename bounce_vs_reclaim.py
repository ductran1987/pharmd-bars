"""Bounce at the near edge vs. fail-the-far-edge-then-reclaim, on every PharmD fade setup (hold / LBAF / LAAF / failed reclaim).

    python bounce_vs_reclaim.py   -> bounce_vs_reclaim_summary.md, bounce_vs_reclaim_paths.csv, bounce_vs_reclaim_trades.csv

Universe: limit_test.collect() — fade setups, session bars from the letter's publish time to the 15:55 bar, per-contract bars,
same ATR / target resolution as backtest_grid.  Setups where price is already at/through the near edge when the letter comes
out are skipped (no resting order possible).  Long described; shorts mirrored.  near = zone top, far = zone bottom.

PART 1 — path probabilities (no money):
  touch      = first bar whose low <= near edge.
  "lost"     = a 5m CLOSE below the far edge (same close-based definition as his reclaim rule).
  win        = price reaches the trade's first target (T1).
  held->T1   = T1 reached after the touch with no 5m close below the far edge first.
  lost->reclaim->T1 = after the lost close, a 5m close back above the far edge (variant: above the near edge), then T1 before
               price makes a new low beyond the sweep extreme.
  Within the touch bar the target is not credited (order unknown).

PART 2 — executable trades, same management for all ($500 risk on micros, BE at +1R, first PharmD target >= 1.5R, flat 15:55,
$2.60/micro, 2-tick slippage on stops; within a bar the stop is checked first):
  LIMIT      buy limit at near edge + k ticks (k = +2 front-run, 0, -2 inside), placed at publish.  Fill = low <= limit - 1 tick
             (realistic queue) except the front-run variant also tested on touch.  No slippage on the limit fill.
             Stop: far edge - 0.5 x ATR5 | far edge - 1.0 x ATR5 | entry - 1.5 x ATR5 (his floor distance).
  RECLAIM    only after a close below the far edge, then a 5m close back above the far edge ("far") or near edge ("near").
             Fills: 'edge' (idealized, at the edge on the close — NOT executable), 'close' (market at the reclaim close, +2 ticks),
             'stop' (resting buy-stop 1 tick above the edge, armed after the lost close; no close confirmation).
             Stop: his rule — 1 tick past the sweep extreme, never closer than 1.5 x ATR5; min 0.2 x ATR15.
  COMBO      the LIMIT trade, and if that one is stopped out, the RECLAIM trade later the same day (if it sets up after the stop).
"""
import numpy as np, pandas as pd
import backtest_grid as bg
import limit_test

TICK = bg.TICK
SPLIT = "2026-06-09"


def mirror(r):
    """Return arrays oriented so the trade is always 'long' (shorts negated)."""
    up = r["dir"] == "long"; sg = 1 if up else -1
    g0, g1 = r["gate"][0], r["gate"][-1]
    near, far = (g1, g0) if up else (-g0, -g1)
    if up: O, H, L, C = r["O"], r["H"], r["L"], r["Cl"]
    else: O, H, L, C = -r["O"], -r["L"], -r["H"], -r["Cl"]
    tg = [x * sg for x in r["tg"]]
    return up, sg, near, far, O, H, L, C, tg


def first(mask, start=0):
    idx = np.flatnonzero(mask[start:])
    return start + int(idx[0]) if len(idx) else None


# ------------------------------------------------------------------ part 1
def paths(r):
    up, sg, near, far, O, H, L, C, tg = mirror(r)
    if O[0] <= near: return None
    t1s = [x for x in tg if x > near]
    if not t1s: return None
    T1 = t1s[0]
    out = dict(date=r["date"], id=r["id"], sym=r["sym"], dir=r["dir"], grade=r["grade"], graded=r["graded"],
               width_atr5=(near - far) / r["atr5"], t1_atr5=(T1 - near) / r["atr5"])
    i_t = first(L <= near)
    if i_t is None: return dict(out, path="no touch")
    i_l = first(C < far, i_t)
    i_w = first(H >= T1, i_t + 1)
    if i_l is None or (i_w is not None and i_w < i_l):
        # held: how deep did it go before T1 / end of day?
        end = i_w if i_w is not None else len(L) - 1
        low = L[i_t:end + 1].min()
        depth = (near - low) / max(near - far, TICK)     # 0 = near edge, 1 = far edge, >1 = wicked through far
        return dict(out, path="held->T1" if i_w is not None else "held, no T1", depth_zone=depth,
                    depth_atr5=(near - low) / r["atr5"], depth_pts=near - low)
    res = dict(out)
    for edge_name, edge in (("far", far), ("near", near)):
        i_r = first(C > edge, i_l + 1)
        if i_r is None: res[f"path_{edge_name}"] = "lost, no reclaim"; continue
        sweep = L[i_t:i_r + 1].min()
        j_w = first(H >= T1, i_r + 1); j_f = first(L < sweep, i_r + 1)
        if j_w is not None and (j_f is None or j_w < j_f): res[f"path_{edge_name}"] = "lost->reclaim->T1"
        elif j_f is not None: res[f"path_{edge_name}"] = "lost->reclaim->new low"
        else: res[f"path_{edge_name}"] = "lost->reclaim, neither"
        res[f"sweep_atr5_{edge_name}"] = (far - sweep) / r["atr5"]
    res["path"] = "lost"
    return res


# ------------------------------------------------------------------ part 2
def sim(r, e, stp, j, H, L, O, C, sg, limit_fill, tgt_rule="ge1.5", be=1.0):
    """Run the shared management from bar j (the fill bar, whose high gets no target credit). Prices are in mirrored (long) space."""
    rk = e - stp
    if rk < 0.2 * r["atr15"]: rk = 0.2 * r["atr15"]; stp = e - rk
    n = int(bg.RISK // ((rk + bg.SLIP) * bg.MICRO[r["sym"]]))
    if n < 1: return None
    Hs, Ls, Os, Cs = H[j:].copy(), L[j:].copy(), O[j:].copy(), C[j:].copy()
    Hs[0] = e; Os[0] = e
    t = dict(dir="long", sym=r["sym"], e=e, H=Hs, L=Ls, O=Os, C=Cs)
    tg = [x * sg for x in r["tg"]]
    tp = bg.pick_target(tg, e, rk, True, tgt_rule)
    pnl, how, pts = bg.simulate_one(t, stp, rk, n, tp, be, None)
    if limit_fill: pnl += bg.SLIP * bg.MICRO[r["sym"]] * n
    # bar index (absolute) where the trade ended, to chain the combo
    fav = Hs - e; adv = Ls - e
    i_s = first(adv <= -rk); end = j + (i_s if i_s is not None else len(Cs) - 1)
    return dict(pnl=pnl, R=pnl / bg.RISK, exit=how, risk_pts=rk, micros=n, end_bar=end if how == "stop" else None,
                R_to_tgt=(tp - e) / rk if tp is not None else np.nan)


def limit_trade(r, k_ticks, stop_kind, fill="through"):
    up, sg, near, far, O, H, L, C, tg = mirror(r)
    if O[0] <= near: return None
    P = near + k_ticks * TICK
    thr = P - (TICK if fill == "through" else 0)
    j = first(L <= thr)
    if j is None: return None
    e = min(P, O[j])
    if stop_kind == "far0.5": stp = far - 0.5 * r["atr5"]
    elif stop_kind == "far1.0": stp = far - 1.0 * r["atr5"]
    else: stp = e - 1.5 * r["atr5"]
    s = sim(r, e, stp, j, H, L, O, C, sg, limit_fill=True)
    return s and dict(s, fill_bar=j, entry=e * sg)


def reclaim_trade(r, edge_name, fill, after_bar=0):
    up, sg, near, far, O, H, L, C, tg = mirror(r)
    if O[0] <= near: return None
    i_t = first(L <= near)
    if i_t is None: return None
    i_l = first(C < far, max(i_t, after_bar))
    if i_l is None: return None
    edge = far if edge_name == "far" else near
    if fill == "stop":
        j = first(H >= edge + TICK, i_l + 1)
        if j is None: return None
        e = max(edge + TICK, O[j]); sweep = L[i_t:j + 1].min()
        stp = min(sweep - TICK, e - 1.5 * r["atr5"])
        s = sim(r, e, stp, j, H, L, O, C, sg, limit_fill=False)
        # fill bar's low already in L[j]; simulate_one sees it as adverse — conservative
        return s and dict(s, fill_bar=j)
    i_r = first(C > edge, i_l + 1)
    if i_r is None or i_r + 1 >= len(C): return None
    sweep = L[i_t:i_r + 1].min()
    e = edge if fill == "edge" else C[i_r]
    stp = min(sweep - TICK, e - 1.5 * r["atr5"])
    s = sim(r, e, stp, i_r + 1, H, L, O, C, sg, limit_fill=False)   # management from the bar after the reclaim close
    return s and dict(s, fill_bar=i_r + 1)


def summarize(rows, offered):
    d = pd.DataFrame([x for x in rows if x is not None])
    if not len(d): return dict(n=0)
    w = d[d.pnl > 0].pnl.sum(); l = -d[d.pnl < 0].pnl.sum()
    return dict(n=len(d), fill_rate=len(d) / offered, win=(d.pnl > 0).mean(), avgR=d.R.mean(), medR=d.R.median(),
                total=d.pnl.sum(), per_setup=d.pnl.sum() / offered, pf=w / l if l else np.inf,
                stop_rate=(d.exit == "stop").mean(), tgt_rate=(d.exit == "target").mean())


def fmt_row(name, m):
    if not m.get("n"): return f"| {name} | 0 | | | | | | | |"
    return (f"| {name} | {m['n']} | {m['fill_rate']:.0%} | {m['win']:.0%} | {m['tgt_rate']:.0%} | {m['avgR']:+.2f} | "
            f"${m['total']:,.0f} | ${m['per_setup']:+,.0f} | {m['pf']:.2f} |")


HDR = ("| strategy | trades | fill/trigger rate | win | hit target | avg R | total $ | $ per setup offered | PF |\n"
       "|---|---|---|---|---|---|---|---|---|")


def main():
    recs = limit_test.collect()
    out = []; P = lambda s="": (print(s), out.append(s))
    P("# Near-edge bounce vs. fail-and-reclaim — PharmD fade setups\n")

    # ---------------- part 1
    pr = [p for p in (paths(r) for r in recs) if p is not None]
    df = pd.DataFrame(pr); df.to_csv("bounce_vs_reclaim_paths.csv", index=False)
    for label, sub in (("Graded setups (A/B/C)", df[df.graded]), ("All fade setups (graded + ungraded)", df)):
        n = len(sub); touched = sub[sub.path != "no touch"]; nt = len(touched)
        held = touched[touched.path.str.startswith("held")]; lost = touched[touched.path == "lost"]
        hw = (touched.path == "held->T1").sum()
        P(f"## Part 1 — what happens after price touches the near edge · {label}\n")
        P(f"{n} setups where price was outside the zone when the letter came out; **{nt} touched the near edge** "
          f"({nt / n:.0%}).\n")
        P("| path after the touch | count | % of touches |\n|---|---|---|")
        P(f"| Held (no 5m close beyond far edge) **and hit T1** | {hw} | **{hw / nt:.0%}** |")
        P(f"| Held, but T1 not reached by 15:55 | {(touched.path == 'held, no T1').sum()} | {(touched.path == 'held, no T1').mean():.0%} |")
        P(f"| Lost the far edge (5m close beyond it) | {len(lost)} | {len(lost) / nt:.0%} |")
        for e in ("far", "near"):
            c = lost[f"path_{e}"].value_counts()
            rw = c.get("lost->reclaim->T1", 0); rf = c.get("lost->reclaim->new low", 0)
            rn = c.get("lost->reclaim, neither", 0); nr = c.get("lost, no reclaim", 0)
            P(f"| &nbsp;&nbsp;↳ reclaimed the **{e}** edge, then hit T1 before a new low | {rw} | {rw / nt:.0%} "
              f"(= {rw / max(len(lost), 1):.0%} of losses; {rw / max(rw + rf + rn, 1):.0%} of reclaims) |")
            P(f"| &nbsp;&nbsp;↳ reclaimed the {e} edge, then made a new low first | {rf} | {rf / nt:.0%} |")
            P(f"| &nbsp;&nbsp;↳ reclaimed the {e} edge, neither by 15:55 | {rn} | {rn / nt:.0%} |")
            P(f"| &nbsp;&nbsp;↳ never reclaimed the {e} edge | {nr} | {nr / nt:.0%} |")
        P()
        if len(held):
            hh = held[held.path == "held->T1"]
            P(f"**How deep the winning holds went before T1** ({len(hh)} trades; 0 = near edge, 1 = far edge):  "
              f"only tagged the near edge (≤ 2 ticks in): {(hh.depth_pts <= 2 * TICK).mean():.0%} · "
              f"median depth {hh.depth_zone.median():.2f} of the zone · 75th pct {hh.depth_zone.quantile(.75):.2f} · "
              f"wicked past the far edge without closing there: {(hh.depth_zone > 1).mean():.0%}.  "
              f"In ATR5: median {hh.depth_atr5.median():.2f}, 75th pct {hh.depth_atr5.quantile(.75):.2f}.\n")
        P(f"Median zone width {sub.width_atr5.median():.2f} ATR5; median distance near edge → T1 {sub.t1_atr5.median():.2f} ATR5.\n")

    # ---------------- part 2
    G = [r for r in recs if r["graded"]]
    for label, S in (("Graded setups", G), ("All fade setups", recs)):
        offered = sum(1 for r in S if mirror(r)[4][0] > mirror(r)[2])
        P(f"## Part 2 — executable trades · {label} ({offered} setups offered)\n")
        P("Same management for every row: $500 risk, BE at +1R, exit at first PharmD target ≥ 1.5R, flat 15:55. "
          "\"$ per setup offered\" puts strategies that trade more or less often on the same footing.\n")
        P(HDR)
        trades = []
        for lab, fn in [
            ("Limit near edge +2t (front-run), touch fill, stop far−0.5 ATR5", lambda r: limit_trade(r, 2, "far0.5", "touch")),
            ("Limit at near edge, stop far−0.5 ATR5", lambda r: limit_trade(r, 0, "far0.5")),
            ("Limit at near edge, stop far−1.0 ATR5", lambda r: limit_trade(r, 0, "far1.0")),
            ("Limit at near edge, stop entry−1.5 ATR5", lambda r: limit_trade(r, 0, "entry1.5")),
            ("Limit 2t inside near edge, stop far−0.5 ATR5", lambda r: limit_trade(r, -2, "far0.5")),
            ("Fail → reclaim FAR edge · idealized fill at edge (not executable)", lambda r: reclaim_trade(r, "far", "edge")),
            ("Fail → reclaim FAR edge · market on reclaim close", lambda r: reclaim_trade(r, "far", "close")),
            ("Fail → reclaim FAR edge · buy-stop 1t above edge", lambda r: reclaim_trade(r, "far", "stop")),
            ("Fail → reclaim NEAR edge · idealized fill at edge (not executable)", lambda r: reclaim_trade(r, "near", "edge")),
            ("Fail → reclaim NEAR edge · market on reclaim close", lambda r: reclaim_trade(r, "near", "close")),
            ("Fail → reclaim NEAR edge · buy-stop 1t above edge", lambda r: reclaim_trade(r, "near", "stop")),
        ]:
            rows = []
            for r in S:
                x = fn(r)
                if x is not None:
                    x.update(strategy=lab, date=r["date"], id=r["id"], sym=r["sym"], dir=r["dir"], grade=r["grade"])
                rows.append(x)
            m = summarize(rows, offered); P(fmt_row(lab, m))
            trades += [x for x in rows if x]
            if label == "Graded setups":
                for half, cond in (("H1", lambda d: d <= SPLIT), ("H2", lambda d: d > SPLIT)):
                    sub = [x for x in rows if x and cond(x["date"])]
                    off_h = sum(1 for r in S if cond(r["date"]) and mirror(r)[4][0] > mirror(r)[2])
                    mh = summarize(sub, off_h); P(fmt_row(f"&nbsp;&nbsp;↳ {half}", mh))
        # combo
        for stop_kind, fill_kind in (("far0.5", "close"), ("far0.5", "stop"), ("far1.0", "close")):
            rows = []
            for r in S:
                a = limit_trade(r, 0, stop_kind)
                if a is None: rows.append(None); continue
                rows.append(a)
                if a["exit"] == "stop" and a.get("end_bar") is not None:
                    b = reclaim_trade(r, "far", fill_kind, after_bar=a["end_bar"])
                    if b is not None and b["fill_bar"] > a["end_bar"]: rows.append(b)
            m = summarize(rows, offered)
            P(fmt_row(f"COMBO: limit near (stop {stop_kind}) + re-enter on far reclaim ({fill_kind})", m))
        P()
        if label == "Graded setups":
            pd.DataFrame(trades).to_csv("bounce_vs_reclaim_trades.csv", index=False)
    open("bounce_vs_reclaim_summary.md", "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
