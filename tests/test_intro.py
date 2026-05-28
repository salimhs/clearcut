"""Tests for clearcut.intro — intro/outro segment assembly."""

from __future__ import annotations

from pathlib import Path




class TestIntroOutroValidation:
    """Test intro/outro path validation."""

    def test_intro_path_accepts_valid(self) -> None:
        from clearcut.models import PipelineConfig

        config = PipelineConfig(
            main=Path("/dev/null"),
            output=Path("out.mp4"),
            intro_path=Path("/dev/null"),
        )
        assert config.intro_path == Path("/dev/null")

    def test_outro_path_accepts_valid(self) -> None:
        from clearcut.models import PipelineConfig

        config = PipelineConfig(
            main=Path("/dev/null"),
            output=Path("out.mp4"),
            outro_path=Path("/dev/null"),
        )
        assert config.outro_path == Path("/dev/null")

    def test_intro_only_triggers_stage(self) -> None:
        from clearcut.models import PipelineConfig

        config = PipelineConfig(
            main=Path("/dev/null"),
            output=Path("out.mp4"),
            intro_path=Path("/tmp"),
        )
        assert config.intro_path is not None

    def test_outro_only_triggers_stage(self) -> None:
        from clearcut.models import PipelineConfig
        config = PipelineConfig(
            main=Path("/dev/null"),
            output=Path("out.mp4"),
            outro_path=Path("/tmp"),
        )
        assert config.outro_path is not None

    def test_intro_outro_default_none(self) -> None:
        from clearcut.models import PipelineConfig
        config = PipelineConfig(main=Path("/dev/null"), output=Path("out.mp4"))
        assert config.intro_path is None
        assert config.outro_path is None
