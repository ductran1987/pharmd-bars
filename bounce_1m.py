"""Fail-and-reclaim confirmed on a 1-MINUTE close vs. the 5m version, on the same PharmD fade setups.

    python bounce_1m.py <dir with ES_bars_1m.parquet, NQ_bars_1m.parquet>   -> bounce_1m_summary.md, bounce_1m_trades.csv

1m bars: Sierra footprint export (claude_export/footprint/*_bars_1m.parquet, trade prices, UTC, one contract per minute
in column `src`).  A setup is used only if the 1m bars on its day come from the SAME contract as the plan and cover the
session (first bar within 30 min of the letter / session start, last bar at or after 15:50 ET).  1m closes match the
repo's 5m closes on 100% of bars; highs/lows differ by a tick or two on some bars (different tick-record handling).

Universe and management exactly as bounce_vs_reclaim.py (limit_test.collect(); $500 risk on micros, BE at +1R, first
PharmD target >= 1.5R, flat at the last bar before 16:00, 2-tick slippage on market entries and stops, stop checked first
within a bar).  Long described; shorts mirrored.  near = zone top, far = zone bottom.  Stop = his rule: 1 tick past the
sweep extreme, never closer than 1.5 x ATR5 (ATR from 5m bars as before); min 0.2 x ATR15.

Variants (entry = market at the confirming close + 2 ticks, unless 'edge' = idealized fill at the edge):
  5m/5m   lost = 5m close past far edge, reclaim = 5m close back through the edge      (the earlier test, same setups)
  1m/1m   lost = 1m close past far edge, reclaim = 1m close back through the edge
  5m/1m   lost = 5m close past far edge (a real flush), reclaim = 1m close back through the edge
  plus the near-edge resting limit on 1m bars for reference.
Reclaim edge: 'near' (close back above the zone top) and 'far' (back above the zone bottom).
"""
import sys
import numpy as np, pandas as pd
import backtest_grid as bg, contracts, limit_test
from bounce_vs_reclaim import mirror, first, sim, limit_trade, summarize, fmt_row, HDR

TICK = bg.TICK; tz = "America/New_York"; SPLIT = "2026-06-09"


def load_1m(d):
    out = {}
    for s in ("ES", "NQ"):
        x = pd.read_parquet(f"{d}/{s}_bars_1m.parquet")
        x["time"] = x.time.dt.tz_localize("UTC").dt.tz_convert(tz)
        x["contract"] = x.src.str.upper().str.replace("-CME.SCID", "").str.replace(".SCID", "").map(contracts.norm)
        out[s] = x.sort_values("time").reset_index(drop=True)
    return out


def attach_1m(r, m1):
    """Return r with 1m arrays (same keys as the 5m record) or None if the 1m data doesn't cover this setup's session."""
    t0 = pd.Timestamp(r["ts"][0]); t_end = pd.Timestamp(r["date"], tz=tz).replace(hour=16)
    x = m1[r["sym"]]
    a, b = x.time.searchsorted(t0), x.time.searchsorted(t_end)
    w = x.iloc[a:b]
    w = w[w.contract == contracts.norm(r["contract"])]
    if len(w) < 30: return None
    if w.time.iloc[0] > t0 + pd.Timedelta(minutes=30) or w.time.iloc[-1] < t_end - pd.Timedelta(minutes=10): return None
    return dict(r, ts=w.time.astype(str).values, t=w.time.values, O=w.open.values.astype(float), H=w.high.values.astype(float),
                L=w.low.values.astype(float), Cl=w.close.values.astype(float))


def reclaim(r1, r5, lost_tf, edge_name, fill):
    """Fail-and-reclaim on 1m bars.  lost_tf='1m': loss = 1m close past the far edge; '5m': loss = a 5m close past the far
    edge (taken from the 5m record) and the 1m reclaim must come after that 5m bar has closed."""
    up, sg, near, far, O, H, L, C, tg = mirror(r1)
    if O[0] <= near: return None
    i_t = first(L <= near)
    if i_t is None: return None
    if lost_tf == "1m":
        i_l = first(C < far, i_t)
        if i_l is None: return None
    else:
        _, _, n5, f5, O5, H5, L5, C5, _ = mirror(r5)
        j_t = first(L5 <= n5)
        if j_t is None: return None
        j_l = first(C5 < f5, j_t)
        if j_l is None: return None
        t_close = pd.Timestamp(r5["ts"][j_l]) + pd.Timedelta(minutes=5)          # the 5m bar has closed
        i_l = int(np.searchsorted(pd.to_datetime(r1["ts"]), t_close)) - 1   # last 1m bar inside that 5m bar
        if i_l < i_t: i_l = i_t
    edge = far if edge_name == "far" else near
    i_r = first(C > edge, i_l + 1)
    if i_r is None or i_r + 1 >= len(C): return None
    sweep = L[i_t:i_r + 1].min()
    e = edge if fill == "edge" else C[i_r]
    stp = min(sweep - TICK, e - 1.5 * r1["atr5"])
    s = sim(r1, e, stp, i_r + 1, H, L, O, C, sg, limit_fill=False)
    if s is None: return None
    return dict(s, entry_time=r1["ts"][i_r], chase_atr5=(C[i_r] - edge) / r1["atr5"])


