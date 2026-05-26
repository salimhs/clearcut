"""Pydantic models for pipeline configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, field_validator


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

    @field_validator("main")
    @classmethod
    def main_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"Main video file not found: {v}")
        return v
