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
- Vertex AI-powered response evaluation with metrics like coherence, fluency, safety, etc.

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

## Usage

Run the complete system:
```bash
python run_agents.py
```

This will start:
- MCP Weather Server
- Weather Agent on port 8001
- Analysis Agent on port 8002

## Vertex AI Evaluation

The system includes Vertex AI evaluation capabilities to assess agent response quality.

### Available Metrics

- **Coherence**: Logical consistency and clarity
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