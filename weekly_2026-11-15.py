"""Weekly chart spec for the week of 11/15 (letter dated 11/14). Run: python weekly_2026-11-15.py"""
import charts, pandas as pd
tz = "America/New_York"
ES, NQ = charts.load_1h("ES"), charts.load_1h("NQ")
ES5, NQ5 = charts.load("ES"), charts.load("NQ")
s = pd.Timestamp("2026-11-02 09:30", tz=tz); e = pd.Timestamp("2026-11-16 16:15", tz=tz)
w5 = ("wk 11/2", pd.Timestamp("2026-11-01 18:00", tz=tz), pd.Timestamp("2026-11-06 16:00", tz=tz))
w6 = ("wk 11/9", pd.Timestamp("2026-11-08 18:00", tz=tz), pd.Timestamp("2026-11-13 16:00", tz=tz))
w7 = ("Mon", pd.Timestamp("2026-11-15 18:00", tz=tz), e)

es_lv = [
 {"p":[7815,7820],"label":"","kind":"up","strong":True},
 {"p":[7784,7788],"label":"","kind":"up"},
 {"p":[7769,7772],"label":"","kind":"up"},
 {"p":[7746.25],"label":"Nov 1 wk high","kind":"ref"},
 {"p":[7738,7741],"label":"","kind":"up"},
 {"p":[7725,7730],"label":"","kind":"up"},
 {"p":[7708,7713],"label":"Thu 11/5 open/high · mother-bar high","kind":"up","strong":True},
 {"p":[7670,7680],"label":"balance top · LAAF monitor","kind":"up","strong":True},
 {"p":[7649],"label":"June ATH · HVN","kind":"ref"},
 {"p":[7628,7636],"label":"","kind":"up"},
 {"p":[7593,7600],"label":"buyers' edge above · Fri ARH 7590","kind":"pivot","strong":True},
 {"p":[7575],"label":"Sept low · wk VPOC area","kind":"ref"},
 {"p":[7558,7563],"label":"Oct low · sellers' edge below","kind":"pivot","strong":True},
 {"p":[7519.25],"label":"Fri low · LBAF watch","kind":"ref"},
 {"p":[7490,7504],"label":"balance bottom · Tue excess low 7493","kind":"pivot","strong":True},
 {"p":[7469,7473],"label":"Nov 6 high · trap below balance","kind":"pivot","strong":True},
 {"p":[7455.75],"label":"Mon RTH low","kind":"ref"},
 {"p":[7388,7396],"label":"","kind":"down","strong":True},
 {"p":[7377.25],"label":"Nov 1 wk RTH low","kind":"ref"},
 {"p":[7369,7372],"label":"intervening","kind":"down"},
 {"p":[7322.25],"label":"Nov 1 wk ETH low","kind":"ref"},
 {"p":[7313,7317],"label":"","kind":"down"},
 {"p":[7292,7296],"label":"LBAF monitor","kind":"down"}]
es_marks = [
 {"t":pd.Timestamp("2026-11-03 22:05",tz=tz),"y":7490.0,"label":"ELECTION: 7490 → gap-up reversal to 7746.25","dy":-110,"dx":-40},
 {"t":pd.Timestamp("2026-11-04 13:05",tz=tz),"y":7746.25,"label":"WED 11/4: 7746.25 at 38-41 / ATH VWAP","dy":28,"dx":-40},
 {"t":pd.Timestamp("2026-11-05 15:55",tz=tz),"y":7377.25,"label":"THU 11/5 mother bar: 7708-7713 open/high → 7377.25; July RTH low 7346 AH","dy":-45,"dx":15},
 {"t":pd.Timestamp("2026-11-06 09:50",tz=tz),"y":7469.0,"label":"FRI 11/6: 7392-7469 range","dy":-95,"dx":30},
 {"t":pd.Timestamp("2026-11-09 15:15",tz=tz),"y":7600.5,"label":"MON: 7455.75 defended → 7600.5","dy":75,"dx":-30},
 {"t":pd.Timestamp("2026-11-10 12:40",tz=tz),"y":7493.0,"label":"TUE CPI: excess low 7493","dy":-70,"dx":-10},
 {"t":pd.Timestamp("2026-11-11 13:45",tz=tz),"y":7671.5,"label":"WED: gap, 7593.25 held → 7671.5","dy":60,"dx":-90},
 {"t":pd.Timestamp("2026-11-12 11:20",tz=tz),"y":7674.75,"label":"THU: gap-down LBAF → 7674.75, 2nd fail in 70-80; big buyer exits","dy":100,"dx":-40},
 {"t":pd.Timestamp("2026-11-13 10:20",tz=tz),"y":7519.25,"label":"FRI: liquidation 7643 → 7519.25, then buy program to 7590 ARH; 5 PM 7561","dy":-120,"dx":-110},
 {"t":pd.Timestamp("2026-11-16 14:45",tz=tz),"y":7420.25,"label":"MON: Sun gap-up to 7614 failed → failed reclaim of 7490-7504 → 7420.25","dy":-45,"dx":-150}]
