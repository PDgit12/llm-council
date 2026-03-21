# Copilot Sentinel

Automated file monitoring and code review with GitHub Copilot.

## Description

Copilot Sentinel watches a folder for new or modified files and automatically sends them to GitHub Copilot for analysis. It tracks processed files and only sends new changes, enabling continuous automated code review.

## Features

- **Incremental Processing** - Only sends new/modified files, not the entire codebase
- **File Tracking** - Tracks processed files to avoid duplicate analysis
- **GitHub Copilot CLI** - Uses the official `gh copilot` extension
- **Watch Mode** - Continuous monitoring with automatic processing

## Requirements

- Python 3.8+
- [GitHub CLI](https://cli.github.com/)
- [Copilot CLI extension](https://docs.github.com/en/copilot/github-copilot-in-the-cli)

## Setup

```bash
# Verify GitHub CLI and Copilot
gh copilot --version
```

## Usage

```bash
# Scan folder
python main_cli.py scan ./my-project

# Send new files to Copilot
python main_cli.py send ./my-project -p "Review for bugs"

# Watch folder continuously
python main_cli.py watch ./my-project
```

## Commands

| Command | Description |
|---------|-------------|
| `scan <folder>` | List files in folder |
| `send <folder> -p "prompt"` | Send new files to Copilot |
| `send <folder> --all` | Send all files |
| `watch <folder>` | Watch for new files |
| `status` | Show tracking status |
| `reset` | Clear tracking |

## How It Works

1. Scanner walks the folder and reads file contents
2. Compares against tracked state in `.copilot_connector_state.json`
3. Only new/modified files are sent to Copilot CLI
4. Response is displayed in terminal

## License

MIT
