"""
Results analysis module - data analysis and visualization.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from scipy import stats
from enum import Enum


class AnalysisType(Enum):
    DESCRIPTIVE = "Описательная статистика"
    COMPARATIVE = "Сравнительный анализ"
    CORRELATION = "Корреляционный анализ"
    REGRESSION = "Регрессионный анализ"
    SURVIVAL = "Анализ выживаемости"
    DIAGNOSTIC = "Диагностический анализ"


@dataclass
class AnalysisResult:
    name: str
    analysis_type: AnalysisType
    description: str
    results: Dict[str, Any]
    interpretation: str
    table_data: Optional[pd.DataFrame] = None
    figure_data: Optional[Dict] = None


class DataAnalyzer:
    """Analyze medical research data."""

    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.results: List[AnalysisResult] = []

    def describe_continuous(
        self,
        column: str,
        group_by: Optional[str] = None,
        check_normality: bool = True
    ) -> AnalysisResult:
        """Describe continuous variable with normality testing."""

        if group_by and group_by in self.data.columns:
            stats_df = self.data.groupby(group_by)[column].agg([
                'count', 'mean', 'std', 'median',
                lambda x: x.quantile(0.25),
                lambda x: x.quantile(0.75),
                'min', 'max'
            ]).round(2)
            stats_df.columns = ['N', 'Среднее', 'СО', 'Медиана', 'Q1', 'Q3', 'Мин', 'Макс']
        else:
            values = self.data[column].dropna()
            stats_dict = {
                'N': len(values),
                'Среднее': values.mean(),
                'СО': values.std(),
                'Медиана': values.median(),
                'Q1': values.quantile(0.25),
                'Q3': values.quantile(0.75),
                'Мин': values.min(),
                'Макс': values.max()
            }
            stats_df = pd.DataFrame([stats_dict]).round(2)

        # Normality test
        normality_result = ""
        if check_normality:
            values = self.data[column].dropna()
            if len(values) >= 3:
                if len(values) <= 50:
                    stat, p_value = stats.shapiro(values)
                    test_name = "Шапиро-Уилка"
                else:
                    stat, p_value = stats.normaltest(values)
                    test_name = "Д'Агостино"

                normality_result = (
                    f"\nПроверка нормальности ({test_name}): "
                    f"статистика = {stat:.3f}, p = {p_value:.4f}. "
                    f"{'Распределение нормальное' if p_value > 0.05 else 'Распределение отличается от нормального'}."
                )

        interpretation = (
            f"Переменная '{column}': среднее значение составило {stats_df['Среднее'].values[0]:.2f} ± "
            f"{stats_df['СО'].values[0]:.2f}, медиана {stats_df['Медиана'].values[0]:.2f} "
            f"[{stats_df['Q1'].values[0]:.2f}; {stats_df['Q3'].values[0]:.2f}].{normality_result}"
        )

        result = AnalysisResult(
            name=f"Описательная статистика: {column}",
            analysis_type=AnalysisType.DESCRIPTIVE,
            description=f"Описательные статистики для переменной {column}",
            results={
                'statistics': stats_df.to_dict(),
                'normality_p': p_value if check_normality else None
            },
            interpretation=interpretation,
            table_data=stats_df
        )

        self.results.append(result)
        return result

    def describe_categorical(
        self,
        column: str,
        group_by: Optional[str] = None
    ) -> AnalysisResult:
        """Describe categorical variable."""

        if group_by and group_by in self.data.columns:
            # Cross-tabulation
            cross_tab = pd.crosstab(
                self.data[column],
                self.data[group_by],
                margins=True,
                margins_name='Всего'
            )

            # Add percentages
            cross_tab_pct = pd.crosstab(
                self.data[column],
                self.data[group_by],
                normalize='columns'
            ) * 100

            stats_df = cross_tab.copy()
            for col in cross_tab.columns[:-1]:
                stats_df[f'{col} (%)'] = cross_tab_pct[col].round(1)

        else:
            counts = self.data[column].value_counts()
            percentages = (self.data[column].value_counts(normalize=True) * 100).round(1)
            stats_df = pd.DataFrame({
                'N': counts,
                '%': percentages
            })

        interpretation = (
            f"Распределение переменной '{column}': "
            + ", ".join([f"{idx}: {row['N']} ({row['%']}%)"
                        for idx, row in stats_df.iterrows()
                        if pd.notna(row.get('N')) and idx != 'Всего'])
        )

        result = AnalysisResult(
            name=f"Частотное распределение: {column}",
            analysis_type=AnalysisType.DESCRIPTIVE,
            description=f"Частотный анализ для переменной {column}",
            results={'frequency_table': stats_df.to_dict()},
            interpretation=interpretation,
            table_data=stats_df
        )

        self.results.append(result)
        return result

    def compare_means(
        self,
        column: str,
        group_column: str,
        paired: bool = False
    ) -> AnalysisResult:
        """Compare means between two groups."""

        groups = self.data[group_column].dropna().unique()
        if len(groups) != 2:
            raise ValueError(f"Expected 2 groups, got {len(groups)}")

        group1_data = self.data[self.data[group_column] == groups[0]][column].dropna()
        group2_data = self.data[self.data[group_column] == groups[1]][column].dropna()

        # Check normality
        _, p1 = stats.shapiro(group1_data) if len(group1_data) <= 50 else stats.normaltest(group1_data)
        _, p2 = stats.shapiro(group2_data) if len(group2_data) <= 50 else stats.normaltest(group2_data)
        is_normal = p1 > 0.05 and p2 > 0.05

        # Choose test
        if paired:
            if is_normal:
                stat, p_value = stats.ttest_rel(group1_data, group2_data)
                test_name = "Парный t-критерий"
            else:
                stat, p_value = stats.wilcoxon(group1_data, group2_data)
                test_name = "Критерий Вилкоксона"
        else:
            if is_normal:
                stat, p_value = stats.ttest_ind(group1_data, group2_data)
                test_name = "t-критерий Стьюдента"
            else:
                stat, p_value = stats.mannwhitneyu(group1_data, group2_data, alternative='two-sided')
                test_name = "Критерий Манна-Уитни"

        # Effect size (Cohen's d)
        pooled_std = np.sqrt(((len(group1_data) - 1) * group1_data.std() ** 2 +
                              (len(group2_data) - 1) * group2_data.std() ** 2) /
                             (len(group1_data) + len(group2_data) - 2))
        cohens_d = (group1_data.mean() - group2_data.mean()) / pooled_std if pooled_std > 0 else 0

        # Summary table
        summary = pd.DataFrame({
            'Группа': groups,
            'N': [len(group1_data), len(group2_data)],
            'Среднее': [group1_data.mean(), group2_data.mean()],
            'СО': [group1_data.std(), group2_data.std()],
            'Медиана': [group1_data.median(), group2_data.median()],
        }).round(2)

        significance = "статистически значимые" if p_value < 0.05 else "статистически незначимые"
        effect_interpretation = (
            "малый" if abs(cohens_d) < 0.5 else
            "средний" if abs(cohens_d) < 0.8 else "большой"
        )

        interpretation = (
            f"Сравнение {column} между группами ({test_name}): "
            f"группа {groups[0]} — {group1_data.mean():.2f} ± {group1_data.std():.2f}, "
            f"группа {groups[1]} — {group2_data.mean():.2f} ± {group2_data.std():.2f}, "
            f"p = {p_value:.4f}. Различия {significance}. "
            f"Размер эффекта (d Коэна) = {cohens_d:.3f} ({effect_interpretation} эффект)."
        )

        result = AnalysisResult(
            name=f"Сравнение средних: {column}",
            analysis_type=AnalysisType.COMPARATIVE,
            description=f"Сравнение {column} между группами {group_column}",
            results={
                'test_name': test_name,
                'statistic': stat,
                'p_value': p_value,
                'cohens_d': cohens_d,
                'is_normal': is_normal,
            },
            interpretation=interpretation,
            table_data=summary
        )

        self.results.append(result)
        return result

    def compare_proportions(
        self,
        column: str,
        group_column: str
    ) -> AnalysisResult:
        """Compare proportions between groups using chi-square or Fisher's exact test."""

        # Create contingency table
        contingency = pd.crosstab(self.data[column], self.data[group_column])

        # Choose test
        expected = stats.contingency.expected_freq(contingency)
        if np.any(expected < 5):
            if contingency.shape == (2, 2):
                odds_ratio, p_value = stats.fisher_exact(contingency)
                test_name = "Точный критерий Фишера"
            else:
                chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
                odds_ratio = None
                test_name = "Хи-квадрат (малые ожидаемые частоты!)"
        else:
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
            test_name = "Хи-квадрат Пирсона"
            odds_ratio = None

            # Calculate OR for 2x2 table
            if contingency.shape == (2, 2):
                a, b = contingency.iloc[0, 0], contingency.iloc[0, 1]
                c, d = contingency.iloc[1, 0], contingency.iloc[1, 1]
                odds_ratio = (a * d) / (b * c) if b * c > 0 else np.inf

        # Calculate confidence interval for OR (2x2 only)
        or_ci = None
        if odds_ratio is not None and contingency.shape == (2, 2) and np.isfinite(odds_ratio):
            a, b = contingency.iloc[0, 0], contingency.iloc[0, 1]
            c, d = contingency.iloc[1, 0], contingency.iloc[1, 1]
            se_log_or = np.sqrt(1/a + 1/b + 1/c + 1/d) if all(x > 0 for x in [a, b, c, d]) else None
            if se_log_or:
                or_ci = (
                    np.exp(np.log(odds_ratio) - 1.96 * se_log_or),
                    np.exp(np.log(odds_ratio) + 1.96 * se_log_or)
                )

        # Summary with percentages
        contingency_pct = pd.crosstab(
            self.data[column],
            self.data[group_column],
            normalize='columns'
        ) * 100

        significance = "статистически значимая" if p_value < 0.05 else "статистически незначимая"

        or_text = ""
        if odds_ratio is not None:
            or_text = f"Отношение шансов = {odds_ratio:.2f}"
            if or_ci:
                or_text += f" (95% ДИ: {or_ci[0]:.2f}-{or_ci[1]:.2f})"
            or_text += ". "

        interpretation = (
            f"Сравнение распределения {column} между группами ({test_name}): "
            f"p = {p_value:.4f}. Связь {significance}. {or_text}"
        )

        result = AnalysisResult(
            name=f"Сравнение пропорций: {column}",
            analysis_type=AnalysisType.COMPARATIVE,
            description=f"Сравнение распределения {column} между группами {group_column}",
            results={
                'test_name': test_name,
                'p_value': p_value,
                'odds_ratio': odds_ratio,
                'or_ci': or_ci,
            },
            interpretation=interpretation,
            table_data=contingency
        )

        self.results.append(result)
        return result

    def correlation_analysis(
        self,
        var1: str,
        var2: str,
        method: str = 'auto'
    ) -> AnalysisResult:
        """Calculate correlation between two variables."""

        x = self.data[var1].dropna()
        y = self.data[var2].dropna()

        # Align data
        common_idx = x.index.intersection(y.index)
        x = x.loc[common_idx]
        y = y.loc[common_idx]

        # Auto-select method
        if method == 'auto':
            _, p1 = stats.shapiro(x) if len(x) <= 50 else stats.normaltest(x)
            _, p2 = stats.shapiro(y) if len(y) <= 50 else stats.normaltest(y)
            method = 'pearson' if (p1 > 0.05 and p2 > 0.05) else 'spearman'

        if method == 'pearson':
            r, p_value = stats.pearsonr(x, y)
            method_name = "Пирсона"
        else:
            r, p_value = stats.spearmanr(x, y)
            method_name = "Спирмена"

        # Interpret correlation strength
        abs_r = abs(r)
        if abs_r < 0.3:
            strength = "слабая"
        elif abs_r < 0.5:
            strength = "умеренная"
        elif abs_r < 0.7:
            strength = "заметная"
        elif abs_r < 0.9:
            strength = "сильная"
        else:
            strength = "очень сильная"

        direction = "положительная" if r > 0 else "отрицательная"
        significance = "статистически значимая" if p_value < 0.05 else "статистически незначимая"

        interpretation = (
            f"Корреляция между {var1} и {var2} (коэффициент {method_name}): "
            f"r = {r:.3f}, p = {p_value:.4f}. "
            f"Выявлена {strength} {direction} {significance} корреляция."
        )

        result = AnalysisResult(
            name=f"Корреляция: {var1} vs {var2}",
            analysis_type=AnalysisType.CORRELATION,
            description=f"Корреляционный анализ между {var1} и {var2}",
            results={
                'method': method_name,
                'correlation': r,
                'p_value': p_value,
                'n': len(x),
            },
            interpretation=interpretation,
            figure_data={'x': var1, 'y': var2, 'type': 'scatter'}
        )

        self.results.append(result)
        return result

    def baseline_table(
        self,
        continuous_vars: List[str],
        categorical_vars: List[str],
        group_column: Optional[str] = None
    ) -> pd.DataFrame:
        """Generate Table 1 (baseline characteristics)."""

        rows = []

        # Continuous variables
        for var in continuous_vars:
            if var not in self.data.columns:
                continue

            if group_column and group_column in self.data.columns:
                groups = self.data[group_column].dropna().unique()
                row = {'Переменная': var}

                for group in groups:
                    group_data = self.data[self.data[group_column] == group][var].dropna()
                    # Check normality
                    _, p_norm = stats.shapiro(group_data) if len(group_data) <= 50 else (0, 0.06)
                    if p_norm > 0.05:
                        row[f'{group}'] = f"{group_data.mean():.1f} ± {group_data.std():.1f}"
                    else:
                        row[f'{group}'] = f"{group_data.median():.1f} [{group_data.quantile(0.25):.1f}; {group_data.quantile(0.75):.1f}]"

                # P-value
                if len(groups) == 2:
                    g1 = self.data[self.data[group_column] == groups[0]][var].dropna()
                    g2 = self.data[self.data[group_column] == groups[1]][var].dropna()
                    _, p = stats.mannwhitneyu(g1, g2, alternative='two-sided')
                    row['p'] = f"{p:.3f}" if p >= 0.001 else "<0.001"
            else:
                values = self.data[var].dropna()
                _, p_norm = stats.shapiro(values) if len(values) <= 50 else (0, 0.06)
                if p_norm > 0.05:
                    row = {'Переменная': var, 'Значение': f"{values.mean():.1f} ± {values.std():.1f}"}
                else:
                    row = {'Переменная': var, 'Значение': f"{values.median():.1f} [{values.quantile(0.25):.1f}; {values.quantile(0.75):.1f}]"}

            rows.append(row)

        # Categorical variables
        for var in categorical_vars:
            if var not in self.data.columns:
                continue

            categories = self.data[var].dropna().unique()

            for cat in categories:
                if group_column and group_column in self.data.columns:
                    groups = self.data[group_column].dropna().unique()
                    row = {'Переменная': f"  {cat}"}

                    for group in groups:
                        group_data = self.data[self.data[group_column] == group]
                        n = (group_data[var] == cat).sum()
                        pct = n / len(group_data) * 100 if len(group_data) > 0 else 0
                        row[f'{group}'] = f"{n} ({pct:.1f}%)"

                    # P-value (chi-square for first category only)
                    if cat == categories[0]:
                        contingency = pd.crosstab(self.data[var], self.data[group_column])
                        _, p, _, _ = stats.chi2_contingency(contingency)
                        row['p'] = f"{p:.3f}" if p >= 0.001 else "<0.001"
                    else:
                        row['p'] = ""
                else:
                    n = (self.data[var] == cat).sum()
                    pct = n / len(self.data) * 100
                    row = {'Переменная': f"  {cat}", 'Значение': f"{n} ({pct:.1f}%)"}

                rows.append(row)

            # Add variable name header
            rows.insert(rows.index(row) - len(categories) + 1, {'Переменная': f"{var}, n (%)"})

        return pd.DataFrame(rows)


