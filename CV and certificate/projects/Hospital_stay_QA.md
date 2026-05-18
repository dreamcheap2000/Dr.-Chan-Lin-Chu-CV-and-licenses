# Hospital Stay Analysis — Statistician Q&A: Challenging Robustness

> **Sources**: `Hospital_Stay.md` (primary fixed-effects analysis) and `Hospital_stay_analysis.md` (clustered-model supplement)  
> **Dataset**: `個案34.xlsx` — 4,046 complete cases (4,065 rows minus 19 missing `drsex`)  
> **Purpose**: A statistician's challenge-and-response session testing the robustness of every major analytical decision.

---

## Part 1 — Data Cleaning & Variable Decisions

---

**Q1. You dropped only 19 rows where `drsex` was missing. Why not impute them? Is complete-case analysis valid here?**

**A1.** The 19 missing `drsex` rows represent ~0.5 % of the sample. Imputing a binary categorical predictor (physician sex) without a principled auxiliary model — when no other variable in the dataset reliably predicts `drsex` — would introduce systematic error rather than reduce it. Under the missing-completely-at-random (MCAR) assumption, complete-case analysis is unbiased. Even under missing-at-random (MAR), the negligible proportion (0.5 %) means any imputation bias on estimates would be smaller than rounding error. The decision therefore favours simplicity without material cost.

---

**Q2. Why was `log(LOS + 1)` chosen as the outcome instead of a Box-Cox optimal transformation or the raw count itself?**

**A2.** Three reasons support `log(LOS + 1)` specifically:

1. **Interpretability**: Log-coefficients translate directly to percentage changes in LOS via `(e^β − 1) × 100`, a clinically meaningful scale.  
2. **The "+1" offset**: LOS values of 1 day are common; `log(0)` is undefined, making the raw log impossible. A +1 shift on a 1–1,911 day scale is negligible.  
3. **Box-Cox alternatives**: A Box-Cox search would optimize residual normality for the given sample, but the chosen transformation parameter would be dataset-specific and harder to reproduce or interpret. The log transformation is a principled, pre-specified choice standard in health-services research — it was not selected by inspecting the data.  

The transformation was validated post-hoc: residuals from the log-OLS model are far more symmetric than from raw-LOS OLS, and the Negative Binomial model (no transformation needed) reaches the same predictor conclusions.

---

**Q3. The binary long-stay threshold was set at P75 (≥ 19 days). Is this arbitrary? Would results change with P90 or a clinical threshold?**

**A3.** Any threshold for a binary long-stay outcome involves some arbitrariness. P75 was chosen because it is a conventional epidemiological definition (top quartile), pre-specified before modelling, and produces a roughly balanced case-to-control ratio (25 % cases), which favours logistic model stability. Using P90 would concentrate extreme stays, potentially diluting department effects. Using a clinical threshold (e.g., >30 days) would depend on local policy. The critical robustness check is that the logistic findings are already corroborated by the continuous-outcome log-OLS and Negative Binomial models, so the binary analysis is confirmatory, not primary. Sensitivity analyses at alternative thresholds were not reported but remain a valid future extension.

---

**Q4. `adrdrug` and the derived `adr_event` / `post_adr_drug` encode the same raw information. Isn't it double-counting or data dredging to test both codings in the same dataset?**

**A4.** The two codings answer different scientific questions and were not both retained in the final primary model. `adrdrug` (continuous count) tests whether the *number* of drugs before an ADR event independently predicts LOS. `adr_event` (binary) tests whether the *occurrence* of an ADR event per se predicts LOS. The sensitivity model using `adr_event + post_adr_drug` was pre-motivated by domain reasoning: the PDF reference document hypothesises that the event itself — not just drug burden — extends stays. Running both as separate sensitivity models (not combined) is not data dredging; it is hypothesis-driven re-coding. The primary model retained `adrdrug` to match the original study design; the re-coded model is clearly labelled a sensitivity check.

---

## Part 2 — Correlation and Collinearity

---

**Q5. `adrdrug` and `drugcount` have Spearman ρ = 0.873. VIF values are below 10, but isn't that threshold too permissive? Could the collinearity still bias individual coefficients?**

**A5.** VIF < 10 is a conventional rule-of-thumb, not a hard statistical boundary. With VIFs of 4.20 (`adrdrug`) and 4.28 (`drugcount`), the standard error inflation factor is approximately √4.28 ≈ 2.07 — meaning SEs are roughly doubled relative to an orthogonal design. However:

- The collinearity makes `adrdrug` *individually* imprecise, but it does not bias the *combined* joint prediction of `adrdrug + drugcount`.  
- The primary clinical conclusion focuses on `drugcount`, which remains highly significant (t = 32.88, p < 0.001) despite the moderate VIF.  
- The condition index analysis (max 22.62) classifies the design matrix as "moderately conditioned" — below the ≥ 30 threshold typically cited for severe instability (Belsley 1980).  
- The `adrdrug` re-coding sensitivity analysis disentangles the two variables, confirming that the main drug-burden signal is attributable to `drugcount`, not the ADR-count component.

