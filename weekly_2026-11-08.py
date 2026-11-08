"""Weekly chart spec for the week of 11/8 (letter dated 11/6). Run: python weekly_2026-11-08.py"""
import charts, pandas as pd
tz = "America/New_York"
ES, NQ = charts.load_1h("ES"), charts.load_1h("NQ")
ES5, NQ5 = charts.load("ES"), charts.load("NQ")
s = pd.Timestamp("2026-10-26 09:30", tz=tz); e = pd.Timestamp("2026-11-06 16:15", tz=tz)
w4 = ("wk 10/26", pd.Timestamp("2026-10-25 18:00", tz=tz), pd.Timestamp("2026-10-30 16:00", tz=tz))
w5 = ("wk 11/2", pd.Timestamp("2026-11-01 18:00", tz=tz), pd.Timestamp("2026-11-06 16:00", tz=tz))

es_lv = [
 {"p":[7815,7820],"label":"","kind":"up","strong":True},
 {"p":[7784,7788],"label":"","kind":"up"},
 {"p":[7769,7772],"label":"","kind":"up"},
 {"p":[7746.25],"label":"wk high","kind":"ref"},
 {"p":[7738,7741],"label":"","kind":"up"},
 {"p":[7725,7730],"label":"","kind":"up"},
 {"p":[7708,7713],"label":"A-singles fill → squeeze above","kind":"up","strong":True},
 {"p":[7670,7680],"label":"LAAF · sellers' last stand","kind":"up","strong":True},
 {"p":[7645,7650],"label":"white box top · structural reclaim","kind":"up","strong":True},
 {"p":[7619,7624],"label":"","kind":"up","strong":True},
 {"p":[7603],"label":"A-period singles 7603-7712.5","kind":"ref"},
 {"p":[7569,7575],"label":"Sept low · LAAF monitor · top of B-singles","kind":"pivot","strong":True},
 {"p":[7539,7543],"label":"Aug low · LAAF · bottom of B-singles","kind":"pivot","strong":True},
 {"p":[7497,7504],"label":"7480-7520 HTF decision","kind":"pivot","strong":True},
 {"p":[7469,7473],"label":"Fri high · LAAF → daily balance","kind":"pivot","strong":True},
 {"p":[7392],"label":"Fri low","kind":"ref"},
 {"p":[7388,7396],"label":"Thu spike base · first reclaim","kind":"pivot","strong":True},
 {"p":[7377.25],"label":"Thu RTH low","kind":"ref"},
 {"p":[7369,7372],"label":"","kind":"down"},
 {"p":[7346],"label":"July RTH low","kind":"ref"},
 {"p":[7322.25],"label":"wk ETH low · LBAF watch","kind":"ref"},
 {"p":[7313,7317],"label":"June demand · YTD VWAP between","kind":"down"},
 {"p":[7292,7296],"label":"LBAF monitor","kind":"down"},
 {"p":[7269,7275],"label":"","kind":"down"},
 {"p":[7247.25],"label":"June RTH low","kind":"ref"},
 {"p":[7232,7240],"label":"June ETH low · LBAF monitor","kind":"down"},
 {"p":[7208,7214],"label":"","kind":"down"},
 {"p":[7177,7186],"label":"LBAF monitor","kind":"down","strong":True},
 {"p":[7169,7170],"label":"","kind":"down","strong":True}]
es_marks = [
 {"t":pd.Timestamp("2026-10-28 16:00",tz=tz),"y":7819.5,"label":"WED 10/28 FOMC: 15-20 rejected","dy":22,"dx":-60},
 {"t":pd.Timestamp("2026-10-30 14:50",tz=tz),"y":7558.25,"label":"FRI 10/30: Sept low taken → monthly OTFU ended","dy":-60,"dx":-100},
 {"t":pd.Timestamp("2026-11-03 22:05",tz=tz),"y":7490.0,"label":"ELECTION: 7490 → gap-up reversal to 7746.25","dy":-70,"dx":-120},
 {"t":pd.Timestamp("2026-11-04 13:05",tz=tz),"y":7746.25,"label":"WED: 7746.25 at 38-41 / ATH VWAP","dy":30,"dx":-60},
 {"t":pd.Timestamp("2026-11-05 15:55",tz=tz),"y":7377.25,"label":"THU: bloodbath — B-singles 7539-80, A-singles 7603-7712; July RTH low 7346 to the tick AH","dy":-110,"dx":-200},
 {"t":pd.Timestamp("2026-11-06 09:50",tz=tz),"y":7469.0,"label":"FRI: muted relief, 7392-7469 = Fri range; ETH low 7322.25","dy":55,"dx":-130}]
