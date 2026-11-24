"""Weekly chart spec for the week of 11/22 (letter dated 11/21). Run: python weekly_2026-11-22.py"""
import charts, pandas as pd
tz = "America/New_York"
ES, NQ = charts.load_1h("ES"), charts.load_1h("NQ")
ES5, NQ5 = charts.load("ES"), charts.load("NQ")
s = pd.Timestamp("2026-11-09 09:30", tz=tz); e = pd.Timestamp("2026-11-24 16:15", tz=tz)
w6 = ("wk 11/9", pd.Timestamp("2026-11-08 18:00", tz=tz), pd.Timestamp("2026-11-13 16:00", tz=tz))
w7 = ("wk 11/16", pd.Timestamp("2026-11-15 18:00", tz=tz), pd.Timestamp("2026-11-20 16:00", tz=tz))
w8 = ("Mon-Tue", pd.Timestamp("2026-11-22 18:00", tz=tz), e)

es_lv = [
 {"p":[7670,7680],"label":"last wk: balance top","kind":"ref"},
 {"p":[7593,7600],"label":"","kind":"ref"},
 {"p":[7558,7563],"label":"","kind":"ref"},
 {"p":[7490,7504],"label":"","kind":"up","strong":True},
 {"p":[7461,7469],"label":"LAAF monitor","kind":"up","strong":True},
 {"p":[7412,7420],"label":"","kind":"up"},
 {"p":[7388,7396],"label":"","kind":"up","strong":True},
 {"p":[7372,7377],"label":"LAAF monitor · Thu B-singles 7354-7390","kind":"up"},
 {"p":[7346],"label":"","kind":"ref"},
 {"p":[7305,7317],"label":"minimum meaningful structural reclaim","kind":"up","strong":True},
 {"p":[7269,7275],"label":"","kind":"up"},
 {"p":[7247],"label":"June RTH low · first technical reclaim","kind":"ref"},
 {"p":[7211,7217],"label":"Fri high 7216.75 · balance top","kind":"pivot","strong":True},
 {"p":[7177,7186],"label":"","kind":"up"},
 {"p":[7138,7149],"label":"","kind":"up"},
 {"p":[7115,7121],"label":"Fri IB low","kind":"up"},
 {"p":[7072,7078],"label":"Fri ARH 7071.75","kind":"up"},
 {"p":[7043],"label":"prior ATH (Jan)","kind":"ref"},
 {"p":[7017,7024],"label":"","kind":"pivot","strong":True},
 {"p":[6999,7003],"label":"LAAF monitor · singles 7001-7021","kind":"pivot"},
 {"p":[6947,6955],"label":"Fri spike base","kind":"pivot"},
 {"p":[6925,6928],"label":"2026 RTH open","kind":"pivot","strong":True},
 {"p":[6898,6902],"label":"2026 ETH open · Fri low 6898","kind":"pivot","strong":True},
 {"p":[6878,6883],"label":"LBAF monitor · demand 6835-6875","kind":"down","strong":True},
 {"p":[6864,6869],"label":"","kind":"down","strong":True},
 {"p":[6837,6847],"label":"","kind":"down","strong":True},
 {"p":[6817,6822],"label":"deepest trappy back-test of 7043","kind":"down","strong":True},
 {"p":[6790,6793],"label":"","kind":"down"},
 {"p":[6780],"label":"LBAF monitor · bull gap 6780 → 6659.5","kind":"ref"},
 {"p":[6760,6764],"label":"","kind":"down"},
 {"p":[6734,6740],"label":"","kind":"down"}]
es_marks = [
 {"t":pd.Timestamp("2026-11-12 11:20",tz=tz),"y":7674.75,"label":"THU 11/12: 2nd fail in 7670-80; big buyer exits","dy":45,"dx":-40},
 {"t":pd.Timestamp("2026-11-13 10:20",tz=tz),"y":7519.25,"label":"FRI 11/13: liquidation → 7519.25","dy":-95,"dx":-70},
 {"t":pd.Timestamp("2026-11-16 14:45",tz=tz),"y":7420.25,"label":"MON: failed gap-up, lost 7490-7504 → 7420.25","dy":-150,"dx":-95},
 {"t":pd.Timestamp("2026-11-17 10:50",tz=tz),"y":7308.0,"label":"TUE: 7308; value shifts down","dy":-120,"dx":-75},
 {"t":pd.Timestamp("2026-11-18 11:20",tz=tz),"y":7305.25,"label":"WED: NVDA gap sold; box 7305-7389","dy":-190,"dx":-70},
 {"t":pd.Timestamp("2026-11-19 15:15",tz=tz),"y":7192.0,"label":"THU: 7388-96 failed → box broke → trapdoor: 7192","dy":-170,"dx":-90},
 {"t":pd.Timestamp("2026-11-20 15:55",tz=tz),"y":6898.0,"label":"FRI: open bought to 7216.75, trend day down, spike 6954 → 6898 (2026 ETH open)","dy":-70,"dx":-95},
 {"t":pd.Timestamp("2026-11-23 10:30",tz=tz),"y":7313.25,"label":"MON: cover rally, news candle 7084 → 7313.25; failure to balance","dy":230,"dx":-75},
 {"t":pd.Timestamp("2026-11-24 11:00",tz=tz),"y":7154.25,"label":"TUE: box 7152-7241, value gapped lower; bearish build","dy":-405,"dx":-60}]
