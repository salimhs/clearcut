"""AI-powered highlight detection and clip extraction.

Analyzes video transcripts using an LLM to identify the most engaging,
quotable, or viral-worthy segments, then extracts them as individual clips
ready for the ClearCut pipeline.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

console = Console()


@dataclass
class HighlightClip:
    """A detected highlight segment."""

    start: float
    end: float
    title: str
    reason: str
    virality_score: float


@dataclass
class HighlightResult:
    """Result of highlight detection on a video."""

    clips: list[HighlightClip]
    total_duration: float = 0.0


def detect_highlights(
    video_path: Path,
    num_clips: int = 5,
    min_duration: float = 20.0,
    max_duration: float = 90.0,
    model: str = "sonnet",
) -> HighlightResult:
    """Analyze a video and detect the best highlight clips using AI.

    Pipeline:
    1. Transcribe with WhisperX
    2. Build timestamped transcript
    3. Send to LLM (Claude CLI) for analysis
    4. Parse response into HighlightClip objects

    Args:
        video_path: Path to the video file.
        num_clips: Number of highlight clips to extract.
        min_duration: Minimum clip duration in seconds.
        max_duration: Maximum clip duration in seconds.
        model: Claude model to use (sonnet, opus, haiku).

    Returns:
        HighlightResult with detected clips.
    """
    console.print(f"[cyan]Transcribing {video_path.name} for highlight detection...[/cyan]")
    words = _transcribe(video_path)
    if not words:
        console.print("[yellow]No speech detected — cannot find highlights[/yellow]")
        return HighlightResult(clips=[])

    transcript = _build_transcript(words)
    duration = words[-1].end if words else 0

    console.print(f"[cyan]Analyzing transcript for top {num_clips} highlights...[/cyan]")
    clips = _llm_analyze(transcript, words, num_clips, min_duration, max_duration, model)

    console.print(f"[green]Found {len(clips)} highlight clips[/green]")
    return HighlightResult(clips=clips, total_duration=duration)


def extract_clips(
    video_path: Path,
    highlights: HighlightResult,
    output_dir: Path,
    prefix: str = "clip",
) -> list[Path]:
    """Extract detected highlight clips from the video using ffmpeg.

    Each clip is extracted losslessly (-c copy) so they can be fed
    individually into the ClearCut pipeline.

    Args:
        video_path: Source video file.
        highlights: HighlightResult from detect_highlights().
        output_dir: Directory to write clip files.
        prefix: Filename prefix for clips.

    Returns:
        List of paths to the extracted clip files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    extracted: list[Path] = []
    for i, clip in enumerate(highlights.clips):
        out_path = output_dir / f"{prefix}_{i + 1:02d}.mp4"
        dur = clip.end - clip.start
        console.print(
            f"  Extracting clip {i + 1}: {clip.title} "
            f"({clip.start:.1f}s - {clip.end:.1f}s, {dur:.0f}s)"
        )
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{clip.start:.3f}",
            "-i", str(video_path),
            "-to", f"{dur:.3f}",
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            str(out_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        extracted.append(out_path)

    console.print(f"[green]Extracted {len(extracted)} clips to {output_dir}[/green]")
    return extracted


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _transcribe(video_path: Path):
    """Transcribe video using WhisperX and return list of Word objects."""
    from clearcut.captions import CaptionGenerator
    from clearcut.styles import get_style

    gen = CaptionGenerator(style=get_style("default"))
    return gen.transcribe(video_path)


def _build_transcript(words) -> str:
    """Build a readable transcript with timestamps from word list."""
    lines: list[str] = []
    chunk_size = 10
    for i in range(0, len(words), chunk_size):
        chunk = words[i : i + chunk_size]
        start = chunk[0].start
        end = chunk[-1].end
        text = " ".join(w.text for w in chunk)
        lines.append(f"[{_fmt_time(start)} - {_fmt_time(end)}] {text}")
    return "\n".join(lines)


def _fmt_time(seconds: float) -> str:
    """Format seconds to MM:SS."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def _llm_analyze(
    transcript: str,
    words,
    num_clips: int,
    min_duration: float,
    max_duration: float,
    model: str,
) -> list[HighlightClip]:
    """Send transcript to Claude CLI and parse the response."""
    prompt = (
        "You are a professional video editor analyzing a transcript to find "
        "the BEST clips for short-form content (TikTok, Reels, Shorts).\n\n"
        f"TRANSCRIPT (with timestamps):\n{transcript}\n\n"
        f"TASK: Find the top {num_clips} highlight segments that would make "
        "the best short-form video clips.\n\n"
        f"RULES:\n"
        f"- Each clip must be between {min_duration:.0f} and {max_duration:.0f} "
        "seconds long\n"
        "- Prioritize: strong openings/hooks, emotional peaks, quotable lines, "
        "funny moments, surprising revelations, passionate arguments, "
        "concise story moments\n"
        "- Clips should feel self-contained (a viewer should understand them "
        "without context)\n"
        "- Avoid: rambling, technical jargon without setup, inside jokes, "
        "off-topic tangents\n"
        "- Timestamps must be ACCURATE — use the EXACT timestamps from the "
        "transcript above\n"
        "- Prefer shorter clips over longer ones when the content is dense\n\n"
        "Respond with ONLY a valid JSON array (no markdown, no explanation):\n"
        "[\n"
        '  {\n'
        '    "start": float,\n'
        '    "end": float,\n'
        '    "title": "short descriptive title",\n'
        '    "reason": "why this clip works for short-form",\n'
        '    "virality_score": 0.0 to 1.0\n'
        "  }\n"
        "]\n\n"
        "If no good clips are found, return an empty array: []"
    )

    response = _call_llm(prompt, model)

    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()

        clips_data = json.loads(response)
        if not isinstance(clips_data, list):
            clips_data = [clips_data]

        clips: list[HighlightClip] = []
        for item in clips_data:
            clip = HighlightClip(
                start=float(item["start"]),
                end=float(item["end"]),
                title=str(item.get("title", "")),
                reason=str(item.get("reason", "")),
                virality_score=float(item.get("virality_score", 0.5)),
            )
            clip.start = max(0.0, clip.start)
            clip.end = max(clip.start + 5.0, clip.end)
            clip.virality_score = max(0.0, min(1.0, clip.virality_score))
            clips.append(clip)

        clips.sort(key=lambda c: c.virality_score, reverse=True)
        return clips[:num_clips]

    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        console.print(f"[yellow]Failed to parse LLM response: {e}[/yellow]")
        console.print(f"[dim]Raw response: {response[:500]}[/dim]")
        return []


def _call_llm(prompt: str, model: str = "sonnet") -> str:
    """Call Claude CLI with the given prompt and return the response."""
    import shutil

    claude_bin = shutil.which("claude")
    if not claude_bin:
        raise RuntimeError(
            "Claude CLI not found. Install with: "
            "npm install -g @anthropic-ai/claude-code"
        )

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="clearcut_"
    ) as f:
        f.write(prompt)
        prompt_path = f.name

    try:
        cmd = [
            claude_bin, "-p", f"@{prompt_path}",
            "--allowedTools", "Read",
            "--max-turns", "1",
            "--model", model,
            "--output-format", "text",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.stdout
    except subprocess.TimeoutExpired:
        console.print("[red]Claude timed out — LLM analysis failed[/red]")
        return "[]"
    finally:
        Path(prompt_path).unlink(missing_ok=True)


def repurpose(
    input_path: Path,
    output_dir: Path,
    num_clips: int = 5,
    min_duration: float = 20.0,
    max_duration: float = 90.0,
    process: bool = True,
    **pipeline_kwargs,
) -> list[Path]:
    """High-level entry point: detect highlights → extract → optionally process.

    This is the main function called by the CLI ``repurpose`` command.

    Args:
        input_path: Input video file.
        output_dir: Directory for output clips.
        num_clips: Number of clips to generate.
        min_duration: Minimum clip duration.
        max_duration: Maximum clip duration.
        process: If True, run each clip through the full ClearCut pipeline.
        **pipeline_kwargs: Arguments passed to PipelineConfig
            (template, style, captions, etc.)

    Returns:
        List of paths to the final output files.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    console.rule("[bold cyan]ClearCut Repurpose[/bold cyan]")
    console.print(f"Input: {input_path.name}")
    console.print(f"Target: {num_clips} clips ({min_duration:.0f}-{max_duration:.0f}s each)")

    highlights = detect_highlights(input_path, num_clips, min_duration, max_duration)

    if not highlights.clips:
        console.print("[yellow]No highlights detected — cannot repurpose[/yellow]")
        return []

    raw_clips = extract_clips(input_path, highlights, output_dir)

    if not process:
        console.print("[green]Clips extracted (pipeline processing skipped)[/green]")
        return raw_clips

    from clearcut.models import PipelineConfig
    from clearcut.pipeline import Pipeline

    processed: list[Path] = []
    for i, (clip_path, hc) in enumerate(zip(raw_clips, highlights.clips)):
        console.rule(f"[bold]Processing clip {i + 1}: {hc.title}[/bold]")
        output_path = output_dir / f"final_{i + 1:02d}.mp4"
        config = PipelineConfig(main=clip_path, output=output_path, **pipeline_kwargs)
        pipeline = Pipeline(config)
        try:
            pipeline.run()
        finally:
            pipeline.clean()
        processed.append(output_path)

    console.rule("[bold green]Repurpose complete![/bold green]")
    for p in processed:
        console.print(f"  {p.name}")

    return processed
