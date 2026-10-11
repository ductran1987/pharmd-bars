# What makes a look-below-and-fail work — and do the stops fit?

405 fail-and-reclaim events (5m close past the far edge, then 5m close back through the near edge) on 144 days, graded + ungraded, with 1m order-flow data. Base: T1-before-new-low 55%, market-fill avg -0.04R, idealized edge fill +0.14R. H1 n=275, H2 n=130.

## Each measurement split into thirds (low / mid / high) — win% = T1 before a new low; R = market fill

A feature is only useful if the same third wins in BOTH halves. ✓ = the best third beats the worst by ≥ 10 pts of win% and ≥ 0.15R in both H1 and H2.

| feature | cut points | low third win% / R | mid | high | H1 low→high R | H2 low→high R | stable |
|---|---|---|---|---|---|---|---|
| depth_atr5 | 0.90 / 2.16 | 39% / -0.07 | 56% / +0.01 | 70% / -0.06 | -0.02 → +0.03 → +0.03 | -0.19 → -0.04 → -0.24 |  |
| mins_flush | 18.00 / 105.00 | 52% / +0.01 | 52% / -0.02 | 60% / -0.12 | +0.09 → -0.05 → -0.02 | -0.17 → +0.01 → -0.35 |  |
| mins_reclaim | 13.00 / 44.33 | 46% / +0.09 | 57% / -0.13 | 61% / -0.10 | +0.11 → -0.04 → -0.05 | +0.05 → -0.33 → -0.20 |  |
| mins_below | 15.00 / 70.00 | 46% / -0.01 | 58% / -0.03 | 61% / -0.10 | +0.06 → +0.02 → -0.06 | -0.16 → -0.12 → -0.18 |  |
| flush_delta | -0.07 / -0.03 | 50% / +0.09 | 56% / -0.11 | 57% / -0.10 | +0.14 → -0.13 → +0.02 | -0.05 → -0.07 → -0.29 |  |
| reclaim_delta | 0.03 / 0.08 | 63% / -0.06 | 52% / -0.12 | 49% / +0.06 | +0.07 → -0.11 → +0.07 | -0.31 → -0.16 → +0.03 |  |
| delta_swing | 0.07 / 0.13 | 61% / -0.10 | 56% / -0.09 | 46% / +0.06 | +0.02 → -0.06 → +0.07 | -0.28 → -0.17 → +0.03 |  |
| cvd_div | 0.00 / 0.00 | 53% / -0.00 | 57% / +0.01 | 55% / -0.13 | +0.03 → +0.10 → -0.08 | -0.08 → -0.20 → -0.22 |  |
| low_vol_share | 0.03 / 0.10 | 61% / -0.10 | 53% / -0.09 | 49% / +0.06 | -0.04 → -0.05 → +0.12 | -0.22 → -0.20 → -0.05 |  |
| rel_vol | 1.26 / 2.42 | 47% / -0.20 | 53% / -0.06 | 64% / +0.13 | -0.20 → -0.13 → +0.29 | -0.21 → +0.09 → -0.45 |  |
| rbar_delta | 0.04 / 0.11 | 50% / -0.18 | 61% / +0.06 | 52% / -0.01 | -0.12 → +0.14 → +0.01 | -0.30 → -0.09 → -0.07 |  |
| rbar_pos | 0.79 / 0.92 | 59% / +0.00 | 54% / -0.01 | 51% / -0.12 | +0.06 → +0.00 → -0.04 | -0.14 → -0.05 → -0.28 |  |
| chase_atr5 | 0.15 / 0.45 | 49% / -0.01 | 50% / -0.08 | 65% / -0.04 | +0.01 → +0.01 → +0.02 | -0.05 → -0.24 → -0.17 |  |
| width_atr5 | 0.00 / 0.55 | 49% / -0.01 | 59% / +0.05 | 56% / -0.15 | +0.10 → +0.06 → -0.13 | -0.21 → +0.01 → -0.20 |  |
| room_R | 1.15 / 1.87 | 70% / -0.02 | 50% / -0.02 | 43% / -0.09 | -0.01 → +0.00 → +0.03 | -0.05 → -0.06 → -0.35 |  |
| hour | 9.42 / 14.78 | 54% / -0.04 | 60% / -0.11 | 50% / +0.02 | -0.01 → -0.04 → +0.09 | -0.11 → -0.27 → -0.10 |  |

