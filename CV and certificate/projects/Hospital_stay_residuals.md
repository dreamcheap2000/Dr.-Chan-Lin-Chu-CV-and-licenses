# Hospital stay residual details

> Companion to [`Hospital_stay_analysis.md`](./Hospital_stay_analysis.md)
> Row-level export: [`Hospital_stay_residuals.csv`](./Hospital_stay_residuals.csv)

## 1. Residual-distribution summary

| Model | Mean | SD | Q1 | Median | Q3 | Min | Max | Skewness | Kurtosis | |r| > 2 | |r| > 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Mixed model standardized residual | -0.000 | 0.975 | -0.596 | 0.022 | 0.629 | -9.895 | 4.023 | -0.466 | 3.389 | 160 | 15 |
| GEE Pearson residual | 0.007 | 0.582 | -0.351 | 0.012 | 0.392 | -6.031 | 2.320 | -0.459 | 3.452 | 7 | 2 |

### Quick interpretation

- The mixed-model standardized residuals are centered near zero and mostly contained within ±2, but a few extreme negative residuals remain.
- The GEE Pearson residuals tell the same story, which means the remaining misfit is concentrated in the same outlying admissions rather than spread across the full sample.
- Both residual sets are left-tailed because a handful of admissions were predicted to stay even longer than they actually did, creating large negative residuals.

## 2. Largest positive mixed-model residuals

| source_row | los1 | log_los | physician_proxy | cook_d_ols_proxy | mixed_fitted | mixed_resid | mixed_std_resid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3743 | 330 | 5.802 | 25.331_1 | 0.010 | 3.568 | 2.234 | 4.023 |
| 686 | 102 | 4.635 | 26.393_1 | 0.002 | 2.800 | 1.835 | 3.304 |
| 4007 | 46 | 3.850 | 28.287_1 | 0.003 | 2.136 | 1.714 | 3.087 |
| 3900 | 72 | 4.290 | 25.875_1 | 0.002 | 2.596 | 1.695 | 3.052 |
| 1610 | 86 | 4.466 | 28.145_1 | 0.003 | 2.876 | 1.590 | 2.863 |
| 767 | 47 | 3.871 | 25.593_1 | 0.001 | 2.316 | 1.555 | 2.801 |
| 3356 | 24 | 3.219 | 25.506_1 | 0.001 | 1.710 | 1.509 | 2.718 |
| 647 | 55 | 4.025 | 28.241_1 | 0.001 | 2.542 | 1.483 | 2.671 |
| 1562 | 96 | 4.575 | 29.229_1 | 0.002 | 3.095 | 1.480 | 2.665 |
| 3001 | 61 | 4.127 | 25.714_1 | 0.001 | 2.649 | 1.479 | 2.663 |

## 3. Largest negative mixed-model residuals

| source_row | los1 | log_los | physician_proxy | cook_d_ols_proxy | mixed_fitted | mixed_resid | mixed_std_resid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3950 | 1911 | 7.556 | 25.459_1 | 0.932 | 13.050 | -5.495 | -9.895 |
| 3691 | 155 | 5.050 | 28.112_1 | 0.125 | 8.503 | -3.453 | -6.219 |
| 1128 | 667 | 6.504 | 26.82_1 | 0.121 | 9.535 | -3.031 | -5.458 |
| 3706 | 352 | 5.866 | 26.078_1 | 0.072 | 8.680 | -2.814 | -5.067 |
| 2885 | 1 | 0.693 | 26.204_0 | 0.006 | 2.759 | -2.066 | -3.721 |
| 1338 | 1 | 0.693 | 25.402_1 | 0.001 | 2.641 | -1.948 | -3.509 |
| 2282 | 1 | 0.693 | 28.52_1 | 0.002 | 2.518 | -1.825 | -3.286 |
| 1178 | 3 | 1.386 | 25.67_1 | 0.002 | 3.145 | -1.758 | -3.166 |
| 1719 | 1 | 0.693 | 25.76_1 | 0.001 | 2.398 | -1.705 | -3.070 |
| 2002 | 1 | 0.693 | 28.597_1 | 0.001 | 2.396 | -1.703 | -3.066 |

## 4. Largest positive GEE Pearson residuals

