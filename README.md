<div align="center">
  <h1>🎬 ClearCut</h1>
  <p><strong>Raw footage to publish-ready video. One command.</strong></p>
  <p>
    <a href="https://pypi.org/project/clearcut/"><img src="https://img.shields.io/pypi/v/clearcut" alt="PyPI"></a>
    <a href="https://github.com/salimhs/clearcut/blob/main/LICENSE"><img src="https://img.shields.io/github/license/salimhs/clearcut" alt="License"></a>
    <a href="https://github.com/salimhs/clearcut"><img src="https://img.shields.io/github/stars/salimhs/clearcut" alt="Stars"></a>
  </p>

  <p><em>Silence removal · Picture-in-picture overlays · Image insertion · Styled captions · Hardware-accelerated encoding</em></p>

  <pre><code>pip install clearcut
clearcut process --main take1.mp4 --context broll.mp4 --images diagram.png --captions --output final.mp4</code></pre>
</div>

---

ClearCut is an automated video editing pipeline for content creators. Feed it your raw footage, B-roll clips, and screenshots — it outputs a polished video ready for publishing.

**Use cases:**
- 🎙️ **Talking-head videos** — remove dead air, silence, and restarts
- 📚 **Tutorials** — PiP screen recordings, styled captions
- 🏢 **Presentations** — insert slides at timestamps, B-roll overlays
- 🎥 **Content repurposing** — slice long recordings into publish-ready clips

## Features

| Feature | Description |
|---------|-------------|
| 🎯 **Silence removal** | Detects and removes dead air using Silero-VAD (voice activity detection) or auto-editor fallback. Smooth jump cuts between speech segments. |
| 🖼️ **PiP overlays** | Composite B-roll or screen recordings as picture-in-picture in any corner. Configurable size and position. |
| 🏷️ **Image insertion** | Insert screenshots, diagrams, or slides at specific timestamps with fade transitions. |
| 📝 **Styled captions** | Transcribe with WhisperX (word-level timestamps), generate ASS subtitles, burn directly into video. Four style presets. |
| ⚡ **Hardware encoding** | Auto-detects NVIDIA NVENC, AMD AMF, Intel QSV, or falls back to software x264. |
| 🔌 **Modular** | Run the full pipeline or individual stages (`clearcut trim`, `clearcut transcribe`). |

## Quick Start

```bash
# Install (core — silence, compositing, encoding)
pip install clearcut

# Install with all extras
pip install "clearcut[all]"

# Run the full pipeline
clearcut process \
  --main ~/videos/take1.mp4 \
  --context ~/videos/screen_recording.mp4 \
  --images ~/assets/diagram.png \
  --assets screenshot.jpg@30 \
  --style modern \
  --captions \
  --output ~/output/final.mp4
```

## Examples

### Basic silence removal

```bash
clearcut trim --input raw_recording.mp4 --output clean.mp4
```

### Talking-head with B-roll PiP

```bash
clearcut process \
  --main talking_head.mp4 \
  --context broll_demo.mp4 \
  --output final.mp4
```

### Full production pipeline

```bash
clearcut process \
  --main talking_head.mp4 \
  --context screen_recording.mp4 \
  --images diagram.png chart.jpg \
  --assets screenshot@15 logo@120 \
  --style bold \
  --captions \
  --burn \
  --preset slow \
  --hardware nvenc \
  --output final.mp4
```

### Generate captions only

```bash
clearcut transcribe --input video.mp4 --style modern --output subtitles.ass
```

## Style Presets

| Style | Font | Size | Animation | Preview |
|-------|------|------|-----------|---------|
| `default` | Arial | 48 | None | Clean, safe |
| `modern` | Montserrat | 52 | Word-highlight | YouTube standard |
| `minimal` | Helvetica Neue | 40 | None | Subtle |
| `bold` | Impact | 64 | Word-highlight | Eye-catching |

## Pipeline Architecture

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Raw footage  │   │ Silence      │   │ Compositing  │   │ Final encode │
│               │──▶│ removal      │──▶│ (lossless)   │──▶│ (HW accel)   │──▶ output.mp4
│ .mp4 / .mov   │   │ Silero-VAD   │   │ MoviePy PiP  │   │ NVENC/AMF    │
│ .mkv          │   │ auto-editor  │   │ + overlays   │   │ x264 fallback│
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
                                            │
                                     ┌──────┴──────┐
                                     │  Captions   │
                                     │  WhisperX   │
                                     │  → ASS subs │
                                     │  → ffmpeg   │
                                     └─────────────┘
