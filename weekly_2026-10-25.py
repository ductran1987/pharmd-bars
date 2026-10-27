"""Weekly chart spec for the week of 10/25 (letter dated 10/24). Run: python weekly_2026-10-25.py"""
import charts, pandas as pd
tz = "America/New_York"
ES, NQ = charts.load_1h("ES"), charts.load_1h("NQ")
ES5, NQ5 = charts.load("ES"), charts.load("NQ")
s = pd.Timestamp("2026-10-12 09:30", tz=tz); e = pd.Timestamp("2026-10-27 16:15", tz=tz)
w2 = ("wk 10/12", pd.Timestamp("2026-10-11 18:00", tz=tz), pd.Timestamp("2026-10-16 16:00", tz=tz))
w3 = ("wk 10/19", pd.Timestamp("2026-10-18 18:00", tz=tz), pd.Timestamp("2026-10-23 16:00", tz=tz))
w4 = ("Mon-Tue", pd.Timestamp("2026-10-25 18:00", tz=tz), e)

es_lv = [
 {"p":[7869,7872],"label":"","kind":"up","strong":True},
 {"p":[7838,7841],"label":"","kind":"up","strong":True},
 {"p":[7815,7820],"label":"bulls need this · range high","kind":"up","strong":True},
 {"p":[7812.25],"label":"wk high","kind":"ref"},
 {"p":[7784,7788],"label":"fresh supply","kind":"up"},
 {"p":[7769,7772],"label":"firm base → 15-20","kind":"up","strong":True},
 {"p":[7742.5,7751],"label":"bearish RTH gap · reactive","kind":"ref"},
 {"p":[7733,7735],"label":"LAAF monitor · supply","kind":"up","strong":True},
 {"p":[7724.5],"label":"Thu ARH","kind":"ref"},
 {"p":[7712,7717],"label":"reclaim = bulls comfortable","kind":"pivot","strong":True},
 {"p":[7707],"label":"daily","kind":"ref"},
 {"p":[7676,7681],"label":"box bottom · LBAF/reclaim","kind":"pivot","strong":True},
 {"p":[7658,7659],"label":"daily · failed-reclaim trigger","kind":"ref"},
 {"p":[7648.5],"label":"Fri low · wk low","kind":"ref"},
 {"p":[7644,7649],"label":"prior ATH · white box top","kind":"down","strong":True},
 {"p":[7631,7634],"label":"","kind":"down","strong":True},
 {"p":[7618,7622],"label":"","kind":"down"},
 {"p":[7591,7594],"label":"","kind":"down"},
 {"p":[7569,7575],"label":"major target · LBAF · mthly balance","kind":"down","strong":True},
 {"p":[7555,7558],"label":"","kind":"down"},
 {"p":[7541,7543],"label":"LBAF · yellow box bottom","kind":"down","strong":True},
 {"p":[7514,7517],"label":"","kind":"down"},
 {"p":[7497,7504],"label":"7460-7520 HTF decision point","kind":"down","strong":True},
 {"p":[7483,7486],"label":"","kind":"down","strong":True}]
es_marks = [
 {"t":pd.Timestamp("2026-10-12 14:50",tz=tz),"y":7846.25,"label":"MON 10/12: box 46-70","dy":-50,"dx":10},
 {"t":pd.Timestamp("2026-10-14 14:00",tz=tz),"y":7741.0,"label":"WED: CPI gap down, box broke","dy":-35,"dx":-40},
 {"t":pd.Timestamp("2026-10-16 15:05",tz=tz),"y":7676.0,"label":"FRI 10/16: failed reclaim → 7676 = mother bar","dy":-70,"dx":-70},
 {"t":pd.Timestamp("2026-10-20 10:30",tz=tz),"y":7791.5,"label":"TUE: bullish engulf → 7791.5","dy":55,"dx":-60},
 {"t":pd.Timestamp("2026-10-21 14:15",tz=tz),"y":7812.25,"label":"WED: 7812.25 = wk high, failed under 15-20 → LAAF of Fri high","dy":45,"dx":-120},
 {"t":pd.Timestamp("2026-10-22 15:00",tz=tz),"y":7676.75,"label":"THU: risk-off, box traverse → 7676.75","dy":-95,"dx":-70},
 {"t":pd.Timestamp("2026-10-23 10:25",tz=tz),"y":7648.5,"label":"FRI: 7644-49 held (7648.5), closed 7662.75 below the box","dy":-140,"dx":-110},
 {"t":pd.Timestamp("2026-10-26 11:00",tz=tz),"y":7739.5,"label":"MON: held 76-81 → 7739.5 (stalled at 33-35); 3-day balance","dy":60,"dx":-110},
 {"t":pd.Timestamp("2026-10-27 15:45",tz=tz),"y":7772.75,"label":"TUE: LBAF 03-04 ON, 12-17 held → book flipped → box break to 7772.75 (YTD VPOC)","dy":45,"dx":-150}]
