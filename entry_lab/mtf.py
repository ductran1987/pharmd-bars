"""Multi-timeframe / multi-oscillator confluence entries at PharmD levels.

A combo fires when signal X and signal Y have both happened at the same level touch with their entry bars no more
than 12 bars (60 min) apart; entry = the later one's entry bar; structural extreme = the deeper of the two lows
(highs for shorts).  'X then Y' variants require Y to come at or after X (higher-timeframe setup, lower-timeframe
trigger).

python entry_lab/mtf.py -> entry_lab/out/mtf_<U>.pkl
"""
import os, sys, pickle, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab
import numpy as np, pandas as pd

GAP = 12


def all_signals(S, Fr, fn, max_n=40):
    out = []; S = dict(S)
    while len(out) < max_n:
        r = fn(S, Fr)
        if r is None: break
        out.append(r); S["_arm"] = r[0]
    return out


T = lab.TRIGGERS
DIV5 = ["rsi_div_5m_R1", "macd_div_5m_R2", "macdh_div_5m_R1"]
DIV15 = ["rsi_div_15m_R1", "macd_div_15m_R1", "macdh_div_15m_R1"]
DIV30 = ["rsi_div_30m_R1", "macd_div_30m_R1", "macdh_div_30m_R1"]
COMBOS = {
    "rsi5+rsi15": (["rsi_div_5m_R1"], ["rsi_div_15m_R1"], False),
    "macd5+macd15": (["macd_div_5m_R2"], ["macd_div_15m_R1"], False),
    "anydiv5+anydiv15": (DIV5, DIV15, False),
    "anydiv5+anydiv30": (DIV5, DIV30, False),
    "rsi5+macd5 (both osc)": (["rsi_div_5m_R1"], ["macd_div_5m_R2", "macdh_div_5m_R1"], False),
    "div15 then 5m candle": (DIV15, ["engulf_5m", "reject_5m"], True),
    "div30 then 5m candle": (DIV30, ["engulf_5m", "reject_5m"], True),
    "div15 then 5m div": (DIV15, DIV5, True),
    "div30 then 5m div": (DIV30, DIV5, True),
}


def combo_entry(S, Fr, xs, ys, ordered):
    X = sorted(s for n in xs for s in all_signals(S, Fr, T[n]))
    Y = sorted(s for n in ys for s in all_signals(S, Fr, T[n]))
    best = None
    up = S["dir"] == "long"
    for ex, xx, _ in X:
        for ey, xy, _ in Y:
            if ordered and ey < ex: continue
            if abs(ey - ex) > GAP: continue
            e = max(ex, ey); x = min(xx, xy) if up else max(xx, xy)
            if best is None or e < best[0]: best = (e, x, {})
    return best


def run(uni, setups):
    rows = []; t0 = time.time()
    for S in setups:
        Fr = lab.frames(S["sym"], S["contract"])
        arm = lab.arm_index(S, Fr)
        if arm is None: continue
        S = dict(S, _arm=arm)
        for name, (xs, ys, ordered) in COMBOS.items():
            ent = combo_entry(S, Fr, xs, ys, ordered)
            if ent is None: continue
            for ex in ("base", "fix2R"):
                r = lab.simulate(S, Fr, ent, ex)
                if r is None: continue
                r.update(trig=name, exit_rule=ex); rows.append(r)
    D = pd.DataFrame(rows); D.to_pickle(os.path.join(lab.HERE, "out", f"mtf_{uni}.pkl"))
    print(uni, len(D), f"{time.time() - t0:.0f}s")
    return D


if __name__ == "__main__":
    A, B, days = pickle.load(open(os.path.join(lab.HERE, "out", "setups.pkl"), "rb"))
    run("A", A); run("B", B)