```

## Installation Options

```bash
pip install clearcut                 # Core: silence, compositing, encoding
pip install "clearcut[captions]"     # + WhisperX transcription
pip install "clearcut[silence]"      # + PyTorch for Silero-VAD
pip install "clearcut[scenes]"       # + PySceneDetect
pip install "clearcut[all]"          # Everything
```

### Dependencies

ClearCut handles all the heavy lifting, but you need `ffmpeg` installed on your system:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
choco install ffmpeg
# Or download from https://ffmpeg.org/download.html
```

## CLI Reference

### `clearcut process`

Run the full video editing pipeline.

| Option | Default | Description |
|--------|---------|-------------|
| `-m, --main` | *(required)* | Main talking-head video file |
| `-c, --context` | — | B-roll video(s) for PiP overlay (repeatable) |
| `-i, --images` | — | Static images to overlay (repeatable) |
| `-a, --assets` | — | Timestamped images: `path@seconds` (repeatable) |
| `-s, --style` | `default` | Caption style: `default`, `modern`, `minimal`, `bold` |
| `-o, --output` | `output.mp4` | Output video file path |
| `--no-silence` | *(flag)* | Skip silence removal stage |
| `--silence-method` | `vad` | Silence detection: `vad` or `auto-editor` |
| `--captions` | *(flag)* | Generate captions from audio |
| `--burn` | *(flag)* | Burn captions directly into video |
| `--preset` | `fast` | Encoder speed: `ultrafast`, `fast`, `medium`, `slow` |
| `--hardware` | `auto` | Encoder: `auto`, `nvenc`, `amf`, `qsv`, `software` |

### `clearcut trim`

Remove silence from a single video file.

```bash
clearcut trim --input raw.mp4 --output trimmed.mp4 --method vad --threshold 0.5
```

| Option | Default | Description |
|--------|---------|-------------|
| `-i, --input` | *(required)* | Video file to trim |
| `-o, --output` | *(auto)* | Output file (default: `input_trimmed.mp4`) |
| `--method` | `vad` | Detection method: `vad` or `auto-editor` |
| `--threshold` | `0.5` | VAD sensitivity (0.0–1.0, lower = more audio kept) |

### `clearcut transcribe`

Generate ASS subtitle captions from a video.

```bash
clearcut transcribe --input video.mp4 --style modern --output captions.ass
```

| Option | Default | Description |
|--------|---------|-------------|
| `-i, --input` | *(required)* | Video/audio file to transcribe |
| `-s, --style` | `default` | Caption style preset |
| `-o, --output` | *(auto)* | Output ASS file (default: `input.ass`) |

## Project Structure

```
clearcut/
├── __init__.py          # Package version
├── cli.py               # Typer CLI (process, trim, transcribe)
├── models.py            # Pydantic configuration models
├── pipeline.py          # Pipeline orchestrator (4 stages)
├── silence.py           # Silero-VAD + ffmpeg concat silence removal
├── compositor.py        # MoviePy PiP overlays + image insertion
├── captions.py          # WhisperX → ASS subtitle generation → ffmpeg burn
├── styles.py            # Caption style presets (ASS parameters)
└── encoder.py           # Hardware-accelerated ffmpeg encoding
```

## Why ClearCut?

- **🎯 Turnkey** — one command from raw footage to publish-ready video
- **🔒 Works offline** — no cloud API calls, everything runs locally
- **⚡ Hardware accelerated** — auto-detects NVENC, AMF, QSV
- **🧩 Modular** — run the full pipeline or individual stages
- **📦 Pip installable** — `pip install clearcut` and go
- **🐍 Python** — easy to extend, script, and integrate

## Tech Stack

| Component | Tool | Why |
|-----------|------|-----|
| Silence detection | [Silero-VAD](https://github.com/snakers4/silero-vad) ⭐ 9.1k | Enterprise-grade VAD, 98%+ accuracy |
| Silence removal | ffmpeg concat demuxer | Lossless segment splicing |
| Video compositing | [MoviePy](https://github.com/Zulko/moviepy) ⭐ 14.6k | `CompositeVideoClip` for PiP + overlays |
| Transcription | [WhisperX](https://github.com/m-bain/whisperX) ⭐ 22k | Word-level timestamps with forced alignment |
| Subtitles | ASS (Advanced SubStation Alpha) | Karaoke, styling, positioning |
| Encoding | ffmpeg (NVENC/AMF/QSV) | Hardware-accelerated final output |

## License

MIT
