"""
Sample size calculation module for various study designs.
"""

import math
from dataclasses import dataclass
from typing import Optional, Dict, Tuple
from enum import Enum
from scipy import stats


class DesignType(Enum):
    TWO_MEANS = "Сравнение двух средних"
    TWO_PROPORTIONS = "Сравнение двух пропорций"
    PAIRED_MEANS = "Парные измерения (средние)"
    ONE_PROPORTION = "Одна пропорция"
    CORRELATION = "Корреляция"
    SURVIVAL = "Анализ выживаемости"
    CASE_CONTROL = "Случай-контроль"
    NONINFERIORITY = "Исследование не меньшей эффективности"
    EQUIVALENCE = "Исследование эквивалентности"
    DIAGNOSTIC = "Диагностическая точность"


@dataclass
class SampleSizeResult:
    n_per_group: int
    n_total: int
    power: float
    alpha: float
    design_type: DesignType
    parameters: Dict
    formula_description: str
    assumptions: str
    recommendation: str


def calculate_two_means(
    mean1: float,
    mean2: float,
    sd: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0,
    two_sided: bool = True
) -> SampleSizeResult:
    """
    Calculate sample size for comparing two independent means.

    Parameters:
    - mean1, mean2: Expected means in each group
    - sd: Common standard deviation (pooled)
    - alpha: Type I error rate
    - power: Statistical power (1 - beta)
    - ratio: Allocation ratio (n2/n1)
    - two_sided: Two-sided test
    """
    effect_size = abs(mean1 - mean2) / sd

    if two_sided:
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)

    z_beta = stats.norm.ppf(power)

    n1 = ((z_alpha + z_beta) ** 2 * (1 + 1 / ratio)) / (effect_size ** 2)
    n1 = math.ceil(n1)
    n2 = math.ceil(n1 * ratio)

    return SampleSizeResult(
        n_per_group=n1,
        n_total=n1 + n2,
        power=power,
        alpha=alpha,
        design_type=DesignType.TWO_MEANS,
        parameters={
            "mean1": mean1,
            "mean2": mean2,
            "sd": sd,
            "effect_size": round(effect_size, 3),
            "ratio": ratio,
        },
        formula_description=(
            f"n = (Zα + Zβ)² × (1 + 1/k) × σ² / δ²\n"
            f"где δ = |μ1 - μ2| = {abs(mean1 - mean2):.2f}, σ = {sd:.2f}, "
            f"Zα = {z_alpha:.3f}, Zβ = {z_beta:.3f}"
        ),
        assumptions=(
            "• Нормальное распределение в обеих группах\n"
            "• Равные дисперсии (гомоскедастичность)\n"
            "• Независимые наблюдения"
        ),
        recommendation=(
            f"Рекомендуемый размер выборки: {n1} в группе 1, {n2} в группе 2.\n"
            f"С учётом возможных выбываний (10-20%), рекомендуется набрать "
            f"{math.ceil(n1 * 1.15)} и {math.ceil(n2 * 1.15)} соответственно."
        ),
    )


