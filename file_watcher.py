import os
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Set, Dict, List, Optional
from dataclasses import dataclass, field
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    path: str
    name: str
    extension: str
    size: int
    modified_time: float
    content_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "name": self.name,
            "extension": self.extension,
            "size": self.size,
            "modified_time": self.modified_time,
            "content_hash": self.content_hash,
        }


@dataclass
class FileChanges:
    new_files: List[FileInfo] = field(default_factory=list)
    modified_files: List[FileInfo] = field(default_factory=list)
    deleted_files: List[str] = field(default_factory=list)


class FileWatcher(FileSystemEventHandler):
    def __init__(
        self,
        watch_folder: str,
        watch_extensions: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
        debounce_seconds: float = 2.0,
        state_file: str = ".processed_files.json",
    ):
        super().__init__()

        self.watch_folder = Path(watch_folder).resolve()
        self.watch_extensions = set(watch_extensions) if watch_extensions else set()
        self.ignore_patterns = set(ignore_patterns) if ignore_patterns else set()
        self.debounce_seconds = debounce_seconds
        self.state_file = Path(state_file)

        self.processed_files: Dict[str, dict] = {}
        self.pending_changes: Dict[str, float] = {}
        self.observer: Optional[Observer] = None

        self._load_state()
        logger.info(f"FileWatcher initialized for folder: {self.watch_folder}")

    def _load_state(self):
        """Load previously processed files from state file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    self.processed_files = json.load(f)
                logger.info(
                    f"Loaded {len(self.processed_files)} processed files from state"
                )
            except Exception as e:
                logger.warning(f"Failed to load state file: {e}")
                self.processed_files = {}

    def _save_state(self):
        """Save processed files to state file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.processed_files, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _should_ignore(self, path: str) -> bool:
        """Check if the file should be ignored based on patterns."""
        path_obj = Path(path)
        name = path_obj.name

        for pattern in self.ignore_patterns:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern in str(path_obj.parts):
                return True
            elif name == pattern:
                return True

        return False

    def _should_watch(self, path: str) -> bool:
        """Check if the file should be watched based on extensions."""
        if not self.watch_extensions:
            return True

        ext = Path(path).suffix.lower()
        return ext in self.watch_extensions

    def _get_file_hash(self, path: str) -> str:
        """Calculate MD5 hash of file content."""
        try:
            with open(path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash file {path}: {e}")
            return ""

    def _get_file_info(self, path: str) -> Optional[FileInfo]:
        """Get file information."""
        try:
            path_obj = Path(path)
            if not path_obj.exists() or not path_obj.is_file():
                return None

            stat = path_obj.stat()

            return FileInfo(
                path=str(path),
                name=path_obj.name,
                extension=path_obj.suffix.lower(),
                size=stat.st_size,
                modified_time=stat.st_mtime,
                content_hash=self._get_file_hash(path),
            )
        except Exception as e:
            logger.error(f"Failed to get file info for {path}: {e}")
            return None

    def _is_new_file(self, file_info: FileInfo) -> bool:
        """Check if this is a new file not previously processed."""
        return file_info.path not in self.processed_files

    def _is_modified(self, file_info: FileInfo) -> bool:
        """Check if file has been modified since last processing."""
        if file_info.path not in self.processed_files:
            return False

        prev = self.processed_files[file_info.path]

        if file_info.content_hash and prev.get("content_hash"):
            return file_info.content_hash != prev["content_hash"]

        return file_info.modified_time > prev.get("modified_time", 0)

    def _mark_processed(self, file_info: FileInfo):
        """Mark a file as processed."""
        self.processed_files[file_info.path] = file_info.to_dict()
        self._save_state()

    def scan_folder(self) -> FileChanges:
        """Scan the folder for new and modified files."""
        changes = FileChanges()

        if not self.watch_folder.exists():
            logger.error(f"Watch folder does not exist: {self.watch_folder}")
            return changes

        for root, dirs, files in os.walk(self.watch_folder):
            dirs[:] = [
                d for d in dirs if not self._should_ignore(os.path.join(root, d))
            ]

            for filename in files:
                filepath = os.path.join(root, filename)

                if self._should_ignore(filepath):
                    continue

                if not self._should_watch(filepath):
                    continue

                file_info = self._get_file_info(filepath)
                if not file_info:
                    continue

                if self._is_new_file(file_info):
                    changes.new_files.append(file_info)
                    logger.info(f"New file detected: {filepath}")
                elif self._is_modified(file_info):
                    changes.modified_files.append(file_info)
                    logger.info(f"Modified file detected: {filepath}")

        deleted = set(self.processed_files.keys()) - {
            os.path.join(root, f)
            for root, _, files in os.walk(self.watch_folder)
            for f in files
            if not self._should_ignore(os.path.join(root, f))
        }

        for path in deleted:
            changes.deleted_files.append(path)
            if path in self.processed_files:
                del self.processed_files[path]

        return changes

    def get_new_files_only(self) -> List[FileInfo]:
        """Get only new files since last scan."""
        changes = self.scan_folder()
        return changes.new_files

    def mark_files_processed(self, files: List[FileInfo]):
        """Mark files as processed after Copilot has handled them."""
        for file_info in files:
            self._mark_processed(file_info)
        logger.info(f"Marked {len(files)} files as processed")

    def get_file_content(self, filepath: str, max_size: int = 500000) -> Optional[str]:
        """Read file content for sending to Copilot."""
        try:
            path = Path(filepath)
            if not path.exists():
                return None

            if path.stat().st_size > max_size:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    first_lines = [next(f) for _ in range(100) if f]
                return (
                    f"File too large ({path.stat().st_size} bytes). First 100 lines:\n\n"
                    + "".join(first_lines)
                )

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {filepath}: {e}")
            return None

    def start_watching(self, callback):
        """Start watching the folder for changes."""
        self.observer = Observer()
        self.observer.schedule(self, str(self.watch_folder), recursive=True)
        self.observer.start()
        logger.info(f"Started watching folder: {self.watch_folder}")

    def stop_watching(self):
        """Stop watching the folder."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Stopped watching folder")

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if event.is_directory:
            return

        if self._should_ignore(event.src_path):
            return

        if not self._should_watch(event.src_path):
            return

        self.pending_changes[event.src_path] = time.time()
        logger.info(f"File created: {event.src_path}")

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return

        if self._should_ignore(event.src_path):
            return

        if not self._should_watch(event.src_path):
            return

        self.pending_changes[event.src_path] = time.time()
        logger.info(f"File modified: {event.src_path}")

    def get_pending_changes(self) -> List[FileInfo]:
        """Get files that have settled (not being modified recently)."""
        current_time = time.time()
        settled_files = []

        to_remove = []
        for filepath, timestamp in self.pending_changes.items():
            if current_time - timestamp >= self.debounce_seconds:
                file_info = self._get_file_info(filepath)
                if file_info:
                    settled_files.append(file_info)
                to_remove.append(filepath)

        for filepath in to_remove:
            del self.pending_changes[filepath]

        new_files = [f for f in settled_files if self._is_new_file(f)]
        modified_files = [f for f in settled_files if self._is_modified(f)]

        return new_files, modified_files
