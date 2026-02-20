"""Entry point for bathymesh TUI when run as a module."""

import argparse
import logging
import sys
from pathlib import Path

from textual.logging import TextualHandler

from bathy.ui import run_tui


def main() -> None:
    """Main entry point for bathymesh TUI."""
    parser = argparse.ArgumentParser(
        description="Bathymesh TUI - 3D Mesh Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m bathy                          # Use default projects directory
  python -m bathy /path/to/projects        # Use custom projects directory
  python -m bathy --no-ansi-colors         # Use Textual's default theme
        """,
    )
    parser.add_argument(
        "projects_root",
        nargs="?",
        type=Path,
        help="Root directory for projects (default: data/projects)",
    )
    parser.add_argument(
        "--no-ansi-colors",
        action="store_true",
        help="Use Textual's default theme instead of terminal theme colors",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level="NOTSET",
        handlers=[TextualHandler()],
        force=True,
    )

    # Run TUI with appropriate color mode
    use_ansi_colors = not args.no_ansi_colors
    run_tui(args.projects_root, ansi_color=use_ansi_colors)


if __name__ == "__main__":
    main()
