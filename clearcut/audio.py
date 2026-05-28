"""Audio processing — normalization (EBU R128) and ducking (sidechain compression)."""

from __future__ import annotations

import json
import logging
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any


from rich.console import Console

from clearcut.exceptions import AudioError, FileError
from clearcut.utils import has_audio

log = logging.getLogger(__name__)

console = Console()


def _require_ffmpeg() -> None:
    """Raise if ffmpeg/ffprobe are not installed."""
    if not shutil.which("ffmpeg"):
        raise AudioError("ffmpeg not found in PATH")
    if not shutil.which("ffprobe"):
        raise AudioError("ffprobe not found in PATH")


def detect_audio(input_path: Path) -> dict:
    """Probe a file for audio stream information.

    Returns:
        Dict with keys: codec, channels, sample_rate, bitrate.
        Returns empty dict if the file has no audio stream.

    Raises:
        FileNotFoundError: If *input_path* does not exist.
        RuntimeError: If ffprobe is not installed.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileError(f"Input file not found: {input_path}")

    _require_ffmpeg()

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,channels,sample_rate,bit_rate",
            "-of",
            "json",
            str(input_path),
        ],
        capture_output=True,
        text=True,
    )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}

    streams = data.get("streams", [])
    if not streams:
        return {}

    s = streams[0]
    return {
        "codec": s.get("codec_name", "unknown"),
        "channels": int(s.get("channels", 0)),
        "sample_rate": int(s.get("sample_rate", 0)),
        "bitrate": s.get("bit_rate", "unknown"),
    }


def normalize_audio(
    input_path: Path,
    output_path: Path,
    target_lufs: float = -14.0,
    true_peak: float = -1.5,
) -> Path:
    """Normalize audio to EBU R128 loudness standards using ffmpeg loudnorm.

    Two-pass approach: measure first, then apply correction.

    Args:
        input_path: Source audio/video file.
        output_path: Destination file with normalized audio.
        target_lufs: Target integrated loudness in LUFS (default -14).
        true_peak: Maximum true peak in dBTP (default -1.5).

    Returns:
        Path to the normalized output file.

    Raises:
        FileNotFoundError: If *input_path* does not exist.
        RuntimeError: If ffmpeg is missing or the file has no audio.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileError(f"Input file not found: {input_path}")

    _require_ffmpeg()

    if not has_audio(input_path):
        console.print("[yellow]No audio stream — skipping normalization[/yellow]")
        shutil.copy2(input_path, output_path)
        return output_path

    console.print(f"[cyan]Normalizing audio → {target_lufs} LUFS, TP {true_peak} dBTP[/cyan]")

    # Pass 1: measure current loudness
    measure_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-af",
        (f"loudnorm=I={target_lufs}:TP={true_peak}:LRA=11:print_format=json"),
        "-f",
        "null",
        "-",
    ]
    measure = subprocess.run(measure_cmd, capture_output=True, text=True)

    # Parse the loudnorm JSON from stderr (ffmpeg outputs it there)
    stderr_lines = measure.stderr.splitlines()
    json_start = None
    for i, line in enumerate(stderr_lines):
        if line.strip().startswith("{"):
            json_start = i
            break

    if json_start is not None:
        json_block = "\n".join(stderr_lines[json_start:])
        try:
            stats = json.loads(json_block)
        except json.JSONDecodeError:
            stats = None
    else:
        stats = None

    # Sanitize measured values — ffmpeg's loudnorm chokes on -inf
    def _safe_float(val: Any, default: float) -> float:
        """Convert to float, returning default if None, -inf, or nan."""
        try:
            f = float(val)
            if math.isinf(f) or math.isnan(f):
                return default
            return f
        except (TypeError, ValueError):
            return default

    # Pass 2: apply normalization
    if stats:
        measured_i = _safe_float(stats.get("input_i"), -24)
        measured_lra = _safe_float(stats.get("input_lra"), 7)
        measured_tp = _safe_float(stats.get("input_tp"), -1)
        measured_thresh = _safe_float(stats.get("input_thresh"), -34)
        loudnorm_filter = (
            f"loudnorm=I={target_lufs}:TP={true_peak}:LRA=11"
            f":measured_I={measured_i}"
            f":measured_LRA={measured_lra}"
            f":measured_TP={measured_tp}"
            f":measured_thresh={measured_thresh}"
            ":linear=true"
        )
    else:
        # Fallback: single-pass normalization
        console.print("[yellow]Could not measure loudness — using single-pass[/yellow]")
        loudnorm_filter = f"loudnorm=I={target_lufs}:TP={true_peak}:LRA=11"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-af",
        loudnorm_filter,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    console.print(f"[green]Audio normalized → {output_path}[/green]")
    return output_path


def add_ducking(
    video_path: Path,
    music_path: Path,
    output_path: Path,
    duck_db: float = -12.0,
    release: float = 0.5,
) -> Path:
    """Mix background music under dialogue with sidechain ducking.

    The voice track from *video_path* drives a compressor that ducks
    *music_path* when speech is detected.

    Args:
        video_path: Video file containing dialogue audio.
        music_path: Background music file.
        output_path: Destination file with ducked mix.
        duck_db: Volume reduction in dB when ducking activates.
        release: Compressor release time in seconds.

    Returns:
        Path to the output file with ducked audio.

    Raises:
        FileNotFoundError: If either input file is missing.
        RuntimeError: If ffmpeg is missing or the video has no audio.
    """
    video_path = Path(video_path)
    music_path = Path(music_path)
    output_path = Path(output_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if not music_path.exists():
        raise FileNotFoundError(f"Music file not found: {music_path}")

    _require_ffmpeg()

    if not has_audio(video_path):
        console.print("[yellow]No audio in video — skipping ducking[/yellow]")
        shutil.copy2(video_path, output_path)
        return output_path

    console.print(f"[cyan]Adding ducked music ({duck_db} dB, release {release}s)[/cyan]")

    # Convert release from seconds to milliseconds for ffmpeg
    release_ms = int(release * 1000)

    # volume=0.3 sets baseline music volume; sidechaincompress ducks further
    # when dialogue is detected on the voice channel
    filter_complex = (
        f"[1:a]volume=0.3[music];"
        f"[0:a][music]sidechaincompress="
        f"threshold=0.3:ratio=20:release={release_ms}:makeup=6[out]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(music_path),
        "-filter_complex",
        filter_complex,
        "-map",
        "0:v",
        "-map",
        "[out]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    console.print(f"[green]Ducked audio → {output_path}[/green]")
    return output_path
