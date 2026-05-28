"""Tests for clearcut.color — LUT validation, parameter clamping, and color presets."""

from __future__ import annotations

from pathlib import Path

import pytest

from clearcut.color import _validate_cube_file, basic_correct, apply_lut
from clearcut.exceptions import FileError
from clearcut.styles import COLOR_PRESETS


class TestValidateCubeFile:
    """Test _validate_cube_file with valid and invalid files."""

    def test_valid_cube_file(self, tmp_path: Path) -> None:
        cube = tmp_path / "test.cube"
        cube.write_text(
            "# Created by test\n"
            "LUT_3D_SIZE 33\n"
            "0.0 0.0 0.0\n"
            "1.0 1.0 1.0\n"
        )
        assert _validate_cube_file(cube) is True

    def test_no_header(self, tmp_path: Path) -> None:
        cube = tmp_path / "bad.cube"
        cube.write_text("0.0 0.0 0.0\n1.0 1.0 1.0\n")
        assert _validate_cube_file(cube) is False

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        assert _validate_cube_file(tmp_path / "missing.cube") is False

    def test_case_insensitive_header(self, tmp_path: Path) -> None:
        cube = tmp_path / "test.cube"
        cube.write_text("lut_3d_size 17\n0.0 0.0 0.0\n")
        assert _validate_cube_file(cube) is True


class TestApplyLut:
    """Test apply_lut parameter clamping."""

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileError, match="Input file not found"):
            apply_lut(
                tmp_path / "missing.mp4",
                tmp_path / "out.mp4",
                tmp_path / "test.cube",
            )

    def test_lut_not_found(self, tmp_path: Path) -> None:
        video = tmp_path / "test.mp4"
        video.write_bytes(b"\x00")
        with pytest.raises(FileError, match="LUT file not found"):
            apply_lut(video, tmp_path / "out.mp4", tmp_path / "missing.cube")


class TestBasicCorrect:
    """Test basic_correct parameter clamping."""

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileError, match="Input file not found"):
            basic_correct(tmp_path / "missing.mp4", tmp_path / "out.mp4")

    def test_default_values_copy(self, tmp_path: Path, mocker) -> None:
        """When all values are defaults, basic_correct copies the file."""
        video = tmp_path / "test.mp4"
        video.write_bytes(b"\x00" * 100)
        output = tmp_path / "out.mp4"

        mocker.patch("clearcut.color.shutil.which", return_value="/usr/bin/ffmpeg")

        result = basic_correct(video, output)
        assert result == output
        assert output.exists()


class TestColorPresets:
    """Test predefined colour correction presets."""

    def test_warm_has_correct_values(self) -> None:
        preset = COLOR_PRESETS["warm"]
        assert preset["temperature"] == 15
        assert preset["saturation"] == 1.1

    def test_cool_has_correct_values(self) -> None:
        preset = COLOR_PRESETS["cool"]
        assert preset["temperature"] == -15
        assert preset["saturation"] == 1.0

    def test_vintage_has_correct_values(self) -> None:
        preset = COLOR_PRESETS["vintage"]
        assert preset["saturation"] == 0.7
        assert preset["temperature"] == 10
        assert preset["contrast"] == 0.9

    def test_vibrant_has_correct_values(self) -> None:
        preset = COLOR_PRESETS["vibrant"]
        assert preset["saturation"] == 1.3
        assert preset["temperature"] == 5

    def test_drama_has_correct_values(self) -> None:
        preset = COLOR_PRESETS["drama"]
        assert preset["contrast"] == 1.3
        assert preset["brightness"] == -0.05

    def test_all_presets_in_valid_ranges(self) -> None:
        for name, preset in COLOR_PRESETS.items():
            if "saturation" in preset:
                assert 0.0 <= preset["saturation"] <= 2.0
            if "contrast" in preset:
                assert 0.0 <= preset["contrast"] <= 2.0
            if "brightness" in preset:
                assert -1.0 <= preset["brightness"] <= 1.0
            if "temperature" in preset:
                assert -100 <= preset["temperature"] <= 100
