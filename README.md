# Multi-Agent Weather System with MCP and A2A

A sophisticated multi-agent system that demonstrates Model Context Protocol (MCP) integration with Agent-to-Agent (A2A) communication, featuring weather data retrieval and analysis with optional Vertex AI evaluation.

## Architecture

- **MCP Server**: Provides weather data tools
- **Weather Agent** (Port 8001): Fetches weather data using MCP tools
- **Analysis Agent** (Port 8002): Analyzes weather data and provides recommendations
- **A2A Protocol**: Enables agent-to-agent communication
- **Vertex AI Evaluation**: Optional evaluation of agent responses

## Features

- Real-time weather data retrieval
- Intelligent weather analysis and recommendations
- Agent-to-agent communication
- **Trajectory Tracking**: Complete request tracing across agents and MCP tools
- **Vertex AI Evaluation**: Comprehensive evaluation with multiple techniques:
  - Model-based evaluation (Gemini as judge)
  - Trajectory evaluation (Vertex AI trajectory metrics)

## Trajectory Tracking

The system implements comprehensive trajectory tracking to enable process-level evaluation. Each request is traced through:

1. **Analysis Agent** → **Weather Agent** (with intent logging)
2. **Weather Agent** → **MCP Tool** (with tool name and arguments)
3. **Final Response** with complete accumulated trajectory

### Trajectory Data Structure

Each trajectory step contains:
- `agent_name`: Name of the agent performing the action
- `action`: Type of action (e.g., "call_weather_agent", "call_mcp_tool")
- `input`: Action parameters and data
- `timestamp`: ISO format timestamp

## Vertex AI Evaluation System

The system includes comprehensive evaluation capabilities using Vertex AI with different evaluation techniques organized in the `evaluation/` folder:

### Evaluation Folder Structure

```
evaluation/
├── __init__.py                 # Package exports and imports
├── base_evaluator.py          # Base evaluator classes and TrajectoryStep
├── model_based_evaluator.py   # Response quality evaluation (Gemini as judge)
└── trajectory_evaluator.py    # Trajectory path evaluation (Vertex AI metrics)
```

### What Each Evaluation Does

#### 🤖 **Model-Based Evaluator** (`model_based_evaluator.py`)
**Purpose**: Evaluates the quality of agent responses using Gemini as a judge.

**Metrics**:
- **Coherence** (1-5): Logical consistency and clarity of the response
- **Fluency** (1-5): Natural language flow and grammar quality
- **Safety** (1-5): Content safety and appropriateness
- **Groundedness** (1-5): Factual accuracy (crucial for weather data)
- **Instruction Following** (1-5): How well the response follows the user's request
- **Verbosity** (1-5): Appropriate response length (not too short/long)

**Use Case**: Assess whether the agent's final answer is good quality.

#### 🗺️ **Trajectory Evaluator** (`trajectory_evaluator.py`)
**Purpose**: Evaluates the quality of the agent's reasoning path and decision-making process.

**Metrics**:
- **Trajectory Exact Match** (1-5): How closely the trajectory matches expected patterns
- **Trajectory Precision** (1-5): Accuracy of steps taken (correct steps / total steps)
- **Trajectory Recall** (1-5): Completeness of necessary steps covered
- **Trajectory F1** (1-5): Balance of precision and recall
- **Reasoning Quality** (1-5): Quality of logical reasoning in the trajectory
- **Tool Usage Efficiency** (1-5): Effectiveness of tool selection and usage

**Use Case**: Assess whether the agent took the right steps to arrive at the answer.

### Testing Files

- **`test_trajectory_evaluation.py`**: Tests the trajectory evaluator with sample trajectories
- **`client.py`**: Interactive client with evaluation options
- **`run_agents.py`**: Starts the multi-agent system

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
   ```
   GROQ_API_KEY=your_groq_api_key_here
   GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id
   ```

### Google Cloud Setup (for Vertex AI Evaluation)

1. Create a Google Cloud Project
2. Enable the Vertex AI API
3. Set up authentication:
   - Install Google Cloud CLI
   - Run `gcloud auth application-default login`
   - Or set `GOOGLE_APPLICATION_CREDENTIALS` to your service account key file

4. The project ID should be set in the `.env` file as `GOOGLE_CLOUD_PROJECT`

## Step-by-Step Usage Guide

### 🚀 **Quick Start**

1. **Start the System**:
   ```bash
   python run_agents.py
   ```
   This starts MCP server + Weather Agent (port 8001) + Analysis Agent (port 8002)

2. **Test with Evaluation**:
   ```bash
   # In another terminal
   python client.py
   ```
   Choose agent → Choose evaluation type → Ask questions!

### 📋 **Detailed Testing Guide**

#### **Option 1: Interactive Client with Evaluation**
```bash
# Terminal 1: Start agents
python run_agents.py

# Terminal 2: Interactive testing
python client.py
```

