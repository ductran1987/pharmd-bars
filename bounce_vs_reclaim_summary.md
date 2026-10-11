# Near-edge bounce vs. fail-and-reclaim — PharmD fade setups

## Part 1 — what happens after price touches the near edge · Graded setups (A/B/C)

425 setups where price was outside the zone when the letter came out; **294 touched the near edge** (69%).

| path after the touch | count | % of touches |
|---|---|---|
| Held (no 5m close beyond far edge) **and hit T1** | 77 | **26%** |
| Held, but T1 not reached by 15:55 | 2 | 1% |
| Lost the far edge (5m close beyond it) | 215 | 73% |
| &nbsp;&nbsp;↳ reclaimed the **far** edge, then hit T1 before a new low | 69 | 23% (= 32% of losses; 36% of reclaims) |
| &nbsp;&nbsp;↳ reclaimed the far edge, then made a new low first | 114 | 39% |
| &nbsp;&nbsp;↳ reclaimed the far edge, neither by 15:55 | 11 | 4% |
| &nbsp;&nbsp;↳ never reclaimed the far edge | 21 | 7% |
| &nbsp;&nbsp;↳ reclaimed the **near** edge, then hit T1 before a new low | 84 | 29% (= 39% of losses; 47% of reclaims) |
| &nbsp;&nbsp;↳ reclaimed the near edge, then made a new low first | 85 | 29% |
| &nbsp;&nbsp;↳ reclaimed the near edge, neither by 15:55 | 11 | 4% |
| &nbsp;&nbsp;↳ never reclaimed the near edge | 35 | 12% |

**How deep the winning holds went before T1** (77 trades; 0 = near edge, 1 = far edge):  only tagged the near edge (≤ 2 ticks in): 10% · median depth 0.72 of the zone · 75th pct 1.50 · wicked past the far edge without closing there: 43%.  In ATR5: median 0.41, 75th pct 0.78.

Median zone width 0.47 ATR5; median distance near edge → T1 2.50 ATR5.

## Part 1 — what happens after price touches the near edge · All fade setups (graded + ungraded)

913 setups where price was outside the zone when the letter came out; **617 touched the near edge** (68%).

| path after the touch | count | % of touches |
|---|---|---|
| Held (no 5m close beyond far edge) **and hit T1** | 168 | **27%** |
| Held, but T1 not reached by 15:55 | 4 | 1% |
| Lost the far edge (5m close beyond it) | 445 | 72% |
| &nbsp;&nbsp;↳ reclaimed the **far** edge, then hit T1 before a new low | 161 | 26% (= 36% of losses; 40% of reclaims) |
| &nbsp;&nbsp;↳ reclaimed the far edge, then made a new low first | 222 | 36% |
| &nbsp;&nbsp;↳ reclaimed the far edge, neither by 15:55 | 20 | 3% |
| &nbsp;&nbsp;↳ never reclaimed the far edge | 42 | 7% |
| &nbsp;&nbsp;↳ reclaimed the **near** edge, then hit T1 before a new low | 193 | 31% (= 43% of losses; 51% of reclaims) |
| &nbsp;&nbsp;↳ reclaimed the near edge, then made a new low first | 165 | 27% |
| &nbsp;&nbsp;↳ reclaimed the near edge, neither by 15:55 | 19 | 3% |
| &nbsp;&nbsp;↳ never reclaimed the near edge | 68 | 11% |

**How deep the winning holds went before T1** (168 trades; 0 = near edge, 1 = far edge):  only tagged the near edge (≤ 2 ticks in): 11% · median depth 0.82 of the zone · 75th pct 2.00 · wicked past the far edge without closing there: 44%.  In ATR5: median 0.37, 75th pct 0.81.

Median zone width 0.42 ATR5; median distance near edge → T1 2.30 ATR5.

## Part 2 — executable trades · Graded setups (425 setups offered)

Same management for every row: $500 risk, BE at +1R, exit at first PharmD target ≥ 1.5R, flat 15:55. "$ per setup offered" puts strategies that trade more or less often on the same footing.

