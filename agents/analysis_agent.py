"""
Analysis Agent - Analyzes weather data and provides insights.
This agent can communicate with the Weather Agent via A2A protocol.
"""

import os
import httpx
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from groq import Groq
from .base_agent import BaseA2AAgent

# Optional Vertex AI evaluation
try:
    from ..evaluation import VertexAIEvaluator
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

load_dotenv()


class AnalysisAgent(BaseA2AAgent):
    """
    Analysis agent that processes weather data and provides insights.
    Can call the Weather Agent via A2A to get data, then analyze it.
    """
    
    def __init__(self, port: int = 8002, weather_agent_url: str = "http://localhost:8001"):
        super().__init__(
            name="Weather Analysis Agent",
            description="Analyzes weather data and provides travel/activity recommendations",
            version="1.0.0",
            port=port
        )
        
        # Initialize Groq client
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        # Weather agent A2A endpoint
        self.weather_agent_url = weather_agent_url
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Optional Vertex AI evaluator
        self.evaluator = None
        if VERTEX_AI_AVAILABLE and os.getenv("GOOGLE_CLOUD_PROJECT"):
            try:
                self.evaluator = VertexAIEvaluator()
                print("✅ Analysis Agent: Vertex AI evaluation enabled")
            except Exception as e:
                print(f"⚠️ Analysis Agent: Vertex AI evaluation not available: {e}")
        else:
            print("ℹ️ Analysis Agent: Vertex AI evaluation not configured")
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "skills": [
                {
                    "id": "analyze_weather",
                    "name": "Analyze Weather",
                    "description": "Analyze weather and provide recommendations"
                },
                {
                    "id": "travel_advice",
                    "name": "Travel Advice",
                    "description": "Get travel advice based on weather"
                }
            ],
            "depends_on": ["weather_agent"]
        }
    
    async def _call_weather_agent(self, query: str) -> str:
        """Call the Weather Agent via A2A protocol."""
        try:
            response = await self.http_client.post(
                f"{self.weather_agent_url}/v1/message:send",
                json={
                    "message": query,
                    "session_id": f"analysis-{self.agent_id}",
                    "sender_id": self.agent_id
                }
            )
            data = response.json()
            return data.get("response", "No response from weather agent")
        except Exception as e:
            return f"Error calling weather agent: {str(e)}"
    
    async def _analyze_with_groq(self, user_message: str, weather_data: str) -> str:
        """Use Groq to analyze weather data and provide insights."""
        
        prompt = f"""You are a weather analysis assistant. Analyze the weather data and provide useful insights.

User question: {user_message}

Weather data: {weather_data}

Provide a helpful response including:
1. Brief summary of the weather
2. Practical recommendations (clothing, activities, etc.)
3. Any warnings if applicable (extreme temperatures, etc.)

Keep it concise and friendly.
"""
        
        response = self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    
    async def process_message(self, message: str, session_id: Optional[str] = None, sender_id: Optional[str] = None) -> str:
        """Process message by first getting weather data, then analyzing it."""
        
        # First, call the weather agent to get data
        weather_data = await self._call_weather_agent(message)
        
        # Then analyze the data with Groq
        analysis = await self._analyze_with_groq(message, weather_data)
        
        # Optional: Evaluate the response with Vertex AI
        if self.evaluator:
            try:
                eval_result = await self.evaluator.evaluate_response(
                    prompt=message,
                    response=analysis,
                    context=weather_data
                )
                if eval_result["success"]:
                    scores = eval_result["scores"]
                    print(f"📊 Response Evaluation Scores:")
                    for metric, score in scores.items():
                        print(f"   {metric}: {score:.2f}")
                else:
                    print(f"⚠️ Evaluation failed: {eval_result['error']}")
            except Exception as e:
                print(f"⚠️ Evaluation error: {e}")
        
        return analysis
    
    async def cleanup(self):
        """Clean up HTTP client."""
        await self.http_client.aclose()