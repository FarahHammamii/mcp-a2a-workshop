import pandas as pd
from typing import Dict, Any, List, Optional
from vertexai.preview.evaluation import EvalTask

from .base_evaluator import BaseEvaluator, TrajectoryStep


class TrajectoryEvaluator(BaseEvaluator):

    async def evaluate(self, **kwargs):
        return await self.evaluate_trajectory(**kwargs)

    def _trajectory_to_list(self, trajectory: List[TrajectoryStep]):
        """Convert TrajectoryStep to Vertex AI expected format."""
        return [
            {
                "tool_name": step.action,  # action contains the tool/function name
                "tool_input": step.input,   # input contains the arguments
                "tool_output": step.output if hasattr(step, 'output') and step.output else {}
            }
            for step in trajectory
        ]

    async def evaluate_trajectory(
        self,
        trajectory: List[TrajectoryStep],
        expected_trajectory: Optional[List[TrajectoryStep]] = None,
        prompt: str = "",
        final_response: str = ""
    ) -> Dict[str, Any]:

        # Convert trajectories to expected format
        pred_traj = self._trajectory_to_list(trajectory)
        ref_traj = self._trajectory_to_list(expected_trajectory or [])
        
        df = pd.DataFrame([{
            "prompt": prompt,
            "reference_trajectory": ref_traj,
            "predicted_trajectory": pred_traj,
            "response": final_response
        }])

        trajectory_metrics = [
            "trajectory_exact_match",
            "trajectory_in_order_match",
            "trajectory_any_order_match",
            "trajectory_precision",
            "trajectory_recall",
        ]

        eval_task = EvalTask(
            dataset=df,
            metrics=trajectory_metrics,
            experiment="trajectory-eval"
        )

        result = eval_task.evaluate()

        # Extract metrics safely
        metrics = {}
        if hasattr(result, "summary_metrics"):
            metrics = result.summary_metrics
        
        return {
            "success": True,
            "scores": metrics,
            "raw": str(result),
            "trajectory_stats": {
                "total_steps": len(trajectory),
                "unique_agents": len(set(t.agent_name for t in trajectory)),
                "actions": [t.action for t in trajectory]
            }
        }