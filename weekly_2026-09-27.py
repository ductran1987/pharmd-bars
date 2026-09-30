"""Weekly chart spec for the week of 9/27 (letter dated 9/26). Run: python weekly_2026-09-27.py"""
import charts, pandas as pd
tz = "America/New_York"
ES, NQ = charts.load_1h("ES"), charts.load_1h("NQ")   # hourly: 60 days, so the whole week stays on the chart
ES5, NQ5 = charts.load("ES"), charts.load("NQ")          # 5-min for the profiles
s = pd.Timestamp("2026-09-18 09:30", tz=tz); e = pd.Timestamp("2026-09-30 18:05", tz=tz)
wk = ("last wk", pd.Timestamp("2026-09-20 18:00", tz=tz), pd.Timestamp("2026-09-25 16:00", tz=tz))
mon = ("Mon-Wed", pd.Timestamp("2026-09-27 18:00", tz=tz), e)

es_lv = [
 {"p":[7917,7920],"label":"key target (as low as 7911)","kind":"up","strong":True},
 {"p":[7893,7896],"label":"","kind":"up"},
 {"p":[7880],"label":"≈ SPX ATH on ES","kind":"up"},
 {"p":[7869,7872],"label":"","kind":"up","strong":True},
 {"p":[7848.5],"label":"last wk high (poor · begging)","kind":"ref"},
 {"p":[7846,7849],"label":"","kind":"up"},
 {"p":[7815,7822],"label":"KEY · false-failed-breakout spot","kind":"pivot","strong":True},
 {"p":[7749,7752],"label":"KEY · wk range floor","kind":"pivot","strong":True},
 {"p":[7725.25],"label":"last wk RTH low (Thu)","kind":"ref"},
 {"p":[7718,7725],"label":"bullish gap 9/18→9/21","kind":"down","strong":True},
 {"p":[7696,7699],"label":"","kind":"down"},
 {"p":[7678,7681],"label":"","kind":"down"},
 {"p":[7666,7669],"label":"monitor LBAF","kind":"down"},
 {"p":[7648.75],"label":"prior ATH · top of multi-wk box","kind":"ref"},
 {"p":[7644,7648],"label":"monitor LBAF · FOMC low below","kind":"down","strong":True}]
es_marks = [
 {"t":pd.Timestamp("2026-09-21 09:30",tz=tz),"y":7760.5,"label":"Mon open 7760.5 — gapped above prior wk high, ATH by Mon","dy":-40,"dx":3},
 {"t":pd.Timestamp("2026-09-22 11:00",tz=tz),"y":7848.5,"label":"Tue high 7848.5 = wk high","dy":22,"dx":-15},
 {"t":pd.Timestamp("2026-09-24 10:30",tz=tz),"y":7725.25,"label":"Wed→Thu selloff; held prior wk high (ETH wick only)","dy":-22,"dx":3},
 {"t":pd.Timestamp("2026-09-25 15:30",tz=tz),"y":7814.75,"label":"Fri: back-test of 7815-22 from below","dy":30,"dx":-35},
 {"t":pd.Timestamp("2026-09-28 10:55",tz=tz),"y":7726.0,"label":"MON: lost 89-91 & 49-52; low 7726 = Thu low to the tick","dy":-38,"dx":-100},
 {"t":pd.Timestamp("2026-09-29 13:00",tz=tz),"y":7712.25,"label":"TUE: ON LBAF of 18-25 +60; cash sold to 7712, held 7706-12","dy":-52,"dx":-150},
 {"t":pd.Timestamp("2026-09-30 15:55",tz=tz),"y":7709.25,"label":"WED: 49-52 → 7782 → LAAF IB high → liquidation 7709; AH 7705.5","dy":-70,"dx":-60}]
charts.weekly("ES", es_lv, ES, s, e, "charts/2026-W40_ES_weekly.png",
              "ES weekly  ·  9/18 – Wed 9/30 (+AH)  ·  week of 9/27 plan", profile_ranges=[wk, mon], marks=es_marks, d5prof=ES5)

nq_lv = [
 {"p":[32369],"label":"first breakout target (conservative)","kind":"up"},
 {"p":[32269,32293],"label":"","kind":"up","strong":True},
 {"p":[32020,32044],"label":"","kind":"up","strong":True},
 {"p":[31646,31669],"label":"","kind":"up","strong":True},
 {"p":[31269,31288],"label":"","kind":"up"},
 {"p":[31125,31143],"label":"","kind":"up"},
 {"p":[31094.75],"label":"last wk ETH high — breakout line","kind":"ref"},
 {"p":[31056,31069],"label":"last wk RTH high 31065.5","kind":"up","strong":True},
 {"p":[30951,30969],"label":"top of 4-month box · LAAF watch","kind":"pivot","strong":True},
 {"p":[30827,30846],"label":"Fri midpoint · false-fail spot","kind":"pivot"},
 {"p":[30684],"label":"Fri low","kind":"ref"},
 {"p":[30638,30669],"label":"KEY · bulls in control above","kind":"pivot","strong":True},
 {"p":[30469,30493],"label":"Thu low","kind":"down","strong":True},
 {"p":[30369,30391],"label":"Thu premarket low 370","kind":"down","strong":True},
 {"p":[30269,30293],"label":"","kind":"down"},
 {"p":[30216.5],"label":"Mon low = wk RTH low · LBAF watch","kind":"ref"},
 {"p":[30137,30155],"label":"","kind":"down"},
 {"p":[30040,30069],"label":"","kind":"down"},
 {"p":[29932,29969],"label":"gap fill 29937.75","kind":"down","strong":True}]
nq_marks = [
 {"t":pd.Timestamp("2026-09-21 09:30",tz=tz),"y":30221.5,"label":"Mon open 30221.5 — SMH/MAGS confirmed, off to the races","dy":-120,"dx":3},
 {"t":pd.Timestamp("2026-09-22 14:00",tz=tz),"y":31065.5,"label":"Tue: new ATH 31065.5 (QQQ ATH overnight) → LAAF","dy":90,"dx":3},
 {"t":pd.Timestamp("2026-09-24 09:30",tz=tz),"y":30493.25,"label":"Thu low — never reached Mon open","dy":-110,"dx":3},
 {"t":pd.Timestamp("2026-09-25 14:00",tz=tz),"y":30951.5,"label":"Fri high = back-test of box top from below","dy":110,"dx":-40},
 {"t":pd.Timestamp("2026-09-28 10:45",tz=tz),"y":30356.75,"label":"MON: through 638-669 & Thu low → 30357, bounced ~560","dy":-100,"dx":-70},
 {"t":pd.Timestamp("2026-09-29 12:45",tz=tz),"y":30504.5,"label":"TUE: inside day; ON held 369-391; capped <638-669","dy":-210,"dx":-100},
 {"t":pd.Timestamp("2026-09-30 11:50",tz=tz),"y":30906,"label":"WED: to 30906 (wk open 870 capped) → 827-846 filled → 680; AH 636.5 held","dy":170,"dx":-150}]
charts.weekly("NQ", nq_lv, NQ, s, e, "charts/2026-W40_NQ_weekly.png",
              "NQ weekly  ·  9/18 – Wed 9/30 (+AH)  ·  week of 9/27 plan", profile_ranges=[wk, mon], marks=nq_marks, d5prof=NQ5)
print("ok")