**What happens**:
- Choose **Weather Agent** or **Analysis Agent**
- Choose **evaluation type**:
  - A. No evaluation (just chat)
  - B. Model-based (evaluates response quality)
  - C. Trajectory (evaluates reasoning path)
  - D. Both (response + reasoning evaluation)

**Example Session**:
```
Select agent (1 or 2): 2  # Analysis Agent
Select evaluation type (A, B, C, or D): D  # Both evaluations

❯ What's the weather in Tokyo?

🤖 Analysis Agent: [response...]

📊 EVALUATION RESULTS
🤖 MODEL-BASED EVALUATION (Gemini as Judge):
   coherence: 4.2
   fluency: 4.5
   groundedness: 4.8

🗺️ TRAJECTORY EVALUATION (Vertex AI):
   trajectory_precision: 4.1
   reasoning_quality: 4.3
   tool_usage_efficiency: 4.6
```

#### **Option 2: Automated Multi-Agent Test**
```bash
python client.py --test
```
**What it does**:
- Tests Weather Agent directly
- Tests Analysis Agent (calls Weather Agent internally)
- Shows trajectory tracking in action
- Runs evaluations on both responses

#### **Option 3: Trajectory Evaluation Only**
```bash
python test_trajectory_evaluation.py
```
**What it tests**:
- Single trajectory evaluation
- Trajectory comparison between paths
- Batch evaluation of multiple trajectories
- Trajectory statistics and metrics

### 🎯 **Understanding the Results**

#### **Model-Based Evaluation Results**
- **High scores (4-5)**: Excellent response quality
- **Medium scores (2-3)**: Acceptable but could be better
- **Low scores (1)**: Poor quality, needs improvement

#### **Trajectory Evaluation Results**
- **High scores (4-5)**: Agent took optimal reasoning path
- **Medium scores (2-3)**: Reasonable approach but could be more efficient
- **Low scores (1)**: Poor decision-making or unnecessary steps

### 🔧 **Configuration**

**Environment Variables** (`.env` file):
```
GROQ_API_KEY=your_groq_key
GOOGLE_CLOUD_PROJECT=your_project_id
```

**Ports**:
- Weather Agent: 8001
- Analysis Agent: 8002
- MCP Server: Auto-assigned

### 📁 **File Purposes**

| File | Purpose |
|------|---------|
| `run_agents.py` | Starts the entire multi-agent system |
| `client.py` | Interactive client with evaluation options |
| `client.py --test` | Automated testing of agent communication |
| `test_trajectory_evaluation.py` | Tests trajectory evaluation metrics |
| `evaluation/model_based_evaluator.py` | Evaluates response quality |
| `evaluation/trajectory_evaluator.py` | Evaluates reasoning paths |
| `agents/analysis_agent.py` | Main agent (calls Weather Agent) |
| `agents/weather_agent.py` | Weather agent (calls MCP tools) |
| `mcp_server.py` | Weather data tools |
- **Fluency**: Natural language flow and grammar
- **Safety**: Content safety and appropriateness
- **Groundedness**: Factual accuracy and relevance
- **Instruction Following**: How well the response addresses the query
- **Text Quality**: Overall response quality
- **Verbosity**: Appropriate level of detail

### Using Evaluation

```python
from evaluation import evaluate_agent_response

# Evaluate a response
result = await evaluate_agent_response(
    prompt="What's the weather in London?",
    response="London currently has 15°C with light rain...",
    context="Weather data from API"
)

print(result['scores'])
```

### Evaluation Scores

Scores are typically on a scale of 1-5, where:
- 1: Poor
- 2: Below Average
- 3: Average
- 4: Good
- 5: Excellent

## API Endpoints

### Weather Agent (Port 8001)
```
POST /v1/message:send
{
  "message": "What's the weather in Tokyo?",
  "session_id": "optional_session_id"
}
```

### Analysis Agent (Port 8002)
```
POST /v1/message:send
{
  "message": "Should I go hiking tomorrow?",
  "session_id": "optional_session_id"
}
```

## Development

The system uses:
- **FastAPI**: Web framework for agent APIs
- **Groq**: LLM for intelligent processing
- **LangChain MCP Adapters**: MCP tool integration
- **Vertex AI**: Response evaluation
- **httpx**: Async HTTP client for A2A communication

## Architecture Details

1. **MCP Server** exposes weather tools
2. **Weather Agent** uses Groq to understand queries and call MCP tools
3. **Analysis Agent** calls Weather Agent via A2A, then uses Groq for analysis
4. **Evaluation** uses Vertex AI to score response quality

## Troubleshooting

- Ensure all API keys are set in `.env`
- Check Google Cloud authentication for Vertex AI
- Verify MCP server starts without errors
- Check agent ports are available