---

**Q6. The Pearson and Spearman correlations between `dis_count` and LOS diverge substantially (r = 0.21 vs. ρ = 0.47). Did you test for non-linearity in `dis_count` before entering it as a linear term?**

**A6.** The univariate descriptive table shows a clear monotonic dose-response (mean LOS: 6.7, 7.7, 9.6, 13.1, 27.0 days for dis_count = 0–4), but the jumps are unequal — the 3→4 jump is by far the largest. This non-linearity is partially absorbed by the log transformation of the outcome: on the log scale, the relationship is closer to linear. The primary model enters `dis_count` linearly, which gives an average marginal effect; this is conservative in the sense that the model slightly underestimates the impact at the high end. A piecewise linear or polynomial specification, or treating `dis_count` as a 5-level factor, would be a valid extension. The sign and significance of `dis_count` would not change; the magnitude estimate would be redistributed across segments.

---

## Part 3 — Residual Diagnostics

---

**Q7. The Shapiro–Wilk test rejects normality (p ≈ 7.6 × 10⁻²²) and Breusch–Pagan rejects homoscedasticity (p ≈ 7.2 × 10⁻¹²³). Why is the OLS log model still called the "primary" model if its assumptions are violated?**

**A7.** At n = 4,046, both Shapiro–Wilk and Breusch–Pagan are virtually guaranteed to detect any departure from the null hypothesis, no matter how small — this is the well-known problem of overpowered omnibus tests. The practical severity of the violations matters more than the p-value:

- **Normality**: OLS coefficient estimates are unbiased regardless of residual distribution. Normality matters only for finite-sample inference. With n > 4,000, the Central Limit Theorem makes the t/F statistics approximately valid even with non-normal residuals.  
- **Heteroscedasticity**: OLS estimates remain unbiased but SEs are inefficient. This was directly corrected by the HC3 heteroscedasticity-consistent SE model (Step 5B-hc3), which produced negligibly different SEs and identical significance patterns. The HC3 result *is* the validation that heteroscedasticity does not change conclusions.  
- **Corroboration**: The Negative Binomial GLM (which makes no normality or homoscedasticity assumption) reaches the same conclusions, providing a fully assumption-free cross-check.

---

**Q8. Cook's distance proxy > 4/n flags 187 observations (4.6 %). One point has Cook's D = 0.932 — the patient with LOS = 1,911 days. Why was this extreme outlier not removed?**

**A8.** Removing an observation because it is influential is defensible only if there is evidence of a *recording error* or if it falls outside the inferential target population. LOS = 1,911 days is extreme but not biologically impossible (e.g., ventilator-dependent patients, severe disability). Removing it would:

1. Optimistically bias R² and improve model diagnostics artificially.  
2. Mean the model no longer applies to complex long-stay cases — the clinically most important subgroup.  

The principled remediation is the P99-trim sensitivity analysis (Step 9a), which excludes all LOS > 113.6 days (n = 4,005). Every key predictor remained significant in the same direction, confirming that the single extreme outlier does not drive the primary findings. The outlier is therefore retained in the primary model with transparency about its influence.

---

## Part 4 — Model Selection

---

**Q9. You compared OLS, NB, and Logistic models. How do you decide which is "primary" when they differ slightly (e.g., `charlson` is significant in log-OLS but not in NB or Logit)?**

**A9.** The primary model selection criterion is alignment between the *research question*, the *outcome scale*, and the *distributional assumptions*:

- **Log-OLS** is primary because it answers the main continuous-LOS question on an interpretable log scale and achieves the best normality approximation after transformation.  
- **NB GLM** addresses count-data overdispersion without a transformation assumption; it is the best model for raw LOS as a count variable.  
- **Logistic** addresses a binary clinical decision (long stay vs. not).  

`Charlson` shows marginal significance in log-OLS (p = 0.001) but weaker signals in NB (p = 0.071) and non-significance in logistic. This pattern is the expected consequence of suppression interacting with model-specific link functions and outcome scales. The key insight — that `charlson` has a *suppressor* relationship with `dis_count` and `drugcount` — is consistent across all three models: the unadjusted correlation is positive (+0.169) while the adjusted coefficient is negative or near-zero in all models. The magnitude of the suppression effect simply varies by model. The overall substantive conclusion (`dis_count` and `drugcount` dominate; `charlson` has a suppressed adjusted effect) is stable across all models.

---

**Q10. AIC values are compared across models (e.g., log-OLS AIC = 7,126 vs. NB AIC = 28,342). Isn't this comparison invalid because the models use different outcome variables?**

