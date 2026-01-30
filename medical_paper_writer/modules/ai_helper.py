"""
AI helper module for generating and improving medical paper content.
Uses Claude API for intelligent suggestions.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class AIResponse:
    content: str
    suggestions: List[str]
    confidence: float


# System prompts for different tasks
SYSTEM_PROMPTS = {
    "endpoint_suggestion": """Вы — эксперт в области клинических исследований и медицинской статистики.
Ваша задача — предложить подходящие первичные и вторичные конечные точки для исследования
на основе PICO-вопроса и типа исследования.

Учитывайте:
1. Клиническую значимость конечных точек
2. Измеримость и валидированность показателей
3. Временные рамки исследования
4. Статистические требования (непрерывные vs бинарные)
5. Рекомендации соответствующих чек-листов (CONSORT, STROBE и др.)

Формат ответа:
- Предложите 2-3 варианта первичной конечной точки с обоснованием
- Предложите 5-7 вторичных конечных точек
- Укажите рекомендуемые методы измерения
""",

    "literature_summary": """Вы — эксперт в области систематического обзора медицинской литературы.
Ваша задача — обобщить предоставленные источники и выделить ключевые находки.

Структура ответа:
1. Основные результаты исследований
2. Точки согласия между исследованиями
3. Противоречивые данные
4. Пробелы в знаниях
5. Рекомендации для обсуждения
""",

    "methods_improvement": """Вы — эксперт в области методологии медицинских исследований.
Ваша задача — проверить и улучшить раздел "Материалы и методы".

Проверьте:
1. Соответствие чек-листу (CONSORT/STROBE/PRISMA)
2. Полноту описания дизайна
3. Адекватность статистических методов
4. Воспроизводимость описания
5. Этические аспекты

Предоставьте конкретные рекомендации по улучшению.
""",

    "discussion_writing": """Вы — опытный медицинский исследователь и научный редактор.
Ваша задача — помочь написать раздел "Обсуждение" на основе результатов исследования.

Структура:
1. Резюме основных находок (связь с гипотезой)
2. Сопоставление с литературой (минимум 5 источников)
3. Возможные механизмы
4. Клиническое значение
5. Сильные стороны
6. Ограничения (честный анализ)
7. Направления будущих исследований

Стиль: академический, объективный, без преувеличений.
""",

    "statistical_advice": """Вы — биостатистик с опытом работы в клинических исследованиях.
Ваша задача — рекомендовать статистические методы анализа данных.

Учитывайте:
1. Тип переменных (непрерывные, бинарные, категориальные, время до события)
2. Распределение данных
3. Зависимость/независимость наблюдений
4. Размер выборки
5. Пропущенные данные
6. Множественные сравнения

