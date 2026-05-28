"""Merge multiple video clips into one — with transitions, audio normalization, and HW encoding."""

from __future__ import annotations

import logging
from pathlib import Path

from rich.console import Console

from clearcut.exceptions import ConfigError, FileError

log = logging.getLogger(__name__)
console = Console()


def merge_clips(
    clips: list[Path],
    output_path: Path,
    transition: str = "fade",
    transition_duration: float = 0.5,
    hardware: str = "auto",
) -> Path:
    """Merge multiple video clips into a single output file.

    Applies audio normalization across segments, transitions between clips,
    and re-encodes with hardware acceleration.

    Args:
        clips: List of input video file paths.
        output_path: Destination file.
        transition: Transition type for apply_transitions.
        transition_duration: Transition duration in seconds.
        hardware: Hardware encoder preference.

    Returns:
        Path to the merged output file.
    """
    if not clips:
        raise ConfigError("No input clips provided")

    for clip in clips:
        if not clip.exists():
            raise FileError(f"Clip not found: {clip}")

    console.print(f"[cyan]Merging {len(clips)} clip(s)[/cyan]")

    import tempfile

    from clearcut.audio import normalize_audio
    from clearcut.encoder import encode
    from clearcut.progress import stage_progress
    from clearcut.transitions import apply_transitions
    from clearcut.utils import has_audio

    with tempfile.TemporaryDirectory(prefix="clearcut_merge_") as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Normalize audio across all segments
        normalized: list[Path] = []
        with stage_progress("Normalizing audio...") as progress:
            task = progress.add_task("Normalizing audio...", total=len(clips))
            for i, clip in enumerate(clips):
                norm_path = tmpdir_path / f"norm_{i:04d}.mp4"
                if has_audio(clip):
                    normalize_audio(clip, norm_path)
                else:
                    import shutil

                    shutil.copy2(clip, norm_path)
                normalized.append(norm_path)
                progress.update(task, completed=i + 1)

        # Apply transitions
        if len(normalized) >= 2:
            with stage_progress("Applying transitions...") as progress:
                progress.add_task("Applying transitions...", total=None)
                transition_output = tmpdir_path / "merged_transitions.mp4"
                apply_transitions(
                    normalized,
                    transition_output,
                    transition=transition,
                    duration=transition_duration,
                )
        else:
            import shutil

            transition_output = tmpdir_path / "merged_transitions.mp4"
            shutil.copy2(normalized[0], transition_output)

        # Final encode with hardware acceleration
        with stage_progress("Encoding final output...") as progress:
            progress.add_task("Encoding final output...", total=None)
            encode(
                transition_output,
                output_path,
                hardware=hardware,
            )

    console.print(f"[green]Merged output → {output_path}[/green]")
    return output_path


def collect_clips_from_dir(
    directory: Path,
    pattern: str = "*.mp4",
) -> list[Path]:
    """Collect and sort video files from a directory."""
    if not directory.exists():
        raise FileError(f"Directory not found: {directory}")
    return sorted(directory.glob(pattern))