**A10.** This is correct — AIC is comparable only across models with the *same* outcome variable and likelihood function. The document acknowledges this explicitly: "NB AIC = 28,342 (much lower than OLS-raw AIC = 37,785 for same outcome; **not comparable** to log-OLS AIC = 7,126 which uses a different DV scale)." AIC is therefore used within model families (e.g., comparing base log-OLS to the interaction models on the same log(LOS+1) outcome), not across the OLS-log vs. NB boundary.

---

**Q11. Interaction terms (drugcount × charlson, dep × charlson) were tested and the ΔAIC was small (< 3). Why not retain marginally significant interactions?**

**A11.** ΔAIC < 3 is below the conventional threshold of meaningful model improvement (Burnham & Anderson suggest ΔAIC < 2 indicates essentially equivalent models, and < 6 indicates weak evidence). The specific interaction effects are also tiny in absolute magnitude — the drugcount × charlson coefficient adds a negligible percentage to predicted LOS in the observed data range. More importantly, retaining a marginal interaction reduces model interpretability, increases the risk of overfitting to this sample, and makes the model harder to apply clinically. A parsimonious additive model that explains 59.9 % of variance is preferred over a marginally more complex model with fractionally better AIC fit unless the interaction has a clear mechanistic justification. These interactions remain as pre-specified hypotheses for future larger studies with condition-specific strata.

---

## Part 5 — Physician Clustering (Hospital_stay_analysis.md)

---

**Q12. The physician proxy cluster is constructed from `round(drage − tenure, 3)` concatenated with `drsex`. How reliable is this as a physician identifier? Could the same physician appear in multiple clusters?**

**A12.** The proxy is explicitly described as a heuristic, not a validated identifier. `drage − tenure` approximates a physician's implied entry age into practice. Rounding to 3 decimal places reduces (but does not eliminate) floating-point collisions. The same physician could theoretically appear in two clusters if their recorded age or tenure fluctuates by rounding artefact across admissions. Conversely, different physicians with identical implied entry ages and the same sex will share a cluster. The document is transparent about this caveat (Section 7 of `Hospital_stay_analysis.md`): "the cluster variable is a proxy, not a true physician identifier … results should be interpreted as a best available sensitivity analysis rather than a definitive physician-level repeated-measures model." Given these limitations, the cluster-aware models serve as a robustness check only — they are not used to draw conclusions about physician-level effects specifically.

---

**Q13. The GEE working-correlation estimate is α = 0.066. Does this mean physician-level clustering is negligible and the original fixed-effects standard errors are approximately correct?**

**A13.** An exchangeable working correlation of α = 0.066 is small but non-negligible. In practical terms, it means that knowing one patient in a physician-proxy cluster has an unusually long stay predicts a small increase in expected stay for the next patient in that cluster. The design effect (DEFF) from this clustering is approximately `1 + (m̄ − 1) × α = 1 + (7.07 − 1) × 0.066 ≈ 1.40`, implying effective sample sizes about 28 % smaller than n = 4,046. The original OLS SEs were therefore modestly underestimated. However, the fixed-effect estimates themselves are almost identical between OLS, mixed, and GEE (see the coefficient table in Section 4 of the supplement), and all key predictors retain significance under clustering. The conclusion is that the OLS SEs were slightly anti-conservative but not materially so — the primary findings are directionally robust.

---

**Q14. The mixed-effects model uses marginal R² = 0.591 and conditional R² = 0.630. The random intercept adds only 0.039 in R². Does physician-level heterogeneity really matter clinically?**

**A14.** The random-intercept variance σ²_u = 0.033 vs. residual variance σ² ≈ 0.951 gives an intraclass correlation (ICC) of approximately 0.033 / (0.033 + 0.951) ≈ 0.034. An ICC of 3.4 % is small — most LOS variance is explained by patient-level factors, not physician clustering. The conditional R² improvement of +0.039 over the marginal R² is consistent with this small ICC. Clinically, this suggests that the dominant levers for LOS reduction are patient comorbidity management and department-level protocols, not physician assignment per se. However, a 3.4 % ICC still means that approximately 1 in 30 units of unexplained LOS variance is attributable to which physician-proxy cluster a patient falls into — this is not zero, and a true physician ID would be needed to determine whether this represents a genuine physician effect or proxy construction artefact.

---

**Q15. Cook's distance for the mixed and GEE models is computed via an OLS proxy on the same design matrix. Why is this acceptable, and what are the risks?**

**A15.** `statsmodels` does not expose Cook's distance diagnostics for `MixedLM` or `GEE` objects. Using an OLS proxy on the identical fixed-effects design matrix is the standard workaround in applied practice when likelihood-based Cook's distance is unavailable. The proxy is acceptable because:

