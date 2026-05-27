"""Tests for clearcut.styles — style presets, templates, ASS formatting."""

from __future__ import annotations

import pytest

from clearcut.models import CaptionStyle
from clearcut.styles import (
    DEFAULT,
    MODERN,
    MINIMAL,
    BOLD,
    TEMPLATES,
    get_style,
    get_template,
    to_ass_style_line,
)


class TestGetStyle:
    """Test get_style preset lookup."""

    def test_get_default(self) -> None:
        style = get_style("default")
        assert style == DEFAULT

    def test_get_modern(self) -> None:
        style = get_style("modern")
        assert style == MODERN
        assert style.font == "Montserrat"
        assert style.animation == "word"

    def test_get_minimal(self) -> None:
        style = get_style("minimal")
        assert style == MINIMAL

    def test_get_bold(self) -> None:
        style = get_style("bold")
        assert style == BOLD
        assert style.font == "Impact"

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown style"):
            get_style("unknown")


class TestGetTemplate:
    """Test get_template lookup."""

    def test_get_tiktok(self) -> None:
        tpl = get_template("tiktok")
        assert tpl.format == "9:16"
        assert tpl.hook_zoom is True
        assert tpl.caption_style == MODERN

    def test_get_cinematic(self) -> None:
        tpl = get_template("cinematic")
        assert tpl.format == "16:9"
        assert tpl.transition == "dissolve"

    def test_get_clean(self) -> None:
        tpl = get_template("clean")
        assert tpl.punch_zoom == 0.0
        assert tpl.hook_zoom is False

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown template"):
            get_template("nonexistent")

    def test_all_templates_have_required_fields(self) -> None:
        for name, tpl in TEMPLATES.items():
            assert tpl.name == name
            assert isinstance(tpl.caption_style, CaptionStyle)
            assert isinstance(tpl.format, str)


class TestToAssStyleLine:
    """Test ASS style line generation."""

    def test_default_style_format(self) -> None:
        line = to_ass_style_line(DEFAULT)
        assert line.startswith("Style: Default,")
        assert "Arial" in line
        assert "&H00FFFFFF" in line

    def test_bold_flag(self) -> None:
        bold_line = to_ass_style_line(CaptionStyle(bold=True))
        assert ",-1,0,0,0," in bold_line

        normal_line = to_ass_style_line(CaptionStyle(bold=False))
        assert ",0,0,0,0," in normal_line

    def test_alignment_bottom(self) -> None:
        line = to_ass_style_line(CaptionStyle(position="bottom"))
        # Alignment 2 = bottom center
        parts = line.split(",")
        assert parts[-5] == "2"

    def test_alignment_center(self) -> None:
        line = to_ass_style_line(CaptionStyle(position="center"))
        parts = line.split(",")
        assert parts[-5] == "5"

    def test_alignment_top(self) -> None:
        line = to_ass_style_line(CaptionStyle(position="top"))
        parts = line.split(",")
        assert parts[-5] == "8"

    def test_custom_name(self) -> None:
        line = to_ass_style_line(DEFAULT, name="Custom")
        assert line.startswith("Style: Custom,")