charts.weekly("ES", es_lv, ES, s, e, "charts/2026-W48_ES_weekly.png",
              "ES weekly  ·  11/9 – Tue 11/24  ·  week of 11/22 plan", profile_ranges=[w7, w8], marks=es_marks, d5prof=ES5)

nq_lv = [
 {"p":[28684,28722],"label":"last wk high area","kind":"ref"},
 {"p":[28200,28233],"label":"failed upper distribution","kind":"ref"},
 {"p":[27838],"label":"Thu 11/19 high","kind":"ref"},
 {"p":[27588,27622],"label":"LAAF monitor","kind":"up","strong":True},
 {"p":[27425,27458],"label":"","kind":"up","strong":True},
 {"p":[27313,27339],"label":"","kind":"up","strong":True},
 {"p":[27201.5],"label":"","kind":"ref"},
 {"p":[27069,27109],"label":"","kind":"up"},
 {"p":[26805,26840],"label":"firm reclaim → 27425-27458","kind":"up","strong":True},
 {"p":[26669,26732],"label":"bare-minimum structural reclaim","kind":"up","strong":True},
 {"p":[26504,26569],"label":"LAAF · bear gap · Fri high 26504","kind":"pivot","strong":True},
 {"p":[26369,26408],"label":"former ATH","kind":"pivot","strong":True},
 {"p":[26069,26117],"label":"Fri A-period low","kind":"pivot","strong":True},
 {"p":[25990,26016],"label":"trappy back-test · Fri premkt low","kind":"pivot","strong":True},
 {"p":[25730,25769],"label":"LAAF monitor · Fri ARH 25762.5","kind":"pivot"},
 {"p":[25687],"label":"2026 RTH open","kind":"ref"},
 {"p":[25438,25493],"label":"LAAF monitor · J singles","kind":"pivot","strong":True},
 {"p":[25245,25275],"label":"deepest trappy back-test","kind":"pivot","strong":True},
 {"p":[25199],"label":"Fri spike base","kind":"ref"},
 {"p":[25135,25160],"label":"","kind":"down"},
 {"p":[24969,24984],"label":"Fri low 24976.5","kind":"down","strong":True},
 {"p":[24926],"label":"LBAF monitor · April gap top 24926.5","kind":"ref"},
 {"p":[24769,24796],"label":"inside the gap","kind":"down"},
 {"p":[24691,24709],"label":"","kind":"down"},
 {"p":[24537,24569],"label":"","kind":"down"},
 {"p":[24452,24469],"label":"","kind":"down","strong":True},
 {"p":[24369,24381],"label":"April gap bottom 24381","kind":"down","strong":True},
 {"p":[24300,24326],"label":"","kind":"down","strong":True},
 {"p":[24243,24269],"label":"","kind":"down"},
 {"p":[24134,24149],"label":"","kind":"down"},
 {"p":[24030,24069],"label":"LBAF · major decision","kind":"down","strong":True}]
nq_marks = [
 {"t":pd.Timestamp("2026-11-11 13:45",tz=tz),"y":28697.0,"label":"WED 11/11: 28697, upper distribution","dy":200,"dx":-40},
 {"t":pd.Timestamp("2026-11-13 11:20",tz=tz),"y":27695.25,"label":"FRI 11/13: failed distribution → 27695","dy":-420,"dx":-80},
 {"t":pd.Timestamp("2026-11-16 15:35",tz=tz),"y":27234.75,"label":"MON: gap-up to 28279 rejected → 27234.75","dy":-700,"dx":-95},
 {"t":pd.Timestamp("2026-11-17 10:50",tz=tz),"y":26658.5,"label":"TUE: 26658.5, responsive buying","dy":-420,"dx":-80},
 {"t":pd.Timestamp("2026-11-19 09:50",tz=tz),"y":27838.0,"label":"THU: gap to 27838 sold, 27588-622 failed → 26559","dy":330,"dx":-70},
 {"t":pd.Timestamp("2026-11-20 15:55",tz=tz),"y":24976.5,"label":"FRI: failed opening drive 26504, trend day down, spike 25199 → 24976.5 (above the April gap)","dy":-330,"dx":-105},
 {"t":pd.Timestamp("2026-11-23 09:30",tz=tz),"y":27137.0,"label":"MON: limit-up on news, 25863 → 27137 (just under the July low)","dy":1420,"dx":-45},
 {"t":pd.Timestamp("2026-11-24 11:10",tz=tz),"y":25998.0,"label":"TUE: box 25998-26510, below the prior ATH; bearish build","dy":-1500,"dx":-60}]
charts.weekly("NQ", nq_lv, NQ, s, e, "charts/2026-W48_NQ_weekly.png",
              "NQ weekly  ·  11/9 – Tue 11/24  ·  week of 11/22 plan", profile_ranges=[w7, w8], marks=nq_marks, d5prof=NQ5)
print("ok")
