"""Video compositing — picture-in-picture, image overlays, layered assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console

console = Console()


@dataclass
class ImageOverlay:
    """An image to composite onto video at a specific timestamp."""

    image_path: Path
    seconds: float
    duration: float = 5.0
    transition: str = "fade"  # fade | cut | slide
    position: str = "center"  # center | top-right | bottom-left | custom
    scale: float = 0.8  # fraction of frame width
    opacity: float = 1.0


@dataclass
class CompositeScene:
    """Assembles main footage, context footage (PiP), and image overlays."""

    main_path: Path
    context_paths: list[Path] = field(default_factory=list)
    overlays: list[ImageOverlay] = field(default_factory=list)
    pip_position: str = "bottom-right"
    pip_scale: float = 0.3

    def render(self, output_path: Path) -> Path:
        """Render the composite scene to a lossless intermediate.

        Uses ffv1 in MKV for a fast, quality-preserving intermediate that the
        final encoder pass can compress without generational loss.
        """
        from moviepy import (
            CompositeVideoClip,
            ImageClip,
            VideoFileClip,
        )

        console.print(f"[cyan]Compositing {self.main_path.name}...[/cyan]")

        main_clip = VideoFileClip(str(self.main_path))
        opened_clips = [main_clip]

        try:
            layers = [main_clip]

            # Picture-in-picture for context footage
            for ctx_path in self.context_paths:
                ctx = VideoFileClip(str(ctx_path))
                opened_clips.append(ctx)
                pip_clip = self._make_pip(ctx, main_clip)
                layers.append(pip_clip)

            # Image overlays at specific timestamps
            for overlay in self.overlays:
                img_clip = self._make_image_overlay(overlay, main_clip)
                layers.append(img_clip)

            composite = CompositeVideoClip(layers, size=main_clip.size)
            composite = composite.with_duration(main_clip.duration)

            # Lossless intermediate — ffv1 in mkv is fast to write
            # and preserves full quality for the encoder pass
            output_path = output_path.with_suffix(".mkv")
            composite.write_videofile(
                str(output_path),
                codec="ffv1",
                audio_codec="pcm_s16le",
                logger=None,
                preset="fast",
            )
        finally:
            for clip in opened_clips:
                try:
                    clip.close()
                except Exception:
                    pass

        console.print(f"[green]Composite written to {output_path}[/green]")
        return output_path

    def _make_pip(self, pip_clip, main_clip):
        """Position and scale a picture-in-picture clip."""
        main_w, main_h = main_clip.size
        pip_w = int(main_w * self.pip_scale)
        pip_h = int(main_h * self.pip_scale)
        pip_clip = pip_clip.resized((pip_w, pip_h))

        margin = 20
        positions = {
            "bottom-right": (main_w - pip_w - margin, main_h - pip_h - margin),
            "bottom-left": (margin, main_h - pip_h - margin),
            "top-right": (main_w - pip_w - margin, margin),
            "top-left": (margin, margin),
        }
        pos = positions.get(self.pip_position, positions["bottom-right"])

        pip_clip = pip_clip.with_position(pos)

        # Trim PiP to main clip duration
        if pip_clip.duration > main_clip.duration:
            pip_clip = pip_clip.subclipped(0, main_clip.duration)

        return pip_clip

    def _make_image_overlay(self, overlay: ImageOverlay, main_clip):
        """Create an image overlay clip with optional transitions."""
        from moviepy import ImageClip

        main_w, main_h = main_clip.size
        img_w = int(main_w * overlay.scale)

        img_clip = (
            ImageClip(str(overlay.image_path))
            .resized(width=img_w)
            .with_start(overlay.seconds)
            .with_duration(overlay.duration)
            .with_opacity(overlay.opacity)
        )

        # Position
        positions = {
            "center": ("center", "center"),
            "top-right": (main_w - img_w - 20, 20),
            "bottom-left": (20, main_h - img_clip.size[1] - 20),
            "bottom-right": (main_w - img_w - 20, main_h - img_clip.size[1] - 20),
        }
        pos = positions.get(overlay.position, ("center", "center"))
        img_clip = img_clip.with_position(pos)

        # Transition
        if overlay.transition == "fade":
            from moviepy.video.fx import FadeIn, FadeOut
            fade_dur = min(0.5, overlay.duration / 4)
            img_clip = img_clip.with_effects([
                FadeIn(fade_dur),
                FadeOut(fade_dur),
            ])

        return img_clip
