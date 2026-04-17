import os
import pandas as pd
from typing import Dict, Any, Optional
from dotenv import load_dotenv

import vertexai
# In the latest SDK, EvalTask and metrics are in vertexai.evaluation
from vertexai.evaluation import EvalTask, PointwiseMetric, MetricPromptTemplateExamples

load_dotenv()

class VertexAIEvaluator:
    """
    Evaluates Analysis Agent responses using Vertex AI metrics as explained 
    in the 'Build with AI' session.
    """
    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1"):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT not set in environment or provided")

        self.location = location
        vertexai.init(project=self.project_id, location=self.location)

        # These are the key metrics discussed in the video [00:51:26]
        # We use the Pointwise constants for reliable, rubric-based scoring.
        self.metrics = [
            MetricPromptTemplateExamples.Pointwise.COHERENCE,
            MetricPromptTemplateExamples.Pointwise.FLUENCY,
            MetricPromptTemplateExamples.Pointwise.SAFETY,
            MetricPromptTemplateExamples.Pointwise.GROUNDEDNESS, # Crucial for Weather Data
            MetricPromptTemplateExamples.Pointwise.INSTRUCTION_FOLLOWING,
            MetricPromptTemplateExamples.Pointwise.VERBOSITY
        ]

    async def evaluate_response(
        self, 
        prompt: str, 
        response: str, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs the evaluation task. 
        Note: Groundedness requires 'context' to ensure the Analysis Agent 
        didn't hallucinate weather details.
        """
        try:
            # Create dataset for evaluation
            data = {
                "prompt": [prompt],
                "response": [response],
                "context": [context if context else ""]
            }
            df = pd.DataFrame(data)

            # Define the EvalTask
            eval_task = EvalTask(
                dataset=df,
                metrics=self.metrics,
                experiment="analysis-agent-eval"
            )

            # Run evaluation using Gemini as the Judge [00:55:03]
            # Remove the explicit model parameter because the dataset already includes a BYOR response column.
            result = eval_task.evaluate()

            # Extract summary metrics (average scores)
            scores = {}
            if hasattr(result, 'summary_metrics'):
                scores = result.summary_metrics
            
            return {
                "success": True, 
                "scores": scores,
                "details": result.metrics_table.to_dict() if hasattr(result, 'metrics_table') else {}
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# Convenience function for your Analysis Agent
async def evaluate_agent_response(prompt, response, context=None):
    evaluator = VertexAIEvaluator()
    return await evaluator.evaluate_response(prompt, response, context)

if __name__ == "__main__":
    import asyncio
    async def main():
        evaluator = VertexAIEvaluator()
        # Simulated Analysis Agent output
        test_prompt = "Is it a good day for a picnic in Tokyo?"
        test_context = "Weather in Tokyo: 22°C, Clear skies, No rain."
        test_response = "Yes! It's 22°C and sunny in Tokyo, perfect for a picnic."
        
        print("Starting Vertex AI Evaluation...")
        result = await evaluator.evaluate_response(test_prompt, test_response, test_context)
        
        if result["success"]:
            print("\n📊 Evaluation Scores (1-5):")
            for metric, score in result["scores"].items():
                print(f" - {metric}: {score}")
        else:
            print(f"❌ Error: {result['error']}")

    asyncio.run(main())