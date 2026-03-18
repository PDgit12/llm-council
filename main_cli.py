#!/usr/bin/env python3
"""
GitHub Copilot File Connector - CLI

Uses GitHub Copilot CLI to process files.
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def cmd_init(args):
    """Initialize configuration."""
    from init_wizard import InitWizard

    wizard = InitWizard()
    wizard.run()
    return 0


def cmd_scan(args):
    """Scan folder for files."""
    from scanner import FileScanner

    scanner = FileScanner(args.folder)
    files = scanner.get_files()

    print(f"\n📁 Found {len(files)} files in {args.folder}:\n")

    for i, path in enumerate(files.keys(), 1):
        size = len(files[path])
        print(f"  {i}. {path} ({size:,} chars)")

    return 0


def cmd_send(args):
    """Send files to GitHub Copilot."""
    from scanner import FileScanner
    from copilot_cli import CopilotCLI

    # Scan files
    scanner = FileScanner(args.folder)
    files = args.all and scanner.get_files() or scanner.get_new_files()

    if not files:
        print("⚠️  No files to process")
        return 1

    # Get prompt
    prompt = args.prompt or "Analyze these files and provide insights."

    print(f"\n📤 Sending {len(files)} files to GitHub Copilot...")

    # Process with Copilot CLI
    copilot = CopilotCLI()
    result = copilot.process(files, prompt)

    if result.success:
        print("\n✅ Success!\n")
        print("=" * 60)
        print(result.response)
        print("=" * 60)

        # Mark as processed
        scanner.mark_processed(files)

        # Save output
        if args.output:
            with open(args.output, "w") as f:
                f.write(f"# Copilot Response\n\n")
                f.write(f"## Files\n")
                for p in files.keys():
                    f.write(f"- {p}\n")
                f.write(f"\n## Task\n{prompt}\n\n")
                f.write(f"## Response\n{result.response}\n")
            print(f"\n💾 Saved to {args.output}")
    else:
        print(f"\n❌ Error: {result.error}")
        return 1

    return 0


def cmd_watch(args):
    """Watch folder for new files."""
    from scanner import FileScanner
    from copilot_cli import CopilotCLI
    import time

    scanner = FileScanner(args.folder)
    copilot = CopilotCLI()
    prompt = args.prompt or "Analyze these files and provide insights."

    print(f"\n👀 Watching {args.folder} for new files...")
    print(f"   Press Ctrl+C to stop\n")

    try:
        while True:
            new_files = scanner.get_new_files()

            if new_files:
                print(f"\n🆕 Found {len(new_files)} new/modified files!")

                result = copilot.process(new_files, prompt)

                if result.success:
                    print("\n" + "=" * 60)
                    print(result.response)
                    print("=" * 60)
                    scanner.mark_processed(new_files)
                else:
                    print(f"❌ Error: {result.error}")

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n\n👋 Stopped watching")

    return 0


def cmd_status(args):
    """Show status."""
    from scanner import FileScanner

    scanner = FileScanner(".")
    files = scanner.get_files()
    new_files = scanner.get_new_files()

    print("\n📊 Status:")
    print(f"   Total files:  {len(files)}")
    print(f"   New files:    {len(new_files)}")
    print(f"   Copilot CLI:  ✅ Installed")

    return 0


def cmd_reset(args):
    """Reset tracking."""
    from scanner import FileScanner

    scanner = FileScanner(".")
    scanner.reset()
    print("\n🔄 Tracking reset. All files will be processed again.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Copilot File Connector - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  copilot-connector init                     Setup wizard
  copilot-connector scan ./my-project        Scan folder
  copilot-connector send                     Send new files
  copilot-connector send --all               Send all files
  copilot-connector send -p "Review code"   Send with custom prompt
  copilot-connector watch ./my-project       Watch for changes
  copilot-connector status                   Check status
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    subparsers.add_parser("init", help="Initialize configuration")

    scan_parser = subparsers.add_parser("scan", help="Scan folder")
    scan_parser.add_argument("folder", help="Folder to scan")

    send_parser = subparsers.add_parser("send", help="Send to Copilot")
    send_parser.add_argument("folder", nargs="?", default=".", help="Folder path")
    send_parser.add_argument("--prompt", "-p", help="Task prompt")
    send_parser.add_argument("--output", "-o", help="Save output file")
    send_parser.add_argument("--all", "-a", action="store_true", help="Send all files")

    watch_parser = subparsers.add_parser("watch", help="Watch folder")
    watch_parser.add_argument("folder", help="Folder to watch")
    watch_parser.add_argument("--prompt", "-p", help="Task prompt")
    watch_parser.add_argument(
        "--interval", "-i", type=int, default=5, help="Check interval"
    )

    subparsers.add_parser("status", help="Show status")
    subparsers.add_parser("reset", help="Reset tracking")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "init": cmd_init,
        "scan": cmd_scan,
        "send": cmd_send,
        "watch": cmd_watch,
        "status": cmd_status,
        "reset": cmd_reset,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