**By grade:** A: n 45, win 53%, -0.08R (H1 -0.04 / H2 -0.16) · B: n 115, win 50%, -0.03R (H1 +0.05 / H2 -0.12) · C: n 18, win 61%, +0.01R (H1 +0.26 / H2 -0.32) · U: n 227, win 56%, -0.05R (H1 -0.01 / H2 -0.16)

**By instrument:** ES: n 231, win 50%, -0.12R (H1 -0.06 / H2 -0.21) · NQ: n 174, win 60%, +0.06R (H1 +0.09 / H2 -0.05)

**By RTH (1) vs overnight (0):** 0: n 260, win 52%, -0.01R (H1 +0.04 / H2 -0.10) · 1: n 145, win 59%, -0.11R (H1 -0.05 / H2 -0.27)

## Combined score (logistic regression on all measurements, fit on H1 only, judged on H2)

Weights (standardized; + = more likely to win): rel_vol +0.57, room_R -0.56, flush_delta -0.19, reclaim_delta -0.18, depth_atr5 +0.18, rbar_pos -0.16, rth +0.12, hour -0.10

| H2 events ranked by the H1 score | n | win% | avg R (market) | avg R (edge fill) |
|---|---|---|---|---|
| bottom third | 44 | 36% | -0.31 | -0.14 |
| middle third | 43 | 63% | +0.05 | +0.27 |
| top third | 43 | 58% | -0.20 | -0.12 |
| all H2 | 130 | 52% | -0.15 | +0.00 |

## Do the stops fit the overshoot?

### Reclaim entry: after buying the reclaim, how far did eventual WINNERS (reached T1) come back down first?

| | n | median | 75th pct | 90th pct |
|---|---|---|---|---|
| ES: pullback from entry, ATR5 | 164 | 1.01 | 2.28 | 4.24 |
| ES: same, points | | 5.6 | 11.6 | 21.0 |
| ES: ATR5 itself, points | | 4.9 | | |
| NQ: pullback from entry, ATR5 | 137 | 1.00 | 1.97 | 3.75 |
| NQ: same, points | | 23.0 | 60.8 | 115.1 |
| NQ: ATR5 itself, points | | 27.7 | | |

Winners that went back below the sweep low before T1: 27%. His stop (tick past sweep, floor 1.5 ATR5) sits a median 2.35 ATR5 from the market entry.

Share of eventual winners a stop k × ATR5 below the market entry would have kept: 1.0: 50% · 1.5: 62% · 2.0: 73% · 2.5: 79% · 3.0: 84% · 4.0: 90%

### Reclaim entry P&L under different stops (market fill, everything else unchanged)

| stop | n | win% | avg R | H1 | H2 | PF |
|---|---|---|---|---|---|---|
| tick past sweep only | 405 | 38% | -0.08 | -0.03 | -0.21 | 0.81 |
| his rule: sweep, floor 1.0 ATR5 | 405 | 39% | -0.06 | +0.00 | -0.19 | 0.86 |
| his rule: sweep, floor 1.5 ATR5 (current) | 405 | 39% | -0.04 | +0.01 | -0.15 | 0.90 |
| sweep, floor 2.0 ATR5 | 405 | 42% | -0.02 | +0.05 | -0.16 | 0.95 |
| sweep, floor 2.5 ATR5 | 403 | 45% | -0.00 | +0.05 | -0.13 | 0.99 |
| sweep, floor 3.0 ATR5 | 401 | 46% | -0.02 | +0.04 | -0.15 | 0.96 |
| sweep − 0.25 ATR5 | 404 | 40% | -0.05 | +0.02 | -0.19 | 0.89 |
| sweep − 0.5 ATR5 | 402 | 42% | -0.04 | +0.01 | -0.15 | 0.90 |
| sweep − 1.0 ATR5 | 399 | 45% | -0.02 | +0.02 | -0.11 | 0.95 |

