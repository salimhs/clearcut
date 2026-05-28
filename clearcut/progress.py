"""Shared Rich Progress context manager for pipeline stages."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)


def _make_progress() -> Progress:
    """Create a configured Rich Progress instance."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        transient=True,
    )


@contextmanager
def stage_progress(description: str) -> Generator[Progress, None, None]:
    """Context manager that shows a spinner + elapsed time for a pipeline stage.

    Usage::

        with stage_progress("Removing silence") as progress:
            task = progress.add_task("Removing silence", total=None)
            # ... do work ...
            progress.update(task, description="Found 12 segments")
    """
    progress = _make_progress()
    with progress:
        yield progress
