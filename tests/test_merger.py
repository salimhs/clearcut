"""Tests for clearcut.merger — merge multiple clips."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from clearcut.exceptions import ConfigError, FileError
from clearcut.merger import collect_clips_from_dir, merge_clips


@pytest.fixture
def clip_dir(tmp_path: Path) -> Path:
    """Create a directory with dummy clip files."""
    clips = tmp_path / "clips"
    clips.mkdir()
    for name in ["a.mp4", "b.mp4", "c.mp4", "d.mov"]:
        (clips / name).write_bytes(b"\x00" * 1024)
    return clips


def test_collect_clips_from_dir_default(clip_dir: Path):
    """Collects .mp4 files sorted by name."""
    clips = collect_clips_from_dir(clip_dir)
    assert len(clips) == 3
    assert clips[0].name == "a.mp4"
    assert clips[-1].name == "c.mp4"


def test_collect_clips_from_dir_custom_pattern(clip_dir: Path):
    """Custom pattern works."""
    clips = collect_clips_from_dir(clip_dir, pattern="*.mov")
    assert len(clips) == 1
    assert clips[0].name == "d.mov"


def test_collect_clips_from_dir_missing():
    """Raises FileError for nonexistent directory."""
    with pytest.raises(FileError, match="not found"):
        collect_clips_from_dir(Path("/nonexistent"))


def test_merge_no_clips():
    """Raises ConfigError with no clips."""
    with pytest.raises(ConfigError, match="No input clips"):
        merge_clips([], Path("out.mp4"))


def test_merge_missing_clip(tmp_path: Path):
    """Raises FileError for missing clip."""
    with pytest.raises(FileError, match="not found"):
        merge_clips([tmp_path / "missing.mp4"], tmp_path / "out.mp4")


@patch("clearcut.encoder.encode")
@patch("clearcut.transitions.apply_transitions")
@patch("clearcut.audio.normalize_audio")
@patch("clearcut.utils.has_audio", return_value=True)
def test_merge_two_clips(mock_has_audio, mock_normalize, mock_transitions, mock_encode, tmp_path: Path):
    """Merge of two clips calls normalize → transitions → encode."""
    clip1 = tmp_path / "clip1.mp4"
    clip2 = tmp_path / "clip2.mp4"
    clip1.write_bytes(b"\x00" * 1024)
    clip2.write_bytes(b"\x00" * 1024)
    output = tmp_path / "merged.mp4"

    # Make normalize_audio create the output file
    def fake_normalize(inp, out, **kw):
        out.write_bytes(b"\x00" * 100)
        return out
    mock_normalize.side_effect = fake_normalize

    # Make transitions create the output file
    def fake_transitions(segs, out, **kw):
        out.write_bytes(b"\x00" * 100)
        return out
    mock_transitions.side_effect = fake_transitions

    # Make encode create the output file
    def fake_encode(inp, out, **kw):
        out.write_bytes(b"\x00" * 100)
        return out
    mock_encode.side_effect = fake_encode

    merge_clips([clip1, clip2], output)

    assert mock_normalize.call_count == 2
    assert mock_transitions.call_count == 1
    assert mock_encode.call_count == 1


@patch("clearcut.encoder.encode")
@patch("clearcut.audio.normalize_audio")
@patch("clearcut.utils.has_audio", return_value=False)
def test_merge_single_clip_no_audio(mock_has_audio, mock_normalize, mock_encode, tmp_path: Path):
    """Single clip without audio skips normalization."""
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"\x00" * 1024)
    output = tmp_path / "merged.mp4"

    def fake_encode(inp, out, **kw):
        out.write_bytes(b"\x00" * 100)
        return out
    mock_encode.side_effect = fake_encode

    merge_clips([clip], output)

    mock_normalize.assert_not_called()
    assert mock_encode.call_count == 1


@patch("clearcut.encoder.encode")
@patch("clearcut.transitions.apply_transitions")
@patch("clearcut.audio.normalize_audio")
@patch("clearcut.utils.has_audio", return_value=True)
def test_merge_passes_transition_params(mock_has_audio, mock_normalize, mock_transitions, mock_encode, tmp_path: Path):
    """Transition type and duration are forwarded."""
    clips = []
    for i in range(3):
        c = tmp_path / f"c{i}.mp4"
        c.write_bytes(b"\x00" * 1024)
        clips.append(c)

    def fake_normalize(inp, out, **kw):
        out.write_bytes(b"\x00" * 100)
        return out
    mock_normalize.side_effect = fake_normalize

    def fake_transitions(segs, out, **kw):
        out.write_bytes(b"\x00" * 100)
        return out
    mock_transitions.side_effect = fake_transitions

    def fake_encode(inp, out, **kw):
        out.write_bytes(b"\x00" * 100)
        return out
    mock_encode.side_effect = fake_encode

    merge_clips(
        clips,
        tmp_path / "out.mp4",
        transition="dissolve",
        transition_duration=0.8,
    )

    call_kwargs = mock_transitions.call_args
    assert call_kwargs[1]["transition"] == "dissolve"
    assert call_kwargs[1]["duration"] == 0.8