def calculate_two_proportions(
    p1: float,
    p2: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0,
    two_sided: bool = True
) -> SampleSizeResult:
    """
    Calculate sample size for comparing two independent proportions.

    Parameters:
    - p1, p2: Expected proportions in each group
    - alpha: Type I error rate
    - power: Statistical power
    - ratio: Allocation ratio (n2/n1)
    - two_sided: Two-sided test
    """
    if two_sided:
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)

    z_beta = stats.norm.ppf(power)

    p_pooled = (p1 + ratio * p2) / (1 + ratio)
    q_pooled = 1 - p_pooled

    numerator = (
        z_alpha * math.sqrt((1 + 1 / ratio) * p_pooled * q_pooled) +
        z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / ratio)
    ) ** 2

    denominator = (p1 - p2) ** 2

    n1 = math.ceil(numerator / denominator)
    n2 = math.ceil(n1 * ratio)

    # Calculate odds ratio and relative risk
    odds_ratio = (p1 / (1 - p1)) / (p2 / (1 - p2)) if p2 < 1 and p1 < 1 else None
    relative_risk = p1 / p2 if p2 > 0 else None

    return SampleSizeResult(
        n_per_group=n1,
        n_total=n1 + n2,
        power=power,
        alpha=alpha,
        design_type=DesignType.TWO_PROPORTIONS,
        parameters={
            "p1": p1,
            "p2": p2,
            "absolute_difference": round(abs(p1 - p2), 3),
            "odds_ratio": round(odds_ratio, 3) if odds_ratio else None,
            "relative_risk": round(relative_risk, 3) if relative_risk else None,
            "ratio": ratio,
        },
        formula_description=(
            f"Формула Fleiss с поправкой на continuity\n"
            f"p1 = {p1:.1%}, p2 = {p2:.1%}, "
            f"абсолютная разница = {abs(p1 - p2):.1%}"
        ),
        assumptions=(
            "• Независимые наблюдения\n"
            "• Бинарный исход\n"
            "• Достаточный размер выборки для нормальной аппроксимации"
        ),
        recommendation=(
            f"Рекомендуемый размер выборки: {n1} в группе 1, {n2} в группе 2.\n"
            f"С учётом выбываний (15%), рекомендуется: "
            f"{math.ceil(n1 * 1.15)} и {math.ceil(n2 * 1.15)}."
        ),
    )


def calculate_case_control(
    p_exposure_cases: float,
    p_exposure_controls: float,
    or_expected: Optional[float] = None,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0
) -> SampleSizeResult:
    """
    Calculate sample size for case-control study.

    Parameters:
    - p_exposure_cases: Proportion of exposure among cases
    - p_exposure_controls: Proportion of exposure among controls
    - or_expected: Expected odds ratio (alternative to p_exposure_cases)
    - alpha: Type I error rate
    - power: Statistical power
    - ratio: Controls per case
    """
    if or_expected and not p_exposure_cases:
        # Calculate p_exposure_cases from OR
        p_exposure_cases = (or_expected * p_exposure_controls) / (
            1 + p_exposure_controls * (or_expected - 1)
        )

    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    p_bar = (p_exposure_cases + ratio * p_exposure_controls) / (1 + ratio)
    q_bar = 1 - p_bar

    n_cases = (
        ((z_alpha * math.sqrt((1 + 1 / ratio) * p_bar * q_bar) +
          z_beta * math.sqrt(p_exposure_cases * (1 - p_exposure_cases) +
                            p_exposure_controls * (1 - p_exposure_controls) / ratio)) ** 2) /
        ((p_exposure_cases - p_exposure_controls) ** 2)
    )

    n_cases = math.ceil(n_cases)
    n_controls = math.ceil(n_cases * ratio)

    actual_or = (p_exposure_cases / (1 - p_exposure_cases)) / (
        p_exposure_controls / (1 - p_exposure_controls)
    )

    return SampleSizeResult(
        n_per_group=n_cases,
        n_total=n_cases + n_controls,
        power=power,
        alpha=alpha,
        design_type=DesignType.CASE_CONTROL,
        parameters={
            "p_exposure_cases": round(p_exposure_cases, 3),
            "p_exposure_controls": round(p_exposure_controls, 3),
            "odds_ratio": round(actual_or, 3),
            "controls_per_case": ratio,
        },
        formula_description=(
            f"Формула Kelsey для исследований случай-контроль\n"
            f"OR = {actual_or:.2f}, экспозиция у случаев = {p_exposure_cases:.1%}, "
            f"у контролей = {p_exposure_controls:.1%}"
        ),
        assumptions=(
            "• Независимый отбор случаев и контролей\n"
            "• Точное определение статуса экспозиции\n"
            "• Репрезентативность контрольной группы"
        ),
        recommendation=(
            f"Требуется {n_cases} случаев и {n_controls} контролей.\n"
            f"С учётом возможного несоответствия критериям (20%): "
            f"{math.ceil(n_cases * 1.2)} случаев, {math.ceil(n_controls * 1.2)} контролей."
        ),
    )


