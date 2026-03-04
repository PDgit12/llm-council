"""6-Stage Council Orchestrator for Parallels."""

import asyncio
import json
import logging
import random
import time
from typing import List, Dict, Any, Optional

from .openrouter import query_models_parallel, query_model
from .config import (
    STAGE1_MODELS, STAGE2_MODELS, STAGE3_MODELS, STAGE4_MODELS, STAGE5_MODELS, STAGE6_MODEL, FAST_MODEL,
    MODEL_GENERAL_REASONER, MODEL_GROUNDING_VERIFIER, TITLE_MODEL, MODEL_TECHNICAL_SPECIALIST
)

# Security & Safety
from .safety.input_guard import InputSafetyGuard
from .safety.output_guard import OutputSafetyGuard
from .safety.policy_engine import PolicyEngine

logger = logging.getLogger(__name__)

class CouncilOrchestrator:
    def __init__(self):
        self.input_guard = InputSafetyGuard()
        self.output_guard = OutputSafetyGuard()
        self.policy_engine = PolicyEngine()

    async def run_pipeline(self, query: str, history: List[Dict[str, str]] = None, target_domain: str = None, attachments: List[Dict[str, Any]] = None, on_event: callable = None):
        """Orchestrate the 6-stage deliberation pipeline with optimized parallelism."""
        start_time = time.time()
        
        def emit(event_type, message=None, data=None):
            if on_event:
                asyncio.create_task(on_event(event_type, message, data))

        # 🚀 1. Security & Validation
        emit("council_start", "Validating structural integrity and policy compliance...")
        input_validation = self.input_guard.validate(query)
        policy_decision = self.policy_engine.check_input_policy({"safe": input_validation["safe"]})
        
        if not input_validation["safe"] or not policy_decision["allowed"]:
            logger.warning(f"Council blocked query: {policy_decision['reason']}")
            return {
                "final_answer": f"Policy Violation: {policy_decision['reason']}",
                "blocked": True
            }

        sanitized_query = input_validation["sanitized_input"]
        
        # 🧠 1.5 Complexity Assessment for Early Exit
        simple_keywords = ["hi", "hello", "hey", "thanks", "ok", "bye", "help"]
        is_very_simple = len(sanitized_query.split()) < 4 or any(w == sanitized_query.lower().strip() for w in simple_keywords)
        complexity = "simple" if is_very_simple else "complex"
        
        context = f"Query: {sanitized_query}"
        if attachments:
            context += f"\n[User attached {len(attachments)} files]"

        # 🚀 FAST TRACK: Bypass Council for simple queries
        if is_very_simple and not attachments:
            logger.info(f"--- Fast Track Activated ({complexity}) ---")
            emit("council_start", "Fast Track active. Routing to speed model...")
            
            # Show the fast model in the UI
            emit("model_activity", data={"model": FAST_MODEL, "status": "started"})
            
            fast_start = time.time()
            # Use the dedicated FAST_MODEL (Gemini Flash Lite) for sub-second response
            fast_response = await query_model(FAST_MODEL, [{"role": "user", "content": sanitized_query}])
            
            emit("model_activity", data={"model": FAST_MODEL, "status": "completed"})
            
            latency_ms = int((time.time() - fast_start) * 1000)
            logger.info(f"--- Fast Track Complete in {latency_ms}ms ---")
            
            return {
                "final_answer": fast_response.get("content") if fast_response else "Service unavailable.",
                "latency_ms": latency_ms,
                "complexity": complexity,
                "fast_track": True
            }

        # 🚀 PARALLEL OPTIMIZATION: Overlap Stage 1 (Exploration) and Stage 3 (Technical Tasking)
        logger.info(f"--- Parallel Phase: Exploration & Technical Tasking ({complexity}) ---")
        emit("parallel_phase_start", "Activating parallel agents for exploration and technical analysis...")
        
        async def on_model_activity(model, status):
            emit("model_activity", data={"model": model, "status": status})

        # Determine targets
        s1_targets = STAGE1_MODELS
        is_technical = any(kw in sanitized_query.lower() for kw in ["code", "implement", "python", "javascript", "error", "debug", "cheat sheet", "quiz"])
        s3_targets = STAGE3_MODELS if (is_technical and not is_very_simple) else []

        # Start tasks
        s1_task = asyncio.create_task(query_models_parallel(s1_targets, messages=[{
            "role": "user", 
            "content": f"Deconstruct this topic with high architectural rigor. Identify the atomic principles and provide 3 unique conceptual mappings...\n\n{context}",
            "attachments": attachments
        }], yield_results=True, on_activity=on_model_activity))

        s3_task = None
        if s3_targets:
            s3_task = asyncio.create_task(query_models_parallel(s3_targets, messages=[{
                "role": "user", 
                "content": f"Generate technical specifications or code snippets for this request:\n\n{context}"
            }], yield_results=True, on_activity=on_model_activity))

        # Collect results in parallel
        s1_results = {}
        s3_results = {}

        async def collect_s1():
            gen = await s1_task
            if gen:
                async for model, res in gen:
                    s1_results[model] = res
                    if res and res.get('content'):
                        emit("stage1_partial", data={model: res})

        async def collect_s3():
            if s3_task:
                gen = await s3_task
                if gen:
                    async for model, res in gen:
                        s3_results[model] = res
                        if res and res.get('content'):
                            emit("stage3_partial", data={model: res})

        await asyncio.gather(collect_s1(), collect_s3())
        
        emit("stage1_complete", data=s1_results)
        if s3_results:
            emit("stage3_complete", data=s3_results)
        
        s1_summary = "\n".join([f"[{m}]: {r.get('content')}" for m, r in s1_results.items() if r and r.get('content')])
        
        if not s1_summary.strip():
            logger.warning("[COUNCIL] Parallel phase failed. Returning direct fallback.")
            fallback_response = await query_model(STAGE6_MODEL, [{"role": "user", "content": sanitized_query}])
            return {
                "final_answer": fallback_response.get("content") if fallback_response else "Service unavailable.",
                "latency_ms": int((time.time() - start_time) * 1000),
                "complexity": complexity
            }

        # Stage 2: Grounding (Sequential because it checks S1 results)
        logger.info("--- Stage 2: Grounding ---")
        emit("stage2_start", "Verifying structural integrity and logic...")
        s2_gen = await query_models_parallel(
            STAGE2_MODELS,
            messages=[{"role": "user", "content": f"Verify the following claims and identify any potential hallucinations or weak logic:\n\n{s1_summary}"}],
            yield_results=True,
            on_activity=on_model_activity
        )
        s2_results = {}
        async for model, res in s2_gen:
            s2_results[model] = res
            if res and res.get('content'):
                emit("stage2_partial", data={model: res})
        
        emit("stage2_complete", data=s2_results)

        # Stage 4: Cross-Pollination
        s4_results = {}
        s4_summary = ""
        if not is_very_simple:
            logger.info("--- Stage 4: Cross-Pollination ---")
            emit("stage4_start", "Mapping conceptual connections...")
            s4_context = f"Exploration:\n{s1_summary}\n\nGrounding:\n{str(s2_results)}"
            s4_gen = await query_models_parallel(
                STAGE4_MODELS,
                messages=[{"role": "user", "content": f"Synthesize these perspectives. Identify structural similarities.\n\n{s4_context}"}],
                yield_results=True,
                on_activity=on_model_activity
            )
            async for model, res in s4_gen:
                s4_results[model] = res
                if res and res.get('content'):
                    emit("stage4_partial", data={model: res})
            
            s4_summary = "\n".join([f"[{m}]: {r.get('content')}" for m, r in s4_results.items() if r and r.get('content')])
            emit("stage4_complete", data=s4_results)

        # Stage 5: Debate
        s5_results = {}
        if not is_very_simple:
            logger.info("--- Stage 5: Debate ---")
            emit("stage5_start", "The Council is debating...")
            s5_gen = await query_models_parallel(
                STAGE5_MODELS,
                messages=[{"role": "user", "content": f"Critique this synthesis. What is missing?\n\n{s4_summary}"}],
                yield_results=True,
                on_activity=on_model_activity
            )
            async for model, res in s5_gen:
                s5_results[model] = res
                if res and res.get('content'):
                    emit("stage5_partial", data={model: res})
            
            emit("stage5_complete", data=s5_results)

        # Stage 6: Synthesis
        logger.info("--- Stage 6: Synthesis ---")
        emit("synthesis_start", "Formulating final consensus...")
        
        deliberation_summary = (
            f"### Deliberation Context\n\n"
            f"**Stage 1 Explorations:**\n{s1_summary}\n\n"
            f"**Stage 2 Grounding:**\n{str(s2_results)}\n\n"
            f"**Stage 3 Technical Specs:**\n{str(s3_results)}\n\n"
            f"**Stage 5 Council Debate:**\n{str(s5_results)}\n"
        )
        
        s6_response = await query_model(
            STAGE6_MODEL,
            messages=[{
                "role": "system", 
                "content": (
                    "You are the Council Head. Produce a 'SUPER ANSWER'.\n"
                    "Format as a TECHNICAL & CONCEPTUAL BRIEF with headers:\n"
                    "## 🧩 CORE LOGIC DECONSTRUCTION\n"
                    "## 🏗️ ARCHITECTURAL MAPPINGS\n"
                    "## ⚙️ TECHNICAL SPECIFICATIONS\n"
                    "## ⚖️ COUNCIL VERDICT & BREAKTHROUGH"
                )
            }, {"role": "user", "content": f"Synthesize this Council deliberation into a final authoritative answer:\n\n{deliberation_summary}\n\nOriginal Query: {sanitized_query}"}],
            on_activity=on_model_activity
        )
        
        final_answer = s6_response.get("content") if s6_response else "The Council was unable to reach consensus."
        
        # 🛡️ 7. Output Safety Check
        emit("synthesis_complete", "Consensus reached. Performing final safety audit...")
        output_validation = self.output_guard.validate(final_answer)
        if not output_validation["is_safe"]:
            logger.warning("Council blocked final answer due to safety policy.")
            final_answer = "The Council has reached a conclusion, but its articulation violates safety policies. Please rephrase your request."

        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(f"--- Pipeline Complete in {latency_ms}ms ---")

        return {
            "final_answer": final_answer,
            "latency_ms": latency_ms,
            "complexity": complexity,
            "stage1": s1_results,
            "stage2": s2_results,
            "stage3": s3_results,
            "stage4": s4_results,
            "stage5": s5_results
        }

# ═══════════════════════════════════════════
#  STANDALONE HELPERS (Backward Compatibility)
# ═══════════════════════════════════════════

orchestrator = CouncilOrchestrator()

async def generate_conversation_title(query: str):
    """Generate a 2-3 word title using the dedicated title model."""
    response = await query_model(TITLE_MODEL, [{"role": "user", "content": f"Create a short, punchy 2-3 word title for this topic: {query}"}])
    return (response.get("content") or "New Exploration").strip().strip('"')

async def run_analogy_pipeline(query: str, history=None, target_domain=None, attachments=None, on_event=None):
    """Standalone wrapper for the class-based orchestrator."""
    return await orchestrator.run_pipeline(query, history, target_domain, attachments, on_event)
