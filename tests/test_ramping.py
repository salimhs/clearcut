"""Tests for clearcut.effects — speed ramping parsing and validation."""

from __future__ import annotations

import pytest

from clearcut.effects import parse_speed_segment, validate_speed_segments, SpeedSegment
from clearcut.exceptions import ConfigError


class TestParseSpeedSegment:
    """Test speed segment string parsing."""

    def test_valid_segment(self) -> None:
        seg = parse_speed_segment("0-5:0.5")
        assert seg.start == 0.0
        assert seg.end == 5.0
        assert seg.speed == 0.5

    def test_valid_decimal_times(self) -> None:
        seg = parse_speed_segment("1.5-10.8:2.0")
        assert seg.start == 1.5
        assert seg.end == 10.8
        assert seg.speed == 2.0

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(ConfigError, match="Expected format"):
            parse_speed_segment("abc-def:xyz")

    def test_missing_speed_raises(self) -> None:
        with pytest.raises(ConfigError, match="Expected format"):
            parse_speed_segment("0-5")

    def test_start_gte_end_raises(self) -> None:
        with pytest.raises(ConfigError, match="must be < end"):
            parse_speed_segment("10-5:0.5")

    def test_speed_too_low_raises(self) -> None:
        with pytest.raises(ConfigError, match="0.1"):
            parse_speed_segment("0-5:0.01")

    def test_speed_too_high_raises(self) -> None:
        with pytest.raises(ConfigError, match="10.0"):
            parse_speed_segment("0-5:20.0")

    def test_edge_speed_low(self) -> None:
        seg = parse_speed_segment("0-5:0.1")
        assert seg.speed == 0.1

    def test_edge_speed_high(self) -> None:
        seg = parse_speed_segment("0-5:10.0")
        assert seg.speed == 10.0


class TestValidateSpeedSegments:
    """Test overlap detection."""

    def test_no_overlap_passes(self) -> None:
        segments = [
            SpeedSegment(start=0.0, end=5.0, speed=0.5),
            SpeedSegment(start=5.0, end=10.0, speed=2.0),
        ]
        validate_speed_segments(segments)  # should not raise

    def test_overlap_raises(self) -> None:
        segments = [
            SpeedSegment(start=0.0, end=5.0, speed=0.5),
            SpeedSegment(start=4.0, end=8.0, speed=2.0),
        ]
        with pytest.raises(ConfigError, match="overlap"):
            validate_speed_segments(segments)

    def test_empty_list_passes(self) -> None:
        validate_speed_segments([])  # should not raise

    def test_single_segment_passes(self) -> None:
        validate_speed_segments([SpeedSegment(start=0.0, end=10.0, speed=1.0)])
