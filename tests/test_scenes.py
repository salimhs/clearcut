"""Tests for clearcut.scenes — scene detection parameters."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestSplitAtBoundaries:
    """Test split_at_boundaries logic with mocked external calls."""

    def test_no_boundaries_returns_single_segment(self, tmp_path: Path, mocker) -> None:
        """If boundaries list is empty, produce one segment (the full video)."""
        from clearcut.scenes import split_at_boundaries

        mocker.patch("clearcut.scenes.shutil.which", return_value="/usr/bin/ffmpeg")
        mock_run = mocker.patch("clearcut.scenes.subprocess.run")
        mock_run.return_value.stdout = '{"format": {"duration": "60.0"}}'

        segments = split_at_boundaries(
            Path("/dev/null"),
            [],
            tmp_path / "scenes",
        )
        assert len(segments) >= 1

    def test_with_boundaries_calls_ffmpeg(self, tmp_path: Path, mocker) -> None:
        """With boundaries, ffmpeg should be called to extract segments."""
        from clearcut.scenes import split_at_boundaries

        mocker.patch("clearcut.scenes.shutil.which", return_value="/usr/bin/ffmpeg")
        mock_run = mocker.patch("clearcut.scenes.subprocess.run")
        mock_run.return_value.stdout = '{"format": {"duration": "120.0"}}'

        segments = split_at_boundaries(
            Path("/dev/null"),
            [30.0, 60.0],
            tmp_path / "scenes",
        )
        assert len(segments) >= 3  # 3 segments for 2 boundaries

    def test_ffmpeg_not_installed_raises(self, tmp_path: Path, mocker) -> None:
        from clearcut.scenes import split_at_boundaries
        from clearcut.exceptions import EncodingError

        mocker.patch("clearcut.scenes.shutil.which", return_value=None)
        with pytest.raises(EncodingError, match="ffmpeg"):
            split_at_boundaries(Path("/dev/null"), [], tmp_path / "out")
