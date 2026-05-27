"""Format conversion — vertical (9:16 TikTok/Reels), square (1:1), etc."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

from rich.console import Console


from clearcut.exceptions import EncodingError, FileError
log = logging.getLogger(__name__)

console = Console()


def _require_ffmpeg() -> None:
    """Raise if ffmpeg/ffprobe are not installed."""
    if not shutil.which("ffmpeg"):
        raise EncodingError("ffmpeg not found in PATH")
    if not shutil.which("ffprobe"):
        raise EncodingError("ffprobe not found in PATH")


def detect_aspect(input_path: Path) -> dict:
    """Probe a file for video dimensions and aspect ratio.

    Returns:
        Dict with keys: width, height, aspect_ratio, display_aspect_ratio.

    Raises:
        FileNotFoundError: If *input_path* does not exist.
        RuntimeError: If ffprobe is missing or no video stream found.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileError(f"Input file not found: {input_path}")

    _require_ffmpeg()

    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries",
            "stream=width,height,display_aspect_ratio",
            "-of", "json",
            str(input_path),
        ],
        capture_output=True, text=True,
    )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise EncodingError(f"Could not probe video dimensions: {input_path}")

    streams = data.get("streams", [])
    if not streams:
        raise EncodingError(f"No video stream found in {input_path}")

    s = streams[0]
    width = int(s.get("width", 0))
    height = int(s.get("height", 0))
    dar = s.get("display_aspect_ratio", "")

    return {
        "width": width,
        "height": height,
        "aspect_ratio": f"{width}:{height}",
        "display_aspect_ratio": dar if dar else f"{width}:{height}",
    }


def _reformat(
    input_path: Path,
    output_path: Path,
    target_w: int,
    target_h: int,
    crop_method: str,
    label: str,
) -> Path:
    """Shared logic for cropping/padding a video to a target resolution.

    Uses crop-then-scale so the output is always exactly target_w × target_h.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileError(f"Input file not found: {input_path}")

    _require_ffmpeg()

    info = detect_aspect(input_path)
    src_w = info["width"]
    src_h = info["height"]

    console.print(
        f"[cyan]Converting {src_w}×{src_h} → {target_w}×{target_h} "
        f"({label}, crop={crop_method})[/cyan]"
    )

    # Figure out the crop dimensions to match the target aspect ratio
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # Source is wider — crop horizontally
        crop_h = src_h
        crop_w = int(src_h * target_ratio)
    else:
        # Source is taller — crop vertically
        crop_w = src_w
        crop_h = int(src_w / target_ratio)

    # Position the crop window
    if crop_method == "top":
        crop_x = (src_w - crop_w) // 2
        crop_y = 0
    else:
        # "center" and "smart" both default to center crop
        crop_x = (src_w - crop_w) // 2
        crop_y = (src_h - crop_h) // 2

    vf = (
        f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},"
        f"scale={target_w}:{target_h}:flags=lanczos"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", vf,
        "-c:a", "copy",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    console.print(f"[green]Formatted → {output_path}[/green]")
    return output_path


def to_vertical(
    input_path: Path,
    output_path: Path,
    crop_method: str = "center",
    scale: float = 0.8,
) -> Path:
    """Convert video to 9:16 vertical format (1080×1920) for TikTok/Reels.

    Args:
        input_path: Source video file.
        output_path: Destination vertical file.
        crop_method: "center" (default), "top" (headroom priority), or "smart".
        scale: Not used for crop-based conversion; reserved for future
            picture-in-frame modes.

    Returns:
        Path to the vertical output file.
    """
    return _reformat(input_path, output_path, 1080, 1920, crop_method, "9:16 vertical")


def to_square(
    input_path: Path,
    output_path: Path,
    crop_method: str = "center",
) -> Path:
    """Convert video to 1:1 square format (1080×1080) for Instagram.

    Args:
        input_path: Source video file.
        output_path: Destination square file.
        crop_method: "center" (default) or "top".

    Returns:
        Path to the square output file.
    """
    return _reformat(input_path, output_path, 1080, 1080, crop_method, "1:1 square")


def to_landscape(
    input_path: Path,
    output_path: Path,
) -> Path:
    """Convert video to 16:9 landscape format (1920×1080).

    Useful for normalising non-standard aspect ratios to standard HD.

    Args:
        input_path: Source video file.
        output_path: Destination landscape file.

    Returns:
        Path to the landscape output file.
    """
    return _reformat(input_path, output_path, 1920, 1080, "center", "16:9 landscape")
