"""
Primary and secondary endpoints management.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class EndpointType(Enum):
    CONTINUOUS = "Непрерывная переменная"
    BINARY = "Бинарная переменная"
    CATEGORICAL = "Категориальная переменная"
    TIME_TO_EVENT = "Время до события"
    COUNT = "Счётная переменная"
    ORDINAL = "Порядковая переменная"


class EndpointCategory(Enum):
    EFFICACY = "Эффективность"
    SAFETY = "Безопасность"
    TOLERABILITY = "Переносимость"
    QUALITY_OF_LIFE = "Качество жизни"
    BIOMARKER = "Биомаркер"
    ECONOMIC = "Экономические показатели"
    COMPOSITE = "Комбинированная конечная точка"


@dataclass
class Endpoint:
    name: str
    description: str
    endpoint_type: EndpointType
    category: EndpointCategory
    measurement_method: str = ""
    measurement_time: str = ""
    clinically_significant_difference: Optional[float] = None
    unit: str = ""
    is_primary: bool = False
    statistical_test: str = ""

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "endpoint_type": self.endpoint_type.value,
            "category": self.category.value,
            "measurement_method": self.measurement_method,
            "measurement_time": self.measurement_time,
            "clinically_significant_difference": self.clinically_significant_difference,
            "unit": self.unit,
            "is_primary": self.is_primary,
            "statistical_test": self.statistical_test,
        }


# Suggested statistical tests for each endpoint type
STATISTICAL_TESTS = {
    EndpointType.CONTINUOUS: [
        ("t-критерий Стьюдента", "Для двух независимых групп при нормальном распределении"),
        ("Критерий Манна-Уитни", "Для двух независимых групп при ненормальном распределении"),
        ("Парный t-критерий", "Для связанных выборок при нормальном распределении"),
        ("Критерий Вилкоксона", "Для связанных выборок при ненормальном распределении"),
        ("ANOVA", "Для трёх и более групп"),
        ("Критерий Краскела-Уоллиса", "Для трёх и более групп при ненормальном распределении"),
        ("ANCOVA", "При необходимости коррекции на ковариаты"),
        ("Смешанные модели (Mixed models)", "Для повторных измерений"),
    ],
    EndpointType.BINARY: [
        ("Хи-квадрат Пирсона", "Для сравнения пропорций"),
        ("Точный критерий Фишера", "При малых выборках"),
        ("Логистическая регрессия", "Для оценки OR с коррекцией на ковариаты"),
        ("Критерий МакНемара", "Для связанных бинарных данных"),
    ],
    EndpointType.CATEGORICAL: [
        ("Хи-квадрат Пирсона", "Для таблиц сопряжённости"),
        ("Точный критерий Фишера", "При малых ожидаемых частотах"),
        ("Критерий хи-квадрат для тренда", "Для упорядоченных категорий"),
    ],
    EndpointType.TIME_TO_EVENT: [
        ("Лог-ранк тест", "Для сравнения кривых выживаемости"),
        ("Регрессия Кокса", "Для оценки HR с ковариатами"),
        ("Метод Каплана-Мейера", "Для построения кривых выживаемости"),
        ("Критерий Гехана-Вилкоксона", "При непропорциональных рисках"),
    ],
    EndpointType.COUNT: [
        ("Пуассоновская регрессия", "Для счётных данных"),
        ("Отрицательная биномиальная регрессия", "При избыточной дисперсии"),
        ("Zero-inflated модели", "При избытке нулей"),
    ],
    EndpointType.ORDINAL: [
        ("Критерий Манна-Уитни", "Для двух групп"),
        ("Критерий Джонкхира-Терпстра", "Для трёх и более упорядоченных групп"),
        ("Ординальная логистическая регрессия", "Для оценки с ковариатами"),
    ],
}


# Common endpoints by medical specialty
SPECIALTY_ENDPOINTS = {
    "кардиология": [
        Endpoint(
            name="MACE (Major Adverse Cardiovascular Events)",
            description="Комбинированная точка: сердечно-сосудистая смерть, нефатальный ИМ, нефатальный инсульт",
            endpoint_type=EndpointType.TIME_TO_EVENT,
            category=EndpointCategory.COMPOSITE,
            statistical_test="Регрессия Кокса"
        ),
        Endpoint(
            name="Фракция выброса ЛЖ",
            description="Систолическая функция левого желудочка по ЭхоКГ",
            endpoint_type=EndpointType.CONTINUOUS,
            category=EndpointCategory.EFFICACY,
            unit="%",
            statistical_test="ANCOVA"
        ),
        Endpoint(
            name="NT-proBNP",
            description="Уровень N-терминального промозгового натрийуретического пептида",
            endpoint_type=EndpointType.CONTINUOUS,
            category=EndpointCategory.BIOMARKER,
            unit="пг/мл",
            statistical_test="Критерий Манна-Уитни"
        ),
    ],
    "онкология": [
        Endpoint(
            name="Общая выживаемость (OS)",
            description="Время от рандомизации до смерти от любой причины",
            endpoint_type=EndpointType.TIME_TO_EVENT,
            category=EndpointCategory.EFFICACY,
            statistical_test="Регрессия Кокса"
        ),
        Endpoint(
            name="Выживаемость без прогрессирования (PFS)",
            description="Время от рандомизации до прогрессирования или смерти",
            endpoint_type=EndpointType.TIME_TO_EVENT,
            category=EndpointCategory.EFFICACY,
            statistical_test="Регрессия Кокса"
        ),
        Endpoint(
            name="Частота объективного ответа (ORR)",
            description="Доля пациентов с полным или частичным ответом по RECIST",
            endpoint_type=EndpointType.BINARY,
            category=EndpointCategory.EFFICACY,
            statistical_test="Логистическая регрессия"
        ),
    ],
    "эндокринология": [
        Endpoint(
            name="HbA1c",
            description="Уровень гликированного гемоглобина",
            endpoint_type=EndpointType.CONTINUOUS,
            category=EndpointCategory.BIOMARKER,
            unit="%",
            clinically_significant_difference=0.5,
            statistical_test="ANCOVA"
        ),
        Endpoint(
            name="Гипогликемии",
            description="Частота эпизодов гипогликемии",
            endpoint_type=EndpointType.COUNT,
            category=EndpointCategory.SAFETY,
            statistical_test="Отрицательная биномиальная регрессия"
        ),
    ],
    "неврология": [
        Endpoint(
            name="Шкала NIHSS",
            description="Тяжесть инсульта по шкале NIHSS",
            endpoint_type=EndpointType.ORDINAL,
            category=EndpointCategory.EFFICACY,
            statistical_test="Критерий Манна-Уитни"
        ),
        Endpoint(
            name="Модифицированная шкала Рэнкина (mRS)",
            description="Функциональный исход после инсульта",
            endpoint_type=EndpointType.ORDINAL,
            category=EndpointCategory.EFFICACY,
            statistical_test="Ординальная логистическая регрессия"
        ),
    ],
    "ревматология": [
        Endpoint(
            name="ACR20/50/70",
            description="Критерии ответа Американской коллегии ревматологов",
            endpoint_type=EndpointType.BINARY,
            category=EndpointCategory.EFFICACY,
            statistical_test="Логистическая регрессия"
        ),
        Endpoint(
            name="DAS28",
            description="Индекс активности ревматоидного артрита",
            endpoint_type=EndpointType.CONTINUOUS,
            category=EndpointCategory.EFFICACY,
            statistical_test="ANCOVA"
        ),
    ],
    "хирургия": [
        Endpoint(
            name="Частота осложнений по Clavien-Dindo",
            description="Классификация хирургических осложнений",
            endpoint_type=EndpointType.ORDINAL,
            category=EndpointCategory.SAFETY,
            statistical_test="Критерий Манна-Уитни"
        ),
        Endpoint(
            name="Длительность операции",
            description="Время от разреза до ушивания",
            endpoint_type=EndpointType.CONTINUOUS,
            category=EndpointCategory.EFFICACY,
            unit="минуты",
            statistical_test="Критерий Манна-Уитни"
        ),
        Endpoint(
            name="Длительность госпитализации",
            description="Время от госпитализации до выписки",
            endpoint_type=EndpointType.CONTINUOUS,
            category=EndpointCategory.ECONOMIC,
            unit="дни",
            statistical_test="Критерий Манна-Уитни"
        ),
    ],
}


def suggest_endpoints(specialty: str, study_type: str) -> List[Endpoint]:
    """Suggest relevant endpoints based on specialty and study type."""
    endpoints = []

    # Find matching specialty
    specialty_lower = specialty.lower()
    for key, eps in SPECIALTY_ENDPOINTS.items():
        if key in specialty_lower or specialty_lower in key:
            endpoints.extend(eps)

    # Add universal endpoints
    universal = [
        Endpoint(
            name="Нежелательные явления",
            description="Частота и тяжесть нежелательных явлений",
            endpoint_type=EndpointType.CATEGORICAL,
            category=EndpointCategory.SAFETY,
            statistical_test="Точный критерий Фишера"
        ),
        Endpoint(
            name="Серьёзные нежелательные явления",
            description="Частота СНЯ (госпитализация, инвалидизация, смерть)",
            endpoint_type=EndpointType.BINARY,
            category=EndpointCategory.SAFETY,
            statistical_test="Точный критерий Фишера"
        ),
        Endpoint(
            name="Качество жизни (SF-36)",
            description="Опросник качества жизни Short Form-36",
            endpoint_type=EndpointType.CONTINUOUS,
            category=EndpointCategory.QUALITY_OF_LIFE,
            statistical_test="ANCOVA"
        ),
    ]
    endpoints.extend(universal)

    return endpoints


def get_statistical_test_recommendation(endpoint: Endpoint) -> List[tuple]:
    """Get recommended statistical tests for an endpoint."""
    return STATISTICAL_TESTS.get(endpoint.endpoint_type, [])
