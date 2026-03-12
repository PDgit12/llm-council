import requests
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class CopilotMessage:
    role: str
    content: str


@dataclass
class CopilotResponse:
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str


class GitHubCopilotClient:
    """GitHub Copilot API client using GitHub's AI API."""

    BASE_URL = "https://api.github.com"

    def __init__(
        self,
        token: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ):
        self.token = token
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        logger.info(f"GitHubCopilotClient initialized with model: {model}")

    def _check_rate_limit(self) -> Dict[str, Any]:
        """Check GitHub API rate limit."""
        try:
            response = self.session.get(f"{self.BASE_URL}/rate_limit", timeout=10)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.warning(f"Failed to check rate limit: {e}")
            return {}

    def chat(
        self, messages: List[CopilotMessage], system_prompt: Optional[str] = None
    ) -> Optional[CopilotResponse]:
        """
        Send a chat request to GitHub Copilot.

        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt

        Returns:
            CopilotResponse object or None on failure
        """
        formatted_messages = []

        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        try:
            response = self.session.post(
                f"{self.BASE_URL}/copilot/text/chat", json=payload, timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                return CopilotResponse(
                    content=data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", ""),
                    model=data.get("model", self.model),
                    usage=data.get("usage", {}),
                    finish_reason=data.get("choices", [{}])[0].get(
                        "finish_reason", "unknown"
                    ),
                )
            elif response.status_code == 403:
                logger.error("Rate limit exceeded or insufficient permissions")
                rate_info = self._check_rate_limit()
                logger.error(f"Rate limit info: {rate_info}")
                return None
            elif response.status_code == 401:
                logger.error("Authentication failed - check your token")
                return None
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def chat_with_files(
        self,
        file_contents: Dict[str, str],
        task_prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,
    ) -> Optional[CopilotResponse]:
        """
        Send files with a task prompt to GitHub Copilot.

        Args:
            file_contents: Dictionary mapping filenames to their contents
            task_prompt: The task to perform on these files
            system_prompt: Optional system prompt
            context: Optional additional context

        Returns:
            CopilotResponse object or None on failure
        """
        files_section = self._format_files_for_prompt(file_contents)

        user_message = f"""## Task
{task_prompt}

## Files to Analyze
{files_section}
"""

        if context:
            user_message += f"\n## Additional Context\n{context}\n"

        messages = [CopilotMessage(role="user", content=user_message)]

        return self.chat(messages, system_prompt)

    def _format_files_for_prompt(self, file_contents: Dict[str, str]) -> str:
        """Format files for the prompt."""
        sections = []
        for filename, content in file_contents.items():
            sections.append(f"### File: {filename}\n```\n{content}\n```")
        return "\n\n".join(sections)

    def streaming_chat(
        self,
        messages: List[CopilotMessage],
        system_prompt: Optional[str] = None,
        callback=None,
    ) -> Optional[str]:
        """
        Send a streaming chat request to GitHub Copilot.

        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt
            callback: Function to call with each chunk

        Returns:
            Full response content or None on failure
        """
        formatted_messages = []

        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }

        full_content = []

        try:
            response = self.session.post(
                f"{self.BASE_URL}/copilot/text/chat",
                json=payload,
                stream=True,
                timeout=120,
            )

            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}")
                return None

            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            import json

                            chunk = json.loads(data)
                            content = (
                                chunk.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content", "")
                            )
                            if content:
                                full_content.append(content)
                                if callback:
                                    callback(content)
                        except:
                            pass

            return "".join(full_content)

        except Exception as e:
            logger.error(f"Streaming request failed: {e}")
            return None


class CopilotClient:
    """
    Unified Copilot client that supports multiple backends:
    - GitHub Copilot API
    - OpenAI API (compatible with Copilot prompts)
    - Anthropic API (for Claude)
    """

    def __init__(
        self,
        token: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        provider: str = "github",
    ):
        self.provider = provider

        if provider == "github":
            self.client = GitHubCopilotClient(
                token=token, model=model, temperature=temperature, max_tokens=max_tokens
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        logger.info(f"CopilotClient initialized with provider: {provider}")

    def chat(
        self, messages: List[CopilotMessage], system_prompt: str = None
    ) -> Optional[CopilotResponse]:
        """Send a chat request."""
        return self.client.chat(messages, system_prompt)

    def chat_with_files(
        self,
        file_contents: Dict[str, str],
        task_prompt: str,
        system_prompt: str = None,
        context: str = None,
    ) -> Optional[CopilotResponse]:
        """Send files with a task prompt."""
        return self.client.chat_with_files(
            file_contents, task_prompt, system_prompt, context
        )

    def streaming_chat(
        self, messages: List[CopilotMessage], system_prompt: str = None, callback=None
    ) -> Optional[str]:
        """Send a streaming chat request."""
        return self.client.streaming_chat(messages, system_prompt, callback)
