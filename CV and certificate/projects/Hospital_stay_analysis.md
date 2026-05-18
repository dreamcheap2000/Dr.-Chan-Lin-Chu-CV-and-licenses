# Hospital stay clustered-model supplement

> Companion to `Hospital_Stay.md`
> Dataset: `個案34.xlsx` (n = 4,046 complete cases after dropping 19 rows with missing `drsex`)
> Residual detail files: [`Hospital_stay_residuals.md`](./Hospital_stay_residuals.md), [`Hospital_stay_residuals.csv`](./Hospital_stay_residuals.csv)

## 1. Why this supplement was added

`Hospital_Stay.md` already documented the fixed-effects OLS / NB / logit analyses. This supplement adds two cluster-aware sensitivity models requested for the same clinical question:

1. **Random-intercept mixed-effects model** on `log(LOS + 1)`.
2. **Generalized estimating equation (GEE)** with an exchangeable working correlation on `log(LOS + 1)`.

Because the workbook does not contain an explicit physician ID, both models use a **physician proxy cluster** defined as the string concatenation of `round(drage - tenure, 3)`, an underscore, and `drsex`. This approximates a stable physician signature from age-at-start-practice plus physician sex.

- Clusters: **572**
- Mean cluster size: **7.07**
- Median cluster size: **4.5**
- IQR cluster size: **2.0–9.0**
- Maximum cluster size: **68**

## 2. Formulas used

| Item | Formula / specification | Purpose |
| --- | --- | --- |
| Fixed-effects mean structure | `log(LOS+1) ~ age + C(sex) + dis_count + drugcount + adrdrug + drage + C(dep) + tenure + C(drsex) + charlson` | Keeps the same covariates as the primary model in `Hospital_Stay.md`. |
| Mixed-effects model | `y_ij = X_ijβ + u_j + ε_ij`, with `u_j ~ N(0, σ²_u)` and `ε_ij ~ N(0, σ²)` | Adds a physician-proxy random intercept so patients sharing the same proxy cluster can have correlated outcomes. |
| GEE model | `E(y_ij)=X_ijβ`, Gaussian family, identity link, exchangeable working correlation `Corr(y_ij, y_ik)=α` | Estimates population-average effects while allowing within-cluster correlation. |
| Mixed residual | `r_i = y_i - ŷ_i` | Raw model error after fixed + random effects. |
| Mixed standardized residual | `r_i / sqrt(σ²)` | Puts mixed-model residuals on a comparable scale. |
| GEE Pearson residual | `(y_i - μ_i) / sqrt(V(μ_i))` | Standardized residual used for GEE diagnostics. |
| Marginal R² | `Var(Xβ) / [Var(Xβ) + Var(u) + Var(ε)]` | Fixed-effects explanatory power for the mixed model. |
| Conditional R² | `[Var(Xβ) + Var(u)] / [Var(Xβ) + Var(u) + Var(ε)]` | Total explanatory power for the mixed model. |
| Condition index | `sqrt(λ_max / λ_k)` | Detects collinearity in the shared fixed-effects design matrix. |
| Cook distance proxy | OLS Cook's D from the identical fixed-effects design matrix | Used as an influence proxy because `statsmodels` does not expose Cook's D for `MixedLM` or `GEE`. |

## 3. Model-comparison table

| Model | Outcome / link | Cluster structure | N | Clusters | Working parameter | R² / pseudo-R² | AIC / QIC | Residual SD | Min eigenvalue | Max condition index | Cook distance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Random-intercept mixed effects | log(LOS + 1), identity | physician_proxy random intercept | 4046 | 572 | σ²_u = 0.033 | Marginal 0.591; Conditional 0.630 | AIC 7034.0 | 0.975 | 0.0136 | 22.62 | Proxy max 0.932; >4/n = 187 |
| GEE (exchangeable Gaussian) | log(LOS + 1), identity | physician_proxy working correlation | 4046 | 572 | α = 0.066 | Not standard; corr² 0.598 | QIC 4116.2; QICu 4062.0 | 0.582 | 0.0136 | 22.62 | Proxy max 0.932; >4/n = 187 |

### Interpretation of the comparison table

- **Substantive conclusions are stable across models**: `dis_count`, `drugcount`, and department indicators remain the dominant predictors.
- The mixed model's **marginal R² = 0.591** and **conditional R² = 0.630** show that the random intercept adds modest explanatory value beyond the fixed effects.
- The GEE working-correlation estimate **α = 0.066** is small, so within-cluster correlation exists but is not large.
- The design matrix is **moderately** conditioned (**max condition index 22.62**), not severely singular. This is consistent with the original `drugcount`/`adrdrug` and `drage`/`tenure` overlap.
- The largest influence point remains the same extreme long stay seen in the original analysis (**Cook distance proxy 0.932**, source row **3950**).

## 4. Fixed-effect estimates: mixed effects vs GEE

