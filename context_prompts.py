from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Template for context engineering."""

    system_prompt: str
    user_template: str
    description: str


SYSTEM_PROMPTS = {
    "default": """You are an expert AI coding assistant. Your role is to analyze, review, and provide insights 
on the files given to you. Be thorough, practical, and focus on delivering actionable results.
When analyzing code, consider:
- Code quality and readability
- Potential bugs or errors
- Security vulnerabilities
- Performance implications
- Best practices and design patterns
- Documentation needs""",
    "code_review": """You are a senior code reviewer with extensive experience in multiple programming languages.
Your goal is to provide comprehensive code reviews that:
- Identify bugs, security issues, and anti-patterns
- Suggest performance optimizations
- Evaluate code structure and design
- Check for proper error handling
- Verify test coverage considerations
- Ensure adherence to best practices
Provide specific, actionable feedback with code examples where applicable.""",
    "documentation": """You are a technical writer specializing in code documentation. Your role is to:
- Generate clear, comprehensive documentation
- Explain complex concepts in simple terms
- Document APIs, functions, and classes thoroughly
- Create usage examples and tutorials
- Maintain consistency in terminology
Focus on making the code accessible to other developers.""",
    "analysis": """You are a software architect specializing in code analysis. Your approach is to:
- Understand the overall system architecture
- Identify component relationships and dependencies
- Evaluate code organization and modularity
- Assess scalability and maintainability
- Provide architectural recommendations
Think at both micro (file-level) and macro (system-level) perspectives.""",
    "security": """You are a cybersecurity expert specializing in application security. Your focus is on:
- Identifying security vulnerabilities (OWASP Top 10)
- Checking for proper authentication and authorization
- Validating input handling and data sanitization
- Ensuring secure coding practices
- Identifying potential attack vectors
- Recommending security improvements
Be thorough and prioritize critical issues.""",
    "debugging": """You are an expert debugger with deep experience in diagnosing complex issues. Your approach:
- Analyze error symptoms and stack traces
- Identify root causes systematically
- Suggest diagnostic steps and tools
- Provide potential solutions with trade-offs
- Consider edge cases and failure modes
Focus on practical, testable solutions.""",
}


def build_file_context(files: Dict[str, str], include_line_numbers: bool = True) -> str:
    """Build context string from file contents."""
    sections = []

    for filename, content in files.items():
        sections.append(f"## File: {filename}")

        if include_line_numbers:
            lines = content.split("\n")
            numbered_lines = [f"{i + 1:4d} | {line}" for i, line in enumerate(lines)]
            sections.append("```\n" + "\n".join(numbered_lines) + "\n```")
        else:
            sections.append("```\n" + content + "\n```")

        sections.append("")

    return "\n".join(sections)


def build_user_prompt(
    task_prompt: str, files: Dict[str, str], additional_context: Optional[str] = None
) -> str:
    """Build user prompt with files and task."""
    prompt_parts = []

    prompt_parts.append(f"## Task\n{task_prompt}\n")

    prompt_parts.append(f"## Files to Process\n{build_file_context(files)}\n")

    if additional_context:
        prompt_parts.append(f"## Additional Context\n{additional_context}\n")

    return "\n".join(prompt_parts)


class ContextEngineer:
    """
    Context engineering for optimal AI responses.

    Provides structured prompts with proper context to maximize
    the quality and relevance of AI responses.
    """

    def __init__(self, template: str = "default"):
        self.template_name = template
        self.system_prompt = SYSTEM_PROMPTS.get(template, SYSTEM_PROMPTS["default"])

    def for_new_files(
        self,
        files: Dict[str, str],
        task_prompt: str,
        project_context: Optional[str] = None,
        history: Optional[List[str]] = None,
    ) -> tuple[str, str]:
        """
        Build context for new files.

        Args:
            files: Dictionary of filename -> content
            task_prompt: The task to perform
            project_context: Optional project-wide context
            history: Optional previous file processing history

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        user_prompt = build_user_prompt(task_prompt, files, project_context)

        if history:
            history_context = self._build_history_context(history)
            user_prompt += f"\n\n## Previous Processing History\n{history_context}"

        return self.system_prompt, user_prompt

    def _build_history_context(self, history: List[str]) -> str:
        """Build context from processing history."""
        if not history:
            return "No previous processing history."

        sections = ["The following files were already processed:"]

        for i, item in enumerate(history[-5:], 1):
            sections.append(f"{i}. {item}")

        return "\n".join(sections)

    def for_file_diff(
        self, old_content: str, new_content: str, filename: str, task_prompt: str
    ) -> tuple[str, str]:
        """Build context for file diff analysis."""
        user_prompt = f"""## Task
{task_prompt}

## File: {filename}

### Original Content
```
{old_content}
```

### New Content
```
{new_content}
```

Please analyze the changes and their implications.
"""
        return self.system_prompt, user_prompt

    def with_custom_instructions(
        self, custom_instructions: List[str]
    ) -> "ContextEngineer":
        """Add custom instructions to the system prompt."""
        additional_instructions = "\n".join(f"- {inst}" for inst in custom_instructions)
        self.system_prompt += f"\n\nAdditional guidelines:\n{additional_instructions}"
        return self

    def for_batch_processing(
        self,
        batch_files: List[Dict[str, str]],
        task_prompt: str,
        batch_number: int,
        total_batches: int,
    ) -> tuple[str, str]:
        """Build context for batch processing."""
        files = {}
        for item in batch_files:
            files[item["filename"]] = item["content"]

        context = f"Processing batch {batch_number} of {total_batches}"

        return self.for_new_files(files, task_prompt, context)


class PromptLibrary:
    """Library of pre-built prompt templates."""

    @staticmethod
    def code_analysis() -> PromptTemplate:
        return PromptTemplate(
            system_prompt=SYSTEM_PROMPTS["analysis"],
            user_template="""Analyze the following files and provide:
1. Summary of what each file does
2. How files relate to each other
3. Architectural patterns used
4. Potential improvements or issues""",
            description="General code analysis",
        )

    @staticmethod
    def security_scan() -> PromptTemplate:
        return PromptTemplate(
            system_prompt=SYSTEM_PROMPTS["security"],
            user_template="""Perform a security analysis on the following files:
1. Identify vulnerabilities (OWASP Top 10)
2. Check for insecure patterns
3. Recommend security fixes
4. Rate severity of issues found""",
            description="Security vulnerability scanning",
        )

    @staticmethod
    def bug_detection() -> PromptTemplate:
        return PromptTemplate(
            system_prompt=SYSTEM_PROMPTS["debugging"],
            user_template="""Analyze these files for potential bugs:
1. Logic errors
2. Edge cases not handled
3. Null/undefined handling issues
4. Race conditions
5. Memory leaks (if applicable)""",
            description="Bug and error detection",
        )

    @staticmethod
    def documentation_gen() -> PromptTemplate:
        return PromptTemplate(
            system_prompt=SYSTEM_PROMPTS["documentation"],
            user_template="""Generate documentation for these files:
1. API documentation
2. Function/class descriptions
3. Usage examples
4. Parameter descriptions
5. Return value documentation""",
            description="Code documentation generation",
        )

    @staticmethod
    def review() -> PromptTemplate:
        return PromptTemplate(
            system_prompt=SYSTEM_PROMPTS["code_review"],
            user_template="""Review these files comprehensively:
1. Code quality assessment
2. Best practices compliance
3. Performance considerations
4. Test coverage suggestions
5. Specific improvement recommendations""",
            description="Comprehensive code review",
        )