| source_row | los1 | log_los | physician_proxy | cook_d_ols_proxy | gee_fitted | gee_resid | gee_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3743 | 330 | 5.802 | 25.331_1 | 0.010 | 3.482 | 2.320 | 2.320 |
| 686 | 102 | 4.635 | 26.393_1 | 0.002 | 2.599 | 2.036 | 2.036 |
| 1562 | 96 | 4.575 | 29.229_1 | 0.002 | 2.764 | 1.811 | 1.811 |
| 3870 | 91 | 4.522 | 28.126_1 | 0.001 | 2.747 | 1.775 | 1.775 |
| 3900 | 72 | 4.290 | 25.875_1 | 0.002 | 2.537 | 1.753 | 1.753 |
| 647 | 55 | 4.025 | 28.241_1 | 0.001 | 2.324 | 1.701 | 1.701 |
| 4007 | 46 | 3.850 | 28.287_1 | 0.003 | 2.157 | 1.693 | 1.693 |
| 1478 | 31 | 3.466 | 38.842_0 | 0.004 | 1.837 | 1.629 | 1.629 |
| 3052 | 30 | 3.434 | 32.12_1 | 0.002 | 1.808 | 1.626 | 1.626 |
| 767 | 47 | 3.871 | 25.593_1 | 0.001 | 2.272 | 1.599 | 1.599 |

## 5. Largest negative GEE Pearson residuals

| source_row | los1 | log_los | physician_proxy | cook_d_ols_proxy | gee_fitted | gee_resid | gee_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3950 | 1911 | 7.556 | 25.459_1 | 0.932 | 13.587 | -6.031 | -6.031 |
| 3691 | 155 | 5.050 | 28.112_1 | 0.125 | 8.708 | -3.658 | -3.658 |
| 1128 | 667 | 6.504 | 26.82_1 | 0.121 | 9.487 | -2.983 | -2.983 |
| 3706 | 352 | 5.866 | 26.078_1 | 0.072 | 8.795 | -2.928 | -2.928 |
| 1338 | 1 | 0.693 | 25.402_1 | 0.001 | 2.700 | -2.007 | -2.007 |
| 2282 | 1 | 0.693 | 28.52_1 | 0.002 | 2.687 | -1.994 | -1.994 |
| 1719 | 1 | 0.693 | 25.76_1 | 0.001 | 2.572 | -1.879 | -1.879 |
| 2885 | 1 | 0.693 | 26.204_0 | 0.006 | 2.559 | -1.866 | -1.866 |
| 2603 | 1 | 0.693 | 25.626_1 | 0.001 | 2.502 | -1.809 | -1.809 |
| 663 | 1 | 0.693 | 25.626_1 | 0.001 | 2.483 | -1.790 | -1.790 |

## 6. Highest influence points (Cook distance proxy)

Threshold used in the original OLS analysis: `4 / n = 0.000989`.

| source_row | los1 | log_los | mixed_std_resid | gee_pearson | cook_d_ols_proxy | physician_proxy |
| --- | --- | --- | --- | --- | --- | --- |
| 3950 | 1911 | 7.556 | -9.895 | -6.031 | 0.932 | 25.459_1 |
| 3691 | 155 | 5.050 | -6.219 | -3.658 | 0.125 | 28.112_1 |
| 1128 | 667 | 6.504 | -5.458 | -2.983 | 0.121 | 26.82_1 |
| 3706 | 352 | 5.866 | -5.067 | -2.928 | 0.072 | 26.078_1 |
| 836 | 188 | 5.242 | -3.020 | -1.717 | 0.016 | 25.462_1 |
| 1687 | 204 | 5.323 | -2.316 | -1.467 | 0.012 | 32.134_1 |
| 2179 | 1 | 0.693 | -2.045 | -1.364 | 0.011 | 27.518_1 |
| 3743 | 330 | 5.802 | 4.023 | 2.320 | 0.010 | 25.331_1 |
| 1412 | 56 | 4.043 | -2.911 | -1.723 | 0.010 | 27.244_1 |
| 3491 | 72 | 4.290 | -2.551 | -1.540 | 0.010 | 26.182_1 |

### Notes

- `source_row` refers to the original Excel row number (header row excluded).
- `cook_d_ols_proxy` comes from the fixed-effects OLS model using the **same** design matrix as the mixed model and GEE. This is a pragmatic influence proxy because `statsmodels` does not provide Cook's distance directly for `MixedLM` or `GEE`.
- Observation **source row 3950** is the dominant influential case in every specification.
- A total of **187** observations exceed the `4/n` Cook-distance proxy threshold; the 95th percentile is **0.0009**.
