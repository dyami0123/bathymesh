#!/usr/bin/env python
"""
Launcher script for the Bathymesh TUI application.

Usage:
    python scripts/tui.py [--projects-root PATH]
"""

import argparse
import logging
from pathlib import Path

from bathy.ui.app import run_tui


def main():
    """Parse arguments and launch the TUI."""
    parser = argparse.ArgumentParser(
        description="Bathymesh TUI - 3D Mesh Generation from Heightmaps"
    )
    parser.add_argument(
        "--projects-root",
        type=Path,
        help="Root directory for projects (default: data/projects)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("bathymesh_tui.log"),
            logging.StreamHandler(),
        ],
    )

    # Run the TUI
    run_tui(projects_root=args.projects_root)


if __name__ == "__main__":
    main()
