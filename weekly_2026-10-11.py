"""Weekly chart spec for the week of 10/11 (letter dated 10/9). Run: python weekly_2026-10-11.py"""
import charts, pandas as pd
tz = "America/New_York"
ES, NQ = charts.load_1h("ES"), charts.load_1h("NQ")
ES5, NQ5 = charts.load("ES"), charts.load("NQ")
s = pd.Timestamp("2026-09-28 09:30", tz=tz); e = pd.Timestamp("2026-10-09 16:15", tz=tz)
w1 = ("wk 9/28", pd.Timestamp("2026-09-27 18:00", tz=tz), pd.Timestamp("2026-10-02 16:00", tz=tz))
w2 = ("wk 10/5", pd.Timestamp("2026-10-04 18:00", tz=tz), pd.Timestamp("2026-10-09 16:00", tz=tz))

es_lv = [
 {"p":[7917,7920],"label":"prior extension","kind":"up","strong":True},
 {"p":[7897.5],"label":"wk high = ATH (Tue)","kind":"ref"},
 {"p":[7893,7896],"label":"","kind":"up"},
 {"p":[7886,7888],"label":"daily","kind":"up"},
 {"p":[7870.5],"label":"Fri high","kind":"ref"},
 {"p":[7869,7872],"label":"START HERE","kind":"pivot","strong":True},
 {"p":[7853],"label":"daily","kind":"pivot"},
 {"p":[7846,7849],"label":"top of yellow multi-wk box","kind":"pivot"},
 {"p":[7838,7840],"label":"demand","kind":"ref"},
 {"p":[7826.75],"label":"Fri low","kind":"ref"},
 {"p":[7815,7820],"label":"bulls fine above (quick LBAF ok)","kind":"down","strong":True},
 {"p":[7780,7784],"label":"wk pivot · RTH low 7778.25","kind":"down","strong":True},
 {"p":[7760.25],"label":"wk ETH low","kind":"ref"},
 {"p":[7747,7754],"label":"must LBAF 80-84","kind":"down","strong":True},
 {"p":[7723,7726],"label":"liquidation target","kind":"down","strong":True},
 {"p":[7706,7712],"label":"~2x weekly straddle","kind":"down","strong":True}]
es_marks = [
 {"t":pd.Timestamp("2026-10-01 11:10",tz=tz),"y":7672.75,"label":"9/27 wk: trap low 7673 → NFP rip","dy":-14,"dx":-20},
 {"t":pd.Timestamp("2026-10-05 10:00",tz=tz),"y":7778.25,"label":"MON: 80-84 claimed fast → new highs","dy":-34,"dx":-60},
 {"t":pd.Timestamp("2026-10-06 10:30",tz=tz),"y":7897.5,"label":"TUE: ATH 7897.5 → sellers triggered a LAAF week","dy":16,"dx":-120},
 {"t":pd.Timestamp("2026-10-08 14:30",tz=tz),"y":7783.0,"label":"THU: selling held 80-84 from above — 'trading lower' never triggered","dy":-50,"dx":-160},
 {"t":pd.Timestamp("2026-10-09 15:00",tz=tz),"y":7870.5,"label":"FRI: YM moon mission; closed 7861 just under 69-72; abysmal volume","dy":12,"dx":-200}]
charts.weekly("ES", es_lv, ES, s, e, "charts/2026-W42_ES_weekly.png",
              "ES weekly  ·  9/28 – Fri 10/9  ·  week of 10/11 plan", profile_ranges=[w1, w2], marks=es_marks, d5prof=ES5)

nq_lv = [
 {"p":[31646,31669],"label":"","kind":"up","strong":True},
 {"p":[31616.5],"label":"wk high (Tue)","kind":"ref"},
 {"p":[31469,31481],"label":"firm reclaim → wk high","kind":"up","strong":True},
 {"p":[31422,31458],"label":"bearish RTH gap Tue→Wed","kind":"ref"},
 {"p":[31400,31420],"label":"LAAF watch into the gap","kind":"up"},
 {"p":[31269,31288],"label":"rotational w/ 125-145","kind":"pivot"},
 {"p":[31266.5],"label":"Fri PM high · 30m lower high?","kind":"ref"},
 {"p":[31180],"label":"Fri high","kind":"ref"},
 {"p":[31125,31145],"label":"CRITICAL · closed into it","kind":"pivot","strong":True},
 {"p":[31056,31069],"label":"Sept RTH high","kind":"pivot"},
 {"p":[30991],"label":"Fri low","kind":"ref"},
 {"p":[30951,30969],"label":"June high","kind":"down","strong":True},
 {"p":[30883,30906],"label":"","kind":"down"},
 {"p":[30792],"label":"wk low (Thu) · solidifies 30m lower high","kind":"ref"},
 {"p":[30706,30725],"label":"","kind":"down"},
 {"p":[30625],"label":"VPOC · demand 546-706","kind":"down","strong":True},
 {"p":[30504,30546],"label":"buyers rewarded here","kind":"down","strong":True}]
nq_marks = [
 {"t":pd.Timestamp("2026-10-02 10:15",tz=tz),"y":31282.5,"label":"9/27 wk high 31282.5","dy":60,"dx":-20},
 {"t":pd.Timestamp("2026-10-06 10:30",tz=tz),"y":31616.5,"label":"TUE: nominal new ATH 31616.5 → immediate pullback","dy":40,"dx":-130},
 {"t":pd.Timestamp("2026-10-08 15:30",tz=tz),"y":30792.0,"label":"THU: wk low 30792; Fri low held just off the June high","dy":-70,"dx":-140},
 {"t":pd.Timestamp("2026-10-09 09:30",tz=tz),"y":31266.5,"label":"FRI: PM high 31266.5 failed under 269-288; never above its open; OR5 mid capped PM; closed 31112 INTO 125-145","dy":90,"dx":-215}]
charts.weekly("NQ", nq_lv, NQ, s, e, "charts/2026-W42_NQ_weekly.png",
              "NQ weekly  ·  9/28 – Fri 10/9  ·  week of 10/11 plan", profile_ranges=[w1, w2], marks=nq_marks, d5prof=NQ5)
print("ok")
