"""Scene detection — split video at scene boundaries using PySceneDetect."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from rich.console import Console

from clearcut.exceptions import EncodingError, FileError

log = logging.getLogger(__name__)
console = Console()


def _require_scenedetect() -> None:
    """Lazily import scenedetect, raising a helpful error if missing."""
    try:
        import scenedetect  # noqa: F401
    except ImportError:
        raise ImportError(
            "Scene detection requires the 'scenedetect' package. "
            "Install it with: pip install 'clearcut[scenes]' "
            "or: pip install scenedetect[opencv]"
        )


def detect_scene_boundaries(video_path: Path, threshold: float = 27.0) -> list[float]:
    """Detect scene change timestamps using PySceneDetect ContentDetector.

    Args:
        video_path: Path to the video file.
        threshold: ContentDetector sensitivity (lower = more sensitive).

    Returns:
        Sorted list of scene boundary timestamps in seconds.

    Raises:
        ImportError: If scenedetect is not installed.
        FileError: If video_path does not exist.
    """
    _require_scenedetect()

    from scenedetect import open_video, SceneManager
    from scenedetect.detectors import ContentDetector

    video_path = Path(video_path)
    if not video_path.exists():
        raise FileError(f"Input file not found: {video_path}")

    console.print(f"[cyan]Detecting scenes in {video_path.name}...[/cyan]")

    video = open_video(str(video_path))
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    scene_manager.detect_scenes(video)

    scene_list = scene_manager.get_scene_list()
    # Each scene is a tuple of (start_timecode, end_timecode)
    boundaries: list[float] = []
    for _start, end in scene_list[:-1]:  # skip last scene's end (= video end)
        boundaries.append(end.get_seconds())

    console.print(f"[green]Found {len(boundaries)} scene boundaries[/green]")
    return sorted(boundaries)


def split_at_boundaries(
    video_path: Path,
    boundaries: list[float],
    output_dir: Path,
    max_clip_duration: float = 0.0,
) -> list[Path]:
    """Split a video at the given timestamps.

    Args:
        video_path: Source video file.
        boundaries: Sorted list of split points in seconds.
        output_dir: Directory to write segment files into.
        max_clip_duration: If > 0, force additional splits so no segment
            exceeds this duration.

    Returns:
        List of segment file paths in order.
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)

    if not video_path.exists():
        raise FileError(f"Input file not found: {video_path}")
    if not shutil.which("ffmpeg"):
        raise EncodingError("ffmpeg not found in PATH")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Add forced splits for max_clip_duration
    all_splits = list(boundaries)
    if max_clip_duration > 0:
        # Get total duration
        import json

        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(video_path),
            ],
            capture_output=True,
            text=True,
        )
        try:
            total_dur = float(json.loads(probe.stdout)["format"]["duration"])
        except (json.JSONDecodeError, KeyError):
            total_dur = 0.0

        if total_dur > 0:
            # Build final split list with forced boundaries
            forced: list[float] = []
            prev = 0.0
            for b in sorted(all_splits):
                while b - prev > max_clip_duration:
                    prev += max_clip_duration
                    forced.append(prev)
                prev = b
            # Handle tail
            while total_dur - prev > max_clip_duration:
                prev += max_clip_duration
                forced.append(prev)
            all_splits = sorted(set(all_splits + forced))

    # Build segment list
    segments: list[Path] = []
    starts = [0.0] + all_splits

    for i, start in enumerate(starts):
        seg_path = output_dir / f"scene_{i:04d}.mp4"
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-ss",
            str(start),
        ]
        if i < len(all_splits):
            cmd.extend(["-to", str(all_splits[i])])
        cmd.extend(
            [
                "-c",
                "copy",
                "-avoid_negative_ts",
                "make_zero",
                str(seg_path),
            ]
        )
        subprocess.run(cmd, capture_output=True, check=True)
        segments.append(seg_path)

    console.print(f"[green]Split into {len(segments)} segments[/green]")
    return segments
