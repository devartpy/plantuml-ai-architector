"""Command-line entry point for AI Architect."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from colorama import Fore, Style, just_fix_windows_console

from ai_architect.core import InitError, InitEvent, initialize_project


class CliParser(argparse.ArgumentParser):
    """Use the same exit status and error presentation for argument failures."""

    def error(self, message: str) -> None:
        _print_status(f"ERROR {message}", color=Fore.RED, error=True)
        raise SystemExit(1)


def _configure_logging() -> None:
    """Enable diagnostic core logging only when LOG_LEVEL is supplied."""
    name = os.environ.get("LOG_LEVEL", "CRITICAL").upper()
    level = logging.getLevelName(name)
    if not isinstance(level, int):
        level = logging.CRITICAL
    logger = logging.getLogger("ai_architect")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
        logger.addHandler(handler)


def _print_status(message: str, *, color: str, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    prefix = color if stream.isatty() else ""
    suffix = Style.RESET_ALL if prefix else ""
    print(f"{prefix}{message}{suffix}", file=stream)


def _show_event(event: InitEvent) -> None:
    if event.action == "reused":
        label, color = "SKIP", Fore.CYAN
    else:
        label, color = ("UPDATED" if event.action == "updated" else "CREATED"), Fore.GREEN
    detail = f" ({event.detail})" if event.detail else ""
    _print_status(f"{label} {event.path}{detail}", color=color)


def _build_parser() -> argparse.ArgumentParser:
    parser = CliParser(prog="ai-architect", description="AI-assisted PlantUML architecture tools.")
    commands = parser.add_subparsers(dest="command")
    init = commands.add_parser("init", help="Initialize this project with specifications and agent workflows")
    init.add_argument(
        "--diagrams-dir",
        metavar="PATH",
        help="Project-relative diagram directory (default: docs/architecture/diagrams)",
    )
    init.add_argument(
        "--plantuml-server-url",
        metavar="URL",
        help="PlantUML renderer base URL (default: https://www.plantuml.com/plantuml)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the selected command and return a process exit status."""
    just_fix_windows_console()
    _configure_logging()
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    try:
        result = initialize_project(Path.cwd(), args.diagrams_dir, args.plantuml_server_url)
    except (InitError, OSError) as error:
        _print_status(f"ERROR {error}", color=Fore.RED, error=True)
        return 1

    for event in result.events:
        _show_event(event)
    _print_status(
        "NEXT Add .ai-architect/mcp-config-example.json to your agent's MCP configuration; "
        "see README.md for client-specific steps.",
        color=Fore.CYAN,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
