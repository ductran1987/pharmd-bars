# Fail-and-reclaim on a 1-minute close — PharmD fade setups

889 of 995 fade setups have 1m bars from the plan's contract covering the session (ES through 2026-10-02; NQ missing 2025-12-19 → 2026-02-27 and after 2026-08-07).

## Graded setups (351 setups offered)

| strategy | trades | fill/trigger rate | win | hit target | avg R | total $ | $ per setup offered | PF |
|---|---|---|---|---|---|---|---|---|
| Limit at near edge, stop entry−1.5 ATR5 (1m bars) | 247 | 70% | 22% | 21% | -0.15 | $-17,925 | $-51 | 0.73 |
| Limit at near edge, stop far−0.5 ATR5 (1m bars) | 247 | 70% | 15% | 15% | -0.30 | $-36,503 | $-104 | 0.51 |
| Reclaim NEAR · 5m lost / 5m reclaim · market (earlier test) | 178 | 51% | 38% | 36% | -0.04 | $-3,280 | $-9 | 0.91 |
| &nbsp;&nbsp;↳ H1 | 102 | 51% | 45% | 41% | +0.05 | $2,488 | $+13 | 1.12 |
| &nbsp;&nbsp;↳ H2 | 76 | 50% | 29% | 29% | -0.15 | $-5,768 | $-38 | 0.68 |
| Reclaim NEAR · 5m lost / 5m reclaim · edge fill (not executable) | 179 | 51% | 41% | 39% | +0.15 | $13,344 | $+38 | 1.40 |
| Reclaim NEAR · 1m lost / **1m reclaim** · market | 199 | 57% | 31% | 31% | -0.08 | $-8,191 | $-23 | 0.83 |
| &nbsp;&nbsp;↳ H1 | 115 | 58% | 32% | 31% | -0.07 | $-4,311 | $-22 | 0.85 |
| &nbsp;&nbsp;↳ H2 | 84 | 55% | 30% | 30% | -0.09 | $-3,880 | $-26 | 0.81 |
| Reclaim NEAR · 1m lost / 1m reclaim · edge fill (not executable) | 199 | 57% | 31% | 30% | -0.02 | $-1,884 | $-5 | 0.96 |
| Reclaim NEAR · 5m lost / **1m reclaim** · market | 185 | 53% | 32% | 31% | -0.07 | $-6,109 | $-17 | 0.86 |
| &nbsp;&nbsp;↳ H1 | 108 | 54% | 36% | 34% | +0.01 | $281 | $+1 | 1.01 |
| &nbsp;&nbsp;↳ H2 | 77 | 51% | 27% | 27% | -0.17 | $-6,390 | $-42 | 0.67 |
| Reclaim NEAR · 5m lost / 1m reclaim · edge fill (not executable) | 185 | 53% | 33% | 32% | +0.01 | $1,030 | $+3 | 1.03 |
| Reclaim FAR · 5m lost / 5m reclaim · market (earlier test) | 196 | 56% | 31% | 29% | -0.09 | $-9,036 | $-26 | 0.81 |
| &nbsp;&nbsp;↳ H1 | 114 | 57% | 32% | 29% | -0.09 | $-4,881 | $-25 | 0.83 |
| &nbsp;&nbsp;↳ H2 | 82 | 54% | 29% | 29% | -0.10 | $-4,155 | $-27 | 0.78 |
| Reclaim FAR · 5m lost / 5m reclaim · edge fill (not executable) | 196 | 56% | 33% | 32% | +0.12 | $11,593 | $+33 | 1.28 |
| Reclaim FAR · 1m lost / **1m reclaim** · market | 211 | 60% | 27% | 27% | -0.07 | $-7,535 | $-21 | 0.86 |
| &nbsp;&nbsp;↳ H1 | 124 | 62% | 30% | 29% | -0.01 | $-797 | $-4 | 0.97 |
| &nbsp;&nbsp;↳ H2 | 87 | 57% | 23% | 23% | -0.15 | $-6,738 | $-44 | 0.70 |
| Reclaim FAR · 1m lost / 1m reclaim · edge fill (not executable) | 211 | 60% | 28% | 28% | +0.03 | $2,681 | $+8 | 1.05 |
| Reclaim FAR · 5m lost / **1m reclaim** · market | 197 | 56% | 29% | 27% | -0.05 | $-4,718 | $-13 | 0.90 |
| &nbsp;&nbsp;↳ H1 | 116 | 58% | 34% | 31% | +0.06 | $3,768 | $+19 | 1.14 |
| &nbsp;&nbsp;↳ H2 | 81 | 53% | 22% | 21% | -0.21 | $-8,486 | $-56 | 0.59 |
| Reclaim FAR · 5m lost / 1m reclaim · edge fill (not executable) | 197 | 56% | 31% | 30% | +0.07 | $6,428 | $+18 | 1.15 |

