"""Pipeline orchestrator — ties all stages together."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from rich.console import Console

from clearcut.models import PipelineConfig
from clearcut.styles import get_style

console = Console()


class Pipeline:
    """Orchestrates the full clearcut video editing pipeline.

    Stages (in order):
    1. Silence removal (VAD or auto-editor)
    2. Audio normalization (EBU R128)
    3. Compositing (PiP, image overlays)
    4. Caption generation + burn-in
    5. Colour grading (LUT + basic correction)
    6. Format conversion (9:16, 1:1, etc.)
    7. Transitions between segments
    8. Final encode (hardware-accelerated)
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self._tmpdir: tempfile.TemporaryDirectory | None = None
        self._workdir: Path | None = None
        self._skip_encode: bool = False

    @property
    def workdir(self) -> Path:
        if self._workdir is None:
            self._tmpdir = tempfile.TemporaryDirectory(prefix="clearcut_")
            self._workdir = Path(self._tmpdir.name)
        return self._workdir

    def run(self) -> Path:
        """Execute the full pipeline and return the output path."""
        console.rule("[bold cyan]clearcut pipeline[/bold cyan]")
        current = self.config.main

        # Stage 1: Silence removal
        if self.config.remove_silence:
            current = self._stage_silence(current)

        # Stage 2: Audio normalization
        if self.config.normalize_audio:
            current = self._stage_normalize_audio(current)

        # Stage 2b: Music ducking (optional)
        if self.config.duck_music:
            current = self._stage_duck_music(current)

        # Stage 3: Compositing
        if self.config.context or self.config.images or self.config.assets:
            current = self._stage_composite(current)

        # Stage 4: Captions
        if self.config.generate_captions:
            current = self._stage_captions(current)

        # Stage 5: Colour grading — LUT and/or basic correction
        current = self._stage_colour(current)

        # Stage 6: Format conversion (skip if already 16:9)
        if self.config.format != "16:9":
            current = self._stage_format(current)

        # Stage 7: Transitions (if multiple context clips form segments)
        # Transitions are applied when there are multiple context/B-roll
        # clips that should be joined with effects between them.

        # Stage 8: Final encode (skip if compositor already produced lossless
        # intermediate and no caption burn needed)
        if not self._skip_encode:
            current = self._stage_encode(current)

        # Move to final output — handle .mkv → .mp4 renaming
        final = self.config.output
        if current.suffix == ".mkv" and final.suffix == ".mp4":
            final = final.with_suffix(".mkv")
        if current != final:
            shutil.move(str(current), str(final))

        console.rule("[bold green]Done[/bold green]")
        console.print(f"Output: [bold]{self.config.output}[/bold]")
        return self.config.output

    def _stage_silence(self, input_path: Path) -> Path:
        from clearcut.silence import remove_silence

        console.print("\n[bold]Stage 1:[/bold] Silence removal")
        output = self.workdir / "01_trimmed.mp4"
        remove_silence(
            input_path, output,
            method=self.config.silence_method,
        )
        return output

    def _stage_normalize_audio(self, input_path: Path) -> Path:
        from clearcut.audio import normalize_audio

        console.print("\n[bold]Stage 2:[/bold] Audio normalization")
        output = self.workdir / "02_normalized.mp4"
        normalize_audio(
            input_path, output,
            target_lufs=self.config.audio_target_lufs,
        )
        return output

    def _stage_duck_music(self, input_path: Path) -> Path:
        from clearcut.audio import add_ducking

        console.print("\n[bold]Stage 2b:[/bold] Music ducking")
        output = self.workdir / "02b_ducked.mp4"
        add_ducking(
            input_path,
            self.config.duck_music,
            output,
        )
        return output

    def _stage_composite(self, input_path: Path) -> Path:
        from clearcut.compositor import CompositeScene, ImageOverlay

        console.print("\n[bold]Stage 3:[/bold] Compositing")
        output = self.workdir / "03_composite.mkv"

        overlays = []
        # Static images shown for 5 seconds at the start
        for i, img_path in enumerate(self.config.images):
            overlays.append(ImageOverlay(
                image_path=img_path,
                seconds=i * 5.0,
                duration=5.0,
            ))
        # Timestamped assets
        for asset in self.config.assets:
            overlays.append(ImageOverlay(
                image_path=asset.path,
                seconds=asset.seconds,
                duration=5.0,
            ))

        scene = CompositeScene(
            main_path=input_path,
            context_paths=list(self.config.context),
            overlays=overlays,
        )
        scene.render(output)

        # If no captions burn needed, skip the encode stage too — we'll output
        # the lossless intermediate as-is for the final step
        if not self.config.burn_captions:
            self._skip_encode = True

        return output

    def _stage_captions(self, input_path: Path) -> Path:
        from clearcut.captions import CaptionGenerator

        console.print("\n[bold]Stage 4:[/bold] Captions")
        style = get_style(self.config.style)
        gen = CaptionGenerator(style=style)

        words = gen.transcribe(input_path)
        ass_content = gen.generate_ass(words)

        ass_path = self.workdir / "captions.ass"
        ass_path.write_text(ass_content)

        if self.config.burn_captions:
            # Preserve intermediate format — keep .mkv if coming from compositor
            ext = input_path.suffix
            output = self.workdir / f"04_captioned{ext}"
            gen.burn(input_path, ass_path, output)
            return output

        # Just save the ASS file next to the output
        final_ass = self.config.output.with_suffix(".ass")
        shutil.copy2(ass_path, final_ass)
        console.print(f"[green]Captions saved to {final_ass}[/green]")
        return input_path

    def _stage_colour(self, input_path: Path) -> Path:
        """Apply LUT and/or basic colour correction."""
        has_lut = self.config.lut is not None
        has_correction = (
            abs(self.config.brightness) >= 0.001
            or abs(self.config.contrast - 1.0) >= 0.001
            or abs(self.config.saturation - 1.0) >= 0.001
        )

        if not has_lut and not has_correction:
            return input_path

        current = input_path

        if has_lut:
            from clearcut.color import apply_lut

            console.print("\n[bold]Stage 5a:[/bold] LUT colour grade")
            output = self.workdir / "05a_lut.mp4"
            apply_lut(current, output, self.config.lut)
            current = output

        if has_correction:
            from clearcut.color import basic_correct

            console.print("\n[bold]Stage 5b:[/bold] Colour correction")
            output = self.workdir / "05b_corrected.mp4"
            basic_correct(
                current, output,
                brightness=self.config.brightness,
                contrast=self.config.contrast,
                saturation=self.config.saturation,
            )
            current = output

        return current

    def _stage_format(self, input_path: Path) -> Path:
        from clearcut.format import to_landscape, to_square, to_vertical

        console.print(f"\n[bold]Stage 6:[/bold] Format conversion → {self.config.format}")
        output = self.workdir / "06_formatted.mp4"

        fmt = self.config.format
        if fmt == "9:16":
            to_vertical(input_path, output)
        elif fmt == "1:1":
            to_square(input_path, output)
        elif fmt == "16:9":
            to_landscape(input_path, output)
        else:
            console.print(
                f"[yellow]Unknown format '{fmt}' — skipping conversion[/yellow]"
            )
            return input_path

        return output

    def _stage_encode(self, input_path: Path) -> Path:
        from clearcut.encoder import encode

        console.print("\n[bold]Stage 8:[/bold] Final encode")
        output = self.workdir / "08_final.mp4"
        encode(
            input_path, output,
            preset=self.config.encoder_preset,
            hardware=self.config.hardware,
        )
        return output

    def apply_transitions_to_segments(self, segment_paths: list[Path]) -> Path:
        """Join multiple video segments with transitions.

        This is a utility for callers that have pre-split segments (e.g. from
        silence removal boundaries or multiple source clips) and want to apply
        transitions between them before continuing the pipeline.

        Returns:
            Path to the joined output file.
        """
        from clearcut.transitions import apply_transitions

        console.print("\n[bold]Stage 7:[/bold] Transitions")
        output = self.workdir / "07_transitions.mp4"
        apply_transitions(
            segment_paths, output,
            transition=self.config.transition,
            duration=self.config.transition_duration,
        )
        return output

    def clean(self) -> None:
        """Clean up temporary working directory."""
        if self._tmpdir is not None:
            self._tmpdir.cleanup()
            self._tmpdir = None
            self._workdir = None
            console.print("[dim]Temporary files cleaned up[/dim]")