| strategy | trades | fill/trigger rate | win | hit target | avg R | total $ | $ per setup offered | PF |
|---|---|---|---|---|---|---|---|---|
| Limit near edge +2t (front-run), touch fill, stop far−0.5 ATR5 | 296 | 70% | 18% | 17% | -0.22 | $-33,222 | $-78 | 0.64 |
| &nbsp;&nbsp;↳ H1 | 148 | 72% | 17% | 16% | -0.24 | $-17,562 | $-86 | 0.62 |
| &nbsp;&nbsp;↳ H2 | 148 | 67% | 19% | 19% | -0.21 | $-15,661 | $-71 | 0.66 |
| Limit at near edge, stop far−0.5 ATR5 | 292 | 69% | 16% | 15% | -0.32 | $-46,439 | $-109 | 0.52 |
| &nbsp;&nbsp;↳ H1 | 145 | 71% | 14% | 14% | -0.32 | $-23,453 | $-114 | 0.51 |
| &nbsp;&nbsp;↳ H2 | 147 | 67% | 17% | 17% | -0.31 | $-22,986 | $-104 | 0.52 |
| Limit at near edge, stop far−1.0 ATR5 | 292 | 69% | 20% | 20% | -0.23 | $-33,044 | $-78 | 0.61 |
| &nbsp;&nbsp;↳ H1 | 145 | 71% | 21% | 20% | -0.20 | $-14,543 | $-71 | 0.67 |
| &nbsp;&nbsp;↳ H2 | 147 | 67% | 20% | 19% | -0.25 | $-18,502 | $-84 | 0.56 |
| Limit at near edge, stop entry−1.5 ATR5 | 292 | 69% | 21% | 21% | -0.17 | $-24,895 | $-59 | 0.70 |
| &nbsp;&nbsp;↳ H1 | 145 | 71% | 21% | 20% | -0.20 | $-14,681 | $-72 | 0.65 |
| &nbsp;&nbsp;↳ H2 | 147 | 67% | 22% | 22% | -0.14 | $-10,214 | $-46 | 0.75 |
| Limit 2t inside near edge, stop far−0.5 ATR5 | 291 | 68% | 16% | 16% | -0.30 | $-43,759 | $-103 | 0.55 |
| &nbsp;&nbsp;↳ H1 | 144 | 70% | 15% | 15% | -0.27 | $-19,615 | $-96 | 0.60 |
| &nbsp;&nbsp;↳ H2 | 147 | 67% | 17% | 17% | -0.33 | $-24,144 | $-110 | 0.51 |
| Fail → reclaim FAR edge · idealized fill at edge (not executable) | 232 | 55% | 34% | 32% | +0.14 | $16,054 | $+38 | 1.34 |
| &nbsp;&nbsp;↳ H1 | 116 | 57% | 37% | 36% | +0.17 | $9,980 | $+49 | 1.39 |
| &nbsp;&nbsp;↳ H2 | 116 | 53% | 30% | 28% | +0.10 | $6,075 | $+28 | 1.28 |
| Fail → reclaim FAR edge · market on reclaim close | 232 | 55% | 31% | 29% | -0.09 | $-10,395 | $-24 | 0.82 |
| &nbsp;&nbsp;↳ H1 | 116 | 57% | 31% | 28% | -0.10 | $-6,038 | $-29 | 0.80 |
| &nbsp;&nbsp;↳ H2 | 116 | 53% | 32% | 29% | -0.08 | $-4,357 | $-20 | 0.83 |
| Fail → reclaim FAR edge · buy-stop 1t above edge | 244 | 57% | 25% | 24% | -0.09 | $-10,596 | $-25 | 0.83 |
| &nbsp;&nbsp;↳ H1 | 122 | 60% | 32% | 30% | +0.05 | $2,962 | $+14 | 1.10 |
| &nbsp;&nbsp;↳ H2 | 122 | 55% | 19% | 18% | -0.22 | $-13,558 | $-62 | 0.60 |
| Fail → reclaim NEAR edge · idealized fill at edge (not executable) | 212 | 50% | 41% | 38% | +0.13 | $13,506 | $+32 | 1.33 |
| &nbsp;&nbsp;↳ H1 | 104 | 51% | 48% | 44% | +0.24 | $12,350 | $+60 | 1.69 |
| &nbsp;&nbsp;↳ H2 | 108 | 49% | 33% | 31% | +0.02 | $1,156 | $+5 | 1.05 |
| Fail → reclaim NEAR edge · market on reclaim close | 211 | 50% | 37% | 35% | -0.05 | $-5,128 | $-12 | 0.89 |
| &nbsp;&nbsp;↳ H1 | 104 | 51% | 44% | 40% | +0.03 | $1,330 | $+6 | 1.06 |
| &nbsp;&nbsp;↳ H2 | 107 | 49% | 31% | 30% | -0.12 | $-6,459 | $-29 | 0.74 |
| Fail → reclaim NEAR edge · buy-stop 1t above edge | 227 | 53% | 31% | 30% | -0.09 | $-10,399 | $-24 | 0.82 |
| &nbsp;&nbsp;↳ H1 | 112 | 55% | 37% | 34% | +0.00 | $187 | $+1 | 1.01 |
| &nbsp;&nbsp;↳ H2 | 115 | 52% | 26% | 25% | -0.18 | $-10,586 | $-48 | 0.65 |
| COMBO: limit near (stop far0.5) + re-enter on far reclaim (close) | 431 | 101% | 22% | 21% | -0.23 | $-50,080 | $-118 | 0.61 |
| COMBO: limit near (stop far0.5) + re-enter on far reclaim (stop) | 441 | 104% | 21% | 21% | -0.21 | $-45,617 | $-107 | 0.65 |
| COMBO: limit near (stop far1.0) + re-enter on far reclaim (close) | 419 | 99% | 26% | 25% | -0.15 | $-32,458 | $-76 | 0.71 |

