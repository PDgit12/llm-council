#!/usr/bin/env python3
"""
Interactive CLI for GitHub Copilot File Connector

This provides a simple interactive interface to:
1. Enter GitHub token
2. Select folder to monitor
3. Enter custom prompt
4. Process files with GitHub Copilot
"""

import os
import sys
import json
import getpass
from pathlib import Path
from typing import Optional

# Try to import colorama for colored output
try:
    from colorama import init, Fore, Style

    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = ""

    class Style:
        RESET_ALL = BRIGHT = ""


def print_colored(text: str, color: str = "GREEN"):
    """Print colored text."""
    if COLORAMA_AVAILABLE:
        color_code = getattr(Fore, color.upper(), "")
        print(f"{color_code}{text}{Style.RESET_ALL}")
    else:
        print(text)


def print_header(text: str):
    """Print header text."""
    print_colored(f"\n{'=' * 60}", "CYAN")
    print_colored(f"  {text}", "CYAN")
    print_colored(f"{'=' * 60}\n", "CYAN")


def print_success(text: str):
    """Print success text."""
    print_colored(f"✓ {text}", "GREEN")


def print_error(text: str):
    """Print error text."""
    print_colored(f"✗ {text}", "RED")


def print_info(text: str):
    """Print info text."""
    print_colored(f"ℹ {text}", "YELLOW")


def get_valid_folder() -> str:
    """Get a valid folder path from user."""
    while True:
        print("\nEnter the folder path to monitor:")
        print("  (press Enter to use current directory)")

        folder = input("\nFolder path: ").strip()

        if not folder:
            folder = os.getcwd()

        # Expand user home directory
        folder = os.path.expanduser(folder)

        # Make absolute
        folder = os.path.abspath(folder)

        if os.path.isdir(folder):
            print_success(f"Valid folder: {folder}")
            return folder
        else:
            print_error(f"Folder does not exist: {folder}")
            print_info("Please enter a valid folder path")


def get_github_token() -> str:
    """Get GitHub token from user or config file."""
    # Check for existing token
    config_file = Path(".copilot_connector_config.json")

    if config_file.exists():
        print_info("Found existing configuration")
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            if config.get("github_token"):
                use_existing = (
                    input("\nUse existing GitHub token? (y/n): ").strip().lower()
                )
                if use_existing == "y":
                    print_success("Using existing token")
                    return config["github_token"]
        except:
            pass

    print("\n" + "=" * 50)
    print_info("To get a GitHub Token:")
    print("  1. Go to https://github.com/settings/tokens")
    print("  2. Click 'Generate new token (classic)'")
    print("  3. Select scopes: 'copilot' and 'repo'")
    print("  4. Generate and copy the token")
    print("=" * 50 + "\n")

    while True:
        token = getpass.getpass("Enter your GitHub Personal Access Token: ").strip()

        if not token:
            print_error("Token cannot be empty")
            continue

        if len(token) < 10:
            print_error("Token seems too short")
            continue

        # Save for future use
        save = input("\nSave token for future use? (y/n): ").strip().lower()
        if save == "y":
            try:
                config = {"github_token": token}
                with open(config_file, "w") as f:
                    json.dump(config, f)
                print_success("Token saved to .copilot_connector_config.json")
            except Exception as e:
                print_info(f"Could not save token: {e}")

        return token


def get_task_prompt() -> str:
    """Get the task prompt from user."""
    print("\n" + "-" * 50)
    print("Enter the task you want GitHub Copilot to perform")
    print("on the new files. Some examples:")
    print("-" * 50)
    print("""
  • "Analyze these files and provide a summary"
  • "Review the code for bugs and security issues"
  • "Generate documentation for these files"
  • "Suggest performance optimizations"
  • "Explain what these files do to a new developer"
    """)
    print("-" * 50)

    print("\nEnter your task prompt (press Enter for default):")
    prompt = input("\n> ").strip()

    if not prompt:
        prompt = """Analyze the following newly added files and provide:
1. A brief summary of what each file does
2. Potential issues or improvements  
3. How these files fit into the overall project structure"""
        print_info("Using default prompt")

    return prompt


