"""Tests for clearcut.silence — segment merging and padding logic."""

from __future__ import annotations

import pytest

from clearcut.silence import _merge_close_segments, _pad_segments


class TestMergeCloseSegments:
    """Test _merge_close_segments with various inputs."""

    def test_empty_list(self) -> None:
        assert _merge_close_segments([], gap=0.3) == []

    def test_single_segment(self) -> None:
        result = _merge_close_segments([(1.0, 2.0)], gap=0.3)
        assert result == [(1.0, 2.0)]

    def test_merge_when_gap_within_threshold(self) -> None:
        segments = [(1.0, 2.0), (2.2, 3.0)]
        result = _merge_close_segments(segments, gap=0.3)
        assert result == [(1.0, 3.0)]

    def test_no_merge_when_gap_exceeds_threshold(self) -> None:
        segments = [(1.0, 2.0), (2.5, 3.0)]
        result = _merge_close_segments(segments, gap=0.3)
        assert result == [(1.0, 2.0), (2.5, 3.0)]

    def test_merge_exact_gap(self) -> None:
        segments = [(1.0, 2.0), (2.3, 3.0)]
        result = _merge_close_segments(segments, gap=0.3)
        assert result == [(1.0, 3.0)]

    def test_merge_chain(self) -> None:
        segments = [(1.0, 2.0), (2.1, 3.0), (3.1, 4.0)]
        result = _merge_close_segments(segments, gap=0.3)
        assert result == [(1.0, 4.0)]

    def test_partial_merge(self) -> None:
        segments = [(1.0, 2.0), (2.1, 3.0), (5.0, 6.0)]
        result = _merge_close_segments(segments, gap=0.3)
        assert result == [(1.0, 3.0), (5.0, 6.0)]


class TestPadSegments:
    """Test _pad_segments padding logic."""

    def test_default_padding(self) -> None:
        result = _pad_segments([(1.0, 2.0)])
        assert len(result) == 1
        assert result[0][0] == pytest.approx(0.95)
        assert result[0][1] == pytest.approx(2.05)

    def test_custom_padding(self) -> None:
        result = _pad_segments([(1.0, 2.0)], pad=0.1)
        assert result[0][0] == pytest.approx(0.9)
        assert result[0][1] == pytest.approx(2.1)

    def test_clamp_at_zero(self) -> None:
        result = _pad_segments([(0.01, 0.5)], pad=0.05)
        assert result[0][0] == 0.0

    def test_multiple_segments(self) -> None:
        result = _pad_segments([(1.0, 2.0), (3.0, 4.0)])
        assert len(result) == 2
        assert result[0] == (pytest.approx(0.95), pytest.approx(2.05))
        assert result[1] == (pytest.approx(2.95), pytest.approx(4.05))
