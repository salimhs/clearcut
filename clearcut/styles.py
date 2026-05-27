"""Caption style presets, ASS subtitle parameters, and template system."""

from __future__ import annotations

import logging
from dataclasses import dataclass


from clearcut.models import CaptionStyle
log = logging.getLogger(__name__)

DEFAULT = CaptionStyle(
    font="Arial",
    color="&H00FFFFFF",
    outline_color="&H00000000",
    size=48,
    position="bottom",
    bold=True,
    outline=2,
    shadow=1,
    margin_v=40,
    animation="none",
)

MODERN = CaptionStyle(
    font="Montserrat",
    color="&H00FFFFFF",
    outline_color="&H00000000",
    size=52,
    position="bottom",
    bold=True,
    outline=3,
    shadow=0,
    margin_v=50,
    animation="word",
)

MINIMAL = CaptionStyle(
    font="Helvetica Neue",
    color="&H00E0E0E0",
    outline_color="&H00202020",
    size=40,
    position="bottom",
    bold=False,
    outline=1,
    shadow=0,
    margin_v=30,
    animation="none",
)

BOLD = CaptionStyle(
    font="Impact",
    color="&H0000FFFF",  # yellow in ASS BGR
    outline_color="&H00000000",
    size=64,
    position="center",
    bold=True,
    outline=4,
    shadow=2,
    margin_v=20,
    animation="word",
)

PRESETS: dict[str, CaptionStyle] = {
    "default": DEFAULT,
    "modern": MODERN,
    "minimal": MINIMAL,
    "bold": BOLD,
}


def get_style(name: str) -> CaptionStyle:
    """Get a caption style preset by name."""
    if name not in PRESETS:
        raise ValueError(f"Unknown style '{name}'. Choose from: {', '.join(PRESETS)}")
    return PRESETS[name]


def to_ass_style_line(style: CaptionStyle, name: str = "Default") -> str:
    """Convert a CaptionStyle to an ASS Style line."""
    alignment = {"bottom": 2, "center": 5, "top": 8}[style.position]
    bold_flag = -1 if style.bold else 0
    return (
        f"Style: {name},"
        f"{style.font},{style.size},"
        f"{style.color},{style.color},{style.outline_color},{style.outline_color},"
        f"{bold_flag},0,0,0,"  # bold, italic, underline, strikeout
        f"100,100,0,0,"  # scaleX, scaleY, spacing, angle
        f"1,"  # border style (outline + drop shadow)
        f"{style.outline},{style.shadow},"  # outline, shadow
        f"{alignment},"  # alignment
        f"10,10,{style.margin_v},"  # marginL, marginR, marginV
        f"1"  # encoding
    )


# ---------------------------------------------------------------------------
# Template system — bundles caption style, colour, audio, and format presets
# ---------------------------------------------------------------------------


@dataclass
class Template:
    """A full pipeline preset that bundles multiple settings."""

    name: str
    caption_style: CaptionStyle
    lut_path: str | None  # path to .cube LUT
    transition: str  # default transition type
    transition_duration: float
    format: str  # "16:9", "9:16", "1:1"
    normalize_audio: bool
    audio_target_lufs: float
    saturation: float
    contrast: float
    brightness: float
    punch_zoom: float  # 0 = off, 1.05 = 5% zoom
    hook_zoom: bool  # quick zoom on first 2s


TEMPLATES: dict[str, Template] = {
    "clean": Template(
        name="clean",
        caption_style=DEFAULT,
        lut_path=None,
        transition="fade",
        transition_duration=0.3,
        format="16:9",
        normalize_audio=True,
        audio_target_lufs=-14.0,
        saturation=1.0,
        contrast=1.0,
        brightness=0.0,
        punch_zoom=0.0,
        hook_zoom=False,
    ),
    "tiktok": Template(
        name="tiktok",
        caption_style=MODERN,
        lut_path=None,
        transition="wiperight",
        transition_duration=0.4,
        format="9:16",
        normalize_audio=True,
        audio_target_lufs=-13.0,
        saturation=1.1,
        contrast=1.05,
        brightness=0.02,
        punch_zoom=1.05,
        hook_zoom=True,
    ),
    "cinematic": Template(
        name="cinematic",
        caption_style=MINIMAL,
        lut_path=None,
        transition="dissolve",
        transition_duration=0.5,
        format="16:9",
        normalize_audio=True,
        audio_target_lufs=-16.0,
        saturation=0.85,
        contrast=1.15,
        brightness=-0.02,
        punch_zoom=1.03,
        hook_zoom=False,
    ),
    "bold": Template(
        name="bold",
        caption_style=BOLD,
        lut_path=None,
        transition="slideleft",
        transition_duration=0.4,
        format="16:9",
        normalize_audio=True,
        audio_target_lufs=-14.0,
        saturation=1.2,
        contrast=1.1,
        brightness=0.02,
        punch_zoom=1.08,
        hook_zoom=True,
    ),
}


def get_template(name: str) -> Template:
    """Get a template preset by name.

    Raises:
        ValueError: If *name* is not a known template.
    """
    if name not in TEMPLATES:
        raise ValueError(
            f"Unknown template '{name}'. Choose from: {', '.join(TEMPLATES)}"
        )
    return TEMPLATES[name]


def list_templates() -> list[str]:
    """Return the names of all available templates."""
    return list(TEMPLATES.keys())
