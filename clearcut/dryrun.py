"""Dry-run validation — check inputs and describe pipeline stages without executing."""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from clearcut.models import PipelineConfig

console = Console()


def validate_inputs(config: PipelineConfig) -> list[str]:
    """Check all input files exist and ffmpeg is available. Return list of errors."""
    errors = []
    if not config.main.exists():
        errors.append(f"Main video not found: {config.main}")
    for c in config.context:
        if not Path(c).exists():
            errors.append(f"Context clip not found: {c}")
    for img in config.images:
        if not Path(img).exists():
            errors.append(f"Image not found: {img}")
    if config.lut is not None and not config.lut.exists():
        errors.append(f"LUT file not found: {config.lut}")
    if config.watermark_path is not None and not config.watermark_path.exists():
        errors.append(f"Watermark not found: {config.watermark_path}")
    if config.intro_path is not None and not config.intro_path.exists():
        errors.append(f"Intro video not found: {config.intro_path}")
    if config.outro_path is not None and not config.outro_path.exists():
        errors.append(f"Outro video not found: {config.outro_path}")
    if not shutil.which("ffmpeg"):
        errors.append("ffmpeg not found on PATH")
    return errors


def describe_stages(config: PipelineConfig) -> None:
    """Print what stages would run and their configuration."""
    stages: list[tuple[str, str]] = []

    def _add(name: str, details: str) -> None:
        stages.append((name, details))

    _add("Input", str(config.main))
    _add("Output", str(config.output.resolve()))

    if config.remove_silence:
        _add("Stage 1: Silence removal", f"method={config.silence_method}")
    if config.detect_scenes:
        _add("Stage 1b: Scene detection", f"max_clip={config.max_clip_duration}s")
    if config.normalize_audio:
        _add("Stage 2: Audio normalization", f"target={config.audio_target_lufs} LUFS")
    if config.duck_music or config.background_music:
        _add("Stage 2b: Music ducking", f"music={config.duck_music or config.background_music}")
    if config.context or config.images or config.assets or config.watermark_path:
        _add(
            "Stage 3: Compositing",
            f"context={len(config.context)} clips, "
            f"images={len(config.images)}, "
            f"assets={len(config.assets)}, "
            f"watermark={'yes' if config.watermark_path else 'no'}",
        )
    if config.lut:
        _add("Stage 4a: LUT", f"lut={config.lut}")
    has_correction = (
        abs(config.brightness) >= 0.001
        or abs(config.contrast - 1.0) >= 0.001
        or abs(config.saturation - 1.0) >= 0.001
    )
    if has_correction or config.color_preset:
        _add(
            "Stage 4b: Colour correction",
            f"bri={config.brightness:+.2f}, "
            f"con={config.contrast:.2f}, "
            f"sat={config.saturation:.2f}"
            + (f", preset={config.color_preset}" if config.color_preset else ""),
        )
    if config.format != "16:9":
        _add("Stage 5: Format conversion", f"{config.format} crop={config.smart_crop}")
    if config.generate_captions:
        _add(
            "Stage 6: Captions",
            f"style={config.style}, burn={'yes' if config.burn_captions else 'no'}",
        )
    if config.punch_zoom or config.hook_zoom:
        _add(
            "Stage 7: Effects",
            f"punch={config.punch_zoom}x, hook={'yes' if config.hook_zoom else 'no'}",
        )
    if config.speed_segments:
        _add("Stage 7b: Speed ramping", f"{len(config.speed_segments)} segments")
    _add("Stage 9: Final encode", f"preset={config.encoder_preset}, encoder={config.hardware}")

    # Summary panel
    console.print(
        Panel(
            f"[bold]Input:[/bold] {config.main}\n[bold]Output:[/bold] {config.output.resolve()}",
            title="ClearCut Dry Run",
        )
    )

    # Stages table
    table = Table(title="Pipeline Stages")
    table.add_column("Stage", style="cyan")
    table.add_column("Details", style="white")

    for stage_name, details in stages:
        table.add_row(stage_name, details)

    console.print(table)

    # Input validation
    errors = validate_inputs(config)
    console.print("\n[bold]Input Validation:[/bold]")
    issues: list[str] = []
    if not config.main.exists():
        issues.append(f"[red]✗[/red] Main video: {config.main}")
    else:
        issues.append(f"[green]✓[/green] Main video: {config.main}")
    issues.append(
        f"{'[green]✓[/green]' if shutil.which('ffmpeg') else '[red]✗[/red]'} ffmpeg available"
    )
    if config.context:
        for c in config.context:
            issues.append(f"{'[green]✓[/green]' if c.exists() else '[red]✗[/red]'} Context: {c}")
    for issue in issues:
        console.print(f"  {issue}")

    if errors:
        console.print("\n[red]Issues found:[/red]")
        for e in errors:
            console.print(f"  [red]✗[/red] {e}")
        console.print("[yellow]Fix issues before running the pipeline.[/yellow]")
    else:
        console.print("\n[green]All inputs valid.[/green]")
