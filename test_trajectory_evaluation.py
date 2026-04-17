#!/usr/bin/env python3
"""
Trajectory Evaluation Test Script
Compatible with Vertex AI EvalTask-based trajectory evaluation.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluation import TrajectoryEvaluator, TrajectoryStep


class TrajectoryEvaluationTester:

    def __init__(self):
        self.evaluator = TrajectoryEvaluator()

    def create_sample_trajectory(self) -> List[TrajectoryStep]:
        """Create a sample trajectory with proper tool call format."""
        return [
            TrajectoryStep(
                agent_name="Weather Agent",
                action="get_current_weather",  # Tool name
                input_data={"city": "Tokyo"},  # Tool input arguments
                timestamp=datetime.now().isoformat()
            ),
            TrajectoryStep(
                agent_name="Weather Agent",
                action="celsius_to_fahrenheit",  # Tool name
                input_data={"celsius": 22},  # Tool input
                timestamp=datetime.now().isoformat()
            )
        ]

    def create_expected_trajectory(self) -> List[TrajectoryStep]:
        """Create expected trajectory with proper tool call format."""
        return [
            TrajectoryStep(
                agent_name="Weather Agent",
                action="get_current_weather",
                input_data={"city": "Tokyo"},
                timestamp=datetime.now().isoformat()
            ),
            TrajectoryStep(
                agent_name="Weather Agent",
                action="celsius_to_fahrenheit",
                input_data={"celsius": 22},
                timestamp=datetime.now().isoformat()
            ),
            TrajectoryStep(
                agent_name="Weather Agent",
                action="format_response",
                input_data={"format_type": "user_friendly", "include_units": True},
                timestamp=datetime.now().isoformat()
            )
        ]

    async def test_single_trajectory_evaluation(self):
        print("\n🧪 SINGLE TRAJECTORY TEST")
        print("-" * 50)

        trajectory = self.create_sample_trajectory()
        expected_trajectory = self.create_expected_trajectory()

        result = await self.evaluator.evaluate_trajectory(
            trajectory=trajectory,
            expected_trajectory=expected_trajectory,
            prompt="What's the weather like in Tokyo?",
            final_response="Weather in Tokyo: 22°C (71.6°F), Clear skies"
        )

        if not result["success"]:
            print(f"❌ FAILED: {result.get('error')}")
            return False

        print("✅ SUCCESS\n")

        print("📊 METRICS:")
        scores = result.get("scores", {})

        if not scores:
            print("⚠️ No scores returned (check Vertex AI metrics config)")
        else:
            for metric, score in scores.items():
                try:
                    if isinstance(score, (int, float)):
                        print(f"   {metric}: {float(score):.3f}")
                    else:
                        print(f"   {metric}: {score}")
                except:
                    print(f"   {metric}: {score}")

        print("\n📈 TRAJECTORY STATS:")
        stats = result.get("trajectory_stats", {})
        print(f"   Total steps: {stats.get('total_steps', 0)}")
        print(f"   Unique agents: {stats.get('unique_agents', 0)}")
        print(f"   Actions: {stats.get('actions', [])}")

        return True

    async def test_trajectory_comparison(self):
        print("\n🧪 TRAJECTORY COMPARISON TEST")
        print("-" * 50)
        
        trajectory = self.create_sample_trajectory()
        expected_trajectory = self.create_expected_trajectory()
        
        print(f"Predicted steps: {len(trajectory)}")
        print(f"Expected steps: {len(expected_trajectory)}")
        
        result = await self.evaluator.evaluate_trajectory(
            trajectory=trajectory,
            expected_trajectory=expected_trajectory,
            prompt="What's the weather like in Tokyo?",
            final_response="Weather in Tokyo: 22°C (71.6°F), Clear skies"
        )
        
        if not result["success"]:
            print(f"❌ FAILED: {result.get('error')}")
            return False
        
        print("✅ Comparison complete")
        scores = result.get("scores", {})
        
        # Check if we got meaningful scores
        exact_match = scores.get("trajectory_exact_match/mean", None)
        if exact_match is not None:
            print(f"   Exact Match Score: {exact_match:.3f}")
        else:
            print("   ⚠️ Exact match metric not available")
        
        return True

    async def test_batch_evaluation(self):
        print("\n🧪 BATCH EVALUATION TEST")
        print("-" * 50)
        
        # Test multiple scenarios
        test_cases = [
            {
                "name": "Weather only",
                "trajectory": [
                    TrajectoryStep(
                        agent_name="Weather Agent",
                        action="get_current_weather",
                        input_data={"city": "London"},
                        timestamp=datetime.now().isoformat()
                    )
                ],
                "expected": [
                    TrajectoryStep(
                        agent_name="Weather Agent",
                        action="get_current_weather",
                        input_data={"city": "London"},
                        timestamp=datetime.now().isoformat()
                    )
                ]
            },
            {
                "name": "Math calculation",
                "trajectory": [
                    TrajectoryStep(
                        agent_name="Math Agent",
                        action="calculate",
                        input_data={"expression": "15 * 4"},
                        timestamp=datetime.now().isoformat()
                    )
                ],
                "expected": [
                    TrajectoryStep(
                        agent_name="Math Agent",
                        action="calculate",
                        input_data={"expression": "15 * 4"},
                        timestamp=datetime.now().isoformat()
                    )
                ]
            }
        ]
        
        results = []
        for test in test_cases:
            result = await self.evaluator.evaluate_trajectory(
                trajectory=test["trajectory"],
                expected_trajectory=test["expected"],
                prompt=f"Test: {test['name']}",
                final_response="Test response"
            )
            results.append(result)
            print(f"   {test['name']}: {'✅' if result['success'] else '❌'}")
        
        return all(r["success"] for r in results)

    async def run_all_tests(self):
        print("\n🚀 TRAJECTORY EVALUATION TEST SUITE")
        print("=" * 60)

        results = {}
        results["single"] = await self.test_single_trajectory_evaluation()
        results["comparison"] = await self.test_trajectory_comparison()
        results["batch"] = await self.test_batch_evaluation()

        print("\n" + "=" * 60)
        print("📊 FINAL SUMMARY")

        passed = sum(results.values())
        total = len(results)

        for k, v in results.items():
            print(f"   {k}: {'✅ PASS' if v else '❌ FAIL'}")

        print(f"\nOVERALL: {passed}/{total} tests passed")

        return {
            "results": results,
            "success": passed == total
        }


async def main():
    tester = TrajectoryEvaluationTester()

    try:
        result = await tester.run_all_tests()

        file_name = f"trajectory_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(file_name, "w") as f:
            json.dump(result, f, indent=2, default=str)

        print(f"\n💾 Saved: {file_name}")

        sys.exit(0 if result["success"] else 1)

    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("Trajectory Evaluation Test")
    print("Using Vertex AI EvalTask system\n")
    asyncio.run(main())