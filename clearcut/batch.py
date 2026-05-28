"""Batch processing — run the pipeline on every video in a directory."""

from __future__ import annotations

import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from rich.console import Console

from clearcut.models import BatchConfig

log = logging.getLogger(__name__)
console = Console()

VIDEO_EXTENSIONS = {"*.mp4", "*.mov", "*.mkv"}


def _collect_files(config: BatchConfig) -> list[Path]:
    """Collect video files matching the pattern from the input directory."""
    pattern = config.pattern
    files = sorted(config.input_dir.glob(pattern))
    return files


def _output_path_for(input_file: Path, output_dir: Path) -> Path:
    """Determine the output path for a given input file."""
    return output_dir / input_file.with_suffix(".mp4").name


def _process_single(input_file: Path, output_file: Path) -> str:
    """Process a single file through the pipeline. Returns status message."""
    from clearcut.models import PipelineConfig
    from clearcut.pipeline import Pipeline

    config = PipelineConfig(
        main=input_file,
        output=output_file,
    )
    pipeline = Pipeline(config)
    try:
        pipeline.run()
        return f"OK: {input_file.name} → {output_file.name}"
    finally:
        pipeline.clean()


def run_batch(config: BatchConfig) -> list[str]:
    """Run batch processing on all matching files.

    Args:
        config: BatchConfig with input/output dirs, pattern, and worker count.

    Returns:
        List of status messages (one per file).
    """
    files = _collect_files(config)

    if not files:
        console.print("[yellow]No matching files found[/yellow]")
        return []

    config.output_dir.mkdir(parents=True, exist_ok=True)

    # Filter out already-processed files (resume support)
    to_process: list[tuple[Path, Path]] = []
    for f in files:
        out = _output_path_for(f, config.output_dir)
        if out.exists():
            console.print(f"[dim]Skipping {f.name} — output already exists[/dim]")
        else:
            to_process.append((f, out))

    if not to_process:
        console.print("[green]All files already processed[/green]")
        return []

    console.print(
        f"[cyan]Processing {len(to_process)} file(s) with {config.max_workers} worker(s)[/cyan]"
    )

    if config.dry_run:
        results = []
        for inp, out in to_process:
            msg = f"[dry-run] Would process: {inp.name} → {out.name}"
            console.print(msg)
            results.append(msg)
        return results

    results: list[str] = []

    if config.max_workers <= 1:
        for inp, out in to_process:
            msg = _process_single(inp, out)
            console.print(msg)
            results.append(msg)
    else:
        with ProcessPoolExecutor(max_workers=config.max_workers) as executor:
            futures = {
                executor.submit(_process_single, inp, out): inp.name for inp, out in to_process
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    msg = future.result()
                except Exception as exc:
                    msg = f"FAILED: {name} — {exc}"
                console.print(msg)
                results.append(msg)

    return results
