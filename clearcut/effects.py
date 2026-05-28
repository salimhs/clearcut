"""Dynamic zoom / punch-in effects and speed ramping for video clips.

Adds cinematic zoom effects at the start of clips for streamer-style
"punch zoom" emphasis, plus variable-speed segments.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from clearcut.exceptions import ConfigError, EncodingError, FileError

log = logging.getLogger(__name__)

console = Console()


def apply_punch_zoom(
    input_path: Path,
    output_path: Path,
    zoom_in: float = 1.05,
) -> Path:
    """Apply a static punch zoom (crop + scale) to a clip.

    Crops the center then scales back to original dimensions,
    creating a 5% zoomed-in effect. Simple, reliable, no ffmpeg
    expression syntax issues.

    Args:
        input_path: Source video file.
        output_path: Destination file with zoom effect.
        zoom_in: Zoom factor (1.05 = 5% zoomed in, 1.15 = 15%).

    Returns:
        Path to the zoomed output file.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileError(f"Input file not found: {input_path}")
    if not shutil.which("ffmpeg"):
        raise EncodingError("ffmpeg not found in PATH")

    # Get input dimensions
    probe = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json",
            str(input_path),
        ],
        capture_output=True, text=True,
    )
    try:
        info = json.loads(probe.stdout)
        w = int(info["streams"][0]["width"])
        h = int(info["streams"][0]["height"])
    except (json.JSONDecodeError, KeyError, IndexError):
        raise EncodingError(f"Could not determine video dimensions: {input_path}")

    console.print(
        f"[cyan]Applying punch zoom ({zoom_in}x) on {input_path.name}[/cyan]"
    )

    # Crop center then scale back up = static zoom effect
    crop_w = int(w / zoom_in)
    crop_h = int(h / zoom_in)
    crop_x = int((w - crop_w) / 2)
    crop_y = int((h - crop_h) / 2)

    vf = f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale={w}:{h}:flags=lanczos"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", vf,
        "-c:a", "copy",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    console.print(f"[green]Punch zoom applied → {output_path}[/green]")
    return output_path


