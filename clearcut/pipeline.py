"""Pipeline orchestrator — ties all stages together."""

from __future__ import annotations

import logging
import signal
import shutil
import tempfile
from pathlib import Path
from types import FrameType

from rich.console import Console

from clearcut.models import PipelineConfig
from clearcut.styles import get_style
log = logging.getLogger(__name__)

console = Console()


class Pipeline:
    """Orchestrates the full clearcut video editing pipeline.

    Stage order:
    1. Silence removal
    2. Audio normalization + ducking
    3. Compositing (PiP, image overlays)
    4. Colour grading (LUT + basic correction)
    5. Format conversion (9:16, 1:1, etc.)
    6. Caption generation + burn-in (AFTER format so ASS positioning is correct)
    7. Effects (punch zoom, hook zoom)
    8. Transitions between segments
    9. Final encode (hardware-accelerated)
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self._tmpdir: tempfile.TemporaryDirectory | None = None
        self._workdir: Path | None = None
        self._skip_encode: bool = False
        self._intermediate_segments: list[Path] = []
        self._interrupted: bool = False
        self._original_sigint: signal.Handlers | None = None
        self._original_sigterm: signal.Handlers | None = None

    @property
    def workdir(self) -> Path:
        if self._workdir is None:
            self._tmpdir = tempfile.TemporaryDirectory(prefix="clearcut_")
            self._workdir = Path(self._tmpdir.name)
        return self._workdir

    def _handle_signal(self, signum: int, frame: FrameType | None) -> None:
        """Handle SIGINT/SIGTERM for graceful shutdown."""
        self._interrupted = True
        console.print("\n[bold yellow]Interrupted — cleaning up...[/bold yellow]")

    def _install_signal_handlers(self) -> None:
        self._original_sigint = signal.getsignal(signal.SIGINT)
        self._original_sigterm = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _restore_signal_handlers(self) -> None:
        if self._original_sigint is not None:
            signal.signal(signal.SIGINT, self._original_sigint)
        if self._original_sigterm is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm)

    def _check_interrupted(self) -> bool:
        if self._interrupted:
            console.print("[yellow]Pipeline interrupted — skipping remaining stages[/yellow]")
            return True
        return False

    def run(self) -> Path:
        """Execute the full pipeline and return the output path."""
        self._install_signal_handlers()
        try:
            return self._run_stages()
        finally:
            self._restore_signal_handlers()

    def _run_stages(self) -> Path:
        """Execute pipeline stages, checking for interruption between each."""
        console.rule("[bold cyan]clearcut pipeline[/bold cyan]")
        current = self.config.main

        # Stage 1: Silence removal
        if self.config.remove_silence and not self._check_interrupted():
            current = self._stage_silence(current)

        # Stage 2: Audio normalization
        if self.config.normalize_audio and not self._check_interrupted():
            current = self._stage_normalize_audio(current)

        # Stage 2b: Music ducking (optional)
        if self.config.duck_music and not self._check_interrupted():
            current = self._stage_duck_music(current)

        # Stage 3: Compositing
        if (self.config.context or self.config.images or self.config.assets) \
                and not self._check_interrupted():
            current = self._stage_composite(current)

        # Stage 4: Colour grading — LUT and/or basic correction
        if not self._check_interrupted():
            current = self._stage_colour(current)

        # Stage 5: Format conversion (apply BEFORE captions so ASS coords are right)
        if self.config.format != "16:9" and not self._check_interrupted():
            current = self._stage_format(current)

        # Stage 6: Captions (burn after correct dimensions are set)
        if self.config.generate_captions and not self._check_interrupted():
            current = self._stage_captions(current)

        # Stage 7: Effects (punch zoom, hook zoom)
        if self.config.punch_zoom and not self._check_interrupted():
            current = self._stage_effects(current)

        # Stage 8: Transitions between segments
        if len(self._intermediate_segments) > 1 and not self._check_interrupted():
            current = self._stage_transitions(current)

        # Stage 9: Final encode
        if not self._skip_encode and not self._check_interrupted():
            current = self._stage_encode(current)

        # Move to final output
        final = self.config.output
        if current.suffix == ".mkv" and final.suffix == ".mp4":
            final = final.with_suffix(".mkv")
        if current != final:
            shutil.move(str(current), str(final))

        if self._interrupted:
            console.rule("[bold yellow]Interrupted[/bold yellow]")
        else:
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
        assert self.config.duck_music is not None
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
        for i, img_path in enumerate(self.config.images):
            overlays.append(ImageOverlay(
                image_path=img_path,
                seconds=i * 5.0,
                duration=5.0,
            ))
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

        if not self.config.burn_captions:
            self._skip_encode = True

        return output

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

            console.print("\n[bold]Stage 4a:[/bold] LUT colour grade")
            output = self.workdir / "04a_lut.mp4"
            assert self.config.lut is not None
            apply_lut(current, output, self.config.lut)
            current = output

        if has_correction:
            from clearcut.color import basic_correct

            console.print("\n[bold]Stage 4b:[/bold] Colour correction")
            output = self.workdir / "04b_corrected.mp4"
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

        console.print(f"\n[bold]Stage 5:[/bold] Format conversion → {self.config.format}")
        output = self.workdir / "05_formatted.mp4"

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

    def _stage_captions(self, input_path: Path) -> Path:
        from clearcut.captions import CaptionGenerator

        console.print("\n[bold]Stage 6:[/bold] Captions")
        style = get_style(self.config.style)
        gen = CaptionGenerator(style=style)

        words = gen.transcribe(input_path)
        ass_content = gen.generate_ass(words)

        ass_path = self.workdir / "captions.ass"
        ass_path.write_text(ass_content)

        if self.config.burn_captions:
            ext = input_path.suffix
            output = self.workdir / f"06_captioned{ext}"
            gen.burn(input_path, ass_path, output)
            return output

        # Save ASS file next to the output
        final_ass = self.config.output.with_suffix(".ass")
        shutil.copy2(ass_path, final_ass)
        console.print(f"[green]Captions saved to {final_ass}[/green]")
        return input_path

    def _stage_effects(self, input_path: Path) -> Path:
        """Apply punch/hook zoom effects."""
        from clearcut.effects import add_hook_zoom, apply_punch_zoom

        console.print("\n[bold]Stage 7:[/bold] Effects")
        current = input_path

        if self.config.hook_zoom:
            console.print("  Adding hook zoom (first 2s)")
            output = self.workdir / "07_hook_zoom.mp4"
            add_hook_zoom(current, output)
            current = output

        if self.config.punch_zoom:
            level = self.config.punch_zoom
            console.print(f"  Applying {level}x punch zoom")
            output = self.workdir / "07_punch_zoom.mp4"
            apply_punch_zoom(current, output, zoom_in=level)
            current = output

        return current

    def _stage_transitions(self, input_path: Path) -> Path:
        """Apply transitions between multiple segments."""
        from clearcut.transitions import apply_transitions

        if len(self._intermediate_segments) < 2:
            return input_path

        console.print("\n[bold]Stage 8:[/bold] Transitions")
        output = self.workdir / "08_transitions.mp4"
        apply_transitions(
            self._intermediate_segments,
            output,
            transition=self.config.transition,
            duration=self.config.transition_duration,
        )
        return output

    def _stage_encode(self, input_path: Path) -> Path:
        from clearcut.encoder import encode

        console.print(f"\n[bold]Stage 9:[/bold] Final encode ({self.config.encoder_preset})")
        output = self.workdir / "09_final.mp4"
        encode(
            input_path, output,
            preset=self.config.encoder_preset,
            hardware=self.config.hardware,
        )
        return output

    def add_segment(self, path: Path) -> None:
        """Register a segment for transition processing."""
        self._intermediate_segments.append(path)

    def clean(self) -> None:
        """Clean up temporary working directory."""
        if self._tmpdir is not None:
            self._tmpdir.cleanup()
            self._tmpdir = None
            self._workdir = None
            console.print("[dim]Temporary files cleaned up[/dim]")
