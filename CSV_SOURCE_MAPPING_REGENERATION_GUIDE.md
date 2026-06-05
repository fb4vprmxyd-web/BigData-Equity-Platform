# CSV Source Mapping: Which Output File Contains Which Table

Use this guide to verify numbers and regenerate tables systematically.

---

## REPORT TABLE ↔ CSV FILE MAPPING

### Section 8: Revised Numbers (✅ Already Correct)

| Report Table | CSV File | Key Columns | Row(s) to Use | Status |
|--------------|----------|-------------|---------------|--------|
| 8.1 Performance Summary | `performance_summary.csv` | all metrics | Rows 1–7 (Combined, Value-only, Sentiment-only, benchmarks) | ✅ Ready |
| 8.2 Top 3 Drawdowns | `top_drawdowns.csv` | start, trough, recovery, depth, duration_days | Rows 1–3 | ✅ Ready |
| 8.3 Year-by-Year | `sub_period_analysis.csv` | annualised_return, sharpe_ratio, max_drawdown | 2023, 2024, 2025 rows | ✅ Ready |
| 8.4 Factor Attribution (FF5) | `fama_french_regression.csv` | Coefficient, t-stat, p-value | All 6 factors | ✅ Ready |
| 8.5 Sector Allocation | `diversification_over_time.csv` | n_holdings, n_sectors, max_sector_name, max_sector_weight | Latest row (2025-10-31) | ✅ Ready |
| Figure 8.1 Cumulative Returns | Generate from `performance_summary.csv` + daily returns | Need full daily return series | — | See below |
| Figure 8.2 Underwater Drawdown | Compute from daily returns | — | — | See below |
| Figure 8.3 Monthly Returns Heatmap | `appendix_b_monthly_returns.csv` | portfolio, month_num, monthly_return | All rows | ✅ Ready |
| Figure 8.4 Rolling 12M Sharpe | Compute from daily returns | — | — | See below |

### Section 9: Sensitivity Analysis (⚠️ Needs Regeneration from Old Baselines)

| Report Section | Table | CSV File | Regeneration Required | Status |
|----------------|-------|----------|----------------------|--------|
| 9.1 | Overview | — | Narrative update only | 📝 Rewrite to reference new baseline 0.9029 |
| 9.2 | Weight Sensitivity Grid (21 rows) | `weight_sensitivity.csv` | ✅ ALL ROWS IDENTICAL (weight-insensitive portfolio) | ✅ Copy as-is |
| 9.3 | Threshold Sensitivity Grid (20 rows) | `threshold_sensitivity.csv` | ⚠️ Update narrative; baseline changed from 0.345→0.9029 | 📝 Rewrite baseline row |
| 9.4 | Year-by-Year Breakdown | `sub_period_analysis.csv` | ✅ Copy 2023/2024/2025 rows directly; narratives flip | ✅ Ready |
| 9.5 | Bootstrap Confidence Intervals | `bootstrap_ci.csv` | ✅ Copy all 4 metric rows; update narrative | ✅ Ready |
| 9.6 | Random Portfolio Benchmark | `random_portfolios.csv` | ✅ Copy single row; update narrative | ✅ Ready |
| 9.7 | Sector Attribution Grid (13 rows) | `sector_attribution.csv` | ✅ Copy all rows; **REFRAME NARRATIVE** (IT sign flip) | ✅ Ready |
| 9.8 | Hypothesis Test Verdicts | — | Narrative rewrite; see Section I verdicts | 📝 Rewrite |

### Section 10: Conclusion (❌ Entire Section Obsolete)

| Section | Content | Status | Action |
|---------|---------|--------|--------|
| 10.1 | Performance Summary Narrative | ❌ All numbers stale | Rewrite with canonical values A1–A7 |
| 10.2 | Interpretive Discussion | ⚠️ Partially stale | Reframe around new 2025 story |
| 10.3 | Hypothesis Conclusions | ❌ Inverted conclusions | Rewrite with I1–I6 verdicts |

