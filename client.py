"""
A2A Protocol Client - Demonstrates agent-to-agent communication.
Evaluates responses using model-based evaluation (Gemini as judge).
"""

import asyncio
import httpx
import sys
from typing import Optional, Dict, Any
import os

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluation import ModelBasedEvaluator


class A2AClient:
    """Client for interacting with A2A protocol agents."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)

    async def discover_agent(self) -> dict:
        """Discover agent capabilities."""
        response = await self.client.get(f"{self.base_url}/.well-known/agent-card.json")
        response.raise_for_status()
        return response.json()

    async def send_message(self, message: str, session_id: Optional[str] = None) -> dict:
        """Send a message to the agent."""
        payload = {
            "message": message,
            "session_id": session_id or "client-session"
        }
        response = await self.client.post(f"{self.base_url}/v1/message:send", json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()


async def perform_model_evaluation(
    prompt: str,
    response_text: str,
    evaluator: ModelBasedEvaluator
):
    """Perform model-based evaluation on the response."""
    print("\n" + "=" * 50)
    print("📊 MODEL-BASED EVALUATION (Gemini as Judge)")
    print("=" * 50)
    
    try:
        eval_result = await evaluator.evaluate_response(
            prompt=prompt,
            response=response_text,
            context=""
        )

        if eval_result.get("success"):
            print("✅ Evaluation completed successfully")
            scores = eval_result.get("scores", {})
            if scores:
                print("\n📈 Scores:")
                for metric, score in scores.items():
                    if isinstance(score, (int, float)):
                        print(f"   {metric}: {score:.2f}")
                    else:
                        print(f"   {metric}: {score}")
            else:
                print("   ⚠️ No scores returned")
        else:
            print(f"❌ Evaluation failed: {eval_result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Evaluation error: {e}")
    
    print("=" * 50)


async def interactive_chat():
    """Interactive chat with an agent."""
    print("🌤️  A2A Multi-Agent Client with Model-Based Evaluation")
    print("=" * 60)
    print("\nAvailable agents:")
    print("  1. Weather Agent (port 8001) - Get weather data")
    print("  2. Analysis Agent (port 8002) - Get weather analysis")
    print("\n" + "=" * 60)

    # Choose agent
    while True:
        choice = input("\nSelect agent (1 or 2): ").strip()
        if choice == "1":
            url = "http://localhost:8001"
            agent_name = "Weather Agent"
            break
        elif choice == "2":
            url = "http://localhost:8002"
            agent_name = "Analysis Agent"
            break
        else:
            print("Please enter 1 or 2")

    print(f"\n✅ Connected to {agent_name}")
    print("\n💡 Example queries:")
    print("   - What's the weather in London?")
    print("   - Tell me about Paris weather")
    print("   - 5-day forecast for Tokyo")
    print("\nType 'quit' to exit, 'switch' to change agent")
    print("-" * 60)

    # Initialize model evaluator
    model_evaluator = ModelBasedEvaluator()

    async with A2AClient(url) as client:
        while True:
            user_input = input("\n❯ ").strip()

            if user_input.lower() == 'quit':
                print("Goodbye! 👋")
                break
            elif user_input.lower() == 'switch':
                return await interactive_chat()

            if not user_input:
                continue

            print("🤔 Processing...")
            try:
                response = await client.send_message(user_input)
                print(f"\n🤖 {agent_name}:\n{response['response']}")

                # Always perform model-based evaluation
                await perform_model_evaluation(
                    user_input,
                    response['response'],
                    model_evaluator
                )

            except Exception as e:
                print(f"❌ Error: {e}")


async def test_multi_agent():
    """Test communication between agents with model-based evaluation."""
    print("\n🧪 Testing Multi-Agent Communication with Model-Based Evaluation")
    print("=" * 60)

    # Initialize model evaluator
    model_evaluator = ModelBasedEvaluator()

    # First, call Weather Agent directly
    print("\n1️⃣ Calling Weather Agent directly...")
    async with A2AClient("http://localhost:8001") as weather_client:
        response = await weather_client.send_message("What's the weather in Paris?")
        print(f"   Weather Agent: {response['response'][:100]}...")

        # Evaluate Weather Agent response
        await perform_model_evaluation(
            "What's the weather in Paris?",
            response['response'],
            model_evaluator
        )

    # Then, call Analysis Agent (which will call Weather Agent)
    print("\n2️⃣ Calling Analysis Agent (will auto-call Weather Agent)...")
    async with A2AClient("http://localhost:8002") as analysis_client:
        response = await analysis_client.send_message("Should I visit Paris?")
        print(f"   Analysis Agent: {response['response'][:150]}...")

        # Evaluate Analysis Agent response
        await perform_model_evaluation(
            "Should I visit Paris?",
            response['response'],
            model_evaluator
        )

    print("\n✅ Multi-agent communication and evaluation successful!")
    print("   Analysis Agent used A2A to call Weather Agent")


async def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        await test_multi_agent()
    else:
        await interactive_chat()


if __name__ == "__main__":
    asyncio.run(main())