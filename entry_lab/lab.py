"""Entry-model lab: which trigger to use once price reaches a PharmD level.

Universes
  A  PharmD fade trades (hold / LBAF / LAAF / failed reclaim) — his direction, his targets.
  B  every level in the plan (zones + brief levels, overlapping ones merged) — long when price comes down into it,
     short when it comes up into it; targets = the next plan levels in the trade direction.
  C  the same triggers anywhere in the session (no level), tagged at-level / away-from-levels — the control.

Data: per-contract 5m bars (contracts.load — Sierra exports + yfinance, never spliced across a roll), plan refs
resolved from the same contract (plan_refs), ATR5/ATR15 at the prior close (backtest_grid.atr_for).
Session: from the letter's publish time (or 18:00 the prior trading day, whichever is later) to the 15:55 bar.
Entries only up to 15:30; flat at the 15:55 bar's close.

Executable fills only: a trigger is known at the CLOSE of its signal bar (on its own timeframe), the order goes in
at the next 5m bar's OPEN + 2 ticks.  The touch-limit baseline fills only when price trades 1 tick through the limit.
Stops: 1 tick past the trigger's structural low/high, never closer than floor x ATR5; 2 ticks slip; a bar that opens
through the stop fills at its open.  Targets are limit orders that need a 1-tick trade-through.  Within a bar the
stop is checked first.  Size = $500 / ((risk + 0.5) x $/pt) micros (fractional), $2.60 per micro round trip.
"""
import os, sys, json, glob, re, math
from functools import lru_cache
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
if ROOT not in sys.path: sys.path.insert(0, ROOT)
os.chdir(ROOT)
import numpy as np, pandas as pd
import contracts, plan_refs, contract_map, backtest
from backtest_grid import atr_for, grade, plan_zones, POST_TIMES

tz = "America/New_York"
TICK = 0.25; RISK = 500.0; MICRO = {"ES": 5.0, "NQ": 2.0}; SLIP = 0.5; COMM = 2.6
TFS = (5, 10, 15, 30, 60)
SPLIT = "2026-03-01"           # H1 / H2 split (roughly half the touch events on each side; set in run.py)
LOC_TOL, LOC_DEPTH = 0.25, 3.0  # "at the level": swing low within [far edge - 3 ATR5, near edge + 0.25 ATR5]
CUTOFF_MIN = 15 * 60 + 30       # no new entries after 15:30 ET
NS_MIN = 60 * 10 ** 9


# ------------------------------------------------------------------ indicators on one timeframe
def rsi(c, n=14):
    d = c.diff(); up = d.clip(lower=0); dn = -d.clip(upper=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean(); ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + au / ad.replace(0, np.nan))


def pivots(x, L, R, low=True):
    """Pivot low (high) at i: strictly beyond the L bars before, at least as extreme as the R bars after.
    Known at the close of bar i+R."""
    s = pd.Series(x)
    if low:
        left = s.shift(1).rolling(L, min_periods=L).min()
        right = s.shift(-1).rolling(R, min_periods=R).min().shift(-(R - 1))
        return ((s < left) & (s <= right)).fillna(False).values
    left = s.shift(1).rolling(L, min_periods=L).max()
    right = s.shift(-1).rolling(R, min_periods=R).max().shift(-(R - 1))
    return ((s > left) & (s >= right)).fillna(False).values


def last_true_before(mask, gap):
    """out[i] = largest j <= i - gap with mask[j], else -1."""
    idx = np.where(mask, np.arange(len(mask)), -1)
    run = np.maximum.accumulate(idx)
    out = np.full(len(mask), -1)
    out[gap:] = run[:len(mask) - gap]
    return out


DIV_P2_L = 5          # P2 must be the lowest low of the 5 bars before it
DIV_SWING = 5         # P1 = a 5/5 swing (lowest of 5 bars either side)
DIV_SEP = (5, 60)     # P1 between 5 and 60 bars before P2 (TradingView divergence-indicator range)


