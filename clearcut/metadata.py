"""Video metadata extraction and display using ffprobe."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VideoMetadata:
    """Extracted video metadata."""

    path: str
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    codec: str = ""
    pixel_format: str = ""
    audio_codec: str = ""
    audio_sample_rate: int = 0
    audio_channels: int = 0
    bitrate: str = ""
    has_video: bool = False
    has_audio: bool = False
    raw: dict[str, Any] = field(default_factory=dict)


def extract_metadata(path: Path) -> VideoMetadata:
    """Extract video metadata using ffprobe.

    Args:
        path: Path to the video file.

    Returns:
        VideoMetadata with all detected fields filled.
    """
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    data = json.loads(result.stdout)
    meta = VideoMetadata(path=str(path))

    for stream in data.get("streams", []):
        if stream["codec_type"] == "video" and not meta.has_video:
            meta.has_video = True
            meta.width = stream.get("width", 0)
            meta.height = stream.get("height", 0)
            meta.codec = stream.get("codec_name", "")
            meta.pixel_format = stream.get("pix_fmt", "")
            fps_str = stream.get("avg_frame_rate") or stream.get("r_frame_rate", "0/1")
            num_str, den_str = fps_str.split("/")
            num, den = float(num_str), float(den_str)
            meta.fps = num / den if den != 0 else 0.0
        elif stream["codec_type"] == "audio" and not meta.has_audio:
            meta.has_audio = True
            meta.audio_codec = stream.get("codec_name", "")
            srate = stream.get("sample_rate", "0")
            meta.audio_sample_rate = int(srate)
            meta.audio_channels = int(stream.get("channels", 0))

    fmt = data.get("format", {})
    duration_str = fmt.get("duration", "0")
    meta.duration = float(duration_str)
    meta.bitrate = fmt.get("bit_rate", "")

    meta.raw = data
    return meta


def format_metadata_line(meta: VideoMetadata) -> str:
    """Return a rich-formatted metadata display string."""
    lines = [
        f"  Duration: [cyan]{meta.duration:.1f}s[/cyan]",
    ]
    if meta.has_video:
        lines.append(
            f"  Video: [green]{meta.width}[/green]×[green]{meta.height}[/green] "
            f"@ [yellow]{meta.fps:.2f}fps[/yellow] "
            f"([dim]{meta.codec}/{meta.pixel_format}[/dim])"
        )
    else:
        lines.append("  Video: [yellow]none[/yellow]")
    if meta.has_audio:
        lines.append(
            f"  Audio: [green]{meta.audio_codec}[/green] @ "
            f"[yellow]{meta.audio_sample_rate}Hz[/yellow], "
            f"[cyan]{meta.audio_channels}ch[/cyan]"
        )
    else:
        lines.append("  Audio: [yellow]none[/yellow]")
    if meta.bitrate:
        lines.append(f"  Bitrate: [magenta]{int(meta.bitrate) // 1000}kbps[/magenta]")
    return "\n".join(lines)


def format_metadata_json(meta: VideoMetadata) -> str:
    """Return JSON metadata string."""
    return json.dumps(
        {
            "path": meta.path,
            "duration": meta.duration,
            "video": {
                "width": meta.width,
                "height": meta.height,
                "fps": meta.fps,
                "codec": meta.codec,
                "pixel_format": meta.pixel_format,
            }
            if meta.has_video
            else None,
            "audio": {
                "codec": meta.audio_codec,
                "sample_rate": meta.audio_sample_rate,
                "channels": meta.audio_channels,
            }
            if meta.has_audio
            else None,
            "bitrate_kbps": int(meta.bitrate) // 1000 if meta.bitrate else None,
        },
        indent=2,
    )


def print_metadata(meta: VideoMetadata) -> None:
    """Print metadata to console with Rich formatting."""
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(
        Panel(
            format_metadata_line(meta),
            title=f"📹 {meta.path}",
        )
    )
