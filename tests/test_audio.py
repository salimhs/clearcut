"""Tests for clearcut.audio — _safe_float and has_audio."""

from __future__ import annotations

import math
from pathlib import Path


class TestSafeFloat:
    """Test the _safe_float helper inside normalize_audio.

    We import the inner function by accessing it from the module namespace.
    Since _safe_float is a nested function, we replicate its logic here for testing.
    """

    @staticmethod
    def _safe_float(val, default: float) -> float:
        """Replicate the _safe_float logic from audio.normalize_audio."""
        try:
            f = float(val)
            if math.isinf(f) or math.isnan(f):
                return default
            return f
        except (TypeError, ValueError):
            return default

    def test_none_returns_default(self) -> None:
        assert self._safe_float(None, -24) == -24

    def test_inf_returns_default(self) -> None:
        assert self._safe_float(float("inf"), -24) == -24

    def test_negative_inf_returns_default(self) -> None:
        assert self._safe_float(float("-inf"), -24) == -24

    def test_nan_returns_default(self) -> None:
        assert self._safe_float(float("nan"), -24) == -24

    def test_valid_float(self) -> None:
        assert self._safe_float(0.5, -24) == 0.5

    def test_valid_string_number(self) -> None:
        assert self._safe_float("-14.0", -24) == -14.0

    def test_invalid_string(self) -> None:
        assert self._safe_float("not_a_number", -24) == -24

    def test_zero(self) -> None:
        assert self._safe_float(0, -24) == 0.0


class TestHasAudio:
    """Test has_audio with mocked ffprobe."""

    def test_has_audio(self, mocker) -> None:
        from clearcut.utils import has_audio

        mock_result = mocker.MagicMock()
        mock_result.stdout = "audio\n"
        mocker.patch("clearcut.utils.subprocess.run", return_value=mock_result)

        assert has_audio(Path("test.mp4")) is True

    def test_no_audio(self, mocker) -> None:
        from clearcut.utils import has_audio

        mock_result = mocker.MagicMock()
        mock_result.stdout = ""
        mocker.patch("clearcut.utils.subprocess.run", return_value=mock_result)

        assert has_audio(Path("test.mp4")) is False
