"""
Copilot CLI Integration

Uses GitHub Copilot CLI for processing files.
"""

import subprocess
from typing import Dict
from dataclasses import dataclass


@dataclass
class Result:
    success: bool
    response: str = ""
    error: str = ""


class CopilotCLI:
    """Uses GitHub Copilot CLI for file processing."""

    def __init__(self):
        self._check_installation()

    def _check_installation(self):
        """Check if Copilot CLI is installed."""
        try:
            subprocess.run(
                ["gh", "copilot", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "GitHub Copilot CLI not found. Install with:\n"
                "  gh extension install github.com/github/gh-copilot"
            )

    def _build_prompt(self, files: Dict[str, str], task: str) -> str:
        """Build prompt with files."""
        prompt_parts = [f"## Task\n{task}\n"]
        prompt_parts.append("\n## Files to Analyze\n")

        for filename, content in files.items():
            prompt_parts.append(f"\n### {filename}\n```\n{content}\n```\n")

        return "".join(prompt_parts)

    def process(self, files: Dict[str, str], task: str) -> Result:
        """Process files using Copilot CLI."""
        if not files:
            return Result(success=False, error="No files to process")

        prompt = self._build_prompt(files, task)

        try:
            result = subprocess.run(
                ["gh", "copilot", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                return Result(success=True, response=result.stdout)
            else:
                return Result(success=False, error=result.stderr)

        except subprocess.TimeoutExpired:
            return Result(success=False, error="Request timed out")
        except Exception as e:
            return Result(success=False, error=str(e))
