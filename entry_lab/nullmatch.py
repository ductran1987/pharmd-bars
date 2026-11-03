"""Timing-matched random-entry benchmark, one per trigger.

For each trigger, take its own trades' (delay after the first touch, stop size in ATR5) pairs.  For every touched
setup of the same universe, draw pairs at random: enter at the 5m open `delay` bars after that setup's touch, with a
stop that many ATR5 away, the same targets, costs and session rules.  The benchmark knows nothing about price, so
"trigger minus benchmark" is the value of the trigger's timing and selection.

(Replaces the first null, which only entered on bars whose own low was at the level: bounces leave that pool at once
while breakdowns stay in it, so it over-sampled breakdowns.)

python entry_lab/nullmatch.py -> entry_lab/out/nullmatch_<U>.pkl  (one row per benchmark trade)
"""
import os, sys, pickle, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab
import numpy as np, pandas as pd

OUT = os.path.join(lab.HERE, "out")


def touched(setups):
    out = []
    for S in setups:
        Fr = lab.frames(S["sym"], S["contract"])
        arm = lab.arm_index(S, Fr)
        if arm is not None: out.append((dict(S, _arm=arm), Fr))
    return out


def run(U, setups, draws, seed=5, base=OUT):
    rng = np.random.default_rng(seed)
    TS = touched(setups)
    by = {(S["date"], S["sym"], S["id"]): (S, Fr) for S, Fr in TS}
    T = pd.read_pickle(os.path.join(base, f"trades_{U}.pkl")); b = T[T.exit_rule == "base"]
    rows = []; t0 = time.time()
    for trig, d in b.groupby("trig"):
        pairs = []
        for r in d.itertuples():
            S, Fr = by[(r.date, r.sym, r.id)]
            j = int(np.searchsorted(Fr["t5"], r.entry_t, "left"))
            pairs.append((j - S["_arm"], r.risk_atr5))
        pairs = np.array(pairs, dtype=float)
        if not len(pairs): continue
        for S, Fr in TS:
            up = S["dir"] == "long"; sg = 1 if up else -1
            for q in rng.integers(0, len(pairs), size=draws):
                dly, ka = pairs[q]
                j = S["_arm"] + int(dly)
                if j < S["s0"] or j > S["cut5"] or j >= S["s1"]: continue
                e = Fr["O"][j] + sg * lab.SLIP
                x = e - sg * ka * S["atr5"] + sg * lab.TICK          # simulate() puts the stop one tick past x
                r = lab.simulate(S, Fr, (j, float(x), {}), "base")
                if r is None: continue
                rows.append((trig, r["date"], r["sym"], r["dir"], r["rth"], r["R"], r["fp1"]))
        print(U, trig, len(pairs), f"{time.time() - t0:.0f}s", flush=True)
    N = pd.DataFrame(rows, columns=["trig", "date", "sym", "dir", "rth", "R", "fp1"])
    N.to_pickle(os.path.join(base, f"nullmatch_{U}.pkl"))
    print(U, "done", len(N))
    return N


if __name__ == "__main__":
    A, B, days = pickle.load(open(os.path.join(OUT, "setups.pkl"), "rb"))
    which = sys.argv[1] if len(sys.argv) > 1 else "AB"
    if "A" in which: run("A", A, draws=20)
    if "B" in which: run("B", B, draws=4)
