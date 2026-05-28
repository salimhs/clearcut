"""Pydantic models for pipeline configuration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal


from pydantic import BaseModel, field_validator, model_validator

log = logging.getLogger(__name__)


class AssetPosition(BaseModel):
    """An image/screenshot to insert at a specific timestamp."""

    path: Path
    seconds: float

    @classmethod
    def parse(cls, raw: str) -> AssetPosition:
        """Parse 'path@seconds' format, e.g. 'screenshot.jpg@10'."""
        if "@" not in raw:
            raise ValueError(f"Asset must be in 'path@seconds' format, got: {raw}")
        path_str, seconds_str = raw.rsplit("@", 1)
        return cls(path=Path(path_str), seconds=float(seconds_str))

    @field_validator("path")
    @classmethod
    def path_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"Asset file not found: {v}")
        return v


class CaptionStyle(BaseModel):
    """ASS subtitle styling parameters."""

    font: str = "Arial"
    color: str = "&H00FFFFFF"  # ASS BGR format, white
    outline_color: str = "&H00000000"  # black
    size: int = 48
    position: Literal["bottom", "center", "top"] = "bottom"
    bold: bool = True
    outline: int = 2
    shadow: int = 1
    margin_v: int = 40
    animation: Literal["none", "word", "fade"] = "none"


class PipelineConfig(BaseModel):
    """Top-level configuration for a clearcut pipeline run."""

    main: Path
    intro_path: Path | None = None
    outro_path: Path | None = None
    intro_only: bool = False
    outro_only: bool = False
    context: list[Path] = []
    images: list[Path] = []
    assets: list[AssetPosition] = []
    style: Literal["default", "modern", "minimal", "bold"] = "default"
    output: Path = Path("output.mp4")
    remove_silence: bool = True
    silence_method: Literal["vad", "auto-editor"] = "vad"
    generate_captions: bool = False
    burn_captions: bool = False
    encoder_preset: str = "fast"
    hardware: str = "auto"

    # Audio processing
    normalize_audio: bool = True
    audio_target_lufs: float = -14.0
    duck_music: Path | None = None  # path to background music for ducking

    # Colour grading
    lut: Path | None = None  # path to .cube LUT file
    brightness: float = 0.0
    contrast: float = 1.0
    saturation: float = 1.0

    # Format / aspect ratio
    format: str = "16:9"  # "16:9", "9:16", "1:1"
    smart_crop: str = "center"  # "center" or "face"
    smart_crop_smooth: int = 5  # smoothing window for face tracking

    # Scene detection
    detect_scenes: bool = False
    max_clip_duration: float = 0.0  # 0 = no forced splits

    # Transitions
    transition: str = "fade"  # transition between segments
    transition_duration: float = 0.3

    # Effects
    punch_zoom: float = 0.0  # 0 = off, 1.05 = 5% zoom, 1.15 = 15% zoom
    hook_zoom: bool = False  # quick zoom-in on first 2 seconds

    # Speed ramping
    speed_segments: list[str] = []

    # Watermark
    watermark_path: Path | None = None
    watermark_position: str = "bottom-right"
    watermark_scale: float = 0.15
    watermark_opacity: float = 0.7

    # Background music
    background_music: Path | None = None
    music_volume: float = 0.3

    # Colour preset
    color_preset: str | None = None

    # Template — overrides individual flags when set
    template: str | None = None

    @field_validator("main")
    @classmethod
    def main_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"Main video file not found: {v}")
        return v

    @model_validator(mode="after")
    def apply_template(self) -> PipelineConfig:
        """If a template is set, override individual flags from template config."""
        if self.template is None:
            return self

        from clearcut.styles import get_template

        tpl = get_template(self.template)

        # Override style from template's caption style name
        for name, preset_style in _caption_style_map().items():
            if preset_style == tpl.caption_style:
                self.style = name  # type: ignore[assignment]
                break

        self.normalize_audio = tpl.normalize_audio
        self.audio_target_lufs = tpl.audio_target_lufs
        self.transition = tpl.transition
        self.transition_duration = tpl.transition_duration
        self.format = tpl.format
        self.saturation = tpl.saturation
        self.contrast = tpl.contrast
        self.brightness = tpl.brightness
        self.punch_zoom = tpl.punch_zoom
        self.hook_zoom = tpl.hook_zoom
        self.color_preset = tpl.color_preset

        if tpl.lut_path is not None:
            self.lut = Path(tpl.lut_path)

        return self


class BatchConfig(BaseModel):
    """Configuration for batch processing of multiple video files."""

    input_dir: Path
    output_dir: Path
    pattern: str = "*.mp4"
    dry_run: bool = False
    max_workers: int = 2
    template: str | None = None
    style: str = "default"
    format: str = "16:9"
    hardware: str = "auto"
    silence_method: str = "vad"
    encoder_preset: str = "fast"

    @field_validator("input_dir")
    @classmethod
    def input_dir_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"Input directory not found: {v}")
        if not v.is_dir():
            raise ValueError(f"Input path is not a directory: {v}")
        return v


def _caption_style_map() -> dict[str, CaptionStyle]:
    """Lazy import to avoid circular dependency with styles module."""
    from clearcut.styles import PRESETS

    return PRESETS