## All fade setups (816 setups offered)

| strategy | trades | fill/trigger rate | win | hit target | avg R | total $ | $ per setup offered | PF |
|---|---|---|---|---|---|---|---|---|
| Limit at near edge, stop entry−1.5 ATR5 (1m bars) | 553 | 68% | 24% | 24% | -0.10 | $-26,567 | $-33 | 0.82 |
| Limit at near edge, stop far−0.5 ATR5 (1m bars) | 553 | 68% | 16% | 16% | -0.30 | $-83,884 | $-103 | 0.51 |
| Reclaim NEAR · 5m lost / 5m reclaim · market (earlier test) | 405 | 50% | 39% | 36% | -0.04 | $-8,641 | $-11 | 0.90 |
| Reclaim NEAR · 5m lost / 5m reclaim · edge fill (not executable) | 407 | 50% | 42% | 39% | +0.14 | $28,455 | $+35 | 1.40 |
| Reclaim NEAR · 1m lost / **1m reclaim** · market | 450 | 55% | 37% | 35% | +0.01 | $2,597 | $+3 | 1.03 |
| Reclaim NEAR · 1m lost / 1m reclaim · edge fill (not executable) | 450 | 55% | 36% | 35% | +0.09 | $19,294 | $+24 | 1.22 |
| Reclaim NEAR · 5m lost / **1m reclaim** · market | 420 | 51% | 37% | 34% | -0.03 | $-7,041 | $-9 | 0.92 |
| Reclaim NEAR · 5m lost / 1m reclaim · edge fill (not executable) | 421 | 52% | 36% | 34% | +0.03 | $6,614 | $+8 | 1.08 |
| Reclaim FAR · 5m lost / 5m reclaim · market (earlier test) | 442 | 54% | 32% | 30% | -0.09 | $-19,403 | $-24 | 0.81 |
| Reclaim FAR · 5m lost / 5m reclaim · edge fill (not executable) | 442 | 54% | 35% | 33% | +0.13 | $28,050 | $+34 | 1.33 |
| Reclaim FAR · 1m lost / **1m reclaim** · market | 481 | 59% | 31% | 29% | -0.00 | $-423 | $-1 | 1.00 |
| Reclaim FAR · 1m lost / 1m reclaim · edge fill (not executable) | 481 | 59% | 32% | 31% | +0.09 | $21,656 | $+27 | 1.21 |
| Reclaim FAR · 5m lost / **1m reclaim** · market | 451 | 55% | 31% | 28% | -0.05 | $-10,930 | $-13 | 0.89 |
| Reclaim FAR · 5m lost / 1m reclaim · edge fill (not executable) | 451 | 55% | 33% | 30% | +0.06 | $12,891 | $+16 | 1.13 |

## How far past the edge the confirming close is (graded, market entries), in ATR5

| variant | median | 75th pct |
|---|---|---|
| Reclaim NEAR · 1m lost / **1m reclaim** · market | 0.16 | 0.28 |
| Reclaim NEAR · 5m lost / **1m reclaim** · market | 0.15 | 0.28 |
| Reclaim FAR · 1m lost / **1m reclaim** · market | 0.14 | 0.28 |
| Reclaim FAR · 5m lost / **1m reclaim** · market | 0.15 | 0.29 |

## Per instrument (graded, market entries)

| strategy | trades | fill/trigger rate | win | hit target | avg R | total $ | $ per setup offered | PF |
|---|---|---|---|---|---|---|---|---|
| Reclaim NEAR · 5m lost / 5m reclaim · market (earlier test) — ES | 108 | 51% | 37% | 36% | -0.07 | $-4,039 | $-19 | 0.84 |
| Reclaim NEAR · 5m lost / 5m reclaim · market (earlier test) — NQ | 70 | 50% | 40% | 36% | +0.02 | $759 | $+5 | 1.06 |
| Reclaim NEAR · 1m lost / **1m reclaim** · market — ES | 120 | 57% | 32% | 32% | -0.10 | $-5,788 | $-27 | 0.81 |
| Reclaim NEAR · 1m lost / **1m reclaim** · market — NQ | 79 | 56% | 29% | 28% | -0.06 | $-2,403 | $-17 | 0.86 |
| Reclaim NEAR · 5m lost / **1m reclaim** · market — ES | 111 | 53% | 34% | 33% | -0.07 | $-3,610 | $-17 | 0.87 |
| Reclaim NEAR · 5m lost / **1m reclaim** · market — NQ | 74 | 53% | 30% | 28% | -0.07 | $-2,499 | $-18 | 0.84 |
