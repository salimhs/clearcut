"""Tests for clearcut.crop — smart crop face tracking."""

from __future__ import annotations

from clearcut.crop import compute_tracking_positions


class TestComputeTrackingPositions:
    """Test the tracking window computation."""

    def test_no_faces_falls_back_to_center(self) -> None:
        """When no faces detected, crop should be centered."""
        face_data = [(0, []), (15, [])]
        positions = compute_tracking_positions(face_data, 1920, 1080, 1080, 1080)
        assert len(positions) == 2
        assert positions[0].x == (1920 - 1080) // 2
        assert positions[0].y == (1080 - 1080) // 2

    def test_follows_largest_face(self) -> None:
        """When a face is detected, crop centers on it."""
        face_data = [(0, [(100, 200, 300, 300)])]
        positions = compute_tracking_positions(face_data, 1920, 1080, 1080, 1080, smooth_window=1)
        assert len(positions) == 1
        # Face center at (250, 350), crop should be aligned to it
        expected_x = 250 - 1080 // 2
        expected_y = 350 - 1080 // 2
        assert positions[0].x == max(0, min(1920 - 1080, expected_x))
        assert positions[0].y == max(0, min(1080 - 1080, expected_y))

    def test_multiple_faces_picks_largest(self) -> None:
        """When multiple faces, pick the largest one (most area)."""
        face_data = [(0, [(100, 100, 50, 50), (400, 300, 200, 200)])]
        positions = compute_tracking_positions(face_data, 1920, 1080, 1080, 1080, smooth_window=1)
        assert len(positions) == 1
        # Largest face center at (500, 400)
        expected_x = 500 - 1080 // 2
        expected_y = 400 - 1080 // 2
        assert positions[0].x == max(0, min(1920 - 1080, expected_x))
        assert positions[0].y == max(0, min(1080 - 1080, expected_y))

    def test_clamps_to_valid_region(self) -> None:
        """Crop window should not extend beyond video boundaries."""
        # Face at edge: center of crop would go negative
        face_data = [(0, [(10, 10, 20, 20)])]
        positions = compute_tracking_positions(face_data, 1920, 1080, 1920, 1080, smooth_window=1)
        assert positions[0].x >= 0
        assert positions[0].y >= 0

    def test_smoothing_averages_adjacent_frames(self) -> None:
        """Moving average should smooth out position jitter."""
        face_data = [
            (0, [(100, 200, 300, 300)]),
            (15, [(900, 200, 300, 300)]),  # jump to different position
            (30, [(100, 200, 300, 300)]),
        ]
        positions = compute_tracking_positions(face_data, 1920, 1080, 1080, 1080, smooth_window=3)
        assert len(positions) == 3
        # Middle frame should be smoothed
        assert positions[1].x != positions[0].x  # not identical to first

    def test_empty_data_returns_empty(self) -> None:
        positions = compute_tracking_positions([], 1920, 1080, 1080, 1080)
        assert positions == []
