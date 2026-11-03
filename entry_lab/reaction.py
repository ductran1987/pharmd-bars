"""Do PharmD levels produce a reaction at all?  First-passage odds from the level fill (resting limit, 1-tick trade-
through) at several scales, PharmD levels vs. pseudo-levels (random prices >= 1.5 ATR5 from every plan level, same
days, same touch/fill logic).  P(+k before -k) is 50% for a level with no information (minus drift / tie effects).

python entry_lab/reaction.py -> entry_lab/out/reaction.pkl
"""
import os, sys, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab
import numpy as np, pandas as pd

KS = (0.5, 1.0, 1.5, 2.0, 3.0)      # multiples of ATR15


def passage(Fr, S, j, e):
    up = S["dir"] == "long"; s1 = S["s1"]
    H, L = Fr["H"][j:s1], Fr["L"][j:s1]
    Hs, Ls, es = (H, L, e) if up else (-L, -H, -e)
    Hs = Hs.copy(); Hs[0] = es                    # fill bar: no favourable credit
    out = {}
    for k in KS:
        d = k * S["atr15"]
        i_dn = lab._first_true(Ls <= es - d); i_up = lab._first_true(Hs >= es + d)
        out[k] = np.nan if (i_dn == lab.BIG and i_up == lab.BIG) else (0.0 if i_dn <= i_up else 1.0)
    return out


def run_level_set(setups):
    rows = []
    for S in setups:
        Fr = lab.frames(S["sym"], S["contract"])
        arm = lab.arm_index(S, Fr)
        if arm is None: continue
        S = dict(S, _arm=arm)
        ent = lab.trig_touch(S, Fr)
        if ent is None: continue
        j, x, info = ent
        r = passage(Fr, S, j, info["limit"])
        rows.append(dict(date=S["date"], sym=S["sym"], uni=S["uni"], id=S["id"], dir=S["dir"], grade=S.get("grade", ""),
                         rth=bool(570 <= Fr["mins"][j] < 960), **{f"p{k}": v for k, v in r.items()}))
    return pd.DataFrame(rows)


def pseudo_setups(days, per_day=10, seed=7):
    """Pseudo-levels from pre-session information only: a real plan level's price shifted by a random 1.5-4 ATR15
    up or down (keeps the same distance-from-price distribution as his levels), kept only if >= 1.5 ATR5 from every
    real plan level.  (Drawing from the session's own high-low range would leak the future: levels near the eventual
    session extreme are turning points by construction.)"""
    rng = np.random.default_rng(seed)
    out = []
    for D in days:
        zs = D["zones"]; a5, a15 = D["atr5"], D["atr15"]
        if not zs: continue
        got = 0; tries = 0
        while got < per_day and tries < 500:
            tries += 1
            z = zs[rng.integers(len(zs))]
            p = (z[0] + z[1]) / 2 + rng.choice([-1, 1]) * rng.uniform(1.5, 4.0) * a15
            p = round(p / lab.TICK) * lab.TICK
            if any(q[0] - 1.5 * a5 <= p <= q[1] + 1.5 * a5 for q in zs): continue
            for d in ("long", "short"):
                out.append(dict({k: D[k] for k in ("date", "sym", "contract", "atr5", "atr15", "s0", "s1", "cut5")},
                                uni="P", id=f"p{got}{d[0]}", dir=d, zlo=p, zhi=p, tg=[], tag="", grade=""))
            got += 1
    return out


if __name__ == "__main__":
    A, B, days = pickle.load(open(os.path.join(lab.HERE, "out", "setups.pkl"), "rb"))
    ra = run_level_set(A); rb = run_level_set(B); rp = run_level_set(pseudo_setups(days))
    R = pd.concat([ra, rb, rp]); R.to_pickle(os.path.join(lab.HERE, "out", "reaction.pkl"))
    for name, g in R.groupby("uni"):
        print(name, len(g), " ".join(f"P(+{k}) {g[f'p{k}'].mean():.3f}" for k in KS))
        for c in ("rth", "dir", "sym"):
            print("   ", c, {kk: f"{len(v)} | " + " ".join(f"{v[f'p{k}'].mean():.3f}" for k in KS) for kk, v in g.groupby(c)})
