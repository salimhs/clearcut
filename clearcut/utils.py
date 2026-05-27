"""Shared utilities for clearcut modules."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


def has_audio(input_path: Path) -> bool:
    """Check if a video file has an audio stream via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0",
            str(input_path),
        ],
        capture_output=True, text=True,
    )
    return "audio" in result.stdout
