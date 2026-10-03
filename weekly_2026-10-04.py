"""Weekly chart spec for the week of 10/4 (letter dated 10/2). Run: python weekly_2026-10-04.py"""
import charts, pandas as pd
tz = "America/New_York"
ES, NQ = charts.load_1h("ES"), charts.load_1h("NQ")
ES5, NQ5 = charts.load("ES"), charts.load("NQ")
s = pd.Timestamp("2026-09-21 09:30", tz=tz); e = pd.Timestamp("2026-10-02 16:15", tz=tz)
w1 = ("wk 9/21", pd.Timestamp("2026-09-20 18:00", tz=tz), pd.Timestamp("2026-09-25 16:00", tz=tz))
w2 = ("wk 9/28", pd.Timestamp("2026-09-27 18:00", tz=tz), pd.Timestamp("2026-10-02 16:00", tz=tz))

es_lv = [
 {"p":[7848.5],"label":"ATH (9/22)","kind":"ref"},
 {"p":[7846,7849],"label":"ATH range · LAAF watch","kind":"up"},
 {"p":[7815,7822],"label":"firm base needed · LAAF watch","kind":"pivot","strong":True},
 {"p":[7810.25],"label":"Fri high","kind":"ref"},
 {"p":[7780,7784],"label":"START HERE · Sept VAH","kind":"pivot","strong":True},
 {"p":[7754],"label":"Fri low","kind":"ref"},
 {"p":[7747,7754],"label":"massive all wk · RTH gap 41-54","kind":"pivot","strong":True},
 {"p":[7740,7741.25],"label":"Thu spike base / high","kind":"ref"},
 {"p":[7723,7726],"label":"narrowed from 7718-25","kind":"down","strong":True},
 {"p":[7706,7712],"label":"OG weekly · weakness below = wk low","kind":"down","strong":True},
 {"p":[7696,7699],"label":"daily until touched · demand","kind":"ref"},
 {"p":[7678,7681],"label":"","kind":"down"},
 {"p":[7672.75],"label":"last wk low (Thu)","kind":"ref"},
 {"p":[7666,7669],"label":"monitor LBAF","kind":"down"},
 {"p":[7644,7648],"label":"monitor LBAF · big target","kind":"down","strong":True}]
es_marks = [
 {"t":pd.Timestamp("2026-09-22 11:00",tz=tz),"y":7848.5,"label":"9/22 ATH 7848.5","dy":-16,"dx":12},
 {"t":pd.Timestamp("2026-09-28 10:55",tz=tz),"y":7726.0,"label":"MON: gave back Fri's cover rally; YM lost 51969","dy":-40,"dx":-110},
 {"t":pd.Timestamp("2026-09-30 15:55",tz=tz),"y":7709.25,"label":"WED: liquidation close 7709","dy":-48,"dx":-90},
 {"t":pd.Timestamp("2026-10-01 11:10",tz=tz),"y":7672.75,"label":"THU: trap — took out prior wk low (7673), LBAF, spike to 7741","dy":-28,"dx":-150},
 {"t":pd.Timestamp("2026-10-02 10:30",tz=tz),"y":7810.25,"label":"FRI: ON rally into NFP; soft print, bonds stuffed; failed open drive, struggled w/ 80-84; closed 7779","dy":-12,"dx":-125}]
charts.weekly("ES", es_lv, ES, s, e, "charts/2026-W41_ES_weekly.png",
              "ES weekly  ·  9/21 – Fri 10/2  ·  week of 10/4 plan", profile_ranges=[w1, w2], marks=es_marks, d5prof=ES5)

nq_lv = [
 {"p":[31527,31545],"label":"first target on breakout","kind":"up"},
 {"p":[31400,31420],"label":"fresh-LAAF-of-wk-high watch","kind":"up"},
 {"p":[31282.5],"label":"Fri high = ATH · the breakout line","kind":"ref"},
 {"p":[31269,31288],"label":"KEY · sustain above = breakout","kind":"pivot","strong":True},
 {"p":[31125,31143],"label":"","kind":"pivot"},
 {"p":[31056,31069],"label":"first reclaim after LBAF","kind":"pivot","strong":True},
 {"p":[30988],"label":"Fri low · LBAF watch","kind":"ref"},
 {"p":[30951,30969],"label":"MOST CRITICAL · June ATH","kind":"pivot","strong":True},
 {"p":[30869,30906],"label":"Wed/Thu highs · gap fill","kind":"down","strong":True},
 {"p":[30706,30725],"label":"","kind":"down"},
 {"p":[30625],"label":"VPOC · demand 595-635","kind":"down","strong":True},
 {"p":[30504,30546],"label":"Thu low · LBAF monitor","kind":"down","strong":True},
 {"p":[30369,30391],"label":"","kind":"down"},
 {"p":[30356.75],"label":"last wk low (Mon)","kind":"ref"},
 {"p":[30269,30293],"label":"","kind":"down"},
 {"p":[30216.5],"label":"9/21 low · balance break","kind":"ref"}]
nq_marks = [
 {"t":pd.Timestamp("2026-09-22 14:00",tz=tz),"y":31065.5,"label":"9/22 ATH 31065.5","dy":60,"dx":-10},
 {"t":pd.Timestamp("2026-09-28 10:45",tz=tz),"y":30356.75,"label":"MON: low of wk 30357, held 369-391 (quick LBAF) → slow grind up","dy":-110,"dx":-120},
 {"t":pd.Timestamp("2026-09-30 11:50",tz=tz),"y":30906,"label":"WED high 30906","dy":40,"dx":-60},
 {"t":pd.Timestamp("2026-10-01 02:10",tz=tz),"y":31151.5,"label":"THU: Asia ATH 31151; cash LAAF to 30529","dy":80,"dx":-120},
 {"t":pd.Timestamp("2026-10-02 10:15",tz=tz),"y":31282.5,"label":"FRI: new ATH 31282.5 (2nd of the week) yet value overlapped LOWER on the week; failed open drive; closed 31070 RIGHT at the Sept high","dy":130,"dx":-100}]
charts.weekly("NQ", nq_lv, NQ, s, e, "charts/2026-W41_NQ_weekly.png",
              "NQ weekly  ·  9/21 – Fri 10/2  ·  week of 10/4 plan", profile_ranges=[w1, w2], marks=nq_marks, d5prof=NQ5)
print("ok")