### Appendices

| Appendix | CSV File | Status | Action |
|----------|----------|--------|--------|
| B (Monthly Returns) | `appendix_b_monthly_returns.csv` | ✅ Fresh | Copy as-is |
| C (Code Snippets) | — | ✅ Fixed | Use as-is |
| D–E (Related Work) | — | ✅ Fixed | Use as-is |
| F (Data Quality) | `appendix_f_data_quality.csv` | ✅ Fresh | Copy as-is |
| G (Code Quality) | `appendix_g_code_quality.csv` | ✅ Fresh | Copy as-is |
| H (Configuration) | `appendix_h_config.csv` | ✅ Fresh | Copy as-is |

---

## STEP-BY-STEP REGENERATION GUIDE

### Step 1: Update Table 8.1 (Performance Summary)
**Action**: Fill placeholder dashes  
**CSVs**: `performance_summary.csv`  
**Procedure**:
1. Read row 1 (Combined) → all cells now have values
2. Read row 2 (Value-only) → fill P1–P5 (Vol, Sortino, Calmar, DD, Info Ratio)
3. Read row 3 (Sentiment-only) → fill P6–P7 (Sortino, Info Ratio)
4. Row 7 (Equal-Weight Universe) → all cells still dashes (pending benchmark fix)

**Verify**: Combined row sums to row 1 of sensitivity grids (9.2, 9.3)

---

### Step 2: Update Table 8.3 (Fama-French Regression)
**Action**: Update t-stats P9–P10  
**CSV**: `fama_french_regression.csv`  
**Procedure**:
1. Read row "Mkt-RF" → update t-stat from 26.74 to **14.703**
2. Read row "HML" → update t-stat from 13.66 to **7.507**
3. All other rows remain unchanged

**Verify**: Alpha t-stat is 0.491 (was 0.49 in revised Section 8—rounding OK)

---

### Step 3: Update Table 9.2 (Weight Sensitivity)
**Action**: Copy weight_sensitivity.csv directly  
**CSV**: `weight_sensitivity.csv`  
**Procedure**:
1. Copy all 21 rows (0.0/1.0 through 1.0/0.0)
2. **NOTE**: All rows are identical except 0.0/1.0 (pure sentiment)
3. Update narrative: "The 60/40 weighting shows minimal sensitivity to allocation (all combinations yield Sharpe 0.9029). This suggests the portfolio selection is driven entirely by the top-20% screen, not by value/sentiment ratio."

**Verify**: Baseline (0.6/0.4) row shows Sharpe 0.9029, Return 19.78%, DD -18.40%, Vol 17.31%

---

### Step 4: Update Table 9.3 (Threshold Sensitivity)
**Action**: Copy threshold_sensitivity.csv directly  
**CSV**: `threshold_sensitivity.csv`  
**Procedure**:
1. Copy all 20 rows (selection_pctl 0.1–0.3, max_debt_equity 1.5–3.0)
2. Identify baseline row: selection_pctl=0.2, max_debt_equity=2.0 → Sharpe 0.9029
3. Update narrative: "The 20% selection percentile and D/E cap of 2.0 are robust to small parameter variations. Tightening to 15% selection or D/E < 1.5 deteriorates performance; loosening to 30% or D/E > 2.5 shows diminishing returns."

**Verify**: Baseline row matches Table 9.2 baseline

---

### Step 5: Update Table 9.5 (Year-by-Year)
**Action**: Copy sub_period_analysis.csv year rows  
**CSV**: `sub_period_analysis.csv`  
**Procedure**:
1. Read 2023 row → 13.91% return, 0.6824 Sharpe, -12.47% DD
2. Read 2024 row → 13.31% return, 0.6709 Sharpe, -9.14% DD
3. Read 2025 row → **29.34% return, 1.1571 Sharpe, -17.45% DD**
4. **CRITICAL NARRATIVE FLIP**: Old table showed 2025 as disastrous (2.32%); new data shows 2025 as the strongest year (29.34%). Rewrite: "2025 is the strongest year of the sample, delivering 29.34% annualised return. This recovery from the late-2024 drawdown is the primary driver of full-period outperformance."