charts.weekly("ES", es_lv, ES, s, e, "charts/2026-W46_ES_weekly.png",
              "ES weekly  ·  10/26 – Fri 11/6  ·  week of 11/8 plan", profile_ranges=[w4, w5], marks=es_marks, d5prof=ES5)

nq_lv = [
 {"p":[29038,29069],"label":"HTF decision · Sept low area","kind":"up","strong":True},
 {"p":[28969],"label":"wk high · bear gap to 29405","kind":"ref"},
 {"p":[28944,28969],"label":"","kind":"up"},
 {"p":[28847,28869],"label":"LAAF monitor","kind":"up","strong":True},
 {"p":[28443,28485],"label":"scene of the crime · LAAF","kind":"up","strong":True},
 {"p":[28200,28233],"label":"June low · first HTF reclaim","kind":"up","strong":True},
 {"p":[28080,28100],"label":"first real volume · Mon low","kind":"up","strong":True},
 {"p":[27588,27622],"label":"election low · Thu B-high · LAAF","kind":"pivot","strong":True},
 {"p":[27425,27458],"label":"Fri high · B-singles · LAAF","kind":"pivot","strong":True},
 {"p":[27313,27339],"label":"July RTH low · capped Fri","kind":"pivot","strong":True},
 {"p":[27201.5],"label":"July ETH low","kind":"ref"},
 {"p":[27110,27123],"label":"daily · Fri 5pm / VAL","kind":"ref"},
 {"p":[27057],"label":"daily · Fri OR5 low","kind":"ref"},
 {"p":[26988.5],"label":"Fri low","kind":"ref"},
 {"p":[26969,26987],"label":"held Fri","kind":"pivot","strong":True},
 {"p":[26805,26840],"label":"must hold / quick LBAF","kind":"down","strong":True},
 {"p":[26718,26732],"label":"daily · Thu RTH low / spike base","kind":"ref"},
 {"p":[26500,26523],"label":"","kind":"down"},
 {"p":[26366.5],"label":"wk ETH low · double-top back-test","kind":"ref"},
 {"p":[26369,26408],"label":"LBAF monitor","kind":"down","strong":True},
 {"p":[26258,26291],"label":"LBAF monitor","kind":"down","strong":True},
 {"p":[26072,26102],"label":"","kind":"down","strong":True},
 {"p":[25990,26016],"label":"routine trappy back-test","kind":"down","strong":True},
 {"p":[25846,25869],"label":"LBAF monitor","kind":"down","strong":True},
 {"p":[25656],"label":"deep back-test · LBAF","kind":"ref"},
 {"p":[25516,25550],"label":"LBAF monitor","kind":"down","strong":True},
 {"p":[25461,25469],"label":"","kind":"down","strong":True},
 {"p":[25369,25393],"label":"","kind":"down","strong":True},
 {"p":[25245,25269],"label":"deepest back-test bulls can afford","kind":"down","strong":True}]
nq_marks = [
 {"t":pd.Timestamp("2026-10-28 16:00",tz=tz),"y":30178.0,"label":"WED 10/28 FOMC: failed under 210-237","dy":40,"dx":-70},
 {"t":pd.Timestamp("2026-10-30 14:50",tz=tz),"y":28232.75,"label":"FRI 10/30: June low","dy":-120,"dx":-40},
 {"t":pd.Timestamp("2026-11-03 22:05",tz=tz),"y":27615.75,"label":"ELECTION: 27615.75 (May low) → 28969","dy":-320,"dx":-180},
 {"t":pd.Timestamp("2026-11-04 10:15",tz=tz),"y":28969.0,"label":"WED: 28969, rejected at the Sept low","dy":80,"dx":-70},
 {"t":pd.Timestamp("2026-11-05 15:55",tz=tz),"y":26718.0,"label":"THU: thru the July lows → 26718; Globex 26366.5 = double-top back-test","dy":-260,"dx":-130},
 {"t":pd.Timestamp("2026-11-06 09:50",tz=tz),"y":27425.0,"label":"FRI: relief to 27425 (B-singles), 26988.5 low; 313-339 capped","dy":110,"dx":-110}]
charts.weekly("NQ", nq_lv, NQ, s, e, "charts/2026-W46_NQ_weekly.png",
              "NQ weekly  ·  10/26 – Fri 11/6  ·  week of 11/8 plan", profile_ranges=[w4, w5], marks=nq_marks, d5prof=NQ5)
print("ok")
