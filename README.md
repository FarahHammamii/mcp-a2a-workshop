# Multi-Agent Weather System with MCP and A2A

A sophisticated multi-agent system that demonstrates Model Context Protocol (MCP) integration with Agent-to-Agent (A2A) communication, featuring weather data retrieval and analysis with Vertex AI model-based evaluation.

## Architecture

- **MCP Server**: Provides weather data tools
- **Weather Agent** (Port 8001): Fetches weather data using MCP tools
- **Analysis Agent** (Port 8002): Analyzes weather data and provides recommendations
- **A2A Protocol**: Enables agent-to-agent communication
- **Vertex AI Evaluation**: Model-based evaluation of agent responses using Gemini as judge

## Features

- Real-time weather data retrieval
- Intelligent weather analysis and recommendations
- Agent-to-agent communication
- Model-Based Evaluation: Response quality assessment using Gemini as judge

## Vertex AI Evaluation System

The system includes comprehensive evaluation capabilities using Vertex AI.

### Evaluation Folder Structure

```text
evaluation/
├── __init__.py
├── base_evaluator.py
└── model_based_evaluator.py
```

### Model-Based Evaluator (`model_based_evaluator.py`)

**Purpose**: Evaluates the quality of agent responses using Gemini as a judge.

**Metrics**:
- **Coherence** (1-5): Logical consistency and clarity of the response
- **Fluency** (1-5): Natural language flow and grammar quality
- **Safety** (0-1): Content safety and appropriateness

**Use Case**: Assess whether the agent's final answer is high quality.

## Setup

### Prerequisites

1. Python 3.8+
2. Google Cloud Project (for Vertex AI evaluation)
3. API Keys:
   - Groq API Key
   - Google Cloud credentials (for Vertex AI)

### Installation

1. Clone the repository

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:

```env
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id
```

## Google Cloud Setup (for Vertex AI Evaluation)

1. Create a Google Cloud Project
2. Enable the Vertex AI API
3. Set up authentication:

```bash
gcloud auth application-default login
```

Or set:

```env
GOOGLE_APPLICATION_CREDENTIALS=path_to_service_account.json
```

4. Ensure `GOOGLE_CLOUD_PROJECT` is set in `.env`

## Step-by-Step Usage Guide

### Quick Start

Start the system:

```bash
python run_agents.py
```

This starts:

- MCP Server
- Weather Agent (Port 8001)
- Analysis Agent (Port 8002)

Test with evaluation:

```bash
python client.py
```

Choose an agent and begin asking questions.

## Detailed Testing Guide

### Option 1: Interactive Client with Evaluation

```bash
# Terminal 1
python run_agents.py

# Terminal 2
python client.py
```

What happens:

1. Choose Weather Agent or Analysis Agent
2. Model-based evaluation runs automatically for every response

Example:

```text
Select agent (1 or 2): 2

What's the weather in Tokyo?

Analysis Agent: The weather in Tokyo is 25°C with humid conditions...

MODEL-BASED EVALUATION
=================================
Scores:
coherence/mean: 4.50
fluency/mean: 4.80
safety/mean: 1.00
=================================
```

### Option 2: Automated Multi-Agent Test

```bash
python client.py --test
```

What it does:

- Tests Weather Agent directly
- Tests Analysis Agent (calls Weather Agent internally)
- Runs model-based evaluation on both responses

## Understanding the Results

### Model-Based Evaluation Scores

- **4-5**: Excellent
- **2-3**: Acceptable / needs improvement
- **1**: Poor quality

### Score Meaning

- **Coherence**: Logical structure and consistency
- **Fluency**: Grammar and natural language quality
- **Safety**: Safe and appropriate content

## Configuration

### Environment Variables

```env
GROQ_API_KEY=your_groq_key
GOOGLE_CLOUD_PROJECT=your_project_id
```

### Ports

- Weather Agent: 8001
- Analysis Agent: 8002
- MCP Server: Auto-assigned

## File Purposes

| File | Purpose |
|------|---------|
| run_agents.py | Starts the multi-agent system |
| client.py | Interactive client with evaluation |
| client.py --test | Automated agent communication testing |
| evaluation/model_based_evaluator.py | Evaluates response quality |
| evaluation/base_evaluator.py | Base evaluator classes |
| agents/analysis_agent.py | Main agent (calls Weather Agent) |
| agents/weather_agent.py | Weather agent (calls MCP tools) |
| mcp_server.py | Weather data tools |

## Using Evaluation Programmatically

```python
from evaluation import ModelBasedEvaluator

evaluator = ModelBasedEvaluator()

result = await evaluator.evaluate_response(
    prompt="What's the weather in London?",
    response="London currently has 15°C with light rain...",
    context="Weather data from API"
)

if result["success"]:
    scores = result["scores"]
    print(scores.get("coherence/mean"))
    print(scores.get("fluency/mean"))
    print(scores.get("safety/mean"))
```

## API Endpoints

### Weather Agent (Port 8001)

```http
POST /v1/message:send
Content-Type: application/json
```

```json
{
  "message": "What's the weather in Tokyo?",
  "session_id": "optional_session_id"
}
```

### Analysis Agent (Port 8002)

```http
POST /v1/message:send
Content-Type: application/json
```

```json
{
  "message": "Should I go hiking tomorrow?",
  "session_id": "optional_session_id"
}
```

## Development Stack

- FastAPI
- Groq
- LangChain MCP Adapters
- Vertex AI
- httpx

## Architecture Details

1. MCP Server exposes weather tools
2. Weather Agent uses Groq to understand queries and call MCP tools
3. Analysis Agent calls Weather Agent via A2A, then uses Groq for analysis
4. Evaluation uses Vertex AI with Gemini to score response quality

## Troubleshooting

### Vertex AI evaluation fails

Verify Google Cloud authentication and project ID in `.env`.

### Groq API errors

Check `GROQ_API_KEY` and API quota.

### Agents can't communicate

Ensure both agents run on ports 8001 and 8002.

### MCP server not starting

Check port availability and installed dependencies.

## License

This project is for demonstration and educational purposes.