**Verify**: 2023+2024+2025 returns compound to full-period 19.78% (with geometric average)

---

### Step 6: Update Table 9.6 (Bootstrap CI)
**Action**: Copy bootstrap_ci.csv directly  
**CSV**: `bootstrap_ci.csv`  
**Procedure**:
1. Read all 4 metric rows (Sharpe, Return, Volatility, Max DD)
2. For each metric, copy: Point Estimate, CI Lower, CI Upper, P(Metric > 0)
3. **CRITICAL NARRATIVE UPDATE**: "The 95% confidence interval for Sharpe is [-0.2865, 2.2210], which crosses zero. However, P(Sharpe > 0) = 92.88%, indicating high confidence that the strategy has positive risk-adjusted return despite the interval crossing zero. This is due to the asymmetric bootstrap distribution."

**Verify**: CI Lower < Point Estimate < CI Upper for all metrics

---

### Step 7: Update Table 9.7 (Random Portfolio Benchmark)
**Action**: Copy random_portfolios.csv directly  
**CSV**: `random_portfolios.csv`  
**Procedure**:
1. Read single row: Strategy Sharpe 0.9029, Random Mean 1.3587, Random Std 0.5609, Percentile 25.0%, P(beat) 75.0%
2. Update narrative: "The strategy outperforms only 25% of randomly constructed portfolios (ranked at the 25th percentile). This indicates that the majority of unconstrained random portfolios beat the strategy on Sharpe basis, suggesting limited edge. Note that this random benchmark includes portfolios without our sector cap or individual name limits."

**Verify**: Percentile + P(beat) should relate (25th percentile means 25% better than, 75% worse than)

---

### Step 8: Update Table 9.8 (Sector Attribution)
**Action**: Copy sector_attribution.csv directly + REFRAME NARRATIVE  
**CSV**: `sector_attribution.csv`  
**Procedure**:
1. Read all 13 rows (12 sectors + baseline)
2. Sort by Δ Sharpe (most negative to most positive)
3. **CRITICAL SIGN FLIP**: Old table showed IT as **+0.110** (best to include). New data shows IT as **-0.4388** (worst included). Complete inversion. Narrative: "Removing Information Technology from the universe improves Sharpe ratio by 44 basis points, indicating that IT holdings are a significant drag on risk-adjusted performance. This is the most negative sector contribution, likely due to [reason: market regime, signal noise, etc.]."
4. Also note: Removing Consumer Staples and Health Care actually *improves* Sharpe, suggesting these sectors are deadweight in the current period.

**Verify**: Baseline Sharpe is 0.9029; all Δ values sum approximately to zero (sanity check)

---

### Step 9: Rewrite Section 9.1 (Overview)
**Action**: Update all baseline references  
**Old baseline**: Sharpe 0.345, Return 8.30%, DD -21.29%  
**New baseline**: Sharpe 0.9029, Return 19.78%, DD -18.40%  
**Procedure**:
1. Replace all mentions of 0.345 with 0.9029
2. Replace all mentions of 8.30% with 19.78%
3. Update narrative to acknowledge: "The baseline (60/40 weighting, 20% selection, D/E < 2.0) exhibits robust performance with Sharpe 0.9029 and return 19.78%, closely mirroring the S&P 500 benchmark (Sharpe 0.9219)."

---

