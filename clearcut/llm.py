"""LLM provider abstraction for AI-powered features."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass

log = logging.getLogger(__name__)


class LlmProvider(ABC):
    """Abstract interface for LLM providers used by clearcut features."""

    @abstractmethod
    def select_clips(
        self,
        transcript: str,
        num_clips: int,
        min_duration: float,
        max_duration: float,
        video_duration: float,
    ) -> list[dict]:
        """Ask the LLM to select the best clip segments from a transcript.

        Args:
            transcript: Full transcript text with timestamps.
            num_clips: Number of clips to select.
            min_duration: Minimum clip duration in seconds.
            max_duration: Maximum clip duration in seconds.
            video_duration: Total video duration in seconds.

        Returns:
            List of dicts with 'start', 'end', 'title', 'reason',
            and 'virality_score' keys.
        """
        ...


@dataclass
class ClaudeCliProvider(LlmProvider):
    """Uses Claude Code CLI for AI features."""

    model: str = "sonnet"
    claude_bin: str = ""

    def __post_init__(self):
        if not self.claude_bin:
            self.claude_bin = shutil.which("claude") or shutil.which("claude-code") or ""
        if not self.claude_bin:
            log.warning("Claude CLI not found on PATH — AI features will fail")

    def select_clips(
        self,
        transcript: str,
        num_clips: int,
        min_duration: float,
        max_duration: float,
        video_duration: float,
    ) -> list[dict]:
        """Ask Claude to pick the best clips from a transcript."""
        if not self.claude_bin:
            raise RuntimeError("Claude CLI not found. Install it or set claude_bin path.")

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
            "  {\n"
            '    "start": float,\n'
            '    "end": float,\n'
            '    "title": "short descriptive title",\n'
            '    "reason": "why this clip works for short-form",\n'
            '    "virality_score": 0.0 to 1.0\n'
            "  }\n"
            "]\n\n"
            "If no good clips are found, return an empty array: []"
        )

        result = subprocess.run(
            [self.claude_bin, "-p", prompt, "--print", "--model", self.model],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI failed (exit {result.returncode}): {result.stderr}")

        output = result.stdout.strip()
        # Strip any markdown code fences
        if output.startswith("```"):
            output = output.split("\n", 1)[-1]
            output = output.rsplit("```", 1)[0]
        return json.loads(output.strip())


def get_provider(name: str = "claude", **kwargs) -> LlmProvider:
    """Factory to get an LLM provider by name.

    Args:
        name: Provider name ('claude' supported, more coming).
        **kwargs: Provider-specific constructor args.

    Returns:
        An LlmProvider instance.
    """
    providers: dict[str, type] = {
        "claude": ClaudeCliProvider,
    }
    cls = providers.get(name, ClaudeCliProvider)
    return cls(**kwargs)
