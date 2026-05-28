"""GPU detection — probe for CUDA/NVENC and report acceleration capabilities."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field

from rich.console import Console

console = Console()


@dataclass
class GpuCapabilities:
    """What GPU acceleration is available on this machine."""

    cuda_available: bool = False
    cuda_device_count: int = 0
    cuda_device_name: str = ""
    nvenc_available: bool = False
    nvenc_encoder: str = ""
    gpu_enhanced: bool = False
    notes: list[str] = field(default_factory=list)


def detect_gpu() -> GpuCapabilities:
    """Probe the current machine for GPU acceleration capabilities.

    Checks for:
    - CUDA (torch) for ML acceleration (transcription, silence detection)
    - NVENC (ffmpeg) for hardware video encoding

    Returns:
        GpuCapabilities with all detection results filled.
    """
    caps = GpuCapabilities()

    # 1. Check CUDA via torch
    try:
        import torch
    except ImportError:
        caps.notes.append("PyTorch not installed — CUDA unavailable")
    except OSError as e:
        caps.notes.append(f"PyTorch found but broken (shared lib issue: {e})")
    else:
        caps.cuda_available = torch.cuda.is_available()
        if caps.cuda_available:
            caps.cuda_device_count = torch.cuda.device_count()
            caps.cuda_device_name = torch.cuda.get_device_name(0)
            caps.gpu_enhanced = True
            caps.notes.append(
                f"CUDA GPU: {caps.cuda_device_name} ({caps.cuda_device_count} device(s))"
            )
        else:
            caps.notes.append("PyTorch installed but no CUDA device detected")

    # 2. Check NVENC via ffmpeg
    if shutil.which("ffmpeg"):
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
        )
        if "h264_nvenc" in result.stdout:
            caps.nvenc_available = True
            caps.nvenc_encoder = "h264_nvenc"
            if not caps.gpu_enhanced:
                caps.gpu_enhanced = True
            caps.notes.append("NVENC hardware encoder available")
        elif "h264_amf" in result.stdout:
            caps.nvenc_available = True
            caps.nvenc_encoder = "h264_amf"
            caps.notes.append("AMD AMF hardware encoder available")
    else:
        caps.notes.append("ffmpeg not found — cannot check encoder support")

    return caps


def print_gpu_banner(caps: GpuCapabilities | None = None) -> None:
    """Print a startup banner showing GPU/mode status.

    Call this once at CLI startup to inform the user what acceleration
    is available.
    """
    if caps is None:
        caps = detect_gpu()

    if caps.gpu_enhanced:
        details = " | ".join(caps.notes)
        console.print(f"[bold green]⚡ GPU Enhanced Mode[/bold green] — {details}")
    else:
        console.print(
            "[dim]💻 CPU Mode — "
            "no GPU detected. "
            "Transcription and encoding will use CPU paths.[/dim]"
        )

    # Detailed breakdown visible with context from other modules
    if caps.cuda_available:
        console.print(f"  [dim]ML acceleration: {caps.cuda_device_name}[/dim]")
    if caps.nvenc_available:
        console.print(f"  [dim]Encode acceleration: {caps.nvenc_encoder}[/dim]")


def accelerated_features(caps: GpuCapabilities | None = None) -> list[dict]:
    """Return a list of clearcut features and whether they benefit from GPU.

    Each entry: {name, gpu_speedup, details, currently_using_gpu}
    """
    if caps is None:
        caps = detect_gpu()

    features = [
        {
            "name": "Transcription (captions)",
            "gpu_speedup": "~10-20x",
            "details": "WhisperX (GPU) → ~1-2min/video vs faster-whisper (CPU) → ~15min/video",
            "gpu_enabled": caps.cuda_available,
        },
        {
            "name": "Silence removal (VAD)",
            "gpu_speedup": "~3x",
            "details": "Silero-VAD benefits from CUDA tensor operations",
            "gpu_enabled": caps.cuda_available,
        },
        {
            "name": "Video encoding",
            "gpu_speedup": "~4-8x",
            "details": "NVENC/AMF/QSV vs software x264 at same quality",
            "gpu_enabled": caps.nvenc_available,
        },
    ]

    # Mark which ones are actually GPU-accelerated right now
    for feat in features:
        feat["active"] = feat["gpu_enabled"]
    return features


def print_accelerated_features(caps: GpuCapabilities | None = None) -> None:
    """Pretty-print which features get GPU speedup."""
    if caps is None:
        caps = detect_gpu()

    features = accelerated_features(caps)
    console.print("\n[bold]Acceleration overview:[/bold]")

    for feat in features:
        icon = "[green]✓[/green]" if feat["gpu_enabled"] else "[yellow]–[/yellow]"
        status = "[green]GPU[/green]" if feat["gpu_enabled"] else "[yellow]CPU[/yellow]"
        console.print(
            f"  {icon} [bold]{feat['name']}[/bold] — {status} "
            f"({feat['gpu_speedup']} speedup when GPU available)"
        )

    # Summary
    if caps.gpu_enhanced:
        gpu_count = sum(1 for f in features if f["gpu_enabled"])
        console.print(f"\n[dim]{gpu_count}/{len(features)} features GPU-accelerated[/dim]")
    else:
        console.print(
            "\n[dim]Install PyTorch with CUDA or connect a GPU machine "
            "to enable acceleration.[/dim]"
        )