1. The fixed-effects estimates are nearly identical across OLS, mixed, and GEE (as confirmed by the coefficient table), so the leverage and residual structure driving Cook's D is similar.  
2. The primary purpose is *screening* — identifying which observations deserve close examination — not computing a precise influence statistic.  

The risk is that the proxy ignores the variance-covariance structure induced by clustering (random effects or working correlation matrix), so it may slightly overstate influence for patients in large clusters and understate it for patients in small clusters. The extreme outlier (row 3950, LOS = 1,911 days) has Cook's D proxy = 0.932 and would be flagged as influential by any reasonable influence measure.

---

## Part 6 — Generalisability and Causal Inference

---

**Q16. All models are regression-based associations. Can you claim causal inference from these findings?**

**A16.** No causal claim is made. The analysis is observational and cross-sectional. Even with robust multi-model triangulation, unmeasured confounders (primary diagnosis, procedure complexity, bed availability, nursing ratios, patient preference) could explain or modify any association. The language throughout the document uses "predicts" and "is associated with" rather than "causes." The findings generate actionable hypotheses for intervention (e.g., polypharmacy review, early discharge planning for high-comorbidity patients, ADR detection protocols), but causal verification would require a prospective study, natural experiment, or randomised evaluation.

---

**Q17. The dataset covers patients from a single medical centre. How generalisable are these findings?**

**A17.** Single-centre observational data limits external validity in several ways:

- Department definitions, staffing ratios, bed capacity, and case mix may differ substantially between hospitals.  
- The hospital's formulary and ADR reporting culture affect `drugcount` and `adrdrug` values.  
- Case selection (elective vs. emergency admissions, referral patterns) may not represent population-level hospital use.  

The findings on `dis_count` and `drugcount` as LOS drivers are consistent with multi-centre literature, lending face validity. Department-specific effects are likely institution-specific and should not be transferred directly. Future replication across multiple centres or using national discharge data would address generalisability.

---

**Q18. The Charlson comorbidity index is negatively associated with LOS after adjustment. If a clinician uses this model, might they incorrectly infer that sicker patients (higher Charlson) can be discharged sooner?**

**A18.** This is a critical clinical misinterpretation risk. The negative adjusted coefficient for Charlson is a *statistical artefact* of suppression by `dis_count` and `drugcount`, not a causal relationship. In crude (unadjusted) analysis, Charlson positively correlates with LOS (ρ = +0.169). The adjusted sign reversal occurs because, after controlling for comorbidity count and drug complexity, the *residual variance* of Charlson is associated with care efficiency — likely reflecting that high-Charlson patients are admitted under structured pathways. The model should **never** be used to justify early discharge for high-Charlson patients. Appropriate clinical application is: given a patient's comorbidity count and medication complexity, the model predicts expected LOS for planning purposes. The Charlson term is retained in the model for statistical adjustment, not for clinical decision-making on its own.

---

## Part 7 — Summary of Robustness Verdict

| Challenge area | Key concern raised | Verdict |
|---|---|---|
| Missing data | 19 dropped rows; MCAR not tested | Low risk; 0.5 % loss, no imputation assumptions needed |
| Log transformation | Pre-specified vs. optimal; +1 offset | Principled; NB model (no transformation) corroborates |
| Long-stay threshold | Arbitrary P75 cutoff | Confirmed by continuous models; sensitivity analysis feasible |
| adrdrug coding | Collinear with drugcount; continuous vs. binary | Addressed by re-coding sensitivity; main conclusions unchanged |
| Collinearity | VIF < 10 but ρ = 0.87 for drug pair | SE inflation ~2×; drugcount conclusion unaffected |
| Residual normality | Shapiro–Wilk rejects | Overpowered test; CLT applies; HC3 and NB corroborate |
| Heteroscedasticity | Breusch–Pagan highly significant | HC3 correction applied; no change to significance |
| Influential points | 4.6 % > Cook threshold; one extreme outlier | P99-trim sensitivity confirms stability |
| AIC cross-model | Different DV scales compared | Document explicitly flags; within-family AIC only used |
| Marginal interactions | Tested post-hoc | ΔAIC < 3; not retained; valid future study question |
| Physician cluster proxy | Imprecise identifier | Acknowledged caveat; cluster results are sensitivity only |
| Low ICC (3.4 %) | Clustering may be negligible | Fixed-effects SEs modestly anti-conservative; estimates stable |
| Cook's D proxy | Mixed/GEE influence approximated | Standard workaround; directionally valid for outlier screening |
| Causality | Observational design | No causal claims made; hypotheses only |
| Single centre | Limited generalisability | Consistent with literature; multi-centre replication recommended |
| Charlson sign reversal | Clinical misuse risk | Clearly explained as suppression; clinical caveat documented |

---

*Document prepared as a companion to `Hospital_Stay.md` and `Hospital_stay_analysis.md`.*  
*Analyst: Dr. Chan-Lin Chu.*
