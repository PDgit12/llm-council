"""6-Stage Council Orchestrator for Parallels."""

import asyncio
import json
import logging
import random
from typing import List, Dict, Any, Optional

from openrouter import query_models_parallel, query_model
from config import (
    STAGE1_MODELS, STAGE2_MODELS, STAGE3_MODELS, 
    STAGE4_MODELS, STAGE5_MODELS, STAGE6_MODEL,
    TITLE_MODEL, DOMAIN_POOL
)

# Security & Safety
from safety.input_guard import InputSafetyGuard
from safety.output_guard import OutputSafetyGuard
from safety.policy_engine import PolicyEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("council_orchestrator")

# Initialize Safety Components
input_guard = InputSafetyGuard()
output_guard = OutputSafetyGuard()
policy_engine = PolicyEngine()

class CouncilOrchestrator:
    def __init__(self):
        pass

    async def run_pipeline(
        self,
        user_query: str,
        history: List[Dict[str, Any]] = None,
        target_domain: str = None,
        attachments: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the 6-stage Council flow.
        """
        # 🛡️ 1. Input Safety Check
        logger.info("[SAFETY] Checking input...")
        input_validation = input_guard.validate(user_query)
        policy_decision = policy_engine.check_input_policy(input_validation)
        
        if not policy_decision["allowed"]:
            logger.warning(f"[SAFETY] Input blocked: {policy_decision['reason']}")
            return self._blocked_response(policy_decision['reason'])

        sanitized_query = input_validation["sanitized_input"]
        context = f"Query: {sanitized_query}"
        if attachments:
            context += f"\n[User attached {len(attachments)} files]"

        # Stage 1: Exploration (Broad & Niche)
        logger.info("--- Stage 1: Exploration ---")
        s1_results = await query_models_parallel(
            STAGE1_MODELS, 
            messages=[{"role": "user", "content": f"Explore this topic/problem from your specialized perspective. Generate 3 unique angles or analogies.\n\n{context}"}]
        )
        
        # Aggregate S1 findings
        s1_summary = "\n".join([f"[{m}]: {r.get('content')}" for m, r in s1_results.items() if r and r.get('content')])

        # Stage 2: Grounding (Verification)
        logger.info("--- Stage 2: Grounding ---")
        s2_results = await query_models_parallel(
            STAGE2_MODELS,
            messages=[{"role": "user", "content": f"Verify the following claims and identify any potential hallucinations or weak logic:\n\n{s1_summary}"}]
        )
        
        # Stage 3: Technical Tasking (Conditional)
        s3_results = {}
        is_technical = "code" in sanitized_query.lower() or "implement" in sanitized_query.lower() or "python" in sanitized_query.lower()
        if is_technical:
            logger.info("--- Stage 3: Technical Tasking ---")
            s3_results = await query_models_parallel(
                STAGE3_MODELS,
                messages=[{"role": "user", "content": f"Generate technical specifications or code snippets for this request:\n\n{context}"}]
            )

        # Stage 4: Cross-Pollination
        logger.info("--- Stage 4: Cross-Pollination ---")
        s4_context = f"Exploration:\n{s1_summary}\n\nGrounding:\n{str(s2_results)}"
        s4_results = await query_models_parallel(
            STAGE4_MODELS,
            messages=[{"role": "user", "content": f"Synthesize these perspectives and find upgrading connections or 'cross-pollination' opportunities:\n\n{s4_context}"}]
        )

        # Stage 5: Debate (Critique)
        logger.info("--- Stage 5: Debate ---")
        s4_summary = "\n".join([f"[{m}]: {r.get('content')}" for m, r in s4_results.items() if r and r.get('content')])
        s5_results = await query_models_parallel(
            STAGE5_MODELS,
            messages=[{"role": "user", "content": f"Critique this synthesis. What is missing? What is over-generalized?\n\n{s4_summary}"}]
        )

        # Stage 6: Synthesis (Final Answer)
        logger.info("--- Stage 6: Synthesis ---")
        final_context = (
            f"Original Query: {sanitized_query}\n\n"
            f"Exploration: {s1_summary}\n"
            f"Grounding: {str(s2_results)}\n"
            f"Technical: {str(s3_results)}\n"
            f"synthesis_draft: {s4_summary}\n"
            f"Critique: {str(s5_results)}"
        )
        
        s6_response = await query_model(
            STAGE6_MODEL,
            messages=[{
                "role": "system", 
                "content": "You are the Council Head. Synthesize all perspectives into a SINGLE, coherent, high-quality Markdown response. Do not label the sections as 'Stage 1', etc., just write the solution/answer naturally and professionally."
            }, {
                "role": "user", 
                "content": final_context
            }]
        )
        
        final_answer = s6_response.get("content") if s6_response else "The Council could not reach a consensus."

        # 🛡️ Output Safety Check
        if final_answer:
            logger.info("[SAFETY] Checking output...")
            output_validation = output_guard.check_output(final_answer)
            policy_decision = policy_engine.check_output_policy(output_validation)
            
            if not policy_decision["allowed"]:
                logger.warning(f"[SAFETY] Output blocked: {policy_decision['reason']}")
                final_answer = f"**Safety Alert**: The response was withheld. {policy_decision['reason']}"

        return {
            "stage1": s1_results,
            "stage2": s2_results,
            "stage3": s3_results,
            "stage4": s4_results,
            "stage5": s5_results,
            "final_answer": final_answer
        }

    def _blocked_response(self, reason: str) -> Dict[str, Any]:
        return {
            "stage1": {},
            "stage2": {},
            "stage3": {},
            "stage4": {},
            "stage5": {},
            "final_answer": f"I cannot process this request. {reason}",
            "error": "Blocked by Safety Policy"
        }

# ═══════════════════════════════════════════
#  Legacy Adapter / Public API
# ═══════════════════════════════════════════

orchestrator = CouncilOrchestrator()

async def run_analogy_pipeline(
    user_query: str,
    history: List[Dict[str, Any]] = None,
    target_domain: str = None,
    attachments: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Public entry point compatible with main.py
    """
    return await orchestrator.run_pipeline(user_query, history, target_domain, attachments)

async def generate_conversation_title(user_query: str) -> str:
    """Generate a short title using the configured Title model."""
    result = await query_model(
        TITLE_MODEL,
        messages=[{"role": "user", "content": f"Generate a 3-5 word title for: {user_query}. Return ONLY the title."}]
    )
    if result and result.get("content"):
        return result["content"].strip().strip('"')
    return "New Conversation"

def select_domains(user_query: str, target_domain: str = None, count: int = 4) -> List[str]:
    """Legacy helper - kept for compatibility if needed."""
    if target_domain:
         remaining = [d for d in DOMAIN_POOL if d.lower() != target_domain.lower()]
         random.shuffle(remaining)
         return [target_domain] + remaining[:count - 1]
    
    shuffled = DOMAIN_POOL.copy()
    random.shuffle(shuffled)
    return shuffled[:count]