def build_tf(d5, tf):
    s = d5.set_index("time")[["Open", "High", "Low", "Close", "Volume"]]
    if tf == 5: f = s.copy()
    else:
        f = s.resample(f"{tf}min", label="left", closed="left", offset=("30min" if tf == 60 else None)).agg(
            {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna(subset=["Open"])
    f = f.reset_index()
    t0 = f.time.dt.tz_convert("UTC").values.astype("datetime64[ns]").astype(np.int64)
    F = dict(tf=tf, t0=t0, tc=t0 + tf * NS_MIN, O=f.Open.values.astype(float), H=f.High.values.astype(float),
             L=f.Low.values.astype(float), C=f.Close.values.astype(float), V=f.Volume.values.astype(float))
    c = f.Close
    F["rsi"] = rsi(c, 14).values
    e12 = c.ewm(span=12, adjust=False).mean(); e26 = c.ewm(span=26, adjust=False).mean()
    macd = e12 - e26; sig = macd.ewm(span=9, adjust=False).mean()
    F["macd"] = macd.values; F["hist"] = (macd - sig).values
    tr = np.maximum(f.High - f.Low, np.maximum((f.High - c.shift()).abs(), (f.Low - c.shift()).abs()))
    F["atr"] = tr.rolling(14, min_periods=5).mean().values
    H, L = F["H"], F["L"]
    sw_lo = pivots(L, DIV_SWING, DIV_SWING, True); sw_hi = pivots(H, DIV_SWING, DIV_SWING, False)
    p1_lo = last_true_before(sw_lo, DIV_SEP[0]); p1_hi = last_true_before(sw_hi, DIV_SEP[0])
    F["div"] = {}
    for R in (1, 2):
        p2_lo = pivots(L, DIV_P2_L, R, True); p2_hi = pivots(H, DIV_P2_L, R, False)
        for osc in ("rsi", "hist", "macd"):
            o = F[osc]
            i = np.arange(len(L))
            okl = p2_lo & (p1_lo >= 0) & (i - p1_lo <= DIV_SEP[1])
            j = np.where(p1_lo >= 0, p1_lo, 0)
            bull = okl & (L < L[j]) & (o > o[j])
            okh = p2_hi & (p1_hi >= 0) & (i - p1_hi <= DIV_SEP[1])
            j2 = np.where(p1_hi >= 0, p1_hi, 0)
            bear = okh & (H > H[j2]) & (o < o[j2])
            # P2 indices (signal known at P2 + R) and each P2's P1 index
            F["div"][(osc, R)] = (np.flatnonzero(bull), np.flatnonzero(bear), j, j2)
    # RSI hook: cross back above lvl (below 100 - lvl); run start of the oversold (overbought) stretch, max 24 bars
    r = F["rsi"]; n = len(r); F["hook"] = {}
    for lvl in (30, 35):
        out = []
        for up in (True, False):
            th = lvl if up else 100 - lvl
            below = (r < th) if up else (r > th)
            cross = np.zeros(n, bool); cross[1:] = below[:-1] & ~below[1:] & ~np.isnan(r[1:])
            ks = np.flatnonzero(cross); j0 = np.empty(len(ks), int)
            for q, k in enumerate(ks):
                j = k - 1
                while j - 1 >= 0 and j > k - 24 and below[j - 1]: j -= 1
                j0[q] = j
            out.append((ks, j0))
        F["hook"][lvl] = tuple(out)
    # rejection candle (long: lower wick >= 50% of range, close in top third, range >= 0.75 ATR(tf))
    O, C, A = F["O"], F["C"], F["atr"]; rg = H - L
    big = (rg > 0) & (rg >= 0.75 * np.nan_to_num(A, nan=np.inf))
    rl = big & ((np.minimum(O, C) - L) >= 0.5 * rg) & (C >= L + 0.66 * rg)
    rs = big & ((H - np.maximum(O, C)) >= 0.5 * rg) & (C <= H - 0.66 * rg)
    F["rej"] = (np.flatnonzero(rl), np.flatnonzero(rs))
    Cp, Op = np.roll(C, 1), np.roll(O, 1)
    el = (C > O) & (Cp < Op) & (C >= Op) & (O <= Cp); el[0] = False
    es = (C < O) & (Cp > Op) & (C <= Op) & (O >= Cp); es[0] = False
    F["eng"] = (np.flatnonzero(el), np.flatnonzero(es))
    F["ph22"] = pivots(H, 2, 2, False); F["pl22"] = pivots(L, 2, 2, True)
    F["ph_before"] = last_true_before(F["ph22"], 1); F["pl_before"] = last_true_before(F["pl22"], 1)
    return F


@lru_cache(maxsize=32)
def frames(sym, contract):
    d5 = contracts.load(sym, contract)
    d5 = d5.sort_values("time").reset_index(drop=True)
    t5 = d5.time.dt.tz_convert("UTC").values.astype("datetime64[ns]").astype(np.int64)
    mins = (d5.time.dt.hour * 60 + d5.time.dt.minute).values
    out = dict(d5=d5, t5=t5, mins=mins, O=d5.Open.values.astype(float), H=d5.High.values.astype(float),
               L=d5.Low.values.astype(float), C=d5.Close.values.astype(float), tf={})
    for tf in TFS:
        F = build_tf(d5, tf)
        F["e5"] = np.searchsorted(t5, F["tc"], side="left")     # 5m bar whose OPEN is the first price after the TF bar closed
        out["tf"][tf] = F
    return out


# ------------------------------------------------------------------ setups
def ns(ts): return pd.Timestamp(ts).tz_convert("UTC").value


def session_bounds(date, post):
    end = pd.Timestamp(date, tz=tz).replace(hour=16)
    start = (end - pd.Timedelta(days=1)).replace(hour=18)
    while start.weekday() > 4: start -= pd.Timedelta(days=1)
    if post is not None and post > start: start = post
    cut = pd.Timestamp(date, tz=tz).replace(hour=15, minute=30)
    return start, cut, end


def _tgt_list(tg, up):
    out = []
    for x in tg:
        if isinstance(x, (list, tuple)): out.append(min(x) if up else max(x))
        elif isinstance(x, (int, float)): out.append(float(x))
    return out


def merge_zones(zs, gap):
    zs = sorted((min(a, b), max(a, b)) for a, b in zs)
    out = []
    for a, b in zs:
        if out and a <= out[-1][1] + gap: out[-1] = (out[-1][0], max(out[-1][1], b))
        else: out.append((a, b))
    return out


def plan_days():
    """[(date, path, {sym: contract})] for every plan with bars; contract per contract_map (<= 10-02) or Z6 after."""
    cmap = json.load(open("plans/contract_map.json"))
    out = []
    for f in sorted(glob.glob("plans/plan-*.json")):
        date = json.load(open(f))["date"]
        C = {}
        for s in ("ES", "NQ"):
            if date in cmap:
                if cmap[date][s]["bars"]: C[s] = cmap[date][s]["contract"]
            elif date > "2026-10-02":
                c = f"{s}Z6"
                if pd.Timestamp(date).date() in contracts.coverage(s, c): C[s] = c
        if C: out.append((date, f, C))
    return out


def post_time(date):
    if date in POST_TIMES: return pd.Timestamp(POST_TIMES[date]["posted_et"], tz=tz)
    # newer drafts carry no publish time: assume 19:00 ET the evening before (he posts ~17:00-19:00 ET)
    return (pd.Timestamp(date, tz=tz) - pd.Timedelta(days=1)).replace(hour=19)


def build_setups():
    A, B, days = [], [], []
    for date, f, C in plan_days():
        try:
            p, trades = plan_refs.load_plan(f, bars_for=lambda s: contracts.load(s, C[s]) if s in C else contracts.load(s, f"{s}Z6"), skip=set())
        except Exception as e:
            print("skip", date, e); continue
        post = post_time(date)
        start, cut, end = session_bounds(date, post)
        for s, c in C.items():
            r = atr_for(s, c, date)
            if r is None: continue
            a5, a15, _ = r
            Fr = frames(s, c)
            s0 = int(np.searchsorted(Fr["t5"], ns(start), "left")); s1 = int(np.searchsorted(Fr["t5"], ns(end), "left"))   # [s0, s1)
            cut5 = int(np.searchsorted(Fr["t5"], ns(cut), "right")) - 1     # last bar whose OPEN may be an entry
            if s1 - s0 < 60: continue
            base = dict(date=date, sym=s, contract=c, atr5=a5, atr15=a15, s0=s0, s1=s1, cut5=cut5,
                        start=str(start), post=str(post))
            days.append(dict(base, zones=merge_zones(plan_zones(p, s), 0.25 * a5)))
            for t in trades:
                if t["instrument"] != s: continue
                kind = t.get("kind") or ("break" if backtest.BREAK.search(t["name"] + " " + str(t.get("gate", ""))) else "fade")
                if kind != "fade": continue
                g = [x for x in ((t.get("levels") or {}).get("gate") or []) if isinstance(x, (int, float))]
                if not g or t.get("dir") not in ("long", "short"): continue
                g = sorted(g); up = t["dir"] == "long"
                tg = _tgt_list(t["levels"]["tgt"], up)
                A.append(dict(base, uni="A", id=t["id"], dir=t["dir"], zlo=float(g[0]), zhi=float(g[-1]), tg=tg,
                              tag=t.get("tag", ""), grade=grade(t.get("tag", ""))))
            zs = merge_zones(plan_zones(p, s), 0.25 * a5)
            for k, (lo, hi) in enumerate(zs):
                above = [z[0] for z in zs if z[0] > hi + 1e-9]; below = [z[1] for z in zs if z[1] < lo - 1e-9]
                B.append(dict(base, uni="B", id=f"z{k}L", dir="long", zlo=lo, zhi=hi, tg=sorted(above), tag="", grade=""))
                B.append(dict(base, uni="B", id=f"z{k}S", dir="short", zlo=lo, zhi=hi, tg=sorted(below, reverse=True), tag="", grade=""))
    return A, B, days


# ------------------------------------------------------------------ arming / location
def arm_index(S, Fr):
    """First 5m bar in the session that trades into the zone (A: any side; B: approached from the trade's side)."""
    H, L, C = Fr["H"], Fr["L"], Fr["C"]; s0, s1 = S["s0"], S["s1"]
    up = S["dir"] == "long"
    rng = np.arange(s0, s1)
    if up: hit = L[s0:s1] <= S["zhi"]
    else: hit = H[s0:s1] >= S["zlo"]
    if S["uni"] in ("B", "P") or S.get("approach"):
        prev = C[s0 - 1:s1 - 1]
        hit = hit & ((prev > S["zhi"]) if up else (prev < S["zlo"]))
    idx = np.flatnonzero(hit)
    return int(rng[idx[0]]) if len(idx) else None


def in_loc(S, x):
    """x = swing low (long) / swing high (short) price."""
    a5 = S["atr5"]
    if S["dir"] == "long": return (x <= S["zhi"] + LOC_TOL * a5) and (x >= S["zlo"] - LOC_DEPTH * a5)
    return (x >= S["zlo"] - LOC_TOL * a5) and (x <= S["zhi"] + LOC_DEPTH * a5)


# ------------------------------------------------------------------ triggers -> (entry 5m index, structural extreme, info)
BIG = 10 ** 9


def _tf_range(S, Fr, F):
    """TF bars that START after the letter exists and whose entry bar is <= the 15:30 cutoff: [a, b)."""
    a = int(np.searchsorted(F["t0"], Fr["t5"][S["s0"]], "left"))
    b = int(np.searchsorted(F["e5"], S["cut5"], "right"))
    return a, b


def _loc_mask(S, x):
    a5 = S["atr5"]
    if S["dir"] == "long": return (x <= S["zhi"] + LOC_TOL * a5) & (x >= S["zlo"] - LOC_DEPTH * a5)
    return (x >= S["zlo"] - LOC_TOL * a5) & (x <= S["zhi"] + LOC_DEPTH * a5)


def _first(S, F, ks, x, R=0, loc=True):
    """ks: signal-defining bar indices (signal known at the close of ks + R); x: structural extremes."""
    if not len(ks): return None
    k = ks + R
    e5 = F["e5"][k]
    ok = (e5 > S["_arm"]) & (e5 <= S["cut5"]) & (e5 >= S["s0"])
    if loc: ok &= _loc_mask(S, x)
    w = np.flatnonzero(ok)
    if not len(w): return None
    i = w[0]
    return int(e5[i]), float(x[i]), dict(sig_t=int(F["tc"][k[i]]))


def _slice(arr, lo, hi):
    return arr[np.searchsorted(arr, lo, "left"):np.searchsorted(arr, hi, "left")]


def trig_div(S, Fr, tf, osc, R, osc_filter=None):
    F = Fr["tf"][tf]; bull, bear, j1, j2 = F["div"][(osc, R)]
    a, b = _tf_range(S, Fr, F); up = S["dir"] == "long"
    ks = _slice(bull if up else bear, a, b - R)
    if osc_filter == "ext" and len(ks):
        o1 = F["rsi"][(j1 if up else j2)[ks]]
        ks = ks[(o1 < 35) if up else (o1 > 65)]
    return _first(S, F, ks, (F["L"] if up else F["H"])[ks], R)


def _hook_x(F, up, ks, j0, a):
    src = F["L"] if up else F["H"]; j0 = np.maximum(j0, a)
    return np.array([(src[s:k + 1].min() if up else src[s:k + 1].max()) for s, k in zip(j0, ks)], dtype=float)


def trig_hook(S, Fr, tf, lvl=30):
    F = Fr["tf"][tf]; a, b = _tf_range(S, Fr, F); up = S["dir"] == "long"
    ks, j0 = F["hook"][lvl][0 if up else 1]
    lo, hi = np.searchsorted(ks, a, "left"), np.searchsorted(ks, b, "left")
    ks, j0 = ks[lo:hi], j0[lo:hi]
    if not len(ks): return None
    return _first(S, F, ks, _hook_x(F, up, ks, j0, a), 0)


def trig_mss(S, Fr, tf):
    """Market-structure shift: after the low at the level (running low since the session start), the first close
    above the last 2/2 swing high made before that low (within 60 bars).  Shorts mirrored."""
    F = Fr["tf"][tf]; a, b = _tf_range(S, Fr, F); up = S["dir"] == "long"
    if b - a < 3: return None
    Ls = F["L"][a:b] if up else -F["H"][a:b]
    Cs = F["C"][a:b] if up else -F["C"][a:b]
    rm = np.minimum.accumulate(Ls)
    is_new = Ls <= np.concatenate([[np.inf], rm[:-1]])
    loc_i = np.arange(len(Ls))
    ext = np.maximum.accumulate(np.where(is_new, loc_i, 0))
    ext_g = a + ext
    h = (F["ph_before"] if up else F["pl_before"])[ext_g]
    valid = (h >= 0) & (ext_g - h <= 60)
    hp = np.where(valid, (F["H"] if up else -F["L"])[np.maximum(h, 0)], np.inf)
    ok = valid & (loc_i > ext) & (Cs > hp)
    ks = (a + loc_i)[ok]; xs = (rm if up else -rm)[ok]
    return _first(S, F, ks, xs, 0)


def trig_pattern(S, Fr, tf, key):
    F = Fr["tf"][tf]; a, b = _tf_range(S, Fr, F); up = S["dir"] == "long"
    ks = _slice(F[key][0 if up else 1], a + (key == "eng"), b)
    if key == "rej": x = (F["L"] if up else F["H"])[ks]
    else: x = np.minimum(F["L"][ks], F["L"][ks - 1]) if up else np.maximum(F["H"][ks], F["H"][ks - 1])
    return _first(S, F, ks, x, 0)


def trig_reclaim(S, Fr, tf=5):
    """His rule: after the first touch, the first close back through the near edge (on tf); entry next 5m open.
    Structural extreme = the sweep (furthest 5m price from the touch to the entry)."""
    F = Fr["tf"][tf]; a, b = _tf_range(S, Fr, F); up = S["dir"] == "long"; arm = S["_arm"]
    k0 = int(np.searchsorted(F["t0"], Fr["t5"][arm], "right")) - 1
    lo = max(k0 + 1, a)
    if lo >= b: return None
    edge = S["zhi"] if up else S["zlo"]
    Cs = F["C"][lo:b]
    w = np.flatnonzero((Cs > edge) if up else (Cs < edge))
    if not len(w): return None
    k = lo + w[0]; e5 = int(F["e5"][k])
    if e5 > S["cut5"] or e5 <= arm: return None
    x = Fr["L"][arm:e5].min() if up else Fr["H"][arm:e5].max()
    return e5, float(x), dict(sig_t=int(F["tc"][k]))


def trig_touch(S, Fr):
    """Resting limit at the near edge; fills when price trades 1 tick through it (gap through -> the open)."""
    up = S["dir"] == "long"; arm = S["_arm"]; edge = S["zhi"] if up else S["zlo"]
    seg = slice(arm, S["cut5"] + 1)
    w = np.flatnonzero(Fr["L"][seg] <= edge - TICK) if up else np.flatnonzero(Fr["H"][seg] >= edge + TICK)
    if not len(w): return None
    j = arm + int(w[0]); O = Fr["O"][j]
    px = min(edge, O) if up else max(edge, O)
    return j, float(S["zlo"] if up else S["zhi"]), dict(limit=float(px))


def null_pool(S, Fr):
    """Random-entry null: every 5m bar after the touch whose low (high) is at the level; entry at the next open,
    structural extreme = lowest low (highest high) of the last 5 bars."""
    up = S["dir"] == "long"; arm = S["_arm"]
    j = np.arange(arm, min(S["cut5"], S["s1"] - 1))
    if not len(j): return []
    x = Fr["L"][j] if up else Fr["H"][j]
    j = j[_loc_mask(S, x)]
    out = []
    for jj in j:
        lo = max(jj - 4, S["s0"])
        xx = Fr["L"][lo:jj + 1].min() if up else Fr["H"][lo:jj + 1].max()
        out.append((int(jj + 1), float(xx), {}))
    return out


TRIGGERS = {}
def _reg(name, fn): TRIGGERS[name] = fn
_reg("touch_limit", trig_touch)
_reg("reclaim_5m", lambda S, Fr: trig_reclaim(S, Fr, 5))
_reg("reclaim_15m", lambda S, Fr: trig_reclaim(S, Fr, 15))
for _tf in (5, 10, 15, 30, 60):
    for _R in (1, 2):
        _reg(f"rsi_div_{_tf}m_R{_R}", (lambda tf, R: lambda S, Fr: trig_div(S, Fr, tf, "rsi", R))(_tf, _R))
        _reg(f"macdh_div_{_tf}m_R{_R}", (lambda tf, R: lambda S, Fr: trig_div(S, Fr, tf, "hist", R))(_tf, _R))
        _reg(f"macd_div_{_tf}m_R{_R}", (lambda tf, R: lambda S, Fr: trig_div(S, Fr, tf, "macd", R))(_tf, _R))
    _reg(f"rsi_div_ext_{_tf}m_R1", (lambda tf: lambda S, Fr: trig_div(S, Fr, tf, "rsi", 1, "ext"))(_tf))
for _tf in (5, 10, 15, 30):
    _reg(f"rsi_hook30_{_tf}m", (lambda tf: lambda S, Fr: trig_hook(S, Fr, tf, 30))(_tf))
    _reg(f"rsi_hook35_{_tf}m", (lambda tf: lambda S, Fr: trig_hook(S, Fr, tf, 35))(_tf))
for _tf in (5, 10, 15):
    _reg(f"mss_{_tf}m", (lambda tf: lambda S, Fr: trig_mss(S, Fr, tf))(_tf))
for _tf in (5, 15, 30):
    _reg(f"reject_{_tf}m", (lambda tf: lambda S, Fr: trig_pattern(S, Fr, tf, "rej"))(_tf))
    _reg(f"engulf_{_tf}m", (lambda tf: lambda S, Fr: trig_pattern(S, Fr, tf, "eng"))(_tf))


# ------------------------------------------------------------------ exits
EXITS = {   # name: (stop floor x ATR5, target rule, breakeven at +R or None)
    "base": (1.0, "pharmd", None),
    "floor0.5": (0.5, "pharmd", None),
    "floor1.5": (1.5, "pharmd", None),
    "be1R": (1.0, "pharmd", 1.0),
    "fix2R": (1.0, "fix2", None),
    "fix1.5R": (1.0, "fix1.5", None),
}


def _first_true(m):
    w = np.flatnonzero(m)
    return int(w[0]) if len(w) else BIG


def simulate(S, Fr, ent, exit_name="base"):
    """ent = (entry 5m index, structural extreme, info).  Returns a row dict or None (skipped: no target >= 1R,
    target on the wrong side, or the entry bar opened through the stop)."""
    floor_k, trule, be = EXITS[exit_name]
    j, x, info = ent
    limit = info.get("limit")
    up = S["dir"] == "long"; sg = 1 if up else -1
    s1 = S["s1"]
    if j >= s1: return None
    O, H, L, C = Fr["O"][j:s1], Fr["H"][j:s1], Fr["L"][j:s1], Fr["C"][j:s1]
    e = limit if limit is not None else O[0] + sg * SLIP
    a5, a15 = S["atr5"], S["atr15"]
    stp = x - sg * TICK
    stp = min(stp, e - floor_k * a5) if up else max(stp, e + floor_k * a5)
    rk = (e - stp) * sg
    if rk < 0.2 * a15: rk = 0.2 * a15; stp = e - sg * rk
    stp = (math.floor(stp / TICK + 1e-9) if up else math.ceil(stp / TICK - 1e-9)) * TICK   # on the tick grid, away from entry
    rk = (e - stp) * sg
    if limit is None and (O[0] - stp) * sg <= 0: return None
    if trule == "pharmd":
        tg = [t for t in S["tg"] if (t - e) * sg > 0]
        if not tg: return None
        pick = next((t for t in tg if (t - e) * sg / rk >= 1.5), tg[-1])
        if (pick - e) * sg / rk < 1.0: return None
        tgt = pick
    else:
        tgt = round((e + sg * float(trule[3:]) * rk) / TICK) * TICK
    # long-space arrays
    if up: Hs, Ls, Os, Cs, es, ss, ts = H, L, O, C, e, stp, tgt
    else: Hs, Ls, Os, Cs, es, ss, ts = -L, -H, -O, -C, -e, -stp, -tgt
    if limit is not None:            # a limit's fill bar: its high (long) may have come BEFORE the fill -> no favourable credit
        Hs = Hs.copy(); Hs[0] = es
    stop_hit = Ls <= ss
    tgt_hit = Hs >= ts + TICK
    i_s, i_t = _first_true(stop_hit), _first_true(tgt_hit)
    i_b = _first_true(Hs - es >= be * rk) if be is not None else BIG
    if be is None or i_b >= min(i_s, i_t):
        if i_s <= i_t and i_s < BIG: px = (min(ss, Os[i_s]) if i_s > 0 else ss) - SLIP; how = "stop"; ix = i_s
        elif i_t < BIG: px = ts; how = "target"; ix = i_t
        else: px = Cs[-1] - SLIP; how = "close"; ix = len(Cs) - 1
    else:
        bp = es + TICK
        s2 = Ls <= bp; s2[:i_b + 1] = False
        j_s = _first_true(s2)
        if j_s <= i_t and j_s < BIG: px = min(bp, Os[j_s]) - SLIP; how = "be"; ix = j_s
        elif i_t < BIG: px = ts; how = "target"; ix = i_t
        else: px = Cs[-1] - SLIP; how = "close"; ix = len(Cs) - 1
    pts = px - es
    n = RISK / ((rk + SLIP) * MICRO[S["sym"]])
    pnl = n * (pts * MICRO[S["sym"]] - COMM)
    # exit-independent: first passage +/-1 ATR15 from the fill (adverse first on ties), 60-min move, MFE/MAE
    i_dn, i_up = _first_true(Ls <= es - a15), _first_true(Hs >= es + a15)
    fp = np.nan if (i_dn == BIG and i_up == BIG) else (0.0 if i_dn <= i_up else 1.0)
    k60 = min(11, len(Cs) - 1)
    mins = Fr["mins"][j]
    return dict(date=S["date"], sym=S["sym"], uni=S["uni"], id=S["id"], dir=S["dir"], grade=S.get("grade", ""),
                entry_t=int(Fr["t5"][j]), rth=bool(570 <= mins < 960), e=e, stop=stp, risk=rk, risk_atr5=rk / a5,
                tgt=tgt, tgtR=abs(tgt - e) / rk, exit=how, pts=pts, pnl=pnl, R=pnl / RISK, fp1=fp,
                fwd60=(Cs[k60] - es) / a15, mfe60=(Hs[:k60 + 1].max() - es) / a15, mae60=(es - Ls[:k60 + 1].min()) / a15,
                bars=ix + 1)
