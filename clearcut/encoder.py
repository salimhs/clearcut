"""Hardware-accelerated encoding via ffmpeg."""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

log = logging.getLogger(__name__)

console = Console()


@dataclass
class HWAccel:
    """Detected hardware acceleration capability."""

    name: str
    encoder: str
    device: str | None = None


def detect_hardware() -> HWAccel:
    """Probe ffmpeg for available hardware encoders.

    Priority: NVENC (NVIDIA) → AMF (AMD) → QSV (Intel) → software fallback.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found in PATH")

    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True, text=True,
    )
    encoder_list = result.stdout

    # Check in priority order
    hw_options = [
        ("nvenc", "h264_nvenc", None),
        ("amf", "h264_amf", None),
        ("qsv", "h264_qsv", None),
        ("vaapi", "h264_vaapi", "/dev/dri/renderD128"),
    ]

    for name, encoder, device in hw_options:
        if encoder in encoder_list:
            # Verify the encoder actually works with a quick probe
            test_cmd = [
                "ffmpeg", "-hide_banner",
                "-f", "lavfi", "-i", "nullsrc=s=64x64:d=0.1",
                "-c:v", encoder,
            ]
            if device:
                test_cmd = [
                    "ffmpeg", "-hide_banner",
                    "-init_hw_device", f"{name}={name}:{device}",
                    "-f", "lavfi", "-i", "nullsrc=s=64x64:d=0.1",
                    "-c:v", encoder,
                ]
            test_cmd += ["-f", "null", "-"]

            probe = subprocess.run(test_cmd, capture_output=True)
            if probe.returncode == 0:
                console.print(f"[green]Hardware encoder detected: {encoder}[/green]")
                return HWAccel(name=name, encoder=encoder, device=device)

    console.print("[yellow]No hardware encoder available, using libx264[/yellow]")
    return HWAccel(name="software", encoder="libx264")


def encode(
    input_path: Path,
    output_path: Path,
    preset: str = "fast",
    hardware: str = "auto",
    crf: int = 23,
    audio_codec: str = "aac",
    audio_bitrate: str = "192k",
) -> Path:
    """Encode video with hardware acceleration when available.

    Args:
        input_path: Source video file.
        output_path: Destination encoded file.
        preset: Encoding speed preset (ultrafast, fast, medium, slow).
        hardware: "auto" to detect, or force "nvenc", "amf", "qsv", "software".
        crf: Constant rate factor (lower = better quality, 18-28 typical).
        audio_codec: Audio codec (aac, libopus, copy).
        audio_bitrate: Audio bitrate string.

    Returns:
        Path to the encoded output file.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if hardware == "auto":
        hw = detect_hardware()
    else:
        encoder_map = {
            "nvenc": "h264_nvenc",
            "amf": "h264_amf",
            "qsv": "h264_qsv",
            "vaapi": "h264_vaapi",
            "software": "libx264",
        }
        encoder = encoder_map.get(hardware, "libx264")
        hw = HWAccel(name=hardware, encoder=encoder)

    console.print(
        f"[cyan]Encoding {input_path.name} → {output_path.name} "
        f"({hw.encoder}, preset={preset})[/cyan]"
    )

    cmd = ["ffmpeg", "-y", "-i", str(input_path)]

    # Hardware-specific input flags
    if hw.device and hw.name == "vaapi":
        cmd = [
            "ffmpeg", "-y",
            "-init_hw_device", f"vaapi=vaapi:{hw.device}",
            "-hwaccel", "vaapi",
            "-hwaccel_output_format", "vaapi",
            "-i", str(input_path),
        ]

    # Video encoder settings
    cmd += ["-c:v", hw.encoder]

    if hw.name == "software":
        cmd += ["-preset", preset, "-crf", str(crf)]
    elif hw.name == "nvenc":
        nvenc_presets = {
            "ultrafast": "p1",
            "fast": "p4",
            "medium": "p5",
            "slow": "p7",
        }
        cmd += [
            "-preset", nvenc_presets.get(preset, "p4"),
            "-rc", "constqp",
            "-qp", str(crf),
        ]
    elif hw.name == "qsv":
        cmd += ["-preset", preset, "-global_quality", str(crf)]
    elif hw.name == "amf":
        cmd += ["-quality", preset, "-rc", "cqp", "-qp_i", str(crf), "-qp_p", str(crf)]

    # Audio
    cmd += ["-c:a", audio_codec]
    if audio_codec != "copy":
        cmd += ["-b:a", audio_bitrate]

    # Output optimization
    cmd += ["-movflags", "+faststart", str(output_path)]

    subprocess.run(cmd, check=True)
    console.print(f"[green]Encoded → {output_path}[/green]")
    return output_path
