"""Tests for Phase 2 reliability features — signal handling and config loading."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestPipelineSignalHandling:
    """Test the Pipeline interrupt detection logic."""

    def test_pipeline_init_has_interrupt_flag(self) -> None:
        """Pipeline should initialize with interrupted=False."""
        from clearcut.pipeline import Pipeline
        from clearcut.models import PipelineConfig

        config = PipelineConfig(main=Path("/dev/null"), output=Path("out.mp4"))
        pipeline = Pipeline(config)
        assert pipeline._interrupted is False

    def test_handle_signal_sets_flag(self) -> None:
        """Calling _handle_signal should set _interrupted=True."""
        from clearcut.pipeline import Pipeline
        from clearcut.models import PipelineConfig

        config = PipelineConfig(main=Path("/dev/null"), output=Path("out.mp4"))
        pipeline = Pipeline(config)
        assert pipeline._interrupted is False
        pipeline._handle_signal(2, None)
        assert pipeline._interrupted is True

    def test_check_interrupted_returns_false_when_not_interrupted(self) -> None:
        from clearcut.pipeline import Pipeline
        from clearcut.models import PipelineConfig

        config = PipelineConfig(main=Path("/dev/null"), output=Path("out.mp4"))
        pipeline = Pipeline(config)
        assert pipeline._check_interrupted() is False

    def test_check_interrupted_returns_true_when_interrupted(self) -> None:
        from clearcut.pipeline import Pipeline
        from clearcut.models import PipelineConfig

        config = PipelineConfig(main=Path("/dev/null"), output=Path("out.mp4"))
        pipeline = Pipeline(config)
        pipeline._interrupted = True
        assert pipeline._check_interrupted() is True


class TestCliVerboseFlag:
    """Test that --verbose is wired up in the CLI."""

    def test_callback_has_verbose(self) -> None:
        """The CLI callback should accept a verbose parameter."""
        import inspect

        from clearcut.cli import main

        sig = inspect.signature(main)
        assert "verbose" in sig.parameters

    def test_callback_verbose_default_false(self) -> None:
        """The verbose parameter should default to False."""
        import inspect

        from clearcut.cli import main

        sig = inspect.signature(main)
        param = sig.parameters["verbose"]
        assert param.default is False


class TestCliConfigFlag:
    """Test that --config is wired up in the process command."""

    def test_process_has_config_param(self) -> None:
        """The process command should accept a --config parameter."""
        import inspect

        from clearcut.cli import process

        sig = inspect.signature(process)
        assert "config" in sig.parameters

    def test_process_config_default_none(self) -> None:
        """The config parameter should default to None."""
        import inspect

        from clearcut.cli import process

        sig = inspect.signature(process)
        param = sig.parameters["config"]
        assert param.default is None


class TestLoggingSetup:
    """Test the logging configuration module."""

    def test_setup_logging_exists(self) -> None:
        """The logging module should export setup_logging."""
        from clearcut.logging import setup_logging

        assert callable(setup_logging)

    def test_setup_logging_with_verbose(self) -> None:
        """Calling setup_logging with verbose=True should not raise."""
        import logging

        from clearcut.logging import setup_logging

        setup_logging(verbose=True)
        assert logging.getLogger("clearcut").isEnabledFor(logging.DEBUG)
