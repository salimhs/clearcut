"""Tests for clearcut.transitions — offset calculation and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from clearcut.transitions import SUPPORTED_TRANSITIONS, apply_transitions


class TestOffsetCalculation:
    """Test the xfade offset calculation logic."""

    @staticmethod
    def _compute_offsets(durations: list[float], transition_duration: float) -> list[float]:
        """Replicate the offset calculation from apply_transitions."""
        offsets: list[float] = []
        cumulative = durations[0]
        for i in range(1, len(durations)):
            offset = cumulative - transition_duration
            offsets.append(offset)
            cumulative += durations[i] - transition_duration
        return offsets

    def test_three_segments(self) -> None:
        """Three 10-second segments with 0.5s transitions."""
        offsets = self._compute_offsets([10.0, 10.0, 10.0], 0.5)
        assert len(offsets) == 2
        assert offsets[0] == pytest.approx(9.5)
        assert offsets[1] == pytest.approx(19.0)

    def test_two_segments(self) -> None:
        offsets = self._compute_offsets([5.0, 8.0], 0.3)
        assert len(offsets) == 1
        assert offsets[0] == pytest.approx(4.7)

    def test_varying_durations(self) -> None:
        offsets = self._compute_offsets([3.0, 5.0, 2.0], 0.5)
        assert len(offsets) == 2
        assert offsets[0] == pytest.approx(2.5)
        assert offsets[1] == pytest.approx(7.0)


class TestSingleSegmentCopy:
    """Test that a single segment is simply copied."""

    def test_single_segment_copies(self, tmp_path: Path) -> None:
        seg = tmp_path / "seg.mp4"
        seg.write_bytes(b"\x00" * 100)
        output = tmp_path / "out.mp4"

        result = apply_transitions([seg], output)
        assert result == output
        assert output.exists()


class TestDurationValidation:
    """Test transition validation logic."""

    def test_supported_transitions_list(self) -> None:
        assert "fade" in SUPPORTED_TRANSITIONS
        assert "wipeleft" in SUPPORTED_TRANSITIONS
        assert "dissolve" in SUPPORTED_TRANSITIONS
        assert "radial" in SUPPORTED_TRANSITIONS

    def test_empty_segments_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one segment"):
            apply_transitions([], Path("out.mp4"))

    def test_unsupported_transition_raises(self, tmp_path: Path) -> None:
        seg1 = tmp_path / "a.mp4"
        seg2 = tmp_path / "b.mp4"
        seg1.write_bytes(b"\x00")
        seg2.write_bytes(b"\x00")
        with pytest.raises(ValueError, match="Unsupported transition"):
            apply_transitions([seg1, seg2], tmp_path / "out.mp4", transition="spin")
