# Copilot Council

A CLI tool that monitors folders for new files and sends them to GitHub Copilot for automated code review and analysis. Uses incremental file tracking to only send new or modified files.

## Features

- **Incremental Processing** - Only sends new/modified files, not the entire folder
- **File Tracking** - Tracks processed files to avoid duplicate analysis
- **GitHub Copilot CLI** - Uses the official `gh copilot` extension
- **Watch Mode** - Automatically detects and processes new files
- **Custom Prompts** - Configure what Copilot should analyze

## Requirements

- [GitHub CLI](https://cli.github.com/)
- [Copilot CLI extension](https://docs.github.com/en/copilot/github-copilot-in-the-cli)
- Python 3.8+

## Installation

```bash
# Install GitHub CLI if needed
brew install gh

# Verify Copilot extension
gh copilot --version
```

## Quick Start

```bash
# Scan a folder
python main_cli.py scan ./my-project

# Send new files to Copilot
python main_cli.py send ./my-project -p "Review for bugs and security issues"

# Watch folder (auto-send new files)
python main_cli.py watch ./my-project
```

## Commands

| Command | Description |
|---------|-------------|
| `scan <folder>` | List files in folder |
| `send <folder> -p "prompt"` | Send new files to Copilot |
| `send <folder> --all` | Send ALL files (ignore tracking) |
| `watch <folder>` | Watch for new files |
| `status` | Show tracking status |
| `reset` | Clear file tracking |

## How It Works

1. Scanner detects files in the specified folder
2. Compares against tracked files (stored in `.copilot_connector_state.json`)
3. Only new/modified files are sent to Copilot CLI
4. Response is displayed in terminal

## Configuration

Edit `copilot_connector.yaml` to customize default folder, model selection, and task prompts.

## License

MIT
