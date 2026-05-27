"""Tests for clearcut.utils — shared has_audio utility."""

from __future__ import annotations

from pathlib import Path


class TestHasAudio:
    """Test has_audio from clearcut.utils with mocked ffprobe."""

    def test_has_audio_returns_true(self, mocker) -> None:
        from clearcut.utils import has_audio

        mock_result = mocker.MagicMock()
        mock_result.stdout = "audio\n"
        mocker.patch("clearcut.utils.subprocess.run", return_value=mock_result)

        assert has_audio(Path("test.mp4")) is True

    def test_has_audio_returns_false(self, mocker) -> None:
        from clearcut.utils import has_audio

        mock_result = mocker.MagicMock()
        mock_result.stdout = ""
        mocker.patch("clearcut.utils.subprocess.run", return_value=mock_result)

        assert has_audio(Path("test.mp4")) is False
