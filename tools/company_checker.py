from smolagents import Tool

from company_name_agent.matching_service import(
    CompanyMatchingService,
)


class CompanyNameChecker(Tool):
    name = "com_check_tool"

    description = (
        "Compares two company names using deterministic"
        "name-matching methods. Returns their similarity score, "
        "decision, and explanation. The score is not a probability"
    )

    inputs = {
        "company_name_one": {
            "type": "string",
            "description": "First company name to compare."
        },
        "company_name_two": {
            "type": "string",
            "description": "Second comapny name to compare."
        },
    }

    output_type = "object"

    def __init__(
            self,
            matching_service: CompanyMatchingService
    ) -> None:
        self.matching_service = matching_service
        super().__init__()

    def forward(
            self,
            company_name_one: str,
            company_name_two: str,
    ) -> dict:
        result = self.matching_service.compare(
            name_one = company_name_one,
            name_two=company_name_two
        )

        return result.to_dict()