"""
Statistical utility functions for medical research.
"""

import numpy as np
from scipy import stats
from typing import Tuple, Optional


def confidence_interval_mean(
    data: np.ndarray,
    confidence: float = 0.95
) -> Tuple[float, float, float]:
    """Calculate confidence interval for mean."""
    n = len(data)
    mean = np.mean(data)
    se = stats.sem(data)
    h = se * stats.t.ppf((1 + confidence) / 2, n - 1)
    return mean, mean - h, mean + h


def confidence_interval_proportion(
    successes: int,
    total: int,
    confidence: float = 0.95,
    method: str = 'wilson'
) -> Tuple[float, float, float]:
    """
    Calculate confidence interval for proportion.

    Methods:
    - 'wilson': Wilson score interval (recommended)
    - 'wald': Normal approximation (simple but less accurate)
    - 'clopper-pearson': Exact binomial (conservative)
    """
    p = successes / total if total > 0 else 0
    z = stats.norm.ppf(1 - (1 - confidence) / 2)

    if method == 'wilson':
        denominator = 1 + z**2 / total
        center = (p + z**2 / (2 * total)) / denominator
        margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator
        return p, center - margin, center + margin

    elif method == 'wald':
        se = np.sqrt(p * (1 - p) / total) if total > 0 else 0
        return p, p - z * se, p + z * se

    elif method == 'clopper-pearson':
        lower = stats.beta.ppf((1 - confidence) / 2, successes, total - successes + 1)
        upper = stats.beta.ppf(1 - (1 - confidence) / 2, successes + 1, total - successes)
        return p, lower, upper

    return p, p, p


def odds_ratio_ci(
    a: int, b: int, c: int, d: int,
    confidence: float = 0.95
) -> Tuple[float, float, float]:
    """
    Calculate odds ratio with confidence interval from 2x2 table.

    Table:
            Outcome+  Outcome-
    Exposed+    a        b
    Exposed-    c        d
    """
    if b * c == 0:
        return np.inf, np.nan, np.nan

    odds_ratio = (a * d) / (b * c)
    log_or = np.log(odds_ratio)

    se_log_or = np.sqrt(1/a + 1/b + 1/c + 1/d) if all(x > 0 for x in [a, b, c, d]) else np.nan

    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    lower = np.exp(log_or - z * se_log_or)
    upper = np.exp(log_or + z * se_log_or)

    return odds_ratio, lower, upper


def relative_risk_ci(
    a: int, b: int, c: int, d: int,
    confidence: float = 0.95
) -> Tuple[float, float, float]:
    """
    Calculate relative risk with confidence interval from 2x2 table.
    """
    n1 = a + b  # Exposed
    n2 = c + d  # Unexposed

    if n1 == 0 or n2 == 0 or a == 0 or c == 0:
        return np.nan, np.nan, np.nan

    p1 = a / n1
    p2 = c / n2
    rr = p1 / p2

    log_rr = np.log(rr)
    se_log_rr = np.sqrt((1 - p1) / (n1 * p1) + (1 - p2) / (n2 * p2))

    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    lower = np.exp(log_rr - z * se_log_rr)
    upper = np.exp(log_rr + z * se_log_rr)

    return rr, lower, upper


def number_needed_to_treat(
    event_rate_treatment: float,
    event_rate_control: float
) -> Tuple[float, str]:
    """
    Calculate Number Needed to Treat (NNT) or Number Needed to Harm (NNH).

    Returns:
    - NNT/NNH value
    - Interpretation string
    """
    arr = event_rate_control - event_rate_treatment  # Absolute Risk Reduction

    if arr == 0:
        return np.inf, "Нет различий между группами"

    nnt = 1 / abs(arr)

    if arr > 0:
        interpretation = f"NNT = {nnt:.1f}: необходимо пролечить {int(np.ceil(nnt))} пациентов для предотвращения 1 исхода"
    else:
        interpretation = f"NNH = {nnt:.1f}: на каждые {int(np.ceil(nnt))} пролеченных пациентов 1 дополнительный исход"

    return nnt, interpretation


