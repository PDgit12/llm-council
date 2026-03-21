"""
File Scanner Module

Handles scanning folders, tracking processed files, and detecting changes.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Optional


class FileScanner:
    """Scans folders and tracks file changes."""

    STATE_FILE = ".copilot_connector_state.json"

    def __init__(self, folder: str, ignore_patterns: Optional[list] = None):
        self.folder = Path(folder).resolve()
        self.ignore_patterns = ignore_patterns or [
            "__pycache__",
            ".git",
            "node_modules",
            ".venv",
            "venv",
            ".env",
            ".pyc",
            ".copilot_connector_state.json",
        ]
        self.state: Dict[str, dict] = {}
        self._load_state()

    def _load_state(self):
        """Load processed files from state file."""
        state_path = self.folder / self.STATE_FILE
        if state_path.exists():
            try:
                with open(state_path, "r") as f:
                    self.state = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.state = {}

    def _save_state(self):
        """Save processed files to state file."""
        state_path = self.folder / self.STATE_FILE
        try:
            with open(state_path, "w") as f:
                json.dump(self.state, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save state: {e}")

    def _should_ignore(self, path: Path) -> bool:
        """Check if file should be ignored."""
        name = path.name
        parts = path.parts

        for pattern in self.ignore_patterns:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern in parts or name == pattern:
                return True
        return False

    def _hash_file(self, path: Path) -> str:
        """Calculate file content hash."""
        try:
            with open(path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except IOError:
            return ""

    def get_files(self, include_all: bool = True) -> Dict[str, str]:
        """Get all files in folder."""
        files = {}

        if not self.folder.exists():
            return files

        for root, dirs, filenames in os.walk(self.folder):
            dirs[:] = [d for d in dirs if not self._should_ignore(Path(root) / d)]

            for filename in filenames:
                filepath = Path(root) / filename

                if self._should_ignore(filepath):
                    continue

                if filepath.stat().st_size > 500_000:  # Skip files > 500KB
                    continue

                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    rel_path = str(filepath.relative_to(self.folder))
                    files[rel_path] = content
                except (IOError, UnicodeDecodeError):
                    continue

        return files

    def get_new_files(self) -> Dict[str, str]:
        """Get only new/modified files since last scan."""
        all_files = self.get_files()
        new_files = {}

        for rel_path, content in all_files.items():
            file_hash = hashlib.md5(content.encode()).hexdigest()

            if rel_path not in self.state:
                new_files[rel_path] = content
            elif self.state[rel_path].get("hash") != file_hash:
                new_files[rel_path] = content

        return new_files

    def mark_processed(self, files: Dict[str, str]):
        """Mark files as processed."""
        for rel_path, content in files.items():
            self.state[rel_path] = {
                "hash": hashlib.md5(content.encode()).hexdigest(),
                "processed_at": str(Path().resolve()),
            }
        self._save_state()

    def reset(self):
        """Reset all tracking."""
        self.state = {}
        self._save_state()
