"""
Initialization Wizard

Interactive setup for the Copilot Connector.
"""

import os
import sys
import getpass
from pathlib import Path

import yaml


class InitWizard:
    """Interactive initialization wizard."""

    CONFIG_FILE = "copilot_connector.yaml"

    def run(self):
        """Run the initialization wizard."""
        self._print_header()

        print("This wizard will help you set up the GitHub Copilot Connector.\n")

        # Get GitHub token
        token = self._get_token()

        # Get folder
        folder = self._get_folder()

        # Get model
        model = self._get_model()

        # Get prompt
        prompt = self._get_prompt()

        # Save config
        self._save_config(token, folder, model, prompt)

        self._print_success()

    def _print_header(self):
        """Print wizard header."""
        print("\n" + "=" * 60)
        print("  🚀 GitHub Copilot Connector - Setup Wizard")
        print("=" * 60 + "\n")

    def _get_token(self) -> str:
        """Get GitHub token."""
        print("📋 Step 1: GitHub Authentication")
        print("-" * 40)

        # Check environment variable
        env_token = os.environ.get("GITHUB_TOKEN", "")
        if env_token:
            use_env = (
                input(f"Use GITHUB_TOKEN from environment? (y/n): ").strip().lower()
            )
            if use_env == "y":
                print("✅ Using environment token\n")
                return env_token

        print("\nTo get a GitHub Token:")
        print("  1. Go to https://github.com/settings/tokens")
        print("  2. Click 'Generate new token (classic)'")
        print("  3. Select scopes: 'copilot' and 'repo'")
        print("  4. Generate and copy the token\n")

        while True:
            token = getpass.getpass("Enter your GitHub Token: ").strip()

            if not token:
                print("❌ Token cannot be empty. Try again.\n")
                continue

            if len(token) < 10:
                print("❌ Token seems too short. Try again.\n")
                continue

            return token

    def _get_folder(self) -> str:
        """Get folder path."""
        print("\n📁 Step 2: Select Folder")
        print("-" * 40)

        default = os.getcwd()

        while True:
            print(f"\nEnter folder path (press Enter for current directory):")
            folder = input(f"Folder [{default}]: ").strip()

            if not folder:
                folder = default

            folder = os.path.expanduser(folder)
            folder = os.path.abspath(folder)

            if os.path.isdir(folder):
                print(f"✅ Selected: {folder}")
                return folder
            else:
                print(f"❌ Folder does not exist: {folder}")
                print("   Please try again.\n")

    def _get_model(self) -> str:
        """Get model selection."""
        print("\n🧠 Step 3: Select Model")
        print("-" * 40)

        models = [
            ("gpt-4o", "Most capable, fastest"),
            ("gpt-4o-mini", "Fast, cost-effective"),
            ("gpt-4-turbo", "Balanced performance"),
        ]

        print("\nAvailable models:")
        for i, (model, desc) in enumerate(models, 1):
            print(f"  {i}. {model} - {desc}")

        while True:
            choice = input("\nSelect model (1-3) [1]: ").strip()

            if not choice:
                return "gpt-4o"

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(models):
                    return models[idx][0]
                print("❌ Invalid selection. Try again.")
            except ValueError:
                print("❌ Please enter a number.")

    def _get_prompt(self) -> str:
        """Get task prompt."""
        print("\n📝 Step 4: Task Prompt")
        print("-" * 40)

        presets = [
            (
                "1",
                "Code Review",
                "Review these files for bugs, security issues, and code quality improvements.",
            ),
            (
                "2",
                "Documentation",
                "Generate documentation for these files including function descriptions and usage examples.",
            ),
            (
                "3",
                "Summary",
                "Provide a brief summary of each file and how they relate to each other.",
            ),
            ("4", "Custom", None),
        ]

        print("\nChoose a task prompt preset:")
        for choice, name, _ in presets:
            print(f"  {choice}. {name}")

        while True:
            choice = input("\nSelect preset (1-4) [1]: ").strip() or "1"

            if choice == "4":
                print("\nEnter your custom prompt:")
                prompt = input("> ").strip()
                if prompt:
                    return prompt
                print("❌ Prompt cannot be empty.")
                continue

            for c, name, preset in presets:
                if c == choice and preset:
                    print(f"✅ Selected: {name}")
                    return preset

            print("❌ Invalid selection.")

    def _save_config(self, token: str, folder: str, model: str, prompt: str):
        """Save configuration to file."""
        print("\n💾 Saving configuration...")

        config = {
            "watch_folder": folder,
            "github": {
                "token": token,
                "model": model,
                "temperature": 0.7,
                "max_tokens": 4000,
            },
            "recursive_agent": {
                "enabled": True,
                "max_loops": 2,
                "similarity_threshold": 0.95,
            },
            "task_prompt": prompt,
        }

        with open(self.CONFIG_FILE, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        print(f"✅ Configuration saved to {self.CONFIG_FILE}")

    def _print_success(self):
        """Print success message."""
        print("\n" + "=" * 60)
        print("  ✅ Setup Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("  copilot-connector scan <folder>   # Scan folder")
        print("  copilot-connector send             # Send to Copilot")
        print("  copilot-connector watch <folder>  # Watch for changes")
        print("\n")
