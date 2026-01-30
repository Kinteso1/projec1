"""
PICO/PICOS framework for hypothesis formulation.
P - Patient/Population/Problem
I - Intervention
C - Comparison/Control
O - Outcome
S - Study design (optional)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class PICOType(Enum):
    THERAPY = "Терапия/Профилактика"
    DIAGNOSIS = "Диагностика"
    PROGNOSIS = "Прогноз"
    ETIOLOGY = "Этиология/Вред"
    QUALITATIVE = "Качественные исследования"


@dataclass
class PICOQuestion:
    population: str = ""
    intervention: str = ""
    comparison: str = ""
    outcome_primary: str = ""
    outcomes_secondary: List[str] = field(default_factory=list)
    study_design: str = ""
    question_type: Optional[PICOType] = None

    def format_question(self) -> str:
        """Format PICO into a research question."""
        if not all([self.population, self.intervention, self.outcome_primary]):
            return ""

        comparison_part = f" по сравнению с {self.comparison}" if self.comparison else ""

        templates = {
            PICOType.THERAPY: (
                f"Является ли {self.intervention} эффективным{comparison_part} "
                f"для улучшения {self.outcome_primary} у пациентов с {self.population}?"
            ),
            PICOType.DIAGNOSIS: (
                f"Насколько точен {self.intervention}{comparison_part} "
                f"для диагностики {self.outcome_primary} у {self.population}?"
            ),
            PICOType.PROGNOSIS: (
                f"Какова вероятность {self.outcome_primary} "
                f"у пациентов с {self.population} при наличии {self.intervention}?"
            ),
            PICOType.ETIOLOGY: (
                f"Связано ли воздействие {self.intervention} "
                f"с развитием {self.outcome_primary} у {self.population}?"
            ),
            PICOType.QUALITATIVE: (
                f"Каков опыт {self.population} в отношении {self.intervention} "
                f"применительно к {self.outcome_primary}?"
            ),
        }

        if self.question_type and self.question_type in templates:
            return templates[self.question_type]

        return (
            f"Влияет ли {self.intervention}{comparison_part} "
            f"на {self.outcome_primary} у {self.population}?"
        )

    def format_hypothesis(self) -> str:
        """Format PICO into a hypothesis statement."""
        if not all([self.population, self.intervention, self.outcome_primary]):
            return ""

        comparison_part = f" по сравнению с {self.comparison}" if self.comparison else ""

        return (
            f"Гипотеза: Применение {self.intervention} у пациентов с {self.population} "
            f"приводит к улучшению показателей {self.outcome_primary}{comparison_part}."
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "population": self.population,
            "intervention": self.intervention,
            "comparison": self.comparison,
            "outcome_primary": self.outcome_primary,
            "outcomes_secondary": self.outcomes_secondary,
            "study_design": self.study_design,
            "question_type": self.question_type.value if self.question_type else None,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PICOQuestion":
        """Create from dictionary."""
        question_type = None
        if data.get("question_type"):
            for pt in PICOType:
                if pt.value == data["question_type"]:
                    question_type = pt
                    break

        return cls(
            population=data.get("population", ""),
            intervention=data.get("intervention", ""),
            comparison=data.get("comparison", ""),
            outcome_primary=data.get("outcome_primary", ""),
            outcomes_secondary=data.get("outcomes_secondary", []),
            study_design=data.get("study_design", ""),
            question_type=question_type,
        )


# Examples and hints for PICO components
PICO_EXAMPLES = {
    "population": [
        "взрослые пациенты с артериальной гипертензией 1-2 степени",
        "дети 5-12 лет с бронхиальной астмой среднетяжёлого течения",
        "пациенты после инфаркта миокарда в возрасте 45-65 лет",
        "беременные женщины с гестационным сахарным диабетом",
        "пожилые пациенты (>65 лет) с остеоартрозом коленного сустава",
    ],
    "intervention": [
        "телемедицинское наблюдение",
        "когнитивно-поведенческая терапия",
        "лапароскопическая холецистэктомия",
        "ингибиторы SGLT2",
        "программа ранней мобилизации",
    ],
    "comparison": [
        "стандартная терапия",
        "плацебо",
        "открытая операция",
        "отсутствие вмешательства",
        "активный контроль (название препарата)",
    ],
    "outcomes": [
        "уровень систолического артериального давления",
        "частота повторных госпитализаций",
        "качество жизни по опроснику SF-36",
        "30-дневная летальность",
        "время до достижения ремиссии",
    ],
}


PICO_HINTS = {
    "population": """
