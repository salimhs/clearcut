"""Social upload stubs — prepare for future TikTok/YouTube integration."""

from __future__ import annotations

from pathlib import Path


def upload_tiktok(path: Path, credentials: dict | None = None) -> dict:
    """Stub: validate file and prepare for TikTok upload.

    Args:
        path: Path to video file.
        credentials: Optional API credentials dict.

    Returns:
        Dict with status, message, platform.
    """
    path = Path(path)
    return {
        "status": "stub",
        "message": f"TikTok upload not implemented — file ready at {path}",
        "platform": "tiktok",
        "file": str(path),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def upload_youtube(path: Path, credentials: dict | None = None) -> dict:
    """Stub: validate file and prepare for YouTube upload.

    Args:
        path: Path to video file.
        credentials: Optional API credentials dict.

    Returns:
        Dict with status, message, platform.
    """
    path = Path(path)
    return {
        "status": "stub",
        "message": f"YouTube upload not implemented — file ready at {path}",
        "platform": "youtube",
        "file": str(path),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }
