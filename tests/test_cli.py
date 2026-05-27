"""Tests for clearcut.cli — version, help, basic command tests."""

from __future__ import annotations

from typer.testing import CliRunner

from clearcut import __version__
from clearcut.cli import app

runner = CliRunner()


class TestCLI:
    """Test CLI entry points."""

    def test_version_flag(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_help_works(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "clearcut" in result.stdout.lower()

    def test_process_help(self) -> None:
        result = runner.invoke(app, ["process", "--help"])
        assert result.exit_code == 0
        assert "--main" in result.stdout

    def test_trim_help(self) -> None:
        result = runner.invoke(app, ["trim", "--help"])
        assert result.exit_code == 0
        assert "--input" in result.stdout

    def test_transcribe_help(self) -> None:
        result = runner.invoke(app, ["transcribe", "--help"])
        assert result.exit_code == 0
        assert "--input" in result.stdout

    def test_templates_command(self) -> None:
        result = runner.invoke(app, ["templates"])
        assert result.exit_code == 0
        assert "clean" in result.stdout
        assert "tiktok" in result.stdout

    def test_repurpose_help(self) -> None:
        result = runner.invoke(app, ["repurpose", "--help"])
        assert result.exit_code == 0
        assert "--input" in result.stdout

    def test_no_args_shows_help(self) -> None:
        result = runner.invoke(app, [])
        # Typer exits with code 0 or 2 for no_args_is_help depending on version
        assert result.exit_code in (0, 2)
        assert "Usage" in result.stdout or "clearcut" in result.stdout.lower()
