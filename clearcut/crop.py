"""Smart crop — face-tracking crop for vertical/square format conversion."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from rich.console import Console

log = logging.getLogger(__name__)
console = Console()


@dataclass
class TrackingWindow:
    """A crop window position at a given frame."""

    x: int
    y: int


def detect_faces_in_frames(
    video_path: str,
    sample_interval: int = 15,
) -> list[tuple[int, list[tuple[int, int, int, int]]]]:
    """Detect faces in sampled frames using OpenCV Haar cascade.

    Args:
        video_path: Path to the video file.
        sample_interval: Analyse every Nth frame.

    Returns:
        List of (frame_index, face_bounding_boxes) where each box is
        (x, y, w, h).  Returns empty list if OpenCV is unavailable.
    """
    try:
        import cv2
        import numpy as np  # noqa: F401 — needed by cv2 at runtime
    except ImportError:
        console.print(
            "[yellow]opencv-python-headless not available — "
            "falling back to center crop[/yellow]"
        )
        return []

    try:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        results: list[tuple[int, list[tuple[int, int, int, int]]]] = []
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % sample_interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )
                face_list = [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]
                results.append((frame_idx, face_list))
            frame_idx += 1

        cap.release()
        return results
    except Exception:
        log.warning("Face detection failed — falling back to center crop", exc_info=True)
        return []


def compute_tracking_positions(
    face_data: list[tuple[int, list[tuple[int, int, int, int]]]],
    src_w: int,
    src_h: int,
    crop_w: int,
    crop_h: int,
    smooth_window: int = 5,
) -> list[TrackingWindow]:
    """Compute smooth crop positions from face detection data.

    Uses a moving average over the primary (largest) face in each sampled
    frame to produce a jitter-free tracking window.  Falls back to center
    for frames where no face is detected.

    Args:
        face_data: Output of :func:`detect_faces_in_frames`.
        src_w: Source video width.
        src_h: Source video height.
        crop_w: Target crop width.
        crop_h: Target crop height.
        smooth_window: Number of frames for the moving average.

    Returns:
        One :class:`TrackingWindow` per entry in *face_data*.
    """
    center_x = (src_w - crop_w) // 2
    center_y = (src_h - crop_h) // 2

    # Extract raw positions (center of largest face, or frame center)
    raw_positions: list[tuple[int, int]] = []
    for _frame_idx, faces in face_data:
        if not faces:
            raw_positions.append((center_x, center_y))
            continue
        # Pick the largest face
        largest = max(faces, key=lambda f: f[2] * f[3])
        fx, fy, fw, fh = largest
        # Center the crop window on the face center
        face_cx = fx + fw // 2
        face_cy = fy + fh // 2
        cx = max(0, min(src_w - crop_w, face_cx - crop_w // 2))
        cy = max(0, min(src_h - crop_h, face_cy - crop_h // 2))
        raw_positions.append((cx, cy))

    # Apply moving average smoothing
    smoothed: list[TrackingWindow] = []
    n = len(raw_positions)
    half = smooth_window // 2
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        window = raw_positions[lo:hi]
        avg_x = sum(p[0] for p in window) // len(window)
        avg_y = sum(p[1] for p in window) // len(window)
        # Clamp to valid range
        avg_x = max(0, min(src_w - crop_w, avg_x))
        avg_y = max(0, min(src_h - crop_h, avg_y))
        smoothed.append(TrackingWindow(x=avg_x, y=avg_y))

    return smoothed