def reclaim5(r5, edge_name, fill):
    from bounce_vs_reclaim import reclaim_trade
    return reclaim_trade(r5, edge_name, fill)


def main(d1m):
    m1 = load_1m(d1m)
    recs = limit_test.collect()
    pairs = [(r, attach_1m(r, m1)) for r in recs]
    pairs = [(r5, r1) for r5, r1 in pairs if r1 is not None]
    out = []; P = lambda s="": (print(s), out.append(s))
    P("# Fail-and-reclaim on a 1-minute close — PharmD fade setups\n")
    P(f"{len(pairs)} of {len(recs)} fade setups have 1m bars from the plan's contract covering the session "
      f"(ES through 2026-10-02; NQ missing 2025-12-19 → 2026-02-27 and after 2026-08-07).\n")
    allrows = []
    for label, sel in (("Graded setups", lambda r: r["graded"]), ("All fade setups", lambda r: True)):
        S = [(a, b) for a, b in pairs if sel(a)]
        offered = sum(1 for a, b in S if mirror(a)[4][0] > mirror(a)[2])
        P(f"## {label} ({offered} setups offered)\n")
        P(HDR)
        variants = [
            ("Limit at near edge, stop entry−1.5 ATR5 (1m bars)", lambda a, b: limit_trade(b, 0, "entry1.5")),
            ("Limit at near edge, stop far−0.5 ATR5 (1m bars)", lambda a, b: limit_trade(b, 0, "far0.5")),
        ]
        for e in ("near", "far"):
            variants += [
                (f"Reclaim {e.upper()} · 5m lost / 5m reclaim · market (earlier test)", lambda a, b, e=e: reclaim5(a, e, "close")),
                (f"Reclaim {e.upper()} · 5m lost / 5m reclaim · edge fill (not executable)", lambda a, b, e=e: reclaim5(a, e, "edge")),
                (f"Reclaim {e.upper()} · 1m lost / **1m reclaim** · market", lambda a, b, e=e: reclaim(b, a, "1m", e, "close")),
                (f"Reclaim {e.upper()} · 1m lost / 1m reclaim · edge fill (not executable)", lambda a, b, e=e: reclaim(b, a, "1m", e, "edge")),
                (f"Reclaim {e.upper()} · 5m lost / **1m reclaim** · market", lambda a, b, e=e: reclaim(b, a, "5m", e, "close")),
                (f"Reclaim {e.upper()} · 5m lost / 1m reclaim · edge fill (not executable)", lambda a, b, e=e: reclaim(b, a, "5m", e, "edge")),
            ]
        for lab, fn in variants:
            rows = []
            for a, b in S:
                x = fn(a, b)
                if x is not None: x.update(strategy=lab, set=label, date=a["date"], id=a["id"], sym=a["sym"], dir=a["dir"], grade=a["grade"])
                rows.append(x)
            P(fmt_row(lab, summarize(rows, offered)))
            if label == "Graded setups" and ("market" in lab):
                for half, cond in (("H1", lambda dd: dd <= SPLIT), ("H2", lambda dd: dd > SPLIT)):
                    sub = [x for x in rows if x and cond(x["date"])]
                    off_h = sum(1 for a, b in S if cond(a["date"]) and mirror(a)[4][0] > mirror(a)[2])
                    P(fmt_row(f"&nbsp;&nbsp;↳ {half}", summarize(sub, off_h)))
            allrows += [x for x in rows if x]
        P()
    T = pd.DataFrame(allrows); T.to_csv("bounce_1m_trades.csv", index=False)
    g = T[(T.set == "Graded setups")]
    P("## How far past the edge the confirming close is (graded, market entries), in ATR5\n")
    P("| variant | median | 75th pct |\n|---|---|---|")
    for lab in g.strategy.unique():
        if "market" in lab and "chase_atr5" in g and g[g.strategy == lab].chase_atr5.notna().any():
            c = g[g.strategy == lab].chase_atr5
            P(f"| {lab} | {c.median():.2f} | {c.quantile(.75):.2f} |")
    P()
    P("## Per instrument (graded, market entries)\n")
    P(HDR)
    for lab in [l for l in g.strategy.unique() if "market" in l and "NEAR" in l]:
        for s in ("ES", "NQ"):
            sub = g[(g.strategy == lab) & (g.sym == s)]
            off = sum(1 for a, b in pairs if a["graded"] and a["sym"] == s and mirror(a)[4][0] > mirror(a)[2])
            P(fmt_row(f"{lab} — {s}", summarize(sub.to_dict("records"), off)))
    open("bounce_1m_summary.md", "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads/SierraChart/claude_export/footprint")
