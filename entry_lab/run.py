"""Run every trigger x exit on universes A (PharmD fade trades) and B (all plan levels), plus the random-entry pool.

python entry_lab/run.py [A|B|AB]  -> entry_lab/out/trades_<U>.pkl, null_<U>.pkl, setups_<U>.pkl
"""
import os, sys, pickle, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab
import numpy as np, pandas as pd

OUT = os.path.join(lab.HERE, "out"); os.makedirs(OUT, exist_ok=True)
SETUPS = os.environ.get("SETUPS", os.path.join(OUT, "setups.pkl"))


def run(uni, setups):
    rows, nulls, info = [], [], []
    t0 = time.time()
    for n, S in enumerate(setups):
        Fr = lab.frames(S["sym"], S["contract"])
        arm = lab.arm_index(S, Fr)
        info.append(dict(date=S["date"], sym=S["sym"], uni=uni, id=S["id"], dir=S["dir"], grade=S["grade"],
                         touched=arm is not None, arm_t=int(Fr["t5"][arm]) if arm is not None else None,
                         arm_rth=bool(arm is not None and 570 <= Fr["mins"][arm] < 960)))
        if arm is None: continue
        S = dict(S, _arm=arm)
        for name, fn in lab.TRIGGERS.items():
            ent = fn(S, Fr)
            if ent is None: continue
            for ex in lab.EXITS:
                r = lab.simulate(S, Fr, ent, ex)
                if r is None: continue
                r.update(trig=name, exit_rule=ex, sig_t=ent[2].get("sig_t"), x=ent[1])
                rows.append(r)
        for k, ent in enumerate(lab.null_pool(S, Fr)):
            for ex in ("base", "fix2R"):
                r = lab.simulate(S, Fr, ent, ex)
                if r is None: continue
                r.update(trig="null", exit_rule=ex, cand=k, x=ent[1])
                nulls.append(r)
        if n % 500 == 0: print(uni, n, len(setups), f"{time.time() - t0:.0f}s", flush=True)
    T = pd.DataFrame(rows); N = pd.DataFrame(nulls); I = pd.DataFrame(info)
    T.to_pickle(os.path.join(OUT, f"trades_{uni}.pkl")); N.to_pickle(os.path.join(OUT, f"null_{uni}.pkl"))
    I.to_pickle(os.path.join(OUT, f"setups_{uni}.pkl"))
    print(uni, "done", len(T), "trade rows,", len(N), "null rows,", int(I.touched.sum()), "of", len(I), "touched",
          f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "AB"
    if not os.path.exists(SETUPS):
        A, B, days = lab.build_setups(); pickle.dump((A, B, days), open(SETUPS, "wb"))
    A, B, days = pickle.load(open(SETUPS, "rb"))
    if "A" in which: run("A", A)
    if "B" in which: run("B", B)


# ---------------------------------------------------------------- universe C: every signal of a trigger, anywhere
C_SPECS = ([(f"rsi_div_{tf}m_R{R}", "div", tf, ("rsi", R)) for tf in lab.TFS for R in (1, 2)] +
           [(f"macdh_div_{tf}m_R{R}", "div", tf, ("hist", R)) for tf in lab.TFS for R in (1, 2)] +
           [(f"macd_div_{tf}m_R{R}", "div", tf, ("macd", R)) for tf in lab.TFS for R in (1, 2)] +
           [(f"rsi_hook30_{tf}m", "hook", tf, 30) for tf in (5, 10, 15, 30)] +
           [(f"rsi_hook35_{tf}m", "hook", tf, 35) for tf in (5, 10, 15, 30)] +
           [(f"reject_{tf}m", "rej", tf, None) for tf in (5, 15, 30)] +
           [(f"engulf_{tf}m", "eng", tf, None) for tf in (5, 15, 30)])


def zone_dist(zs, x, up, a5):
    """(at_level by the B location rule, distance in ATR5 from x to the nearest plan level, 0 inside)."""
    at = False; best = np.inf
    for lo, hi in zs:
        if up: at |= (x <= hi + lab.LOC_TOL * a5) and (x >= lo - lab.LOC_DEPTH * a5)
        else: at |= (x >= lo - lab.LOC_TOL * a5) and (x <= hi + lab.LOC_DEPTH * a5)
        best = min(best, 0.0 if lo <= x <= hi else min(abs(x - lo), abs(x - hi)))
    return at, best / a5


def run_C(days):
    rows = []; t0 = time.time()
    for n, D in enumerate(days):
        Fr = lab.frames(D["sym"], D["contract"])
        for name, kind, tf, par in C_SPECS:
            F = Fr["tf"][tf]
            for up in (True, False):
                S = dict(D, dir="long" if up else "short", _arm=D["s0"] - 1, zlo=0.0, zhi=0.0, tg=[], uni="C", id=name, grade="")
                a, b = lab._tf_range(S, Fr, F)
                if kind == "div":
                    bull, bear, _, _ = F["div"][par]; R = par[1]
                    ks = lab._slice(bull if up else bear, a, b - R); x = (F["L"] if up else F["H"])[ks]
                elif kind == "hook":
                    kk, j0 = F["hook"][par][0 if up else 1]; R = 0
                    lo_, hi_ = np.searchsorted(kk, a, "left"), np.searchsorted(kk, b, "left")
                    ks, j0 = kk[lo_:hi_], j0[lo_:hi_]
                    x = lab._hook_x(F, up, ks, j0, a) if len(ks) else np.array([])
                else:
                    R = 0
                    ks = lab._slice(F[kind][0 if up else 1], a + (kind == "eng"), b)
                    if kind == "rej": x = (F["L"] if up else F["H"])[ks]
                    else: x = np.minimum(F["L"][ks], F["L"][ks - 1]) if up else np.maximum(F["H"][ks], F["H"][ks - 1])
                for k, xx in zip(ks, x):
                    e5 = int(F["e5"][k + R])
                    if e5 > D["cut5"] or e5 < D["s0"]: continue
                    r = lab.simulate(S, Fr, (e5, float(xx), {}), "fix2R")
                    if r is None: continue
                    at, dist = zone_dist(D["zones"], float(xx), up, D["atr5"])
                    r.update(trig=name, exit_rule="fix2R", at_level=at, dist_atr5=dist, x=float(xx))
                    rows.append(r)
        if n % 100 == 0: print("C", n, len(days), f"{time.time() - t0:.0f}s", flush=True)
    T = pd.DataFrame(rows); T.to_pickle(os.path.join(OUT, "trades_C.pkl"))
    print("C done", len(T), f"{time.time() - t0:.0f}s")


if __name__ == "__main__" and len(sys.argv) > 1 and "C" in sys.argv[1]:
    A, B, days = pickle.load(open(SETUPS, "rb"))
    run_C(days)
