# File Monitoring & GitHub Copilot Integration

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure settings in `config.yaml`:
   - Set `watch_folder` to the folder path you want to monitor
   - Set your GitHub token
   - Configure AI model settings
   - Set your task prompt

3. Run the watcher:
```bash
python main.py
```

## Project Structure

- `config.yaml` - Configuration file
- `file_watcher.py` - Folder monitoring with file tracking
- `copilot_client.py` - GitHub Copilot API integration
- `recursive_agent.py` - Recursive agents framework integration
- `context_prompts.py` - Context engineering prompts
- `orchestrator.py` - Main orchestrator
- `main.py` - Entry point

## Features

- Monitors folder for new files in real-time
- Tracks processed files to only send new additions
- Uses recursive-agents framework for self-improving responses
- Context engineering for optimal AI performance
- Configurable task prompts