def calculate_survival(
    hazard_ratio: float,
    p_event_control: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0,
    accrual_time: float = 12,
    followup_time: float = 12
) -> SampleSizeResult:
    """
    Calculate sample size for survival analysis (log-rank test).

    Parameters:
    - hazard_ratio: Expected hazard ratio
    - p_event_control: Probability of event in control group by end of study
    - alpha: Type I error rate
    - power: Statistical power
    - ratio: Allocation ratio
    - accrual_time: Recruitment period (months)
    - followup_time: Follow-up after last enrollment (months)
    """
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    # Number of events needed (Schoenfeld formula)
    log_hr = math.log(hazard_ratio)
    d = (4 * (z_alpha + z_beta) ** 2) / (log_hr ** 2)
    d = math.ceil(d)

    # Calculate probability of event in treatment group
    p_event_treatment = 1 - (1 - p_event_control) ** hazard_ratio

    # Average probability of event
    p_event_avg = (p_event_control + ratio * p_event_treatment) / (1 + ratio)

    # Total sample size
    n_total = math.ceil(d / p_event_avg)
    n1 = math.ceil(n_total / (1 + ratio))
    n2 = math.ceil(n1 * ratio)

    return SampleSizeResult(
        n_per_group=n1,
        n_total=n1 + n2,
        power=power,
        alpha=alpha,
        design_type=DesignType.SURVIVAL,
        parameters={
            "hazard_ratio": hazard_ratio,
            "events_needed": d,
            "p_event_control": round(p_event_control, 3),
            "p_event_treatment": round(p_event_treatment, 3),
            "accrual_time": accrual_time,
            "followup_time": followup_time,
        },
        formula_description=(
            f"Формула Schoenfeld для лог-ранк теста\n"
            f"Требуемое число событий d = 4(Zα + Zβ)² / ln(HR)² = {d}\n"
            f"HR = {hazard_ratio}, частота событий в контроле = {p_event_control:.1%}"
        ),
        assumptions=(
            "• Пропорциональные риски (proportional hazards)\n"
            "• Экспоненциальное распределение времени до события\n"
            "• Независимое цензурирование\n"
            "• Равномерный набор пациентов"
        ),
        recommendation=(
            f"Требуется {n1 + n2} пациентов для наблюдения {d} событий.\n"
            f"Период набора: {accrual_time} мес., наблюдение: {followup_time} мес.\n"
            f"С учётом выбываний (15%): {math.ceil((n1 + n2) * 1.15)} пациентов."
        ),
    )


def calculate_diagnostic_accuracy(
    sensitivity: float,
    specificity: float,
    prevalence: float,
    precision: float = 0.05,
    confidence: float = 0.95
) -> SampleSizeResult:
    """
    Calculate sample size for diagnostic accuracy study.

    Parameters:
    - sensitivity: Expected sensitivity
    - specificity: Expected specificity
    - prevalence: Disease prevalence in study population
    - precision: Desired width of confidence interval
    - confidence: Confidence level
    """
    z = stats.norm.ppf(1 - (1 - confidence) / 2)

    # Sample size for sensitivity
    n_diseased = math.ceil(
        (z ** 2 * sensitivity * (1 - sensitivity)) / (precision ** 2)
    )

    # Sample size for specificity
    n_healthy = math.ceil(
        (z ** 2 * specificity * (1 - specificity)) / (precision ** 2)
    )

    # Total sample size accounting for prevalence
    n_total_for_sens = math.ceil(n_diseased / prevalence)
    n_total_for_spec = math.ceil(n_healthy / (1 - prevalence))

    n_total = max(n_total_for_sens, n_total_for_spec)

    return SampleSizeResult(
        n_per_group=n_diseased,  # diseased patients
        n_total=n_total,
        power=confidence,
        alpha=1 - confidence,
        design_type=DesignType.DIAGNOSTIC,
        parameters={
            "sensitivity": sensitivity,
            "specificity": specificity,
            "prevalence": prevalence,
            "precision": precision,
            "n_diseased_needed": n_diseased,
            "n_healthy_needed": n_healthy,
        },
        formula_description=(
            f"Расчёт для оценки чувствительности и специфичности\n"
            f"Чувствительность = {sensitivity:.1%}, специфичность = {specificity:.1%}\n"
            f"Ширина 95% ДИ = ±{precision:.1%}"
        ),
        assumptions=(
            "• Независимая оценка тестом и референсным стандартом\n"
            "• Применение референсного стандарта ко всем пациентам\n"
            "• Репрезентативность выборки"
        ),
        recommendation=(
            f"Требуется минимум {n_diseased} больных и {n_healthy} здоровых.\n"
            f"При распространённости {prevalence:.1%}: всего {n_total} пациентов.\n"
            f"Рекомендуется: {math.ceil(n_total * 1.1)} (запас 10%)."
        ),
    )