## Part 2 — executable trades · All fade setups (913 setups offered)

Same management for every row: $500 risk, BE at +1R, exit at first PharmD target ≥ 1.5R, flat 15:55. "$ per setup offered" puts strategies that trade more or less often on the same footing.

| strategy | trades | fill/trigger rate | win | hit target | avg R | total $ | $ per setup offered | PF |
|---|---|---|---|---|---|---|---|---|
| Limit near edge +2t (front-run), touch fill, stop far−0.5 ATR5 | 623 | 68% | 19% | 18% | -0.22 | $-67,335 | $-74 | 0.65 |
| Limit at near edge, stop far−0.5 ATR5 | 614 | 67% | 17% | 16% | -0.29 | $-88,572 | $-97 | 0.55 |
| Limit at near edge, stop far−1.0 ATR5 | 614 | 67% | 22% | 21% | -0.17 | $-51,962 | $-57 | 0.70 |
| Limit at near edge, stop entry−1.5 ATR5 | 614 | 67% | 23% | 23% | -0.12 | $-36,284 | $-40 | 0.78 |
| Limit 2t inside near edge, stop far−0.5 ATR5 | 611 | 67% | 17% | 16% | -0.28 | $-85,165 | $-93 | 0.58 |
| Fail → reclaim FAR edge · idealized fill at edge (not executable) | 490 | 54% | 35% | 33% | +0.14 | $33,861 | $+37 | 1.36 |
| Fail → reclaim FAR edge · market on reclaim close | 490 | 54% | 33% | 30% | -0.08 | $-19,675 | $-22 | 0.83 |
| Fail → reclaim FAR edge · buy-stop 1t above edge | 518 | 57% | 28% | 26% | -0.08 | $-20,088 | $-22 | 0.84 |
| Fail → reclaim NEAR edge · idealized fill at edge (not executable) | 450 | 49% | 42% | 39% | +0.13 | $29,728 | $+33 | 1.37 |
| Fail → reclaim NEAR edge · market on reclaim close | 447 | 49% | 39% | 36% | -0.05 | $-10,445 | $-11 | 0.89 |
| Fail → reclaim NEAR edge · buy-stop 1t above edge | 484 | 53% | 34% | 31% | -0.06 | $-15,167 | $-17 | 0.86 |
| COMBO: limit near (stop far0.5) + re-enter on far reclaim (close) | 904 | 99% | 23% | 22% | -0.21 | $-96,116 | $-105 | 0.64 |
| COMBO: limit near (stop far0.5) + re-enter on far reclaim (stop) | 924 | 101% | 22% | 22% | -0.18 | $-83,214 | $-91 | 0.69 |
| COMBO: limit near (stop far1.0) + re-enter on far reclaim (close) | 883 | 97% | 28% | 27% | -0.12 | $-52,763 | $-58 | 0.77 |

