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
    2. Compositing (PiP, image overlays)
    3. Caption generation + burn-in
    4. Final encode (hardware-accelerated)
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self._tmpdir: tempfile.TemporaryDirectory | None = None
        self._workdir: Path | None = None

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

        # Stage 2: Compositing
        if self.config.context or self.config.images or self.config.assets:
            current = self._stage_composite(current)

        # Stage 3: Captions
        if self.config.generate_captions:
            current = self._stage_captions(current)

        # Stage 4: Final encode
        current = self._stage_encode(current)

        # Move to final output
        if current != self.config.output:
            shutil.move(str(current), str(self.config.output))

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

    def _stage_composite(self, input_path: Path) -> Path:
        from clearcut.compositor import CompositeScene, ImageOverlay

        console.print("\n[bold]Stage 2:[/bold] Compositing")
        output = self.workdir / "02_composite.mp4"

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
        return output

    def _stage_captions(self, input_path: Path) -> Path:
        from clearcut.captions import CaptionGenerator

        console.print("\n[bold]Stage 3:[/bold] Captions")
        style = get_style(self.config.style)
        gen = CaptionGenerator(style=style)

        words = gen.transcribe(input_path)
        ass_content = gen.generate_ass(words)

        ass_path = self.workdir / "captions.ass"
        ass_path.write_text(ass_content)

        if self.config.burn_captions:
            output = self.workdir / "03_captioned.mp4"
            gen.burn(input_path, ass_path, output)
            return output

        # Just save the ASS file next to the output
        final_ass = self.config.output.with_suffix(".ass")
        shutil.copy2(ass_path, final_ass)
        console.print(f"[green]Captions saved to {final_ass}[/green]")
        return input_path

    def _stage_encode(self, input_path: Path) -> Path:
        from clearcut.encoder import encode

        console.print("\n[bold]Stage 4:[/bold] Final encode")
        output = self.workdir / "04_final.mp4"
        encode(
            input_path, output,
            preset=self.config.encoder_preset,
            hardware=self.config.hardware,
        )
        return output

    def clean(self) -> None:
        """Clean up temporary working directory."""
        if self._tmpdir is not None:
            self._tmpdir.cleanup()
            self._tmpdir = None
            self._workdir = None
            console.print("[dim]Temporary files cleaned up[/dim]")
