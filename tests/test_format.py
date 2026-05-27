"""Tests for clearcut.format — aspect ratio conversion math."""

from __future__ import annotations

class TestFormatMath:
    """Test the crop dimension math for format conversions.

    Replicates the logic from _reformat to verify without ffmpeg.
    """

    @staticmethod
    def _compute_crop(src_w: int, src_h: int, target_w: int, target_h: int) -> dict:
        """Replicate the crop math from _reformat."""
        target_ratio = target_w / target_h
        src_ratio = src_w / src_h

        if src_ratio > target_ratio:
            crop_h = src_h
            crop_w = int(src_h * target_ratio)
        else:
            crop_w = src_w
            crop_h = int(src_w / target_ratio)

        crop_x = (src_w - crop_w) // 2
        crop_y = (src_h - crop_h) // 2

        return {
            "crop_w": crop_w,
            "crop_h": crop_h,
            "crop_x": crop_x,
            "crop_y": crop_y,
        }

    def test_16_9_to_vertical(self) -> None:
        """1920x1080 → 9:16 (1080x1920) — should crop horizontally."""
        result = self._compute_crop(1920, 1080, 1080, 1920)
        assert result["crop_w"] == 607
        assert result["crop_h"] == 1080
        assert result["crop_x"] == 656
        assert result["crop_y"] == 0

    def test_16_9_to_square(self) -> None:
        """1920x1080 → 1:1 (1080x1080) — should crop horizontally."""
        result = self._compute_crop(1920, 1080, 1080, 1080)
        assert result["crop_w"] == 1080
        assert result["crop_h"] == 1080
        assert result["crop_x"] == 420
        assert result["crop_y"] == 0

    def test_square_to_vertical(self) -> None:
        """1080x1080 → 9:16 — should crop horizontally."""
        result = self._compute_crop(1080, 1080, 1080, 1920)
        assert result["crop_w"] == 607
        assert result["crop_h"] == 1080
        assert result["crop_x"] == 236
        assert result["crop_y"] == 0

    def test_already_correct_ratio(self) -> None:
        """16:9 to 16:9 — crop should be full frame."""
        result = self._compute_crop(1920, 1080, 1920, 1080)
        assert result["crop_w"] == 1920
        assert result["crop_h"] == 1080
        assert result["crop_x"] == 0
        assert result["crop_y"] == 0
