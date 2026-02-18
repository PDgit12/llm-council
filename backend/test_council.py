import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies before importing council to avoid side effects if any
# (Though council.py imports seem mostly safe, except for the initialization of safety guards)
# We will patch the instances on the imported module.

from backend.council import CouncilOrchestrator

class TestCouncilOrchestrator(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.orchestrator = CouncilOrchestrator()

        # Patch the safety components on the council module
        self.input_guard_patcher = patch('backend.council.input_guard')
        self.output_guard_patcher = patch('backend.council.output_guard')
        self.policy_engine_patcher = patch('backend.council.policy_engine')

        self.mock_input_guard = self.input_guard_patcher.start()
        self.mock_output_guard = self.output_guard_patcher.start()
        self.mock_policy_engine = self.policy_engine_patcher.start()

        # Patch openrouter functions
        self.query_models_parallel_patcher = patch('backend.council.query_models_parallel', new_callable=AsyncMock)
        self.query_model_patcher = patch('backend.council.query_model', new_callable=AsyncMock)

        self.mock_query_models_parallel = self.query_models_parallel_patcher.start()
        self.mock_query_model = self.query_model_patcher.start()

    async def asyncTearDown(self):
        self.input_guard_patcher.stop()
        self.output_guard_patcher.stop()
        self.policy_engine_patcher.stop()
        self.query_models_parallel_patcher.stop()
        self.query_model_patcher.stop()

    async def test_run_pipeline_success(self):
        """Test the happy path where all stages succeed."""
        user_query = "Explain quantum physics"

        # Mock Safety Checks
        self.mock_input_guard.validate.return_value = {"sanitized_input": user_query, "original_input": user_query}
        self.mock_policy_engine.check_input_policy.return_value = {"allowed": True}
        self.mock_output_guard.check_output.return_value = {"safe": True}
        self.mock_policy_engine.check_output_policy.return_value = {"allowed": True}

        # Mock Stage Results
        self.mock_query_models_parallel.side_effect = [
            {"model_a": {"content": "Stage 1 Result"}},  # Stage 1
            {"model_b": {"content": "Stage 2 Result"}},  # Stage 2
            # Stage 3 is conditional (skipped for this query)
            {"model_c": {"content": "Stage 4 Result"}},  # Stage 4
            {"model_d": {"content": "Stage 5 Result"}},  # Stage 5
        ]

        self.mock_query_model.return_value = {"content": "Final Answer"}

        # Run Pipeline
        result = await self.orchestrator.run_pipeline(user_query)

        # Assertions
        self.assertEqual(result["final_answer"], "Final Answer")
        self.assertEqual(result["stage1"]["model_a"]["content"], "Stage 1 Result")
        self.assertEqual(result["stage2"]["model_b"]["content"], "Stage 2 Result")
        self.assertEqual(result["stage3"], {}) # Should be empty as no technical keywords
        self.assertEqual(result["stage4"]["model_c"]["content"], "Stage 4 Result")
        self.assertEqual(result["stage5"]["model_d"]["content"], "Stage 5 Result")

        # Verify calls
        self.mock_input_guard.validate.assert_called_once_with(user_query)
        self.assertEqual(self.mock_query_models_parallel.call_count, 4) # S1, S2, S4, S5
        self.mock_query_model.assert_called_once()

    async def test_run_pipeline_technical_trigger(self):
        """Test that technical keywords trigger Stage 3."""
        user_query = "Write some Python code"

        # Mock Safety
        self.mock_input_guard.validate.return_value = {"sanitized_input": user_query}
        self.mock_policy_engine.check_input_policy.return_value = {"allowed": True}
        self.mock_output_guard.check_output.return_value = {"safe": True}
        self.mock_policy_engine.check_output_policy.return_value = {"allowed": True}

        # Mock Stages
        self.mock_query_models_parallel.side_effect = [
            {"m1": {"content": "s1"}},
            {"m2": {"content": "s2"}},
            {"m3": {"content": "s3_code"}}, # Stage 3 should be called
            {"m4": {"content": "s4"}},
            {"m5": {"content": "s5"}},
        ]
        self.mock_query_model.return_value = {"content": "Final Code"}

        result = await self.orchestrator.run_pipeline(user_query)

        self.assertEqual(result["stage3"]["m3"]["content"], "s3_code")
        self.assertEqual(self.mock_query_models_parallel.call_count, 5) # S1, S2, S3, S4, S5

    async def test_run_pipeline_input_blocked(self):
        """Test that blocked input stops the pipeline."""
        user_query = "bad query"

        self.mock_input_guard.validate.return_value = {"sanitized_input": user_query}
        self.mock_policy_engine.check_input_policy.return_value = {
            "allowed": False,
            "reason": "Policy Violation"
        }

        result = await self.orchestrator.run_pipeline(user_query)

        self.assertIn("I cannot process this request", result["final_answer"])
        self.assertEqual(result["error"], "Blocked by Safety Policy")
        self.mock_query_models_parallel.assert_not_called()

    async def test_run_pipeline_output_blocked(self):
        """Test that blocked output replaces the final answer."""
        user_query = "risky query"

        # Safety Mocking
        self.mock_input_guard.validate.return_value = {"sanitized_input": user_query}
        self.mock_policy_engine.check_input_policy.return_value = {"allowed": True}

        # Run through stages
        self.mock_query_models_parallel.side_effect = [
            {"s1": {"content": "c"}}, {"s2": {"content": "c"}},
            {"s4": {"content": "c"}}, {"s5": {"content": "c"}}
        ]
        self.mock_query_model.return_value = {"content": "Unsafe Output"}

        # Output Safety Block
        self.mock_output_guard.check_output.return_value = {"safe": False}
        self.mock_policy_engine.check_output_policy.return_value = {
            "allowed": False,
            "reason": "Unsafe Content"
        }

        result = await self.orchestrator.run_pipeline(user_query)

        self.assertIn("**Safety Alert**", result["final_answer"])
        self.assertIn("Unsafe Content", result["final_answer"])

    async def test_run_pipeline_empty_stage_results(self):
        """Test pipeline robustness when stages return empty results."""
        user_query = "Valid query"

        self.mock_input_guard.validate.return_value = {"sanitized_input": user_query}
        self.mock_policy_engine.check_input_policy.return_value = {"allowed": True}
        self.mock_output_guard.check_output.return_value = {"safe": True}
        self.mock_policy_engine.check_output_policy.return_value = {"allowed": True}

        # All stages return empty dicts or Nones
        self.mock_query_models_parallel.side_effect = [{}, {}, {}, {}]
        self.mock_query_model.return_value = None # Final synthesis fails

        result = await self.orchestrator.run_pipeline(user_query)

        self.assertEqual(result["final_answer"], "The Council could not reach a consensus.")
        self.assertEqual(result["stage1"], {})

    async def test_run_pipeline_with_attachments(self):
        """Test that attachments are included in the context."""
        user_query = "Analyze this file"
        attachments = [{"name": "file.txt", "content": "content"}]

        self.mock_input_guard.validate.return_value = {"sanitized_input": user_query}
        self.mock_policy_engine.check_input_policy.return_value = {"allowed": True}
        self.mock_output_guard.check_output.return_value = {"safe": True}
        self.mock_policy_engine.check_output_policy.return_value = {"allowed": True}

        self.mock_query_models_parallel.side_effect = [
            {"s1": {"content": "c"}}, {"s2": {"content": "c"}},
            {"s4": {"content": "c"}}, {"s5": {"content": "c"}}
        ]
        self.mock_query_model.return_value = {"content": "Answer"}

        await self.orchestrator.run_pipeline(user_query, attachments=attachments)

        # Check that the first call to query_models_parallel included the attachment info in the prompt
        args, kwargs = self.mock_query_models_parallel.call_args_list[0]
        messages = kwargs['messages']
        user_content = messages[0]['content']
        self.assertIn("[User attached 1 files]", user_content)
