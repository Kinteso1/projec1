# Medical Paper Writer modules
from .study_types import STUDY_TYPES, StudyType, get_study_type, get_study_types_by_category
from .pico import PICOQuestion, PICOType, PICO_EXAMPLES, PICO_HINTS, suggest_outcomes_for_condition
from .endpoints import Endpoint, EndpointType, EndpointCategory, suggest_endpoints, STATISTICAL_TESTS
from .sample_size import (
    DesignType, SampleSizeResult,
    calculate_two_means, calculate_two_proportions,
    calculate_case_control, calculate_survival,
    calculate_diagnostic_accuracy, calculate_noninferiority
)
from .database_template import (
    DatabaseTemplateGenerator, Variable, VariableType,
    DEMOGRAPHIC_VARIABLES, CLINICAL_VARIABLES, VITAL_SIGNS,
    TREATMENT_VARIABLES, OUTCOME_VARIABLES, LABORATORY_VARIABLES,
    create_template_for_study
)
from .literature import Reference, PubMedSearcher, search_for_literature_review, generate_search_strategy
from .methods import generate_full_methods_section, METHODS_CHECKLISTS
from .results import DataAnalyzer, AnalysisType, suggest_analyses
from .discussion import generate_discussion_structure, generate_conclusion, generate_abstract
from .ai_helper import AIHelper, get_fallback_suggestions

__all__ = [
    'STUDY_TYPES', 'StudyType', 'get_study_type', 'get_study_types_by_category',
    'PICOQuestion', 'PICOType', 'PICO_EXAMPLES', 'PICO_HINTS',
    'Endpoint', 'EndpointType', 'suggest_endpoints',
    'DesignType', 'SampleSizeResult',
    'DatabaseTemplateGenerator', 'create_template_for_study',
    'Reference', 'PubMedSearcher', 'search_for_literature_review',
    'generate_full_methods_section',
    'DataAnalyzer', 'suggest_analyses',
    'generate_discussion_structure', 'generate_conclusion',
    'AIHelper',
]
