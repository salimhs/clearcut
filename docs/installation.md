# Installation

## Prerequisites

ClearCut requires **Python 3.10 or later** and **ffmpeg** installed on your system.

## Pip Install

ClearCut is available on PyPI. You can install it with different extras depending on what features you need:

```bash
# Core: silence removal, compositing, encoding
pip install clearcut

# + WhisperX for caption generation
pip install "clearcut[captions]"

# + PyTorch for Silero-VAD (faster silence detection)
pip install "clearcut[silence]"

# + PySceneDetect for scene boundary detection
pip install "clearcut[scenes]"

# Everything
pip install "clearcut[all]"
```

### What Each Extra Includes

| Extra | Dependencies | Enables |
|-------|-------------|---------|
| `core` (default) | typer, moviepy, opencv, numpy, ffmpeg-python, pydantic, rich | Pipeline, trimming, compositing, encoding |
| `captions` | whisperx | `clearcut transcribe`, `--captions` flag |
| `silence` | torch, torchaudio | Silero-VAD (faster, more accurate silence removal) |
| `scenes` | scenedetect[opencv] | `--detect-scenes` flag |
| `all` | All of the above | Everything |

## Installing ffmpeg

ClearCut relies on ffmpeg for all video/audio processing. You need it installed separately.

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install ffmpeg
```

### macOS

```bash
brew install ffmpeg
```

### Windows

Using Chocolatey:

```powershell
choco install ffmpeg
```

Or download manually from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to your PATH.

### Verify Installation

```bash
ffmpeg -version
```

## Using Docker

A Docker image is available with all dependencies pre-installed:

```bash
docker run --rm -v $(pwd):/workspace ghcr.io/salimhs/clearcut \
  process --main /workspace/input.mp4 --output /workspace/output.mp4
```

## Development Installation

For contributing or running from source:

```bash
git clone https://github.com/salimhs/clearcut.git
cd clearcut
pip install -e ".[all,dev,test]"
```

This installs ClearCut in editable mode with all extras plus dev tools (ruff, mypy, pre-commit) and test dependencies (pytest).

## Verifying Installation

After installation, check that ClearCut is ready:

```bash
clearcut --version
clearcut info
```

The `info` command will show your system's GPU acceleration capabilities and verify ffmpeg is available.
