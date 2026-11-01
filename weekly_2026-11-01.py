"""Weekly chart spec for the week of 11/1 (letter dated 10/31). Run: python weekly_2026-11-01.py"""
import charts, pandas as pd
tz = "America/New_York"
ES, NQ = charts.load_1h("ES"), charts.load_1h("NQ")
ES5, NQ5 = charts.load("ES"), charts.load("NQ")
s = pd.Timestamp("2026-10-19 09:30", tz=tz); e = pd.Timestamp("2026-10-30 16:15", tz=tz)
w3 = ("wk 10/19", pd.Timestamp("2026-10-18 18:00", tz=tz), pd.Timestamp("2026-10-23 16:00", tz=tz))
w4 = ("wk 10/26", pd.Timestamp("2026-10-25 18:00", tz=tz), pd.Timestamp("2026-10-30 16:00", tz=tz))

es_lv = [
 {"p":[7838,7841],"label":"","kind":"up","strong":True},
 {"p":[7819.5],"label":"wk high · 15-20 rejection","kind":"ref"},
 {"p":[7815,7820],"label":"the level that trapped bulls","kind":"up","strong":True},
 {"p":[7784,7788],"label":"","kind":"up"},
 {"p":[7769,7772],"label":"reversion if no LAAF (at least 65)","kind":"up"},
 {"p":[7738,7741],"label":"daily","kind":"ref"},
 {"p":[7725,7730],"label":"acceptance above = sellers pressured","kind":"up","strong":True},
 {"p":[7703,7712],"label":"most of wk volume above","kind":"up","strong":True},
 {"p":[7670,7677],"label":"Fri high · LAAF monitor · back in Oct value","kind":"pivot","strong":True},
 {"p":[7644,7649],"label":"June high · first upside test","kind":"pivot","strong":True},
 {"p":[7628.25],"label":"Fri IB low","kind":"ref"},
 {"p":[7618,7623],"label":"Fri close","kind":"pivot"},
 {"p":[7600],"label":"honorable mention","kind":"ref"},
 {"p":[7591,7594],"label":"","kind":"pivot"},
 {"p":[7569,7575],"label":"Sept low · monthly OTFU ended","kind":"pivot","strong":True},
 {"p":[7558.25],"label":"Fri low · wk low · LBAF watch","kind":"ref"},
 {"p":[7555,7558],"label":"","kind":"down"},
 {"p":[7541,7543],"label":"MAJOR decision · LBAF monitor","kind":"down","strong":True},
 {"p":[7514,7517],"label":"","kind":"down"},
 {"p":[7497,7504],"label":"7480-7520 HTF decision","kind":"down","strong":True},
 {"p":[7483,7486],"label":"cautious shorts","kind":"down","strong":True},
 {"p":[7459,7462],"label":"cautious shorts","kind":"down","strong":True},
 {"p":[7446,7449],"label":"","kind":"down"},
 {"p":[7412,7417],"label":"cautious shorts","kind":"down","strong":True}]
es_marks = [
 {"t":pd.Timestamp("2026-10-20 10:30",tz=tz),"y":7791.5,"label":"TUE 10/20: bullish engulf","dy":-85,"dx":-25},
 {"t":pd.Timestamp("2026-10-21 14:15",tz=tz),"y":7812.25,"label":"WED: failed under 15-20","dy":22,"dx":-40},
 {"t":pd.Timestamp("2026-10-23 10:25",tz=tz),"y":7648.5,"label":"FRI 10/23: 7644-49 held → trap below the box","dy":-55,"dx":-70},
 {"t":pd.Timestamp("2026-10-27 15:45",tz=tz),"y":7772.75,"label":"TUE: book flip → 7772.75 (YTD VPOC)","dy":48,"dx":-110},
 {"t":pd.Timestamp("2026-10-28 16:00",tz=tz),"y":7819.5,"label":"WED FOMC: AH 7819.5 — 15-20 REJECTED, 'enormous trap'","dy":12,"dx":-95},
 {"t":pd.Timestamp("2026-10-29 18:45",tz=tz),"y":7693.75,"label":"THU: LAAF IB high → 7725; AH liquidation","dy":-60,"dx":-90},
 {"t":pd.Timestamp("2026-10-30 14:50",tz=tz),"y":7558.25,"label":"FRI: thru 7569-75 (Sept low) → 7558.25; monthly OTFU ENDED; closed 7615.75","dy":-60,"dx":-170}]
