"""
Streamlit Web UI for GitHub Copilot File Connector

A click-friendly interface to:
1. Enter GitHub token
2. Select/enter folder path
3. Enter custom prompt
4. Process files with GitHub Copilot
5. View responses

Run with: streamlit run streamlit_app.py
"""

import streamlit as st
import os
import json
from pathlib import Path
from typing import Optional

# Page config
st.set_page_config(page_title="GitHub Copilot Connector", page_icon="🤖", layout="wide")


def load_config() -> dict:
    """Load configuration from file."""
    config_file = Path("config.yaml")
    if config_file.exists():
        import yaml

        with open(config_file, "r") as f:
            return yaml.safe_load(f)
    return {}


def save_config(config: dict):
    """Save configuration to file."""
    import yaml

    with open("config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_files_in_folder(folder: str, max_files: int = 50) -> dict:
    """Get files from folder."""
    files = {}

    if not os.path.isdir(folder):
        return files

    count = 0
    for root, dirs, filenames in os.walk(folder):
        if count >= max_files:
            break

        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".") and d not in ("__pycache__", "node_modules")
        ]

        for filename in filenames:
            if count >= max_files:
                break
            if filename.startswith("."):
                continue

            filepath = os.path.join(root, filename)

            try:
                size = os.path.getsize(filepath)
                if size > 100000:  # 100KB limit for UI
                    continue
            except:
                continue

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                rel_path = os.path.relpath(filepath, folder)
                files[rel_path] = content
                count += 1
            except:
                pass

    return files


def process_with_copilot(files: dict, prompt: str, token: str, model: str = "gpt-4o"):
    """Process files with GitHub Copilot."""
    from copilot_client import CopilotClient, CopilotMessage
    from context_prompts import ContextEngineer

    client = CopilotClient(token=token, model=model, temperature=0.7, max_tokens=4000)

    engineer = ContextEngineer()
    system_prompt, user_prompt = engineer.for_new_files(files=files, task_prompt=prompt)

    messages = [CopilotMessage(role="user", content=user_prompt)]
    response = client.chat(messages=messages, system_prompt=system_prompt)

    return response


