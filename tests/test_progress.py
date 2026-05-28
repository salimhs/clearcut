"""Tests for clearcut.progress — Rich progress context manager."""

from __future__ import annotations

from clearcut.progress import stage_progress, _make_progress


def test_make_progress_returns_progress_instance():
    """_make_progress returns a configured Rich Progress."""
    progress = _make_progress()
    assert progress is not None
    assert len(progress.columns) == 3  # Spinner + Text + TimeElapsed


def test_stage_progress_context_manager():
    """stage_progress yields a usable Progress object."""
    with stage_progress("Testing stage") as progress:
        task = progress.add_task("Testing stage", total=None)
        progress.update(task, description="Done")
        assert progress.tasks[0].description == "Done"


def test_stage_progress_multiple_tasks():
    """Multiple tasks can be tracked in a single progress context."""
    with stage_progress("Multi-task") as progress:
        t1 = progress.add_task("Task 1", total=10)
        t2 = progress.add_task("Task 2", total=None)
        progress.update(t1, completed=5)
        progress.update(t2, description="Task 2 updated")
        assert progress.tasks[0].completed == 5
        assert progress.tasks[1].description == "Task 2 updated"


def test_stage_progress_indeterminate():
    """Indeterminate (total=None) tasks work without error."""
    with stage_progress("Spinner only") as progress:
        task = progress.add_task("Spinner only", total=None)
        # Just verifying no exception is raised
        progress.update(task, description="Still going...")
        assert progress.tasks[0].total is None
