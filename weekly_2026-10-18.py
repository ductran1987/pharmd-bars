"""Weekly chart spec for the week of 10/18 (letter dated 10/17). Run: python weekly_2026-10-18.py"""
import charts, pandas as pd
tz = "America/New_York"
ES, NQ = charts.load_1h("ES"), charts.load_1h("NQ")
ES5, NQ5 = charts.load("ES"), charts.load("NQ")
s = pd.Timestamp("2026-10-05 09:30", tz=tz); e = pd.Timestamp("2026-10-20 16:15", tz=tz)
w1 = ("wk 10/5", pd.Timestamp("2026-10-04 18:00", tz=tz), pd.Timestamp("2026-10-09 16:00", tz=tz))
w2 = ("wk 10/12", pd.Timestamp("2026-10-11 18:00", tz=tz), pd.Timestamp("2026-10-16 16:00", tz=tz))
w3 = ("Mon-Tue", pd.Timestamp("2026-10-18 18:00", tz=tz), e)

es_lv = [
 {"p":[7869,7872],"label":"never traded above all week","kind":"up","strong":True},
 {"p":[7838,7841],"label":"certainty for bulls above","kind":"up","strong":True},
 {"p":[7815,7820],"label":"sellers probably dead above","kind":"up","strong":True},
 {"p":[7803.25],"label":"Fri RTH high · lower high","kind":"ref"},
 {"p":[7797,7803],"label":"","kind":"up"},
 {"p":[7780,7784],"label":"VERY much a short · A+++","kind":"pivot","strong":True},
 {"p":[7760,7765],"label":"short · LAAF watch","kind":"pivot"},
 {"p":[7739,7743],"label":"first key reclaim","kind":"pivot"},
 {"p":[7723,7726],"label":"","kind":"pivot"},
 {"p":[7706,7712],"label":"closed just below","kind":"pivot"},
 {"p":[7676],"label":"Fri low · 9/28 low 7672.75","kind":"ref"},
 {"p":[7669,7673],"label":"prospective range low · LBAF","kind":"down","strong":True},
 {"p":[7644,7649],"label":"white box top","kind":"down","strong":True},
 {"p":[7631,7634],"label":"traded thru, never flipped","kind":"down","strong":True},
 {"p":[7618,7622],"label":"","kind":"down"},
 {"p":[7591,7594],"label":"","kind":"down"},
 {"p":[7569,7575],"label":"Sept low · LBAF","kind":"down","strong":True},
 {"p":[7541,7543],"label":"major decision point","kind":"down","strong":True}]
es_marks = [
 {"t":pd.Timestamp("2026-10-06 10:30",tz=tz),"y":7897.5,"label":"10/6 ATH 7897.5 → LAAF week","dy":-16,"dx":10},
 {"t":pd.Timestamp("2026-10-12 14:50",tz=tz),"y":7846.25,"label":"MON: box 46-70","dy":-60,"dx":-60},
 {"t":pd.Timestamp("2026-10-14 14:00",tz=tz),"y":7741.0,"label":"WED: CPI → true gap down, box broke, 7741","dy":-30,"dx":-150},
 {"t":pd.Timestamp("2026-10-15 15:20",tz=tz),"y":7801.75,"label":"THU: relief to 7801.75 = back inside; closed above 80-84","dy":-60,"dx":-170},
 {"t":pd.Timestamp("2026-10-16 15:05",tz=tz),"y":7676.0,"label":"FRI: failed reclaim → 7676 (2x weekly straddle); glimpse of capitulation","dy":-70,"dx":-150},
 {"t":pd.Timestamp("2026-10-19 11:35",tz=tz),"y":7773.25,"label":"MON: VIX crush rally → 7773 LAAF of ON/IB high; inside day, weak close 7734.75","dy":40,"dx":-120},
 {"t":pd.Timestamp("2026-10-20 10:30",tz=tz),"y":7791.5,"label":"TUE: 7706-12 held → rip to 7791.5 (supply above 80-84); bullish engulfing; AH ripping","dy":60,"dx":-200}]
charts.weekly("ES", es_lv, ES, s, e, "charts/2026-W43_ES_weekly.png",
              "ES weekly  ·  10/5 – Tue 10/20  ·  week of 10/18 plan", profile_ranges=[w2, w3], marks=es_marks, d5prof=ES5)

nq_lv = [
 {"p":[30520,30546],"label":"sellers sweat above","kind":"up","strong":True},
 {"p":[30344,30369],"label":"LAAF watch","kind":"up","strong":True},
 {"p":[30210,30237],"label":"structural lower high","kind":"up","strong":True},
 {"p":[30069,30103],"label":"","kind":"up"},
 {"p":[30045.75],"label":"Fri RTH high","kind":"ref"},
 {"p":[29932,29969],"label":"","kind":"up","strong":True},
 {"p":[29754,29787],"label":"A+++ swing short","kind":"pivot","strong":True},
 {"p":[29615,29645],"label":"first reclaim · LAAF watch","kind":"pivot","strong":True},
 {"p":[29469,29483],"label":"","kind":"pivot"},
 {"p":[29268.75],"label":"Fri low · wk low","kind":"ref"},
 {"p":[29269,29303],"label":"'Cerberus' · LBAF","kind":"down","strong":True},
 {"p":[29038,29069],"label":"reactive · key reclaim","kind":"down"},
 {"p":[28944,28969],"label":"reactive","kind":"down"},
 {"p":[28878.75],"label":"Sept RTH low","kind":"ref"},
 {"p":[28847,28869],"label":"Sept ETH low 28816 · LBAF","kind":"down","strong":True},
 {"p":[28684,28722],"label":"quite strong · singles below","kind":"down","strong":True},
 {"p":[28500,28524],"label":"demand","kind":"down"}]
nq_marks = [
 {"t":pd.Timestamp("2026-10-06 10:30",tz=tz),"y":31616.5,"label":"10/6 ATH 31616.5","dy":-40,"dx":10},
 {"t":pd.Timestamp("2026-10-12 14:50",tz=tz),"y":30844.25,"label":"MON: ON failed 269-288 → LAAF of 125-145","dy":-150,"dx":-100},
 {"t":pd.Timestamp("2026-10-14 15:05",tz=tz),"y":30078.0,"label":"WED: LAAF 815-845 on CPI → 30078 (216.5)","dy":-90,"dx":-170},
 {"t":pd.Timestamp("2026-10-15 15:45",tz=tz),"y":30196.75,"label":"THU: 615-645 held → closed in a back-test of 216.5 from below","dy":80,"dx":-150},
 {"t":pd.Timestamp("2026-10-16 15:05",tz=tz),"y":29268.75,"label":"FRI: back-test → another leg to 29268.75 (YTD VPOC); breakout FAILED","dy":-200,"dx":-200},
 {"t":pd.Timestamp("2026-10-19 11:35",tz=tz),"y":29983.5,"label":"MON: LBAF of Fri low at the open → +760 to 29983.5; inside day, closed 29722 under 754-787","dy":150,"dx":-150},
 {"t":pd.Timestamp("2026-10-20 09:45",tz=tz),"y":29391.75,"label":"TUE: nuked thru ON low to 29392 (Fri VPOC) → LBAF rip to 29903.5 under 910","dy":-170,"dx":-150}]
charts.weekly("NQ", nq_lv, NQ, s, e, "charts/2026-W43_NQ_weekly.png",
              "NQ weekly  ·  10/5 – Tue 10/20  ·  week of 10/18 plan", profile_ranges=[w2, w3], marks=nq_marks, d5prof=NQ5)
print("ok")
