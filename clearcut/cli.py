"""clearcut CLI — Typer-based command interface."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console


from clearcut import __version__

log = logging.getLogger(__name__)

app = typer.Typer(
    name="clearcut",
    help="Raw footage to publish-ready video. One command.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"clearcut {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="Enable verbose/debug logging"),
    ] = False,
) -> None:
    """clearcut — automated video editing pipeline."""
    from clearcut.logging import setup_logging

    setup_logging(verbose=verbose)

    # Print GPU banner on startup
    from clearcut.gpu import print_gpu_banner

    print_gpu_banner()


@app.command()
def process(
    main: Annotated[Path, typer.Option("--main", "-m", help="Main video file")],
    intro: Annotated[
        Optional[Path],
        typer.Option("--intro", help="Intro video clip to prepend"),
    ] = None,
    outro: Annotated[
        Optional[Path],
        typer.Option("--outro", help="Outro video clip to append"),
    ] = None,
    intro_only: Annotated[
        bool,
        typer.Option("--intro-only", help="Only inject intro (skip outro)"),
    ] = False,
    outro_only: Annotated[
        bool,
        typer.Option("--outro-only", help="Only append outro (skip intro)"),
    ] = False,
    context: Annotated[
        Optional[list[Path]],
        typer.Option("--context", "-c", help="Context/B-roll video files"),
    ] = None,
    images: Annotated[
        Optional[list[Path]],
        typer.Option("--images", "-i", help="Static image overlays"),
    ] = None,
    assets: Annotated[
        Optional[list[str]],
        typer.Option("--assets", "-a", help="Timestamped assets (path@seconds)"),
    ] = None,
    style: Annotated[
        str,
        typer.Option("--style", "-s", help="Caption style preset"),
    ] = "default",
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file path"),
    ] = Path("output.mp4"),
    no_silence: Annotated[
        bool,
        typer.Option("--no-silence", help="Skip silence removal"),
    ] = False,
    silence_method: Annotated[
        str,
        typer.Option("--silence-method", help="vad or auto-editor"),
    ] = "vad",
    captions: Annotated[
        bool,
        typer.Option("--captions", help="Generate captions"),
    ] = False,
    burn: Annotated[
        bool,
        typer.Option("--burn", help="Burn captions into video"),
    ] = False,
    preset: Annotated[
        str,
        typer.Option("--preset", help="Encoder preset (ultrafast/fast/medium/slow)"),
    ] = "fast",
    hardware: Annotated[
        str,
        typer.Option("--hardware", help="Hardware encoder (auto/nvenc/amf/qsv/software)"),
    ] = "auto",
    # --- Audio ---
    normalize: Annotated[
        bool,
        typer.Option("--normalize/--no-normalize", help="Normalize audio loudness"),
    ] = True,
    audio_target: Annotated[
        float,
        typer.Option("--audio-target", help="Target loudness in LUFS"),
    ] = -14.0,
    duck_music: Annotated[
        Optional[Path],
        typer.Option("--duck-music", help="Background music file for ducking"),
    ] = None,
    background_music: Annotated[
        Optional[Path],
        typer.Option("--background-music", help="Auto-ducked background music file"),
    ] = None,
    music_volume: Annotated[
        float,
        typer.Option("--music-volume", help="Background music volume (0.0-1.0)"),
    ] = 0.3,
    # --- Colour grading ---
    lut: Annotated[
        Optional[Path],
        typer.Option("--lut", help="Path to .cube LUT file"),
    ] = None,
    brightness: Annotated[
        float,
        typer.Option("--brightness", help="Brightness adjustment (-1.0 to 1.0)"),
    ] = 0.0,
    contrast: Annotated[
        float,
        typer.Option("--contrast", help="Contrast adjustment (0.0 to 2.0)"),
    ] = 1.0,
    saturation: Annotated[
        float,
        typer.Option("--saturation", help="Saturation adjustment (0.0 to 2.0)"),
    ] = 1.0,
    # --- Format ---
    format: Annotated[
        str,
        typer.Option("--format", help="Output format: 16:9, 9:16, 1:1"),
    ] = "16:9",
    smart_crop: Annotated[
        str,
        typer.Option("--smart-crop", help="Crop mode: center (default) or face"),
    ] = "center",
    smart_crop_smooth: Annotated[
        int,
        typer.Option("--smart-crop-smooth", help="Smoothing window for face tracking"),
    ] = 5,
    # --- Transitions ---
    transition: Annotated[
        str,
        typer.Option(
            "--transition",
            help="Transition type (fade/wipeleft/wiperight/slideleft/slideright/dissolve/radial)",
        ),
    ] = "fade",
    transition_duration: Annotated[
        float,
        typer.Option("--transition-duration", help="Transition duration in seconds"),
    ] = 0.3,
    # --- Effects ---
    punch_zoom: Annotated[
        float,
        typer.Option("--punch-zoom", help="Punch zoom factor (0=off, 1.05=5%, 1.15=15%)"),
    ] = 0.0,
    hook_zoom: Annotated[
        bool,
        typer.Option("--hook-zoom/--no-hook-zoom", help="Quick zoom on first 2 seconds"),
    ] = False,
    speed_segments: Annotated[
        Optional[str],
        typer.Option(
            "--speed-segments",
            help="Speed ramp segments (comma-separated, e.g. '0-10:2.0,10-20:0.5')",
        ),
    ] = None,
    # --- Watermark ---
    watermark: Annotated[
        Optional[Path],
        typer.Option("--watermark", help="Path to watermark/logo image"),
    ] = None,
    watermark_position: Annotated[
        str,
        typer.Option(
            "--watermark-position",
            help="Watermark position (bottom-right/bottom-left/top-right/top-left)",
        ),
    ] = "bottom-right",
    watermark_scale: Annotated[
        float,
        typer.Option("--watermark-scale", help="Watermark scale (fraction of frame width)"),
    ] = 0.15,
    watermark_opacity: Annotated[
        float,
        typer.Option("--watermark-opacity", help="Watermark opacity (0.0-1.0)"),
    ] = 0.7,
    # --- Scene detection ---
    detect_scenes: Annotated[
        bool,
        typer.Option("--detect-scenes", help="Detect and split at scene boundaries"),
    ] = False,
    max_clip_duration: Annotated[
        float,
        typer.Option("--max-clip-duration", help="Max segment duration (seconds, 0=off)"),
    ] = 0.0,
    # --- Colour preset ---
    color_preset: Annotated[
        Optional[str],
        typer.Option("--color-preset", help="Colour preset (warm/cool/vintage/vibrant/drama)"),
    ] = None,
    # --- Template ---
    template: Annotated[
        Optional[str],
        typer.Option("--template", help="Template preset (clean/tiktok/cinematic/bold)"),
    ] = None,
    # --- Config file ---
    config: Annotated[
        Optional[Path],
        typer.Option("--config", help="YAML config file (CLI args override config values)"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Validate inputs and show pipeline stages without executing"
        ),
    ] = False,
) -> None:
    """Process raw footage into a publish-ready video."""
    from clearcut.models import AssetPosition, PipelineConfig
    from clearcut.pipeline import Pipeline

    # Load YAML config if provided, then let CLI args override
    file_defaults: dict = {}
    if config is not None:
        import yaml

        file_defaults = yaml.safe_load(config.read_text()) or {}

    def _parse_speed_segments(raw: str | list[str] | None) -> list[str]:
        """Parse speed segments from comma-separated string or list."""
        if raw is None:
            return []
        if isinstance(raw, str):
            if not raw.strip():
                return []
            return [s.strip() for s in raw.split(",") if s.strip()]
        if isinstance(raw, list):
            return raw
        return []

    def _pick(cli_val: object, key: str, cli_default: object) -> object:
        """Return CLI value if explicitly set, else fall back to config file."""
        if cli_val != cli_default:
            return cli_val
        return file_defaults.get(key, cli_default)

    parsed_assets = []
    raw_assets = _pick(assets, "assets", None)
    if raw_assets:
        for raw in raw_assets:
            if isinstance(raw, str):
                parsed_assets.append(AssetPosition.parse(raw))
            elif isinstance(raw, dict):
                parsed_assets.append(AssetPosition(path=Path(raw["path"]), seconds=raw["seconds"]))

    config_obj = PipelineConfig(
        main=Path(_pick(main, "main", main)),  # type: ignore[arg-type]
        intro_path=_pick(intro, "intro", None),  # type: ignore[arg-type]
        outro_path=_pick(outro, "outro", None),  # type: ignore[arg-type]
        intro_only=_pick(intro_only, "intro_only", False),  # type: ignore[arg-type]
        outro_only=_pick(outro_only, "outro_only", False),  # type: ignore[arg-type]
        context=[Path(p) for p in _pick(context, "context", None) or []],
        images=[Path(p) for p in _pick(images, "images", None) or []],
        assets=parsed_assets,
        style=_pick(style, "style", "default"),  # type: ignore[arg-type]
        output=Path(_pick(output, "output", Path("output.mp4"))),
        remove_silence=not _pick(no_silence, "no_silence", False),
        silence_method=_pick(silence_method, "silence_method", "vad"),  # type: ignore[arg-type]
        generate_captions=_pick(captions, "captions", False),  # type: ignore[arg-type]
        burn_captions=_pick(burn, "burn", False),  # type: ignore[arg-type]
        encoder_preset=_pick(preset, "preset", "fast"),  # type: ignore[arg-type]
        hardware=_pick(hardware, "hardware", "auto"),  # type: ignore[arg-type]
        normalize_audio=_pick(normalize, "normalize", True),  # type: ignore[arg-type]
        audio_target_lufs=_pick(audio_target, "audio_target", -14.0),  # type: ignore[arg-type]
        duck_music=_pick(duck_music, "duck_music", None),  # type: ignore[arg-type]
        lut=_pick(lut, "lut", None),  # type: ignore[arg-type]
        brightness=_pick(brightness, "brightness", 0.0),  # type: ignore[arg-type]
        contrast=_pick(contrast, "contrast", 1.0),  # type: ignore[arg-type]
        saturation=_pick(saturation, "saturation", 1.0),  # type: ignore[arg-type]
        format=_pick(format, "format", "16:9"),  # type: ignore[arg-type]
        smart_crop=_pick(smart_crop, "smart_crop", "center"),  # type: ignore[arg-type]
        smart_crop_smooth=_pick(smart_crop_smooth, "smart_crop_smooth", 5),  # type: ignore[arg-type]
        transition=_pick(transition, "transition", "fade"),  # type: ignore[arg-type]
        transition_duration=_pick(transition_duration, "transition_duration", 0.3),  # type: ignore[arg-type]
        punch_zoom=_pick(punch_zoom, "punch_zoom", 0.0),  # type: ignore[arg-type]
        hook_zoom=_pick(hook_zoom, "hook_zoom", False),  # type: ignore[arg-type]
        speed_segments=_parse_speed_segments(_pick(speed_segments, "speed_segments", None)),
        detect_scenes=_pick(detect_scenes, "detect_scenes", False),  # type: ignore[arg-type]
        max_clip_duration=_pick(max_clip_duration, "max_clip_duration", 0.0),  # type: ignore[arg-type]
        color_preset=_pick(color_preset, "color_preset", None),  # type: ignore[arg-type]
        template=_pick(template, "template", None),  # type: ignore[arg-type]
        watermark_path=_pick(watermark, "watermark", None),  # type: ignore[arg-type]
        watermark_position=_pick(watermark_position, "watermark_position", "bottom-right"),  # type: ignore[arg-type]
        watermark_scale=_pick(watermark_scale, "watermark_scale", 0.15),  # type: ignore[arg-type]
        watermark_opacity=_pick(watermark_opacity, "watermark_opacity", 0.7),  # type: ignore[arg-type]
        background_music=_pick(background_music, "background_music", None),  # type: ignore[arg-type]
        music_volume=_pick(music_volume, "music_volume", 0.3),  # type: ignore[arg-type]
    )

    # Dry-run mode
    if dry_run:
        from clearcut.dryrun import describe_stages, validate_inputs

        errors = validate_inputs(config_obj)
        describe_stages(config_obj)
        if errors:
            console.print("\n[red]Issues found — fix before running:[/red]")
            for e in errors:
                console.print(f"  [red]✗[/red] {e}")
        return

    pipeline = Pipeline(config_obj)
    try:
        pipeline.run()
    finally:
        pipeline.clean()


@app.command()
def transcribe(
    input: Annotated[Path, typer.Option("--input", "-i", help="Video/audio file")],
    style: Annotated[str, typer.Option("--style", "-s")] = "default",
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output ASS file path"),
    ] = None,
) -> None:
    """Generate captions for a video file."""
    from clearcut.captions import CaptionGenerator
    from clearcut.styles import get_style

    if not input.exists():
        console.print(f"[red]File not found: {input}[/red]")
        raise typer.Exit(1)

    caption_style = get_style(style)
    gen = CaptionGenerator(style=caption_style)
    words = gen.transcribe(input)
    ass_content = gen.generate_ass(words)

    out_path = output or input.with_suffix(".ass")
    out_path.write_text(ass_content)
    console.print(f"[green]Captions saved to {out_path}[/green]")


@app.command()
def trim(
    input: Annotated[Path, typer.Option("--input", "-i", help="Video file to trim")],
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output file path"),
    ] = None,
    method: Annotated[
        str,
        typer.Option("--method", help="vad or auto-editor"),
    ] = "vad",
    threshold: Annotated[
        float,
        typer.Option("--threshold", help="VAD threshold (0.0-1.0)"),
    ] = 0.5,
) -> None:
    """Remove silence from a video file."""
    from clearcut.silence import remove_silence

    if not input.exists():
        console.print(f"[red]File not found: {input}[/red]")
        raise typer.Exit(1)

    out_path = output or input.with_stem(input.stem + "_trimmed")
    remove_silence(input, out_path, method=method, threshold=threshold)
    console.print(f"[green]Trimmed video saved to {out_path}[/green]")


@app.command()
def templates() -> None:
    """List available pipeline templates."""
    from clearcut.styles import TEMPLATES

    for name, tpl in TEMPLATES.items():
        console.print(
            f"  [bold]{name}[/bold] — "
            f"format={tpl.format}, transition={tpl.transition}, "
            f"lufs={tpl.audio_target_lufs}, "
            f"sat={tpl.saturation}, con={tpl.contrast}, bri={tpl.brightness:+.2f}"
        )


@app.command()
def repurpose(
    input: Annotated[Path, typer.Option("--input", "-i", help="Input video file")],
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output directory for clips"),
    ] = None,
    num_clips: Annotated[
        int,
        typer.Option("--num-clips", "-n", help="Number of clips to generate"),
    ] = 5,
    min_duration: Annotated[
        float,
        typer.Option("--min-duration", help="Minimum clip duration in seconds"),
    ] = 20.0,
    max_duration: Annotated[
        float,
        typer.Option("--max-duration", help="Maximum clip duration in seconds"),
    ] = 90.0,
    no_process: Annotated[
        bool,
        typer.Option("--no-process", help="Skip pipeline processing (extract only)"),
    ] = False,
    template: Annotated[
        Optional[str],
        typer.Option("--template", help="Template to apply to each clip"),
    ] = "tiktok",
    model: Annotated[
        str,
        typer.Option("--model", help="Claude model (sonnet/opus/haiku)"),
    ] = "sonnet",
    llm_provider: Annotated[
        str,
        typer.Option("--llm-provider", help="LLM provider (claude)"),
    ] = "claude",
    captions: Annotated[bool, typer.Option("--captions")] = True,
    burn: Annotated[bool, typer.Option("--burn")] = True,
    style: Annotated[str, typer.Option("--style")] = "default",
) -> None:
    """Analyze a video and repurpose it into short-form clips.

    Uses AI (Claude) to find the most engaging segments, extracts them,
    and optionally runs each through the full editing pipeline.
    """
    from clearcut.repurpose import repurpose as repurpose_fn

    output_dir = output or Path("output_clips")

    kwargs: dict = dict(
        template=template,
        generate_captions=captions,
        burn_captions=burn,
        style=style,
        llm_provider=llm_provider,
    )
    if template is None:
        kwargs.pop("template", None)

    repurpose_fn(
        input_path=input,
        output_dir=output_dir,
        num_clips=num_clips,
        min_duration=min_duration,
        max_duration=max_duration,
        process=not no_process,
        **kwargs,
    )


@app.command()
def remote(
    input: Annotated[
        Path, typer.Option("--input", "-i", help="Input video file to process on remote GPU")
    ],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output file path")],
    host: Annotated[
        str,
        typer.Option("--host", help="Remote GPU machine Tailscale IP or hostname"),
    ] = "100.97.187.60",
    user: Annotated[
        Optional[str],
        typer.Option("--user", "-u", help="SSH username for remote machine"),
    ] = None,
    captions: Annotated[
        bool, typer.Option("--captions", help="Generate captions (requires GPU)")
    ] = False,
    template: Annotated[
        Optional[str],
        typer.Option("--template", help="Template preset (clean/tiktok/cinematic/bold)"),
    ] = None,
    format: Annotated[
        str,
        typer.Option("--format", help="Output format: 16:9, 9:16, 1:1"),
    ] = "16:9",
    no_silence: Annotated[
        bool,
        typer.Option("--no-silence", help="Skip silence removal"),
    ] = False,
) -> None:
    """Run pipeline on a remote GPU machine via Tailscale.

    Transfers your video to the remote machine, processes it with
    full CUDA/NVENC acceleration, and returns the result.

    No files are left on the remote machine — temporary directory
    is cleaned up automatically.
    """
    from clearcut.remote import RemoteGpuConfig, remote_pipeline

    config = RemoteGpuConfig(host=host, user=user)

    remote_pipeline(
        config=config,
        input_path=input,
        output_path=output,
        remove_silence=not no_silence,
        generate_captions=captions,
        template=template,
        format=format,
    )


@app.command()
def merge(
    input: Annotated[
        Optional[list[Path]],
        typer.Option("--input", "-i", help="Input video clips to merge"),
    ] = None,
    from_dir: Annotated[
        Optional[Path],
        typer.Option("--from-dir", help="Directory containing clips to merge"),
    ] = None,
    pattern: Annotated[
        str,
        typer.Option("--pattern", help="Glob pattern when using --from-dir"),
    ] = "*.mp4",
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file path"),
    ] = Path("merged.mp4"),
    transition: Annotated[
        str,
        typer.Option("--transition", help="Transition type between clips"),
    ] = "fade",
    transition_duration: Annotated[
        float,
        typer.Option("--transition-duration", help="Transition duration in seconds"),
    ] = 0.5,
    hardware: Annotated[
        str,
        typer.Option("--hardware", help="Hardware encoder (auto/nvenc/amf/qsv/software)"),
    ] = "auto",
) -> None:
    """Merge multiple video clips into a single video with transitions."""
    from clearcut.merger import collect_clips_from_dir, merge_clips

    clips: list[Path] = []

    if input:
        clips.extend(input)
    if from_dir:
        clips.extend(collect_clips_from_dir(from_dir, pattern))

    if not clips:
        console.print("[red]No input clips provided. Use --input or --from-dir[/red]")
        raise typer.Exit(1)

    merge_clips(
        clips=clips,
        output_path=output,
        transition=transition,
        transition_duration=transition_duration,
        hardware=hardware,
    )


@app.command()
def batch(
    dir: Annotated[
        Path,
        typer.Option("--dir", help="Input directory containing video files"),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory"),
    ],
    pattern: Annotated[
        str,
        typer.Option("--pattern", help="Glob pattern to filter files"),
    ] = "*.mp4",
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview files without processing"),
    ] = False,
    max_workers: Annotated[
        int,
        typer.Option("--max-workers", help="Number of parallel workers"),
    ] = 2,
    template: Annotated[
        Optional[str],
        typer.Option("--template", help="Template preset (clean/tiktok/cinematic/bold)"),
    ] = None,
    style: Annotated[
        str,
        typer.Option("--style", "-s", help="Caption style preset"),
    ] = "default",
    format: Annotated[
        str,
        typer.Option("--format", help="Output format: 16:9, 9:16, 1:1"),
    ] = "16:9",
    hardware: Annotated[
        str,
        typer.Option("--hardware", help="Hardware encoder (auto/nvenc/amf/qsv/software)"),
    ] = "auto",
    silence_method: Annotated[
        str,
        typer.Option("--silence-method", help="vad or auto-editor"),
    ] = "vad",
    preset: Annotated[
        str,
        typer.Option("--preset", help="Encoder preset (ultrafast/fast/medium/slow)"),
    ] = "fast",
) -> None:
    """Batch process all videos in a directory."""
    from clearcut.batch import run_batch
    from clearcut.models import BatchConfig

    config = BatchConfig(
        input_dir=dir,
        output_dir=output,
        pattern=pattern,
        dry_run=dry_run,
        max_workers=max_workers,
        template=template,
        style=style,
        format=format,
        hardware=hardware,
        silence_method=silence_method,
        encoder_preset=preset,
    )
    run_batch(config)


@app.command()
def info() -> None:
    """Show system information and GPU acceleration status."""
    from clearcut.gpu import detect_gpu, print_accelerated_features, print_gpu_banner

    caps = detect_gpu()
    print_gpu_banner(caps)
    print_accelerated_features(caps)

    # Also show ffmpeg availability
    import shutil

    if shutil.which("ffmpeg"):
        console.print("[green]✓[/green] ffmpeg installed")
    else:
        console.print("[red]✗[/red] ffmpeg not found — clearcut requires ffmpeg")

    if shutil.which("ffprobe"):
        console.print("[green]✓[/green] ffprobe installed")


@app.command()
def metadata(
    input: Annotated[Path, typer.Option("--input", "-i", help="Video file to analyze")],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Output metadata as JSON"),
    ] = False,
) -> None:
    """Show metadata for a video file using ffprobe."""
    from clearcut.metadata import (
        extract_metadata,
        format_metadata_json,
        print_metadata,
    )

    if not input.exists():
        console.print(f"[red]File not found: {input}[/red]")
        raise typer.Exit(1)

    import shutil

    if not shutil.which("ffprobe"):
        console.print("[red]ffprobe not found — install ffmpeg to use this command[/red]")
        raise typer.Exit(1)

    meta = extract_metadata(input)

    if json_output:
        console.print(format_metadata_json(meta))
    else:
        print_metadata(meta)


@app.command()
def preview(
    input: Annotated[Path, typer.Option("--input", "-i", help="Video file to preview")],
) -> None:
    """Preview a video file in ffplay."""
    import shutil

    from clearcut.preview import preview_video

    if not input.exists():
        console.print(f"[red]File not found: {input}[/red]")
        raise typer.Exit(1)
    if not shutil.which("ffplay"):
        console.print("[red]ffplay not found — install ffmpeg[/red]")
        raise typer.Exit(1)

    preview_video(input)


@app.command()
def web() -> None:
    """Launch the ClearCut web interface."""
    from clearcut.web.app import launch

    launch()


@app.command()
def upload(
    input: Annotated[Path, typer.Option("--input", "-i", help="Video file to upload")],
    platform: Annotated[
        str, typer.Option("--platform", "-p", help="Platform: tiktok or youtube")
    ] = "tiktok",
) -> None:
    """Stub: prepare a video for social media upload."""
    from clearcut.social import upload_tiktok, upload_youtube

    if not input.exists():
        console.print(f"[red]File not found: {input}[/red]")
        raise typer.Exit(1)

    if platform == "tiktok":
        result = upload_tiktok(input)
    elif platform == "youtube":
        result = upload_youtube(input)
    else:
        console.print(f"[red]Unknown platform: {platform}[/red]")
        raise typer.Exit(1)

    console.print(f"[yellow]{result['message']}[/yellow]")


if __name__ == "__main__":
    app()