charts.weekly("ES", es_lv, ES, s, e, "charts/2026-W45_ES_weekly.png",
              "ES weekly  ·  10/19 – Fri 10/30  ·  week of 11/1 plan", profile_ranges=[w3, w4], marks=es_marks, d5prof=ES5)

nq_lv = [
 {"p":[30210,30237],"label":"major test above · LAAF","kind":"up","strong":True},
 {"p":[30178],"label":"wk high (AH)","kind":"ref"},
 {"p":[30069,30103],"label":"","kind":"up"},
 {"p":[30009],"label":"wk RTH high","kind":"ref"},
 {"p":[29903,29932],"label":"","kind":"up","strong":True},
 {"p":[29754,29787],"label":"bear gap 29677-29767 · last line","kind":"up"},
 {"p":[29623,29656],"label":"LAAF monitor · Thu high 29677","kind":"up","strong":True},
 {"p":[29380,29436],"label":"gap-fill reversal · firm above = shift","kind":"up","strong":True},
 {"p":[29269,29303],"label":"","kind":"up"},
 {"p":[29194,29220],"label":"daily","kind":"ref"},
 {"p":[29038,29069],"label":"29k reclaim · min. requirement","kind":"pivot","strong":True},
 {"p":[28944,28969],"label":"29k reclaim","kind":"pivot"},
 {"p":[28878.75],"label":"Sept RTH low · first order of business","kind":"ref"},
 {"p":[28860.5],"label":"Fri IB high · bear gap to 29405","kind":"ref"},
 {"p":[28847,28869],"label":"Fri high · LAAF monitor","kind":"pivot","strong":True},
 {"p":[28684,28722],"label":"trapped IB buying","kind":"pivot"},
 {"p":[28614.75],"label":"Fri IB low","kind":"ref"},
 {"p":[28569,28583],"label":"Fri close · first order of business","kind":"pivot"},
 {"p":[28446],"label":"Fri VAL","kind":"ref"},
 {"p":[28369,28394],"label":"","kind":"down"},
 {"p":[28336,28346],"label":"honorable mention","kind":"ref"},
 {"p":[28232.75],"label":"Fri low · wk low · June low · LBAF watch","kind":"ref"},
 {"p":[28200,28233],"label":"LBAF · 28228-28408 critical","kind":"down","strong":True},
 {"p":[28080,28100],"label":"","kind":"down"},
 {"p":[27969,27996],"label":"LBAF · 200d / VWAP cluster","kind":"down","strong":True},
 {"p":[27877,27900],"label":"","kind":"down"},
 {"p":[27592,27622],"label":"","kind":"down"},
 {"p":[27409,27440],"label":"","kind":"down"},
 {"p":[27313,27339],"label":"","kind":"down"},
 {"p":[27201.5],"label":"July low · 0.5 fib","kind":"ref"}]
nq_marks = [
 {"t":pd.Timestamp("2026-10-21 13:20",tz=tz),"y":30113.0,"label":"WED 10/21: 30113, never saw 210-237","dy":90,"dx":-20},
 {"t":pd.Timestamp("2026-10-23 09:35",tz=tz),"y":28987.0,"label":"FRI 10/23: 28987 → buyers again","dy":-180,"dx":-90},
 {"t":pd.Timestamp("2026-10-27 15:45",tz=tz),"y":29881.25,"label":"TUE: spike into 903-932","dy":120,"dx":-60},
 {"t":pd.Timestamp("2026-10-28 16:00",tz=tz),"y":30178.0,"label":"WED FOMC: AH 30178, failed under 210-237","dy":90,"dx":-120},
 {"t":pd.Timestamp("2026-10-29 18:45",tz=tz),"y":29043.25,"label":"THU: 623-656 gave way → 380-436 → AH 29043","dy":-250,"dx":-120},
 {"t":pd.Timestamp("2026-10-30 14:50",tz=tz),"y":28232.75,"label":"FRI: dip buyers let go → thru 684-722 → 28232.75 (June low, 0.382); closed 28542","dy":-220,"dx":-190}]
charts.weekly("NQ", nq_lv, NQ, s, e, "charts/2026-W45_NQ_weekly.png",
              "NQ weekly  ·  10/19 – Fri 10/30  ·  week of 11/1 plan", profile_ranges=[w3, w4], marks=nq_marks, d5prof=NQ5)
print("ok")