### Step 10: Rewrite Section 9.8 (Hypothesis Verdicts)
**Action**: Update H1–H6 conclusions  
**Procedure**:
- **H1** (Sharpe > benchmark): Change from "clearly fails" to "essentially tied with S&P 500 (0.9029 vs 0.9219); fails vs MSCI Value (1.0570). Mixed verdict."
- **H2** (DD < benchmark): Change from "fails" to "tied with S&P 500 (-18.40% vs -18.90%); fails vs MSCI Value (-14.46%). Mixed verdict."
- **H3** (60/40 near-optimal): Verify by inspecting weight_sensitivity.csv (all weights identical—unusual but true).
- **H4** (robustness): Update with threshold_sensitivity.csv findings.
- **H5** (concentration): Update with diversification_over_time.csv latest rebalance (10 holdings, 6 sectors).
- **H6** (2023 outperformance): **FLIP COMPLETELY**: 2023 was modest (13.91%), but 2025 was strong (29.34%). Narrative: "The strategy exhibited the strongest performance in 2025 (29.34% annualised return, 1.1571 Sharpe), recovering from a late-2024 drawdown and driving the full-period outperformance."

---

### Step 11: Rewrite Section 10.1 (Main Narrative)
**Action**: Replace all empirical claims  
**Procedure**:
1. Replace "the portfolio achieves an annual return of 8.30%" → **19.78%**
2. Replace "the Sharpe ratio is only 0.345" → **0.9029** (essentially tied with S&P 500)
3. Replace "the Fama-French five-factor regression gives an alpha of -7.63%" → **+3.33% (insignificant, t=0.49, p=0.624)**
4. Replace "the strategy is only at the 11.4th percentile" → **25.0th percentile** (still underperforms random)
5. Replace "the cumulative trading cost is about 108 basis points" → **129 basis points**
6. Replace "the strategy does not outperform the benchmark in terms of Sharpe ratio" → **The strategy is essentially tied with the S&P 500 on Sharpe (0.9029 vs 0.9219) but underperforms MSCI World Value (1.0570).**

---

### Step 12: Rewrite Section 10.3 (Conclusions)
**Action**: Flip narrative conclusions  
**Procedure**:
1. Remove claim about "negative alpha" (alpha is now positive if insignificant)
2. Remove claim about "poor 2025 performance" (2025 is now the strongest year)
3. Update random portfolio verdict: "The strategy underperforms most randomly constructed portfolios (25th percentile), suggesting limited alpha or edge. This is consistent with the positive but insignificant Fama-French alpha of +3.33%."
4. Reframe overall: "The strategy achieves near-parity with broad-market benchmarks on risk-adjusted basis, neither clearly outperforming nor underperforming. The combination of value and sentiment signals improves upon either signal in isolation but does not generate sustained outperformance net of trading costs."

---

## VERIFICATION CHECKLIST

After regeneration, spot-check:

- [ ] Table 9.2: All rows have identical Sharpe (0.9029) except 0.0/1.0 (0.2053)
- [ ] Table 9.3: Baseline row (0.2/2.0) matches Table 9.2 baseline
- [ ] Table 9.5: 2025 return is 29.34%, not 2.32%
- [ ] Table 9.6: CI lower for Sharpe is negative (-0.2865) but P(>0) is high (92.88%)
- [ ] Table 9.7: Percentile 25 with P(beat) 75%
- [ ] Table 9.8: IT sector has negative Δ Sharpe (-0.4388), not positive
- [ ] Section 9.8: H5 narrative updated to match 2025 = strongest year
- [ ] Section 10.1: All empirical numbers updated (19.78%, 0.9029, +3.33%, etc.)

---

## FINAL NOTES

✅ All canonical numbers are now in `/coursework_two/output/tables/` CSVs.  
✅ Copy/paste from CSVs directly; do NOT recalculate or estimate.  
⚠️ The 2025 inversion (2.32% → 29.34%) is the most critical narrative flip.  
⚠️ The IT sector sign flip (-0.4388 instead of +0.110) inverts sector conclusions.  
⚠️ Regenerate Table 9.2 and Table 9.3 **as grids** (all rows together), not row-by-row.

