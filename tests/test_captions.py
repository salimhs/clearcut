"""Tests for clearcut.captions — ASS time formatting."""

from __future__ import annotations

import pytest

from clearcut.captions import _seconds_to_ass_time


class TestSecondsToAssTime:
    """Test _seconds_to_ass_time conversion."""

    @pytest.mark.parametrize(
        "seconds,expected",
        [
            (0, "0:00:00.00"),
            (1.0, "0:00:01.00"),
            (59.99, "0:00:59.99"),
            (60.0, "0:01:00.00"),
            (3661.5, "1:01:01.50"),
            (3723.25, "1:02:03.25"),
            (0.01, "0:00:00.01"),
            (7200.0, "2:00:00.00"),
        ],
    )
    def test_conversion(self, seconds: float, expected: str) -> None:
        assert _seconds_to_ass_time(seconds) == expected