charts.weekly("ES", es_lv, ES, s, e, "charts/2026-W44_ES_weekly.png",
              "ES weekly  ·  10/12 – Tue 10/27  ·  week of 10/25 plan", profile_ranges=[w3, w4], marks=es_marks, d5prof=ES5)

nq_lv = [
 {"p":[30520,30546],"label":"real clarity above","kind":"up","strong":True},
 {"p":[30344,30369],"label":"LAAF monitor","kind":"up","strong":True},
 {"p":[30210,30237],"label":"LAAF · min. reclaim","kind":"up","strong":True},
 {"p":[30113],"label":"wk high","kind":"ref"},
 {"p":[30069,30103],"label":"","kind":"up"},
 {"p":[29903,29932],"label":"supply 870-960","kind":"up","strong":True},
 {"p":[29754,29787],"label":"magnet","kind":"up"},
 {"p":[29623,29656],"label":"first real reclaim · LAAF","kind":"up","strong":True},
 {"p":[29569,29583],"label":"daily","kind":"ref"},
 {"p":[29380,29436],"label":"Thu singles · LAAF","kind":"pivot","strong":True},
 {"p":[29326],"label":"Fri high","kind":"ref"},
 {"p":[29269,29303],"label":"box bottom · fail/LAAF","kind":"pivot"},
 {"p":[29194,29220],"label":"daily · fail/LAAF B/B+","kind":"pivot"},
 {"p":[29089,29102],"label":"daily · hold/LBAF B/B+","kind":"ref"},
 {"p":[29038,29069],"label":"sellers stall below","kind":"pivot"},
 {"p":[28987],"label":"wk low","kind":"ref"},
 {"p":[28944,28969],"label":"wary of shorts","kind":"down"},
 {"p":[28878.75],"label":"Sept RTH low","kind":"ref"},
 {"p":[28847,28869],"label":"Sept ETH low 28816 · LBAF","kind":"down","strong":True},
 {"p":[28684,28722],"label":"quite strong · singles below","kind":"down","strong":True},
 {"p":[28500,28524],"label":"","kind":"down"},
 {"p":[28419],"label":"8/3 open","kind":"ref"},
 {"p":[28369,28394],"label":"","kind":"down"},
 {"p":[28313.25],"label":"8/3 low · full straddle","kind":"ref"},
 {"p":[28269,28299],"label":"","kind":"down","strong":True}]
nq_marks = [
 {"t":pd.Timestamp("2026-10-12 14:50",tz=tz),"y":30844.25,"label":"MON 10/12: LAAF of 125-145","dy":-60,"dx":10},
 {"t":pd.Timestamp("2026-10-14 15:05",tz=tz),"y":30078.0,"label":"WED: CPI → 30078, broke 216.5","dy":-120,"dx":-50},
 {"t":pd.Timestamp("2026-10-16 15:05",tz=tz),"y":29268.75,"label":"FRI 10/16: 29268.75 (YTD VPOC) = mother bar","dy":-150,"dx":-80},
 {"t":pd.Timestamp("2026-10-20 09:45",tz=tz),"y":29391.75,"label":"TUE: Fri VPOC held → +510","dy":-70,"dx":-30},
 {"t":pd.Timestamp("2026-10-21 13:20",tz=tz),"y":30113.0,"label":"WED: 30113 = wk high, never saw 210-237","dy":110,"dx":-90},
 {"t":pd.Timestamp("2026-10-22 15:45",tz=tz),"y":29033.0,"label":"THU: box BROKE → 29033, singles 380-436","dy":-200,"dx":-80},
 {"t":pd.Timestamp("2026-10-23 09:35",tz=tz),"y":28987.0,"label":"FRI: 28987 wk low → 29326 (just above 269-303), closed 29136","dy":-340,"dx":-120},
 {"t":pd.Timestamp("2026-10-26 11:00",tz=tz),"y":29572.0,"label":"MON: covered under 038-069 → reclaimed 380-436 → 29572","dy":300,"dx":-120},
 {"t":pd.Timestamp("2026-10-27 15:45",tz=tz),"y":29881.25,"label":"TUE: 269-303 held ON → 29881 spike into 903-932; 754-787 held all PM","dy":160,"dx":-130}]
charts.weekly("NQ", nq_lv, NQ, s, e, "charts/2026-W44_NQ_weekly.png",
              "NQ weekly  ·  10/12 – Tue 10/27  ·  week of 10/25 plan", profile_ranges=[w3, w4], marks=nq_marks, d5prof=NQ5)
print("ok")
