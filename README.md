# Copilot Sentinel

A CLI tool that monitors folders for new or modified files and automatically sends them to GitHub Copilot for code review, analysis, and documentation.

## Overview

Copilot Sentinel watches a folder and detects new files as they are added. When new files are detected, it sends them to GitHub Copilot CLI with a configurable prompt. This enables automated, continuous code review without manual intervention.

### Key Features

- **Automatic Detection** - Monitors folders and detects new/modified files in real-time
- **Incremental Processing** - Only sends new files, not the entire codebase
- **File Tracking** - Maintains state to avoid processing the same files twice
- **GitHub Copilot Integration** - Uses the official `gh copilot` CLI
- **Watch Mode** - Continuous monitoring with automatic analysis

## Requirements

- Python 3.8 or higher
- [GitHub CLI](https://cli.github.com/)
- [GitHub Copilot CLI extension](https://docs.github.com/en/copilot/github-copilot-in-the-cli)

### Installation

```bash
# Install GitHub CLI
brew install gh

# Login to GitHub
gh auth login

# Verify Copilot CLI is available
gh copilot --version
```

## Quick Start

```bash
# Scan a folder to see available files
python main_cli.py scan ./my-project

# Send new files to Copilot for review
python main_cli.py send ./my-project -p "Review for security issues"

# Watch folder continuously
python main_cli.py watch ./my-project
```

## Commands

| Command | Description |
|---------|-------------|
| `scan <folder>` | List all files in folder |
| `send <folder> -p "prompt"` | Send new files to Copilot |
| `send <folder> --all` | Send all files (ignore tracking) |
| `watch <folder>` | Watch folder continuously |
| `status` | Show tracking status |
| `reset` | Clear all tracking |

## Usage Guide

### Scanning Files

Before sending files, scan the folder to see what will be processed:

```bash
python main_cli.py scan ./my-project
```

Output:
```
Found 5 files in ./my-project:
  1. app.py
  2. auth.py
  3. models.py
  4. database.py
  5. config.py
```

### Sending Files for Review

Send new files to Copilot with a specific task:

```bash
python main_cli.py send ./my-project -p "Review for security vulnerabilities"
```

Only new files since the last scan will be sent. Previously processed files are tracked in `.copilot_connector_state.json`.

### Sending All Files

To ignore tracking and send all files:

```bash
python main_cli.py send ./my-project --all -p "Explain this codebase"
```

### Continuous Monitoring

Watch a folder and automatically process new files:

```bash
python main_cli.py watch ./my-project -p "Analyze new files"
```

The tool will check for new files every 5 seconds. Use `--interval` to change:

```bash
python main_cli.py watch ./my-project --interval 10
```

### Custom Prompts

Configure what Copilot should do with your files:

```bash
# Security review
python main_cli.py send ./project -p "Review for security issues and vulnerabilities"

# Code quality
python main_cli.py send ./project -p "Suggest performance improvements"

# Documentation
python main_cli.py send ./project -p "Generate documentation"

# Bug analysis
python main_cli.py send ./project -p "Identify potential bugs"
```

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    Your Project                           │
│                                                         │
│   file1.py   file2.py   file3.py   new_file.py         │
│       │           │           │           │              │
│       └───────────┴───────────┴───────────┘              │
│                         │                                 │
│              ┌──────────▼──────────┐                     │
│              │   File Scanner      │                     │
│              │   (tracks state)    │                     │
│              └──────────┬──────────┘                     │
│                         │                                 │
│              ┌──────────▼──────────┐                     │
│              │   New Files Only    │                     │
│              │   (new_file.py)     │                     │
│              └──────────┬──────────┘                     │
│                         │                                 │
│              ┌──────────▼──────────┐                     │
│              │   GitHub Copilot    │                     │
│              │       CLI           │                     │
│              └──────────┬──────────┘                     │
│                         │                                 │
│                    Analysis                               │
└─────────────────────────────────────────────────────────┘
```

1. Scanner walks the folder and reads file contents
2. Compares against tracked state in `.copilot_connector_state.json`
3. Only new/modified files are sent to Copilot CLI
4. Response is displayed in terminal

## File Tracking

The tool maintains a state file (`.copilot_connector_state.json`) in the monitored folder. This file stores:

- File paths that have been processed
- Content hashes to detect modifications
- Timestamp of last processing

To reprocess all files:

```bash
python main_cli.py reset
python main_cli.py send ./project --all
```

## Configuration

No configuration file is required. All options are passed via CLI arguments. For repeated use, you can create a shell script:

```bash
#!/bin/bash
# review.sh
python main_cli.py send ./src -p "Review for security and bugs"
```

## Error Handling

- **No new files**: Shows "No files to process"
- **Copilot CLI not installed**: Shows installation instructions
- **API errors**: Displays error message from Copilot
- **Large files**: Skips files over 500KB

## Troubleshooting

### Copilot CLI not found

```bash
gh copilot --version
```

If not installed, enable it in GitHub settings.

### Authentication errors

```bash
gh auth status
gh auth login
```

### Rate limiting

Copilot CLI may rate limit intensive usage. Wait a few minutes and try again.

## License

MIT
