"""clearcut CLI — Typer-based command interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from clearcut import __version__

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
) -> None:
    """clearcut — automated video editing pipeline."""


@app.command()
def process(
    main: Annotated[Path, typer.Option("--main", "-m", help="Main video file")],
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
    # --- Template ---
    template: Annotated[
        Optional[str],
        typer.Option("--template", help="Template preset (clean/tiktok/cinematic/bold)"),
    ] = None,
) -> None:
    """Process raw footage into a publish-ready video."""
    from clearcut.models import AssetPosition, PipelineConfig
    from clearcut.pipeline import Pipeline

    parsed_assets = []
    if assets:
        for raw in assets:
            parsed_assets.append(AssetPosition.parse(raw))

    config = PipelineConfig(
        main=main,
        context=context or [],
        images=images or [],
        assets=parsed_assets,
        style=style,
        output=output,
        remove_silence=not no_silence,
        silence_method=silence_method,
        generate_captions=captions,
        burn_captions=burn,
        encoder_preset=preset,
        hardware=hardware,
        normalize_audio=normalize,
        audio_target_lufs=audio_target,
        duck_music=duck_music,
        lut=lut,
        brightness=brightness,
        contrast=contrast,
        saturation=saturation,
        format=format,
        transition=transition,
        transition_duration=transition_duration,
        template=template,
    )

    pipeline = Pipeline(config)
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


if __name__ == "__main__":
    app()
