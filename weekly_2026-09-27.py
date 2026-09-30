"""Weekly chart spec for the week of 9/27 (letter dated 9/26). Run: python weekly_2026-09-27.py"""
import charts, pandas as pd
tz = "America/New_York"
ES, NQ = charts.load("ES"), charts.load("NQ")
s = pd.Timestamp("2026-09-18 09:30", tz=tz); e = pd.Timestamp("2026-09-29 16:15", tz=tz)
wk = ("last wk", pd.Timestamp("2026-09-20 18:00", tz=tz), pd.Timestamp("2026-09-25 16:00", tz=tz))
mon = ("Mon-Tue", pd.Timestamp("2026-09-27 18:00", tz=tz), e)

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
 {"t":pd.Timestamp("2026-09-21 09:30",tz=tz),"y":7760.5,"label":"Mon open 7760.5 — gapped above prior wk high, ATH by Mon","dy":-40},
 {"t":pd.Timestamp("2026-09-22 11:00",tz=tz),"y":7848.5,"label":"Tue high 7848.5 = wk high","dy":22,"dx":-30},
 {"t":pd.Timestamp("2026-09-24 10:30",tz=tz),"y":7725.25,"label":"Wed→Thu selloff; held prior wk high (ETH wick only)","dy":-35},
 {"t":pd.Timestamp("2026-09-25 15:30",tz=tz),"y":7814.75,"label":"Fri: back-test of 7815-22 from below","dy":30,"dx":-70},
 {"t":pd.Timestamp("2026-09-28 10:55",tz=tz),"y":7726.0,"label":"MON: Iran deal rebuffed, oil +4%, 10y 5.2% → lost 89-91 & 49-52; low 7726 = Thu low to the tick","dy":-42,"dx":-215},
 {"t":pd.Timestamp("2026-09-29 13:00",tz=tz),"y":7712.25,"label":"TUE: ON LBAF of 7718-25 +60 → cash opened 58-59, sold to 7712, held OG 7706-12, closed in box","dy":-60,"dx":-245}]
charts.weekly("ES", es_lv, ES, s, e, "charts/2026-W40_ES_weekly.png",
              "ES weekly  ·  9/18 – Tue 9/29  ·  week of 9/27 plan", profile_ranges=[wk, mon], marks=es_marks)

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
 {"t":pd.Timestamp("2026-09-21 09:30",tz=tz),"y":30221.5,"label":"Mon open 30221.5 — SMH/MAGS confirmed, off to the races","dy":-120},
 {"t":pd.Timestamp("2026-09-22 14:00",tz=tz),"y":31065.5,"label":"Tue: new ATH 31065.5 (QQQ ATH taken overnight) → LAAF","dy":90,"dx":8},
 {"t":pd.Timestamp("2026-09-24 09:30",tz=tz),"y":30493.25,"label":"Thu low — never reached Mon open","dy":-110},
 {"t":pd.Timestamp("2026-09-25 14:00",tz=tz),"y":30951.5,"label":"Fri high = back-test of box top from below","dy":110,"dx":-80},
 {"t":pd.Timestamp("2026-09-28 10:45",tz=tz),"y":30356.75,"label":"MON: through 638-669 AND Thu low → 30357 in 369-391, bounced to ~560","dy":-100,"dx":-330},
 {"t":pd.Timestamp("2026-09-29 12:45",tz=tz),"y":30504.5,"label":"TUE: inside day; ON low held 369-391 again; capped below 638-669, 500-530 bid","dy":-235,"dx":-150}]
charts.weekly("NQ", nq_lv, NQ, s, e, "charts/2026-W40_NQ_weekly.png",
              "NQ weekly  ·  9/18 – Tue 9/29  ·  week of 9/27 plan", profile_ranges=[wk, mon], marks=nq_marks)
print("ok")
