"""Tests for clearcut.repurpose — time formatting and dataclass."""

from __future__ import annotations

import pytest

from clearcut.repurpose import HighlightClip, HighlightResult, _fmt_time


class TestFmtTime:
    """Test _fmt_time formatting."""

    @pytest.mark.parametrize(
        "seconds,expected",
        [
            (0, "00:00"),
            (65, "01:05"),
            (3661, "61:01"),
            (30, "00:30"),
            (120, "02:00"),
            (59, "00:59"),
        ],
    )
    def test_formatting(self, seconds: float, expected: str) -> None:
        assert _fmt_time(seconds) == expected


class TestHighlightClip:
    """Test HighlightClip dataclass."""

    def test_creation(self) -> None:
        clip = HighlightClip(
            start=10.0,
            end=30.0,
            title="Test Clip",
            reason="Engaging content",
            virality_score=0.85,
        )
        assert clip.start == 10.0
        assert clip.end == 30.0
        assert clip.title == "Test Clip"
        assert clip.virality_score == 0.85

    def test_duration(self) -> None:
        clip = HighlightClip(start=5.0, end=25.0, title="", reason="", virality_score=0.5)
        assert clip.end - clip.start == 20.0


class TestHighlightResult:
    """Test HighlightResult dataclass."""

    def test_empty_result(self) -> None:
        result = HighlightResult(clips=[])
        assert len(result.clips) == 0
        assert result.total_duration == 0.0

    def test_with_clips(self) -> None:
        clips = [
            HighlightClip(start=0, end=10, title="A", reason="", virality_score=0.9),
            HighlightClip(start=20, end=40, title="B", reason="", virality_score=0.7),
        ]
        result = HighlightResult(clips=clips, total_duration=60.0)
        assert len(result.clips) == 2
        assert result.total_duration == 60.0