def diagnostic_metrics(
    tp: int, fp: int, fn: int, tn: int
) -> dict:
    """
    Calculate diagnostic accuracy metrics from confusion matrix.

    Parameters:
    - tp: True Positives (disease +, test +)
    - fp: False Positives (disease -, test +)
    - fn: False Negatives (disease +, test -)
    - tn: True Negatives (disease -, test -)
    """
    # Basic metrics
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0  # Positive Predictive Value
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0  # Negative Predictive Value
    accuracy = (tp + tn) / (tp + fp + fn + tn) if (tp + fp + fn + tn) > 0 else 0

    # Likelihood ratios
    lr_positive = sensitivity / (1 - specificity) if specificity < 1 else np.inf
    lr_negative = (1 - sensitivity) / specificity if specificity > 0 else np.inf

    # Youden's J statistic
    youden_j = sensitivity + specificity - 1

    # Diagnostic Odds Ratio
    dor = (tp * tn) / (fp * fn) if (fp * fn) > 0 else np.inf

    return {
        'sensitivity': sensitivity,
        'specificity': specificity,
        'ppv': ppv,
        'npv': npv,
        'accuracy': accuracy,
        'lr_positive': lr_positive,
        'lr_negative': lr_negative,
        'youden_j': youden_j,
        'diagnostic_or': dor,
        'sensitivity_ci': confidence_interval_proportion(tp, tp + fn),
        'specificity_ci': confidence_interval_proportion(tn, tn + fp),
    }


def cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Calculate Cohen's d effect size."""
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

    return (np.mean(group1) - np.mean(group2)) / pooled_std if pooled_std > 0 else 0


def interpret_effect_size(d: float, metric: str = 'cohens_d') -> str:
    """Interpret effect size magnitude."""
    abs_d = abs(d)

    if metric == 'cohens_d':
        if abs_d < 0.2:
            return "незначительный"
        elif abs_d < 0.5:
            return "малый"
        elif abs_d < 0.8:
            return "средний"
        else:
            return "большой"

    elif metric == 'correlation':
        if abs_d < 0.1:
            return "незначительная"
        elif abs_d < 0.3:
            return "слабая"
        elif abs_d < 0.5:
            return "умеренная"
        elif abs_d < 0.7:
            return "заметная"
        elif abs_d < 0.9:
            return "сильная"
        else:
            return "очень сильная"

    return "неизвестно"


def multiple_testing_correction(
    p_values: list,
    method: str = 'bonferroni'
) -> list:
    """
    Correct p-values for multiple testing.

    Methods:
    - 'bonferroni': Bonferroni correction (conservative)
    - 'holm': Holm-Bonferroni (step-down)
    - 'fdr': Benjamini-Hochberg FDR
    """
    n = len(p_values)

    if method == 'bonferroni':
        return [min(p * n, 1.0) for p in p_values]

    elif method == 'holm':
        sorted_indices = np.argsort(p_values)
        sorted_pvals = np.array(p_values)[sorted_indices]
        corrected = np.zeros(n)

        for i, p in enumerate(sorted_pvals):
            corrected[sorted_indices[i]] = min(p * (n - i), 1.0)

        return list(corrected)

    elif method == 'fdr':
        sorted_indices = np.argsort(p_values)
        sorted_pvals = np.array(p_values)[sorted_indices]
        corrected = np.zeros(n)

        for i, p in enumerate(sorted_pvals):
            corrected[sorted_indices[i]] = min(p * n / (i + 1), 1.0)

        # Enforce monotonicity
        for i in range(n - 2, -1, -1):
            if corrected[sorted_indices[i]] > corrected[sorted_indices[i + 1]]:
                corrected[sorted_indices[i]] = corrected[sorted_indices[i + 1]]

        return list(corrected)

    return p_values


def power_analysis(
    effect_size: float,
    n: int,
    alpha: float = 0.05,
    test_type: str = 'two_sample_t'
) -> float:
    """
    Calculate statistical power for given parameters.

    Parameters:
    - effect_size: Expected effect size (Cohen's d for t-test)
    - n: Sample size per group
    - alpha: Significance level
    - test_type: Type of test
    """
    if test_type == 'two_sample_t':
        # Non-central t-distribution
        df = 2 * n - 2
        nc = effect_size * np.sqrt(n / 2)  # Non-centrality parameter
        t_crit = stats.t.ppf(1 - alpha / 2, df)
        power = 1 - stats.nct.cdf(t_crit, df, nc) + stats.nct.cdf(-t_crit, df, nc)
        return power

    elif test_type == 'one_sample_t':
        df = n - 1
        nc = effect_size * np.sqrt(n)
        t_crit = stats.t.ppf(1 - alpha / 2, df)
        power = 1 - stats.nct.cdf(t_crit, df, nc) + stats.nct.cdf(-t_crit, df, nc)
        return power

    return 0.0