def calculate_noninferiority(
    control_response: float,
    margin: float,
    alpha: float = 0.025,  # One-sided
    power: float = 0.80,
    ratio: float = 1.0
) -> SampleSizeResult:
    """
    Calculate sample size for non-inferiority trial.

    Parameters:
    - control_response: Expected response rate in control
    - margin: Non-inferiority margin (absolute)
    - alpha: One-sided Type I error rate
    - power: Statistical power
    - ratio: Allocation ratio
    """
    z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)

    # Assuming treatment is truly equal to control
    p = control_response
    q = 1 - p

    n1 = math.ceil(
        (2 * (z_alpha + z_beta) ** 2 * p * q) / (margin ** 2)
    )
    n2 = math.ceil(n1 * ratio)

    return SampleSizeResult(
        n_per_group=n1,
        n_total=n1 + n2,
        power=power,
        alpha=alpha,
        design_type=DesignType.NONINFERIORITY,
        parameters={
            "control_response": control_response,
            "noninferiority_margin": margin,
            "one_sided_alpha": alpha,
        },
        formula_description=(
            f"Исследование не меньшей эффективности\n"
            f"Эффект контроля = {control_response:.1%}, "
            f"граница не меньшей эффективности = {margin:.1%}\n"
            f"Односторонний α = {alpha}"
        ),
        assumptions=(
            "• Истинный эффект лечения не хуже контроля\n"
            "• Граница не меньшей эффективности клинически обоснована\n"
            "• AACE (активный контроль действительно эффективен)"
        ),
        recommendation=(
            f"Требуется {n1} в группе эксперимента и {n2} в контроле.\n"
            f"С учётом выбываний (15%): {math.ceil(n1 * 1.15)} и {math.ceil(n2 * 1.15)}.\n"
            f"ITT и PP анализы должны быть согласованы."
        ),
    )


# Helper function to select appropriate calculator
def get_sample_size_calculator(design_type: DesignType):
    """Return the appropriate calculator function for the design type."""
    calculators = {
        DesignType.TWO_MEANS: calculate_two_means,
        DesignType.TWO_PROPORTIONS: calculate_two_proportions,
        DesignType.CASE_CONTROL: calculate_case_control,
        DesignType.SURVIVAL: calculate_survival,
        DesignType.DIAGNOSTIC: calculate_diagnostic_accuracy,
        DesignType.NONINFERIORITY: calculate_noninferiority,
    }
    return calculators.get(design_type)


# Common effect sizes reference
EFFECT_SIZE_REFERENCE = {
    "Cohen's d": {
        "small": 0.2,
        "medium": 0.5,
        "large": 0.8,
        "description": "Для сравнения средних: d = (M1 - M2) / SD",
    },
    "Odds Ratio": {
        "small": 1.5,
        "medium": 2.0,
        "large": 3.0,
        "description": "Для бинарных исходов",
    },
    "Hazard Ratio": {
        "small": 0.8,  # or 1.25
        "medium": 0.67,  # or 1.5
        "large": 0.5,  # or 2.0
        "description": "Для выживаемости: HR < 1 = защитный эффект",
    },
    "Correlation (r)": {
        "small": 0.1,
        "medium": 0.3,
        "large": 0.5,
        "description": "Для корреляционного анализа",
    },
}
