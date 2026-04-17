"""
Base evaluation classes for the multi-agent system.
"""

import os
import pandas as pd
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dotenv import load_dotenv

import vertexai
from vertexai.evaluation import EvalTask, PointwiseMetric, MetricPromptTemplateExamples

load_dotenv()


class BaseEvaluator(ABC):
    """Base class for all evaluators."""

    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1"):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT not set in environment or provided")

        self.location = location
        vertexai.init(project=self.project_id, location=self.location)

    @abstractmethod
    async def evaluate(self, **kwargs) -> Dict[str, Any]:
        """Evaluate using specific metrics."""
        pass

    def _run_eval_task(self, dataset: pd.DataFrame, metrics: List, experiment_name: str) -> Dict[str, Any]:
        """Run Vertex AI evaluation task."""
        try:
            eval_task = EvalTask(
                dataset=dataset,
                metrics=metrics,
                experiment=experiment_name
            )

            result = eval_task.evaluate()

            # Extract summary metrics
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


class TrajectoryStep:
    """Represents a single step in the agent trajectory."""

    def __init__(self, agent_name: str, action: str, input_data: Dict[str, Any], timestamp: str):
        self.agent_name = agent_name
        self.action = action
        self.input = input_data
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "action": self.action,
            "input": self.input,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrajectoryStep':
        return cls(
            agent_name=data["agent_name"],
            action=data["action"],
            input_data=data["input"],
            timestamp=data["timestamp"]
        )