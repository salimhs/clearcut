"""Caption style presets with ASS subtitle parameters."""

from __future__ import annotations

from clearcut.models import CaptionStyle

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
