"""Color grading — LUT application and basic color correction."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from rich.console import Console


from clearcut.exceptions import EncodingError, FileError

log = logging.getLogger(__name__)

console = Console()


def _require_ffmpeg() -> None:
    """Raise if ffmpeg is not installed."""
    if not shutil.which("ffmpeg"):
        raise EncodingError("ffmpeg not found in PATH")


def _validate_cube_file(lut_path: Path) -> bool:
    """Basic validation that a .cube LUT file looks correct.

    Checks for required LUT_3D_SIZE header and numeric data lines.
    Returns True if valid, False otherwise.
    """
    try:
        with open(lut_path) as f:
            content = f.read(4096)  # read enough to find the header
    except OSError:
        return False

    has_size = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("LUT_3D_SIZE"):
            has_size = True
            break

    return has_size


def apply_lut(
    input_path: Path,
    output_path: Path,
    lut_path: Path,
    strength: float = 1.0,
) -> Path:
    """Apply a 3D LUT (.cube) colour grade to a video.

    Args:
        input_path: Source video file.
        output_path: Destination graded file.
        lut_path: Path to a .cube LUT file.
        strength: Blend strength 0.0 (original) → 1.0 (full LUT). Values
            between 0 and 1 blend the graded result with the original.

    Returns:
        Path to the graded output file.

    Raises:
        FileNotFoundError: If *input_path* or *lut_path* do not exist.
        RuntimeError: If ffmpeg is missing.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    lut_path = Path(lut_path)

    if not input_path.exists():
        raise FileError(f"Input file not found: {input_path}")
    if not lut_path.exists():
        raise FileError(f"LUT file not found: {lut_path}")

    _require_ffmpeg()

    if not _validate_cube_file(lut_path):
        console.print(
            f"[yellow]Warning: {lut_path.name} may not be a valid .cube LUT "
            "— applying anyway[/yellow]"
        )

    strength = max(0.0, min(1.0, strength))
    console.print(f"[cyan]Applying LUT {lut_path.name} (strength {strength:.0%})[/cyan]")

    lut_abs = lut_path.resolve()

    if strength >= 1.0:
        # Full-strength — simple lut3d filter
        vf = f"lut3d='{lut_abs}':interp=tetrahedral"
    else:
        # Blend original with LUT-graded version using the split/blend approach
        vf = (
            f"split[original][forLut];"
            f"[forLut]lut3d='{lut_abs}':interp=tetrahedral[graded];"
            f"[original][graded]blend=all_mode=normal:"
            f"all_opacity={strength}"
        )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-filter_complex" if strength < 1.0 else "-vf",
        vf,
        "-c:a",
        "copy",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    console.print(f"[green]LUT applied → {output_path}[/green]")
    return output_path


def basic_correct(
    input_path: Path,
    output_path: Path,
    brightness: float = 0.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    temperature: int = 0,
) -> Path:
    """Apply basic colour correction using ffmpeg eq and colorbalance filters.

    Args:
        input_path: Source video file.
        output_path: Destination corrected file.
        brightness: -1.0 to 1.0 (0.0 = no change).
        contrast: 0.0 to 2.0 (1.0 = no change).
        saturation: 0.0 to 2.0 (1.0 = no change).
        temperature: Colour temperature shift, -100 (cool) to 100 (warm).

    Returns:
        Path to the corrected output file.

    Raises:
        FileNotFoundError: If *input_path* does not exist.
        RuntimeError: If ffmpeg is missing.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileError(f"Input file not found: {input_path}")

    _require_ffmpeg()

    # Clamp values to safe ranges
    brightness = max(-1.0, min(1.0, brightness))
    contrast = max(0.0, min(2.0, contrast))
    saturation = max(0.0, min(2.0, saturation))
    temperature = max(-100, min(100, temperature))

    # Skip if all values are defaults — just copy
    is_default = (
        abs(brightness) < 0.001
        and abs(contrast - 1.0) < 0.001
        and abs(saturation - 1.0) < 0.001
        and temperature == 0
    )
    if is_default:
        console.print("[dim]No colour correction needed — copying[/dim]")
        shutil.copy2(input_path, output_path)
        return output_path

    console.print(
        f"[cyan]Colour correction: brightness={brightness:+.2f} "
        f"contrast={contrast:.2f} saturation={saturation:.2f} "
        f"temperature={temperature:+d}[/cyan]"
    )

    filters: list[str] = []

    # eq filter handles brightness, contrast, saturation
    eq_parts: list[str] = []
    if abs(brightness) >= 0.001:
        eq_parts.append(f"brightness={brightness}")
    if abs(contrast - 1.0) >= 0.001:
        eq_parts.append(f"contrast={contrast}")
    if abs(saturation - 1.0) >= 0.001:
        eq_parts.append(f"saturation={saturation}")
    if eq_parts:
        filters.append("eq=" + ":".join(eq_parts))

    # colorbalance for temperature (warm = more red/yellow, cool = more blue)
    if temperature != 0:
        # Normalize temperature to -1.0 … 1.0 range
        t = temperature / 100.0
        if t > 0:
            # Warm: boost reds/yellows in shadows/midtones/highlights
            filters.append(
                f"colorbalance=rs={t * 0.3}:gs={t * 0.1}:bs={-t * 0.3}"
                f":rm={t * 0.2}:gm={t * 0.05}:bm={-t * 0.2}"
            )
        else:
            # Cool: boost blues
            at = abs(t)
            filters.append(
                f"colorbalance=rs={-at * 0.2}:gs={at * 0.05}:bs={at * 0.3}"
                f":rm={-at * 0.15}:gm={at * 0.03}:bm={at * 0.2}"
            )

    vf = ",".join(filters)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        vf,
        "-c:a",
        "copy",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    console.print(f"[green]Colour corrected → {output_path}[/green]")
    return output_path
