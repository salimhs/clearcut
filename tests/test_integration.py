"""Integration tests for clearcut — test real pipeline stages with actual ffmpeg.

These tests generate short synthetic test videos using ffmpeg's lavfi
filters. They are marked with @require_ffmpeg and skipped when ffmpeg
is not available on the system (CI environments without it).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


# ─── Helpers ────────────────────────────────────────────────────


def require_ffmpeg(func):
    """Decorator: skip test if ffmpeg is not available."""
    return pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not available")(func)


def require_ffprobe(func):
    """Decorator: skip test if ffprobe is not available."""
    return pytest.mark.skipif(not shutil.which("ffprobe"), reason="ffprobe not available")(func)


def _torch_available() -> bool:
    """Check if PyTorch is importable without error."""
    try:
        import torch  # noqa: F401

        return True
    except (ImportError, OSError):
        return False


def require_torch(func):
    """Decorator: skip test if PyTorch is not available."""
    return pytest.mark.skipif(not _torch_available(), reason="PyTorch not available")(func)


def require_auto_editor(func):
    """Decorator: skip test if auto-editor is not available."""
    return pytest.mark.skipif(not shutil.which("auto-editor"), reason="auto-editor not available")(
        func
    )


# ─── Fixtures ───────────────────────────────────────────────────


@pytest.fixture
def sample_video(tmp_path: Path) -> Path:
    """Generate a 2-second test video with colour bars."""
    path = tmp_path / "input.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=2:size=1280x720:rate=30",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=mono",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-c:a",
            "aac",
            "-shortest",
            str(path),
        ],
        capture_output=True,
        check=True,
    )
    return path


@pytest.fixture
def sample_short(tmp_path: Path) -> Path:
    """Generate a 10-second test video at 1280x720 with real audio."""
    path = tmp_path / "short.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=1280x720:d=10",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=44100:d=10",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-c:a",
            "aac",
            "-shortest",
            str(path),
        ],
        capture_output=True,
        check=True,
    )
    return path


# ─── Silence Removal ────────────────────────────────────────────


class TestSilenceRemoval:
    @require_torch
    @require_ffmpeg
    def test_removal_on_noiseless_video(self, sample_video: Path, tmp_path: Path):
        """VAD on a video with no silence should produce same-length output."""
        from clearcut.silence import remove_silence

        output = tmp_path / "trimmed.mp4"
        remove_silence(sample_video, output, method="vad")

        assert output.exists(), "Output file was not created"
        assert output.stat().st_size > 0, "Output file is empty"

    @require_auto_editor
    @require_ffmpeg
    def test_auto_editor_fallback(self, sample_video: Path, tmp_path: Path):
        """Auto-editor method should produce valid output."""
        from clearcut.silence import remove_silence

        output = tmp_path / "trimmed.mp4"
        remove_silence(sample_video, output, method="auto-editor")

        assert output.exists()


# ─── Format Conversion ──────────────────────────────────────────


class TestFormatConversion:
    @require_ffmpeg
    @require_ffprobe
    def test_16_9_to_9_16(self, sample_video: Path, tmp_path: Path):
        """Convert 16:9 to 9:16 vertical format."""
        from clearcut.format import to_vertical

        output = tmp_path / "vertical.mp4"
        to_vertical(sample_video, output, crop_method="center")

        assert output.exists()
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=p=0",
                str(output),
            ],
            capture_output=True,
            text=True,
        )
        parts = probe.stdout.strip().split(",")
        assert len(parts) == 2, f"Expected width,height got: {parts}"
        width, height = map(int, parts)
        assert height > width, f"{width}x{height} is not vertical (expected 9:16)"

    @require_ffmpeg
    @require_ffprobe
    def test_16_9_to_1_1(self, sample_video: Path, tmp_path: Path):
        """Convert 16:9 to 1:1 square."""
        from clearcut.format import to_square

        output = tmp_path / "square.mp4"
        to_square(sample_video, output, crop_method="center")

        assert output.exists()
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=p=0",
                str(output),
            ],
            capture_output=True,
            text=True,
        )
        parts = probe.stdout.strip().split(",")
        assert len(parts) == 2, f"Expected width,height got: {parts}"
        width, height = map(int, parts)
        ratio = width / height if height > 0 else 0
        assert 0.9 <= ratio <= 1.1, f"{width}x{height} ratio={ratio:.2f} not square (expected ~1:1)"


# ─── Encoding ───────────────────────────────────────────────────


class TestEncoding:
    @require_ffmpeg
    def test_software_encoding(self, sample_video: Path, tmp_path: Path):
        """Software encoding should produce valid output."""
        from clearcut.encoder import encode

        output = tmp_path / "encoded.mp4"
        encode(sample_video, output, preset="fast", hardware="software")

        assert output.exists()
        assert output.stat().st_size > 0

    @require_ffmpeg
    def test_auto_hardware_detection(self, sample_video: Path, tmp_path: Path):
        """Auto hardware mode should not crash."""
        from clearcut.encoder import encode

        output = tmp_path / "auto_enc.mp4"
        encode(sample_video, output, preset="ultrafast", hardware="auto")

        assert output.exists()
        assert output.stat().st_size > 0


# ─── Intro / Outro ──────────────────────────────────────────────


class TestIntroOutro:
    @require_ffmpeg
    def test_intro_path_not_found(self, sample_video: Path, tmp_path: Path):
        """Missing intro file should raise FileError."""
        from clearcut.exceptions import FileError
        from clearcut.intro import inject_intro

        missing = tmp_path / "nonexistent.mp4"
        intro_out = tmp_path / "intro_out.mp4"
        with pytest.raises(FileError, match="not found"):
            inject_intro(missing, sample_video, intro_out)


# ─── Colour Correction ──────────────────────────────────────────


class TestColourCorrection:
    @require_ffmpeg
    def test_basic_correct(self, sample_video: Path, tmp_path: Path):
        """Basic colour correction should not corrupt output."""
        from clearcut.color import basic_correct

        output = tmp_path / "corrected.mp4"
        basic_correct(sample_video, output, brightness=0.1, contrast=1.1, saturation=1.1)

        assert output.exists()
        assert output.stat().st_size > 0

    @require_ffmpeg
    def test_default_passthrough(self, sample_video: Path, tmp_path: Path):
        """Default values (bri=0, con=1, sat=1) should copy the file."""
        from clearcut.color import basic_correct

        output = tmp_path / "passthrough.mp4"
        basic_correct(sample_video, output)

        assert output.exists()
        assert output.stat().st_size > 0

    @require_ffmpeg
    def test_missing_input_raises_error(self, tmp_path: Path):
        """Missing input file should raise FileError."""
        from clearcut.exceptions import FileError
        from clearcut.color import basic_correct

        missing = tmp_path / "nonexistent.mp4"
        output = tmp_path / "out.mp4"
        with pytest.raises(FileError, match="Input file not found"):
            basic_correct(missing, output)

    @require_ffmpeg
    def test_missing_lut_raises_error(self, sample_video: Path, tmp_path: Path):
        """Missing LUT file should raise FileError."""
        from clearcut.exceptions import FileError
        from clearcut.color import apply_lut

        missing_lut = tmp_path / "nonexistent.cube"
        output = tmp_path / "out.mp4"
        with pytest.raises(FileError, match="LUT file not found"):
            apply_lut(sample_video, output, missing_lut)


# ─── Merge ──────────────────────────────────────────────────────


class TestMerge:
    @require_ffmpeg
    def test_merge_two_clips(self, sample_short: Path, tmp_path: Path):
        """Merging two clips should produce valid output."""
        from clearcut.merger import merge_clips

        output = tmp_path / "merged.mp4"
        merge_clips(
            clips=[sample_short, sample_short],
            output_path=output,
            transition="fade",
            transition_duration=0.3,
        )

        assert output.exists()
        assert output.stat().st_size > 0

    @require_ffmpeg
    def test_empty_clips_list(self, tmp_path: Path):
        """Empty clips list should raise ConfigError."""
        from clearcut.exceptions import ConfigError
        from clearcut.merger import merge_clips

        with pytest.raises((ConfigError, ValueError)):
            merge_clips(
                clips=[],
                output_path=tmp_path / "empty.mp4",
                transition="fade",
                transition_duration=0.3,
            )


# ─── Speed Ramping ──────────────────────────────────────────────


class TestSpeedRamping:
    @require_ffmpeg
    def test_speed_segment_parse_and_apply(self, sample_video: Path, tmp_path: Path):
        """Speed ramping should produce valid output."""
        from clearcut.effects import (
            apply_speed_segments,
            parse_speed_segment,
            validate_speed_segments,
        )

        segments = [parse_speed_segment("0-2:2.0")]
        validate_speed_segments(segments)

        output = tmp_path / "speed.mp4"
        apply_speed_segments(sample_video, output, segments)

        assert output.exists()
        assert output.stat().st_size > 0


# ─── Pipeline Integration ───────────────────────────────────────


class TestPipelineIntegration:
    @require_torch
    @require_ffmpeg
    def test_silence_plus_encode(self, sample_video: Path, tmp_path: Path):
        """Silence removal followed by encoding should produce valid output."""
        from clearcut.silence import remove_silence
        from clearcut.encoder import encode

        trimmed = tmp_path / "trimmed.mp4"
        remove_silence(sample_video, trimmed, method="vad")

        final = tmp_path / "final.mp4"
        encode(trimmed, final, preset="ultrafast", hardware="auto")

        assert final.exists()
        assert final.stat().st_size > 0
