########################################################
# Description
########################################################
# Module that serves as the central application component:
# loads the canonical company data
# initializes and prepares NameMatcher
# validate user inputs
# perform pairwise comparisons
# retrieve top-k database candidates
# ask DecisionPolicy to classify result
# Return result schemas
########################################################



########################################################
# Imports & Settings
########################################################
from pathlib import Path
import pandas as pd
from name_matching.name_matcher import NameMatcher


from .decision_policy import DecisionPolicy
from .schemas import Candidate, ComparisonResult, SearchResult
########################################################




########################################################
# Classes
########################################################
class CompanyMatchingService:
    """
    Service class that provides methods for comparing company names and searching for potential matches
    in a canonical company database. It uses the NameMatcher for similarity scoring and the DecisionPolicy
    for classifying the results based on predefined thresholds.
    """
    def __init__(
            self,
            company_data_path: str | Path,
            policy: DecisionPolicy | None = None,
            max_candidates: int =1,
    ) -> None:
        self.company_data_path = Path(company_data_path)
        self.policy = policy or DecisionPolicy()
        self.max_candidates = max_candidates

        self.companies = self._load_companies()
        self.matcher = self._build_matcher()

    def _load_companies(self) -> pd.DataFrame:
        """
        Load company data from a CSV file.
        Validate that the required columns are present and that there are no missing values.
        
        Output
        -----------
        DataFrame containing the company data.
        """
        companies = pd.read_csv(self.company_data_path)

        required_columns = {
            "company_id",
            "canonical_name",
        }

        missing_columns = required_columns - set(companies.columns)

        if missing_columns:
            raise ValueError(
                f"Canonical company data is missing columns: "
                f"{sorted(missing_columns)}"
            )
        
        companies = companies.dropna(
            subset = ["company_id", "canonical_name"]
        ).copy()

        companies["company_id"] = companies["company_id"].astype(str).str.strip()

        companies["canonical_name"] = (
            companies["canonical_name"].astype(str).str.strip()
                                       )
        
        companies = companies[
            (companies["company_id"] != "")
             & (companies["canonical_name"] != "")
        ]

        if companies["company_id"].duplicated().any():
            raise ValueError("company_id values must be unique.")
        
        return companies.reset_index(drop=True)
    

    
    def _build_matcher(self) -> NameMatcher:
        matcher = self._create_matcher(
            number_of_matches=self.max_candidates,
        )

        matching_data = self.companies[
            ["canonical_name"]
        ].copy()

        matcher.load_and_process_master_data(
            column="canonical_name",
            df_matching_data=matching_data,
            transform=True,
        )

        return matcher
    
    def compare(
            self,
            name_one:str,
            name_two:str,
    ) -> ComparisonResult:
        name_one = self._validate_name(name_one, "name_one")
        name_two = self._validate_name(name_two, "name_two")

        score = self._calculate_pairwise_score(
            name_one,
            name_two
        )

        decision, reason = self.policy.classify_pair(score)

        return ComparisonResult(
            name_one=name_one,
            name_two=name_two,
            score=round(score,2),
            decision=decision,
            reason=reason
        )
    
    def search(
        self,
        query: str,
        top_k: int | None = None,
    ) -> SearchResult:
        
        query = self._validate_name(query, "query")

        if top_k is None:
            top_k = self.max_candidates

        if not isinstance(top_k, int) or isinstance(top_k, bool):
            raise TypeError("top_k must be an integer.")

        if not 1 <= top_k <= self.max_candidates:
            raise ValueError(
                "top_k must be between 1 and "
                f"{self.max_candidates}."
            )

        ranked_candidates = self._find_candidates(
            query=query,
            top_k=self.max_candidates,
        )

        if not ranked_candidates:
            return SearchResult(
                query=query,
                candidates=[],
                decision="NO_MATCH",
                reason=(
                    "No candidate was returned by "
                    "the matching engine."
                ),
            )

        best_score = ranked_candidates[0].score

        second_score = (
            ranked_candidates[1].score
            if len(ranked_candidates) > 1
            else None
        )

        decision, reason = self.policy.classify_search(
            best_score=best_score,
            second_best_score=second_score,
        )

        return SearchResult(
            query=query,
            candidates=ranked_candidates[:top_k],
            decision=decision,
            reason=reason,
        )
    

    def _find_candidates(
        self,
        query: str,
        top_k: int,
    ) -> list[Candidate]:
        """
        Find the top-k candidate matches for a given query string using the NameMatcher.
        Returns a list of Candidate dataclass instances containing the company_id, canonical_name, and score
        """
        query_data = pd.DataFrame(
            {"query_name": [query]}
        )

        matches = self.matcher.match_names(
            to_be_matched=query_data,
            column_matching="query_name"
       )

        if matches.empty:
            return []

        match_row = matches.iloc[0]

        if self.max_candidates == 1:
            result_columns = [
                ("match_index", "score")
            ]
        else:
            result_columns = [
                (
                    f"match_index_{rank}",
                    f"score_{rank}",
                )
                for rank in range(self.max_candidates)
            ]
        candidates = []
        seen_company_ids: set[str] = set()

        for index_column, score_column in result_columns[:top_k]:
            if (
                index_column not in matches.columns
                or score_column not in matches.columns
            ):
                raise RuntimeError(
                    "Unexpected NameMatcher output columns. "
                    f"Received: {matches.columns.tolist()}"
                )

            match_index = match_row[index_column]
            score = match_row[score_column]

            if pd.isna(match_index) or pd.isna(score):
                continue

            company = self.companies.iloc[
                int(match_index)
            ]
            company_id = str(company["company_id"])

            if company_id in seen_company_ids:
                continue

            seen_company_ids.add(company_id)

            candidates.append(
                Candidate(
                    company_id=company_id,
                    canonical_name=str(
                        company["canonical_name"]
                    ),
                score=round(float(score), 2),
                )
            )
        candidates.sort(
            key=lambda candidate: candidate.score,
            reverse=True,
        )
        return candidates


    def _create_matcher(
            self,
            number_of_matches: int = 1,
    ) -> NameMatcher:
        """
        Create an uninitialized NameMatcher with standard Settings
        """

        matcher = NameMatcher(
            number_of_matches=number_of_matches,
            legal_suffixes=True,
            common_words=False,
            top_n=50,
            verbose=False
        )

        matcher.set_distance_metrics(
            [
                "discounted_levenshtein",
                "SSK",
                "fuzzy_wuzzy_token_sort"
            ]
        )

        return matcher
    
    def _calculate_pairwise_score(
            self,
            name_one:str,
            name_two: str,
    ) -> float:
        """
        Calculate the similarity score between two company names
        """
        reference_data = pd.DataFrame(
            {"reference_name": [name_one]}
        )

        query_data = pd.DataFrame(
            {"query_name": [name_two]}
        )

        matcher = self._create_matcher(
            number_of_matches=1
        )

        matcher.load_and_process_master_data(
            column="reference_name",
            df_matching_data=reference_data,
            transform=True
        )

        matches=matcher.match_names(
            to_be_matched=query_data,
            column_matching="query_name"
        )

        if matches.empty:
            raise RuntimeError(
                "NameMatcher did not return a pairwise comparison result."
            )

        if "score" not in matches.columns:
            raise RuntimeError(
                "NameMatcher result does not contain a 'score' column."
            )
        
        score = matches.iloc[0]["score"]

        if pd.isna(score):
            raise RuntimeError(
                "NameMatcher returned a missing pairwise similarity score"
            )
        return float(score)
    
    @staticmethod
    def _validate_name(
        value:str,
        field_name:str
    ) -> str:
        if not isinstance(value,str):
            raise TypeError(f"{field_name} must be a string.")
        
        value = value.strip()

        if not value:
            raise ValueError(f"{field_name} cannot be empty")
        return value
########################################################