"""Silence detection and removal using Silero-VAD or auto-editor fallback."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

console = Console()

Segment = tuple[float, float]


def _has_audio(input_path: Path) -> bool:
    """Check if a video file has an audio stream."""
    import subprocess
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-select_streams", "a",
         "-show_entries", "stream=codec_type",
         "-of", "csv=p=0", str(input_path)],
        capture_output=True, text=True,
    )
    return "audio" in result.stdout


def detect_audio_segments(input_path: Path, threshold: float = 0.5) -> list[Segment]:
    """Detect speech segments using Silero-VAD.

    Returns list of (start_seconds, end_seconds) tuples for voiced regions.
    """
    try:
        import torch
        import torchaudio
    except ImportError:
        raise RuntimeError(
            "Silero-VAD requires torch and torchaudio. "
            "Install with: pip install clearcut[silence]"
        )

    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad",
        model="silero_vad",
        force_reload=False,
        trust_repo=True,
    )
    get_speech_timestamps, _, read_audio, _, _ = utils

    SAMPLE_RATE = 16000
    wav = read_audio(str(input_path), sampling_rate=SAMPLE_RATE)
    speech_timestamps = get_speech_timestamps(
        wav, model, sampling_rate=SAMPLE_RATE, threshold=threshold
    )

    segments: list[Segment] = []
    for ts in speech_timestamps:
        start = ts["start"] / SAMPLE_RATE
        end = ts["end"] / SAMPLE_RATE
        segments.append((start, end))

    return _merge_close_segments(segments, gap=0.3)


def _merge_close_segments(segments: list[Segment], gap: float) -> list[Segment]:
    """Merge segments that are closer together than `gap` seconds."""
    if not segments:
        return []
    merged = [segments[0]]
    for start, end in segments[1:]:
        prev_start, prev_end = merged[-1]
        if start - prev_end <= gap:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged


def _pad_segments(segments: list[Segment], pad: float = 0.05) -> list[Segment]:
    """Add small padding around each segment to avoid clipping words."""
    return [(max(0.0, s - pad), e + pad) for s, e in segments]


def cut_silence(input_path: Path, segments: list[Segment], output_path: Path) -> Path:
    """Cut silence using ffmpeg concat demuxer with the given speech segments."""
    if not segments:
        console.print("[yellow]No speech segments found — copying original file[/yellow]")
        shutil.copy2(input_path, output_path)
        return output_path

    padded = _pad_segments(segments)

    with tempfile.TemporaryDirectory(prefix="clearcut_") as tmpdir:
        tmpdir_path = Path(tmpdir)
        segment_files: list[Path] = []

        for i, (start, end) in enumerate(padded):
            seg_path = tmpdir_path / f"seg_{i:04d}.ts"
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-ss", f"{start:.3f}",
                "-to", f"{end:.3f}",
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                seg_path.name,
            ]
            subprocess.run(
                cmd,
                cwd=str(tmpdir_path),
                capture_output=True,
                check=True,
            )
            segment_files.append(seg_path)

        concat_list = tmpdir_path / "concat.txt"
        concat_list.write_text(
            "\n".join(f"file '{seg.name}'" for seg in segment_files)
        )

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            "-movflags", "+faststart",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    return output_path


def _remove_silence_auto_editor(input_path: Path, output_path: Path) -> Path:
    """Fallback: use auto-editor CLI if installed."""
    if not shutil.which("auto-editor"):
        raise RuntimeError("auto-editor not found. Install with: pip install auto-editor")
    cmd = [
        "auto-editor",
        str(input_path),
        "--no-open",
        "--output", str(output_path),
    ]
    subprocess.run(cmd, check=True)
    return output_path


def remove_silence(
    input_path: Path,
    output_path: Path,
    method: str = "vad",
    threshold: float = 0.5,
) -> Path:
    """Remove silence from a video file.

    Args:
        input_path: Source video path.
        output_path: Destination path for trimmed video.
        method: "vad" for Silero-VAD (default), "auto-editor" for CLI fallback.
        threshold: VAD confidence threshold (0.0–1.0). Lower keeps more audio.

    Returns:
        Path to the output file.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Skip silence removal if video has no audio track
    if not _has_audio(input_path):
        console.print("[yellow]No audio track found — skipping silence removal[/yellow]")
        shutil.copy2(input_path, output_path)
        return output_path

    if method == "auto-editor":
        return _remove_silence_auto_editor(input_path, output_path)

    console.print(f"[cyan]Detecting speech segments in {input_path.name}...[/cyan]")

    try:
        segments = detect_audio_segments(input_path, threshold=threshold)
    except RuntimeError:
        console.print("[yellow]Silero-VAD unavailable, falling back to auto-editor[/yellow]")
        return _remove_silence_auto_editor(input_path, output_path)

    console.print(f"[green]Found {len(segments)} speech segments[/green]")

    return cut_silence(input_path, segments, output_path)
