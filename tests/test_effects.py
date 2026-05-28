"""Tests for clearcut.effects — punch zoom dimension math."""

from __future__ import annotations


class TestPunchZoomMath:
    """Test the crop/scale dimension calculations for punch zoom.

    We replicate the math from apply_punch_zoom to verify correctness
    without needing ffmpeg.
    """

    @staticmethod
    def _compute_crop(w: int, h: int, zoom_in: float) -> dict:
        """Replicate the crop dimension math from apply_punch_zoom."""
        crop_w = int(w / zoom_in)
        crop_h = int(h / zoom_in)
        crop_x = int((w - crop_w) / 2)
        crop_y = int((h - crop_h) / 2)
        return {"crop_w": crop_w, "crop_h": crop_h, "crop_x": crop_x, "crop_y": crop_y}

    def test_1920x1080_default_zoom(self) -> None:
        result = self._compute_crop(1920, 1080, 1.05)
        assert result["crop_w"] == 1828
        assert result["crop_h"] == 1028
        assert result["crop_x"] == 46
        assert result["crop_y"] == 26

    def test_1920x1080_heavy_zoom(self) -> None:
        result = self._compute_crop(1920, 1080, 1.15)
        assert result["crop_w"] == 1669
        assert result["crop_h"] == 939
        # Crop centered
        assert result["crop_x"] == 125
        assert result["crop_y"] == 70

    def test_1080x1920_vertical(self) -> None:
        result = self._compute_crop(1080, 1920, 1.05)
        assert result["crop_w"] == 1028
        assert result["crop_h"] == 1828
        assert result["crop_x"] == 26
        assert result["crop_y"] == 46

    def test_no_zoom(self) -> None:
        result = self._compute_crop(1920, 1080, 1.0)
        assert result["crop_w"] == 1920
        assert result["crop_h"] == 1080
        assert result["crop_x"] == 0
        assert result["crop_y"] == 0
