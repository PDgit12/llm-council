# GitHub Copilot File Connector

A powerful CLI tool that monitors folders for new files and sends them to GitHub Copilot with customizable prompts. Built with the **recursive-agents** framework for self-improving AI responses.

## Features

- 📁 **Smart File Monitoring** - Only sends NEW files, not the whole folder
- 🔄 **Incremental Processing** - Tracks processed files, detects changes
- 🧠 **Recursive Agents** - Draft → Critique → Revision for better responses
- ⚡ **Real-time Watching** - Monitors folder for changes automatically
- 🎯 **Custom Prompts** - Configure what GitHub Copilot should do with your files

## Installation

```bash
# Clone or download the project
cd copilot-connector

# Install dependencies
pip install PyYAML requests

# Make executable (optional)
chmod +x run.sh
```

## Quick Start

```bash
# Step 1: Initialize configuration (interactive wizard)
python main_cli.py init

# Step 2: Scan a folder to see files
python main_cli.py scan ./my-project

# Step 3: Send files to GitHub Copilot
python main_cli.py send

# Step 4: Watch folder for new files (auto-send)
python main_cli.py watch ./my-project
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `init` | Interactive setup wizard |
| `scan <folder>` | Scan folder and show files |
| `send` | Send new files to Copilot |
| `send --all` | Send ALL files (not just new) |
| `send -p "..."` | Custom prompt |
| `watch <folder>` | Watch for changes |
| `status` | Check current status |
| `reset` | Reset file tracking |

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    Your Project                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ file.py │  │ util.js │  │ app.ts │  │ data.json│   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘   │
│       │            │            │            │         │
│       └────────────┴─────┬──────┴────────────┘         │
│                          │                              │
│                    File Scanner                         │
│            (tracks processed files)                    │
│                          │                              │
│              ┌───────────┴───────────┐                  │
│              │   NEW FILE DETECTED  │                  │
│              └───────────┬───────────┘                  │
│                          │                              │
│              ┌───────────▼───────────┐                   │
│              │   GitHub Copilot API │                   │
│              └───────────┬───────────┘                   │
│                          │                              │
│              ┌───────────▼───────────┐                   │
│              │  Recursive Refinement │                  │
│              │  (Draft→Critique→Rev) │                  │
│              └───────────┬───────────┘                   │
│                          │                              │
│                   📋 Response                           │
└─────────────────────────────────────────────────────────┘
```

### Recursive Agent Process

1. **Draft** - Initial analysis from Copilot
2. **Critique** - Identify gaps and improvements
3. **Revision** - Enhanced response addressing critique
4. **Convergence** - Repeat until stable

## Configuration

Configuration is saved to `copilot_connector.yaml`:

```yaml
watch_folder: ./my-project

github:
  token: ghp_xxxxx  # Your GitHub token
  model: gpt-4o
  temperature: 0.7

recursive_agent:
  enabled: true
  max_loops: 2

task_prompt: |
  Review these files for bugs and improvements.
```

## Usage Examples

### Code Review
```bash
python main_cli.py send -p "Review code for bugs, security issues, and improvements."
```

### Generate Documentation
```bash
python main_cli.py send -p "Generate documentation for these files."
```

### Watch Mode
```bash
# Watch folder, auto-send new files
python main_cli.py watch ./my-project

# Custom interval (10 seconds)
python main_cli.py watch ./my-project --interval 10
```

## Requirements

- Python 3.8+
- GitHub account with Copilot access
- GitHub Personal Access Token with `copilot` scope

## Getting a GitHub Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `copilot` and `repo`
4. Generate and copy the token

## License

MIT
