# Company Name Matcher Agentic App
This is a Dockerized AI agent app built using smolagents and Gradio as well as the Qwen/Qwen2.5-Coder-32B-Instruct model from Hugging Face. The app provides an interactive AI agent accessible in your browser via Gradio.



## Features

 - Interactive AI agent with multiple tools:
	- Company name matching
	- Company checker
	- Python interpreter
	- Final answer tool
- Fully containerized via Docker
- Works locally in your browser
- Configurable via .env file for Hugging Face API token




## Requirements

Docker installed
Hugging Face account with an API token



## Installation

### 1. Clone the repository:
```console
git clone https://github.com/your-username/my-agentic-app.git
cd my-agentic-app
```

### 2. Create a .env file
Copy the example .env file:
```console
cp .env.example .env
```
Open .env and add your Hugging Face API token:
HUGGINGFACEHUB_API_TOKEN=hf_your_token_here


### 3. Build and Run the Docker Container
Build the Docker image:
```console
docker build --no-cache -t my-gradio-app .
```
Run the container:
```console
docker run --dns 8.8.8.8 --env-file .env -p 7860:7860 my-gradio-app
```
Open your browser and go to:
http://localhost:7860
