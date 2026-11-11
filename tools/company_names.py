from smolagents import Tool
from company_name_agent.matching_service import (
    CompanyMatchingService,
)

class CompanyNameMatcher(Tool):
    name = "company_tool"

    description = (
        "Searches the canonical company database for a noisy, "
        "misspelled, or abbreviated company name. Returns the "
        "canidate, similarity score, deterministic decision, "
        "and explanation."
    )

    inputs = {
        "company_name": {
            "type": "string",
            "description": (
                "Company name to search for in the "
                "canonical database."
            ),
        }
    }

    output_type = "object"

    def __init__(
            self,
            matching_service: CompanyMatchingService,
    ) -> None:
        self.matching_service = matching_service
        super().__init__()

    def forward(
            self,
            company_name: str,
    ) -> dict:
        result = self.matching_service.search(
            query=company_name,
        )

        return result.to_dict()