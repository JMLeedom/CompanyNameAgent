import os
import yaml
from smolagents import (
    GradioUI,
    CodeAgent,
    InferenceClientModel,
#    FinalAnswerTool,
#    PythonInterpreterTool
)
from company_name_agent.matching_service import CompanyMatchingService
from tools.company_names import CompanyNameMatcher
from tools.company_checker import CompanyNameChecker
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(CURRENT_DIR, ".env"))


hf_token = os.environ.get("HUGGINGFACEHUB_API_TOKEN")

if not hf_token:
    raise RuntimeError(
        "HUGGINGFACEHUB_API_TOKEN was not found. "
        "Add it to the project's .env file."
    )

model = InferenceClientModel(
    model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
    api_key=hf_token,
)


#load model with HF token
model = InferenceClientModel(
    model_id="Qwen/Qwen3-Next-80B-A3B-Instruct",
    provider="deepinfra",
    token=hf_token,
    max_tokens=2048,
)


# create one shared matching service
matching_service = CompanyMatchingService(
    company_data_path = os.path.join(
        CURRENT_DIR,
        "data",
        "canonical_companies.csv"
    ),
    max_candidates=3
)

# give both tools the shared service
#final_answer = FinalAnswerTool
#interp_tool = PythonInterpreterTool()

company_tool = CompanyNameMatcher(
    matching_service=matching_service
)

check_tool = CompanyNameChecker(
    matching_service=matching_service
)


# load prompts
#with open(
#    os.path.join(CURRENT_DIR, "prompts.yaml"),
#    "r",
#    encoding="utf-8"
#) as file:
#    prompt_templates = yaml.safe_load(file)



AGENT_INSTRUCTIONS = """
You are an entity-resolution assistant.

Use com_check_tool when comparing two supplied company names.
Use company_tool when searching for a name in the canonical database.

Treat the decision returned by the relevant tool call as authoritative:

- MATCH: report that the names match.
- POSSIBLE_MATCH: report only a possible match and recommend manual review.
- NO_MATCH: report that no sufficiently strong match was found.

Never upgrade POSSIBLE_MATCH to MATCH based on intuition, prior conversation,
or the candidate name. Never override NO_MATCH.

A score is a string-similarity score, not a probability or confidence
percentage. Include the decision, candidate or compared names, score, and
reason in the final response. Do not answer with only "Yes" or "No".
"""

# create agent
agent = CodeAgent(
    model=model,
    tools=[
        company_tool,
        check_tool,
        #final_answer,
        #interp_tool
    ],
    managed_agents=[],
    max_steps=10,
    verbosity_level=1,
    instructions=AGENT_INSTRUCTIONS
    #prompt_templates=prompt_templates
)


# launch gradio
if __name__ == "__main__":
    GradioUI(agent).launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )