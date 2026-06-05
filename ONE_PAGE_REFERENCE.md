# ONE-PAGE REFERENCE: All Contradictions Resolved

## THE CORE ISSUE
Old Sections 9–10 reference a stale backtest run. Revised Section 8 is from the current canonical run.

---

## CORRECT NUMBERS (Copy These Everywhere)

### Combined Portfolio Metrics
```
Metric                  OLD §9–10    CORRECT (§8)   SOURCE
Return                  8.30%        19.78%         ✅
Sharpe Ratio           0.345        0.9029         ✅
Volatility             14.98%       17.31%         ✅
Max Drawdown          -21.29%      -18.40%        ✅
Sortino                  —          1.2537         ✅
Alpha (FF5)            -7.63%       +3.33%         ✅
Alpha t-stat           -1.80         0.49          ✅
Alpha p-value          0.072        0.624          ✅
```

### Year-by-Year Breakdown
```
Year    OLD §9     CORRECT §8     KEY CHANGE
2023    16.16%     13.91%         —
2024    11.30%     13.31%         —
2025     2.32%     29.34%         🚨 INVERTED (was worst, now best)
```

### Key Metrics Tables
```
                       OLD §9–10           CORRECT         TABLE
Weight Sensitivity     All different       All identical    9.2
Threshold Sensitivity  Baseline 0.345      Baseline 0.9029  9.3
Year-by-Year          Baseline 8.30%      Baseline 19.78%  9.5
Bootstrap CI          [-0.814, 1.643]     [-0.2865, 2.221] 9.6
Random Portfolio %ile  11.4th              25.0th           9.7
Sector Attribution    IT +0.110 (best)    IT -0.4388 (worst) 9.8
```

---

## THE THREE BIGGEST FLIPS

| # | What | Old | New | Status |
|---|------|-----|-----|--------|
| 1 | **2025 Return** | 2.32% | **29.34%** | 🚨 INVERT narrative |
| 2 | **Combined Sharpe** | 0.345 | **0.9029** | 🔴 REDO all tables |
| 3 | **IT Sector Impact** | +0.110 | **-0.4388** | 🔴 FLIP conclusion |

---

## WHAT TO DO NOW

### Immediate (Today)
- [ ] Fill Table 8.1 blanks using performance_summary.csv
- [ ] Share this reference card with your group

### This Week
- [ ] Regenerate Tables 9.2, 9.3, 9.5–9.8 from corresponding CSVs
- [ ] Rewrite Sections 9.1, 9.8, 10.1–10.3 with new numbers

### Before Submission
- [ ] Check: Table 9.5 2025 = 29.34% (not 2.32%)
- [ ] Check: Table 9.8 IT = -0.4388 (not +0.110)
- [ ] Check: Section 10.1 alpha = +3.33% (not -7.63%)

---

## CSV FILES (Ground Truth)

| Table | CSV File |
|-------|----------|
| 8.1 Performance | performance_summary.csv |
| 8.2 Drawdowns | top_drawdowns.csv |
| 8.3 FF5 Regression | fama_french_regression.csv |
| 9.2 Weight Sens | weight_sensitivity.csv |
| 9.3 Threshold Sens | threshold_sensitivity.csv |
| 9.5 Year-by-Year | sub_period_analysis.csv |
| 9.6 Bootstrap CI | bootstrap_ci.csv |
| 9.7 Random Portfolios | random_portfolios.csv |
| 9.8 Sector Attribution | sector_attribution.csv |

All in: `/coursework_two/output/tables/`

---

## DETAILED DOCUMENTS

📄 **RECONCILIATION_CANONICAL_NUMBERS.md** — Full analysis  
📄 **QUICK_REFERENCE_CORRECT_NUMBERS.md** — Lookup tables  
📄 **CSV_SOURCE_MAPPING_REGENERATION_GUIDE.md** — Step-by-step  
📄 **SUMMARY_CORRECT_NUMBERS_ACTION_PLAN.md** — Master plan  

All in: `/Users/moha/Desktop/bigdatatshakh/`

---

## SUMMARY

✅ **Revised Section 8 is 100% canonical**  
❌ **Old Sections 9–10 are completely stale**  
🔄 **Copy new numbers from CSVs, regenerate all tables**  
⚠️ **2025 and IT sector conclusions flip completely**