charts.weekly("ES", es_lv, ES, s, e, "charts/2026-W47_ES_weekly.png",
              "ES weekly  ·  11/2 – Mon 11/16  ·  week of 11/15 plan", profile_ranges=[w6, w7], marks=es_marks, d5prof=ES5)

nq_lv = [
 {"p":[29038,29069],"label":"major accomplishment if reclaimed","kind":"up","strong":True},
 {"p":[28944,28969],"label":"Nov 1 wk high · bear gap to 29405","kind":"up"},
 {"p":[28847,28869],"label":"LAAF monitor","kind":"up","strong":True},
 {"p":[28684,28722],"label":"wk high 28697","kind":"up"},
 {"p":[28583,28608],"label":"","kind":"up"},
 {"p":[28400,28443],"label":"Fri open/high · LAAF monitor","kind":"up","strong":True},
 {"p":[28200,28233],"label":"upper dist above · failed-reclaim monitor","kind":"pivot","strong":True},
 {"p":[28096,28129],"label":"lower dist below · LAAF monitor · ARH 28111.75","kind":"pivot","strong":True},
 {"p":[27953,27969],"label":"daily · Fri value cap","kind":"ref"},
 {"p":[27695.25],"label":"Fri low · LBAF watch","kind":"ref"},
 {"p":[27588,27622],"label":"LBAF monitor · Tue low 27516 below","kind":"pivot","strong":True},
 {"p":[27425,27458],"label":"Nov 6 high","kind":"down"},
 {"p":[27313,27339],"label":"Mon open/low · wk RTH low 27316","kind":"down","strong":True},
 {"p":[27201.5],"label":"July low · responsive bid watch","kind":"ref"},
 {"p":[26969,26987],"label":"","kind":"down","strong":True},
 {"p":[26805,26840],"label":"held Sunday night","kind":"down","strong":True},
 {"p":[26500,26523],"label":"","kind":"down"},
 {"p":[26369,26408],"label":"LBAF monitor","kind":"down","strong":True},
 {"p":[26366.5],"label":"Nov 1 wk ETH low · prior-ATH backtest","kind":"ref"},
 {"p":[26258,26291],"label":"LBAF monitor","kind":"down","strong":True},
 {"p":[26072,26102],"label":"","kind":"down","strong":True},
 {"p":[25990,26016],"label":"","kind":"down","strong":True}]
nq_marks = [
 {"t":pd.Timestamp("2026-11-03 22:05",tz=tz),"y":27615.75,"label":"ELECTION: 27615.75 → 28969","dy":-200,"dx":-50},
 {"t":pd.Timestamp("2026-11-04 10:15",tz=tz),"y":28969.0,"label":"WED 11/4: 28969, rejected at the Sept low","dy":90,"dx":-40},
 {"t":pd.Timestamp("2026-11-05 15:55",tz=tz),"y":26718.0,"label":"THU 11/5 mother bar → 26718; Globex 26366.5 = prior-ATH backtest","dy":-180,"dx":15},
 {"t":pd.Timestamp("2026-11-06 09:50",tz=tz),"y":27425.0,"label":"FRI 11/6: relief to 27425","dy":120,"dx":-50},
 {"t":pd.Timestamp("2026-11-09 15:25",tz=tz),"y":28129.25,"label":"MON: 26805-840 held Sun night → squeeze to 28129","dy":-480,"dx":-20},
 {"t":pd.Timestamp("2026-11-10 12:40",tz=tz),"y":27516.0,"label":"TUE CPI: excess low 27516","dy":-280,"dx":-10},
 {"t":pd.Timestamp("2026-11-11 13:45",tz=tz),"y":28697.0,"label":"WED: gap open → 28697, upper distribution","dy":260,"dx":-90},
 {"t":pd.Timestamp("2026-11-12 11:20",tz=tz),"y":28652.25,"label":"THU: 28652, lost 443-485; big buyer exits","dy":520,"dx":-20},
 {"t":pd.Timestamp("2026-11-13 11:20",tz=tz),"y":27695.25,"label":"FRI: liquidation → 27695 (LBAF of IB low), buy program to 28111.75 ARH; failed distribution","dy":-560,"dx":-150},
 {"t":pd.Timestamp("2026-11-16 15:35",tz=tz),"y":27234.75,"label":"MON: gap-up to 28279 rejected from the upper dist → 27588-622 rejected from below → poor low 27234.75","dy":-330,"dx":-200}]
charts.weekly("NQ", nq_lv, NQ, s, e, "charts/2026-W47_NQ_weekly.png",
              "NQ weekly  ·  11/2 – Mon 11/16  ·  week of 11/15 plan", profile_ranges=[w6, w7], marks=nq_marks, d5prof=NQ5)
print("ok")
