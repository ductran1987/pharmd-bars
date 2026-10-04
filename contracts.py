"""Per-contract 5m bars (never spliced across a roll).

load(sym, contract) -> DataFrame(time, Open, High, Low, Close, Volume), ET tz, same format as charts.load().
Sources, merged per timestamp for the SAME contract only (Sierra preferred, yfinance fills gaps):
  - bars/contracts/<CONTRACT>_5m.csv   exported from Sierra Chart .scid files with tools/scid2csv.py (UTC -> ET,
                                       5m bar-start labels; checked against yfinance: 98-100% identical OHLC in RTH)
  - bars/<SYM>_5m.csv (yfinance ES=F/NQ=F continuous), cut into the contract segments listed in YF_SEGMENTS.
coverage(sym, contract) -> set of dates with a full RTH session (>= 75 of 78 bars).
"""
import os
from functools import lru_cache
import pandas as pd
import charts

tz = "America/New_York"
HERE = os.path.dirname(os.path.abspath(__file__))

# yfinance continuous front-month segments: (start, end) in ET, contract by month code + year digit.
# ES=F / NQ=F switched Sep -> Dec on Sun 2026-09-13 (first Dec bar 18:10 ET; -50 ES / -384 NQ gap).
# Add a row at each future roll (the next switch is expected on the Sunday of Dec 2026 expiry week).
YF_SEGMENTS = {
    "ES": [("2026-07-24 00:00", "2026-09-13 17:00", "ESU6"), ("2026-09-13 17:00", "2099-01-01", "ESZ6")],
    "NQ": [("2026-07-24 00:00", "2026-09-13 17:00", "NQU6"), ("2026-09-13 17:00", "2099-01-01", "NQZ6")],
}


def norm(contract):
    """'ESU26' / 'ESU6' -> 'ESU6' (single year digit, as used in plan files)."""
    c = contract.upper().replace("-CME", "")
    return c[:3] + c[-1]


def _sierra_name(contract):
    c = norm(contract)
    return f"{c[:3]}2{c[3]}"          # ESU6 -> ESU26 (2020s)


def _read(path):
    d = pd.read_csv(path)
    d["time"] = pd.to_datetime(d["time"], utc=True).dt.tz_convert(tz)
    return d


@lru_cache(maxsize=64)
def _load(sym, contract):
    c = norm(contract)
    parts = []
    p = os.path.join(HERE, "bars", "contracts", f"{_sierra_name(c)}_5m.csv")
    if os.path.exists(p):
        s = _read(p); s["src"] = 0; parts.append(s)
    for a, b, cc in YF_SEGMENTS.get(sym, []):
        if cc == c:
            y = charts.load(sym)
            y = y[(y.time >= pd.Timestamp(a, tz=tz)) & (y.time < pd.Timestamp(b, tz=tz))].copy(); y["src"] = 1
            parts.append(y)
    if not parts:
        return pd.DataFrame(columns=["time", "Open", "High", "Low", "Close", "Volume"])
    d = pd.concat(parts).sort_values(["time", "src"]).drop_duplicates("time", keep="first")
    return d.drop(columns="src").reset_index(drop=True)


def load(sym, contract):
    return _load(sym, norm(contract)).copy()


def rth(d):
    m = d.time.dt.hour * 60 + d.time.dt.minute
    return d[(m >= 570) & (m < 960)]


@lru_cache(maxsize=64)
def coverage(sym, contract):
    r = rth(_load(sym, norm(contract)))
    n = r.groupby(r.time.dt.date).size()
    return frozenset(n[n >= 75].index)


def available(sym):
    """Contracts with any data for sym."""
    out = set()
    for f in os.listdir(os.path.join(HERE, "bars", "contracts")):
        if f.startswith(sym) and f.endswith("_5m.csv"): out.add(norm(f.split("_")[0]))
    out |= {c for _, _, c in YF_SEGMENTS.get(sym, [])}
    return sorted(out)


if __name__ == "__main__":
    for s in ("ES", "NQ"):
        for c in available(s):
            cov = sorted(coverage(s, c))
            print(f"{c}: {len(cov)} full RTH days" + (f", {cov[0]} -> {cov[-1]}" if cov else ""))
