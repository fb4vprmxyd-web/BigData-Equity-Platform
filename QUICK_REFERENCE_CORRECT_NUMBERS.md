# Quick Reference: Correct Numbers for All Contradictions

Generated: 28 April 2026  
Source: Canonical CSVs in `/coursework_two/output/tables/`

---

## SECTION A: HEADLINE METRICS (Use These in All Sections 8–10)

```
Combined Portfolio Performance:
  Annualised Return:        19.78% (NOT 8.30%)
  Sharpe Ratio:             0.9029 (NOT 0.345)
  Annualised Volatility:    17.31% (NOT 14.98%)
  Maximum Drawdown:         -18.40% (NOT -21.29%)
  Sortino Ratio:            1.2537
  Information Ratio:        0.1752
  Fama-French Alpha:        +3.33% (NOT -7.63%)
  FF5 Alpha t-stat:         0.491 (NOT -1.80)
  FF5 Alpha p-value:        0.624 (NOT 0.072)
```

---

## SECTION B: YEAR-BY-YEAR BREAKDOWN (Replace §9.4 Table 9.5 with these)

```
2023 (Stub: 108 trading days, Aug–Dec)
  Annualised Return:        13.91%  (NOT 16.16%)
  Sharpe Ratio:             0.6824  (NOT 0.824)
  Max Drawdown:             -12.47% (NOT -11.92%)

2024 (Full year)
  Annualised Return:        13.31%  (NOT 11.30%)
  Sharpe Ratio:             0.6709  (NOT 0.592)
  Max Drawdown:             -9.14%

2025 (Full year)
  Annualised Return:        29.34%  (NOT 2.32% ⚠️ CRITICAL INVERSION)
  Sharpe Ratio:             1.1571  (NOT -0.011 ⚠️ CRITICAL INVERSION)
  Max Drawdown:             -17.45%
```

---

## SECTION C: DRAWDOWN TABLE (Table 8.2 is correct; update §9 references)

```
Rank 1 (Largest):
  Start:       2024-11-26
  Trough:      2025-04-08
  Recovery:    2025-09-05
  Depth:       -18.40%
  Duration:    283 days

Rank 2:
  Start:       2023-08-02
  Trough:      2023-10-27
  Recovery:    2023-12-01
  Depth:       -12.47%
  Duration:    121 days

Rank 3:
  Start:       2024-04-02
  Trough:      2024-04-19
  Recovery:    2024-08-29
  Depth:       -9.14%
  Duration:    149 days
```

---

## SECTION D: BOOTSTRAP CONFIDENCE INTERVALS (Replace §9.5 Table 9.6 completely)

```
Sharpe Ratio
  Point Estimate:           0.9029
  95% CI Lower:             -0.2865
  95% CI Upper:             2.2210
  P(Sharpe > 0):            92.88%

Annualised Return
  Point Estimate:           19.7801%
  95% CI Lower:             -3.23%
  95% CI Upper:             47.76%

Annualised Volatility
  Point Estimate:           17.3131%
  95% CI Lower:             14.63%
  95% CI Upper:             20.89%

Max Drawdown
  Point Estimate:           -18.4025%
  95% CI Lower:             -33.49%
  95% CI Upper:             -8.75%
```

---

## SECTION E: RANDOM PORTFOLIO BENCHMARK (Replace §9.6 Table 9.7 completely)

```
Strategy Sharpe:           0.9029
Random Portfolio Mean:     1.3587
Random Portfolio Std Dev:  0.5609
Percentile Rank:           25.0%  (NOT 11.4%)
P(Random Beats Strategy):  75.0%  (NOT 88.6%)

Interpretation: Strategy outperforms 25% of random portfolios;
                underperforms 75%. Worse than random.
```

---

## SECTION F: SECTOR ATTRIBUTION (Replace §9.7 Table 9.8 completely)

Use these values; note IT is now NEGATIVE (old table had sign wrong):

```
Excluded Sector          Sharpe    Δ Sharpe vs Baseline
─────────────────────────────────────────────────────
None (Baseline)          0.9029    —
Communication Services   0.5332    -0.3697
Consumer Discretionary   0.7683    -0.1346
Consumer Staples         1.0561    +0.1532 ✓ IMPROVES when excluded
Energy                   0.9238    +0.0209
Financials               0.7486    -0.1543
Health Care              1.0763    +0.1734 ✓ IMPROVES when excluded
Industrials              0.9437    +0.0408
Information Technology   0.4641    -0.4388 🚨 MOST NEGATIVE (NOT positive!)
Materials                0.9439    +0.0410
Real Estate              0.8706    -0.0323
Utilities                0.8993    -0.0036
```

**KEY INVERSION**: Old table showed IT as +0.110 (best to include).  
**Reality**: IT is -0.4388 (worst included sector). Complete sign flip.

---

## SECTION G: LATEST SECTOR ALLOCATION (From 2025-10-31 rebalance)

