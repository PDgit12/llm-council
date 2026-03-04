#!/usr/bin/env python3
"""
File Monitoring & GitHub Copilot Connector

This script monitors a folder for new files and automatically sends them
to GitHub Copilot (or recursive agents) for processing with customizable prompts.

Usage:
    python main.py                    # Run once and process new files
    python main.py --continuous       # Run continuously
    python main.py --watch            # Use file system watcher
    python main.py --single <file>    # Process a single file
    python main.py --reset            # Reset processed files state
    python main.py --status           # Show current status
"""

import argparse
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import CopilotConnector


def main():
    parser = argparse.ArgumentParser(
        description="File Monitoring & GitHub Copilot Connector"
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config file (default: config.yaml)",
    )

    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously, monitoring for new files",
    )

    parser.add_argument(
        "--watch",
        action="store_true",
        help="Use file system watcher for real-time monitoring",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Poll interval in seconds for continuous mode (default: 5)",
    )

    parser.add_argument("--single", type=str, help="Process a single file and exit")

    parser.add_argument(
        "--reset", action="store_true", help="Reset the processed files state"
    )

    parser.add_argument(
        "--status", action="store_true", help="Show current status and exit"
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    try:
        connector = CopilotConnector(args.config)

        if args.status:
            status = connector.get_status()
            print("\n=== Copilot Connector Status ===")
            print(f"Watching folder: {status['watching_folder']}")
            print(f"Processed files: {status['processed_files_count']}")
            print(f"Pending changes: {status['pending_changes']}")
            print(
                f"Recursive agent: {'Enabled' if status['recursive_agent_enabled'] else 'Disabled'}"
            )
            print(f"Model: {status['copilot_model']}")
            print("=" * 35)
            return

        if args.reset:
            connector.reset_state()
            print("State has been reset. All files will be processed on next run.")
            return

        if args.single:
            result = connector.process_file(args.single)
            if result.success:
                print(f"\n=== Processed: {args.single} ===")
                print(result.response)
            else:
                print(f"Error: {result.error}")
            return

        if args.continuous or args.watch:
            connector.start_monitoring(poll_interval=args.interval, continuous=True)
        else:
            result = connector.start_monitoring(
                poll_interval=args.interval, continuous=False
            )

            if result.success and result.files_processed:
                print(f"\n=== Processed {len(result.files_processed)} files ===")
                print(result.response)
            elif not result.success:
                print(f"Error: {result.error}")
                sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nMake sure config.yaml exists and the watch_folder path is valid.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
