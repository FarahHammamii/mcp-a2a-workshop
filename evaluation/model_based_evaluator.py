"""
Model-based evaluation using Gemini as a judge.
Evaluates agent responses using predefined metrics like coherence, fluency, etc.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from vertexai.evaluation import MetricPromptTemplateExamples

from .base_evaluator import BaseEvaluator


class ModelBasedEvaluator(BaseEvaluator):
    """
    Evaluates agent responses using Vertex AI model-based metrics.
    Uses Gemini as a judge for rubric-based scoring.
    """

    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1"):
        super().__init__(project_id, location)

        # Essential metrics for response quality
        self.metrics = [
            MetricPromptTemplateExamples.Pointwise.COHERENCE,
            MetricPromptTemplateExamples.Pointwise.FLUENCY,
            MetricPromptTemplateExamples.Pointwise.SAFETY,
        ]

    async def evaluate_response(
    self,
    prompt: str,
    response: str,
    context: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
        """
        Evaluate a single agent response using model-based metrics.
        """
        try:
            # Create simple dataset
            data = {
                "prompt": [prompt],
                "response": [response],
                "context": [context or ""]
            }

            df = pd.DataFrame(data)

            result = self._run_eval_task(
                dataset=df,
                metrics=self.metrics,
                experiment_name="response-eval"
            )

            # Ensure scores are properly formatted
            if result.get("success") and result.get("scores"):
                # Convert any non-serializable values
                scores = {}
                for k, v in result["scores"].items():
                    if isinstance(v, (int, float)):
                        scores[k] = float(v)
                    else:
                        scores[k] = str(v)
                result["scores"] = scores

            return result

        except Exception as e:
            return {"success": False, "error": str(e), "scores": {}}

    # Simple alias for backward compatibility
    async def evaluate(self, prompt: str, response: str, **kwargs) -> Dict[str, Any]:
        """Simple evaluate method for convenience."""
        return await self.evaluate_response(prompt, response, **kwargs)


# Simple convenience function
async def evaluate_response(prompt: str, response: str, context: str = None) -> Dict[str, Any]:
    """Quick evaluation function for simple use cases."""
    evaluator = ModelBasedEvaluator()
    return await evaluator.evaluate_response(prompt, response, context)