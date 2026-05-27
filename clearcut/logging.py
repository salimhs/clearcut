"""Logging configuration for clearcut."""

from __future__ import annotations

import logging
from pathlib import Path

from rich.logging import RichHandler


def setup_logging(*, verbose: bool = False, log_file: Path | None = None) -> None:
    """Configure logging with rich console handler and optional file handler.

    Args:
        verbose: If True, set level to DEBUG; otherwise INFO.
        log_file: Optional path to a log file.
    """
    level = logging.DEBUG if verbose else logging.INFO

    handlers: list[logging.Handler] = [
        RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=verbose,
        ),
    ]

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,
    )
