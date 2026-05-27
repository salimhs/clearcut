"""Dynamic zoom / punch-in effects for video clips.

Adds cinematic zoom effects at the start of clips for streamer-style
"punch zoom" emphasis.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from rich.console import Console

from clearcut.exceptions import EncodingError, FileError

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