def add_hook_zoom(
    input_path: Path,
    output_path: Path,
    hook_duration: float = 2.0,
    zoom_amount: float = 1.08,
) -> Path:
    """Add a quick zoom-in at the start for a hook effect.

    Zooms in over the first `hook_duration` seconds, then cuts to
    normal view. Mimics the streamer "punch zoom on reaction" style.

    Uses split + crop/scale for the hook portion, then concat with
    the remainder.

    Args:
        input_path: Source video file.
        output_path: Destination file.
        hook_duration: Seconds to apply the hook zoom.
        zoom_amount: How much to zoom (1.08 = 8% zoom).

    Returns:
        Path to output file.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileError(f"Input file not found: {input_path}")
    if not shutil.which("ffmpeg"):
        raise EncodingError("ffmpeg not found in PATH")

    console.print(
        f"[cyan]Adding hook zoom ({zoom_amount}x for {hook_duration}s) "
        f"on {input_path.name}[/cyan]"
    )

    # Get total duration
    probe = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "json",
            str(input_path),
        ],
        capture_output=True, text=True,
    )
    try:
        total_dur = float(json.loads(probe.stdout)["format"]["duration"])
    except (json.JSONDecodeError, KeyError):
        raise EncodingError(f"Could not determine duration: {input_path}")

    if total_dur <= hook_duration:
        shutil.copy2(input_path, output_path)
        return output_path

    # Get dimensions
    probe2 = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json",
            str(input_path),
        ],
        capture_output=True, text=True,
    )
    try:
        info = json.loads(probe2.stdout)
        w = int(info["streams"][0]["width"])
        h = int(info["streams"][0]["height"])
    except (json.JSONDecodeError, KeyError, IndexError):
        raise EncodingError(f"Could not determine video dimensions: {input_path}")

    with tempfile.TemporaryDirectory(prefix="clearcut_zoom_") as tmpdir:
        tmp = Path(tmpdir)
        part1 = tmp / "hook.mp4"
        part2 = tmp / "rest.mp4"

        # Part 1: first hook_duration seconds with static zoom
        crop_w = int(w / zoom_amount)
        crop_h = int(h / zoom_amount)
        crop_x = int((w - crop_w) / 2)
        crop_y = int((h - crop_h) / 2)

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-t", str(hook_duration),
                "-vf",
                f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},"
                f"scale={w}:{h}:flags=lanczos",
                "-c:a", "aac",
                str(part1),
            ],
            capture_output=True, check=True,
        )

        # Part 2: rest of video, unzoomed
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-ss", str(hook_duration),
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                str(part2),
            ],
            capture_output=True, check=True,
        )

        # Concatenate (use absolute paths in concat file)
        concat_file = tmp / "concat.txt"
        concat_file.write_text(
            f"file '{part1}'\nfile '{part2}'\n"
        )
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(output_path),
            ],
            capture_output=True, check=True,
        )

    console.print(f"[green]Hook zoom applied → {output_path}[/green]")
    return output_path


# ---------------------------------------------------------------------------
# Speed ramping — variable speed segments
# ---------------------------------------------------------------------------


@dataclass
class SpeedSegment:
    """A time range with a speed multiplier."""

    start: float
    end: float
    speed: float


def parse_speed_segment(raw: str) -> SpeedSegment:
    """Parse a speed segment string like '0-5:0.5'.

    Format: ``start-end:multiplier``

    Raises:
        ConfigError: If the format is invalid or values are out of range.
    """
    m = re.match(r"^([\d.]+)-([\d.]+):([\d.]+)$", raw.strip())
    if not m:
        raise ConfigError(
            f"Invalid speed segment '{raw}'. Expected format: start-end:multiplier"
        )
    start, end, speed = float(m.group(1)), float(m.group(2)), float(m.group(3))
    if start >= end:
        raise ConfigError(f"Speed segment start ({start}) must be < end ({end})")
    if speed < 0.1 or speed > 10.0:
        raise ConfigError(f"Speed multiplier must be 0.1–10.0, got {speed}")
    return SpeedSegment(start=start, end=end, speed=speed)


def validate_speed_segments(segments: list[SpeedSegment]) -> None:
    """Check that speed segments don't overlap.

    Raises:
        ConfigError: If any two segments overlap.
    """
    sorted_segs = sorted(segments, key=lambda s: s.start)
    for i in range(len(sorted_segs) - 1):
        if sorted_segs[i].end > sorted_segs[i + 1].start:
            raise ConfigError(
                f"Speed segments overlap: "
                f"{sorted_segs[i].start}-{sorted_segs[i].end} and "
                f"{sorted_segs[i + 1].start}-{sorted_segs[i + 1].end}"
            )


def _build_atempo_chain(speed: float) -> list[str]:
    """Build a chain of atempo filters for a given speed.

    ffmpeg atempo is limited to 0.5–2.0 per instance, so we chain
    multiple filters for values outside that range.
    """
    filters: list[str] = []
    remaining = speed
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.6f}")
    return filters


def apply_speed_segments(
    input_path: Path,
    output_path: Path,
    segments: list[SpeedSegment],
) -> Path:
    """Apply variable speed to specific time ranges of a video.

    Splits the video into parts (normal-speed gaps and speed-adjusted
    segments), processes each, then concatenates with brief audio
    crossfades at boundaries.

    Args:
        input_path: Source video file.
        output_path: Destination file.
        segments: Parsed and validated speed segments.

    Returns:
        Path to the output file.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileError(f"Input file not found: {input_path}")
    if not shutil.which("ffmpeg"):
        raise EncodingError("ffmpeg not found in PATH")

    # Get total duration
    probe = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "json",
            str(input_path),
        ],
        capture_output=True, text=True,
    )
    try:
        total_dur = float(json.loads(probe.stdout)["format"]["duration"])
    except (json.JSONDecodeError, KeyError):
        raise EncodingError(f"Could not determine duration: {input_path}")

    sorted_segs = sorted(segments, key=lambda s: s.start)

    with tempfile.TemporaryDirectory(prefix="clearcut_speed_") as tmpdir:
        tmp = Path(tmpdir)
        parts: list[Path] = []
        cursor = 0.0

        for i, seg in enumerate(sorted_segs):
            # Normal-speed gap before this segment
            if seg.start > cursor:
                part = tmp / f"normal_{i}.mp4"
                subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-i", str(input_path),
                        "-ss", str(cursor),
                        "-to", str(seg.start),
                        "-c", "copy",
                        "-avoid_negative_ts", "make_zero",
                        str(part),
                    ],
                    capture_output=True, check=True,
                )
                parts.append(part)

            # Speed-adjusted segment
            part = tmp / f"speed_{i}.mp4"
            vf = f"setpts={1.0 / seg.speed:.6f}*PTS"
            atempo = _build_atempo_chain(seg.speed)
            af = ",".join(atempo)

            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(input_path),
                    "-ss", str(seg.start),
                    "-to", str(seg.end),
                    "-vf", vf,
                    "-af", af,
                    "-avoid_negative_ts", "make_zero",
                    str(part),
                ],
                capture_output=True, check=True,
            )
            parts.append(part)
            cursor = seg.end

        # Trailing normal-speed portion
        if cursor < total_dur:
            part = tmp / "normal_tail.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(input_path),
                    "-ss", str(cursor),
                    "-c", "copy",
                    "-avoid_negative_ts", "make_zero",
                    str(part),
                ],
                capture_output=True, check=True,
            )
            parts.append(part)

        # Concatenate all parts
        concat_file = tmp / "concat.txt"
        concat_file.write_text(
            "\n".join(f"file '{p}'" for p in parts) + "\n"
        )
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(output_path),
            ],
            capture_output=True, check=True,
        )

    console.print(f"[green]Speed ramping applied → {output_path}[/green]")
    return output_path