Формат: рекомендуйте конкретные тесты с обоснованием.
""",
}


class AIHelper:
    """Helper class for AI-assisted content generation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = None

        if self.api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except ImportError:
                pass

    def is_available(self) -> bool:
        """Check if AI service is available."""
        return self.client is not None

    def _call_api(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000
    ) -> str:
        """Make API call to Claude."""
        if not self.client:
            return ""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            return message.content[0].text
        except Exception as e:
            return f"Ошибка API: {str(e)}"

    def suggest_endpoints(self, pico: Dict, study_type: str) -> str:
        """Suggest appropriate endpoints based on PICO and study type."""
        user_message = f"""
Тип исследования: {study_type}

PICO:
- Популяция: {pico.get('population', 'не указано')}
- Вмешательство: {pico.get('intervention', 'не указано')}
- Сравнение: {pico.get('comparison', 'не указано')}
- Текущий исход: {pico.get('outcome_primary', 'не указано')}

Предложите подходящие первичные и вторичные конечные точки для данного исследования.
"""
        return self._call_api(SYSTEM_PROMPTS["endpoint_suggestion"], user_message)

    def summarize_literature(self, references: List[Dict]) -> str:
        """Summarize literature findings."""
        refs_text = "\n\n".join([
            f"**{ref.get('title', 'Без названия')}** ({ref.get('year', 'год не указан')})\n"
            f"Журнал: {ref.get('journal', 'не указан')}\n"
            f"Абстракт: {ref.get('abstract', 'не доступен')[:500]}..."
            for ref in references[:10]  # Limit to 10 references
        ])

        user_message = f"""
Проанализируйте следующие источники и подготовьте краткое резюме для раздела "Обзор литературы":

{refs_text}

Выделите ключевые находки, точки согласия и противоречия.
"""
        return self._call_api(SYSTEM_PROMPTS["literature_summary"], user_message, max_tokens=3000)

    def improve_methods(self, methods_text: str, study_type: str, checklist: str) -> str:
        """Review and suggest improvements for methods section."""
        user_message = f"""
Тип исследования: {study_type}
Чек-лист: {checklist}

Текущий текст раздела "Материалы и методы":

{methods_text}

Проверьте текст на соответствие чек-листу и предложите улучшения.
"""
        return self._call_api(SYSTEM_PROMPTS["methods_improvement"], user_message, max_tokens=2500)

    def generate_discussion(
        self,
        study_type: str,
        pico: Dict,
        main_results: str,
        key_references: List[str]
    ) -> str:
        """Generate discussion section draft."""
        refs_text = "\n".join([f"- {ref}" for ref in key_references[:10]])

        user_message = f"""
Тип исследования: {study_type}

PICO:
- Популяция: {pico.get('population', '')}
- Вмешательство: {pico.get('intervention', '')}
- Сравнение: {pico.get('comparison', '')}
- Исход: {pico.get('outcome_primary', '')}

Основные результаты:
{main_results}

Ключевые источники для сравнения:
{refs_text}

Напишите черновик раздела "Обсуждение" на русском языке.
"""
        return self._call_api(SYSTEM_PROMPTS["discussion_writing"], user_message, max_tokens=4000)

    def recommend_statistics(
        self,
        outcome_type: str,
        groups: int,
        paired: bool,
        sample_size: int,
        additional_info: str = ""
    ) -> str:
        """Recommend statistical methods for analysis."""
        user_message = f"""
Характеристики данных:
- Тип исхода: {outcome_type}
- Количество групп: {groups}
- Связанные выборки: {'Да' if paired else 'Нет'}
- Размер выборки: {sample_size}
{f'- Дополнительно: {additional_info}' if additional_info else ''}

Рекомендуйте статистические методы для анализа данных.
Укажите основной тест и альтернативы, условия применения.
"""
        return self._call_api(SYSTEM_PROMPTS["statistical_advice"], user_message)

    def translate_to_english(self, text: str) -> str:
        """Translate Russian medical text to English."""
        system_prompt = """Вы — профессиональный переводчик медицинских текстов.
Переведите текст на английский язык, сохраняя научный стиль и терминологию.
Используйте стандартные медицинские термины и сокращения."""

        return self._call_api(system_prompt, text, max_tokens=3000)


# Fallback suggestions when AI is not available
FALLBACK_ENDPOINT_SUGGESTIONS = {
    "rct": {
        "primary": [
            "Изменение основного показателя эффективности через [X] недель",
            "Доля пациентов, достигших целевого значения",
            "Время до достижения ремиссии/ответа",
        ],
        "secondary": [
            "Качество жизни (SF-36, EQ-5D)",
            "Частота нежелательных явлений",
            "Приверженность лечению",
            "Изменение лабораторных показателей",
            "Длительность госпитализации",
            "Частота повторных госпитализаций",
        ],
    },
    "cohort": {
        "primary": [
            "Относительный риск (RR) исхода",
            "Hazard Ratio",
            "Кумулятивная инцидентность",
        ],
        "secondary": [
            "Атрибутивный риск",
            "Время до события",
            "Подгрупповые анализы",
        ],
    },
    "case_control": {
        "primary": [
            "Отношение шансов (OR)",
        ],
        "secondary": [
            "Скорректированный OR",
            "Популяционный атрибутивный риск",
            "Дозо-зависимый эффект",
        ],
    },
    "diagnostic": {
        "primary": [
            "Чувствительность и специфичность",
            "AUC-ROC",
        ],
        "secondary": [
            "Прогностическая ценность положительного результата",
            "Прогностическая ценность отрицательного результата",
            "Отношения правдоподобия",
            "Оптимальный порог отсечения",
        ],
    },
}


def get_fallback_suggestions(study_type: str) -> Dict:
    """Get fallback endpoint suggestions when AI is not available."""
    if "rct" in study_type.lower() or "рандом" in study_type.lower():
        return FALLBACK_ENDPOINT_SUGGESTIONS["rct"]
    elif "когорт" in study_type.lower() or "cohort" in study_type.lower():
        return FALLBACK_ENDPOINT_SUGGESTIONS["cohort"]
    elif "случай" in study_type.lower() or "case" in study_type.lower():
        return FALLBACK_ENDPOINT_SUGGESTIONS["case_control"]
    elif "диагност" in study_type.lower() or "diagnostic" in study_type.lower():
        return FALLBACK_ENDPOINT_SUGGESTIONS["diagnostic"]
    return FALLBACK_ENDPOINT_SUGGESTIONS["rct"]
