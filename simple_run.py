#!/usr/bin/env python3
"""
Simple CLI for GitHub Copilot File Connector

Usage:
    python simple_run.py --token "your_github_token" --folder "./test_folder" --prompt "Analyze these files"
"""

import argparse
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(description="GitHub Copilot File Connector")

    parser.add_argument("--token", required=True, help="GitHub Personal Access Token")
    parser.add_argument("--folder", required=True, help="Folder to scan")
    parser.add_argument(
        "--prompt",
        default="Analyze these files and provide a summary",
        help="Task prompt",
    )
    parser.add_argument("--model", default="gpt-4o", help="Model to use")

    args = parser.parse_args()

    # Verify folder exists
    if not os.path.isdir(args.folder):
        print(f"Error: Folder does not exist: {args.folder}")
        sys.exit(1)

    # Get files
    print(f"Scanning folder: {args.folder}")
    files = {}

    for root, dirs, filenames in os.walk(args.folder):
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".") and d not in ("__pycache__", "node_modules")
        ]

        for filename in filenames:
            if filename.startswith("."):
                continue

            filepath = os.path.join(root, filename)

            try:
                size = os.path.getsize(filepath)
                if size > 100000:
                    continue
            except:
                continue

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                rel_path = os.path.relpath(filepath, args.folder)
                files[rel_path] = content
            except:
                pass

    print(f"Found {len(files)} files")

    if not files:
        print("No files found!")
        sys.exit(1)

    # Process with Copilot
    print("Sending to GitHub Copilot...")

    from copilot_client import CopilotClient, CopilotMessage
    from context_prompts import ContextEngineer

    client = CopilotClient(
        token=args.token, model=args.model, temperature=0.7, max_tokens=4000
    )

    engineer = ContextEngineer()
    system_prompt, user_prompt = engineer.for_new_files(
        files=files, task_prompt=args.prompt
    )

    messages = [CopilotMessage(role="user", content=user_prompt)]

    try:
        response = client.chat(messages=messages, system_prompt=system_prompt)

        if response:
            print("\n" + "=" * 60)
            print("GITHUB COPILOT RESPONSE")
            print("=" * 60)
            print(response.content)
            print("=" * 60)

            # Save response
            with open("copilot_response.md", "w") as f:
                f.write(f"# GitHub Copilot Response\n\n")
                f.write(f"## Files\n")
                for p in files.keys():
                    f.write(f"- {p}\n")
                f.write(f"\n## Task\n{args.prompt}\n\n")
                f.write(f"## Response\n{response.content}\n")

            print(f"\nSaved to copilot_response.md")
        else:
            print("Failed to get response from GitHub Copilot")
            print("Check your token and try again")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
