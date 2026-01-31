"""
Medical Paper Writer - Streamlit Application
Помощник для написания медицинских научных статей
"""

import streamlit as st
import pandas as pd
from io import BytesIO
import json

# Import modules
from modules.study_types import STUDY_TYPES, get_study_types_by_category, StudyCategory
from modules.pico import PICOQuestion, PICOType, PICO_EXAMPLES, PICO_HINTS, suggest_outcomes_for_condition
from modules.endpoints import (
    Endpoint, EndpointType, EndpointCategory,
    suggest_endpoints as suggest_specialty_endpoints,
    STATISTICAL_TESTS
)
from modules.sample_size import (
    DesignType, calculate_two_means, calculate_two_proportions,
    calculate_case_control, calculate_survival, calculate_diagnostic_accuracy
)
from modules.database_template import create_template_for_study, DEMOGRAPHIC_VARIABLES, CLINICAL_VARIABLES
from modules.literature import search_for_literature_review, generate_search_strategy
from modules.methods import generate_full_methods_section, METHODS_CHECKLISTS
from modules.results import DataAnalyzer, suggest_analyses
from modules.discussion import generate_discussion_structure, generate_conclusion, generate_abstract
from modules.ai_helper import AIHelper, get_fallback_suggestions


# Page config
st.set_page_config(
    page_title="Medical Paper Writer",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        margin-bottom: 1rem;
    }
    .step-header {
        font-size: 1.5rem;
        color: #2e7d32;
        border-bottom: 2px solid #2e7d32;
        padding-bottom: 0.5rem;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1976d2;
    }
    .warning-box {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff9800;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        'current_step': 0,
        'study_type': None,
        'pico': PICOQuestion(),
        'primary_endpoint': None,
        'secondary_endpoints': [],
        'sample_size_result': None,
        'uploaded_data': None,
        'analysis_results': [],
        'generated_sections': {},
        'references': [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar():
    """Render navigation sidebar."""
    with st.sidebar:
        st.markdown("### Навигация")

        steps = [
            "1. Тип исследования",
            "2. PICO гипотеза",
            "3. Конечные точки",
            "4. Расчёт выборки",
            "5. Шаблон базы данных",
            "6. Написание разделов",
        ]

        for i, step in enumerate(steps):
            if i == st.session_state.current_step:
                st.markdown(f"**→ {step}**")
            elif i < st.session_state.current_step:
                st.markdown(f"✓ {step}")
            else:
                st.markdown(f"○ {step}")

        st.divider()

        # Quick info about current project
        if st.session_state.study_type:
            st.markdown("### Текущий проект")
            study = STUDY_TYPES.get(st.session_state.study_type)
            if study:
                st.write(f"**Тип:** {study.name}")
                st.write(f"**Чек-лист:** {study.checklist}")

        st.divider()

        # Save/Load project
        st.markdown("### Сохранение проекта")

        # Save button
        if st.session_state.study_type:  # Only show if project started
            json_str = export_project()
            st.download_button(
                label="💾 Сохранить проект",
                data=json_str,
                file_name="medical_paper_project.json",
                mime="application/json",
                help="Скачать проект для продолжения позже"
            )

        # Load project
        uploaded_project = st.file_uploader(
            "📂 Загрузить проект",
            type=['json'],
            help="Загрузить ранее сохранённый проект"
        )
        if uploaded_project:
            success, message = load_project(uploaded_project)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

        st.divider()

        # Reset
        if st.button("🔄 Начать заново"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def render_step_1_study_type():
    """Step 1: Select study type."""
    st.markdown('<p class="step-header">Шаг 1: Выберите тип исследования</p>', unsafe_allow_html=True)

    st.markdown("""
    Выберите тип материала, который вы готовите. От этого зависит структура работы,
    требуемые разделы и применяемый чек-лист качества.
    """)

    categories = get_study_types_by_category()

    for category in StudyCategory:
        with st.expander(f"📁 {category.value}", expanded=(category == StudyCategory.EXPERIMENTAL)):
            studies = categories[category]
            for study in studies:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{study.name}**")
                    st.caption(study.description)
                    st.caption(f"Чек-лист: {study.checklist}")
                with col2:
                    if st.button("Выбрать", key=f"select_{study.id}"):
                        st.session_state.study_type = study.id
                        st.session_state.current_step = 1
                        st.rerun()

    # Show selected
    if st.session_state.study_type:
        study = STUDY_TYPES[st.session_state.study_type]
        st.success(f"Выбран тип: **{study.name}**")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Разделы работы:**")
            for section in study.sections:
                st.write(f"- {section}")
        with col2:
            st.markdown("**Типичные конечные точки:**")
            for endpoint in study.typical_endpoints[:5]:
                st.write(f"- {endpoint}")

        if st.button("Далее →", type="primary"):
            st.session_state.current_step = 1
            st.rerun()


def render_step_2_pico():
    """Step 2: PICO hypothesis."""
    st.markdown('<p class="step-header">Шаг 2: Формулировка гипотезы (PICO)</p>', unsafe_allow_html=True)

    st.markdown("""
    PICO — стандарт формулировки клинического вопроса:
    **P**opulation, **I**ntervention, **C**omparison, **O**utcome
    """)

    # Question type
    col1, col2 = st.columns([2, 1])
    with col1:
        question_type = st.selectbox(
            "Тип клинического вопроса",
            options=[pt for pt in PICOType],
            format_func=lambda x: x.value
        )
        st.session_state.pico.question_type = question_type

    st.divider()

    # PICO fields
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### P — Популяция/Пациенты")
        with st.expander("Подсказка"):
            st.markdown(PICO_HINTS["population"])
            st.markdown("**Примеры:**")
            for ex in PICO_EXAMPLES["population"]:
                st.write(f"• {ex}")

        population = st.text_area(
            "Опишите целевую популяцию",
            value=st.session_state.pico.population,
            height=100,
            placeholder="Например: взрослые пациенты (18-65 лет) с артериальной гипертензией 1-2 степени"
        )
        st.session_state.pico.population = population

    with col2:
        st.markdown("### I — Вмешательство")
        with st.expander("Подсказка"):
            st.markdown(PICO_HINTS["intervention"])
            st.markdown("**Примеры:**")
            for ex in PICO_EXAMPLES["intervention"]:
                st.write(f"• {ex}")

        intervention = st.text_area(
            "Опишите изучаемое вмешательство",
            value=st.session_state.pico.intervention,
            height=100,
            placeholder="Например: телемедицинское наблюдение с еженедельным контролем АД"
        )
        st.session_state.pico.intervention = intervention

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("### C — Сравнение")
        with st.expander("Подсказка"):
            st.markdown(PICO_HINTS["comparison"])

        comparison = st.text_area(
            "Опишите группу сравнения",
            value=st.session_state.pico.comparison,
            height=100,
            placeholder="Например: стандартное наблюдение с визитами каждые 3 месяца"
        )
        st.session_state.pico.comparison = comparison

    with col4:
        st.markdown("### O — Исход")
        with st.expander("Подсказка"):
            st.markdown(PICO_HINTS["outcome"])

        outcome = st.text_area(
            "Опишите основной исход",
            value=st.session_state.pico.outcome_primary,
            height=100,
            placeholder="Например: достижение целевого уровня АД (<140/90 мм рт.ст.)"
        )
        st.session_state.pico.outcome_primary = outcome

    st.divider()

    # Show formatted question and hypothesis
    if all([population, intervention, outcome]):
        st.markdown("### Сформулированный вопрос")
        st.info(st.session_state.pico.format_question())

        st.markdown("### Гипотеза исследования")
        st.success(st.session_state.pico.format_hypothesis())

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Назад"):
            st.session_state.current_step = 0
            st.rerun()
    with col3:
        if st.button("Далее →", type="primary", disabled=not all([population, intervention, outcome])):
            st.session_state.current_step = 2
            st.rerun()


def render_step_3_endpoints():
    """Step 3: Select endpoints."""
    st.markdown('<p class="step-header">Шаг 3: Конечные точки исследования</p>', unsafe_allow_html=True)

    pico = st.session_state.pico
    study_type = st.session_state.study_type

    # Suggest endpoints based on PICO
    st.markdown("### Предлагаемые конечные точки")
    st.markdown("На основе вашего PICO-вопроса рекомендуем следующие варианты:")

    # Get suggestions
    suggested = suggest_outcomes_for_condition(pico.population, pico.intervention)
    fallback = get_fallback_suggestions(study_type)

    # Primary endpoint
    st.markdown("#### Первичная конечная точка")

    primary_options = [pico.outcome_primary] + fallback.get("primary", []) + suggested[:3]
    primary_options = list(dict.fromkeys(primary_options))  # Remove duplicates

    primary = st.selectbox(
        "Выберите или введите первичную конечную точку",
        options=primary_options + ["Другое (ввести вручную)"],
    )

    if primary == "Другое (ввести вручную)":
        primary = st.text_input("Введите первичную конечную точку")

    if primary:
        col1, col2 = st.columns(2)
        with col1:
            primary_type = st.selectbox(
                "Тип переменной",
                options=[et for et in EndpointType],
                format_func=lambda x: x.value,
                key="primary_type"
            )
        with col2:
            if primary_type in STATISTICAL_TESTS:
                tests = STATISTICAL_TESTS[primary_type]
                st.markdown("**Рекомендуемые статистические тесты:**")
                for test, desc in tests[:3]:
                    st.caption(f"• {test}: {desc}")

    st.session_state.primary_endpoint = primary

    st.divider()

    # Secondary endpoints
    st.markdown("#### Вторичные конечные точки")

    # Combine all options including previously added custom ones
    secondary_options = fallback.get("secondary", []) + suggested[3:]
    # Add any custom endpoints that were previously added
    for ep in st.session_state.secondary_endpoints:
        if ep not in secondary_options:
            secondary_options.append(ep)
    secondary_options = list(dict.fromkeys(secondary_options))  # Remove duplicates

    secondary = st.multiselect(
        "Выберите вторичные конечные точки (рекомендуется 3-5)",
        options=secondary_options,
        default=st.session_state.secondary_endpoints if st.session_state.secondary_endpoints else []
    )

    # Add custom endpoint
    custom_secondary = st.text_input("Добавить свою вторичную точку")
    if custom_secondary:
        if st.button("Добавить"):
            if custom_secondary not in secondary:
                secondary.append(custom_secondary)
                st.session_state.secondary_endpoints = secondary
                st.rerun()

    st.session_state.secondary_endpoints = secondary

    # Show summary
    if primary and secondary:
        st.divider()
        st.markdown("### Итого выбрано")
        st.write(f"**Первичная точка:** {primary}")
        st.write("**Вторичные точки:**")
        for s in secondary:
            st.write(f"- {s}")

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Назад"):
            st.session_state.current_step = 1
            st.rerun()
    with col3:
        if st.button("Далее →", type="primary", disabled=not primary):
            st.session_state.current_step = 3
            st.rerun()


def render_step_4_sample_size():
    """Step 4: Sample size calculation."""
    st.markdown('<p class="step-header">Шаг 4: Расчёт размера выборки</p>', unsafe_allow_html=True)

    study = STUDY_TYPES.get(st.session_state.study_type)

    if not study.requires_sample_size:
        st.info(f"Для типа исследования '{study.name}' формальный расчёт выборки обычно не требуется.")
        if st.button("Далее →", type="primary"):
            st.session_state.current_step = 4
            st.rerun()
        return

    # Select calculation type
    calc_type = st.selectbox(
        "Тип расчёта",
        options=[
            ("two_means", "Сравнение двух средних"),
            ("two_proportions", "Сравнение двух пропорций"),
            ("case_control", "Исследование случай-контроль"),
            ("survival", "Анализ выживаемости"),
            ("diagnostic", "Диагностическая точность"),
        ],
        format_func=lambda x: x[1]
    )

    st.divider()

    result = None

    if calc_type[0] == "two_means":
        st.markdown("### Параметры для сравнения средних")

        col1, col2 = st.columns(2)
        with col1:
            mean1 = st.number_input("Ожидаемое среднее в группе 1", value=100.0)
            mean2 = st.number_input("Ожидаемое среднее в группе 2", value=90.0)
            sd = st.number_input("Стандартное отклонение", value=20.0, min_value=0.1)
        with col2:
            alpha = st.selectbox("Уровень значимости (α)", [0.05, 0.01, 0.1], index=0)
            power = st.selectbox("Мощность (1-β)", [0.80, 0.85, 0.90, 0.95], index=0)
            ratio = st.number_input("Соотношение групп (n2/n1)", value=1.0, min_value=0.5, max_value=4.0)

        if st.button("Рассчитать"):
            result = calculate_two_means(mean1, mean2, sd, alpha, power, ratio)

    elif calc_type[0] == "two_proportions":
        st.markdown("### Параметры для сравнения пропорций")

        col1, col2 = st.columns(2)
        with col1:
            p1 = st.slider("Ожидаемая доля в группе 1 (%)", 1, 99, 30) / 100
            p2 = st.slider("Ожидаемая доля в группе 2 (%)", 1, 99, 20) / 100
        with col2:
            alpha = st.selectbox("Уровень значимости (α)", [0.05, 0.01, 0.1], index=0)
            power = st.selectbox("Мощность (1-β)", [0.80, 0.85, 0.90, 0.95], index=0)

        if st.button("Рассчитать"):
            result = calculate_two_proportions(p1, p2, alpha, power)

    elif calc_type[0] == "case_control":
        st.markdown("### Параметры для исследования случай-контроль")

        col1, col2 = st.columns(2)
        with col1:
            p_exp_cases = st.slider("Доля экспозиции у случаев (%)", 1, 99, 40) / 100
            p_exp_controls = st.slider("Доля экспозиции у контролей (%)", 1, 99, 20) / 100
        with col2:
            alpha = st.selectbox("Уровень значимости (α)", [0.05, 0.01, 0.1], index=0)
            power = st.selectbox("Мощность (1-β)", [0.80, 0.85, 0.90, 0.95], index=0)
            ratio = st.number_input("Контролей на 1 случай", value=1, min_value=1, max_value=4)

        if st.button("Рассчитать"):
            result = calculate_case_control(p_exp_cases, p_exp_controls, None, alpha, power, ratio)

    elif calc_type[0] == "survival":
        st.markdown("### Параметры для анализа выживаемости")

        col1, col2 = st.columns(2)
        with col1:
            hr = st.number_input("Ожидаемый Hazard Ratio", value=0.7, min_value=0.1, max_value=2.0)
            p_event = st.slider("Частота событий в контроле (%)", 5, 80, 30) / 100
        with col2:
            alpha = st.selectbox("Уровень значимости (α)", [0.05, 0.01, 0.1], index=0)
            power = st.selectbox("Мощность (1-β)", [0.80, 0.85, 0.90, 0.95], index=0)
            accrual = st.number_input("Период набора (мес)", value=12)
            followup = st.number_input("Период наблюдения (мес)", value=12)

        if st.button("Рассчитать"):
            result = calculate_survival(hr, p_event, alpha, power, 1.0, accrual, followup)

    elif calc_type[0] == "diagnostic":
        st.markdown("### Параметры для диагностического исследования")

        col1, col2 = st.columns(2)
        with col1:
            sens = st.slider("Ожидаемая чувствительность (%)", 50, 99, 85) / 100
            spec = st.slider("Ожидаемая специфичность (%)", 50, 99, 90) / 100
        with col2:
            prev = st.slider("Распространённость заболевания (%)", 1, 50, 10) / 100
            precision = st.slider("Желаемая точность ДИ (±%)", 3, 15, 5) / 100

        if st.button("Рассчитать"):
            result = calculate_diagnostic_accuracy(sens, spec, prev, precision)

    # Show result
    if result:
        st.session_state.sample_size_result = result

        st.divider()
        st.markdown("### Результаты расчёта")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Размер выборки на группу", result.n_per_group)
            st.metric("Общий размер выборки", result.n_total)
        with col2:
            st.metric("Мощность", f"{result.power:.0%}")
            st.metric("Уровень значимости", f"{result.alpha}")

        st.markdown("#### Формула")
        st.code(result.formula_description)

        st.markdown("#### Допущения")
        st.warning(result.assumptions)

        st.markdown("#### Рекомендация")
        st.success(result.recommendation)

    # Navigation
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Назад"):
            st.session_state.current_step = 2
            st.rerun()
    with col3:
        if st.button("Далее →", type="primary"):
            st.session_state.current_step = 4
            st.rerun()


def render_step_5_database():
    """Step 5: Database template."""
    st.markdown('<p class="step-header">Шаг 5: Шаблон базы данных</p>', unsafe_allow_html=True)

    st.markdown("""
    Создайте шаблон Excel-файла для сбора данных исследования.
    Шаблон включает стандартные переменные и ваши конечные точки.
    """)

    # Configure template
    st.markdown("### Настройка шаблона")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Включить группы переменных:**")
        include_demo = st.checkbox("Демографические данные", value=True)
        include_clinical = st.checkbox("Клинические данные", value=True)
        include_vitals = st.checkbox("Витальные показатели", value=True)
        include_lab = st.checkbox("Лабораторные показатели", value=False)
        include_treatment = st.checkbox("Данные о лечении", value=True)

    with col2:
        st.markdown("**Временные точки:**")
        timepoints = st.multiselect(
            "Выберите точки измерения",
            options=["baseline", "week1", "week4", "week12", "week24", "week52"],
            default=["baseline", "week12"],
            format_func=lambda x: {
                "baseline": "Исходно",
                "week1": "1 неделя",
                "week4": "4 недели",
                "week12": "12 недель",
                "week24": "24 недели",
                "week52": "52 недели"
            }.get(x, x)
        )

    # Generate template
    if st.button("Сгенерировать шаблон", type="primary"):
        endpoints = [st.session_state.primary_endpoint] + st.session_state.secondary_endpoints
        endpoints = [e for e in endpoints if e]

        generator = create_template_for_study(st.session_state.study_type, endpoints)
        generator.set_time_points(timepoints)

        # Generate Excel
        excel_buffer = generator.generate_excel()

        st.download_button(
            label="📥 Скачать шаблон Excel",
            data=excel_buffer,
            file_name="database_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Show preview
        st.markdown("### Предпросмотр шаблона")

        codebook = generator.generate_codebook()
        st.dataframe(codebook, use_container_width=True)

    st.divider()

    # Upload filled data
    st.markdown("### Загрузка заполненных данных")
    st.markdown("После сбора данных загрузите заполненный файл для анализа.")

    uploaded_file = st.file_uploader("Загрузить Excel файл", type=['xlsx', 'xls'])

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            st.session_state.uploaded_data = df

            st.success(f"Загружено {len(df)} записей, {len(df.columns)} переменных")
            st.dataframe(df.head(10), use_container_width=True)
        except Exception as e:
            st.error(f"Ошибка загрузки: {e}")

    # Navigation
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Назад"):
            st.session_state.current_step = 3
            st.rerun()
    with col3:
        if st.button("Далее →", type="primary"):
            st.session_state.current_step = 5
            st.rerun()


def render_step_6_writing():
    """Step 6: Write paper sections."""
    st.markdown('<p class="step-header">Шаг 6: Написание разделов</p>', unsafe_allow_html=True)

    study = STUDY_TYPES.get(st.session_state.study_type)
    pico = st.session_state.pico

    # Section selector
    section = st.selectbox(
        "Выберите раздел для работы",
        options=[
            "literature", "methods", "results", "discussion", "conclusion", "abstract"
        ],
        format_func=lambda x: {
            "literature": "📚 Обзор литературы",
            "methods": "🔬 Материалы и методы",
            "results": "📊 Результаты",
            "discussion": "💬 Обсуждение",
            "conclusion": "✅ Заключение",
            "abstract": "📝 Резюме (Abstract)"
        }.get(x, x)
    )

    st.divider()

    if section == "literature":
        render_literature_section()
    elif section == "methods":
        render_methods_section()
    elif section == "results":
        render_results_section()
    elif section == "discussion":
        render_discussion_section()
    elif section == "conclusion":
        render_conclusion_section()
    elif section == "abstract":
        render_abstract_section()

    # Navigation
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Назад"):
            st.session_state.current_step = 4
            st.rerun()


def render_literature_section():
    """Render literature review section."""
    st.markdown("### Обзор литературы")

    pico = st.session_state.pico

    # Search strategy
    st.markdown("#### Стратегия поиска")

    search_strategy = generate_search_strategy(pico.to_dict())
    st.markdown(search_strategy)

    st.divider()

    # PubMed search
    st.markdown("#### Поиск в PubMed")

    search_query = st.text_input(
        "Поисковый запрос",
        value=f"{pico.population} {pico.intervention} {pico.outcome_primary}"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        min_year = st.number_input("Минимальный год", value=2018, min_value=1990, max_value=2025)
    with col2:
        include_reviews = st.checkbox("Систематические обзоры", value=True)
        include_rcts = st.checkbox("РКИ", value=True)
    with col3:
        include_meta = st.checkbox("Мета-анализы", value=True)
        max_results = st.number_input("Максимум результатов", value=50, min_value=10, max_value=200)

    if st.button("🔍 Искать"):
        with st.spinner("Поиск в PubMed..."):
            references = search_for_literature_review(
                search_query,
                pico.to_dict(),
                min_year=min_year,
                include_reviews=include_reviews,
                include_rcts=include_rcts,
                include_meta=include_meta,
                max_results=max_results
            )

            if references:
                st.session_state.references = references
                st.success(f"Найдено {len(references)} источников")
            else:
                st.warning("Источники не найдены. Попробуйте изменить запрос.")

    # Show references
    if st.session_state.references:
        st.markdown("#### Найденные источники")

        for i, ref in enumerate(st.session_state.references[:20]):
            with st.expander(f"{i+1}. {ref.title[:80]}..." if len(ref.title) > 80 else f"{i+1}. {ref.title}"):
                st.write(f"**Авторы:** {', '.join(ref.authors[:3])}{'...' if len(ref.authors) > 3 else ''}")
                st.write(f"**Журнал:** {ref.journal} ({ref.year})")
                st.write(f"**Тип:** {ref.study_type}")
                if ref.abstract:
                    st.write(f"**Абстракт:** {ref.abstract[:500]}...")
                st.code(ref.format_vancouver())


def render_methods_section():
    """Render methods section."""
    st.markdown("### Материалы и методы")

    pico = st.session_state.pico
    study_type = st.session_state.study_type
    study = STUDY_TYPES.get(study_type)

    # Checklist reminder
    if study_type in METHODS_CHECKLISTS:
        checklist = METHODS_CHECKLISTS[study_type]
        with st.expander(f"📋 Чек-лист {checklist['name']}"):
            for item in checklist['items']:
                st.checkbox(item, key=f"check_{item[:20]}")

    # Generate methods
    if st.button("Сгенерировать раздел", type="primary"):
        sample_info = None
        if st.session_state.sample_size_result:
            sample_info = {
                'power': st.session_state.sample_size_result.power,
                'alpha': st.session_state.sample_size_result.alpha,
                'recommendation': st.session_state.sample_size_result.recommendation,
                'formula_description': st.session_state.sample_size_result.formula_description,
            }

        methods_text = generate_full_methods_section(
            study_type=study_type,
            pico=pico.to_dict(),
            primary_outcome=st.session_state.primary_endpoint or pico.outcome_primary,
            secondary_outcomes=st.session_state.secondary_endpoints,
            outcome_type="continuous",
            sample_size_info=sample_info
        )

        st.session_state.generated_sections['methods'] = methods_text

    # Show generated text
    if 'methods' in st.session_state.generated_sections:
        st.markdown("#### Сгенерированный текст")
        st.markdown(st.session_state.generated_sections['methods'])

        st.download_button(
            "📥 Скачать раздел",
            st.session_state.generated_sections['methods'],
            file_name="methods.md",
            mime="text/markdown"
        )


def render_results_section():
    """Render results section with data analysis."""
    st.markdown("### Результаты")

    if st.session_state.uploaded_data is None:
        st.warning("Для анализа результатов загрузите данные на шаге 5.")
        return

    df = st.session_state.uploaded_data

    st.markdown("#### Загруженные данные")
    st.write(f"Размер: {len(df)} записей, {len(df.columns)} переменных")

    # Column selector
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    st.markdown("#### Анализ данных")

    analysis_type = st.selectbox(
        "Тип анализа",
        options=[
            "descriptive", "compare_means", "compare_proportions",
            "correlation", "baseline_table"
        ],
        format_func=lambda x: {
            "descriptive": "Описательная статистика",
            "compare_means": "Сравнение средних",
            "compare_proportions": "Сравнение пропорций",
            "correlation": "Корреляция",
            "baseline_table": "Таблица 1 (характеристики)"
        }.get(x, x)
    )

    analyzer = DataAnalyzer(df)

    if analysis_type == "descriptive":
        col = st.selectbox("Переменная", options=numeric_cols)
        group_col = st.selectbox("Группировать по", options=["Нет"] + categorical_cols)

        if st.button("Анализировать"):
            result = analyzer.describe_continuous(
                col,
                group_by=group_col if group_col != "Нет" else None
            )
            st.markdown("**Результат:**")
            st.dataframe(result.table_data)
            st.info(result.interpretation)

    elif analysis_type == "compare_means":
        col = st.selectbox("Переменная для сравнения", options=numeric_cols)
        group_col = st.selectbox("Группирующая переменная", options=categorical_cols)

        if st.button("Анализировать"):
            try:
                result = analyzer.compare_means(col, group_col)
                st.dataframe(result.table_data)
                st.info(result.interpretation)
            except Exception as e:
                st.error(f"Ошибка: {e}")

    elif analysis_type == "baseline_table":
        continuous = st.multiselect("Непрерывные переменные", options=numeric_cols)
        categorical = st.multiselect("Категориальные переменные", options=categorical_cols)
        group_col = st.selectbox("Группировать по", options=["Нет"] + categorical_cols)

        if st.button("Создать таблицу"):
            table = analyzer.baseline_table(
                continuous,
                categorical,
                group_col if group_col != "Нет" else None
            )
            st.dataframe(table, use_container_width=True)

            # Download
            csv = table.to_csv(index=False)
            st.download_button("📥 Скачать таблицу", csv, "table1.csv", "text/csv")


def render_discussion_section():
    """Render discussion section."""
    st.markdown("### Обсуждение")

    pico = st.session_state.pico
    study_type = st.session_state.study_type

    st.markdown("#### Основные результаты")
    st.markdown("Введите основные находки вашего исследования:")

    main_findings = []
    for i in range(3):
        finding = st.text_input(f"Находка {i+1}", key=f"finding_{i}")
        if finding:
            main_findings.append(finding)

    secondary_findings = st.text_area("Дополнительные находки (через запятую)")
    secondary_list = [s.strip() for s in secondary_findings.split(",") if s.strip()]

    if st.button("Сгенерировать обсуждение", type="primary"):
        discussion = generate_discussion_structure(
            study_type=study_type,
            pico=pico.to_dict(),
            main_findings=main_findings,
            secondary_findings=secondary_list
        )
        st.session_state.generated_sections['discussion'] = discussion

    if 'discussion' in st.session_state.generated_sections:
        st.markdown("#### Сгенерированный текст")
        st.markdown(st.session_state.generated_sections['discussion'])

        st.download_button(
            "📥 Скачать раздел",
            st.session_state.generated_sections['discussion'],
            file_name="discussion.md"
        )


def render_conclusion_section():
    """Render conclusion section."""
    st.markdown("### Заключение")

    pico = st.session_state.pico
    study_type = st.session_state.study_type

    main_findings = st.text_area("Основные выводы", height=100)
    clinical_implications = st.text_area("Клиническое значение", height=100)

    findings_list = [f.strip() for f in main_findings.split("\n") if f.strip()]
    implications_list = [i.strip() for i in clinical_implications.split("\n") if i.strip()]

    if st.button("Сгенерировать заключение"):
        conclusion = generate_conclusion(
            study_type=study_type,
            pico=pico.to_dict(),
            main_findings=findings_list,
            clinical_implications=implications_list
        )
        st.session_state.generated_sections['conclusion'] = conclusion

    if 'conclusion' in st.session_state.generated_sections:
        st.markdown(st.session_state.generated_sections['conclusion'])


def render_abstract_section():
    """Render abstract section."""
    st.markdown("### Резюме (Abstract)")

    pico = st.session_state.pico
    study_type = st.session_state.study_type

    methods_summary = st.text_area("Краткое описание методов", height=80)
    results_summary = st.text_area("Краткое описание результатов", height=80)
    conclusion_summary = st.text_area("Краткое заключение", height=80)

    if st.button("Сгенерировать резюме"):
        abstract = generate_abstract(
            study_type=study_type,
            pico=pico.to_dict(),
            methods_summary=methods_summary,
            results_summary=results_summary,
            conclusion_summary=conclusion_summary
        )
        st.session_state.generated_sections['abstract'] = abstract

    if 'abstract' in st.session_state.generated_sections:
        st.markdown(st.session_state.generated_sections['abstract'])


def export_project():
    """Export project data as JSON."""
    # Prepare sample size result for serialization
    sample_size_data = None
    if st.session_state.sample_size_result:
        ssr = st.session_state.sample_size_result
        sample_size_data = {
            'n_per_group': ssr.n_per_group,
            'n_total': ssr.n_total,
            'power': ssr.power,
            'alpha': ssr.alpha,
            'parameters': ssr.parameters,
            'formula_description': ssr.formula_description,
            'assumptions': ssr.assumptions,
            'recommendation': ssr.recommendation,
        }

    project_data = {
        'version': '1.0',
        'current_step': st.session_state.current_step,
        'study_type': st.session_state.study_type,
        'pico': st.session_state.pico.to_dict(),
        'primary_endpoint': st.session_state.primary_endpoint,
        'secondary_endpoints': st.session_state.secondary_endpoints,
        'sample_size_result': sample_size_data,
        'generated_sections': st.session_state.generated_sections,
    }

    json_str = json.dumps(project_data, ensure_ascii=False, indent=2)
    return json_str


def load_project(uploaded_file):
    """Load project from JSON file."""
    try:
        project_data = json.load(uploaded_file)

        # Restore state
        st.session_state.current_step = project_data.get('current_step', 0)
        st.session_state.study_type = project_data.get('study_type')
        st.session_state.primary_endpoint = project_data.get('primary_endpoint')
        st.session_state.secondary_endpoints = project_data.get('secondary_endpoints', [])
        st.session_state.generated_sections = project_data.get('generated_sections', {})

        # Restore PICO
        pico_data = project_data.get('pico', {})
        st.session_state.pico = PICOQuestion.from_dict(pico_data)

        # Restore sample size (basic info, not full object)
        sample_data = project_data.get('sample_size_result')
        if sample_data:
            from modules.sample_size import SampleSizeResult, DesignType
            st.session_state.sample_size_result = SampleSizeResult(
                n_per_group=sample_data['n_per_group'],
                n_total=sample_data['n_total'],
                power=sample_data['power'],
                alpha=sample_data['alpha'],
                design_type=DesignType.TWO_MEANS,  # Default, actual type not critical for display
                parameters=sample_data.get('parameters', {}),
                formula_description=sample_data.get('formula_description', ''),
                assumptions=sample_data.get('assumptions', ''),
                recommendation=sample_data.get('recommendation', ''),
            )

        return True, "Проект успешно загружен!"
    except Exception as e:
        return False, f"Ошибка загрузки: {str(e)}"


def main():
    """Main application."""
    init_session_state()

    # Header
    st.markdown('<p class="main-header">📝 Medical Paper Writer</p>', unsafe_allow_html=True)
    st.markdown("Помощник для написания медицинских научных статей и диссертаций")

    render_sidebar()

    # Render current step
    step = st.session_state.current_step

    if step == 0:
        render_step_1_study_type()
    elif step == 1:
        render_step_2_pico()
    elif step == 2:
        render_step_3_endpoints()
    elif step == 3:
        render_step_4_sample_size()
    elif step == 4:
        render_step_5_database()
    elif step == 5:
        render_step_6_writing()


if __name__ == "__main__":
    main()