```
Number of Holdings:       10
Number of Sectors:        6
Largest Sector:           Financials (20.0%)
Max Sector Cap:           20% (0.2)
HHI Index:                0.10 (perfect 10-way equal weight)
Effective N:              10.0
```

---

## SECTION H: TURNOVER & COSTS

```
Average Quarterly Turnover:       51.69%
Annualised Turnover:              206.77%
Cumulative Trading Cost:          129.23 bps (NOT 108 bps)
Max Single-Rebalance Turnover:    70.00%
Min Single-Rebalance Turnover:    32.22%
Number of Rebalances:             10
```

---

## SECTION I: HYPOTHESIS TEST VERDICTS (Update §9.8 & §10.3)

```
OLD VERDICT          ➜  NEW VERDICT (Canonical)
─────────────────────────────────────────────────────────────
H1 fails clearly     ➜  Essentially tied with S&P 500 (0.9029 vs 0.9219)
                        BUT fails vs MSCI Value (0.9029 vs 1.0570)
                        MIXED on Sharpe

H2 fails clearly     ➜  Tied with S&P 500 drawdown (-18.40% vs -18.90%)
                        BUT fails vs MSCI Value (-18.40% vs -14.46%)
                        MIXED on drawdown

I5: 2023 strong,     ➜  2025 is the strongest year (29.34% return)
    2024-25 weak          2025 recovery drives full-period return
                        COMPLETE NARRATIVE FLIP

I6: Negative alpha   ➜  Alpha is +3.33% (positive but insignificant)
                        Random portfolio at 25th percentile (worse than random)
                        Alpha sign flips; random test still negative
```

---

## SECTION J: VALUE-ONLY & SENTIMENT-ONLY MISSING VALUES

**Fill Table 8.1 placeholder dashes with these:**

```
VALUE-ONLY PORTFOLIO:
  Annualised Return:        14.71%
  Annualised Volatility:    29.10%
  Sharpe Ratio:             0.4804
  Sortino Ratio:            0.5614
  Calmar Ratio:             0.7176
  Max Drawdown:             -20.50%
  Information Ratio:        0.0115

SENTIMENT-ONLY PORTFOLIO:
  Annualised Return:        9.44%
  Annualised Volatility:    16.42%
  Sharpe Ratio:             0.3925
  Sortino Ratio:            0.5411
  Calmar Ratio:             0.4309
  Max Drawdown:             -21.91%
  Information Ratio:        -0.8347
```

---

## SECTION K: FAMA-FRENCH 5-FACTOR REGRESSION (Update Table 8.3 t-stats)

```
Factor              Coefficient    t-stat      p-value
─────────────────────────────────────────────────────────
Alpha               +0.0333        +0.491      0.624
Mkt-RF              0.8198         14.703      <0.001
SMB                 0.0457         0.872       0.383
HML                 0.5647         7.507       <0.001
RMW                -0.1638        -2.348       0.019
CMA                 0.2144         2.593       0.010
```

**Update t-stats P9 and P10**: Mkt-RF was 26.74 (old), now 14.70; HML was 13.66, now 7.51.

---

## SECTION L: WEIGHT SENSITIVITY (Entire Table 9.2 baseline row)

All weight combinations from 0.05/0.95 to 1.0/0.0 yield **identical results**:

```
Sharpe:              0.9029  (for all weights)
Return:              19.78%  (for all weights)
Max DD:              -18.40% (for all weights)
Volatility:          17.31%  (for all weights)
```

Exception: 0.0/1.0 (pure sentiment) gives:
```
Sharpe:              0.2053  (NOT 0.622 as in old §9.2)
Return:              6.10%
Max DD:              -21.09%
Vol:                 16.01%
```

---

## SECTION M: CHECKLIST—What Numbers Changed Most

| # | Category | Old | New | Change | Severity |
|---|----------|-----|-----|--------|----------|
| 1 | **2025 Return** | 2.32% | **29.34%** | +2,600 bps | 🚨 CRITICAL |
| 2 | **2025 Sharpe** | -0.011 | **1.1571** | +1.168 | 🚨 CRITICAL |
| 3 | **Combined Sharpe** | 0.345 | **0.9029** | +0.558 | 🚨 CRITICAL |
| 4 | **Combined Return** | 8.30% | **19.78%** | +1,148 bps | 🚨 CRITICAL |
| 5 | **Alpha** | -7.63% | **+3.33%** | +996 bps | 🔴 HIGH |
| 6 | **Cumulative Cost** | 108 bps | **129 bps** | +21 bps | 🟡 MEDIUM |
| 7 | **IT Sector Impact** | +0.110 | **-0.4388** | -0.549 | 🔴 HIGH |
| 8 | **Percentile Rank** | 11.4th | **25.0th** | +13.6pp | 🟡 MEDIUM |

---

## FINAL INSTRUCTION

**For every mention of old numbers in Sections 9–10, replace with canonical values above.**  
**Copy these numbers directly from the CSVs; do NOT recalculate or estimate.**