def main():
    st.title("🤖 GitHub Copilot File Connector")
    st.markdown("Monitor a folder and automatically send new files to GitHub Copilot")

    # Sidebar for configuration
    st.sidebar.header("⚙️ Configuration")

    # GitHub Token
    st.sidebar.subheader("GitHub Authentication")

    # Check for saved token
    saved_token = ""
    token_file = Path(".copilot_connector_config.json")
    if token_file.exists():
        try:
            with open(token_file, "r") as f:
                saved_config = json.load(f)
                saved_token = saved_config.get("github_token", "")
        except:
            pass

    github_token = st.sidebar.text_input(
        "GitHub Token",
        type="password",
        value=saved_token,
        help="Get token from https://github.com/settings/tokens (needs copilot scope)",
    )

    if st.sidebar.checkbox("Save token for later", value=bool(saved_token)):
        if github_token and not saved_token:
            with open(token_file, "w") as f:
                json.dump({"github_token": github_token}, f)
            st.sidebar.success("Token saved!")

    # Model selection
    model = st.sidebar.selectbox(
        "Model", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"], index=0
    )

    # Main content
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📁 Folder Selection")

        # Load saved config
        config = load_config()

        # Folder path input
        default_folder = config.get("watch_folder", os.getcwd())
        folder_path = st.text_input(
            "Folder to monitor",
            value=default_folder,
            help="Path to folder that will be monitored for new files",
        )

        # Verify folder exists
        if folder_path:
            if os.path.isdir(folder_path):
                st.success(f"✓ Folder exists: {folder_path}")

                # Show files in folder
                files = get_files_in_folder(folder_path)
                st.info(f"Found {len(files)} files")

                with st.expander("View files"):
                    for filepath in list(files.keys())[:20]:
                        st.text(f"• {filepath}")
                    if len(files) > 20:
                        st.text(f"... and {len(files) - 20} more")
            else:
                st.error(f"✗ Folder does not exist: {folder_path}")

    with col2:
        st.header("📝 Task Configuration")

        # Task prompt
        task_prompt = st.text_area(
            "Task for GitHub Copilot",
            value=config.get(
                "task_prompt",
                """Analyze the following newly added files and provide:
1. A brief summary of what each file does
2. Potential issues or improvements
3. How these files fit into the overall project structure""",
            ),
            height=150,
            help="The prompt that will be sent to GitHub Copilot with the new files",
        )

        # Quick prompt suggestions
        st.caption("Quick prompts:")
        prompt_col1, prompt_col2, prompt_col3 = st.columns(3)

        if prompt_col1.button("📖 Summarize"):
            st.session_state.prompt = "Provide a brief summary of each file and how they relate to each other."

        if prompt_col2.button("🔍 Code Review"):
            st.session_state.prompt = "Review these files for bugs, security issues, and code quality improvements."

        if prompt_col3.button("📚 Document"):
            st.session_state.prompt = "Generate documentation for these files including function descriptions and usage examples."

        if "prompt" in st.session_state:
            task_prompt = st.session_state.prompt

    # Process button
    st.header("🚀 Process Files")

    col_btn1, col_btn2 = st.columns([1, 1])

    with col_btn1:
        process_once = st.button(
            "📤 Process Files Once",
            type="primary",
            disabled=not (github_token and folder_path and os.path.isdir(folder_path)),
            use_container_width=True,
        )

    with col_btn2:
        continuous_mode = st.button(
            "🔄 Start Continuous Mode",
            disabled=not (github_token and folder_path and os.path.isdir(folder_path)),
            use_container_width=True,
        )

    # Process files
    if process_once:
        if not github_token:
            st.error("Please enter your GitHub token")
        elif not folder_path or not os.path.isdir(folder_path):
            st.error("Please select a valid folder")
        elif not task_prompt:
            st.error("Please enter a task prompt")
        else:
            with st.spinner("Scanning files..."):
                files = get_files_in_folder(folder_path)

            if not files:
                st.warning("No files found in the folder")
            else:
                st.info(f"Processing {len(files)} files...")

                with st.spinner("Sending to GitHub Copilot..."):
                    try:
                        response = process_with_copilot(
                            files, task_prompt, github_token, model
                        )

                        if response:
                            st.success("✓ Response received!")

                            # Display response
                            st.subheader("📋 GitHub Copilot Response")
                            st.markdown(response.content)

                            # Save response
                            response_file = "copilot_response.md"
                            with open(response_file, "w") as f:
                                f.write(f"# GitHub Copilot Response\n\n")
                                f.write(f"## Files Processed\n")
                                for filepath in files.keys():
                                    f.write(f"- {filepath}\n")
                                f.write(f"\n## Task\n{task_prompt}\n\n")
                                f.write(f"## Response\n{response.content}\n")

                            st.success(f"Response saved to {response_file}")
                        else:
                            st.error("Failed to get response from GitHub Copilot")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Continuous mode
    if continuous_mode:
        st.info("Starting continuous monitoring mode...")
        st.info("Press Ctrl+C in terminal to stop")

        try:
            from orchestrator import CopilotConnector

            # Update config
            config = {
                "watch_folder": folder_path,
                "github": {
                    "token": github_token,
                    "model": model,
                    "temperature": 0.7,
                    "max_tokens": 4000,
                },
                "recursive_agent": {
                    "enabled": True,
                    "max_loops": 3,
                    "similarity_threshold": 0.95,
                },
                "task_prompt": task_prompt,
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
                "processing": {
                    "debounce_seconds": 2,
                    "state_file": ".processed_files.json",
                },
            }
            save_config(config)

            st.info("Monitoring for new files... (check terminal for output)")

            # Run connector
            connector = CopilotConnector()
            connector.start_monitoring(poll_interval=5, continuous=True)

        except KeyboardInterrupt:
            st.info("Stopped monitoring")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # Footer
    st.markdown("---")
    st.caption("""
    **How it works:**
    1. The folder is scanned for files
    2. Files are tracked - only NEW files are sent to Copilot
    3. Your task prompt is sent with the files
    4. GitHub Copilot processes and returns insights
    """)


if __name__ == "__main__":
    main()
