"""
Study types and their configurations for medical research papers.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class StudyCategory(Enum):
    EXPERIMENTAL = "Экспериментальные исследования"
    OBSERVATIONAL = "Обсервационные исследования"
    SECONDARY = "Вторичные исследования"
    OTHER = "Другие типы работ"


@dataclass
class StudyType:
    id: str
    name: str
    name_en: str
    category: StudyCategory
    description: str
    sections: List[str]
    requires_sample_size: bool
    typical_endpoints: List[str]
    checklist: str  # CONSORT, STROBE, PRISMA, etc.


STUDY_TYPES: Dict[str, StudyType] = {
    "rct": StudyType(
        id="rct",
        name="Рандомизированное контролируемое исследование (РКИ)",
        name_en="Randomized Controlled Trial",
        category=StudyCategory.EXPERIMENTAL,
        description="Золотой стандарт для оценки эффективности вмешательств",
        sections=[
            "Введение", "Цели и задачи", "Материалы и методы",
            "Результаты", "Обсуждение", "Заключение", "Список литературы"
        ],
        requires_sample_size=True,
        typical_endpoints=[
            "Смертность", "Частота осложнений", "Длительность госпитализации",
            "Качество жизни (SF-36, EQ-5D)", "Время до события", "Уровень боли (ВАШ)",
            "Функциональный статус", "Лабораторные показатели"
        ],
        checklist="CONSORT"
    ),
    "cohort_prospective": StudyType(
        id="cohort_prospective",
        name="Проспективное когортное исследование",
        name_en="Prospective Cohort Study",
        category=StudyCategory.OBSERVATIONAL,
        description="Наблюдение за группами с разным воздействием во времени",
        sections=[
            "Введение", "Цели и задачи", "Материалы и методы",
            "Результаты", "Обсуждение", "Заключение", "Список литературы"
        ],
        requires_sample_size=True,
        typical_endpoints=[
            "Относительный риск (RR)", "Incidence Rate Ratio",
            "Кумулятивная инцидентность", "Время до события",
            "Hazard Ratio", "Выживаемость"
        ],
        checklist="STROBE"
    ),
    "cohort_retrospective": StudyType(
        id="cohort_retrospective",
        name="Ретроспективное когортное исследование",
        name_en="Retrospective Cohort Study",
        category=StudyCategory.OBSERVATIONAL,
        description="Анализ исторических данных когорт",
        sections=[
            "Введение", "Цели и задачи", "Материалы и методы",
            "Результаты", "Обсуждение", "Заключение", "Список литературы"
        ],
        requires_sample_size=False,
        typical_endpoints=[
            "Относительный риск (RR)", "Частота исходов",
            "Факторы риска", "Выживаемость"
        ],
        checklist="STROBE"
    ),
    "case_control": StudyType(
        id="case_control",
        name="Исследование случай-контроль",
        name_en="Case-Control Study",
        category=StudyCategory.OBSERVATIONAL,
        description="Сравнение больных и здоровых по воздействию факторов риска",
        sections=[
            "Введение", "Цели и задачи", "Материалы и методы",
            "Результаты", "Обсуждение", "Заключение", "Список литературы"
        ],
        requires_sample_size=True,
        typical_endpoints=[
            "Отношение шансов (OR)", "Атрибутивный риск",
            "Популяционный атрибутивный риск", "Факторы риска"
        ],
        checklist="STROBE"
    ),
    "cross_sectional": StudyType(
        id="cross_sectional",
        name="Поперечное (одномоментное) исследование",
        name_en="Cross-Sectional Study",
        category=StudyCategory.OBSERVATIONAL,
        description="Оценка распространённости на определённый момент времени",
        sections=[
            "Введение", "Цели и задачи", "Материалы и методы",
            "Результаты", "Обсуждение", "Заключение", "Список литературы"
        ],
        requires_sample_size=True,
        typical_endpoints=[
            "Распространённость", "Превалентность",
            "Отношение превалентностей", "Корреляции"
        ],
        checklist="STROBE"
    ),
    "case_series": StudyType(
        id="case_series",
        name="Серия случаев",
        name_en="Case Series",
        category=StudyCategory.OBSERVATIONAL,
        description="Описание группы пациентов с определённым состоянием",
        sections=[
            "Введение", "Описание случаев", "Обсуждение",
            "Заключение", "Список литературы"
        ],
        requires_sample_size=False,
        typical_endpoints=[
            "Частота симптомов", "Исходы лечения",
            "Характеристики пациентов"
        ],
        checklist="CARE (адаптированный)"
    ),
    "case_report": StudyType(
        id="case_report",
        name="Клинический случай",
        name_en="Case Report",
        category=StudyCategory.OBSERVATIONAL,
        description="Детальное описание одного или нескольких уникальных случаев",
        sections=[
            "Введение", "Описание случая", "Обсуждение",
            "Заключение", "Список литературы"
        ],
        requires_sample_size=False,
        typical_endpoints=[],
        checklist="CARE"
    ),
    "systematic_review": StudyType(
        id="systematic_review",
        name="Систематический обзор",
        name_en="Systematic Review",
        category=StudyCategory.SECONDARY,
        description="Систематический поиск и синтез данных по определённому вопросу",
        sections=[
            "Введение", "Методы поиска", "Критерии включения/исключения",
            "Результаты поиска", "Качество исследований",
            "Синтез данных", "Обсуждение", "Заключение", "Список литературы"
        ],
        requires_sample_size=False,
        typical_endpoints=[
            "Количество включённых исследований",
            "Качество доказательств", "Гетерогенность"
        ],
        checklist="PRISMA"
    ),
    "meta_analysis": StudyType(
        id="meta_analysis",
        name="Мета-анализ",
        name_en="Meta-Analysis",
        category=StudyCategory.SECONDARY,
        description="Статистическое объединение результатов нескольких исследований",
        sections=[
            "Введение", "Методы", "Стратегия поиска",
            "Статистический анализ", "Результаты",
            "Обсуждение", "Заключение", "Список литературы"
        ],
        requires_sample_size=False,
        typical_endpoints=[
            "Суммарный эффект (pooled effect)",
            "Гетерогенность (I², Q)", "Публикационное смещение"
        ],
        checklist="PRISMA"
    ),
    "literature_review": StudyType(
        id="literature_review",
        name="Обзорная статья (нарративный обзор)",
        name_en="Literature Review / Narrative Review",
        category=StudyCategory.SECONDARY,
        description="Обзор и анализ литературы по определённой теме",
        sections=[
            "Введение", "Основная часть (по подтемам)",
            "Обсуждение", "Заключение", "Список литературы"
        ],
        requires_sample_size=False,
        typical_endpoints=[],
        checklist="Нет стандартного"
    ),
    "dissertation_phd": StudyType(
        id="dissertation_phd",
        name="Кандидатская диссертация",
        name_en="PhD Dissertation",
        category=StudyCategory.OTHER,
        description="Квалификационная работа на соискание учёной степени кандидата наук",
        sections=[
            "Введение", "Глава 1: Обзор литературы",
            "Глава 2: Материалы и методы",
            "Глава 3: Результаты собственных исследований",
            "Глава 4: Обсуждение результатов",
            "Заключение", "Выводы", "Практические рекомендации",
            "Список литературы", "Приложения"
        ],
        requires_sample_size=True,
        typical_endpoints=[],
        checklist="Требования ВАК"
    ),
    "dissertation_doctoral": StudyType(
        id="dissertation_doctoral",
        name="Докторская диссертация",
        name_en="Doctoral Dissertation",
        category=StudyCategory.OTHER,
        description="Квалификационная работа на соискание учёной степени доктора наук",
        sections=[
            "Введение", "Глава 1: Обзор литературы",
            "Глава 2: Материалы и методы",
            "Главы 3-5: Результаты исследований",
            "Глава 6: Обсуждение",
            "Заключение", "Выводы", "Практические рекомендации",
            "Список литературы", "Приложения"
        ],
        requires_sample_size=True,
        typical_endpoints=[],
        checklist="Требования ВАК"
    ),
    "diagnostic_accuracy": StudyType(
        id="diagnostic_accuracy",
        name="Исследование диагностической точности",
        name_en="Diagnostic Accuracy Study",
        category=StudyCategory.OBSERVATIONAL,
        description="Оценка чувствительности и специфичности диагностического теста",
        sections=[
            "Введение", "Цели", "Материалы и методы",
            "Результаты", "Обсуждение", "Заключение", "Список литературы"
        ],
        requires_sample_size=True,
        typical_endpoints=[
            "Чувствительность", "Специфичность",
            "ПЦПР (PPV)", "ПЦОР (NPV)",
            "Отношение правдоподобия (+LR, -LR)",
            "AUC-ROC", "Точность (Accuracy)"
        ],
        checklist="STARD"
    ),
    "prognostic": StudyType(
        id="prognostic",
        name="Прогностическое исследование",
        name_en="Prognostic Study",
        category=StudyCategory.OBSERVATIONAL,
        description="Изучение факторов, влияющих на исход заболевания",
        sections=[
            "Введение", "Цели", "Материалы и методы",
            "Результаты", "Обсуждение", "Заключение", "Список литературы"
        ],
        requires_sample_size=True,
        typical_endpoints=[
            "Hazard Ratio", "Выживаемость",
            "C-статистика", "Калибрация модели"
        ],
        checklist="TRIPOD"
    ),
}


def get_study_types_by_category() -> Dict[StudyCategory, List[StudyType]]:
    """Group study types by category."""
    result = {cat: [] for cat in StudyCategory}
    for study_type in STUDY_TYPES.values():
        result[study_type.category].append(study_type)
    return result


def get_study_type(study_id: str) -> Optional[StudyType]:
    """Get study type by ID."""
    return STUDY_TYPES.get(study_id)
