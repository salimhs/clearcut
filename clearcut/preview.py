"""Video preview using ffplay."""

from __future__ import annotations

import subprocess
from pathlib import Path

from clearcut.exceptions import FileError


def preview_video(path: Path) -> None:
    """Open a video file in ffplay for preview."""
    path = Path(path)
    if not path.exists():
        raise FileError(f"File not found: {path}")
    subprocess.run(
        ["ffplay", "-i", str(path), "-autoexit"],
    )
