"""Shared test fixtures for clearcut tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from clearcut.models import CaptionStyle, PipelineConfig


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test outputs."""
    return tmp_path


@pytest.fixture
def sample_video(tmp_path: Path) -> Path:
    """Create a minimal dummy video file for tests that just need a path."""
    video = tmp_path / "sample.mp4"
    video.write_bytes(b"\x00" * 1024)
    return video


@pytest.fixture
def sample_config(sample_video: Path, tmp_path: Path) -> PipelineConfig:
    """Create a minimal PipelineConfig for testing."""
    output = tmp_path / "output.mp4"
    return PipelineConfig(
        main=sample_video,
        output=output,
        remove_silence=False,
        normalize_audio=False,
        generate_captions=False,
    )


@pytest.fixture
def default_caption_style() -> CaptionStyle:
    """Return the default CaptionStyle."""
    return CaptionStyle()
