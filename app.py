import os
import yaml
from smolagents import (
    GradioUI,
    CodeAgent,
    InferenceClientModel,
    FinalAnswerTool,
    PythonInterpreterTool
)
from tools.company_names import CompanyNameMatcher
from tools.company_checker import CompanyNameChecker

# Load model with HF token
model = InferenceClientModel(
    model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
    api_key=os.environ.get("HUGGINGFACEHUB_API_TOKEN")
)

# Load tools
final_answer = FinalAnswerTool()      # built-in tool
interp_tool = PythonInterpreterTool()
company_tool = CompanyNameMatcher()
check_tool = CompanyNameChecker()

# Load prompts
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(CURRENT_DIR, "prompts.yaml"), 'r') as f:
    prompt_templates = yaml.safe_load(f)

# Create the agent
agent = CodeAgent(
    model=model,
    tools=[company_tool, final_answer, interp_tool, check_tool],
    managed_agents=[],
    max_steps=10,
    verbosity_level=1,
    prompt_templates=prompt_templates
)

# Launch Gradio UI
if __name__ == "__main__":
    GradioUI(agent).launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
        # 🔴 stream_output removed for Gradio 5.x
    )

