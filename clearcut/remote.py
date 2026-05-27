"""Remote GPU execution — run clearcut on a GPU-enabled machine via SSH.

Transfers input files to a remote host over Tailscale, runs the
pipeline with full CUDA/NVENC acceleration, and retrieves results.

The remote host never sees your source files outside a clean temp
directory that's deleted after each run.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TransferSpeedColumn,
)

console = Console()


class RemoteGpuError(Exception):
    """Remote GPU execution failure."""


@dataclass
class RemoteGpuConfig:
    """Configuration for connecting to a remote GPU machine.

    Attributes:
        host: Tailscale IP or hostname (e.g., '100.97.187.60')
        user: SSH username (default: current user)
        port: SSH port (default: 22, or 0 for Tailscale SSH)
        ssh_key: Optional path to SSH private key
        remote_workdir: Temp dir on remote (default: auto-created)
    """

    host: str
    user: str | None = None
    port: int = 0  # 0 = use Tailscale SSH default
    ssh_key: Path | None = None
    remote_workdir: str | None = None

    @property
    def ssh_host(self) -> str:
        """Return the SSH target string."""
        if self.user:
            return f"{self.user}@{self.host}"
        return self.host

    def ssh_base_cmd(self) -> list[str]:
        """Return the base SSH command list."""
        cmd = ["ssh"]
        if self.port:
            cmd += ["-p", str(self.port)]
        if self.ssh_key:
            cmd += ["-i", str(self.ssh_key)]
        cmd += ["-o", "StrictHostKeyChecking=accept-new",
                "-o", "ConnectTimeout=10"]
        cmd.append(self.ssh_host)
        return cmd

    def scp_base_cmd(self) -> list[str]:
        """Return the base SCP command list."""
        cmd = ["scp"]
        if self.port:
            cmd += ["-P", str(self.port)]
        if self.ssh_key:
            cmd += ["-i", str(self.ssh_key)]
        cmd += ["-o", "StrictHostKeyChecking=accept-new",
                "-o", "ConnectTimeout=10"]
        return cmd


def _run_ssh(config: RemoteGpuConfig, command: str, desc: str = "") -> str:
    """Run a command on the remote host and return stdout.

    Raises:
        RemoteGpuError: If SSH fails or command exits non-zero.
    """
    cmd = config.ssh_base_cmd() + [command]
    if desc:
        console.print(f"[cyan]{desc}...[/cyan]")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        error_msg = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise RemoteGpuError(
            f"Remote command failed (exit {result.returncode}): {error_msg}"
        )

    return result.stdout.strip()


def _run_scp(config: RemoteGpuConfig, src: str, dst: str, desc: str = "") -> None:
    """Copy a file to/from the remote host."""
    cmd = config.scp_base_cmd() + [src, dst]
    if desc:
        console.print(f"[cyan]{desc}...[/cyan]")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        error_msg = result.stderr.strip() or "unknown error"
        raise RemoteGpuError(f"SCP failed: {error_msg}")


def check_remote_connection(config: RemoteGpuConfig) -> bool:
    """Test whether the remote host is reachable via SSH.

    Returns True if connected, False otherwise.
    """
    try:
        result = _run_ssh(config, "echo connected")
        return result == "connected"
    except (subprocess.TimeoutExpired, RemoteGpuError, OSError):
        return False


def check_remote_capabilities(config: RemoteGpuConfig) -> dict:
    """Check what GPU capabilities the remote host has.

    Returns:
        Dict with keys: cuda, nvenc, os, python_version, clearcut_installed.
    """
    caps: dict = {}

    try:
        caps["os"] = _run_ssh(config, "uname -s")
    except RemoteGpuError:
        caps["os"] = "unknown"

    try:
        result = _run_ssh(
            config,
            'python3 -c "import torch; print(torch.cuda.is_available()); '
            'print(torch.cuda.get_device_name(0))"',
        )
        lines = result.splitlines()
        caps["cuda"] = lines[0] == "True"
        caps["gpu_name"] = lines[1] if len(lines) > 1 else ""
    except (RemoteGpuError, subprocess.TimeoutExpired):
        caps["cuda"] = False
        caps["gpu_name"] = ""

    try:
        result = _run_ssh(config, "ffmpeg -hide_banner -encoders 2>/dev/null | grep -c h264_nvenc")
        caps["nvenc"] = result.strip() != "0"
    except RemoteGpuError:
        caps["nvenc"] = False

    try:
        caps["clearcut_installed"] = (
                _run_ssh(config, "pip show clearcut 2>/dev/null && echo YES || echo NO")
                == "YES"
        )
    except RemoteGpuError:
        caps["clearcut_installed"] = False

    return caps


def remote_pipeline(
    config: RemoteGpuConfig,
    input_path: Path,
    output_path: Path,
    *,
    # Pipeline options — mirror the local process command
    remove_silence: bool = True,
    generate_captions: bool = False,
    template: str | None = None,
    format: str = "16:9",
    preset: str = "fast",
) -> Path:
    """Run the full clearcut pipeline on a remote GPU machine.

    Workflow:
    1. Create isolated temp dir on remote
    2. SCP input video to remote temp dir
    3. Run clearcut on remote with CUDA + NVENC
    4. SCP result back
    5. Clean up remote temp dir

    Args:
        config: Connection config for the remote GPU machine.
        input_path: Local path to the input video file.
        output_path: Local path where the output should be saved.
        remove_silence: Whether to remove silence.
        generate_captions: Whether to generate captions (requires
            whisperx/faster-whisper on remote).
        template: Pipeline template to apply (e.g., 'tiktok', 'cinematic').
        format: Output format (16:9, 9:16, 1:1).
        preset: Encoder preset.

    Returns:
        Path to the local output file.

    Raises:
        RemoteGpuError: If remote execution fails at any stage.
        FileNotFoundError: If input_path doesn't exist locally.
    """
    input_path = Path(input_path).resolve()
    output_path = Path(output_path).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    console.rule("[bold cyan]Remote GPU Pipeline[/bold cyan]")
    console.print(f"Input:  {input_path}")
    console.print(f"Remote: {config.ssh_host}")
    console.print(f"Output: {output_path}")

    # 1. Check connection
    console.print(f"\n[bold]Step 1:[/bold] Checking connection to {config.ssh_host}...")
    if not check_remote_connection(config):
        raise RemoteGpuError(
            f"Cannot reach {config.ssh_host}. "
            "Make sure Tailscale is connected and Tailscale SSH is "
            "enabled on the remote machine."
        )
    console.print(f"[green]✓ Connected to {config.ssh_host}[/green]")

    # 2. Create remote temp dir
    remote_dir = _run_ssh(
        config,
        'mktemp -d /tmp/clearcut_gpu_XXXXXX',
        desc="Creating remote workspace",
    )
    remote_input = f"{remote_dir}/{input_path.name}"
    remote_output = f"{remote_dir}/output.mp4"

    try:
        # 3. Transfer input file
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TransferSpeedColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Uploading {input_path.name}...",
                total=input_path.stat().st_size,
            )
            _run_scp(
                config,
                str(input_path),
                f"{config.ssh_host}:{remote_input}",
            )
            progress.update(task, completed=input_path.stat().st_size)

        # 4. Build remote pipeline command
        cmd_parts = [
            "cd", remote_dir, "&&",
            "clearcut", "process",
            "--main", remote_input,
            "--output", remote_output,
            "--hardware", "nvenc",  # Force GPU encoding
        ]

        if not remove_silence:
            cmd_parts.append("--no-silence")
        if generate_captions:
            cmd_parts.append("--captions")
            cmd_parts.append("--burn")
        if template:
            cmd_parts.extend(["--template", template])
        if format != "16:9":
            cmd_parts.extend(["--format", format])
        cmd_parts.extend(["--preset", preset])

        remote_cmd = " ".join(cmd_parts)

        # 5. Run pipeline on remote
        _run_ssh(
            config,
            remote_cmd,
            desc="Running pipeline on remote GPU machine",
        )

        # 6. Download result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _run_scp(
            config,
            f"{config.ssh_host}:{remote_output}",
            str(output_path),
            desc=f"Downloading output to {output_path}",
        )

        console.print(f"\n[bold green]✓ Output saved to {output_path}[/bold green]")

    finally:
        # 7. Clean up remote temp dir
        try:
            _run_ssh(config, f"rm -rf {remote_dir}", desc="Cleaning up remote workspace")
        except (RemoteGpuError, subprocess.TimeoutExpired):
            console.print("[yellow]Warning: could not clean up remote temp dir[/yellow]")

    return output_path