def suggest_analyses(data: pd.DataFrame, outcome_var: str, group_var: Optional[str] = None) -> List[Dict]:
    """Suggest appropriate analyses based on data structure."""

    suggestions = []

    # Detect variable types
    outcome_type = "continuous" if data[outcome_var].dtype in ['float64', 'int64'] else "categorical"
    unique_outcomes = data[outcome_var].nunique()

    if outcome_type == "categorical" and unique_outcomes == 2:
        outcome_type = "binary"

    if group_var:
        n_groups = data[group_var].nunique()

        if outcome_type == "continuous":
            if n_groups == 2:
                suggestions.append({
                    "analysis": "compare_means",
                    "description": "Сравнение средних между группами",
                    "recommended_test": "t-критерий или Манна-Уитни",
                    "params": {"column": outcome_var, "group_column": group_var}
                })
            else:
                suggestions.append({
                    "analysis": "anova",
                    "description": "Сравнение средних между несколькими группами",
                    "recommended_test": "ANOVA или Краскела-Уоллиса",
                    "params": {"column": outcome_var, "group_column": group_var}
                })

        elif outcome_type in ["binary", "categorical"]:
            suggestions.append({
                "analysis": "compare_proportions",
                "description": "Сравнение пропорций между группами",
                "recommended_test": "Хи-квадрат или точный критерий Фишера",
                "params": {"column": outcome_var, "group_column": group_var}
            })

    # Always suggest descriptive statistics
    suggestions.insert(0, {
        "analysis": "descriptive",
        "description": "Описательная статистика исхода",
        "recommended_test": "Среднее/медиана, СО/МКР",
        "params": {"column": outcome_var}
    })

    # Suggest baseline table
    suggestions.append({
        "analysis": "baseline_table",
        "description": "Таблица 1: характеристики пациентов",
        "recommended_test": "Описательная статистика с тестами",
        "params": {}
    })

    return suggestions
