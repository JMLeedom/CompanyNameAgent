########################################################
# Description
########################################################
# Module for specifying what the matching system returns

########################################################



########################################################
# Imports & Settings
########################################################
from dataclasses import asdict, dataclass
from typing import Literal
########################################################


########################################################
# Classes
########################################################
Decision = Literal[
    "MATCH",
    "POSSIBLE_MATCH",
    "NO_MATCH",
]

@dataclass(frozen=True)
class Candidate:
    """
    A candidate is a proposed match, and 
    contains the following information:
    {
        "company_id": str,
        "canonical_name": str,
        "score": float
    }
    This class has a to_dict() method to convert 
    the dataclass to a dictionary.
    """
    company_id: str
    canonical_name: str
    score: float

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass(frozen=True)
class SearchResult:
    """
    Contains the complete results of a search query, including the query string,
    the list of candidates, the decision, and the reason for the decision.
    An example search result contains:
    {
        "query": "JPMorgan Chase",
        "candidates": [
            {
                "company_id": "12345",
                "canonical_name": "JPMorgan Chase & Co.",
                "score": 95.0
            }
        ],
        "decision": "MATCH",
        "reason": "Similarity score exceeds the automatic-match threshold"
    }
    """
    query:str
    candidates: list[Candidate]
    decision: Decision
    reason: str

    def to_dict(self) -> dict:
        return{
            "query": self.query,
            "candidates": [
                candidate.to_dict() for candidate in self.candidates
            ],
            "decision": self.decision,
            "reason": self.reason
        }

@dataclass(frozen=True)
class ComparisonResult:
    """
    Contains the results of a pairwise comparison between two names, including the names,
    the similarity score, the decision, and the reason for the decision.
    An example comparison results contains
    {
        "name_one": "J.P. Morgan",
        "name_two": "JPMOrgan",
        "score": 74.0,
        "decision": "POSSIBLE_MATCH",
        "reason": "similarity score falls within the review range"
    }
    """
    name_one: str
    name_two: str
    score: float
    decision: Decision
    reason: str

    def to_dict(self)-> dict:
        return asdict(self)
    
########################################################