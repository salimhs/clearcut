"""Intro / outro injection — prepend and append branded clips."""

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


def _require_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise EncodingError("ffmpeg not found in PATH")


def _get_resolution(path: Path) -> tuple[int, int]:
    """Return (width, height) of a video file."""
    probe = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json",
            str(path),
        ],
        capture_output=True, text=True,
    )
    try:
        info = json.loads(probe.stdout)
        return int(info["streams"][0]["width"]), int(info["streams"][0]["height"])
    except (json.JSONDecodeError, KeyError, IndexError):
        raise EncodingError(f"Could not determine video dimensions: {path}")


def _scale_to_match(
    clip_path: Path,
    target_w: int,
    target_h: int,
    output_path: Path,
) -> Path:
    """Scale a clip to match a target resolution if necessary."""
    cw, ch = _get_resolution(clip_path)
    if cw == target_w and ch == target_h:
        shutil.copy2(clip_path, output_path)
        return output_path

    console.print(
        f"[dim]Scaling {clip_path.name} from {cw}×{ch} → {target_w}×{target_h}[/dim]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(clip_path),
        "-vf", f"scale={target_w}:{target_h}:flags=lanczos",
        "-c:a", "aac",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def inject_intro(
    main_path: Path,
    intro_path: Path,
    output_path: Path,
    transition: str = "dissolve",
    transition_duration: float = 0.5,
) -> Path:
    """Prepend an intro clip to the main video with a dissolve transition.

    The intro is resolution-matched to the main video, then joined
    using ffmpeg's xfade filter for a smooth dissolve.

    Args:
        main_path: Main video file (post-silence removal).
        intro_path: Intro clip to prepend.
        output_path: Output file path.
        transition: xfade transition type (default: dissolve).
        transition_duration: Duration of the transition in seconds.

    Returns:
        Path to the output file.
    """
    main_path = Path(main_path)
    intro_path = Path(intro_path)
    output_path = Path(output_path)

    if not main_path.exists():
        raise FileError(f"Main file not found: {main_path}")
    if not intro_path.exists():
        raise FileError(f"Intro file not found: {intro_path}")
    _require_ffmpeg()

    main_w, main_h = _get_resolution(main_path)

    with tempfile.TemporaryDirectory(prefix="clearcut_intro_") as tmpdir:
        tmp = Path(tmpdir)
        scaled_intro = tmp / "intro_scaled.mp4"
        _scale_to_match(intro_path, main_w, main_h, scaled_intro)

        # Get intro duration for xfade offset
        probe = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "json",
                str(scaled_intro),
            ],
            capture_output=True, text=True,
        )
        try:
            intro_dur = float(json.loads(probe.stdout)["format"]["duration"])
        except (json.JSONDecodeError, KeyError):
            raise EncodingError(f"Could not determine duration: {intro_path}")

        offset = max(0, intro_dur - transition_duration)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(scaled_intro),
            "-i", str(main_path),
            "-filter_complex",
            f"[0:v][1:v]xfade=transition={transition}"
            f":duration={transition_duration}:offset={offset}[vout];"
            f"[0:a][1:a]acrossfade=d={transition_duration}[aout]",
            "-map", "[vout]",
            "-map", "[aout]",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    console.print(f"[green]Intro injected → {output_path}[/green]")
    return output_path


def append_outro(
    main_path: Path,
    outro_path: Path,
    output_path: Path,
    transition: str = "fade",
    transition_duration: float = 0.5,
) -> Path:
    """Append an outro clip to the main video with a fade transition.

    The outro is resolution-matched to the main video, then joined
    using ffmpeg's xfade filter for a smooth fade.

    Args:
        main_path: Main video file (post-encode).
        outro_path: Outro clip to append.
        output_path: Output file path.
        transition: xfade transition type (default: fade).
        transition_duration: Duration of the transition in seconds.

    Returns:
        Path to the output file.
    """
    main_path = Path(main_path)
    outro_path = Path(outro_path)
    output_path = Path(output_path)

    if not main_path.exists():
        raise FileError(f"Main file not found: {main_path}")
    if not outro_path.exists():
        raise FileError(f"Outro file not found: {outro_path}")
    _require_ffmpeg()

    main_w, main_h = _get_resolution(main_path)

    with tempfile.TemporaryDirectory(prefix="clearcut_outro_") as tmpdir:
        tmp = Path(tmpdir)
        scaled_outro = tmp / "outro_scaled.mp4"
        _scale_to_match(outro_path, main_w, main_h, scaled_outro)

        # Get main duration for xfade offset
        probe = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "json",
                str(main_path),
            ],
            capture_output=True, text=True,
        )
        try:
            main_dur = float(json.loads(probe.stdout)["format"]["duration"])
        except (json.JSONDecodeError, KeyError):
            raise EncodingError(f"Could not determine duration: {main_path}")

        offset = max(0, main_dur - transition_duration)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(main_path),
            "-i", str(scaled_outro),
            "-filter_complex",
            f"[0:v][1:v]xfade=transition={transition}"
            f":duration={transition_duration}:offset={offset}[vout];"
            f"[0:a][1:a]acrossfade=d={transition_duration}[aout]",
            "-map", "[vout]",
            "-map", "[aout]",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    console.print(f"[green]Outro appended → {output_path}[/green]")
    return output_path
