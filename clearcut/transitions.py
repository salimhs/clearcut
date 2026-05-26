"""Transition effects — crossfade, wipe, slide, dissolve between video segments."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from rich.console import Console

console = Console()

SUPPORTED_TRANSITIONS: list[str] = [
    "fade",
    "wipeleft",
    "wiperight",
    "slideleft",
    "slideright",
    "dissolve",
    "radial",
]


def _require_ffmpeg() -> None:
    """Raise if ffmpeg is not installed."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found in PATH")


def _get_duration(path: Path) -> float:
    """Get the duration of a media file in seconds via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "json",
            str(path),
        ],
        capture_output=True, text=True,
    )
    try:
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except (json.JSONDecodeError, KeyError, ValueError):
        raise RuntimeError(f"Could not determine duration of {path}")


def apply_transitions(
    segment_paths: list[Path],
    output_path: Path,
    transition: str = "fade",
    duration: float = 0.5,
) -> Path:
    """Concatenate video segments with transitions between each pair.

    Uses ffmpeg's ``xfade`` video filter to blend consecutive segments.

    Args:
        segment_paths: Ordered list of video files to join.
        output_path: Destination file.
        transition: Transition type (see :data:`SUPPORTED_TRANSITIONS`).
        duration: Transition duration in seconds.

    Returns:
        Path to the concatenated output file.

    Raises:
        ValueError: If fewer than 2 segments or an unsupported transition type.
        FileNotFoundError: If any segment file is missing.
        RuntimeError: If ffmpeg is missing.
    """
    segment_paths = [Path(p) for p in segment_paths]
    output_path = Path(output_path)

    if len(segment_paths) < 2:
        if len(segment_paths) == 1:
            console.print("[dim]Single segment — no transitions needed[/dim]")
            shutil.copy2(segment_paths[0], output_path)
            return output_path
        raise ValueError("Need at least one segment")

    for p in segment_paths:
        if not p.exists():
            raise FileNotFoundError(f"Segment file not found: {p}")

    if transition not in SUPPORTED_TRANSITIONS:
        raise ValueError(
            f"Unsupported transition '{transition}'. "
            f"Choose from: {', '.join(SUPPORTED_TRANSITIONS)}"
        )

    _require_ffmpeg()

    console.print(
        f"[cyan]Joining {len(segment_paths)} segments with "
        f"'{transition}' transitions ({duration}s each)[/cyan]"
    )

    # Get durations for offset calculations
    durations = [_get_duration(p) for p in segment_paths]

    # Validate that segments are long enough for the transition
    for i, dur in enumerate(durations):
        if dur <= duration:
            raise ValueError(
                f"Segment {i} ({segment_paths[i].name}) is {dur:.2f}s — "
                f"shorter than the transition duration ({duration}s)"
            )

    # Build ffmpeg filter_complex with chained xfade filters
    # For N segments we need N-1 xfade operations
    n = len(segment_paths)

    # Input flags
    inputs: list[str] = []
    for p in segment_paths:
        inputs += ["-i", str(p)]

    # Build the filter graph
    filter_parts: list[str] = []

    # Calculate offsets: each xfade starts at (sum of previous durations)
    # minus (number of previous transitions × transition duration)
    # because each transition overlaps *duration* seconds.
    offsets: list[float] = []
    cumulative = durations[0]
    for i in range(1, n):
        offset = cumulative - duration
        offsets.append(offset)
        cumulative += durations[i] - duration

    # Chain xfade filters
    prev_label = "[0:v]"
    for i in range(n - 1):
        next_input = f"[{i + 1}:v]"
        out_label = f"[v{i}]" if i < n - 2 else "[vout]"
        filter_parts.append(
            f"{prev_label}{next_input}xfade="
            f"transition={transition}:duration={duration}:"
            f"offset={offsets[i]:.3f}{out_label}"
        )
        prev_label = out_label

    # Audio: concat all audio streams sequentially
    audio_inputs = "".join(f"[{i}:a]" for i in range(n))
    filter_parts.append(
        f"{audio_inputs}concat=n={n}:v=0:a=1[aout]"
    )

    filter_complex = ";".join(filter_parts)

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "[aout]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path),
        ]
    )
    subprocess.run(cmd, check=True, capture_output=True)

    console.print(f"[green]Transitions applied → {output_path}[/green]")
    return output_path
