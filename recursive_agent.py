import os
import sys
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RecursiveAgentResponse:
    content: str
    iterations: int
    transcript: str
    success: bool
    error: Optional[str] = None


class RecursiveAgentWrapper:
    """
    Wrapper for the recursive-agents framework.

    This provides a simple interface to use the three-phase
    (Draft -> Critique -> Revision) self-improving agent pattern.
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_loops: int = 3,
        temperature: float = 0.3,
        similarity_threshold: float = 0.95,
        verbose: bool = False,
    ):
        self.model = model
        self.max_loops = max_loops
        self.temperature = temperature
        self.similarity_threshold = similarity_threshold
        self.verbose = verbose

        self.run_log: List[Dict[str, Any]] = []

        self._setup_client(openai_api_key)

        logger.info(f"RecursiveAgentWrapper initialized with model: {model}")

    def _setup_client(self, api_key: Optional[str]):
        """Setup the LLM client."""
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
            self.use_langchain = False
            logger.info("Using OpenAI client")
        except ImportError:
            try:
                from langchain_openai import ChatOpenAI

                self.client = ChatOpenAI(
                    model=self.model, temperature=self.temperature, api_key=api_key
                )
                self.use_langchain = True
                logger.info("Using LangChain OpenAI client")
            except ImportError:
                logger.error(
                    "Neither openai nor langchain_openai packages are installed"
                )
                raise ImportError("Please install openai or langchain_openai")

    def _cosine_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple cosine similarity between two texts."""
        from collections import Counter
        import math

        words1 = Counter(text1.lower().split())
        words2 = Counter(text2.lower().split())

        all_words = set(words1.keys()) | set(words2.keys())

        if not all_words:
            return 0.0

        dot_product = sum(words1.get(w, 0) * words2.get(w, 0) for w in all_words)
        mag1 = math.sqrt(sum(v**2 for v in words1.values()))
        mag2 = math.sqrt(sum(v**2 for v in words2.values()))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM with prompts."""
        if self.use_langchain:
            from langchain.schema import HumanMessage, SystemMessage

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            response = self.client.invoke(messages)
            return response.content
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
            )
            return response.choices[0].message.content

    def _draft(self, task: str, context: Optional[str] = None) -> str:
        """Phase 1: Generate initial draft."""
        system_prompt = """You are an expert AI assistant. Provide a thorough, accurate response to the user's task.
Focus on clarity, completeness, and practical insights."""

        user_prompt = task
        if context:
            user_prompt = f"{context}\n\n---\n\n{task}"

        return self._call_llm(system_prompt, user_prompt)

    def _critique(self, draft: str, task: str) -> str:
        """Phase 2: Critique the draft."""
        system_prompt = """You are a critical reviewer. Analyze the provided response and identify:
1. Missing or incomplete information
2. Potential errors or inaccuracies
3. Areas that could be improved or expanded
4. Suggestions for better clarity or actionability

Be specific and constructive in your feedback."""

        user_prompt = f"""Task: {task}

Draft Response:
{draft}

Provide a detailed critique focusing on improvements."""

        return self._call_llm(system_prompt, user_prompt)

    def _revise(self, draft: str, critique: str, task: str) -> str:
        """Phase 3: Revise based on critique."""
        system_prompt = """You are an expert reviser. Improve the draft based on the critique provided.
Keep what is good, fix what is wrong, and enhance where possible.
Provide a polished, improved response."""

        user_prompt = f"""Original Task: {task}

Current Draft:
{draft}

Critique:
{critique}

Please revise the draft to address the critique and provide an improved response."""

        return self._call_llm(system_prompt, user_prompt)

    def run(
        self,
        task: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> RecursiveAgentResponse:
        """
        Run the recursive agent on a task.

        Args:
            task: The task to perform
            context: Additional context for the task
            system_prompt: Custom system prompt

        Returns:
            RecursiveAgentResponse with content, iterations, and transcript
        """
        self.run_log = []

        try:
            draft = self._draft(task, context)

            self.run_log.append({"iteration": 1, "phase": "draft", "content": draft})

            if self.verbose:
                print(f"\n=== Iteration 1: Draft ===\n{draft[:500]}...")

            for i in range(1, self.max_loops + 1):
                critique = self._critique(draft, task)

                self.run_log.append(
                    {"iteration": i, "phase": "critique", "content": critique}
                )

                if self.verbose:
                    print(f"\n=== Critique {i} ===\n{critique[:500]}...")

                revised = self._revise(draft, critique, task)

                self.run_log.append(
                    {"iteration": i, "phase": "revision", "content": revised}
                )

                if self.verbose:
                    print(f"\n=== Revision {i} ===\n{revised[:500]}...")

                similarity = self._cosine_similarity(draft, revised)

                if self.verbose:
                    print(f"\nSimilarity: {similarity:.3f}")

                if similarity >= self.similarity_threshold:
                    logger.info(
                        f"Converged at iteration {i} with similarity {similarity:.3f}"
                    )
                    break

                draft = revised

            return RecursiveAgentResponse(
                content=revised,
                iterations=len(self.run_log) // 2,
                transcript=self.transcript_as_markdown(),
                success=True,
            )

        except Exception as e:
            logger.error(f"Recursive agent failed: {e}")
            return RecursiveAgentResponse(
                content="", iterations=0, transcript="", success=False, error=str(e)
            )

    def transcript_as_markdown(self) -> str:
        """Generate a markdown transcript of the agent's thinking."""
        if not self.run_log:
            return "No iterations recorded."

        lines = []
        current_iteration = None

        for entry in self.run_log:
            iteration = entry.get("iteration")
            phase = entry.get("phase")
            content = entry.get("content", "")

            if iteration != current_iteration:
                current_iteration = iteration
                lines.append(f"\n### Iteration {iteration}")

            phase_title = phase.capitalize()
            lines.append(f"**{phase_title}**:\n{content}\n")

        return "\n".join(lines)

    def __call__(self, task: str, context: Optional[str] = None) -> str:
        """Make the agent callable."""
        result = self.run(task, context)
        return result.content


class RecursiveAgentFactory:
    """Factory for creating recursive agents with different configurations."""

    @staticmethod
    def create_code_reviewer(
        api_key: Optional[str] = None, model: str = "gpt-4o-mini"
    ) -> RecursiveAgentWrapper:
        """Create a code review agent."""
        return RecursiveAgentWrapper(
            openai_api_key=api_key,
            model=model,
            max_loops=3,
            temperature=0.2,
            similarity_threshold=0.90,
        )

    @staticmethod
    def create_analyzer(
        api_key: Optional[str] = None, model: str = "gpt-4o-mini"
    ) -> RecursiveAgentWrapper:
        """Create a general analysis agent."""
        return RecursiveAgentWrapper(
            openai_api_key=api_key,
            model=model,
            max_loops=2,
            temperature=0.5,
            similarity_threshold=0.95,
        )

    @staticmethod
    def create_documentation(
        api_key: Optional[str] = None, model: str = "gpt-4o-mini"
    ) -> RecursiveAgentWrapper:
        """Create a documentation agent."""
        return RecursiveAgentWrapper(
            openai_api_key=api_key,
            model=model,
            max_loops=3,
            temperature=0.3,
            similarity_threshold=0.92,
        )
