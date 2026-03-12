import logging
import time
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from file_watcher import FileWatcher, FileInfo
from copilot_client import CopilotClient, CopilotMessage
from context_prompts import ContextEngineer, PromptLibrary
from recursive_agent import RecursiveAgentWrapper

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    success: bool
    files_processed: List[str]
    response: str
    error: Optional[str] = None


class CopilotConnector:
    """
    Main orchestrator that coordinates file watching, context engineering,
    and AI processing.
    """

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self._setup_logging()

        self.file_watcher: Optional[FileWatcher] = None
        self.copilot_client: Optional[CopilotClient] = None
        self.recursive_agent: Optional[RecursiveAgentWrapper] = None
        self.context_engineer: Optional[ContextEngineer] = None

        self._initialize_components()

        logger.info("CopilotConnector initialized successfully")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        logger.info(f"Loaded configuration from {config_path}")
        return config

    def _setup_logging(self):
        """Setup logging based on config."""
        log_config = self.config.get("logging", {})
        level = getattr(logging, log_config.get("level", "INFO"))

        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_config.get("file", "copilot_connector.log")),
            ],
        )

    def _initialize_components(self):
        """Initialize all components."""
        watch_config = self.config.get("watch_folder", {})
        file_config = self.config.get("file_watcher", {})
        github_config = self.config.get("github", {})
        ra_config = self.config.get("recursive_agent", {})

        self.file_watcher = FileWatcher(
            watch_folder=self.config.get("watch_folder", ""),
            watch_extensions=self.config.get("watch_extensions", []),
            ignore_patterns=self.config.get("ignore_patterns", []),
            debounce_seconds=self.config.get("processing", {}).get(
                "debounce_seconds", 2
            ),
            state_file=self.config.get("processing", {}).get(
                "state_file", ".processed_files.json"
            ),
        )

        self.copilot_client = CopilotClient(
            token=github_config.get("token", ""),
            model=github_config.get("model", "gpt-4o"),
            temperature=github_config.get("temperature", 0.7),
            max_tokens=github_config.get("max_tokens", 4000),
            provider="github",
        )

        if ra_config.get("enabled", True):
            self.recursive_agent = RecursiveAgentWrapper(
                model=github_config.get("model", "gpt-4o-mini"),
                max_loops=ra_config.get("max_loops", 3),
                temperature=github_config.get("temperature", 0.3),
                similarity_threshold=ra_config.get("similarity_threshold", 0.95),
                verbose=ra_config.get("verbose", False),
            )

        self.context_engineer = ContextEngineer()

        logger.info("All components initialized")

    def scan_and_process(self) -> ProcessingResult:
        """
        Scan folder for new files and process them.

        Returns:
            ProcessingResult with success status and response
        """
        try:
            new_files = self.file_watcher.get_new_files_only()

            if not new_files:
                logger.info("No new files to process")
                return ProcessingResult(
                    success=True, files_processed=[], response="No new files found"
                )

            logger.info(f"Found {len(new_files)} new files to process")

            file_contents = {}
            for file_info in new_files:
                content = self.file_watcher.get_file_content(file_info.path)
                if content:
                    file_contents[file_info.name] = content

            response = self._process_with_ai(file_contents, new_files)

            self.file_watcher.mark_files_processed(new_files)

            return ProcessingResult(
                success=True,
                files_processed=[f.path for f in new_files],
                response=response,
            )

        except Exception as e:
            logger.error(f"Error in scan_and_process: {e}")
            return ProcessingResult(
                success=False, files_processed=[], response="", error=str(e)
            )

    def _process_with_ai(
        self, file_contents: Dict[str, str], file_infos: List[FileInfo]
    ) -> str:
        """Process files with AI (Copilot or recursive agent)."""
        task_prompt = self.config.get("task_prompt", "Analyze these files.")

        if self.recursive_agent:
            logger.info("Using recursive agent for processing")
            return self._process_with_recursive_agent(file_contents, task_prompt)
        else:
            logger.info("Using Copilot API for processing")
            return self._process_with_copilot(file_contents, task_prompt)

    def _process_with_copilot(
        self, file_contents: Dict[str, str], task_prompt: str
    ) -> str:
        """Process files using GitHub Copilot API."""
        system_prompt, user_prompt = self.context_engineer.for_new_files(
            files=file_contents, task_prompt=task_prompt
        )

        messages = [CopilotMessage(role="user", content=user_prompt)]

        response = self.copilot_client.chat(
            messages=messages, system_prompt=system_prompt
        )

        if response:
            return response.content
        else:
            return "Failed to get response from Copilot"

    def _process_with_recursive_agent(
        self, file_contents: Dict[str, str], task_prompt: str
    ) -> str:
        """Process files using recursive agent."""
        system_prompt, user_prompt = self.context_engineer.for_new_files(
            files=file_contents, task_prompt=task_prompt
        )

        result = self.recursive_agent.run(task=user_prompt, context=system_prompt)

        if result.success:
            return result.content
        else:
            return f"Recursive agent error: {result.error}"

    def start_monitoring(self, poll_interval: int = 5, continuous: bool = True):
        """
        Start continuous folder monitoring.

        Args:
            poll_interval: How often to check for new files (seconds)
            continuous: If True, runs forever; if False, runs once
        """
        logger.info("Starting continuous folder monitoring...")

        if continuous:
            while True:
                result = self.scan_and_process()

                if result.success and result.files_processed:
                    logger.info(f"Processed {len(result.files_processed)} files")
                    logger.info(f"Response:\n{result.response}")

                time.sleep(poll_interval)
        else:
            result = self.scan_and_process()

            if result.success and result.files_processed:
                logger.info(f"Processed {len(result.files_processed)} files")
                print(f"\n{'=' * 60}")
                print("AI Response:")
                print(f"{'=' * 60}")
                print(result.response)
                print(f"{'=' * 60}\n")

            return result

    def process_file(self, filepath: str) -> ProcessingResult:
        """
        Process a specific file.

        Args:
            filepath: Path to the file to process

        Returns:
            ProcessingResult
        """
        try:
            file_info = self.file_watcher._get_file_info(filepath)

            if not file_info:
                return ProcessingResult(
                    success=False,
                    files_processed=[],
                    response="",
                    error="Could not read file",
                )

            content = self.file_watcher.get_file_content(filepath)

            if not content:
                return ProcessingResult(
                    success=False,
                    files_processed=[],
                    response="",
                    error="Could not read file content",
                )

            file_contents = {file_info.name: content}

            response = self._process_with_ai(file_contents, [file_info])

            self.file_watcher.mark_files_processed([file_info])

            return ProcessingResult(
                success=True, files_processed=[filepath], response=response
            )

        except Exception as e:
            logger.error(f"Error processing file {filepath}: {e}")
            return ProcessingResult(
                success=False, files_processed=[], response="", error=str(e)
            )

    def reset_state(self):
        """Reset processed files state."""
        self.file_watcher.processed_files = {}
        self.file_watcher._save_state()
        logger.info("State reset - all files will be processed again")

    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            "watching_folder": str(self.file_watcher.watch_folder),
            "processed_files_count": len(self.file_watcher.processed_files),
            "pending_changes": len(self.file_watcher.pending_changes),
            "recursive_agent_enabled": self.recursive_agent is not None,
            "copilot_model": self.copilot_client.model if self.copilot_client else None,
        }
