"""Tests for clearcut.batch — batch processing."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from clearcut.batch import _collect_files, _output_path_for, run_batch
from clearcut.models import BatchConfig


@pytest.fixture
def batch_dir(tmp_path: Path) -> Path:
    """Create a directory with dummy video files."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    for name in ["clip1.mp4", "clip2.mp4", "clip3.mov", "notes.txt"]:
        (input_dir / name).write_bytes(b"\x00" * 1024)
    return input_dir


def test_collect_files_mp4(batch_dir: Path, tmp_path: Path):
    """Collects only .mp4 files by default."""
    config = BatchConfig(
        input_dir=batch_dir,
        output_dir=tmp_path / "out",
        pattern="*.mp4",
    )
    files = _collect_files(config)
    assert len(files) == 2
    assert all(f.suffix == ".mp4" for f in files)


def test_collect_files_custom_pattern(batch_dir: Path, tmp_path: Path):
    """Custom pattern filters correctly."""
    config = BatchConfig(
        input_dir=batch_dir,
        output_dir=tmp_path / "out",
        pattern="*.mov",
    )
    files = _collect_files(config)
    assert len(files) == 1
    assert files[0].name == "clip3.mov"


def test_collect_files_star_pattern(batch_dir: Path, tmp_path: Path):
    """Star pattern collects all files."""
    config = BatchConfig(
        input_dir=batch_dir,
        output_dir=tmp_path / "out",
        pattern="*.*",
    )
    files = _collect_files(config)
    assert len(files) == 4


def test_output_path_for():
    """Output path has .mp4 extension and lives in output dir."""
    out = _output_path_for(Path("/input/video.mov"), Path("/output"))
    assert out == Path("/output/video.mp4")


def test_dry_run(batch_dir: Path, tmp_path: Path):
    """Dry run doesn't create output files."""
    out_dir = tmp_path / "out"
    config = BatchConfig(
        input_dir=batch_dir,
        output_dir=out_dir,
        pattern="*.mp4",
        dry_run=True,
    )
    results = run_batch(config)
    assert len(results) == 2
    assert all("[dry-run]" in r for r in results)
    # Output dir is created but no video files
    assert out_dir.exists()
    assert list(out_dir.glob("*.mp4")) == []


def test_skip_existing(batch_dir: Path, tmp_path: Path):
    """Already-processed files are skipped."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    # Pre-create one output
    (out_dir / "clip1.mp4").write_bytes(b"\x00")

    config = BatchConfig(
        input_dir=batch_dir,
        output_dir=out_dir,
        pattern="*.mp4",
        dry_run=True,
    )
    results = run_batch(config)
    # Only clip2.mp4 should be in results
    assert len(results) == 1
    assert "clip2" in results[0]


def test_no_matching_files(tmp_path: Path):
    """Empty directory returns empty results."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    config = BatchConfig(
        input_dir=empty_dir,
        output_dir=tmp_path / "out",
        pattern="*.mp4",
    )
    results = run_batch(config)
    assert results == []


def test_batch_config_validation(tmp_path: Path):
    """BatchConfig validates that input_dir exists."""
    with pytest.raises(ValueError, match="not found"):
        BatchConfig(
            input_dir=tmp_path / "nonexistent",
            output_dir=tmp_path / "out",
        )


def test_batch_config_not_a_dir(tmp_path: Path):
    """BatchConfig validates that input_dir is a directory."""
    a_file = tmp_path / "file.txt"
    a_file.write_text("hello")
    with pytest.raises(ValueError, match="not a directory"):
        BatchConfig(
            input_dir=a_file,
            output_dir=tmp_path / "out",
        )


def test_run_batch_sequential(batch_dir: Path, tmp_path: Path):
    """Sequential processing calls _process_single for each file."""
    out_dir = tmp_path / "out"
    config = BatchConfig(
        input_dir=batch_dir,
        output_dir=out_dir,
        pattern="*.mp4",
        max_workers=1,
    )
    with patch("clearcut.batch._process_single", return_value="OK: test") as mock:
        results = run_batch(config)
        assert mock.call_count == 2
        assert len(results) == 2
