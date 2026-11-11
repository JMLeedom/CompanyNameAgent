from pathlib import Path
import pytest
from company_name_agent.matching_service import (
    CompanyMatchingService,
)



PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = (
    PROJECT_ROOT/ "data" / "canonical_companies.csv"
)

@pytest.fixture(scope='module')
def service() -> CompanyMatchingService:
    return CompanyMatchingService(
        company_data_path=DATA_PATH,
        max_candidates=3,
    )

def test_exact_datanase_match(service):
    result = service.search("JPMorgan Chase")

    print(result.to_dict())

    assert result.decision == "MATCH"
    assert 1 <= len(result.candidates) <= 3

    candidate = result.candidates[0]

    assert candidate.company_id == "bank_005"
    assert candidate.canonical_name == "JPMorgan Chase"
    assert candidate.score == pytest.approx(100.0)

def test_misspelled_database_match(service):
    result = service.search("JPMOrgan")

    candidate = result.candidates[0]

    assert candidate.company_id == "bank_005"
    assert candidate.canonical_name == "JPMorgan Chase"
    assert result.decision == "POSSIBLE_MATCH"



def test_unrelated_name_is_rejected(service):
    result = service.search(
        "Lasarium Mining Corporation"
    )

    assert result.decision == "NO_MATCH"
    assert result.candidates[0].score < 65.0


def test_different_pair_is_rejected(service):
    result = service.compare(
        "JPMorgan Chase",
        "Crédit Agricole",
    )

    assert result.decision == "NO_MATCH"
    assert 0 <= result.score <= 100


def test_canonical_data_is_not_mutated(service):
    service.search("JPMOrgan")

    jpmorgan = service.companies.loc[
        service.companies["company_id"] == "bank_005",
        "canonical_name",
    ].iloc[0]

    assert jpmorgan == "JPMorgan Chase"


def test_result_serialization(service):
    result = service.search("HSBC")
    output = result.to_dict()

    assert output["query"] == "HSBC"
    assert isinstance(output["candidates"], list)
    assert output["candidates"][0][
        "company_id"
    ] == "bank_008"

def test_candidates_are_ranked(service):
    result = service.search("JPMOrgan")

    assert 1 <= len(result.candidates) <= 3

    scores = [
        candidate.score
        for candidate in result.candidates
    ]

    assert scores == sorted(scores, reverse=True)