| Term | Mixed β | Mixed SE | Mixed p | %Δ LOS (mixed) | GEE β | GEE SE | GEE p | %Δ LOS (GEE) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Intercept | 1.510 | 0.114 | <0.001 | — | 1.512 | 0.114 | <0.001 | — |
| C(sex)[T.1] | -0.004 | 0.019 | 0.848 | -0.4% | -0.002 | 0.020 | 0.905 | -0.2% |
| C(dep)[T.2] | 0.133 | 0.036 | <0.001 | 14.2% | 0.134 | 0.037 | <0.001 | 14.4% |
| C(dep)[T.3] | -0.158 | 0.049 | 0.001 | -14.6% | -0.156 | 0.053 | 0.003 | -14.4% |
| C(dep)[T.4] | -0.276 | 0.057 | <0.001 | -24.1% | -0.277 | 0.052 | <0.001 | -24.2% |
| C(dep)[T.5] | 0.233 | 0.061 | <0.001 | 26.3% | 0.239 | 0.059 | <0.001 | 27.0% |
| C(dep)[T.6] | 0.175 | 0.061 | 0.004 | 19.1% | 0.166 | 0.062 | 0.007 | 18.1% |
| C(dep)[T.7] | 0.093 | 0.036 | 0.010 | 9.8% | 0.096 | 0.041 | 0.020 | 10.0% |
| C(drsex)[T.1.0] | -0.018 | 0.041 | 0.668 | -1.7% | -0.022 | 0.039 | 0.571 | -2.2% |
| age | -0.001 | 0.001 | 0.076 | -0.1% | -0.001 | 0.001 | 0.088 | -0.1% |
| dis_count | 0.118 | 0.008 | <0.001 | 12.6% | 0.120 | 0.012 | <0.001 | 12.7% |
| drugcount | 0.019 | 0.001 | <0.001 | 1.9% | 0.019 | 0.001 | <0.001 | 1.9% |
| adrdrug | -0.001 | 0.001 | 0.174 | -0.1% | -0.001 | 0.001 | 0.456 | -0.1% |
| drage | 0.004 | 0.004 | 0.270 | 0.4% | 0.004 | 0.004 | 0.303 | 0.4% |
| tenure | -0.007 | 0.004 | 0.079 | -0.7% | -0.006 | 0.004 | 0.125 | -0.6% |
| charlson | -0.015 | 0.005 | 0.001 | -1.5% | -0.015 | 0.005 | 0.004 | -1.5% |

Department legend: `T.2 = 外科`, `T.3 = 兒科`, `T.4 = 感染科`, `T.5 = 婦科`, `T.6 = 腫瘤科`, `T.7 = 其他`.

### Short reading of the coefficient table

- **`dis_count`** stays strongly positive in both models (**mixed β 0.118**, **GEE β 0.120**), roughly **+12.6% to +12.7%** longer LOS per additional comorbidity.
- **`drugcount`** is still the strongest continuous driver (**mixed β 0.019**, **GEE β 0.019**), about **+1.9%** longer LOS per additional drug category.
- Department effects stay directionally stable: **婦科 (`C(dep)[T.5]`)**, **外科 (`C(dep)[T.2]`)**, and **腫瘤科 (`C(dep)[T.6]`)** increase LOS; **兒科 (`C(dep)[T.3]`)** and **感染科 (`C(dep)[T.4]`)** shorten LOS relative to internal medicine.
- **`charlson`** remains negative after adjustment in both clustered models, so the earlier suppression interpretation still applies.
- **`adrdrug`**, **patient sex**, **physician sex**, **physician age**, and **tenure** remain non-significant after clustering is introduced.

## 5. What each parameter / metric does

| Parameter / metric | What it does |
| --- | --- |
| Intercept | Expected log(LOS+1) for the reference patient (female patient, internal medicine, female physician, all numeric predictors at 0). |
| age | Patient age effect; one-year increase shifts expected log(LOS+1) holding other predictors fixed. |
| C(sex)[T.1] | Difference for male vs female patients. |
| dis_count | Change per additional comorbidity count. |
| drugcount | Change per additional drug category prescribed. |
| adrdrug | Change per additional pre-ADR prescription count after total drug burden is already in the model. |
| drage | Physician age effect after accounting for tenure. |
| C(dep)[T.k] | Department effect relative to internal medicine (dep=1). |
| tenure | Physician years in practice effect after accounting for physician age. |
| C(drsex)[T.1.0] | Difference for male vs female physicians. |
| charlson | Charlson comorbidity index effect after other disease-burden terms are controlled. |
| σ²_u (mixed Group Var) | Between-cluster random-intercept variance; larger values mean more physician-level heterogeneity. |
| α (GEE exchangeable) | Working within-cluster correlation; values near 0 indicate weak residual correlation inside clusters. |
| Residual SD / Pearson residual SD | Spread of unexplained model error on the log scale. |
| Marginal / conditional R² | Marginal R² = fixed effects only; conditional R² = fixed + random effects. |
| QIC / QICu | Quasi-likelihood analogues of AIC for GEE; smaller is better among GEE models fit to the same outcome. |
| Eigenvalue / condition index | Global collinearity diagnostics from the fixed-effects design matrix; small eigenvalues and large condition indices imply unstable linear combinations. |
| Cook distance proxy | Observation-level influence from the fixed-effects OLS model with the same design matrix; used because statsmodels does not expose Cook distance for MixedLM or GEE. |

## 6. Practical conclusion

The new clustered analyses **do not overturn the original clinical message**. After allowing patients within the same physician-proxy cluster to be correlated:

1. **Comorbidity burden (`dis_count`)** and **medication complexity (`drugcount`)** remain the most consistent LOS drivers.
2. **Department-level workflow differences** remain clinically important.
3. **Physician-level clustering is present but modest**, so the original fixed-effects conclusions were directionally robust.
4. The main residual problem is still **a very small number of extreme long-stay outliers**, not widespread model instability.

## 7. Important caveat

The cluster variable is a **proxy**, not a true physician identifier. The mixed-effects and GEE results should therefore be interpreted as a **best available sensitivity analysis** rather than a definitive physician-level repeated-measures model. If a true physician ID becomes available, these two models should be rerun with that identifier.
