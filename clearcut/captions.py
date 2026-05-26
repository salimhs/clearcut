"""Caption generation — WhisperX transcription + ASS subtitle output."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from clearcut.models import CaptionStyle
from clearcut.styles import get_style, to_ass_style_line

console = Console()


@dataclass
class Word:
    """A single word with timing information."""

    text: str
    start: float
    end: float


class CaptionGenerator:
    """Generate captions from audio using WhisperX (when available)."""

    def __init__(self, style: CaptionStyle | None = None, style_name: str = "default"):
        self.style = style or get_style(style_name)

    def transcribe(self, audio_path: Path) -> list[Word]:
        """Transcribe audio to word-level timestamps using WhisperX.

        Args:
            audio_path: Path to audio or video file.

        Returns:
            List of Word objects with text, start, and end times.
        """
        try:
            import whisperx
            import torch
        except ImportError:
            raise RuntimeError(
                "WhisperX requires additional dependencies. "
                "Install with: pip install clearcut[captions]"
            )

        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        console.print(f"[cyan]Transcribing {audio_path.name} on {device}...[/cyan]")

        model = whisperx.load_model("large-v3", device, compute_type=compute_type)
        audio = whisperx.load_audio(str(audio_path))
        result = model.transcribe(audio, batch_size=16)

        # Align for word-level timestamps
        align_model, metadata = whisperx.load_align_model(
            language_code=result["language"], device=device
        )
        aligned = whisperx.align(
            result["segments"], align_model, metadata, audio, device,
            return_char_alignments=False,
        )

        words: list[Word] = []
        for segment in aligned["segments"]:
            for w in segment.get("words", []):
                if "start" in w and "end" in w:
                    words.append(Word(text=w["word"], start=w["start"], end=w["end"]))

        console.print(f"[green]Transcribed {len(words)} words[/green]")
        return words

    def generate_ass(self, words: list[Word], style: CaptionStyle | None = None) -> str:
        """Generate ASS subtitle content from word timestamps.

        Groups words into lines of ~6 words each, applies the given style.
        """
        style = style or self.style
        style_line = to_ass_style_line(style)

        header = (
            "[Script Info]\n"
            "ScriptType: v4.00+\n"
            "PlayResX: 1920\n"
            "PlayResY: 1080\n"
            "WrapStyle: 0\n"
            "ScaledBorderAndShadow: yes\n"
            "\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"{style_line}\n"
            "\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )

        events: list[str] = []
        chunk_size = 6
        for i in range(0, len(words), chunk_size):
            chunk = words[i : i + chunk_size]
            start = chunk[0].start
            end = chunk[-1].end
            text = " ".join(w.text for w in chunk)

            if style.animation == "word":
                # Per-word highlight using ASS karaoke tags
                tagged_parts: list[str] = []
                for w in chunk:
                    dur_cs = int((w.end - w.start) * 100)  # centiseconds
                    tagged_parts.append(f"{{\\kf{dur_cs}}}{w.text}")
                text = " ".join(tagged_parts)
            elif style.animation == "fade":
                text = f"{{\\fad(200,200)}}{text}"

            start_ts = _seconds_to_ass_time(start)
            end_ts = _seconds_to_ass_time(end)
            events.append(
                f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{text}"
            )

        return header + "\n".join(events) + "\n"

    def burn(self, video_path: Path, ass_path: Path, output_path: Path) -> Path:
        """Burn ASS subtitles into video using ffmpeg's ass filter."""
        console.print(f"[cyan]Burning captions into {video_path.name}...[/cyan]")

        # Use absolute path with proper ffmpeg escaping via filter argument syntax
        ass_abs = ass_path.resolve()
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"ass={ass_abs}",
            "-c:v", "libx264",
            "-c:a", "copy",
            "-preset", "fast",
            str(output_path),
        ]
        subprocess.run(cmd, check=True)

        console.print(f"[green]Captions burned → {output_path}[/green]")
        return output_path


def _seconds_to_ass_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp format: H:MM:SS.cc"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
