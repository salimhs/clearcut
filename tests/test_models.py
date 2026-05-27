"""Tests for clearcut.models — PipelineConfig, AssetPosition, CaptionStyle."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from clearcut.models import AssetPosition, CaptionStyle, PipelineConfig


class TestAssetPosition:
    """Test AssetPosition parsing and validation."""

    def test_parse_valid(self, tmp_path: Path) -> None:
        img = tmp_path / "screenshot.jpg"
        img.write_bytes(b"\xff\xd8")
        asset = AssetPosition.parse(f"{img}@10")
        assert asset.path == img
        assert asset.seconds == 10.0

    def test_parse_float_seconds(self, tmp_path: Path) -> None:
        img = tmp_path / "img.png"
        img.write_bytes(b"\x89PNG")
        asset = AssetPosition.parse(f"{img}@3.5")
        assert asset.seconds == 3.5

    def test_parse_no_at_sign(self) -> None:
        with pytest.raises(ValueError, match="path@seconds"):
            AssetPosition.parse("screenshot.jpg")

    def test_path_must_exist(self) -> None:
        with pytest.raises(ValidationError, match="Asset file not found"):
            AssetPosition(path=Path("/nonexistent/file.jpg"), seconds=5.0)


class TestCaptionStyle:
    """Test CaptionStyle defaults."""

    def test_defaults(self) -> None:
        style = CaptionStyle()
        assert style.font == "Arial"
        assert style.color == "&H00FFFFFF"
        assert style.size == 48
        assert style.position == "bottom"
        assert style.bold is True
        assert style.outline == 2
        assert style.shadow == 1
        assert style.margin_v == 40
        assert style.animation == "none"

    def test_custom_values(self) -> None:
        style = CaptionStyle(font="Impact", size=64, position="center", animation="word")
        assert style.font == "Impact"
        assert style.size == 64
        assert style.position == "center"
        assert style.animation == "word"

    def test_invalid_position(self) -> None:
        with pytest.raises(ValidationError):
            CaptionStyle(position="left")  # type: ignore[arg-type]

    def test_invalid_animation(self) -> None:
        with pytest.raises(ValidationError):
            CaptionStyle(animation="slide")  # type: ignore[arg-type]


class TestPipelineConfig:
    """Test PipelineConfig validation and template application."""

    def test_valid_config(self, sample_video: Path, tmp_path: Path) -> None:
        config = PipelineConfig(main=sample_video, output=tmp_path / "out.mp4")
        assert config.remove_silence is True
        assert config.normalize_audio is True
        assert config.format == "16:9"

    def test_main_must_exist(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError, match="Main video file not found"):
            PipelineConfig(main=tmp_path / "nonexistent.mp4")

    def test_defaults(self, sample_video: Path) -> None:
        config = PipelineConfig(main=sample_video)
        assert config.style == "default"
        assert config.encoder_preset == "fast"
        assert config.audio_target_lufs == -14.0
        assert config.punch_zoom == 0.0
        assert config.hook_zoom is False
        assert config.transition == "fade"

    def test_template_override(self, sample_video: Path) -> None:
        config = PipelineConfig(main=sample_video, template="tiktok")
        assert config.format == "9:16"
        assert config.hook_zoom is True
        assert config.punch_zoom == 1.05
        assert config.transition == "wiperight"