**Население/Пациенты (P)**
Опишите целевую популяцию максимально конкретно:
- Возраст
- Пол (если релевантно)
- Диагноз/состояние
- Степень тяжести
- Сопутствующие состояния (критерии включения/исключения)
- Условия (стационар, амбулаторно)
""",
    "intervention": """
**Вмешательство (I)**
Опишите изучаемое вмешательство:
- Название препарата/процедуры/метода
- Дозировка/интенсивность
- Длительность применения
- Способ применения
- Кто проводит вмешательство
""",
    "comparison": """
**Сравнение (C)**
Укажите контрольную группу:
- Плацебо
- Стандартная терапия (опишите)
- Другое активное лечение
- Отсутствие вмешательства
- Историческая контрольная группа
""",
    "outcome": """
**Исходы (O)**
Определите измеряемые результаты:
- Первичный исход (основной показатель эффективности)
- Вторичные исходы
- Временные точки измерения
- Способ измерения
- Клинически значимая разница
""",
}


def suggest_outcomes_for_condition(condition: str, intervention: str) -> List[str]:
    """
    Suggest potential outcomes based on condition and intervention.
    This is a basic implementation - in production, this could use AI/ML.
    """
    # Common outcome categories
    common_outcomes = {
        "mortality": ["30-дневная летальность", "Госпитальная летальность", "Общая выживаемость"],
        "morbidity": ["Частота осложнений", "Частота рецидивов", "Частота повторных госпитализаций"],
        "qol": ["Качество жизни (SF-36)", "Качество жизни (EQ-5D)", "Функциональный статус"],
        "symptoms": ["Интенсивность боли (ВАШ)", "Выраженность симптомов", "Частота приступов"],
        "biomarkers": ["Лабораторные показатели", "Уровень маркёров воспаления", "Гликемический контроль (HbA1c)"],
        "resource": ["Длительность госпитализации", "Затраты на лечение", "Количество визитов к врачу"],
        "time": ["Время до события", "Время до ремиссии", "Безрецидивная выживаемость"],
        "functional": ["Функциональный класс", "Толерантность к нагрузке", "Индекс активности"],
    }

    # Keywords mapping to outcome categories
    condition_keywords = {
        "сердечн": ["mortality", "morbidity", "functional", "qol"],
        "онколог": ["mortality", "time", "qol", "morbidity"],
        "диабет": ["biomarkers", "morbidity", "qol"],
        "боль": ["symptoms", "qol", "functional"],
        "инфекц": ["mortality", "morbidity", "biomarkers", "time"],
        "хирург": ["mortality", "morbidity", "resource", "symptoms"],
        "психиат": ["symptoms", "qol", "functional"],
        "неврол": ["functional", "symptoms", "qol"],
    }

    # Find relevant categories
    relevant_categories = set(["qol", "morbidity"])  # Always include these

    condition_lower = condition.lower()
    intervention_lower = intervention.lower()

    for keyword, categories in condition_keywords.items():
        if keyword in condition_lower or keyword in intervention_lower:
            relevant_categories.update(categories)

    # Collect outcomes
    suggested = []
    for cat in relevant_categories:
        suggested.extend(common_outcomes.get(cat, []))

    return list(set(suggested))[:10]  # Return unique outcomes, max 10
