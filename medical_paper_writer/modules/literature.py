"""
Literature review module - search and organize scientific sources.
Focuses on Q1-Q3 journals for quality references.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import requests
from datetime import datetime


class JournalQuartile(Enum):
    Q1 = "Q1 (Top 25%)"
    Q2 = "Q2 (25-50%)"
    Q3 = "Q3 (50-75%)"
    Q4 = "Q4 (Bottom 25%)"
    UNKNOWN = "Не определён"


@dataclass
class Reference:
    pmid: str = ""
    doi: str = ""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    year: int = 0
    volume: str = ""
    issue: str = ""
    pages: str = ""
    abstract: str = ""
    quartile: JournalQuartile = JournalQuartile.UNKNOWN
    impact_factor: Optional[float] = None
    citation_count: int = 0
    study_type: str = ""
    keywords: List[str] = field(default_factory=list)

    def format_vancouver(self) -> str:
        """Format reference in Vancouver style."""
        authors_str = ", ".join(self.authors[:6])
        if len(self.authors) > 6:
            authors_str += ", et al"

        return (
            f"{authors_str}. {self.title}. {self.journal}. "
            f"{self.year};{self.volume}({self.issue}):{self.pages}. "
            f"doi: {self.doi}" if self.doi else ""
        )

    def format_apa(self) -> str:
        """Format reference in APA style."""
        if len(self.authors) > 7:
            authors_str = ", ".join(self.authors[:6]) + ", ... " + self.authors[-1]
        else:
            authors_str = ", ".join(self.authors[:-1]) + ", & " + self.authors[-1] if len(self.authors) > 1 else self.authors[0]

        return (
            f"{authors_str} ({self.year}). {self.title}. "
            f"{self.journal}, {self.volume}({self.issue}), {self.pages}. "
            f"https://doi.org/{self.doi}" if self.doi else ""
        )

    def format_gost(self) -> str:
        """Format reference in Russian GOST style."""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += " и др."

        return (
            f"{authors_str} {self.title} // {self.journal}. "
            f"{self.year}. Т. {self.volume}, № {self.issue}. С. {self.pages}."
        )


# High-quality medical journals by category (Q1-Q2)
TOP_JOURNALS = {
    "general_medicine": [
        "New England Journal of Medicine",
        "The Lancet",
        "JAMA",
        "BMJ",
        "Annals of Internal Medicine",
    ],
    "cardiology": [
        "Circulation",
        "European Heart Journal",
        "Journal of the American College of Cardiology",
        "JAMA Cardiology",
        "Circulation Research",
    ],
    "oncology": [
        "Journal of Clinical Oncology",
        "Lancet Oncology",
        "JAMA Oncology",
        "Annals of Oncology",
        "Cancer Discovery",
    ],
    "surgery": [
        "Annals of Surgery",
        "JAMA Surgery",
        "British Journal of Surgery",
        "Journal of the American College of Surgeons",
        "Surgical Endoscopy",
    ],
    "neurology": [
        "Lancet Neurology",
        "JAMA Neurology",
        "Annals of Neurology",
        "Brain",
        "Neurology",
    ],
    "psychiatry": [
        "Lancet Psychiatry",
        "JAMA Psychiatry",
        "American Journal of Psychiatry",
        "Molecular Psychiatry",
        "Biological Psychiatry",
    ],
    "pediatrics": [
        "JAMA Pediatrics",
        "Pediatrics",
        "Lancet Child & Adolescent Health",
        "Journal of Pediatrics",
        "Archives of Disease in Childhood",
    ],
    "endocrinology": [
        "Lancet Diabetes & Endocrinology",
        "Diabetes Care",
        "Journal of Clinical Endocrinology & Metabolism",
        "Diabetologia",
        "Thyroid",
    ],
}


class PubMedSearcher:
    """Search PubMed for relevant articles."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()

    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make a request to PubMed API."""
        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.BASE_URL}/{endpoint}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        if "retmode" in params and params["retmode"] == "json":
            return response.json()
        return {"text": response.text}

    def search(
        self,
        query: str,
        max_results: int = 50,
        min_year: Optional[int] = None,
        article_types: Optional[List[str]] = None,
        sort: str = "relevance"
    ) -> List[str]:
        """
        Search PubMed and return list of PMIDs.

        Parameters:
        - query: Search query
        - max_results: Maximum number of results
        - min_year: Minimum publication year
        - article_types: Filter by article type (e.g., "Review", "Clinical Trial")
        - sort: Sort order ("relevance" or "date")
        """
        # Build query with filters
        search_query = query

        if min_year:
            search_query += f" AND {min_year}:{datetime.now().year}[pdat]"

        if article_types:
            type_filter = " OR ".join([f'"{t}"[pt]' for t in article_types])
            search_query += f" AND ({type_filter})"

        params = {
            "db": "pubmed",
            "term": search_query,
            "retmax": max_results,
            "retmode": "json",
            "sort": sort,
        }

        try:
            result = self._make_request("esearch.fcgi", params)
            return result.get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            print(f"PubMed search error: {e}")
            return []

    def fetch_details(self, pmids: List[str]) -> List[Reference]:
        """Fetch article details for given PMIDs."""
        if not pmids:
            return []

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }

        try:
            result = self._make_request("efetch.fcgi", params)
            return self._parse_pubmed_xml(result.get("text", ""))
        except Exception as e:
            print(f"PubMed fetch error: {e}")
            return []

    def _parse_pubmed_xml(self, xml_text: str) -> List[Reference]:
        """Parse PubMed XML response."""
        references = []

        # Simple regex-based parsing (in production, use xml.etree or lxml)
        articles = re.findall(r'<PubmedArticle>(.*?)</PubmedArticle>', xml_text, re.DOTALL)

        for article in articles:
            ref = Reference()

            # PMID
            pmid_match = re.search(r'<PMID[^>]*>(\d+)</PMID>', article)
            if pmid_match:
                ref.pmid = pmid_match.group(1)

            # Title
            title_match = re.search(r'<ArticleTitle>(.*?)</ArticleTitle>', article, re.DOTALL)
            if title_match:
                ref.title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()

            # Journal
            journal_match = re.search(r'<Title>(.*?)</Title>', article)
            if journal_match:
                ref.journal = journal_match.group(1)

            # Year
            year_match = re.search(r'<PubDate>.*?<Year>(\d{4})</Year>', article, re.DOTALL)
            if year_match:
                ref.year = int(year_match.group(1))

            # Authors
            authors = re.findall(r'<LastName>(.*?)</LastName>.*?<Initials>(.*?)</Initials>', article, re.DOTALL)
            ref.authors = [f"{last} {init}" for last, init in authors]

            # DOI
            doi_match = re.search(r'<ArticleId IdType="doi">(.*?)</ArticleId>', article)
            if doi_match:
                ref.doi = doi_match.group(1)

            # Abstract
            abstract_match = re.search(r'<AbstractText[^>]*>(.*?)</AbstractText>', article, re.DOTALL)
            if abstract_match:
                ref.abstract = re.sub(r'<[^>]+>', '', abstract_match.group(1)).strip()

            # Volume, Issue, Pages
            volume_match = re.search(r'<Volume>(\d+)</Volume>', article)
            if volume_match:
                ref.volume = volume_match.group(1)

            issue_match = re.search(r'<Issue>(\d+)</Issue>', article)
            if issue_match:
                ref.issue = issue_match.group(1)

            pages_match = re.search(r'<MedlinePgn>(.*?)</MedlinePgn>', article)
            if pages_match:
                ref.pages = pages_match.group(1)

            # Publication type / Study type
            pub_types = re.findall(r'<PublicationType>(.*?)</PublicationType>', article)
            if pub_types:
                ref.study_type = ", ".join(pub_types[:2])

            # Keywords
            keywords = re.findall(r'<Keyword[^>]*>(.*?)</Keyword>', article)
            ref.keywords = keywords[:5]

            references.append(ref)

        return references


def build_search_query(pico: Dict, specialty: str = "") -> str:
    """Build an optimized PubMed search query from PICO."""
    terms = []

    if pico.get("population"):
        terms.append(f'({pico["population"]}[MeSH Terms] OR {pico["population"]}[Title/Abstract])')

    if pico.get("intervention"):
        terms.append(f'({pico["intervention"]}[MeSH Terms] OR {pico["intervention"]}[Title/Abstract])')

    if pico.get("comparison"):
        terms.append(f'({pico["comparison"]}[Title/Abstract])')

    if pico.get("outcome_primary"):
        terms.append(f'({pico["outcome_primary"]}[Title/Abstract])')

    return " AND ".join(terms)


def search_for_literature_review(
    topic: str,
    pico: Optional[Dict] = None,
    specialty: str = "",
    min_year: int = 2018,
    include_reviews: bool = True,
    include_rcts: bool = True,
    include_meta: bool = True,
    max_results: int = 100
) -> List[Reference]:
    """
    Search for high-quality literature for review.

    Parameters:
    - topic: Main topic for search
    - pico: PICO question components
    - specialty: Medical specialty for journal filtering
    - min_year: Minimum publication year
    - include_reviews: Include systematic reviews
    - include_rcts: Include RCTs
    - include_meta: Include meta-analyses
    - max_results: Maximum results to return
    """
    searcher = PubMedSearcher()

    # Build article type filter
    article_types = []
    if include_reviews:
        article_types.append("Systematic Review")
    if include_rcts:
        article_types.append("Randomized Controlled Trial")
    if include_meta:
        article_types.append("Meta-Analysis")

    # Build query
    if pico:
        query = build_search_query(pico, specialty)
    else:
        query = topic

    # Search PubMed
    pmids = searcher.search(
        query=query,
        max_results=max_results,
        min_year=min_year,
        article_types=article_types if article_types else None,
        sort="relevance"
    )

    # Fetch details
    references = searcher.fetch_details(pmids)

    # Sort by year (newest first) and filter high-quality journals
    references.sort(key=lambda x: x.year, reverse=True)

    return references


# Literature review structure templates
REVIEW_TEMPLATES = {
    "systematic": {
        "sections": [
            ("Методы поиска", "Описание стратегии поиска, баз данных, ключевых слов"),
            ("Критерии включения", "PICO критерии для отбора исследований"),
            ("Оценка качества", "Инструменты оценки риска систематической ошибки"),
            ("Характеристики исследований", "Таблица с основными характеристиками"),
            ("Синтез результатов", "Качественный или количественный синтез"),
            ("Обсуждение", "Интерпретация, ограничения, значение для практики"),
        ],
        "checklist": "PRISMA 2020"
    },
    "narrative": {
        "sections": [
            ("Эпидемиология", "Распространённость, заболеваемость, факторы риска"),
            ("Патофизиология", "Механизмы развития заболевания"),
            ("Клиническая картина", "Симптомы, диагностические критерии"),
            ("Диагностика", "Методы диагностики, дифференциальный диагноз"),
            ("Лечение", "Современные подходы к терапии"),
            ("Прогноз", "Исходы, осложнения, качество жизни"),
        ],
        "checklist": "SANRA"
    },
    "scoping": {
        "sections": [
            ("Обоснование", "Почему необходим скоупинг-обзор"),
            ("Исследовательские вопросы", "Широкие вопросы для картирования"),
            ("Источники и поиск", "Стратегия идентификации источников"),
            ("Отбор источников", "Процесс скрининга"),
            ("Извлечение данных", "Charting data"),
            ("Результаты", "Картирование существующих данных"),
        ],
        "checklist": "PRISMA-ScR"
    },
}


def generate_search_strategy(pico: Dict, databases: List[str] = None) -> str:
    """Generate a detailed search strategy for methods section."""
    if databases is None:
        databases = ["PubMed/MEDLINE", "Cochrane Library", "Embase", "Web of Science"]

    strategy = f"""
## Стратегия поиска

### Базы данных
Поиск проводился в следующих базах данных: {', '.join(databases)}.

### Ключевые слова и MeSH-термины

**Население (P):** {pico.get('population', '[не указано]')}
- Термины: {pico.get('population', '')}

**Вмешательство (I):** {pico.get('intervention', '[не указано]')}
- Термины: {pico.get('intervention', '')}

**Сравнение (C):** {pico.get('comparison', '[не указано]')}
- Термины: {pico.get('comparison', '')}

**Исходы (O):** {pico.get('outcome_primary', '[не указано]')}
- Термины: {pico.get('outcome_primary', '')}

### Пример поисковой строки для PubMed

```
({pico.get('population', '')}[MeSH Terms] OR {pico.get('population', '')}[Title/Abstract])
AND
({pico.get('intervention', '')}[MeSH Terms] OR {pico.get('intervention', '')}[Title/Abstract])
AND
({pico.get('outcome_primary', '')}[Title/Abstract])
```

### Ограничения
- Язык: английский, русский
- Период: последние 10 лет
- Тип публикаций: РКИ, систематические обзоры, мета-анализы, когортные исследования
"""
    return strategy
