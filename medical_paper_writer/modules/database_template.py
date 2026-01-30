"""
Database template generator for data collection.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import pandas as pd
from io import BytesIO


class VariableType(Enum):
    NUMERIC_CONTINUOUS = "Числовая непрерывная"
    NUMERIC_DISCRETE = "Числовая дискретная"
    CATEGORICAL_NOMINAL = "Категориальная номинальная"
    CATEGORICAL_ORDINAL = "Категориальная порядковая"
    BINARY = "Бинарная (да/нет)"
    DATE = "Дата"
    TEXT = "Текст"


@dataclass
class Variable:
    name: str
    label: str
    var_type: VariableType
    unit: str = ""
    allowed_values: List[str] = field(default_factory=list)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    required: bool = True
    description: str = ""
    coding: str = ""  # For categorical: "1=Male, 2=Female"


@dataclass
class VariableGroup:
    name: str
    variables: List[Variable]


# Standard variable templates
DEMOGRAPHIC_VARIABLES = VariableGroup(
    name="Демографические данные",
    variables=[
        Variable(
            name="patient_id",
            label="ID пациента",
            var_type=VariableType.TEXT,
            required=True,
            description="Уникальный идентификатор"
        ),
        Variable(
            name="age",
            label="Возраст",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="лет",
            min_value=0,
            max_value=120,
            description="Полных лет на момент включения"
        ),
        Variable(
            name="sex",
            label="Пол",
            var_type=VariableType.BINARY,
            allowed_values=["М", "Ж"],
            coding="М=мужской, Ж=женский"
        ),
        Variable(
            name="height",
            label="Рост",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="см",
            min_value=50,
            max_value=250
        ),
        Variable(
            name="weight",
            label="Масса тела",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="кг",
            min_value=20,
            max_value=300
        ),
        Variable(
            name="bmi",
            label="ИМТ",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="кг/м²",
            description="Рассчитывается: вес/(рост/100)²"
        ),
    ]
)

CLINICAL_VARIABLES = VariableGroup(
    name="Клинические данные",
    variables=[
        Variable(
            name="diagnosis_primary",
            label="Основной диагноз",
            var_type=VariableType.TEXT,
            description="По МКБ-10"
        ),
        Variable(
            name="diagnosis_code",
            label="Код МКБ-10",
            var_type=VariableType.TEXT
        ),
        Variable(
            name="disease_duration",
            label="Длительность заболевания",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="мес."
        ),
        Variable(
            name="disease_severity",
            label="Степень тяжести",
            var_type=VariableType.CATEGORICAL_ORDINAL,
            allowed_values=["Лёгкая", "Средняя", "Тяжёлая"],
            coding="1=Лёгкая, 2=Средняя, 3=Тяжёлая"
        ),
        Variable(
            name="comorbidity_count",
            label="Количество сопутствующих заболеваний",
            var_type=VariableType.NUMERIC_DISCRETE
        ),
    ]
)

VITAL_SIGNS = VariableGroup(
    name="Витальные показатели",
    variables=[
        Variable(
            name="sbp",
            label="САД",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="мм рт.ст.",
            min_value=60,
            max_value=300,
            description="Систолическое артериальное давление"
        ),
        Variable(
            name="dbp",
            label="ДАД",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="мм рт.ст.",
            min_value=30,
            max_value=200,
            description="Диастолическое артериальное давление"
        ),
        Variable(
            name="heart_rate",
            label="ЧСС",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="уд/мин",
            min_value=30,
            max_value=250
        ),
        Variable(
            name="respiratory_rate",
            label="ЧДД",
            var_type=VariableType.NUMERIC_DISCRETE,
            unit="в мин",
            min_value=5,
            max_value=60
        ),
        Variable(
            name="temperature",
            label="Температура тела",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="°C",
            min_value=34,
            max_value=42
        ),
        Variable(
            name="spo2",
            label="SpO2",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="%",
            min_value=50,
            max_value=100
        ),
    ]
)

TREATMENT_VARIABLES = VariableGroup(
    name="Лечение",
    variables=[
        Variable(
            name="group",
            label="Группа",
            var_type=VariableType.CATEGORICAL_NOMINAL,
            allowed_values=["Основная", "Контроль"],
            coding="1=Основная, 2=Контроль"
        ),
        Variable(
            name="treatment_start",
            label="Дата начала лечения",
            var_type=VariableType.DATE
        ),
        Variable(
            name="treatment_end",
            label="Дата окончания лечения",
            var_type=VariableType.DATE
        ),
        Variable(
            name="treatment_duration",
            label="Длительность лечения",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="дней"
        ),
        Variable(
            name="dose",
            label="Доза препарата",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="мг"
        ),
    ]
)

OUTCOME_VARIABLES = VariableGroup(
    name="Исходы",
    variables=[
        Variable(
            name="primary_outcome",
            label="Первичный исход",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            description="Основной показатель эффективности"
        ),
        Variable(
            name="response",
            label="Ответ на лечение",
            var_type=VariableType.BINARY,
            allowed_values=["Да", "Нет"],
            coding="1=Да, 0=Нет"
        ),
        Variable(
            name="adverse_event",
            label="Нежелательное явление",
            var_type=VariableType.BINARY,
            allowed_values=["Да", "Нет"],
            coding="1=Да, 0=Нет"
        ),
        Variable(
            name="ae_severity",
            label="Тяжесть НЯ",
            var_type=VariableType.CATEGORICAL_ORDINAL,
            allowed_values=["Лёгкая", "Средняя", "Тяжёлая", "Жизнеугрожающая"],
            coding="1=Лёгкая, 2=Средняя, 3=Тяжёлая, 4=Жизнеугрожающая",
            required=False
        ),
        Variable(
            name="followup_date",
            label="Дата контрольного визита",
            var_type=VariableType.DATE
        ),
        Variable(
            name="status",
            label="Статус пациента",
            var_type=VariableType.CATEGORICAL_NOMINAL,
            allowed_values=["Жив", "Умер", "Выбыл из наблюдения"],
            coding="1=Жив, 2=Умер, 3=Выбыл"
        ),
    ]
)

LABORATORY_VARIABLES = VariableGroup(
    name="Лабораторные показатели",
    variables=[
        Variable(
            name="hemoglobin",
            label="Гемоглобин",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="г/л",
            min_value=30,
            max_value=250
        ),
        Variable(
            name="wbc",
            label="Лейкоциты",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="×10⁹/л",
            min_value=0.1,
            max_value=100
        ),
        Variable(
            name="platelets",
            label="Тромбоциты",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="×10⁹/л",
            min_value=10,
            max_value=1000
        ),
        Variable(
            name="creatinine",
            label="Креатинин",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="мкмоль/л",
            min_value=20,
            max_value=2000
        ),
        Variable(
            name="alt",
            label="АЛТ",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="Ед/л",
            min_value=0,
            max_value=5000
        ),
        Variable(
            name="ast",
            label="АСТ",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="Ед/л",
            min_value=0,
            max_value=5000
        ),
        Variable(
            name="glucose",
            label="Глюкоза",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="ммоль/л",
            min_value=1,
            max_value=50
        ),
        Variable(
            name="crp",
            label="С-реактивный белок",
            var_type=VariableType.NUMERIC_CONTINUOUS,
            unit="мг/л",
            min_value=0,
            max_value=500
        ),
    ]
)


TIME_POINTS = ["baseline", "week1", "week4", "week12", "week24", "week52"]
TIME_POINT_LABELS = {
    "baseline": "Исходно",
    "week1": "1 неделя",
    "week4": "4 недели",
    "week12": "12 недель",
    "week24": "24 недели",
    "week52": "52 недели",
}


class DatabaseTemplateGenerator:
    """Generate Excel templates for data collection."""

    def __init__(self):
        self.variable_groups: List[VariableGroup] = []
        self.time_points: List[str] = ["baseline"]
        self.custom_variables: List[Variable] = []

    def add_standard_group(self, group: VariableGroup):
        """Add a standard variable group."""
        self.variable_groups.append(group)

    def add_custom_variable(self, variable: Variable):
        """Add a custom variable."""
        self.custom_variables.append(variable)

    def set_time_points(self, time_points: List[str]):
        """Set measurement time points."""
        self.time_points = time_points

    def get_all_variables(self) -> List[Variable]:
        """Get all variables from all groups."""
        variables = []
        for group in self.variable_groups:
            variables.extend(group.variables)
        variables.extend(self.custom_variables)
        return variables

    def generate_codebook(self) -> pd.DataFrame:
        """Generate a codebook describing all variables."""
        rows = []
        for group in self.variable_groups:
            for var in group.variables:
                rows.append({
                    "Группа": group.name,
                    "Имя переменной": var.name,
                    "Название": var.label,
                    "Тип": var.var_type.value,
                    "Единицы": var.unit,
                    "Допустимые значения": ", ".join(var.allowed_values) if var.allowed_values else "",
                    "Кодирование": var.coding,
                    "Мин": var.min_value if var.min_value is not None else "",
                    "Макс": var.max_value if var.max_value is not None else "",
                    "Обязательное": "Да" if var.required else "Нет",
                    "Описание": var.description,
                })

        for var in self.custom_variables:
            rows.append({
                "Группа": "Пользовательские",
                "Имя переменной": var.name,
                "Название": var.label,
                "Тип": var.var_type.value,
                "Единицы": var.unit,
                "Допустимые значения": ", ".join(var.allowed_values) if var.allowed_values else "",
                "Кодирование": var.coding,
                "Мин": var.min_value if var.min_value is not None else "",
                "Макс": var.max_value if var.max_value is not None else "",
                "Обязательное": "Да" if var.required else "Нет",
                "Описание": var.description,
            })

        return pd.DataFrame(rows)

    def generate_data_template(self, n_rows: int = 10) -> pd.DataFrame:
        """Generate a data collection template."""
        columns = []

        # Static variables (measured once)
        static_vars = ["patient_id", "age", "sex", "height", "weight", "bmi",
                       "diagnosis_primary", "diagnosis_code", "group"]

        for var in self.get_all_variables():
            if var.name in static_vars:
                columns.append(var.label)
            else:
                # For repeated measures, add time point suffix
                if len(self.time_points) > 1:
                    for tp in self.time_points:
                        tp_label = TIME_POINT_LABELS.get(tp, tp)
                        columns.append(f"{var.label}_{tp_label}")
                else:
                    columns.append(var.label)

        df = pd.DataFrame(columns=columns)

        # Add example rows
        for i in range(n_rows):
            df.loc[i] = [""] * len(columns)

        return df

    def generate_excel(self) -> BytesIO:
        """Generate an Excel file with multiple sheets."""
        output = BytesIO()

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Data sheet
            data_df = self.generate_data_template()
            data_df.to_excel(writer, sheet_name='Данные', index=False)

            # Codebook sheet
            codebook_df = self.generate_codebook()
            codebook_df.to_excel(writer, sheet_name='Словарь переменных', index=False)

            # Instructions sheet
            instructions = pd.DataFrame({
                'Инструкции': [
                    'Как заполнять базу данных:',
                    '',
                    '1. Каждая строка = один пациент',
                    '2. Заполняйте все обязательные поля',
                    '3. Используйте кодирование из словаря переменных',
                    '4. Даты в формате ДД.ММ.ГГГГ',
                    '5. Десятичные числа через точку (например, 1.5)',
                    '6. Пропущенные значения оставляйте пустыми',
                    '',
                    'Правила валидации:',
                    '- Проверяйте допустимые диапазоны значений',
                    '- Убедитесь в уникальности ID пациентов',
                    '- Проверьте логику дат (начало < конец)',
                ]
            })
            instructions.to_excel(writer, sheet_name='Инструкции', index=False, header=False)

            # Format worksheets
            workbook = writer.book

            # Format for headers
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1
            })

            # Apply formatting to Data sheet
            worksheet = writer.sheets['Данные']
            for col_num, value in enumerate(data_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15)

            # Apply formatting to Codebook
            worksheet = writer.sheets['Словарь переменных']
            for col_num, value in enumerate(codebook_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 18)

        output.seek(0)
        return output


def create_template_for_study(study_type: str, endpoints: List[str]) -> DatabaseTemplateGenerator:
    """Create a database template based on study type."""
    generator = DatabaseTemplateGenerator()

    # Always include demographics
    generator.add_standard_group(DEMOGRAPHIC_VARIABLES)

    # Add groups based on study type
    if study_type in ["rct", "cohort_prospective", "cohort_retrospective"]:
        generator.add_standard_group(CLINICAL_VARIABLES)
        generator.add_standard_group(TREATMENT_VARIABLES)
        generator.add_standard_group(OUTCOME_VARIABLES)
        generator.add_standard_group(VITAL_SIGNS)
        generator.set_time_points(["baseline", "week4", "week12"])

    elif study_type == "case_control":
        generator.add_standard_group(CLINICAL_VARIABLES)
        generator.add_standard_group(OUTCOME_VARIABLES)
        # Add exposure variable
        generator.add_custom_variable(Variable(
            name="exposure",
            label="Экспозиция (фактор риска)",
            var_type=VariableType.BINARY,
            allowed_values=["Да", "Нет"],
            coding="1=Да, 0=Нет"
        ))

    elif study_type == "cross_sectional":
        generator.add_standard_group(CLINICAL_VARIABLES)
        generator.add_standard_group(VITAL_SIGNS)
        generator.add_standard_group(LABORATORY_VARIABLES)

    elif study_type == "diagnostic_accuracy":
        generator.add_standard_group(CLINICAL_VARIABLES)
        generator.add_custom_variable(Variable(
            name="test_result",
            label="Результат теста",
            var_type=VariableType.CATEGORICAL_NOMINAL,
            allowed_values=["Положительный", "Отрицательный"],
            coding="1=Положительный, 0=Отрицательный"
        ))
        generator.add_custom_variable(Variable(
            name="reference_result",
            label="Результат референс-теста",
            var_type=VariableType.CATEGORICAL_NOMINAL,
            allowed_values=["Положительный", "Отрицательный"],
            coding="1=Положительный, 0=Отрицательный"
        ))

    # Add custom endpoints
    for i, endpoint in enumerate(endpoints):
        generator.add_custom_variable(Variable(
            name=f"endpoint_{i + 1}",
            label=endpoint,
            var_type=VariableType.NUMERIC_CONTINUOUS,
            description=f"Конечная точка: {endpoint}"
        ))

    return generator
