########################################################
# Description
########################################################
# Module containing pure decision logic, kept apart from agents
# Keeping the policy separate has several advantages:
# we can easily test threshold behaviour
# thresholds can be adjusted without touching matching code
# LLM cannot silently invent its own policy 
# pairwise comparison and database search can follow different rules
# replace simple policy with a calibrated classifier
########################################################



########################################################
# Imports & Settings
########################################################
from dataclasses import dataclass
from .schemas import Decision
########################################################



########################################################
# Classes
########################################################
@dataclass(frozen=True)
class DecisionPolicy:
    """
    Dataclass that encapsulates the decision policy for classifying similarity scores into decisions.
    It contains thresholds for automatic matches, possible matches, and the minimum margin required to distinguish between
    candidates. The class provides methods to classify pairwise comparisons and search results based on these thresholds.
    """
    match_threshold: float = 85.0
    possible_match_threshold: float = 65.0
    minimum_margin:float = 10.0

    def classify_pair(self, score:float) -> tuple[Decision, str]:
        if score >= self.match_threshold:
            return(
                "MATCH",
                "Similarity score exceeds the automatic-match threshold"
            )
        if score >= self.possible_match_threshold:
            return(
                "POSSIBLE_MATCH",
                "Similarity score falls within the review range."
            )
        return (
            "NO_MATCH",
            "Similarity score is below the minimum review threshold"
        )
    
    def classify_search(
            self,
            best_score: float,
            second_best_score: float | None = None,
    ) -> tuple[Decision, str]:
        if best_score < self.possible_match_threshold:
            return(
                "NO_MATCH",
                "No candidate exceeds the minimum review threshold"
            )
        if (
            second_best_score is not None
            and best_score - second_best_score < self.minimum_margin
        ):
            return(
                "POSSIBLE_MATCH",
                "The leading candidates are too close to distinguish reliably"
            )
        
        if best_score >= self.match_threshold:
            return(
                "MATCH",
                "The best candidate exceeds the automatic-match threshold"
            )
        return (
            "POSSIBLE_MATCH",
            "The best candidate requires manual review"
        )
    def __post_init__(self) -> None:
        if not (
            0 <= self.possible_match_threshold <= self.match_threshold <= 100
        ):
            raise ValueError(
                "Thresholds must satisfy: "
                "0 <= possible_match_threshold <= match_threshold <= 100"
            )
        if self.minimum_margin < 0:
            raise ValueError(
                "minimum_margin cannot be negative"
            )
########################################################