def get_files_to_process(folder: str) -> dict:
    """Get all files in folder."""
    files = {}

    for root, dirs, filenames in os.walk(folder):
        # Skip hidden and common ignore patterns
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".")
            and d not in ("__pycache__", "node_modules", "venv")
        ]

        for filename in filenames:
            if filename.startswith("."):
                continue

            filepath = os.path.join(root, filename)

            # Skip large files
            try:
                size = os.path.getsize(filepath)
                if size > 500000:  # 500KB limit
                    continue
            except:
                continue

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                rel_path = os.path.relpath(filepath, folder)
                files[rel_path] = content
            except:
                pass

    return files


def update_config_file(folder: str, token: str, prompt: str):
    """Update the config.yaml file."""
    import yaml

    config = {
        "watch_folder": folder,
        "github": {
            "token": token,
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 4000,
        },
        "recursive_agent": {
            "enabled": True,
            "max_loops": 3,
            "similarity_threshold": 0.95,
        },
        "task_prompt": prompt,
        "watch_extensions": [
            ".py",
            ".js",
            ".ts",
            ".json",
            ".yaml",
            ".yml",
            ".md",
            ".txt",
        ],
        "ignore_patterns": [
            "__pycache__",
            ".git",
            "node_modules",
            ".venv",
            "venv",
            ".env",
            "*.pyc",
        ],
        "processing": {"debounce_seconds": 2, "state_file": ".processed_files.json"},
    }

    with open("config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    print_success("Configuration saved to config.yaml")


def run_interactive():
    """Run the interactive setup and execution."""
    print_header("GitHub Copilot File Connector")

    print_info("This tool will:")
    print("  1. Monitor a folder for new files")
    print("  2. Send new files to GitHub Copilot")
    print("  3. Process them with your custom prompt")
    print("  4. Only send NEW files (not the whole folder)")

    # Step 1: Get GitHub token
    print_header("Step 1: GitHub Authentication")
    token = get_github_token()

    # Step 2: Get folder
    print_header("Step 2: Select Folder")
    folder = get_valid_folder()

    # Step 3: Get task prompt
    print_header("Step 3: Task Configuration")
    prompt = get_task_prompt()

    # Step 4: Save configuration
    print_header("Step 4: Saving Configuration")
    update_config_file(folder, token, prompt)

    # Step 5: Get files
    print_header("Step 5: Scanning Files")
    print_info(f"Scanning folder: {folder}")

    files = get_files_to_process(folder)

    if not files:
        print_error("No files found in the folder")
        return

    print_success(f"Found {len(files)} files")

    for i, filepath in enumerate(files.keys(), 1):
        print(f"  {i}. {filepath}")

    # Step 6: Process with Copilot
    print_header("Step 6: Processing with GitHub Copilot")
    print_info("Sending files to GitHub Copilot...")
    print_info("This may take a moment...\n")

    try:
        from copilot_client import CopilotClient, CopilotMessage
        from context_prompts import ContextEngineer

        # Initialize client
        client = CopilotClient(
            token=token, model="gpt-4o", temperature=0.7, max_tokens=4000
        )

        # Build context
        engineer = ContextEngineer()
        system_prompt, user_prompt = engineer.for_new_files(
            files=files, task_prompt=prompt
        )

        # Send to Copilot
        messages = [CopilotMessage(role="user", content=user_prompt)]
        response = client.chat(messages=messages, system_prompt=system_prompt)

        if response:
            print_header("GitHub Copilot Response")
            print(response.content)

            # Save response
            response_file = "copilot_response.md"
            with open(response_file, "w") as f:
                f.write(f"# GitHub Copilot Response\n\n")
                f.write(f"## Files Processed\n")
                for filepath in files.keys():
                    f.write(f"- {filepath}\n")
                f.write(f"\n## Task\n{prompt}\n\n")
                f.write(f"## Response\n{response.content}\n")

            print_success(f"\nResponse saved to {response_file}")
        else:
            print_error("Failed to get response from GitHub Copilot")
            print_info("Check your token and try again")

    except Exception as e:
        print_error(f"Error: {e}")
        import traceback

        traceback.print_exc()

    print_header("Done!")


def run_continuous_mode():
    """Run in continuous monitoring mode."""
    print_header("Continuous Monitoring Mode")
    print_info("Monitoring folder for new files...")
    print_info("Press Ctrl+C to stop\n")

    try:
        from orchestrator import CopilotConnector

        connector = CopilotConnector()
        connector.start_monitoring(poll_interval=5, continuous=True)
    except KeyboardInterrupt:
        print("\n")
        print_info("Stopped monitoring")
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        run_continuous_mode()
    else:
        run_interactive()
