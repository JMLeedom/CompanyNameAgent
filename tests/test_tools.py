from pathlib import Path

import pytest

from company_name_agent.matching_service import (
    CompanyMatchingService,
)
from tools.company_checker import CompanyNameChecker
from tools.company_names import CompanyNameMatcher


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "canonical_companies.csv"
)


@pytest.fixture(scope="module")
def service():
    return CompanyMatchingService(
        company_data_path=DATA_PATH,
        max_candidates=3,
    )


def test_database_search_tool(service):
    tool = CompanyNameMatcher(service)

    result = tool.forward(
        company_name="JPMOrgan",
    )

    assert isinstance(result, dict)
    assert result["query"] == "JPMOrgan"
    assert result["candidates"][0][
        "company_id"
    ] == "bank_005"
    assert result["decision"] == "POSSIBLE_MATCH"


def test_pairwise_comparison_tool(service):
    tool = CompanyNameChecker(service)

    result = tool.forward(
        company_name_one="JPMorgan Chase",
        company_name_two="Crédit Agricole",
    )

    assert isinstance(result, dict)
    assert result["decision"] == "NO_MATCH"
    assert 0 <= result["score"] <= 100